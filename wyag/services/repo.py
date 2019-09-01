"""Repository services."""

from pathlib import Path
from typing import Optional, Union

from ..models import Repository


def init_repo(path: str) -> Repository:
    """Create a new Git repository.

    To create a new repository the worktree directory must not exist, or must be empty.
    """

    repo = Repository(path, force=True)

    if not repo.worktree.exists():
        # Initialize a new directory for the worktree if none exists
        repo.worktree.mkdir(parents=True)  # mkdir -p
    else:
        # If there's already a directory or file in .wyag, abort
        if not repo.worktree.is_dir():
            raise Exception(f"{repo.worktree} is not a directory!")

        if list(repo.worktree.iterdir()):
            raise Exception(f"{repo.worktree} is not an empty directory!")

    # .git/description
    description_file = repo.repo_file("description", touch=True)

    with description_file.open("w") as f:
        f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

    # .git/HEAD
    head_file = repo.repo_file("HEAD", touch=True)

    with head_file.open("w") as f:
        f.write("ref: refs/heads/master\n")

    # .git/config
    config_file = repo.repo_file("config", touch=True)

    with config_file.open("w") as f:
        repo.default_config.write(f)

    print(f"Initialized empty git repository in {repo.worktree}")

    return repo


def find_repo(path: Union[Path, str] = ".", required: bool = True) -> Optional[Repository]:
    """Find a return the git repository containing the specified path."""

    current_dir = Path(path).resolve()

    gitdir = current_dir / ".git"

    if gitdir.exists():
        return Repository(path)

    # We've hit the filesystem root if the 'parent' of the current directory is ITSELF.
    # This is a unique property of the root directory '/'. If we hit the root, we can
    # safely say we didn't find a .git directory.
    if current_dir.parent == current_dir:
        # If an existing repository isn't required for an operation, return
        # a temporary one based on the current directory.
        if not required:
            return Repository(".")

        raise Exception("No .git directory found.")

    # If we haven't found a .git directory yet, recurse into the parent and try again.
    return find_repo(current_dir.parent, required)
