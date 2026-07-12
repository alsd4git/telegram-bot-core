import pytest

from telegram_bot_core import split_telegram_message


def test_split_message_preserves_content_and_limit() -> None:
    message = "first line\nsecond line\nthird"
    chunks = split_telegram_message(message, limit=10)
    assert "".join(chunks) == message
    assert all(len(chunk) <= 10 for chunk in chunks)


def test_split_message_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        split_telegram_message("hello", limit=0)
