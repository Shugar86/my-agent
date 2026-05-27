"""Tests for secret redaction in log formatters."""
import logging

from core.logging_setup import RedactingFormatter


def test_redacting_formatter_masks_api_keys():
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="token sk-abcdefghijklmnopqrstuvwxyz123456",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in output
    assert "REDACTED" in output
