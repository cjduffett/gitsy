"""Object reference services."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..models.repo import Repository


def list_refs(
    repo: Repository, path: Optional[Union[Path, str]] = None
) -> Dict[Union[Path, str], Any]:
    """Collect and resolve a list of references in the given `path`, defaults to `.git/refs/`."""

    if not path:
        ref_dir = repo.repo_dir("refs")
    else:
        ref_dir = Path(path)

    refs: Dict[Union[Path, str], Any] = dict()

    # Collect refs in sorted order
    for item_path in sorted(ref_dir.iterdir(), key=str):
        ref_path = ref_dir / item_path

        if ref_path.is_dir():
            refs[ref_path] = list_refs(repo, ref_path)
        else:
            refs[ref_path] = resolve_ref(repo, ref_path)

    return refs


def resolve_ref(repo: Repository, ref: Union[Path, str]) -> str:
    """Resolve an Object reference to a full SHA-1 hash."""

    ref_file = repo.repo_file(ref)

    with ref_file.open("r") as f:
        data = f.read()[:-1]  # Drop final newline

    if data.startswith(b"ref: "):
        return resolve_ref(repo, data[5:])

    return data
