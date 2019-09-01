"""Git Tag services."""

from typing import Optional

from .objects import write_object


def create_tag(name: str, obj_sha: Optional[str] = None, tag_type: str = "ref"):
    """Creat a new tag with the given name, optionally referencing the specified object."""

    # TODO: implementation
