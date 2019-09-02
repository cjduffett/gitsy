"""Message model tests."""

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
