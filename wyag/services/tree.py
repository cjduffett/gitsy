"""Git tree manipulation services."""

from pathlib import Path
from typing import Union, cast

from ..models import objects
from ..models.repo import Repository
from .objects import read_object, resolve_object


def checkout(repo: Repository, sha: str, path: str = "."):
    """Checkout the specified Commit or Tree."""

    full_sha = resolve_object(repo, name=sha)[0]
    obj = read_object(repo, full_sha)

    # If the specified object is a Commit, grab its Tree
    if obj.type_ == "commit":
        commit = cast(objects.Commit, obj)
        obj = read_object(repo, commit.tree_sha, obj_type="tree")

    # Verify that path is an empty directory
    checkout_path = Path(path)

    if checkout_path.exists():
        if not checkout_path.is_dir():
            raise Exception(f"{checkout_path} is not a directory!")
        if list(checkout_path.iterdir()):
            raise Exception(f"Directory {checkout_path} is not empty!")
    else:
        checkout_path.mkdir(parents=True)


def _checkout_tree(repo: Repository, tree: objects.Tree, path: Union[Path, str]):
    """Checkout the given Tree."""

    for node in tree.nodes:
        node_obj = read_object(repo, node.sha)
        dest = Path(path) / str(node.path, encoding="ascii")

        if node_obj.type_ == "tree":
            dest.mkdir(parents=True)
            tree_obj = cast(objects.Tree, node_obj)
            _checkout_tree(repo, tree_obj, path)

        if node_obj.type_ == "blob":
            blob_obj = cast(objects.Blob, node_obj)

            with dest.open("wb") as f:
                f.write(blob_obj.blob_data)


def ls_tree(repo: Repository, tree_sha: str) -> None:
    """Print the specified Tree."""

    tree = cast(objects.Tree, read_object(repo, tree_sha, obj_type="tree"))

    for node in tree.nodes:
        # Left pad with zeros to always display a 6-digit file mode
        display_mode = "0" * (6 - len(node.mode)) + node.mode.decode("ascii")

        # Read the object referenced by this node
        node_obj = read_object(repo, node.sha)

        print(f"{display_mode} {node_obj.type_} {node.sha} {node.path.decode('ascii')}")
