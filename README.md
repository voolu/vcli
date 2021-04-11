# Voolu CLI

Simplify terminal access to remote machines using the [voolu network](https://dev.voolu.io).

## Create an account

While in beta accounts are totally free and unlimited. (Within reason...)

```bash
vacc create
```

```shell script
[?] Choose a username: username
[?] Choose a password: ********
[?] Re-enter password: ********
```

## Login

Use the login command to authenticate your current machine.

```bash
vacc login
```

```bash
[?] Username: username
[?] Password: ********

Logged in and saved token at ~/.voolu/token
```

## Connect host

Use the `vhost` command to register the current machine as a host with a given 'tag'.

```bash
vhost my-host
```

## Connect clients

The `vsh` command creates an ssh-like session with a given host tag.

```bash
vsh my-host
```

## Contributing

The goal is to build out v___ commands to cover all desired use cases. Modules folder is designed to support an ecosystem of top level commands.

## Support

For support, please create an issue or email support@voolu.io.