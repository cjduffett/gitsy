"""Git Tag services."""

from typing import Optional

from ..models.objects import Tag
from ..models.repo import Repository
from .objects import resolve_object
from .refs import create_ref


def create_tag(
    repo: Repository,
    name: str,
    obj_sha: Optional[str] = None,
    annotate: bool = False,
    message: Optional[str] = None,
):
    """Creat a new tag with the given name, optionally referencing the specified object.

    There are 2 flavors of tags:
    1. "Lightweight" tags  - refs to a commits, trees, or blobs.
    2. Tag objects - store an author, date, and message, like commits.

    The tag `message` is ignored if `annotate = False`.
    """

    if annotate and not message:
        raise Exception("A 'message' is required to annotate a tag")

    if annotate:
        # Create a tag object
        tag = Tag(repo)

    else:
        # Create a "lightweight" tag ref
        ref_name = f"tags/{name}"
        full_sha = resolve_object(repo, obj_sha)
        create_ref(repo, ref_name, sha=full_sha)
