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
    def parse(cls, data: bytes) -> "MessageAuthor":
        """Parse and return a MessageAuthor from the given data."""

        email_start = data.find(b"<")
        email_end = data.find(b">", email_start + 1)
        timestamp_end = data.find(b" ", email_end + 2)

        if any(index == -1 for index in [email_start, email_end, timestamp_end]):
            raise Exception("Message author is malformed!")

        return cls(
            name=_convert_str(data[0 : email_start - 1]),
            email=_convert_str(data[email_start + 1 : email_end]),
            authored_at=int(data[email_end + 1 : timestamp_end]),
            timezone=_convert_str(data[timestamp_end + 1 :]),
        )

    def write(self) -> bytes:
        """Write the author to bytes."""
        return f"{self.name} <{self.email}> {self.authored_at} {self.timezone}".encode()


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

        key = _convert_bytes(key)

        try:
            # If a key exists in the header there must be at least one value.
            return _convert_str(self._headers[key][0])
        except KeyError:
            raise Exception(f"Message header {_convert_str(key)!r} not found!")

    def set_header(self, key: Union[str, bytes], value: Union[str, bytes]):
        """Set a key-value pair in the message's headers."""

        key = _convert_bytes(key)
        value = _convert_bytes(value)

        try:
            self._headers[key].append(value)
        except KeyError:
            self._headers[key] = [value]

    def get_text(self) -> str:
        """Returns the message text as a string."""

        return _convert_str(self._text)

    def set_text(self, text: Union[str, bytes]):
        """Sets the message text."""

        self._text = _convert_bytes(text)

    def get_author(self, key: Union[str, bytes] = "author") -> MessageAuthor:
        """Returns the author of the Message, parsed from the 'author' header.

        Optionally specify a non-default `key` if the message author is stored under a
        different header key.
        """

        author_data = _convert_bytes(self.get_header(key))
        return MessageAuthor.parse(author_data)

    def set_author(self, author: MessageAuthor, key: Union[str, bytes] = "author"):
        """Sets the author of the message.

        The message author is stored in the 'author' header. Optionally specify a
        non-default `key` to store the author under a different header key.
        """
        self.set_header(key, author.write())

    @classmethod
    def parse(cls, data: bytes) -> "Message":
        """Parse and return a Message from the given data."""
        return cls._parse(data)

    @classmethod
    def _parse(
        cls, data: bytes, start: int = 0, headers: Optional[MessageHeaders] = None
    ) -> "Message":
        """Private implementation of message parsing with additional options.

        Messages are formatted like:

        ```
        tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
        parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
        author Carlton Duffett <carlton.duffett@example.com> 1527025023 -0700
        committer Carlton Duffett <carlton.duffett@example.com> 1527025044 -0700
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

        Messages are expected to be well-formed: parser behavior is undefined for malformed
        messages.
        """

        if headers is None:
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
        value_start = space_index + 1

        while True:
            value_end = data.find(b"\n", value_start)

            # Continuation lines begin with a space. Continue collecting the value until
            # we encounter a newline NOT immediately followed by a space. When comparing
            # a single byte Python views the characters as ints, rather than bytes.
            if data[value_end + 1] != ord(" "):
                break

            # Skip the newline and the space and continue reading the value.
            value_start = value_end + 2

        # Extract the value and drop leading spaces on continuation lines.
        # Omit the trailing newline from any values too.
        value = data[space_index + 1 : value_end].replace(b"\n ", b"\n")

        # Keys may appear more than once, so we store them as lists.
        try:
            headers[key].append(value)
        except KeyError:
            headers[key] = [value]

        return cls._parse(data, start=value_end + 1, headers=headers)

    def write(self) -> bytes:
        """Write the Message's headers and text to bytes."""

        data = b""

        for key, values in self._headers.items():
            for value in values:
                # Add the leading spaces back for continuation lines, also restore
                # the trailing newline at the end of a key's value.
                data += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

        # Append message
        data = data + b"\n" + self._text + b"\n"

        return data


def _convert_str(value: Union[str, bytes]) -> str:
    """Converts the given value to a string if needed."""

    if isinstance(value, bytes):
        return value.decode()

    return value


def _convert_bytes(value: Union[str, bytes]) -> bytes:
    """Converts the given value to bytes if needed."""

    if isinstance(value, str):
        return value.encode()

    return value
