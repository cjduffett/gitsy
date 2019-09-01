"""Git Repository model."""

from configparser import ConfigParser
from pathlib import Path
from typing import Optional, Union


class Repository:
    """A Git repository."""

    worktree: Path
    gitdir: Path

    config_file: Path
    config: ConfigParser

    def __init__(self, path: Union[Path, str], force: bool = False) -> None:
        """Initialize the Git repository."""

        # If force = True, continue with initialization in the face of errors
        self._force = force

        self.worktree = Path(path)
        self.gitdir = self.worktree / ".git"

        if not self.gitdir.exists() and not self._force:
            raise Exception(f"Not a git repository {self.gitdir}")

        self.config_file = self.gitdir / "config"
        self.config = ConfigParser()  # Add config defaults here, if needed

        self._parse_config_file()

    def __repr__(self) -> str:
        return f"Repository('{self.worktree}')"

    def _parse_config_file(self):
        """Parse the Git config .ini file in the project's git directory."""

        config_exists = self.config_file.exists()

        if not config_exists and not self._force:
            raise Exception("Configuration file missing")

        if config_exists:
            with self.config_file.open() as f:
                self.config.read_file(f)

            self._check_repo_version()

    def _check_repo_version(self):
        """Check that the repository version is supported."""

        version = self.config.get("core", "repositoryformatversion")
        if int(version) != 0:
            raise Exception(f"Unsupported repositoryformatversion {version}")

    def repo_file(self, file_name: Union[Path, str], touch: bool = False) -> Path:
        """Returns a Path to the named file within the repository.

        If `touch` = True creates an empty file if it does not exist.
        """

        file_path = self.gitdir / file_name

        if touch and not file_path.exists():
            self.repo_dir(file_path.parent, mkdir=True)
            file_path.touch()

        if not file_path.exists():
            raise Exception(f"File {file_path} does not exist!")

        return file_path

    def repo_dir(self, dir_name: Union[Path, str], mkdir: bool = False) -> Path:
        """Returns a Path to the named directory within the repository.

        If `mkdir` = True creates the Path if it does not exist.
        """

        dir_path = self.gitdir / dir_name

        if mkdir and not dir_path.exists():
            dir_path.mkdir(parents=True)

        if not dir_path.is_dir():
            raise Exception(f"{dir_path} is not a directory!")

        return dir_path

    @classmethod
    def find(cls, path: Union[Path, str] = ".", required: bool = True) -> Optional["Repository"]:
        """Find a return the git repository containing the specified path."""

        current_dir = Path(path).resolve()

        gitdir = current_dir / ".git"

        if gitdir.exists():
            return cls(path)

        # Base case, we've hit the filesystem root without finding a .git directory.
        # The 'parent' of the root directory IS the root directory.
        if current_dir.parent == current_dir:
            if not required:
                return None

            raise Exception("No .git directory found.")

        # If we haven't found a .git directory yet, recurse into the parent and try again.
        return cls.find(current_dir.parent, required)

    @property
    def default_config(self) -> ConfigParser:
        """Returns default configuration for a new repository."""

        defaults = ConfigParser()
        defaults.add_section("core")

        # Initial Git repository format, WITHOUT extensions.
        defaults.set("core", "repositoryformatversion", "0")

        # Disable tracking of file mode changes in the worktree.
        defaults.set("core", "filemode", "false")

        # This repository has a worktree (is not "bare").
        defaults.set("core", "bare", "false")
        return defaults
