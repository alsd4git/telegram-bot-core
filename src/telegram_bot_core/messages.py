"""Text helpers for Telegram message limits."""

from __future__ import annotations


def split_telegram_message(message: str, *, limit: int) -> list[str]:
    """Split text on line boundaries while preserving every character."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if not message:
        return []

    chunks: list[str] = []
    current = ""
    for line in message.splitlines(keepends=True):
        remaining = line
        while remaining:
            available = limit - len(current)
            current += remaining[:available]
            remaining = remaining[available:]
            if len(current) == limit:
                chunks.append(current)
                current = ""
    if current:
        chunks.append(current)
    return chunks
