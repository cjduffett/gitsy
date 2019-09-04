"""Shared test fixtures."""

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

    return empty_worktree


@pytest.fixture
def repo(worktree) -> Repository:
    """Creates an empty Repository, for testing."""
    return Repository(worktree)
