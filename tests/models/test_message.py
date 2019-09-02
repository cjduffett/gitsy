"""Message model tests."""

from wyag.models.message import Message, MessageAuthor, MessageHeaders


def test_message_author__read_author():
    """Should parse a well-formed MessageAuthor from bytes."""

    data = b"Carlton Duffett <carlton.duffett@example.com> 1567452846 +0000"

    author = MessageAuthor.parse(data)

    assert author.name == "Carlton Duffett"
    assert author.email == "carlton.duffett@example.com"
    assert author.authored_at == 1567452846
    assert author.timezone == "+0000"


def test_message_author__encode():
    """Should return the MessageAuthor as bytes."""

    author = MessageAuthor(
        name="Michael Scott", email="mscott@dunder-mifflin.com", authored_at=1567452952
    )

    assert author.write() == b"Michael Scott <mscott@dunder-mifflin.com> 1567452952 +0000"
