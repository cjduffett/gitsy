"""Git tree manipulation services."""

from typing import List, Tuple

from .. import models


def read_nodes(data: bytes) -> List[models.objects.TreeNode]:
    """Read a Git Tree's nodes."""

    index: int = 0
    nodes: List[models.objects.TreeNode] = list()

    while index < len(data):
        index, node = _parse_node(data, start=index)
        nodes.append(node)

    return nodes


def write_nodes(nodes: List[models.objects.TreeNode]) -> bytes:
    """Write a Git Tree's nodes to bytes."""

    data = b""

    for node in nodes:
        data += node.mode
        data += b" " + node.path
        data += b"\x00" + int(node.sha, 16).to_bytes(20, byteorder="big")

    return data


def _parse_node(data: bytes, start: int = 0) -> Tuple[int, models.objects.TreeNode]:
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

    return sha_end_index, models.objects.TreeNode(mode=mode, path=path, sha=sha)
