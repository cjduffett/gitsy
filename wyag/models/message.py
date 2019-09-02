"""Commit and Tag messages."""

from typing import Dict, List, NamedTuple, Optional, Union

# The key-value pairs that form the header of a Message.
MessageHeaders = Dict[bytes, List[bytes]]


class MessageAuthor(NamedTuple):
    """The author of a Message."""

    name: str
    email: str
    authored_at: int  # Unix timestamp
    timezone: str = "+0000"  # All times in UTC for now

    @classmethod
    def read_author(cls, data: bytes) -> "MessageAuthor":
        """Parse and return a MessageAuthor from the given data."""

        # We want all parts as strings, so decode everything first
        author_data = data.decode("ascii")

        email_start = author_data.find("<")
        email_end = author_data.find(">", start=email_start + 1)
        timestamp_end = author_data.find(" ", start=email_end + 1)

        if any(index == -1 for index in [email_start, email_end, timestamp_end]):
            raise Exception("Malformed message author")

        return cls(
            name=author_data[0 : email_start - 1],
            email=author_data[email_start + 1 : email_end],
            authored_at=int(author_data[email_end + 1 : timestamp_end]),
            timezone=author_data[timestamp_end + 1 :],
        )

    def encode(self) -> bytes:
        """Encode the author for serialization."""
        return f"{self.name} <{self.email}> {self.authored_at} {self.timezone}".encode("ascii")


class Message:
    """A Commit or Tag message from the object store."""

    # Key-value headers parsed from the message body.
    # Repeat instances of a key become a list.
    _headers: MessageHeaders

    # The commit or tag message text.
    _text: bytes

    def __init__(
        self,
        text: Union[str, bytes],
        author: Optional[MessageAuthor] = None,
        headers: Optional[MessageHeaders] = None,
    ) -> None:

        if headers:
            self._headers = headers
        else:
            self._headers = dict()

        if author:
            self.set_author(author)

        self.set_text(text)

    def get_header(self, key: Union[str, bytes]) -> str:
        """Return a single value from the message header, as a string."""

        key = self._convert_bytes(key)

        try:
            # If a key exists in the header there must be at least one value.
            return self._convert_str(self._headers[key][0])
        except KeyError:
            raise Exception(f"Message header {self._convert_str(key)!r} not found")

    def set_header(self, key: Union[str, bytes], value: Union[str, bytes]):
        """Set a key-value pair in the message's headers."""

        key = self._convert_bytes(key)
        self._headers[key] = self._convert_bytes(value)

    def get_text(self) -> str:
        """Returns the message text as a string."""

        return self._convert_str(self._text)

    def set_text(self, text: Union[str, bytes]):
        """Sets the message text."""

        self._text = self._convert_bytes(text)

    def get_author(self, key: Union[str, bytes] = "author") -> MessageAuthor:
        """Returns the author of the Message, parsed from the 'author' header.

        Optionally specify a non-default `key` if the message author is stored under a
        different header key.
        """

        author_data = self._convert_bytes(self.get_header(key))
        return MessageAuthor.read_author(author_data)

    def set_author(self, author: MessageAuthor, key: Union[str, bytes] = "author"):
        """Sets the author of the message.

        The message author is stored in the 'author' header. Optionally specify a
        non-default `key` to store the author under a different header key.
        """

        header_value = author.encode()
        self.set_header(key, header_value)

    @staticmethod
    def _convert_str(value: Union[str, bytes]) -> str:
        """Converts the given value to a string if needed."""

        if isinstance(value, bytes):
            return value.decode("ascii")

        return value

    @staticmethod
    def _convert_bytes(value: Union[str, bytes]) -> bytes:
        """Converts the given value to bytes if needed."""

        if isinstance(value, str):
            return value.encode("ascii")

        return value

    @classmethod
    def read_message(
        cls, data: bytes, start: int = 0, headers: Optional[MessageHeaders] = None
    ) -> "Message":
        """Read a Git Commit or Tag message's headers and text.

        Commits and Tag messages are formatted like:

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

        Messages start with a "header" of key-value pairs. A single value may be continued on
        several lines, where each subsequent line starts with an additional "continuation space"
        (see 'gpgsig' as an example of that).

        A blank line follows the header. The remainder of the message body after the blank line
        is reserved for the message text.
        """

        if not headers:
            headers = dict()

        # Find the next space and newline, deliniating another key-value pair.
        space_index = data.find(b" ", start)
        newline_index = data.find(b"\n", start)

        # If a newline appears first (before a space), or there's no space at all (-1), we
        # assume a blank line. A blank line means the remainder of the data is the message.
        if space_index < 0 or newline_index < space_index:
            return Message(headers=headers, text=data[start + 1 :])

        # If a space appears before a newline, we have a keyword:

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
            headers[key].append(value)
        except KeyError:
            headers[key] = [value]

        return cls.read_message(data, start=end + 1, headers=headers)

    def write(self) -> bytes:
        """Write the Message's headers and text to bytes."""

        data = b""

        for key, values in self._headers.items():
            # Lists will be serialized on adjacent lines
            for value in values:
                # Add the leading spaces back for continuation lines.
                data += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

        # Append message
        data = data + b"\n" + self._text

        return data
