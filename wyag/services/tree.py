"""Git tree manipulation services."""

from typing import List, Tuple, cast

from ..models.objects import Tree, TreeNode
from ..models.repo import Repository
from .objects import read_object


def read_nodes(data: bytes) -> List[TreeNode]:
    """Read a Git Tree's nodes."""

    index: int = 0
    nodes: List[TreeNode] = list()

    while index < len(data):
        index, node = _parse_node(data, start=index)
        nodes.append(node)

    return nodes


def write_nodes(nodes: List[TreeNode]) -> bytes:
    """Write a Git Tree's nodes to bytes."""

    data = b""

    for node in nodes:
        data += node.mode
        data += b" " + node.path
        data += b"\x00" + int(node.sha, 16).to_bytes(20, byteorder="big")

    return data


def ls_tree(repo: Repository, tree_sha: str) -> None:
    """Print the specified Tree."""

    tree = cast(Tree, read_object(repo, tree_sha, obj_type="tree"))

    for node in tree.nodes:
        # Left pad with zeros to always display a 6-digit file mode
        display_mode = "0" * (6 - len(node.mode)) + node.mode.decode("ascii")

        # Read the object referenced by this node
        node_obj = read_object(repo, node.sha)

        print(f"{display_mode} {node_obj.type_} {node.sha} {node.path.decode('ascii')}")


def _parse_node(data: bytes, start: int = 0) -> Tuple[int, TreeNode]:
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
