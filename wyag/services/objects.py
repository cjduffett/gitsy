"""Object services."""

import hashlib
import zlib
from pathlib import Path
from typing import Type

from .. import models


def read_object(repo: models.Repository, sha: str) -> models.objects.Object:
    """Load the specified Git object from the filesystem, if it exists."""

    obj_path = Path("objects") / sha[0:2] / sha[2:]
    obj_file = repo.repo_file(obj_path)

    if not obj_file.exists():
        raise Exception(f"Object {sha} does not exist!")

    with obj_file.open("rb") as f:
        raw_data = zlib.decompress(f.read())

    # Read object type
    obj_type_separator = raw_data.find(b" ")
    obj_type = raw_data[0:obj_type_separator].decode("utf-8")

    # Read and validate object size
    obj_size_separator = raw_data.find(b"\x00")
    obj_size = raw_data[obj_type_separator:obj_size_separator].decode("utf-8")

    if int(obj_size) != len(raw_data) - obj_size_separator - 1:
        raise Exception(f"Malformed object {sha}: bad length")

    obj_data = raw_data[obj_size_separator + 1 :]
    obj_class = _get_object_class(obj_type)
    return obj_class(repo, obj_data)


def cat_object(repo: models.Repository, sha: str, obj_type: str) -> None:
    """Display the given object of the specified type."""

    obj = read_object(repo, resolve_sha(repo, name=sha, obj_type=obj_type))

    if obj.type_ != obj_type:
        raise Exception(f"Object {sha} is not of type {obj_type!r}")

    print(obj.serialize())


def write_object(obj: models.objects.Object, write: bool = True) -> str:
    """Serialize object data and generate a new SHA-1 hash of that object."""

    obj_data = obj.serialize()

    # Add the header, format: "<obj_type> <checksum>\x00<obj_data>"
    raw_data = obj.type_.encode() + b" " + str(len(obj_data)).encode() + b"\x00" + obj_data

    # Compute the hash
    sha = hashlib.sha1(raw_data).hexdigest()

    if write:
        obj_path = Path("objects") / sha[0:2] / sha[2:]
        obj_file = obj.repo.repo_file(obj_path, touch=True)
        obj_file.write_bytes(zlib.compress(raw_data))

    return sha


def hash_object(
    repo: models.Repository, file_name: str, obj_type: str = "blob", write: bool = False
) -> str:
    """Reads the given file and generates a SHA-1 hash of its contents.

    Specify `write = True` to write the object's contents to disk.
    """

    file_ = Path(file_name)

    if not file_.exists():
        raise Exception(f"File {file_} does not exist!")

    obj_data = file_.read_bytes()
    obj_class = _get_object_class(obj_type)
    obj = obj_class(repo, obj_data)

    return write_object(obj, write=write)


def resolve_sha(repo: models.Repository, name: str, obj_type: str, follow: bool = True) -> str:
    """Resolves the name of a Git Object to its full SHA-1 hash."""
    return name  # TODO: implement name resolution


def _get_object_class(obj_type: str) -> Type[models.objects.Object]:
    """Get the Object subclass for the given type."""

    try:
        return {
            "blob": models.objects.Blob,
            "commit": models.objects.Commit,
            "tag": models.objects.Tag,
            "tree": models.objects.Tree,
        }[obj_type]

    except KeyError:
        raise Exception(f"Invalid object type {obj_type!r}")
