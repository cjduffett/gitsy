"""Wyag CLI entrypoint and commands."""

import click


@click.group()
@click.pass_context
def wyag(context):
    """The stupid content tracker."""


@click.command()
def version():
    with open(".version") as f:
        print(f.readline())


@click.command()
def init():
    """Initialize a wyag repository."""
    print("New repo install in .wyag")


# Add all of the subcommands to the main group
wyag.add_command(version)
wyag.add_command(init)
