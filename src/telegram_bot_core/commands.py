"""Safe parsing for simple Telegram slash commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramCommand:
    name: str
    arguments: tuple[str, ...]


def parse_telegram_command(text: object) -> TelegramCommand | None:
    if not isinstance(text, str):
        return None
    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        return None
    name = parts[0][1:].split("@", 1)[0].lower()
    if not name or not name.replace("_", "").isalnum():
        return None
    return TelegramCommand(name, tuple(parts[1:]))
