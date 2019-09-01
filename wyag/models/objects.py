"""Git Object model."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from .repo import Repository


class Object(ABC):
    """A Git object."""

    type_: str
    repo: Repository
    data: bytes

    def __init__(self, repo: Repository, data: Optional[bytes] = None) -> None:
        self.repo = repo

        if data is not None:
            self.deserialize(data)

    @abstractmethod
    def serialize(self) -> bytes:
        """Convert the object into bytes."""

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Convert object data as bytes into a native Python representation."""


class Blob(Object):
    """A Git blob."""

    type_ = "blob"
    blob_data: bytes

    def serialize(self) -> bytes:
        return self.blob_data

    def deserialize(self, data: bytes) -> Any:
        self.blob_data = data


class Commit(Object):
    """A Git commit."""

    type_ = "commit"

    def serialize(self) -> bytes:
        return b""

    def deserialize(self, data: bytes) -> Any:
        return "commit"


class Tag(Object):
    """A Git tag."""

    type_ = "tag"

    def serialize(self) -> bytes:
        return b""

    def deserialize(self, data: bytes) -> Any:
        return "tag"


class Tree(Object):
    """A Git tree."""

    type_ = "tree"

    def serialize(self) -> bytes:
        return b""

    def deserialize(self, data: bytes) -> Any:
        return "tree"
