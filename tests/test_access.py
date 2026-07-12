import pytest

from telegram_bot_core import TelegramAccessPolicy, TelegramConfigurationError


def test_access_requires_explicit_user() -> None:
    with pytest.raises(TelegramConfigurationError):
        TelegramAccessPolicy(frozenset(), frozenset({-100}))


def test_access_policy_fails_closed() -> None:
    policy = TelegramAccessPolicy(frozenset({42}), frozenset({-100}))
    assert policy.allows(42, -100)
    assert not policy.allows(43, -100)
    assert not policy.allows(42, -200)
    assert not policy.allows("42", -100)


def test_access_policy_can_be_scoped_to_users_only() -> None:
    policy = TelegramAccessPolicy(frozenset({42}))
    assert policy.allows(42, -100)
    assert not policy.allows(43, -100)
