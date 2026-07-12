"""Fail-closed authorization for Telegram updates."""

from __future__ import annotations

from dataclasses import dataclass


class TelegramConfigurationError(ValueError):
    """Raised when Telegram integration configuration is invalid."""


@dataclass(frozen=True, slots=True)
class TelegramAccessPolicy:
    """Authorize Telegram updates using a required user scope and optional chat scope.

    A bot with no configured chat IDs is deliberately user-scoped rather than
    open to every sender: the user allow-list is always mandatory.  Bots that
    need an additional chat boundary simply provide ``allowed_chat_ids``.
    """

    allowed_user_ids: frozenset[int]
    allowed_chat_ids: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if not self.allowed_user_ids:
            raise TelegramConfigurationError("at least one allowed Telegram user ID is required")

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
        """Return true only for an allowed user and, when set, an allowed chat."""
        return self.allows_user(user_id) and (
            not self.allowed_chat_ids or self.allows_chat(chat_id)
        )
