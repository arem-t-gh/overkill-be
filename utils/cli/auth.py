import click


@click.group()
def auth_cli():
    """Auth cli group."""
    pass


@auth_cli.command()
def get_access_token():
    """Get access token."""
    click.echo("Access token fetched: Bearer ABC123")


# access token getter w/ login

# access token getter w/o login

if __name__ == "__main__":
    auth_cli()
