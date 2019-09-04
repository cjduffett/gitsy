"""Git Repository model tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gitsy.models.repo import Repository
from gitsy.services.repo import init_repo


@pytest.fixture
def empty_worktree():
    """Creates a temporary worktree directory for a Repository to exist inside."""

    with TemporaryDirectory() as dirname:
        yield dirname


@pytest.fixture
def worktree(empty_worktree):
    """Creates a temporary worktree directory with a .git directory initialized inside."""

    new_repo = init_repo(empty_worktree)

    assert new_repo.worktree.exists()
    assert new_repo.gitdir.exists()
    assert new_repo.config_file.exists()

    yield empty_worktree


def test_repo__init__ok(worktree):
    """Should correctly initialize a Repository from an active worktree."""

    repo = Repository(worktree)

    assert repo._force is False
    assert repo.worktree == Path(worktree)
    assert repo.gitdir == Path(worktree) / ".git"

    assert repo.config_file == Path(worktree) / ".git" / "config"
    assert repo.config_file.exists

    core_config = repo.config["core"]
    assert core_config["repositoryformatversion"] == "0"
    assert core_config["filemode"] == "false"
    assert core_config["bare"] == "false"


def test_repo__init__force(empty_worktree):
    """Should correctly initialize a new Repository in an empty worktree if force = True."""

    repo = Repository(empty_worktree, force=True)

    assert repo._force is True
    assert repo.worktree == Path(empty_worktree)
    assert repo.gitdir == Path(empty_worktree) / ".git"
    assert repo.config_file == Path(empty_worktree) / ".git" / "config"

    # If there's no config file the Repository has empty configuration.
    assert not repo.config.sections()


def test_repo__init__no_gitdir(empty_worktree):
    """Should raise an Exception if there's no .git directory."""

    with pytest.raises(Exception) as excinfo:
        Repository(empty_worktree)

    assert str(excinfo.value) == f"Not a git repository {empty_worktree}/.git"


def test_repo__init__no_config(empty_worktree):
    """Should raise an Exception if there's no config in the .git directory."""

    gitdir = Path(empty_worktree) / ".git"
    gitdir.mkdir(parents=True)

    with pytest.raises(Exception) as excinfo:
        Repository(empty_worktree)

    assert str(excinfo.value) == f"Configuration file missing!"


def test_repo__repo_file__found(worktree):
    """Should return a Path to the existing file in the .git directory."""

    gitdir = Path(worktree) / ".git"
    test_file = gitdir / "test.txt"
    test_file.touch()

    path = Repository(worktree).repo_file("test.txt")
    assert path == test_file


def test_repo__repo_file__not_found(worktree):
    """Should raise an Exception if the specified file is not found in the .git directory."""

    gitdir = Path(worktree) / ".git"
    test_file = gitdir / "does_not_exist.txt"
    assert not test_file.exists()

    with pytest.raises(Exception) as excinfo:
        Repository(worktree).repo_file("does_not_exist.txt")

    assert str(excinfo.value) == f"{worktree}/.git/does_not_exist.txt does not exist!"


def test_repo__repo_file__touch(worktree):
    """Should create the file if it doesn't exist."""

    path = Repository(worktree).repo_file("test.txt", touch=True)
    assert path == Path(worktree) / ".git" / "test.txt"


def test_repo__repo_dir__found(worktree):
    """Should return a Path to the existing file in the .git directory."""

    gitdir = Path(worktree) / ".git"
    test_dir = gitdir / "testdir"
    test_dir.mkdir(parents=True)

    path = Repository(worktree).repo_dir("testdir")
    assert path == test_dir


def test_repo__repo_dir__not_found(worktree):
    """Should raise an Exception if the specified directory is not found in the .git directory."""

    gitdir = Path(worktree) / ".git"
    test_dir = gitdir / "not_a_dir"
    assert not test_dir.exists()

    with pytest.raises(Exception) as excinfo:
        Repository(worktree).repo_dir("not_a_dir")

    assert str(excinfo.value) == f"{worktree}/.git/not_a_dir is not a directory!"


def test_repo__repo_dir__mkdir(worktree):
    """Should create the directory if it doesn't exist."""

    path = Repository(worktree).repo_dir("testdir", mkdir=True)
    assert path == Path(worktree) / ".git" / "testdir"


def test_repo__default_config(worktree):
    """Should return the default core config for the repository."""

    defaults = Repository(worktree).default_config
    assert defaults.sections() == ["core"]

    core_defaults = defaults["core"]
    assert core_defaults["repositoryformatversion"] == "0"
    assert core_defaults["filemode"] == "false"
    assert core_defaults["bare"] == "false"
