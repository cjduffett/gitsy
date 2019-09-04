"""Object services."""

import hashlib
import re
import zlib
from pathlib import Path
from typing import List, Optional, Type, cast

from ..models import objects
from ..models.repo import Repository
from .refs import resolve_ref


def read_object(repo: Repository, sha: str, obj_type: Optional[str] = None) -> objects.Object:
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


def cat_object(repo: Repository, sha: str, obj_type: str) -> None:
    """Display the given object of the specified type."""

    full_sha = resolve_object(repo, name=sha, obj_type=obj_type)[0]
    obj = read_object(repo, full_sha, obj_type=obj_type)
    print(obj.serialize())


def write_object(obj: objects.Object, write: bool = True) -> str:
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
    repo: Repository, file_name: str, obj_type: str = "blob", write: bool = False
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


def resolve_object(repo: Repository, name: str) -> str:
    """Resolves the name of a Git Object to its full SHA-1 hash."""

    candidates: List[str] = list()

    # Anything with more than 16 characters is considered a "long" hash.
    # Full length SHA-1 hashes are 40 characters long.
    LONG_HASH_REGEX = re.compile(r"^[0-9A-Fa-f]{16,40}$")

    # The minimum length for a "short" hash references is 4 characters.
    # Anything sorter is too likely to be ambiguous.
    SHORT_HASH_REGEX = re.compile(r"^[0-9A-Fa-f]{4,16}$")

    name = name.strip()

    if not name:
        raise Exception("No name to resolve!")

    if name == "HEAD":
        return [resolve_ref(repo, "HEAD")]

    if LONG_HASH_REGEX.match(name):
        if len(name) == 40:
            # This is a complete hash
            return [name.lower()]

    if SHORT_HASH_REGEX.match(name):
        # This is a short hash.
        name = name.lower()
        prefix = name[0:2]
        path = repo.repo_dir("objects", mkdir=False) / prefix

        rest = name[2:]
        for file_ in path.iterdir():
            if file_.name.startswith(rest):
                candidates.append(prefix + file_.name)

    return candidates


def find_object(
    repo: Repository, name: str, obj_type: Optional[str] = None, follow: bool = True
) -> Optional[str]:
    """Find the Object with the given name. Returns None if no Object is found."""

    candidates = resolve_object(repo, name)

    if not candidates:
        raise Exception(f"No such reference {name}")

    if len(candidates) > 1:
        display_candidates = "\n - ".join(candidates)
        raise Exception(f"Ambiguous reference {name}, candidates are:\n - {display_candidates}")

    sha = candidates[0]

    if not obj_type:
        return sha

    while True:
        obj = read_object(repo, sha)

        # Object is of the requested type
        if obj.type_ == obj_type:
            return sha

        if not follow:
            return None

        # Follow tags
        if obj.type_ == "tag":
            tag = cast(objects.Tag, obj)
            sha = tag.obj_sha

        elif obj.type_ == "commit" and obj_type == "tree":
            commit = cast(objects.Commit, obj)
            sha = commit.tree_sha
        else:
            return None


def log_history(repo: Repository, commit_sha: str) -> None:
    """Logs a history of Commits to the console, starting with the given commit SHA."""

    full_sha = find_object(repo, commit_sha, obj_type="commit")
    assert full_sha
    commit = cast(objects.Commit, read_object(repo, full_sha, obj_type="commit"))
    _log_commit(commit, commit_sha)


def _log_commit(commit: objects.Commit, commit_sha: str) -> None:
    """Logs a single Commit to the console."""

    print(f"commit: {commit_sha}")

    author = commit.message.author

    print(f"Author: {author.name} <{author.email}>")
    print(f"Date:   {author.authored_at}")
    print(f"\n\t{str(commit.message.text)}")


def _get_object_class(obj_type: str) -> Type[objects.Object]:
    """Get the Object subclass for the given type."""

    try:
        return {
            "blob": objects.Blob,
            "commit": objects.Commit,
            "tag": objects.Tag,
            "tree": objects.Tree,
        }[obj_type]

    except KeyError:
        raise Exception(f"Invalid object type {obj_type!r}")
