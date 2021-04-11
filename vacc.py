import asyncio
import os
import click
import inquirer

from modules.auth import AuthService
import modules.exceptions as ex


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    if debug:
        click.echo('Debug mode is on')


async def do_login():
    async with AuthService() as auth:
        questions = [
            inquirer.Text('user', message="Username"),
            inquirer.Password('pass', message="Password"),
        ]
        answers = inquirer.prompt(questions)

        token = await auth.login(answers['user'], answers['pass'])
        p = os.path.expanduser('~/.voolu/')
        if not os.path.exists(p):
            os.mkdir(p)
        with open(p + 'token', 'w') as f:
            f.write(token)

        print('Logged in and saved token at ~/.voolu/token')


async def create_account():
    async with AuthService() as auth:
        questions = [
            inquirer.Text('user', message="Choose a username"),
            inquirer.Password('pass', message="Choose a password"),
            inquirer.Password('repass', message="Re-enter password"),
        ]
        answers = inquirer.prompt(questions)

        if answers['pass'] != answers['repass']:
            print('passwords do not match')
            return

        await auth.create_account(answers['user'], answers['pass'])

        print('Account create, please login using "vacc login"')


@cli.command()
def login():
    ex.run_and_catch(do_login())


@cli.command()
def create():
    asyncio.get_event_loop().run_until_complete(create_account())


if __name__ == '__main__':
    cli()
