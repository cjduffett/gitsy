"""gitsy CLI entrypoint and commands."""

import sys

import click

from . import services

VERSION = "0.1.0"
OBJECT_TYPE_CHOICES = ["blob", "commit", "tag", "tree"]


@click.group()
def gitsy():
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


@click.command()
@click.option("-m", "--message", help="Commit message.")
@click.option("-a", "--all", "add_all", is_flag=True, help="Commit all tracked changes.")
def commit(message, add_all):
    """Commit staged changes."""

    repo = services.repo.find_repo(required=True)
    services.commit.create_commit(repo, message, add_all)


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
@click.argument("name", required=False)
@click.argument("obj_sha", default="HEAD")
@click.option("-a", "--annotate", is_flag=True, help="Create an unsigned, annotated tag object.")
@click.option("-m", "--message", help="Tag message.")
@click.option("-d", "--delete", is_flag=True, help="Delete an existing tag")
def tag(name, obj_sha, annotate, message, delete):
    """Create, list, and manage tags.

    Optionally specify an OBJECT the new tag will point to. If no OBJECT is provided,
    defaults to 'HEAD'.
    """

    if annotate and delete:
        raise click.BadOptionUsage(
            "-d", "Tag annotation (-a) and deletion (-d) are mutually exclusive options."
        )

    if annotate and not message:
        raise click.BadOptionUsage("-a", "Tag annotation requires a message (-m).")

    repo = services.repo.find_repo(required=annotate)

    if not name:
        # List tags
        refs = services.refs.list_refs(repo)
        services.refs.show_refs(refs.get("tags", {}))

    if name or annotate:
        # Create a new tag with the specified NAME
        services.tags.create_tag(name, obj_sha, annotate, message)

    if delete:
        sha = services.refs.delete_ref(repo, name)
        print(f"Deleted tag {name!r}, was {sha}")


@click.command()
def version():
    """Print this project's version and exit."""
    print(VERSION)


# Add all of the subcommands to the main group
gitsy.add_command(cat_file)
gitsy.add_command(checkout)
gitsy.add_command(commit)
gitsy.add_command(hash_object)
gitsy.add_command(init)
gitsy.add_command(log)
gitsy.add_command(ls_tree)
gitsy.add_command(rev_parse)
gitsy.add_command(show_ref)
gitsy.add_command(tag)
gitsy.add_command(version)
