"""Object reference service tests."""

import pytest

from gitsy.services import refs


@pytest.fixture
def existing_refs(repo):
    """Some existing refs in the active repository."""

    # HEAD ref
    ref_head = repo.repo_file("HEAD", touch=True)
    ref_head.write_text("ref: refs/heads/master")

    # Create some branches
    branch_master = repo.repo_file("refs/heads/master", touch=True)
    branch_master.write_text("174acae109186ba66c5e7638cd68f9779dee6694")

    branch_dev = repo.repo_file("refs/heads/dev", touch=True)
    branch_dev.write_text("96e86353078f58a63e9d0dbd5beadc23e76a918f")

    branch_nested = repo.repo_file("refs/heads/feature/my-branch", touch=True)
    branch_nested.write_text("8c67749d6b047996146f8f71fd7b2d1a12b9b0ba")

    # Create some tags
    tag_head = repo.repo_file("refs/tags/1.1.0", touch=True)
    tag_head.write_text("HEAD")

    tag_version = repo.repo_file("refs/tags/1.0.0", touch=True)
    tag_version.write_text("5e880e8919d623ab8f981ac8b698a1b8fa137db8")

    tag_nested = repo.repo_file("refs/tags/beta/2.0.0a1", touch=True)
    tag_nested.write_text("1c1f34386c8ee3a31bcbd45bd14c55702ea07adb")


def test_create_ref__mutually_exclusive_options():
    pass


def test_create_ref__new():
    pass


def test_create_ref__existing():
    pass


def test_create_ref__force_overwrite():
    pass


def test_delete_ref__ok():
    pass


def test_delete_ref__not_found():
    pass


def test_list_refs(repo, existing_refs):
    """Should collect and recursively resolve all refs in the repository."""

    ref_lookup = refs.list_refs(repo)
    assert ref_lookup == {
        "heads": {
            "master": "174acae109186ba66c5e7638cd68f9779dee6694",
            "dev": "96e86353078f58a63e9d0dbd5beadc23e76a918f",
            "feature": {"my-branch": "8c67749d6b047996146f8f71fd7b2d1a12b9b0ba"},
        },
        "tags": {
            "1.1.0": "HEAD",
            "1.0.0": "5e880e8919d623ab8f981ac8b698a1b8fa137db8",
            "beta": {"2.0.0a1": "1c1f34386c8ee3a31bcbd45bd14c55702ea07adb"},
        },
    }

    # Refs inserted into lookup in sorted order
    assert list(ref_lookup["heads"]) == ["dev", "feature", "master"]
    assert list(ref_lookup["tags"]) == ["1.0.0", "1.1.0", "beta"]


def test_resolve_ref__direct(repo):
    """Should resolve a direct reference to the SHA-1 hash it contains."""

    ref_file = repo.repo_file("refs/my-ref", touch=True)
    ref_file.write_text("bbdc4ac77e11b3ae223f2a807455f72f7b5700c1")

    sha = refs.resolve_ref(repo, "refs/my-ref")
    assert sha == "bbdc4ac77e11b3ae223f2a807455f72f7b5700c1"


def test_resolve_ref__nested_dir(repo):
    """Should resolve a nested direct reference to the SHA-1 hash it contains."""

    ref_file = repo.repo_file("refs/tags/my-tag", touch=True)
    ref_file.write_text("bbdc4ac77e11b3ae223f2a807455f72f7b5700c1")

    sha = refs.resolve_ref(repo, "refs/tags/my-tag")
    assert sha == "bbdc4ac77e11b3ae223f2a807455f72f7b5700c1"


def test_resolve_ref__indirect(repo):
    """Should recursively resolve an indirect reference until a SHA-1 hash is found."""

    indirect_ref_file = repo.repo_file("refs/tags/latest", touch=True)
    indirect_ref_file.write_text("ref: refs/tags/v2.3.40")

    direct_ref_file = repo.repo_file("refs/tags/v2.3.40", touch=True)
    direct_ref_file.write_text("bbdc4ac77e11b3ae223f2a807455f72f7b5700c1")

    sha = refs.resolve_ref(repo, "refs/tags/latest")
    assert sha == "bbdc4ac77e11b3ae223f2a807455f72f7b5700c1"
