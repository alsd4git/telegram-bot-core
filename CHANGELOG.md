# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Structured Telegram Bot API errors with status code, response parameters, and typed `retry_after`, including JSON error bodies returned with HTTP 400/429.
- Redaction of the configured bot token from Telegram API error details.
- Opt-in `callback_query` polling and a safe callback-query parser without breaking message-only callers.
- `answer_callback_query()`, optional `send_message(reply_markup=...)`, and a validated inline callback keyboard helper.

## [0.1.0] - 2026-08-23

### Added

- Reusable Telegram Bot API transport and command primitives.
- Fail-closed authorization helpers and shared message utilities.
- Cross-platform test coverage for supported Python versions.

[Unreleased]: https://github.com/alsd4git/telegram-bot-core/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alsd4git/telegram-bot-core/releases/tag/v0.1.0
