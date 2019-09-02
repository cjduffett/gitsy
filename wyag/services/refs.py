"""Object reference services."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..models.repo import Repository

References = Dict[str, Any]


def create_ref(
    repo: Repository,
    name: str,
    ref: Optional[str] = None,
    sha: Optional[str] = None,
    force: bool = False,
):
    """Creates a new reference in `.git/refs/`.

    If `force = True`, overwrite the existing ref if there is one.
    """

    data = b""

    # Refs can either point to another ref, or to an object's full SHA-1 hash, but not both.
    if ref and not sha:
        # We have an indirect reference
        data = b"ref: " + ref.encode()

    elif sha and not ref:
        # We have a direct reference
        data = sha.encode()
    else:
        raise ValueError("Specify only one of 'ref', 'sha'!")

    ref_dir = repo.repo_dir("refs", mkdir=True)
    new_ref = ref_dir / name

    if not force:
        if new_ref.exists():
            raise Exception(f"Ref {new_ref} already exists!")

    with new_ref.open("wb") as f:
        f.write(data)


def delete_ref(repo: Repository, name: str) -> str:
    """Delete an existing reference in `.git/refs/`, if it exists."""

    sha = resolve_ref(repo, name)

    ref_file = repo.repo_dir("refs", mkdir=True) / name
    ref_file.unlink()

    return sha


def list_refs(repo: Repository, path: Optional[Union[Path, str]] = None) -> References:
    """Collect and resolve a list of references in the given `path`, defaults to `.git/refs/`.

    Returns a recursive lookup of references like:
    refs = {
        "heads": {
            "master": "174acae109186ba66c5e7638cd68f9779dee6694",
            "feature": {
                "my-branch": "8c67749d6b047996146f8f71fd7b2d1a12b9b0ba",
            },
        },
        "tags": {
            "1.1.0": "HEAD",
            "1.0.0": "5e880e8919d623ab8f981ac8b698a1b8fa137db8",
            "beta": {
                "2.0.0a": "1c1f34386c8ee3a31bcbd45bd14c55702ea07adb",
            },
        },
        ...
    }
    """

    if not path:
        ref_dir = repo.repo_dir("refs", mkdir=True)
    else:
        ref_dir = Path(path)

    refs: References = dict()

    # Collect refs in sorted order
    for item_path in sorted(ref_dir.iterdir(), key=str):

        ref_path = ref_dir / item_path

        if ref_path.is_dir():
            # If the reference is a directory, recursively resolve all of the
            # references in that directory.
            refs[ref_path.stem] = list_refs(repo, path=ref_path)
        else:
            # If the reference is a file, read the reference and resolve it to
            # its full SHA-1 hash.
            refs[ref_path.name] = resolve_ref(repo, name=str(ref_path))

    return refs


def resolve_ref(repo: Repository, name: str) -> str:
    """Resolve an Object reference to a full SHA-1 hash."""

    ref_file = repo.repo_file(name)

    with ref_file.open("r") as f:
        data = f.readline()[:-1]  # Drop final newline

    if data.startswith("ref: "):
        return resolve_ref(repo, data[5:])  # Indirect reference

    return data  # Direct reference to an Object hash


def show_refs(refs: References, show_hash: bool = True, prefix: str = "") -> None:
    """List references."""

    for ref, value in refs.items():

        if isinstance(value, str):
            display_hash = value + " " if value else ""
            print(f"{display_hash}{ref}")
        else:
            prefix = ref + ("/" if prefix else "")
            show_refs(value, show_hash=show_hash, prefix=prefix)
