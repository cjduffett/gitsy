"""Object services."""

import zlib
from typing import Type

from .. import models


def read_object(repo: models.Repository, sha: str) -> models.objects.Object:
    """Load the specified Git object from the filesystem, if it exists."""

    object_dir = repo.repo_dir("objects")
    object_file = object_dir / sha[0:2] / sha[2:]

    if not object_file.exists():
        raise Exception(f"Object {sha} does not exist!")

    with object_file.open("rb") as f:
        raw_data = zlib.decompress(f.read())

    # Read object type
    obj_type_separator = raw_data.find(b" ")
    obj_type = raw_data[0:obj_type_separator].decode("ascii")

    # Read and validate object size
    obj_size_separator = raw_data.find(b"\x00")
    obj_size = raw_data[obj_type_separator:obj_size_separator].decode("ascii")

    if int(obj_size) != len(raw_data) - obj_size_separator - 1:
        raise Exception(f"Malformed object {sha}: bad length")

    obj_data = raw_data[obj_size_separator + 1 :]
    obj_class = _get_object_class(obj_type)
    return obj_class(repo, obj_data)


def _get_object_class(object_type: str) -> Type[models.objects.Object]:
    """Get the Object subclass for the given type."""

    try:
        return {
            "blob": models.objects.Blob,
            "commit": models.objects.Commit,
            "tag": models.objects.Tag,
            "tree": models.objects.Tree,
        }[object_type]

    except KeyError:
        raise Exception(f"Invalid object type {object_type!r}")


def cat_object(repo: models.Repository, sha: str) -> None:
    """Display the given object of the specified type."""

    obj = read_object(repo, sha)
    print(obj.serialize())
