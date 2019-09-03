"""Message model tests."""

from pathlib import Path

import pytest

from wyag.models.message import Message, MessageAuthor, MessageHeaders


@pytest.fixture
def author() -> MessageAuthor:
    """A fake MessageAuthor, for testing."""

    return MessageAuthor(
        name="Michael Scott", email="mscott@dunder-mifflin.com", authored_at=1567452952
    )


@pytest.fixture
def headers() -> MessageHeaders:
    """Some fake MessageHeaders, for testing."""

    return {b"foo": [b"bar"], b"spam": [b"eggs"]}


@pytest.fixture
def commit_message() -> bytes:
    """A raw commit message, for testing."""

    with Path("tests/fixtures/commit_message").open("rb") as f:
        return f.read()


def test_message_author__read_author():
    """Should parse a well-formed MessageAuthor from bytes."""

    data = b"Carlton Duffett <carlton.duffett@example.com> 1567452846 +0000"

    author = MessageAuthor.parse(data)

    assert author.name == "Carlton Duffett"
    assert author.email == "carlton.duffett@example.com"
    assert author.authored_at == 1567452846
    assert author.timezone == "+0000"


def test_message_author__encode(author):
    """Should return the MessageAuthor as bytes."""

    assert author.write() == b"Michael Scott <mscott@dunder-mifflin.com> 1567452952 +0000"


def test_message__init():
    """Should correctly initialize a bare Message."""

    message = Message("Hello world!")

    assert message._text == b"Hello world!"
    assert message._headers == dict()


def test_message__init__author_and_header(author, headers):
    """Should correctly initialize a Message with the given MessageAuthor and MessageHeader."""

    message = Message("Hello world!", author=author, headers=headers)

    assert message._text == b"Hello world!"
    assert message._headers == {b"foo": [b"bar"], b"spam": [b"eggs"], b"author": [author.write()]}


def test_message__get_header__ok(headers):
    """Should return the header value as a string if it exists."""

    message = Message("Hello world!", headers=headers)

    assert message.get_header("foo") == "bar"
    assert message.get_header("spam") == "eggs"


def test_message__get_header__not_found(headers):
    """Should raise an Exception if the header key doesn't exist."""

    message = Message("Hello world!", headers=headers)

    with pytest.raises(Exception) as excinfo:
        message.get_header("title")

    assert str(excinfo.value) == "Message header 'title' not found!"


def test_message__set_header__new():
    """Should set the first value under a new header key."""

    message = Message("Hello world!")
    message.set_header("title", "My first message")

    assert message._headers[b"title"] == [b"My first message"]


def test_message__set_header__append():
    """Should append the next value to the list of existing values under the header key."""

    message = Message("Hello world!")
    message.set_header("things", "Thing One")
    message.set_header("things", "Thing Two")

    assert message._headers[b"things"] == [b"Thing One", b"Thing Two"]


def test_message__set_text():
    """Should correctly set the Message's text as bytes."""

    message = Message("Hello world!")
    message.set_text("Goodbye cruel world...")

    assert message._text == b"Goodbye cruel world..."


def test_message__get_text():
    """Should return the Message's text as a string."""

    message = Message("Hello world!")

    assert message.get_text() == "Hello world!"


def test_message__get_author__ok(author):
    """Should return the Message's MessageAuthor if it exists."""

    message = Message("Hello world!", author=author)

    got_author = message.get_author()
    assert got_author.name == "Michael Scott"


def test_message__get_author__non_default_key(author):
    """Should return the Message's MessageAuthor from a non-default header key."""

    message = Message("Hello world!")
    message.set_author(author, key="tagger")

    got_author = message.get_author(key="tagger")
    assert got_author.name == "Michael Scott"


def test_message__get_author__not_found():
    """Should raise an Exception if the Message doesn't have an author."""

    message = Message("Hello world!")

    with pytest.raises(Exception) as excinfo:
        message.get_author()

    assert str(excinfo.value) == "Message header 'author' not found!"


def test_message__get_author__malformed():
    """Should raise an Exception if the author is malformed and cannot be parsed."""

    message = Message("Hello world!", headers={b"author": [b"gibberish"]})

    with pytest.raises(Exception) as excinfo:
        message.get_author()

    assert str(excinfo.value) == "Message author is malformed!"


def test_message__parse(commit_message):
    """Should correctly parse a well-formed message."""

    message = Message.parse(commit_message)

    assert message._text == b"Initial commit.\n"

    for key in [b"tree", b"parent", b"author", b"committer", b"gpgsig"]:
        assert key in message._headers

    assert message._headers[b"tree"] == [b"29ff16c9c14e2652b22f8b78bb08a5a07930c147"]
    assert message._headers[b"parent"] == [b"206941306e8a8af65b66eaaaea388a7ae24d49a0"]
    assert message._headers[b"author"] == [
        b"Carlton Duffett <carlton.duffett@example.com> 1527025023 -0700"
    ]
    assert message._headers[b"committer"] == [
        b"Carlton Duffett <carlton.duffett@example.com> 1527025044 -0700"
    ]

    expected_gpgsig = b"""-----BEGIN PGP SIGNATURE-----
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
-----END PGP SIGNATURE-----"""

    assert message._headers[b"gpgsig"] == [expected_gpgsig]


def test_message__write(author, headers):
    """Should correctly serialize the Message as bytes."""

    headers[b"pets"] = [b"cat", b"rabbit", b"dog"]
    headers[b"haiku"] = [b"O snail\nClimb Mount Fuji,\nBut slowly, slowly!"]

    message = Message("My first commit message!", author=author, headers=headers)

    expected_bytes = b"""foo bar
spam eggs
pets cat
pets rabbit
pets dog
haiku O snail
 Climb Mount Fuji,
 But slowly, slowly!
author Michael Scott <mscott@dunder-mifflin.com> 1567452952 +0000

My first commit message!
"""

    assert message.write() == expected_bytes
