"""Git Object model."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional

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


class MessageBody(NamedTuple):
    """The body of a Commit or Tag message from the object store."""

    # Key-value pairs parsed from the message body.
    # Repeat instances of a key become a list.
    values: Dict[bytes, List[bytes]]

    # The commit or tag message.
    message: bytes


class MessageObject(Object):
    """An object serialized using the simplified RFC 2822 message format."""

    body: MessageBody

    def deserialize(self, data: bytes):
        self.message = self._parse_message(data)

    def serialize(self) -> bytes:
        return self._write_message(self.message)

    def _parse_message(
        self, data: bytes, start: int = 0, value_lookup: Optional[dict] = None
    ) -> MessageBody:
        """Parse as Git Commit or Tag message body as a series of key-value pairs.

        Commits (and Tags) are formatted like:

        ```
        tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
        parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
        author Carlton Duffett <carlton.duffett@gmail.com> 1527025023 -0700
        committer Carlton Duffett <carlton.duffett@gmail.com> 1527025044 -0700
        gpgsig -----BEGIN PGP SIGNATURE-----
        iQIzBAABCAAdFiEExwXquOM8bWb4Q2zVGxM2FxoLkGQFAlsEjZQACgkQGxM2FxoL
        kGQdcBAAqPP+ln4nGDd2gETXjvOpOxLzIMEw4A9gU6CzWzm+oB8mEIKyaH0UFIPh
        rNUZ1j7/ZGFNeBDtT55LPdPIQw4KKlcf6kC8MPWP3qSu3xHqx12C5zyai2duFZUU
        wqOt9iCFCscFQYqKs3xsHI+ncQb+PGjVZA8+jPw7nrPIkeSXQV2aZb1E68wa2YIL
        3eYgTUKz34cB6tAq9YwHnZpyPx8UJCZGkshpJmgtZ3mCbtQaO17LoihnqPn4UOMr
        V75R/7FjSuPLS8NaZF4wfi52btXMSxO/u7GuoJkzJscP3p4qtwe6Rl9dc1XC8P7k
        NIbGZ5Yg5cEPcfmhgXFOhQZkD0yxcJqBUcoFpnp2vu5XJl2E5I/quIyVxUXi6O6c
        /obspcvace4wy8uO0bdVhc4nJ+Rla4InVSJaUaBeiHTW8kReSFYyMmDCzLjGIu1q
        doU61OM3Zv1ptsLu3gUE6GU27iWYj2RWN3e3HE4Sbd89IFwLXNdSuM0ifDLZk7AQ
        WBhRhipCCgZhkj9g2NEk7jRVslti1NdN5zoQLaJNqSwO1MtxTmJ15Ksk3QP6kfLB
        Q52UWybBzpaP9HEd4XnR+HuQ4k2K0ns2KgNImsNvIyFwbpMUyUWLMPimaV1DWUXo
        5SBjDB/V/W2JBFR+XKHFJeFwYhj7DD/ocsGr4ZMx/lgc8rjIBkI=
        =lgTX
        -----END PGP SIGNATURE-----

        Initial commit
        ```

        A single value may be continued on several lines, where each subsequent line starts with
        an additional space (see gpgsig as an example of that).
        """

        if not value_lookup:
            value_lookup = dict()

        # Find the next space and newline, deliniating another key-value pair.
        space_index = data.find(b" ", start)
        newline_index = data.find(b"\n", start)

        # If a space appears before a newline, we have a keyword.

        # If a newline appears first (before a space), or there's no space at all (-1), we
        # assume a blank line. A blank line means the remainder of the data is the message.
        if space_index < 0 or newline_index < space_index:
            return MessageBody(values=value_lookup, message=data[start + 1 :])

        # Read the next key in the body
        key = data[start:space_index]

        # Read the value after that key
        end = start

        while True:
            # Continuation lines begin with a space. Continue collecting the value until
            # we encounter a newline immediately followed by a space.
            end = data.find(b"\n", end + 1)
            if data[end + 1] != b" ":
                break

        # Extract the value and drop leading spaces on continuation lines.
        value = data[space_index + 1 : end].replace(b"\n ", b"\n")

        # Keys may appear more than once, so we store them as lists.
        try:
            value_lookup[key].append(value)
        except KeyError:
            value_lookup[key] = [value]

        return self._parse_message(data, start=end + 1, value_lookup=value_lookup)

    def _write_message(self, body: MessageBody) -> bytes:
        """Write a MessageBody's items and message to bytes."""

        data = b""

        for key, value in body.values.items():
            # Add the leading spaces back for continuation lines.
            data += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

        # Append message
        data = data + b"\n" + body.message

        return data


class Blob(Object):
    """A Git blob."""

    type_ = "blob"
    blob_data: bytes

    def serialize(self) -> bytes:
        return self.blob_data

    def deserialize(self, data: bytes):
        self.blob_data = data


class Commit(MessageObject):
    """A Git commit."""

    type_ = "commit"


class Tag(MessageObject):
    """A Git tag."""

    type_ = "tag"


class Tree(Object):
    """A Git tree."""

    type_ = "tree"

    def serialize(self) -> bytes:
        return b""

    def deserialize(self, data: bytes) -> Any:
        return "tree"
