import asyncio
import ssl
from modules.auth import AuthService


class MessageTypes:
    CSS = b'CSS'
    CSM = b'CSM'
    CSC = b'CSC'


class HostProtocol:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    token: str
    auth_service: AuthService = AuthService()

    def __init__(self, host_tag):
        self.host_tag = host_tag

    async def __aenter__(self):
        replicas = await self.auth_service.find_replicas()
        endpoint = replicas[0]
        ssl_context = await self.auth_service.get_certificate(endpoint)
        reader, writer = await asyncio.open_connection(endpoint, 222, ssl=ssl_context)

        self.reader = reader
        self.writer = writer

        host_token = await self.auth_service.get_host_token(self.host_tag)

        self.writer.write(b'HCQ' + host_token.encode() + b'\n')
        await self.writer.drain()

        # Get host connect response
        connect_response = (await self.reader.readline())[3:-1]

        if connect_response == b'E':
            await self._close()
            raise Exception('host tag in use')

        print('connected to:', endpoint)

        asyncio.get_running_loop().create_task(self.start_heartbeat())

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

    async def _close(self):
        await self.auth_service.client.aclose()
        self.writer.close()

    async def start_heartbeat(self):
        while True:
            self.writer.write(b'HBT\n')
            await asyncio.sleep(10)

    async def read_messages(self):
        while True:
            line = await self.reader.readline()
            if not line:
                break

            if len(line) == 1:
                # This shouldn't happen
                continue

            command = line[:3]
            session_id = line[3:39]

            yield command, session_id, line[39:-1]

    async def send_line(self, line):
        self.writer.write(line + b'\n')
        await self.writer.drain()
