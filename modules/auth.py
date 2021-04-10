import httpx
import os

import modules.exceptions as ex

LOOKUP_SERVICE_URL = 'https://discover.dev.voolu.io'


class AuthService:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.client.aclose()

    async def find_replicas(self):
        r = await self.client.get(LOOKUP_SERVICE_URL + '/replicas')
        r = r.json()
        return r['replicas']
        # return ['0.0.0.0']

    async def login(self, email, password):
        r = await self.client.post(LOOKUP_SERVICE_URL + '/login', json={'email': email, 'password': password})
        r = r.json()

        if 'token' in r:
            return r['token']
        else:
            raise ex.BadCredentials()

    async def create_account(self, email, password):
        r = await self.client.post(LOOKUP_SERVICE_URL + '/create-account', json={'email': email, 'password': password})
        r = r.json()

        if 'success' in r and r['success']:
            return
        else:
            raise Exception(r['msg'])

    async def get_host_token(self, host_tag):
        path = os.path.expanduser('~/.voolu/token')

        if not os.path.exists(path):
            await self.client.aclose()
            raise ex.NotLoggedIn()

        with open(path, 'r') as f:
            account_token = f.read()

        r = await self.client.post(LOOKUP_SERVICE_URL + '/host-connect', json={'tag': host_tag, 'token': account_token})
        r = r.json()

        if not r['success']:
            await self.client.aclose()
            raise Exception('failed to get host token')

        return r['host_token']
