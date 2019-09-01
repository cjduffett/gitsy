"""Commit and Tag messages."""

from typing import Dict, List, NamedTuple

MessageHeaders = Dict[bytes, List[bytes]]


class Message(NamedTuple):
    """A Commit or Tag message from the object store."""

    # Key-value headers parsed from the message body.
    # Repeat instances of a key become a list.
    headers: MessageHeaders

    # The commit or tag message text.
    text: bytes
