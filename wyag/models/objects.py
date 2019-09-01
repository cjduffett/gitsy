"""Git Object model."""

from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional

from ..services.message import read_message, write_message
from ..services.tree import read_nodes, write_nodes
from .message import Message
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
    def deserialize(self, data: bytes):
        """Parse raw object data into object attributes."""

    @abstractmethod
    def serialize(self) -> bytes:
        """Write the object as bytes."""


class Blob(Object):
    """A Git blob."""

    type_ = "blob"
    blob_data: bytes

    def serialize(self) -> bytes:
        return self.blob_data

    def deserialize(self, data: bytes):
        self.blob_data = data


class Commit(Object):
    """A Git commit."""

    type_ = "commit"
    message: Message

    def deserialize(self, data: bytes):
        self.message = read_message(data)

    def serialize(self) -> bytes:
        return write_message(self.message)


class Tag(Object):
    """A Git tag."""

    type_ = "tag"
    message: Message

    def deserialize(self, data: bytes):
        self.message = read_message(data)

    def serialize(self) -> bytes:
        return write_message(self.message)


class TreeNode(NamedTuple):
    """A node of a Git Tree."""

    mode: bytes
    path: bytes
    sha: str


class Tree(Object):
    """A Git tree."""

    type_ = "tree"
    nodes: List[TreeNode]

    def deserialize(self, data: bytes):
        self.nodes = read_nodes(data)

    def serialize(self) -> bytes:
        return write_nodes(self.nodes)
