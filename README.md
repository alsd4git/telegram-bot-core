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
uv add "telegram-bot-core @ git+https://github.com/alsd4git/telegram-bot-core.git@v0.1.0"
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

allowed_users = parse_telegram_ids("123456,789012", setting="ALLOWED_USERS")
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
- `TelegramApiError` reports unsuccessful Telegram responses.
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

The client uses Python's standard library and has no runtime dependencies. It is
synchronous and intentionally small. Applications remain responsible for retry
policy, logging, persistence, scheduling, and secret management.

## Development

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```

CI runs the suite on Linux, macOS, and Windows with the oldest and newest
supported Python versions.

## Releases

See [CHANGELOG.md](CHANGELOG.md) for user-visible changes. A `v*` tag must match
the version in `pyproject.toml`; the release workflow builds and validates the
wheel and source archive before creating a GitHub release.

## License

MIT. See [LICENSE](LICENSE).
