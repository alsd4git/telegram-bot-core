from __future__ import annotations

import io
import json
from pathlib import Path
from urllib import error
from unittest import mock

import pytest

from telegram_bot_core import TelegramApiError, TelegramBotApi
from telegram_bot_core import api as api_module


class Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_call_posts_json_to_the_official_endpoint() -> None:
    with mock.patch.object(
        api_module.request, "urlopen", return_value=Response({"ok": True, "result": {}})
    ) as urlopen:
        TelegramBotApi("TOKEN").send_message(123, "hello")

    req = urlopen.call_args.args[0]
    assert req.full_url == "https://api.telegram.org/botTOKEN/sendMessage"
    assert json.loads(req.data) == {"chat_id": 123, "text": "hello"}


def test_call_raises_on_an_api_error() -> None:
    with mock.patch.object(
        api_module.request,
        "urlopen",
        return_value=Response({"ok": False, "description": "bad request"}),
    ):
        with pytest.raises(TelegramApiError, match="sendMessage"):
            TelegramBotApi("TOKEN").send_message(123, "hello")


def test_send_document_uses_multipart_form_data(tmp_path: Path) -> None:
    document = tmp_path / "report.txt"
    document.write_text("details", encoding="utf-8")
    with mock.patch.object(
        api_module.request, "urlopen", return_value=Response({"ok": True, "result": {}})
    ) as urlopen:
        TelegramBotApi("TOKEN").send_document(123, "summary", document)

    req = urlopen.call_args.args[0]
    assert req.full_url == "https://api.telegram.org/botTOKEN/sendDocument"
    assert b'name="chat_id"' in req.data
    assert b"details" in req.data


def test_structured_api_error_retains_code_and_safe_parameters() -> None:
    response = {
        "ok": False,
        "error_code": 400,
        "description": "Bad Request: bot TOKEN rejected",
        "parameters": {"migrate_to_chat_id": -100123, "debug": {"note": "TOKEN"}},
    }
    with mock.patch.object(api_module.request, "urlopen", return_value=Response(response)):
        with pytest.raises(TelegramApiError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")

    api_error = caught.value
    assert isinstance(api_error, RuntimeError)
    assert api_error.method == "sendMessage"
    assert api_error.error_code == 400
    assert api_error.description == "Bad Request: bot [REDACTED] rejected"
    assert api_error.parameters == {
        "migrate_to_chat_id": -100123,
        "debug": {"note": "[REDACTED]"},
    }
    assert api_error.retry_after is None
    assert "TOKEN" not in str(api_error)
    assert "TOKEN" not in repr(api_error)


def test_http_rate_limit_is_structured_without_automatic_retry() -> None:
    body = json.dumps(
        {
            "ok": False,
            "error_code": 429,
            "description": "Too Many Requests: retry after 7",
            "parameters": {"retry_after": 7},
        }
    ).encode()
    http_error = error.HTTPError(
        "https://api.telegram.org/botTOKEN/sendMessage",
        429,
        "Too Many Requests",
        {},
        io.BytesIO(body),
    )
    with mock.patch.object(
        api_module.request, "urlopen", side_effect=http_error
    ) as urlopen:
        with pytest.raises(TelegramApiError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")

    assert urlopen.call_count == 1
    assert caught.value.error_code == 429
    assert caught.value.retry_after == 7
    assert caught.value.parameters == {"retry_after": 7}
    assert "TOKEN" not in str(caught.value)


def test_http_api_error_uses_status_when_payload_has_no_error_code() -> None:
    http_error = error.HTTPError(
        "https://api.telegram.org/botTOKEN/sendMessage",
        403,
        "Forbidden",
        {},
        io.BytesIO(b'{"ok": false, "description": "Forbidden: bot was blocked"}'),
    )
    with mock.patch.object(api_module.request, "urlopen", side_effect=http_error):
        with pytest.raises(TelegramApiError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")

    assert caught.value.error_code == 403
    assert caught.value.retry_after is None


@pytest.mark.parametrize("value", [True, "7", -1])
def test_invalid_retry_after_is_ignored(value: object) -> None:
    with mock.patch.object(
        api_module.request,
        "urlopen",
        return_value=Response(
            {"ok": False, "error_code": 429, "parameters": {"retry_after": value}}
        ),
    ):
        with pytest.raises(TelegramApiError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")

    assert caught.value.error_code == 429
    assert caught.value.retry_after is None


def test_non_json_http_errors_remain_urllib_http_errors() -> None:
    http_error = error.HTTPError(
        "https://api.telegram.org/botTOKEN/sendMessage",
        502,
        "Bad Gateway",
        {},
        io.BytesIO(b"not JSON"),
    )
    with mock.patch.object(api_module.request, "urlopen", side_effect=http_error):
        with pytest.raises(error.HTTPError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")

    assert caught.value.code == 502


def test_invalid_success_payload_is_a_structured_api_error() -> None:
    with mock.patch.object(api_module.request, "urlopen", return_value=Response([])):
        with pytest.raises(TelegramApiError) as caught:
            TelegramBotApi("TOKEN").send_message(123, "hello")
    assert caught.value.error_code is None
    assert caught.value.description == "invalid API response"


def test_legacy_api_error_constructor_remains_compatible() -> None:
    api_error = TelegramApiError("sendMessage", "bad request")
    assert api_error.error_code is None
    assert api_error.parameters is None
    assert api_error.retry_after is None
    assert str(api_error) == "Telegram API sendMessage failed: bad request"
