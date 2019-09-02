"""Git Object model."""

from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional, Tuple

from .message import Message, MessageAuthor
from .repo import Repository


class Object(ABC):
    """A Git object."""

    type_: str  # Don't set this directly
    repo: Repository

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
    data: bytes

    def serialize(self) -> bytes:
        return self.data

    def deserialize(self, data: bytes):
        self.data = data


class Commit(Object):
    """A Git commit."""

    type_ = "commit"

    # The author of the commit.
    author: MessageAuthor

    # The commit message text.
    message: str

    # The full SHA-1 hash of the worktree's root tree.
    tree_sha: str

    def deserialize(self, data: bytes):
        """Parse the Commit from a Message."""

        message = Message.read_message(data)

        self.tree_sha = message.get_header("tree")
        self.author = message.get_author()
        self.message = message.get_text()

    def serialize(self) -> bytes:
        """Create a Message from the Commit and write that Message to bytes."""

        message = Message(author=self.author, text=self.message)
        message.set_header("tree", self.tree_sha)
        return message.write()


class Tag(Object):
    """A Git tag.

    Tag objects are stored as messages, formatted like:
    ```
    object b6a7fad7ec645c74f26dfe5b28fc73c29d6c7182
    type commit
    tag 1.0.0
    tagger Carlton Duffett <carlton.duffett@gmail.com> 1567444360 -0700

    Initial release
    ```
    """

    type_ = "tag"

    # The author of the tag.
    author: MessageAuthor

    # The tag message text.
    message: str

    # The name used to refer to the tag.
    name: str

    # Full SHA-1 hash of the object being tagged.
    obj_sha: str

    # The type of object this tag refers to.
    obj_type: str

    def deserialize(self, data: bytes):
        """Parse the Tag from a Message."""

        message = Message.read_message(data)

        self.author = message.get_author(key="tagger")
        self.message = message.get_text()
        self.obj_sha = message.get_header("object")
        self.obj_type = message.get_header("type")
        self.name = message.get_header("tag")

    def serialize(self) -> bytes:
        """Create a Message from the Tag and write that message to bytes."""

        message = Message(text=self.message)
        message.set_author(self.author, key="tagger")
        message.set_header("object", self.obj_sha)
        message.set_header("type", self.obj_type)
        message.set_header("tag", self.name)

        return message.write()


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
