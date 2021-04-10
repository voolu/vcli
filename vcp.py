import base64
import asyncio
import json
import os

import click
from tqdm import tqdm

import modules.exceptions as ex
from modules.client.protocol import ClientProtocol
from modules.auth import AuthService

PORT = 8080

auth_service = AuthService()


def get_data_size(line):
    return int(line.decode().split('.')[-1])


async def read_from(uri):
    if ":" in uri:
        host_tag = uri.split(':')[0]

        async with ClientProtocol(host_tag) as protocol:
            await protocol.start_session('CPY')

            header = base64.b64encode(json.dumps({'p': uri.split(':')[1], 'pull': 1}).encode())
            protocol.writer.write(b'CSM' + header + b'.\n')
            await protocol.writer.drain()
            data_size = get_data_size(await protocol.reader.readline())

            with tqdm(total=data_size, desc=uri, unit="B", unit_scale=True, unit_divisor=1024) as bar:

                while True:
                    o = await protocol.reader.readline()
                    data = o[:-1].split(b'.')[1]

                    if len(data) == 0:
                        break

                    d = base64.b64decode(data)
                    bar.update(len(d))

                    yield d

    else:
        with open(uri, 'rb') as f:
            with tqdm(total=os.path.getsize(uri), desc=uri, unit="B", unit_scale=True, unit_divisor=1024) as bar:
                while True:
                    d = f.read(10240)
                    bar.update(len(d))
                    yield d


async def write_to(uri, source):
    if ":" in uri:
        remote_path = uri.split(':')[1]
        host_tag = uri.split(':')[0]

        async with ClientProtocol(host_tag) as protocol:
            await protocol.start_session('CPY')

            header = b'CSM' + base64.b64encode(json.dumps({'p': remote_path, 'push': 1}).encode())

            async for o in source:
                if not o:
                    protocol.writer.write(header + b'.\n')
                    await protocol.writer.drain()
                    print('sent close')
                    break
                else:
                    o = base64.b64encode(o)
                    protocol.writer.write(header + b'.' + o + b'\n')
                    await protocol.writer.drain()

    else:
        with open(uri, 'wb') as f:
            async for o in source:
                f.write(o)


async def main(source, target):
    reader = read_from(source)
    await write_to(target, reader)


@click.command()
@click.argument('source')
@click.argument('target')
def cli(source, target):
    ex.run_and_catch(main(source, target))


if __name__ == '__main__':
    cli()
