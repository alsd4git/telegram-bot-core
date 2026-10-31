# Telegram Bot Core

[![CI](https://github.com/alsd4git/telegram-bot-core/actions/workflows/ci.yml/badge.svg)](https://github.com/alsd4git/telegram-bot-core/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/alsd4git/telegram-bot-core)](https://github.com/alsd4git/telegram-bot-core/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Small, dependency-free building blocks for personal Telegram bot automations.

The package provides a synchronous Bot API client, fail-closed access policies,
command parsing, Telegram ID validation, and safe message splitting. It is meant
for scripts that do not need a full bot framework.

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) for development and source installs

## Installation

The package is currently distributed through GitHub releases, not PyPI:

```bash
uv add "telegram-bot-core @ git+https://github.com/alsd4git/telegram-bot-core.git@v0.2.0"
```

Applications in this account use the Git tag as their dependency reference. A
tag gives the shared API a stable version while keeping publication separate
from PyPI.

## Example

```python
from telegram_bot_core import (
    TelegramAccessPolicy,
    TelegramBotApi,
    parse_telegram_command,
    parse_telegram_ids,
)

allowed_users = parse_telegram_ids("123456,789012", setting_name="ALLOWED_USERS")
policy = TelegramAccessPolicy(allowed_user_ids=allowed_users, allowed_chat_ids={-1001234})

command = parse_telegram_command("/status verbose")
if command and policy.allows_user(123456) and policy.allows_chat(-1001234):
    TelegramBotApi("BOT_TOKEN").send_message(-1001234, f"command: {command.name}")
```

Never commit bot tokens or place them directly in logs. Load them from an
environment file or secret store owned by the application.

## Public API

- `TelegramBotApi` calls JSON Bot API methods and uploads local documents with
  `sendDocument`. Mutating calls do not retry automatically.
- `TelegramApiError` exposes `method`, `description`, `error_code`, `parameters`, and an optional integer `retry_after` for Bot API errors, including Telegram JSON bodies returned with HTTP 400/429. Diagnostic fields redact the configured bot token; unrelated non-JSON HTTP failures remain urllib errors.
- `TelegramAccessPolicy` authorizes users and chats. Missing allowlists fail
  closed instead of granting access.
- `parse_telegram_ids()` accepts JSON lists, comma-separated strings, and native
  sequences.
- `require_single_telegram_id()` validates one numeric chat ID, including
  negative group and channel IDs.
- `parse_telegram_command()` parses slash commands, optional bot suffixes, and
  positional arguments.
- `split_telegram_message()` splits text on line boundaries without exceeding
  the caller-provided message limit.
- `TelegramBotApi.get_updates()` defaults to message-only updates and accepts
  an optional `allowed_updates` sequence to opt into `callback_query` events.
- `parse_telegram_callback_query()` returns the callback ID, sender/chat/message
  IDs and opaque callback data; it never interprets or executes the data.
- `inline_keyboard()` builds callback-only markup and validates Telegram's
  1–64 byte UTF-8 `callback_data` constraint.
- `TelegramBotApi.send_message(..., reply_markup=...)` can send inline buttons;
  `TelegramBotApi.answer_callback_query()` acknowledges an interaction.

The client uses Python's standard library and has no runtime dependencies. It is
synchronous and intentionally small. Applications remain responsible for retry
policy (including honoring `TelegramApiError.retry_after`), logging, persistence,
scheduling, and secret management. The client never retries automatically.

## Callback queries (opt-in)

Existing bots still receive only message updates. Interactive bots can request
callback updates explicitly:

```python
from telegram_bot_core import (
    TelegramAccessPolicy,
    TelegramBotApi,
    inline_keyboard,
    parse_telegram_callback_query,
)

api = TelegramBotApi("BOT_TOKEN")
policy = TelegramAccessPolicy(
    allowed_user_ids=frozenset({123456}),
    allowed_chat_ids=frozenset({-1001234}),
)
api.send_message(
    -1001234,
    "Choose an action",
    reply_markup=inline_keyboard([[("Refresh", "refresh"), ("Details", "details")]]),
)

updates = api.get_updates(
    offset=None, timeout=30, allowed_updates=("message", "callback_query")
)
for update in updates:
    callback = parse_telegram_callback_query(update)
    if callback is None:
        continue
    # Inline callbacks may have no chat context; enforce your access policy.
    if callback.chat_id is None or not policy.allows(callback.user_id, callback.chat_id):
        continue
    # Interpret callback.data only after authorization; never execute it as code.
    api.answer_callback_query(callback.id, text="Received")
```

The caller still owns offset persistence, authorization, callback-data routing,
confirmation for sensitive operations, and retry policy. A callback's `data`
value is untrusted user input and never triggers any action inside the core.
The inline-keyboard helper supports callback-data buttons only (not URL/login
buttons).

## Development

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```

CI runs tests on Linux, macOS, and Windows with Python 3.11–3.15, plus Python
3.10 on Linux. Formatting and lint run once on Linux with Python 3.15.

## Releases

See [CHANGELOG.md](CHANGELOG.md) for user-visible changes. A `v*` tag must match
the version in `pyproject.toml`; the release workflow builds and validates the
wheel and source archive before creating a GitHub release.

## License

MIT. See [LICENSE](LICENSE).
