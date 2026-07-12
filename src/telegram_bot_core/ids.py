"""Telegram numeric-ID parsing and validation."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from .access import TelegramConfigurationError


def _values(value: object, *, setting_name: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return []
        try:
            decoded = json.loads(normalized)
        except json.JSONDecodeError:
            return [item.strip() for item in normalized.split(",") if item.strip()]
        if isinstance(decoded, list):
            return decoded
        return [decoded]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return list(value)
    return [value]


def parse_telegram_ids(
    value: object,
    *,
    setting_name: str,
    require_non_empty: bool = False,
    positive_only: bool = False,
) -> frozenset[int]:
    """Parse Telegram IDs from JSON, CSV, or a native sequence.

    User IDs are positive; chat IDs may be negative for groups and channels.
    Invalid input is rejected instead of silently widening or narrowing access.
    """
    parsed_ids: set[int] = set()
    for item in _values(value, setting_name=setting_name):
        if isinstance(item, bool):
            raise TelegramConfigurationError(f"{setting_name} must contain numeric Telegram IDs")
        try:
            identifier = int(str(item).strip())
        except (TypeError, ValueError) as exc:
            raise TelegramConfigurationError(
                f"{setting_name} must contain numeric Telegram IDs"
            ) from exc
        if positive_only and identifier <= 0:
            raise TelegramConfigurationError(
                f"{setting_name} must contain positive Telegram user IDs"
            )
        if not positive_only and identifier == 0:
            raise TelegramConfigurationError(f"{setting_name} cannot contain zero")
        parsed_ids.add(identifier)

    if require_non_empty and not parsed_ids:
        raise TelegramConfigurationError(f"{setting_name} is required")
    return frozenset(parsed_ids)


def require_single_telegram_id(value: object, *, setting_name: str) -> int:
    """Validate and return one configured Telegram chat ID."""
    identifiers = parse_telegram_ids(value, setting_name=setting_name, require_non_empty=True)
    if len(identifiers) != 1:
        raise TelegramConfigurationError(f"{setting_name} must contain exactly one Telegram ID")
    return next(iter(identifiers))
