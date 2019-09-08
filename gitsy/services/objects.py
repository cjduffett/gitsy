"""Object services."""

import hashlib
import re
import zlib
from typing import List, Optional, Tuple, Type, cast

from ..models import objects
from ..models.repo import Repository
from .refs import resolve_ref


def read_object(repo: Repository, sha: str, obj_type: Optional[str] = None) -> objects.Object:
    """Load the specified Git object from the filesystem, if it exists.

    Optionall specify `obj_type` to validate that the retrieved object is of the given type.
    """

    obj_dir = repo.repo_dir("objects")
    obj_file = obj_dir / sha[0:2] / sha[2:]

    if not obj_file.exists():
        raise Exception(f"Object {sha} does not exist!")

    raw_data = zlib.decompress(obj_file.read_bytes())

    try:
        parsed_obj_type, obj_size, obj_data = _parse_object(raw_data)
    except Exception:
        raise Exception(f"Malformed object {sha}: cannot parse")

    if obj_type and parsed_obj_type != obj_type:
        raise Exception(f"Object {sha} is not of type {obj_type!r}!")

    if obj_size != len(obj_data):
        raise Exception(f"Malformed object {sha}: bad length")

    obj_class = _get_object_class(parsed_obj_type)
    return obj_class(repo, obj_data)


def _parse_object(data: bytes) -> Tuple[str, int, bytes]:
    """Parses a raw comporessed object, returning it's (type, size, data)."""

    # Read object type
    space_index = data.find(b" ")
    obj_type = str(data[0:space_index], "utf-8")

    # Read and validate object size
    null_index = data.find(b"\x00")
    obj_size = str(data[space_index:null_index], "utf-8")
    obj_data = data[null_index + 1 :]

    return obj_type, int(obj_size), obj_data


def cat_object(repo: Repository, name: str, obj_type: str) -> None:
    """Display the given object of the specified type."""

    full_sha = resolve_object_name(repo, name=name)
    obj = read_object(repo, sha=full_sha, obj_type=obj_type)
    print(obj.write())


def write_object(repo, obj: objects.Object, write: bool = True) -> str:
    """Serialize object data and generate a new SHA-1 hash of that object."""

    obj_data = obj.write()

    # Add the header, format: "<obj_type> <checksum>\x00<obj_data>"
    raw_data = obj.type_.encode() + b" " + str(len(obj_data)).encode() + b"\x00" + obj_data

    # Compute the hash
    sha = hashlib.sha1(raw_data).hexdigest()

    if write:
        obj_dir = repo.repo_dir("objects")
        obj_path = obj_dir / sha[0:2] / sha[2:]
        obj_file = repo.repo_file(obj_path, touch=True)
        obj_file.write_bytes(zlib.compress(raw_data))

    return sha


def hash_object(
    repo: Repository, file_name: str, obj_type: str = "blob", write: bool = False
) -> str:
    """Reads the given file and generates a SHA-1 hash of its contents.

    Specify `write = True` to write the object's contents to disk.
    """

    file_ = repo.worktree / file_name

    if not file_.exists():
        raise Exception(f"File {file_} does not exist!")

    obj_data = file_.read_bytes()
    obj_class = _get_object_class(obj_type)
    obj = obj_class(repo, obj_data)

    return write_object(repo, obj, write=write)


def resolve_object_name(repo: Repository, name: str) -> str:
    """Resolves the name of a Git Object to its full SHA-1 hash."""

    if not name:
        raise Exception("No name to resolve!")

    candidates: List[str] = list()

    # Full length SHA-1 hashes are 40 characters long.
    FULL_HASH_REGEX = re.compile(r"^[0-9a-f]{40}$")

    # The minimum length for a "short" hash references is 4 characters.
    # Anything sorter is too likely to be ambiguous to even bother with.
    SHORT_HASH_REGEX = re.compile(r"^[0-9a-f]{4,40}$")

    name = name.strip().lower()

    if FULL_HASH_REGEX.match(name):
        # If the object exists, return the SHA-1 hash as-is.
        obj_file = repo.repo_dir("objects") / name[0:2] / name[2:]
        if obj_file.exists():
            return name

    if SHORT_HASH_REGEX.match(name):
        # Search the 'objects' directory for files matching the name. We initially
        # have only the first 2 characters to search for as an intermediate directory.
        prefix = name[0:2]
        prefix_dir = repo.repo_dir("objects") / prefix

        if not prefix_dir.exists():
            raise Exception(f"No such object {name}")

        rest = name[2:]
        for file_ in prefix_dir.iterdir():
            if file_.name.startswith(rest):
                candidates.append(prefix + file_.name)

    if len(candidates) == 1:
        # We've found exactly one match
        return candidates[0]

    if not candidates:
        raise Exception(f"No such object {name}")

    display_candidates = "\n - ".join(candidates)
    raise Exception(f"Ambiguous object name {name!r}, candidates are:\n - {display_candidates}\n")


def find_object(
    repo: Repository, name: str, obj_type: Optional[str] = None, follow: bool = True
) -> Optional[str]:
    """Find the Object with the given name. Returns None if no Object is found."""

    if name.upper() == "HEAD":
        return resolve_ref(repo, "HEAD")

    sha = resolve_object_name(repo, name)

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
            continue

        # Follow commit trees
        if obj.type_ == "commit" and obj_type == "tree":
            commit = cast(objects.Commit, obj)
            sha = commit.tree_sha
            continue

        return None


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
