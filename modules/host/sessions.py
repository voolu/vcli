import fcntl
import os
import struct
import termios
import pty
from subprocess import Popen
import base64
import asyncio
import json
from modules.host.protocol import HostProtocol


# TODO: use aiofiles

class Session:
    protocol: HostProtocol
    session_id: bytes

    async def send_line(self, data):
        await self.protocol.send_line(b'CSM' + self.session_id + data)

    async def send_close(self):
        await self.protocol.send_line(b'CSC' + self.session_id)


class ShellSession(Session):
    is_ended = False

    def __init__(self, protocol, session_id):
        master_fd, slave_fd = pty.openpty()

        p = Popen('bash',
                  preexec_fn=os.setsid,
                  stdin=slave_fd,
                  stdout=slave_fd,
                  stderr=slave_fd,
                  universal_newlines=True)

        self.master_fd = master_fd
        self.slave_fd = slave_fd
        self.process = p
        self.protocol = protocol
        self.session_id = session_id
        self.outgoing_queue = asyncio.Queue()

        loop = asyncio.get_running_loop()
        loop.add_reader(master_fd, self.forward_to_client, master_fd, loop)
        loop.create_task(self.watch_exit())
        loop.create_task(self.watch_queue())

    def close(self):
        pass

    def forward_to_client(self, master_fd, loop):
        o = os.read(master_fd, 50000)
        o = base64.b64encode(o)
        self.outgoing_queue.put_nowait(o)

    async def watch_queue(self):
        while True:
            o = await self.outgoing_queue.get()
            await self.send_line(o)
            self.outgoing_queue.task_done()

    async def watch_exit(self):
        while True:
            await asyncio.sleep(0.5)
            if self.process.poll() is not None:
                await self.send_close()
                self.is_ended = True
                break

    def resize(self, data):
        size = json.loads(data)
        rows, cols = size['rows'], size['cols']
        req = getattr(termios, 'TIOCSWINSZ', -2146929561)
        s = bytearray(struct.pack('HHHH', rows, cols, 0, 0))
        fcntl.ioctl(self.slave_fd, req, s)

    def forward(self, d):
        header = d[:3]
        body = d[3:]

        if header == b'RSZ':
            self.resize(body)
        elif header == b'DTA':
            os.write(self.master_fd, base64.b64decode(body))

    def __del__(self):
        asyncio.get_running_loop().remove_reader(self.master_fd)


class CopySession(Session):
    """
    On WS connect create a new session that accepts incoming messages and writes files to disk.
    For fast uploads multiple sessions will run in parallel.
    """
    is_closed = False

    def __init__(self, protocol, session_id):
        self.protocol = protocol
        self.session_id = session_id
        self.loop = asyncio.get_running_loop()
        self.active_file = {}

    def close(self):
        self.is_closed = True

    def forward(self, d):
        header, body = d.split(b'.')
        header = json.loads(base64.b64decode(header))

        p = header['p']

        if 'pull' in header:
            self.loop.create_task(self.send_file(p))
        elif 'push' in header:
            if p not in self.active_file:
                self.active_file[p] = open(p, 'wb')

            if len(body) != 0:
                try:
                    d = base64.b64decode(body)
                    self.active_file[p].write(d)
                except:
                    # print('error decoding', body)
                    pass
            else:
                print('closing', p)
                self.active_file[p].close()
                del self.active_file[p]

    async def send_file(self, path):
        header = base64.b64encode(json.dumps({'p': path}).encode())

        size = os.path.getsize(path)
        await self.send_line(header + b'.' + str(size).encode())

        with open(path, 'rb') as f:
            while True:
                if self.is_closed:
                    return

                o = f.read(10240)

                if not o:
                    await self.send_line(header + b'.')
                    break

                o = base64.b64encode(o)
                await self.send_line(header + b'.' + o)


def new_session(protocol, session_id, session_type):
    print('new ', session_type, 'session', session_id)

    if session_type == b'VSH':
        return ShellSession(protocol, session_id)
    elif session_type == b'CPY':
        return CopySession(protocol, session_id)
    else:
        print(f'unknown session type: {session_type}')
