"""Git object model tests."""

import pytest

from wyag.models import objects
from wyag.models.repo import Repository


@pytest.fixture
def repo() -> Repository:
    """Return a fake Repository, for testing."""

    return Repository(".", force=True)


def test_blob__parse(repo):
    """Should correctly parse a Blob from data."""

    data = b"Some file contents\n"

    blob = objects.Blob(repo, data)
    assert blob.data == data


def test_blob__write(repo):
    """Should correctly serialize the Blob's data."""

    data = b"Some file contents\n"

    blob = objects.Blob(repo, data)
    assert blob.write() == data
