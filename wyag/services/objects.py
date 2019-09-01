"""Object services."""

import hashlib
import zlib
from pathlib import Path
from typing import Optional, Type

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
    space_index = raw_data.find(b" ")
    obj_type = raw_data[0:space_index].decode("utf-8")

    # Read and validate object size
    null_index = raw_data.find(b"\x00")
    obj_size = raw_data[space_index:null_index].decode("utf-8")

    if int(obj_size) != len(raw_data) - null_index - 1:
        raise Exception(f"Malformed object {sha}: bad length")

    obj_data = raw_data[null_index + 1 :]
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


def parse_message(raw_data: bytes, start: int = 0, value_lookup: Optional[dict] = None) -> dict:
    """Parse as Git Commit or Tag message body as a series of key-value pairs.

    Commits (and Tags) are formatted like:

    ```
    tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
    parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
    author Carlton Duffett <carlton.duffett@gmail.com> 1527025023 -0700
    committer Carlton Duffett <carlton.duffett@gmail.com> 1527025044 -0700
    gpgsig -----BEGIN PGP SIGNATURE-----
     iQIzBAABCAAdFiEExwXquOM8bWb4Q2zVGxM2FxoLkGQFAlsEjZQACgkQGxM2FxoL
     kGQdcBAAqPP+ln4nGDd2gETXjvOpOxLzIMEw4A9gU6CzWzm+oB8mEIKyaH0UFIPh
     rNUZ1j7/ZGFNeBDtT55LPdPIQw4KKlcf6kC8MPWP3qSu3xHqx12C5zyai2duFZUU
     wqOt9iCFCscFQYqKs3xsHI+ncQb+PGjVZA8+jPw7nrPIkeSXQV2aZb1E68wa2YIL
     3eYgTUKz34cB6tAq9YwHnZpyPx8UJCZGkshpJmgtZ3mCbtQaO17LoihnqPn4UOMr
     V75R/7FjSuPLS8NaZF4wfi52btXMSxO/u7GuoJkzJscP3p4qtwe6Rl9dc1XC8P7k
     NIbGZ5Yg5cEPcfmhgXFOhQZkD0yxcJqBUcoFpnp2vu5XJl2E5I/quIyVxUXi6O6c
     /obspcvace4wy8uO0bdVhc4nJ+Rla4InVSJaUaBeiHTW8kReSFYyMmDCzLjGIu1q
     doU61OM3Zv1ptsLu3gUE6GU27iWYj2RWN3e3HE4Sbd89IFwLXNdSuM0ifDLZk7AQ
     WBhRhipCCgZhkj9g2NEk7jRVslti1NdN5zoQLaJNqSwO1MtxTmJ15Ksk3QP6kfLB
     Q52UWybBzpaP9HEd4XnR+HuQ4k2K0ns2KgNImsNvIyFwbpMUyUWLMPimaV1DWUXo
     5SBjDB/V/W2JBFR+XKHFJeFwYhj7DD/ocsGr4ZMx/lgc8rjIBkI=
     =lgTX
     -----END PGP SIGNATURE-----

    Initial commit
    ```

    A single value may be continued on several lines, where each subsequent line starts with
    an additional space (see gpgsig as an example of that).
    """

    if not value_lookup:
        value_lookup = dict()

    # Find the next space and newline, deliniating another key-value pair.
    space_index = raw_data.find(b" ", start)
    newline_index = raw_data.find(b"\n", start)

    # If a space appears before a newline, we have a keyword.

    # If a newline appears first, or there's no space at all (-1), we assume a blank line.
    # A blank line means the remainder of the data is the message.
    if (space_index < 0) or (newline_index < space_index):
        value_lookup[b""] = raw_data[start + 1 :]
        return value_lookup

    # Read the next key in the body
    key = raw_data[start:space_index]

    # Read the value after that key
    end = start

    while True:
        # Continuation lines begin with a space. Continue collecting the value until
        # we encounter a newline immediately followed by a space.
        end = raw_data.find(b"\n", end + 1)
        if raw_data[end + 1] == b" ":
            break

    # Extract the value and drop leading spaces on continuation lines.
    value = raw_data[space_index + 1 : end].replace(b"\n ", b"\n")

    # Repeat instances of a key become a list
    try:
        existing_value = value_lookup[key]
    except KeyError:
        value_lookup[key] = value
    else:
        if isinstance(existing_value, list):
            value_lookup[key].append(value)
        else:
            value_lookup[key] = [existing_value, value]

    return parse_message(raw_data, start=end + 1, value_lookup=value_lookup)


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
