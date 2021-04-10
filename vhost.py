import click
import modules.exceptions as ex

from modules.host.sessions import new_session
from modules.host.protocol import HostProtocol, MessageTypes


async def main(host_tag):
    sessions = {}
    async with HostProtocol(host_tag) as protocol:
        async for command, session_id, body in protocol.read_messages():
            # Create new client session
            if command == MessageTypes.CSS:
                sessions[session_id] = new_session(protocol, session_id, body)
                continue

            # Check for existing session
            if session_id not in sessions:
                print('session not found', command, session_id)
                continue

            # Forward data to session
            if command == MessageTypes.CSM:
                sessions[session_id].forward(body)
            # Close session
            elif command == MessageTypes.CSC:
                print('session close', session_id)
                sessions[session_id].close()
            # Unexpected data
            else:
                print('unknown command', command)
                continue


@click.command()
@click.argument('host_tag')
def cli(host_tag):
    ex.run_and_catch(main(host_tag))


if __name__ == '__main__':
    cli()
