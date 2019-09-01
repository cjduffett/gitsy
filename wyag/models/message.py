"""Commit and Tag messages."""

from typing import Dict, List, NamedTuple

MessageHeaders = Dict[bytes, List[bytes]]


class MessageAuthor(NamedTuple):
    """The author of a Message."""

    name: str
    email: str
    authored_at: str


class Message(NamedTuple):
    """A Commit or Tag message from the object store."""

    # Key-value headers parsed from the message body.
    # Repeat instances of a key become a list.
    headers: MessageHeaders

    # The commit or tag message text.
    text: bytes

    @property
    def author(self) -> MessageAuthor:
        """Returns the author of the message."""

        try:
            author = self.headers[b"author"][0]
        except (KeyError, IndexError):
            raise Exception("Message does not have an author!")

        email_start = author.find(b"<")
        email_end = author.find(b">")

        author_name = str(author[0 : email_start - 1])
        email = str(author[email_start + 1 : email_end])
        authored_at = str(author[email_end + 1 :])

        return MessageAuthor(name=author_name, email=email, authored_at=authored_at)
