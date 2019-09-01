"""Git Object model."""

from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional, Tuple

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
        self.message = Message.read_message(data)

    def serialize(self) -> bytes:
        return self.message.write()

    @property
    def tree_sha(self) -> str:
        """Returns the full SHA-1 hash of the Tree this Commit belongs to."""

        try:
            return str(self.message.headers[b"tree"][0], "ascii")
        except (KeyError, IndexError):
            raise Exception("Commit message does not specify a tree!")


class Tag(Object):
    """A Git tag."""

    type_ = "tag"
    message: Message

    def deserialize(self, data: bytes):
        self.message = Message.read_message(data)

    def serialize(self) -> bytes:
        return self.message.write()

    @property
    def object_sha(self) -> str:
        """Returns the full SHA-1 of the Object this Tag references."""

        try:
            return str(self.message.headers[b"object"][0], "ascii")
        except (KeyError, IndexError):
            raise Exception("Tag message does not specify an object!")


class TreeNode(NamedTuple):
    """A node of a Git Tree."""

    mode: bytes
    path: bytes
    sha: str

    def write(self) -> bytes:
        """Write the node to bytes."""

        data = b""
        data += self.mode
        data += b" " + self.path
        data += b"\x00" + int(self.sha, 16).to_bytes(20, byteorder="big")
        return data


class Tree(Object):
    """A Git tree."""

    type_ = "tree"
    nodes: List[TreeNode]

    def deserialize(self, data: bytes):
        self.nodes = self._read_nodes(data)

    def serialize(self) -> bytes:
        return self._write_nodes()

    @classmethod
    def _read_nodes(cls, data: bytes) -> List[TreeNode]:
        """Read a Git Tree's nodes."""

        index: int = 0
        nodes: List[TreeNode] = list()

        while index < len(data):
            index, node = cls._parse_node(data, start=index)
            nodes.append(node)

        return nodes

    @classmethod
    def _parse_node(cls, data: bytes, start: int = 0) -> Tuple[int, TreeNode]:
        """Parse a Node of a Git Tree.

        Format: `[mode] space [path] 0x00 [sha-1]`
        """

        # Find the space terminator of the node
        space_index = data.find(b" ", start)

        # Read the mode
        mode = data[start:space_index]

        # Find the null terminator after the space
        null_index = data.find(b"\x00", space_index)

        # Read the path
        path = data[space_index + 1 : null_index]

        # Read the SHA and convert from 20 bytes binary to the hex string
        sha_end_index = null_index + 21
        sha_bytes = data[null_index + 1 : sha_end_index]
        sha_int = int.from_bytes(sha_bytes, byteorder="big")
        sha = hex(sha_int)[2:]  # Ditch the '0x' added to the begining

        return sha_end_index, TreeNode(mode=mode, path=path, sha=sha)

    def _write_nodes(self) -> bytes:
        """Write the Git Tree's nodes to bytes."""

        data = b""

        for node in self.nodes:
            data += node.write()

        return data
