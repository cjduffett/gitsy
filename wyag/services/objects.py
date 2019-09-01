"""Object services."""

import hashlib
import zlib
from pathlib import Path
from typing import Optional, Type, cast

from .. import models


def read_object(
    repo: models.Repository, sha: str, obj_type: Optional[str] = None
) -> models.objects.Object:
    """Load the specified Git object from the filesystem, if it exists.

    Optionall specify `obj_type` to validate that the retrieved object is of the given type.
    """

    obj_path = Path("objects") / sha[0:2] / sha[2:]
    obj_file = repo.repo_file(obj_path)

    if not obj_file.exists():
        raise Exception(f"Object {sha} does not exist!")

    with obj_file.open("rb") as f:
        raw_data = zlib.decompress(f.read())

    # Read object type
    space_index = raw_data.find(b" ")
    found_obj_type = raw_data[0:space_index].decode("utf-8")

    if obj_type and found_obj_type != obj_type:
        raise Exception(f"Object {sha} is not of type {obj_type!r}!")

    # Read and validate object size
    null_index = raw_data.find(b"\x00")
    obj_size = raw_data[space_index:null_index].decode("utf-8")

    if int(obj_size) != len(raw_data) - null_index - 1:
        raise Exception(f"Malformed object {sha}: bad length")

    obj_data = raw_data[null_index + 1 :]
    obj_class = _get_object_class(found_obj_type)
    return obj_class(repo, obj_data)


def cat_object(repo: models.Repository, sha: str, obj_type: str) -> None:
    """Display the given object of the specified type."""

    full_sha = resolve_sha(repo, name=sha, obj_type=obj_type)
    obj = read_object(repo, full_sha, obj_type=obj_type)
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


def log_history(repo: models.Repository, commit_sha: str) -> None:
    """Logs a history of Commits to the console, starting with the given commit SHA."""

    full_sha = resolve_sha(repo, commit_sha, obj_type="commit")
    commit = cast(models.objects.Commit, read_object(repo, full_sha, obj_type="commit"))
    _log_commit(commit, commit_sha)


def _log_commit(commit: models.objects.Commit, commit_sha: str) -> None:
    """Logs a single Commit to the console."""

    print(f"commit: {commit_sha}")

    author = commit.message.author

    print(f"Author: {author.name} <{author.email}>")
    print(f"Date:   {author.authored_at}")
    print(f"\n\t{str(commit.message.text)}")


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
