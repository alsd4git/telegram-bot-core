# Telegram Bot Core

Small, dependency-free primitives shared by personal Telegram automations.

The package intentionally does not implement a Telegram HTTP client or depend on
a bot framework. Applications keep their existing transports while sharing the
security-sensitive parts: parsing numeric IDs, fail-closed access policies, and
safe message splitting.

## API

- `parse_telegram_ids()` parses JSON lists, comma-separated strings, or native
  sequences into validated ID sets.
- `require_single_telegram_id()` validates a single chat ID, including negative
  group and channel IDs.
- `TelegramAccessPolicy` authorizes users and chats with an explicit
  fail-closed policy.
- `split_telegram_message()` splits text on line boundaries without exceeding a
  caller-provided Telegram message limit.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
```
