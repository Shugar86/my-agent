"""Tests for Kimi Code provider helpers."""

from core.kimi_provider import (
    KIMI_CODE_BASE_URL,
    apply_kimi_headers,
    extract_message_content,
    is_kimi_code_key,
    resolve_kimi_base_url,
)


class _FakeMessage:
    def __init__(self, content=None, reasoning_content=None):
        self.content = content
        self.reasoning_content = reasoning_content


def test_is_kimi_code_key() -> None:
    assert is_kimi_code_key("sk-kimi-test")
    assert not is_kimi_code_key("sk-or-v1-test")
    assert not is_kimi_code_key(None)


def test_resolve_kimi_base_url_prefers_explicit_base() -> None:
    import os

    os.environ["KIMI_BASE_URL"] = "https://api.kimi.com/coding/v1"
    assert (
        resolve_kimi_base_url("sk-or-v1-test", "https://openrouter.ai/api/v1")
        == "https://openrouter.ai/api/v1"
    )
    del os.environ["KIMI_BASE_URL"]


def test_resolve_kimi_base_url_from_prefix() -> None:
    assert resolve_kimi_base_url("sk-kimi-abc") == KIMI_CODE_BASE_URL


def test_apply_kimi_headers() -> None:
    kwargs = apply_kimi_headers({"api_base": KIMI_CODE_BASE_URL})
    assert kwargs["extra_headers"]["User-Agent"] == "KimiCLI/1.0"


def test_extract_message_content_prefers_content() -> None:
    msg = _FakeMessage(content="hello", reasoning_content="think")
    assert extract_message_content(msg) == "hello"


def test_extract_message_content_uses_reasoning() -> None:
    msg = _FakeMessage(content="", reasoning_content="think")
    assert extract_message_content(msg) == "think"
