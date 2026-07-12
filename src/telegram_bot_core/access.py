"""Fail-closed authorization for Telegram updates."""

from __future__ import annotations

from dataclasses import dataclass


class TelegramConfigurationError(ValueError):
    """Raised when Telegram integration configuration is invalid."""


@dataclass(frozen=True, slots=True)
class TelegramAccessPolicy:
    """Authorize a Telegram update only when both configured scopes allow it."""

    allowed_user_ids: frozenset[int]
    allowed_chat_ids: frozenset[int]

    def __post_init__(self) -> None:
        if not self.allowed_user_ids:
            raise TelegramConfigurationError("at least one allowed Telegram user ID is required")
        if not self.allowed_chat_ids:
            raise TelegramConfigurationError("at least one allowed Telegram chat ID is required")

    def allows_user(self, user_id: object) -> bool:
        return (
            isinstance(user_id, int)
            and not isinstance(user_id, bool)
            and user_id in self.allowed_user_ids
        )

    def allows_chat(self, chat_id: object) -> bool:
        return (
            isinstance(chat_id, int)
            and not isinstance(chat_id, bool)
            and chat_id in self.allowed_chat_ids
        )

    def allows(self, user_id: object, chat_id: object) -> bool:
        """Return true only when the sender and chat are both explicitly allowed."""
        return self.allows_user(user_id) and self.allows_chat(chat_id)
