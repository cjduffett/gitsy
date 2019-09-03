"""Shared model test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def commit_message() -> bytes:
    """A raw commit message, for testing."""

    with Path("tests/fixtures/commit_message").open("rb") as f:
        return f.read()


@pytest.fixture
def initial_commit_message() -> bytes:
    """A raw initial commit message, for testing."""

    with Path("tests/fixtures/initial_commit_message").open("rb") as f:
        return f.read()


@pytest.fixture
def signed_commit_message() -> bytes:
    """A raw signed commit message, for testing."""

    with Path("tests/fixtures/signed_commit_message").open("rb") as f:
        return f.read()
