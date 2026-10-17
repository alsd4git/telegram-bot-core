"""Opt-in Telegram callback-query parsing and inline keyboard helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramCallbackQuery:
    """An opaque callback from one Telegram getUpdates entry.

    Authorization and interpretation of data remain the caller's responsibility.
    chat_id is None for inline-message callbacks without a chat context.
    """

    id: str
    user_id: int
    chat_id: int | None
    message_id: int | None
    data: str | None
    inline_message_id: str | None = None


def parse_telegram_callback_query(update: object) -> TelegramCallbackQuery | None:
    """Parse a callback_query update without interpreting or executing its data."""
    if not isinstance(update, dict):
        return None
    callback = update.get("callback_query")
    if not isinstance(callback, dict):
        return None

    query_id = callback.get("id")
    sender = callback.get("from")
    if not isinstance(query_id, str) or not query_id or not isinstance(sender, dict):
        return None
    user_id = sender.get("id")
    if type(user_id) is not int or user_id <= 0:
        return None

    inline_message_id = callback.get("inline_message_id")
    if inline_message_id is not None and (
        not isinstance(inline_message_id, str) or not inline_message_id
    ):
        return None

    chat_id = None
    message_id = None
    message = callback.get("message")
    if message is not None:
        if not isinstance(message, dict) or not isinstance(message.get("chat"), dict):
            return None
        chat_id = message["chat"].get("id")
        message_id = message.get("message_id")
        # An inaccessible message may legitimately have message_id=0.
        if type(chat_id) is not int or chat_id == 0:
            return None
        if type(message_id) is not int or message_id < 0:
            return None
    elif inline_message_id is None:
        return None

    data = callback.get("data")
    if data is not None and not isinstance(data, str):
        return None

    return TelegramCallbackQuery(
        id=query_id,
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        data=data,
        inline_message_id=inline_message_id,
    )


def inline_keyboard(
    rows: Sequence[Sequence[tuple[str, str]]],
) -> dict[str, list[list[dict[str, str]]]]:
    """Build a callback-only inline keyboard with Telegram's 64-byte data limit."""
    if isinstance(rows, (str, bytes)):
        raise ValueError("inline keyboard rows must be a sequence of rows")
    keyboard: list[list[dict[str, str]]] = []
    for row in rows:
        if isinstance(row, (str, bytes)):
            raise ValueError("inline keyboard row must contain buttons")
        buttons: list[dict[str, str]] = []
        for button in row:
            if (
                not isinstance(button, Sequence)
                or isinstance(button, (str, bytes))
                or len(button) != 2
            ):
                raise ValueError("inline callback button must contain text and callback data")
            label, data = button
            if not isinstance(label, str) or not label.strip():
                raise ValueError("inline callback button text must be non-empty")
            if not isinstance(data, str) or not 1 <= len(data.encode("utf-8")) <= 64:
                raise ValueError("inline callback data must contain 1 to 64 UTF-8 bytes")
            buttons.append({"text": label, "callback_data": data})
        if not buttons:
            raise ValueError("inline keyboard rows must not be empty")
        keyboard.append(buttons)
    if not keyboard:
        raise ValueError("inline keyboard must contain at least one row")
    return {"inline_keyboard": keyboard}
