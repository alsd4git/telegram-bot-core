"""Shared, dependency-free Telegram integration primitives."""

from .access import TelegramAccessPolicy, TelegramConfigurationError
from .api import TelegramApiError, TelegramBotApi
from .callbacks import TelegramCallbackQuery, inline_keyboard, parse_telegram_callback_query
from .commands import TelegramCommand, parse_telegram_command
from .ids import parse_telegram_ids, require_single_telegram_id
from .messages import split_telegram_message

__all__ = [
    "TelegramAccessPolicy",
    "TelegramApiError",
    "TelegramBotApi",
    "TelegramCallbackQuery",
    "TelegramCommand",
    "TelegramConfigurationError",
    "inline_keyboard",
    "parse_telegram_callback_query",
    "parse_telegram_ids",
    "parse_telegram_command",
    "require_single_telegram_id",
    "split_telegram_message",
]
