"""Wyag CLI entrypoint and commands."""

import sys

import click

from . import models, services

VERSION = "0.1.0"


@click.group()
def wyag():
    """The stupid content tracker."""
    sys.tracebacklimit = 0  # Disable error tracebacks


@click.command()
def version():
    """Print this project's version and exit."""
    print(VERSION)


@click.command()
@click.argument("path", default=".")
def init(path):
    """Initialize a new, empty repository."""
    services.repo.init_repo(path)


@click.command("cat-file")
@click.argument("object_", metavar="OBJECT")
def cat_file(object_):
    """Print the specified OBJECT."""

    repo = models.repo.Repository.find()
    services.objects.cat_object(repo, object_)


# Add all of the subcommands to the main group
wyag.add_command(version)
wyag.add_command(init)
wyag.add_command(cat_file)
