"""Small client for Telegram's official HTTP Bot API."""

from __future__ import annotations

import io
import json
import uuid
from collections.abc import Sequence
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

    def __post_init__(self) -> None:
        # Retain the historical two-element BaseException.args.
        RuntimeError.__init__(self, self.method, self.description)

    def __reduce__(self) -> tuple[type[TelegramApiError], tuple[Any, ...]]:
        # Rebuild all structured fields across pickle/process boundaries.
        return (
            type(self),
            (self.method, self.description, self.error_code, self.parameters, self.retry_after),
        )

    def __str__(self) -> str:
        return f"Telegram API {self.method} failed: {self.description}"


def _redact_token(value: Any, token: str) -> Any:
    """Keep Telegram's diagnostic fields without echoing the Bot API token."""
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]")
    if isinstance(value, dict):
        return {
            _redact_token(key, token): _redact_token(item, token) for key, item in value.items()
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
    if isinstance(retry_after, bool) or not isinstance(retry_after, int) or retry_after < 0:
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
            # Telegram often returns JSON with HTTP 4xx. urllib's HTTPError
            # delegates read() to the original stream, so replace *all* of
            # its read accessors after inspection to preserve the body for
            # callers handling non-Telegram failures themselves.
            try:
                body = exc.read()
            except OSError:
                raise exc
            replay = io.BytesIO(body)
            exc.fp = replay
            exc.file = replay
            exc.read = replay.read
            exc.readline = replay.readline
            exc.readlines = replay.readlines
            try:
                parsed = json.loads(body.decode("utf-8", errors="replace"))
            except ValueError:
                raise exc
            if isinstance(parsed, dict) and parsed.get("ok") is False:
                raise _api_error(method, parsed, self._token, http_status=exc.code) from exc
            raise exc
        if not isinstance(parsed, dict) or parsed.get("ok") is not True:
            raise _api_error(method, parsed, self._token)
        return parsed

    def send_message(
        self, chat_id: int, text: str, *, reply_markup: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self.call("sendMessage", payload)

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
        url: str | None = None,
        cache_time: int = 0,
    ) -> dict[str, Any]:
        """Acknowledge a callback; this does not execute its callback_data."""
        if not isinstance(callback_query_id, str) or not callback_query_id:
            raise ValueError("callback_query_id must be a non-empty string")
        if type(cache_time) is not int or cache_time < 0:
            raise ValueError("cache_time must be a non-negative integer")
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text is not None:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = True
        if url is not None:
            payload["url"] = url
        if cache_time:
            payload["cache_time"] = cache_time
        return self.call("answerCallbackQuery", payload)

    def get_updates(
        self,
        *,
        offset: int | None,
        timeout: int,
        allowed_updates: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Poll message updates by default; callback queries must be opted into."""
        if allowed_updates is None:
            requested_updates = ["message"]
        else:
            if isinstance(allowed_updates, (str, bytes)) or any(
                not isinstance(item, str) or not item for item in allowed_updates
            ):
                raise ValueError("allowed_updates must be a sequence of update type names")
            requested_updates = list(allowed_updates)
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": requested_updates}
        if offset is not None:
            payload["offset"] = offset
        result = self.call("getUpdates", payload).get("result", [])
        return result if isinstance(result, list) else []
