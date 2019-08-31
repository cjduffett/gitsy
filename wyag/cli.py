"""Wyag CLI entrypoint and commands."""

import sys

import click

from . import services


@click.group()
def wyag():
    """The stupid content tracker."""
    sys.tracebacklimit = 0  # Disable error tracebacks


@click.command()
def version():
    """Print this project's version and exit."""
    with open(".version") as f:
        print(f.readline())


@click.command()
@click.argument("path", default=".")
def init(path):
    """Initialize a new, empty repository."""

    services.init_repo(path)


# Add all of the subcommands to the main group
wyag.add_command(version)
wyag.add_command(init)
