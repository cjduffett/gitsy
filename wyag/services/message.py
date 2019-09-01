"""Commit and Tag message services."""

from typing import Optional

from ..models.message import Message, MessageHeaders


def read_message(data: bytes, start: int = 0, headers: Optional[MessageHeaders] = None) -> Message:
    """Read a Git Commit or Tag message's headers and text.

    Commits and Tags are formatted like:

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
    an additional "continuation space" (see gpgsig as an example of that).
    """

    if not headers:
        headers = dict()

    # Find the next space and newline, deliniating another key-value pair.
    space_index = data.find(b" ", start)
    newline_index = data.find(b"\n", start)

    # If a space appears before a newline, we have a keyword.

    # If a newline appears first (before a space), or there's no space at all (-1), we
    # assume a blank line. A blank line means the remainder of the data is the message.
    if space_index < 0 or newline_index < space_index:
        return Message(headers=headers, text=data[start + 1 :])

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

    return read_message(data, start=end + 1, headers=headers)


def write_message(message: Message) -> bytes:
    """Write a Message's headers and text to bytes."""

    data = b""

    for key, values in message.headers.items():
        # Lists will be serialized on adjacent lines
        for value in values:
            # Add the leading spaces back for continuation lines.
            data += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

    # Append message
    data = data + b"\n" + message.text

    return data
