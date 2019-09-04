"""Git Commit services."""

from typing import Optional

from ..models.message import Message, MessageHeaders
from ..models.objects import Commit
from ..models.repo import Repository


def create_commit(repo: Repository, message: Optional[str] = None, add_all: bool = False):
    """Commit all staged changes.

    Optionally specify a commit `message`. Specify `add_all` to commit all tracked changes.
    """

    commit = Commit(repo)

    commit_headers: MessageHeaders = {b"tree": [commit.tree_sha.encode()]}

    message_text = message.encode() if message else b""
    commit.message = Message(headers=commit_headers, text=message_text)
