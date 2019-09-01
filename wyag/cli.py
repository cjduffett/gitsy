"""Wyag CLI entrypoint and commands."""

import sys

import click

from . import services

VERSION = "0.1.0"


@click.group()
def wyag():
    """The stupid content tracker."""
    sys.tracebacklimit = 0  # Disable error tracebacks


@click.command("cat-file")
@click.argument("obj_type", metavar="TYPE")
@click.argument("obj_sha", metavar="OBJECT")
def cat_file(obj_type, obj_sha):
    """Print the specified OBJECT."""

    repo = services.repo.find_repo(required=True)
    services.objects.cat_object(repo, obj_sha, obj_type)


@click.command("hash-object")
@click.argument("file_name", metavar="FILE")
@click.option(
    "-t",
    "--type",
    "obj_type",
    type=click.Choice(["blob", "commit", "tag", "tree"]),
    default="blob",
    help="The type of object.",
)
@click.option("-w", "--write", is_flag=True, help="Write the hashed file to disk.")
def hash_object(file_name, obj_type, write):
    """Compute the SHA-1 hash of the specified FILE."""

    repo = services.repo.find_repo(required=write)
    sha = services.objects.hash_object(repo, file_name, obj_type=obj_type, write=write)
    print(sha)


@click.command()
@click.argument("path", default=".")
def init(path):
    """Initialize a new, empty repository."""
    services.repo.init_repo(path)


@click.command()
@click.argument("commit_sha", metavar="COMMIT")
def log(commit_sha):
    """Print the history of the specified COMMIT."""

    repo = services.repo.find_repo(required=True)
    services.objects.log_history(repo, commit_sha)


@click.command("ls-tree")
@click.argument("tree_sha", metavar="TREE")
def ls_tree(tree_sha):
    """Print the specified TREE."""

    repo = services.repo.find_repo(required=True)
    services.tree.ls_tree(repo, tree_sha)


@click.command()
def version():
    """Print this project's version and exit."""
    print(VERSION)


# Add all of the subcommands to the main group
wyag.add_command(cat_file)
wyag.add_command(hash_object)
wyag.add_command(init)
wyag.add_command(log)
wyag.add_command(ls_tree)
wyag.add_command(version)
