import pytest

from telegram_bot_core import (
    TelegramConfigurationError,
    parse_telegram_ids,
    require_single_telegram_id,
)


def test_parse_ids_accepts_json_csv_and_sequences() -> None:
    assert parse_telegram_ids("[1, 2]", setting_name="USERS", positive_only=True) == frozenset(
        {1, 2}
    )
    assert parse_telegram_ids("-100, 200", setting_name="CHATS") == frozenset({-100, 200})
    assert parse_telegram_ids([1, "2"], setting_name="USERS", positive_only=True) == frozenset(
        {1, 2}
    )


@pytest.mark.parametrize("value", ["alice", "[true]", "0", "-1"])
def test_parse_ids_rejects_invalid_users(value: object) -> None:
    with pytest.raises(TelegramConfigurationError):
        parse_telegram_ids(value, setting_name="USERS", positive_only=True)


def test_single_chat_id_allows_negative_group_id() -> None:
    assert require_single_telegram_id("-100123", setting_name="CHAT") == -100123
    with pytest.raises(TelegramConfigurationError):
        require_single_telegram_id("1,2", setting_name="CHAT")
