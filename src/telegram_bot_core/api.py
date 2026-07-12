"""Small client for Telegram's official HTTP Bot API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request


@dataclass(frozen=True, slots=True)
class TelegramApiError(RuntimeError):
    """An unsuccessful response from Telegram's Bot API."""

    method: str
    description: str

    def __str__(self) -> str:
        return f"Telegram API {self.method} failed: {self.description}"


class TelegramBotApi:
    """Synchronous client with explicit, no-retry semantics for mutating calls."""

    def __init__(self, token: str, *, timeout: int = 30) -> None:
        if not token.strip():
            raise ValueError("Telegram bot token must not be empty")
        if timeout <= 0:
            raise ValueError("Telegram API timeout must be positive")
        self._token = token
        self._timeout = timeout

    def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode()
        req = request.Request(
            f"https://api.telegram.org/bot{self._token}/{method}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self._timeout) as response:
            parsed = json.loads(response.read().decode("utf-8", errors="replace"))
        if not isinstance(parsed, dict) or parsed.get("ok") is not True:
            description = (
                parsed.get("description", "invalid API response")
                if isinstance(parsed, dict)
                else "invalid API response"
            )
            raise TelegramApiError(method, str(description))
        return parsed

    def send_message(self, chat_id: int, text: str) -> dict[str, Any]:
        return self.call("sendMessage", {"chat_id": chat_id, "text": text})

    def get_updates(self, *, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        result = self.call("getUpdates", payload).get("result", [])
        return result if isinstance(result, list) else []
