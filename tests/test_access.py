import pytest

from telegram_bot_core import TelegramAccessPolicy, TelegramConfigurationError


def test_access_requires_explicit_user_and_chat() -> None:
    with pytest.raises(TelegramConfigurationError):
        TelegramAccessPolicy(frozenset(), frozenset({-100}))
    with pytest.raises(TelegramConfigurationError):
        TelegramAccessPolicy(frozenset({42}), frozenset())


def test_access_policy_fails_closed() -> None:
    policy = TelegramAccessPolicy(frozenset({42}), frozenset({-100}))
    assert policy.allows(42, -100)
    assert not policy.allows(43, -100)
    assert not policy.allows(42, -200)
    assert not policy.allows("42", -100)
