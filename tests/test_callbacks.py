"""Callback queries are opt-in, untrusted data; callers own authorization."""

from __future__ import annotations

import pytest

from telegram_bot_core import (
    TelegramAccessPolicy,
    TelegramCallbackQuery,
    inline_keyboard,
    parse_telegram_callback_query,
)


def callback_update() -> dict[str, object]:
    return {
        "update_id": 100,
        "callback_query": {
            "id": "query-123",
            "from": {"id": 42},
            "message": {
                "message_id": 101,
                "chat": {"id": -100123, "type": "supergroup"},
            },
            "data": "remote:restart",
        },
    }


def test_parse_callback_query_exposes_untrusted_data_and_numeric_ids() -> None:
    query = parse_telegram_callback_query(callback_update())

    assert isinstance(query, TelegramCallbackQuery)
    assert query.id == "query-123"
    assert query.user_id == 42
    assert query.chat_id == -100123
    assert query.message_id == 101
    assert query.data == "remote:restart"
    assert query.inline_message_id is None

    policy = TelegramAccessPolicy(frozenset({42}), frozenset({-100123}))
    assert policy.allows(query.user_id, query.chat_id)
    assert not TelegramAccessPolicy(frozenset({43}), frozenset({-100123})).allows(
        query.user_id, query.chat_id
    )


def test_parse_inline_callback_without_chat_context() -> None:
    update = {
        "callback_query": {
            "id": "inline-query",
            "from": {"id": 42},
            "inline_message_id": "inline-msg",
            "data": "details",
        }
    }
    query = parse_telegram_callback_query(update)

    assert query is not None
    assert query.id == "inline-query"
    assert query.chat_id is None
    assert query.message_id is None
    assert query.inline_message_id == "inline-msg"
    assert query.data == "details"
    # Chat-scoped access must not silently fall back to a user-only decision.
    policy = TelegramAccessPolicy(frozenset({42}), frozenset({-100123}))
    assert not policy.allows(query.user_id, query.chat_id)


def test_parse_inaccessible_message_keeps_zero_message_id() -> None:
    update = callback_update()
    update["callback_query"]["message"]["message_id"] = 0

    parsed = parse_telegram_callback_query(update)
    assert parsed is not None
    assert parsed.message_id == 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda update: update.pop("callback_query"),
        lambda update: update["callback_query"].update(id=""),
        lambda update: update["callback_query"]["from"].update(id=True),
        lambda update: update["callback_query"]["from"].update(id=-1),
        lambda update: update["callback_query"]["message"]["chat"].update(id="42"),
        lambda update: update["callback_query"]["message"].update(message_id=True),
        lambda update: update["callback_query"].update(data={"command": "/restart"}),
        lambda update: update["callback_query"].update(message="not a message"),
    ],
)
def test_parse_malformed_callback_query_returns_none(mutation) -> None:
    update = callback_update()
    mutation(update)
    assert parse_telegram_callback_query(update) is None


def test_parse_rejects_callback_without_message_or_inline_message_id() -> None:
    update = callback_update()
    del update["callback_query"]["message"]
    assert parse_telegram_callback_query(update) is None
    assert parse_telegram_callback_query("callback_query") is None


def test_inline_keyboard_builds_callback_only_reply_markup() -> None:
    markup = inline_keyboard(
        [[("Aggiorna", "refresh"), ("Dettagli", "details")], [("Restart", "remote:restart")]]
    )

    assert markup == {
        "inline_keyboard": [
            [
                {"text": "Aggiorna", "callback_data": "refresh"},
                {"text": "Dettagli", "callback_data": "details"},
            ],
            [{"text": "Restart", "callback_data": "remote:restart"}],
        ]
    }


def test_inline_keyboard_counts_utf8_bytes_in_callback_data() -> None:
    assert inline_keyboard([[("OK", "é" * 32)]])
    with pytest.raises(ValueError, match="64 UTF-8 bytes"):
        inline_keyboard([[("Too long", "é" * 33)]])


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [[]],
        [[("", "refresh")]],
        [[("label", "")]],
        [[("label", "x" * 65)]],
        [["not-a-button"]],
        ["not-a-row"],
    ],
)
def test_inline_keyboard_rejects_invalid_buttons(rows) -> None:
    with pytest.raises(ValueError):
        inline_keyboard(rows)
