from __future__ import annotations

import json
from pathlib import Path
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
