"""Small client for Telegram's official HTTP Bot API."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


@dataclass(frozen=True, slots=True)
class TelegramApiError(RuntimeError):
    """A Telegram Bot API rejection with structured, token-redacted details."""

    method: str
    description: str
    error_code: int | None = None
    parameters: dict[str, Any] | None = None
    retry_after: int | None = None

    def __str__(self) -> str:
        return f"Telegram API {self.method} failed: {self.description}"


def _redact_token(value: Any, token: str) -> Any:
    """Keep Telegram's diagnostic fields without echoing the Bot API token."""
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]")
    if isinstance(value, dict):
        return {
            _redact_token(key, token): _redact_token(item, token)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_token(item, token) for item in value]
    return value


def _api_error(
    method: str,
    payload: object,
    token: str,
    *,
    http_status: int | None = None,
) -> TelegramApiError:
    if not isinstance(payload, dict):
        return TelegramApiError(method, "invalid API response", error_code=http_status)

    description = payload.get("description")
    if not isinstance(description, str):
        description = "invalid API response"
    error_code = payload.get("error_code")
    if isinstance(error_code, bool) or not isinstance(error_code, int):
        error_code = http_status

    raw_parameters = payload.get("parameters")
    parameters = _redact_token(raw_parameters, token) if isinstance(raw_parameters, dict) else None
    retry_after = parameters.get("retry_after") if parameters is not None else None
    if (
        isinstance(retry_after, bool)
        or not isinstance(retry_after, int)
        or retry_after < 0
    ):
        retry_after = None

    return TelegramApiError(
        method=method,
        description=_redact_token(description, token),
        error_code=error_code,
        parameters=parameters,
        retry_after=retry_after,
    )


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
                f'Content-Disposition: form-data; name="document"; filename="{document_path.name}"'
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
        try:
            with request.urlopen(req, timeout=self._timeout) as response:
                parsed = json.loads(response.read().decode("utf-8", errors="replace"))
        except error.HTTPError as exc:
            # Telegram normally delivers Bot API errors with a non-2xx HTTP
            # status. Preserve urllib's error for non-JSON or unrelated replies.
            try:
                parsed = json.loads(exc.read().decode("utf-8", errors="replace"))
            except (OSError, ValueError):
                raise exc
            if isinstance(parsed, dict) and parsed.get("ok") is False:
                raise _api_error(method, parsed, self._token, http_status=exc.code) from exc
            raise exc
        if not isinstance(parsed, dict) or parsed.get("ok") is not True:
            raise _api_error(method, parsed, self._token)
        return parsed

    def send_message(self, chat_id: int, text: str) -> dict[str, Any]:
        return self.call("sendMessage", {"chat_id": chat_id, "text": text})

    def get_updates(self, *, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        result = self.call("getUpdates", payload).get("result", [])
        return result if isinstance(result, list) else []
