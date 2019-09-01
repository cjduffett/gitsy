"""Object reference services."""

from pathlib import Path
from typing import Dict, Optional, Union

from ..models.repo import Repository

References = Dict[str, str]


def list_refs(repo: Repository, path: Optional[Union[Path, str]] = None) -> References:
    """Collect and resolve a list of references in the given `path`, defaults to `.git/refs/`.

    Returns a lookup of references:
    refs = {
        "refs/heads/master": "174acae109186ba66c5e7638cd68f9779dee6694",
        "refs/heads/feature/my-branch": "8c67749d6b047996146f8f71fd7b2d1a12b9b0ba",
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
            refs_in_dir = list_refs(repo, path=ref_path)
            refs.update(refs_in_dir)
        else:
            refs[str(ref_path)] = resolve_ref(repo, ref=ref_path)

    return refs


def resolve_ref(repo: Repository, ref: Union[Path, str]) -> str:
    """Resolve an Object reference to a full SHA-1 hash."""

    ref_file = repo.repo_file(ref)

    with ref_file.open("r") as f:
        data = f.read()[:-1]  # Drop final newline

    if data.startswith(b"ref: "):
        return resolve_ref(repo, data[5:])

    return data


def show_refs(repo: Repository, refs: References, show_hash: bool = True):
    """List references."""

    for ref, sha in refs.items():
        display_sha = sha + " " if show_hash else ""
        print(f"{display_sha}{ref}")
