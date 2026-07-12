"""Shared, dependency-free Telegram integration primitives."""

from .access import TelegramAccessPolicy, TelegramConfigurationError
from .ids import parse_telegram_ids, require_single_telegram_id
from .messages import split_telegram_message

__all__ = [
    "TelegramAccessPolicy",
    "TelegramConfigurationError",
    "parse_telegram_ids",
    "require_single_telegram_id",
    "split_telegram_message",
]
