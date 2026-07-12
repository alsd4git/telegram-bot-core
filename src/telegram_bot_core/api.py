"""Small client for Telegram's official HTTP Bot API."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
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
        return self._request_json(
            method,
            data,
            headers={"Content-Type": "application/json"},
        )

    def send_document(
        self,
        chat_id: int,
        caption: str,
        document_path: Path,
        *,
        content_type: str = "text/plain; charset=utf-8",
    ) -> dict[str, Any]:
        """Upload one local file through Telegram's ``sendDocument`` method."""
        boundary = uuid.uuid4().hex
        crlf = b"\r\n"
        body = bytearray()

        def add_field(name: str, value: str) -> None:
            body.extend(f"--{boundary}".encode())
            body.extend(crlf)
            body.extend(f'Content-Disposition: form-data; name="{name}"'.encode())
            body.extend(crlf)
            body.extend(crlf)
            body.extend(value.encode())
            body.extend(crlf)

        add_field("chat_id", str(chat_id))
        add_field("caption", caption[:1024])
        body.extend(f"--{boundary}".encode())
        body.extend(crlf)
        body.extend(
            (
                'Content-Disposition: form-data; name="document"; '
                f'filename="{document_path.name}"'
            ).encode()
        )
        body.extend(crlf)
        body.extend(f"Content-Type: {content_type}".encode())
        body.extend(crlf)
        body.extend(crlf)
        body.extend(document_path.read_bytes())
        body.extend(crlf)
        body.extend(f"--{boundary}--".encode())
        body.extend(crlf)
        return self._request_json(
            "sendDocument",
            bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def _request_json(self, method: str, data: bytes, *, headers: dict[str, str]) -> dict[str, Any]:
        req = request.Request(
            f"https://api.telegram.org/bot{self._token}/{method}",
            data=data,
            headers=headers,
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
