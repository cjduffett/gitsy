"""Object service tests."""

import zlib

import pytest

from gitsy.models import objects
from gitsy.services import objects as services


def test_read_object__ok(repo):
    """Should load the specified object from the filesystem if it exists."""

    blob = objects.Blob(repo, b"Hello world!\n")
    sha = services.write_object(repo, blob)

    obj = services.read_object(repo, sha=sha, obj_type="blob")
    assert obj.type_ == "blob"
    assert obj.data == b"Hello world!\n"


def test_read_object__not_found(repo):
    """Should raise an Exception if the requested object is not found."""

    with pytest.raises(Exception) as excinfo:
        services.read_object(repo, sha="abc123")

    assert str(excinfo.value) == "Object abc123 does not exist!"


def test_read_object__malformed(repo):
    """Should raise an Exception if the object is malformed."""

    obj_file = repo.repo_file("objects/ab/c123", touch=True)
    obj_file.write_bytes(zlib.compress(b"blob fe\x00My spoon is too"))

    with pytest.raises(Exception) as excinfo:
        services.read_object(repo, sha="abc123")

    assert str(excinfo.value) == "Malformed object abc123: cannot parse"


def test_read_object__type_mismatch(repo, commit_message):
    """Should raise an Exception if the object type does not match the expected one."""

    commit = objects.Commit(repo, commit_message)
    sha = services.write_object(repo, commit)

    with pytest.raises(Exception) as excinfo:
        services.read_object(repo, sha=sha, obj_type="blob")

    assert (
        str(excinfo.value)
        == "Object d740e0b7e47a0a6d71e98b68b872193254cf72bb is not of type 'blob'!"
    )


def test_read_object__bad_length(repo):
    """Should raise an Exception if the object's checksum fails."""

    obj_file = repo.repo_file("objects/de/f456", touch=True)
    obj_file.write_bytes(zlib.compress(b"blob 4\x00I am a banana"))

    with pytest.raises(Exception) as excinfo:
        services.read_object(repo, sha="def456")

    assert str(excinfo.value) == "Malformed object def456: bad length"


def test_parse_object__ok():
    """Should parse a well-formed object."""

    data = b"blob 13\x00I am a banana"
    obj_type, obj_size, obj_data = services._parse_object(data)

    assert obj_type == "blob"
    assert obj_size == 13
    assert obj_data == b"I am a banana"


def test_parse_object__fail():
    """Should raise an Exception for malformed objects."""

    data = b"No, I am a banana!"

    with pytest.raises(Exception) as excinfo:
        services._parse_object(data)

    assert str(excinfo.value) == "invalid literal for int() with base 10: ' I am a banana'"


def test_cat_object(repo, mocker):
    """Should print the object's full SHA-1 hash as-is."""

    mock_print = mocker.patch("gitsy.services.objects.print")

    obj = objects.Blob(repo, b"My spoon is too big")
    sha = services.write_object(repo, obj)

    services.cat_object(repo, name=sha, obj_type="blob")

    mock_print.assert_called_once_with(b"My spoon is too big")


def test_write_object__dry_run(repo):
    """Should generate a SHA-1 hash for the object. Skips writing to the database."""

    obj = objects.Blob(repo, b"I am a banana")
    sha = services.write_object(repo, obj, write=False)
    assert sha == "8ff79d2828b3af736abc66a922b2c48fed82d803"


def test_write_object__blob(repo):
    """Should write the hashed and compressed Blob to the database."""

    obj = objects.Blob(repo, b"Hello my name is dog")
    sha = services.write_object(repo, obj)
    assert sha == "f030b72246ee29130ba701aae9bf2231733c60ca"

    obj_file = repo.gitdir / "objects" / "f0" / "30b72246ee29130ba701aae9bf2231733c60ca"
    file_data = zlib.decompress(obj_file.read_bytes())
    assert file_data == b"blob 20\x00Hello my name is dog"


def test_write_object__commit(repo, commit_message):
    """Should write the hashed and compressed Commit to the database."""

    commit = objects.Commit(repo, commit_message)
    sha = services.write_object(repo, commit)
    assert sha == "d740e0b7e47a0a6d71e98b68b872193254cf72bb"

    obj_file = repo.gitdir / "objects" / "d7" / "40e0b7e47a0a6d71e98b68b872193254cf72bb"
    file_data = zlib.decompress(obj_file.read_bytes())

    expected_data = b"""commit 256\x00tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
author Carlton Duffett <carlton.duffett@example.com> 1527025023 -0700
committer Carlton Duffett <cduffett@example.tech> 1527025044 -0700

Add attribute to model.
"""
    assert file_data == expected_data


def test_write_object__tag(repo, tag_message):
    """Should write the hashed and compressed Tag object to the database."""

    tag = objects.Tag(repo, tag_message)
    sha = services.write_object(repo, tag)
    assert sha == "c7bfd28fc7bc397568bb09b9ef70a367a9b8e036"

    obj_file = repo.gitdir / "objects" / "c7" / "bfd28fc7bc397568bb09b9ef70a367a9b8e036"
    file_data = zlib.decompress(obj_file.read_bytes())

    expected_data = b"""tag 191\x00object b6a7fad7ec645c74f26dfe5b28fc73c29d6c7182
type commit
tag 1.0.2
tagger Carlton Duffett <carlton.duffett@example.com> 1567444360 -0700

Release version 1.0.2, see changelog for details.
"""
    assert file_data == expected_data


def test_write_object__tree():
    """SHould write the hashed and compressed Tree object to the database."""

    # TODO: Test writing Trees


def test_hash_object__not_found():
    pass


def test_hash_object__full_sha():
    pass


def test_resolve_oblect__full_sha():
    pass


def test_resolve_oblect__short_sha():
    pass


def test_resolve_oblect__head():
    pass


def test_resolve_object__ref():
    pass


def test_find_object__no_results():
    pass


def test_find_object__multiple_results():
    pass


def test_find_object__no_obj_type():
    pass


def test_find_object__dont_follow():
    pass


def test_find_object__follow_tag():
    pass


def test_find_object__follow_commit():
    pass


def test_log_history():
    pass


def test_log_commit():
    pass
