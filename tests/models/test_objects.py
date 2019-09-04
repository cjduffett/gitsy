"""Git object model tests."""

import pytest

from wyag.models import objects
from wyag.models.repo import Repository

# TODO: Test Tree and TreeNode models


@pytest.fixture
def repo() -> Repository:
    """Return a fake Repository, for testing."""

    return Repository(".", force=True)


def test_blob__parse(repo):
    """Should correctly parse a Blob object from bytes."""

    data = b"Some file contents\n"

    blob = objects.Blob(repo, data)
    assert blob.type_ == "blob"
    assert blob.data == data


def test_blob__write(repo):
    """Should correctly serialize a Blob object to bytes."""

    data = b"Other file contents\n"

    blob = objects.Blob(repo, data)
    assert blob.write() == data


def test_commit__parse(repo, commit_message):
    """Should correctly parse a Commit object from bytes."""

    commit = objects.Commit(repo, commit_message)

    assert commit.type_ == "commit"
    assert commit.message == "Add attribute to model.\n"
    assert commit.tree_sha == "29ff16c9c14e2652b22f8b78bb08a5a07930c147"
    assert commit.parent_sha == "206941306e8a8af65b66eaaaea388a7ae24d49a0"

    assert commit.author.name == "Carlton Duffett"
    assert commit.author.email == "carlton.duffett@example.com"
    assert commit.author.authored_at == 1527025023
    assert commit.author.timezone == "-0700"

    assert commit.committer.name == "Carlton Duffett"
    assert commit.committer.email == "cduffett@example.tech"
    assert commit.committer.authored_at == 1527025044
    assert commit.committer.timezone == "-0700"


def test_commit__parse__initial(repo, initial_commit_message):
    """Should correctly parse a Commit object from an initial commit (no parent)."""

    commit = objects.Commit(repo, initial_commit_message)

    assert commit.type_ == "commit"
    assert commit.message == "Initial commit.\n"
    assert commit.tree_sha == "29ff16c9c14e2652b22f8b78bb08a5a07930c147"
    assert commit.parent_sha is None

    assert commit.author.name == "Carlton Duffett"
    assert commit.author.email == "carlton.duffett@example.com"
    assert commit.author.authored_at == 1527025023
    assert commit.author.timezone == "-0700"

    assert commit.committer.name == "Carlton Duffett"
    assert commit.committer.email == "carlton.duffett@example.com"
    assert commit.committer.authored_at == 1527025023
    assert commit.committer.timezone == "-0700"


def test_commit__write(repo, commit_message):
    """Should correctly serialize a Commit object to bytes."""

    commit = objects.Commit(repo, commit_message)
    assert commit.write() == commit_message


def test_commit__write__initial(repo, initial_commit_message):
    """Should correctly serialize an initial Commit object to bytes (no parent)."""

    commit = objects.Commit(repo, initial_commit_message)
    assert commit.write() == initial_commit_message


def test_tag__parse(repo, tag_message):
    """Should correctly parse a Tag object from bytes."""

    tag = objects.Tag(repo, tag_message)

    assert tag.type_ == "tag"
    assert tag.message == "Release version 1.0.2, see changelog for details.\n"
    assert tag.obj_type == "commit"
    assert tag.obj_sha == "b6a7fad7ec645c74f26dfe5b28fc73c29d6c7182"

    assert tag.tagger.name == "Carlton Duffett"
    assert tag.tagger.email == "carlton.duffett@example.com"
    assert tag.tagger.authored_at == 1567444360
    assert tag.tagger.timezone == "-0700"


def test_tag__write(repo, tag_message):
    """Should correctly serialize a Tag object to bytes."""

    tag = objects.Tag(repo, tag_message)
    assert tag.write() == tag_message
