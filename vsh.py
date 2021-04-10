import json
import os
import sys
import termios
import tty
import base64
import signal
import asyncio
import click

from modules.client.protocol import ClientProtocol
import modules.exceptions as ex


def forward_input(protocol):
    d = os.read(sys.stdin.fileno(), 10240)
    d = base64.b64encode(d)
    d = 'CSMDTA' + d.decode('utf8') + '\n'
    protocol.writer.write(d.encode())


def forward_output(o):
    o = base64.b64decode(o)
    os.write(sys.stdout.fileno(), o)


async def forward_resize(protocol):
    size = os.get_terminal_size()
    line = 'CSMRSZ' + json.dumps({'rows': size.lines, 'cols': size.columns}) + '\n'
    protocol.writer.write(line.encode())


async def main(host_tag, old_tty):
    async with ClientProtocol(host_tag) as protocol:
        # Send session start request
        await protocol.start_session('VSH')

        await forward_resize(protocol)

        loop = asyncio.get_running_loop()
        tty.setraw(sys.stdin.fileno())

        signal.signal(signal.SIGWINCH,
                      lambda _, __: loop.create_task(forward_resize(protocol)))  # TODO: use async queue for this
        loop.add_reader(sys.stdin.fileno(), forward_input, protocol)

        while True:
            line = await protocol.reader.readline()
            command = line[:3].decode()
            msg = line[3:]

            if command == 'CSM':
                forward_output(msg)
            elif command == 'CSC':
                return
            else:
                return


@click.command()
@click.argument('host_tag')
def cli(host_tag):
    old_tty = termios.tcgetattr(sys.stdin)
    ex.run_and_catch(main(host_tag, old_tty))
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)


if __name__ == '__main__':
    cli()
