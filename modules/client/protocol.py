import asyncio

from modules.auth import AuthService


class ClientProtocol:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    auth_service = AuthService()

    def __init__(self, host_tag):
        self.host_tag = host_tag

    async def __aenter__(self):
        self.replicas = await self.auth_service.find_replicas()

        self.host_token = await self.auth_service.get_host_token(self.host_tag)

        self.reader, self.writer = await self.find_connection()
        asyncio.get_running_loop().create_task(self.start_heartbeat())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.auth_service.close()
        self.writer.close()

    async def start_session(self, session_type: str):
        self.writer.write(b'CSS' + session_type.encode() + b'\n')
        await self.writer.drain()

    async def start_heartbeat(self):
        while True:
            await asyncio.sleep(10)
            self.writer.write(b'HBT\n')

    async def find_connection(self):
        # TODO: this should be done in parallel
        for ip_addr in self.replicas:
            con = await self.attempt_connection(ip_addr)
            if con:
                print('connecting to:', ip_addr)
                return con

        raise Exception(f"Can't find host {self.host_token}")

    async def attempt_connection(self, ip_addr):
        ssl_context = await self.auth_service.get_certificate(ip_addr)
        reader, writer = await asyncio.open_connection(ip_addr, 8080, ssl=ssl_context)

        # send client connect request
        writer.write(b'CCQ' + self.host_token.encode() + b'\n')
        await writer.drain()
        # get client connect response
        ccr = await reader.readline()
        if ccr.endswith(b'N\n'):
            print(self.host_token, 'not found at host', ip_addr)
            writer.close()
            return
        else:
            return reader, writer
