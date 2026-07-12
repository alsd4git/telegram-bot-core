from telegram_bot_core import parse_telegram_command


def test_parse_command_handles_bot_suffix_and_arguments() -> None:
    command = parse_telegram_command("/trip@my_bot BLQ IAS 2026-08-01 2026-08-08")
    assert command is not None
    assert command.name == "trip"
    assert command.arguments == ("BLQ", "IAS", "2026-08-01", "2026-08-08")


def test_parse_command_rejects_non_commands() -> None:
    assert parse_telegram_command("hello") is None
    assert parse_telegram_command("/") is None
