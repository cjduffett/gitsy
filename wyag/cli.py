"""Wyag CLI entrypoint and commands."""

import sys

import click

from . import services

VERSION = "0.1.0"
OBJECT_TYPE_CHOICES = ["blob", "commit", "tag", "tree"]


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


@click.command()
@click.argument("sha", metavar="COMMIT")
@click.argument("path", default=".")
def checkout(sha, path):
    """Checkout a COMMIT in the directory specified by PATH.

    PATH must be an EMPTY directory.
    """

    repo = services.repo.find_repo()
    services.tree.checkout(repo, sha, path)


@click.command("hash-object")
@click.argument("file_name", metavar="FILE")
@click.option(
    "-t",
    "--type",
    "obj_type",
    type=click.Choice(OBJECT_TYPE_CHOICES),
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


@click.command("rev-parse")
@click.argument("name")
@click.option(
    "-t",
    "--type",
    "obj_type",
    type=click.Choice(OBJECT_TYPE_CHOICES),
    default=None,
    help="The expected object type.",
)
def rev_parse(name, obj_type):
    """Parse the specified revision or object NAME identifier.

    Optionally specify the expected object TYPE.
    """

    repo = services.repo.find_repo()
    obj_sha = services.objects.find_object(repo, name, obj_type=obj_type, follow=True)
    print(obj_sha)


@click.command("show-ref")
def show_ref():
    """List references in a local repository."""

    repo = services.repo.find_repo(required=True)
    refs = services.refs.list_refs(repo)
    services.refs.show_refs(refs)


@click.command()
@click.argument("name", default="HEAD")
@click.argument("obj_sha", required=False)
@click.option("-a", "create_tag_obj", is_flag=True, help="Create a tag object.")
def tag(name, obj_sha, create_tag_obj):
    """List tags or create a new tag with the specified NAME.

    Optionally specify an OBJECT the new tag will point to.
    """

    repo = services.repo.find_repo(required=create_tag_obj)

    if name:
        # Create a new tag with the specified NAME
        tag_type = "object" if create_tag_obj else "ref"
        services.tags.create_tag(name, obj_sha, tag_type)

    else:
        # List tags
        refs = services.refs.list_refs(repo)
        services.refs.show_refs(refs["tags"], show_hash=False)


@click.command()
def version():
    """Print this project's version and exit."""
    print(VERSION)


# Add all of the subcommands to the main group
wyag.add_command(cat_file)
wyag.add_command(checkout)
wyag.add_command(hash_object)
wyag.add_command(init)
wyag.add_command(log)
wyag.add_command(ls_tree)
wyag.add_command(rev_parse)
wyag.add_command(show_ref)
wyag.add_command(tag)
wyag.add_command(version)
