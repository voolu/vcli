import asyncio


class NotLoggedIn(Exception):
    pass


class BadCredentials(Exception):
    pass


def run_and_catch(coroutine):
    try:
        asyncio.get_event_loop().run_until_complete(coroutine)
    except NotLoggedIn:
        print('Please login by running "vacc login".')
    except BadCredentials:
        print('Incorrect user or password.')
