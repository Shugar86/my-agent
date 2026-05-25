"""Kimi Code / Moonshot provider helpers for LLMGateway."""

from __future__ import annotations

import os
from typing import Any

KIMI_CODE_BASE_URL = "https://api.kimi.com/coding/v1"
KIMI_MOONSHOT_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_CODE_USER_AGENT = "KimiCLI/1.0"
KIMI_CODE_MODEL = "openai/kimi-for-coding"


def is_kimi_code_key(api_key: str | None) -> bool:
    """Return True if the key is a Kimi Code platform key (sk-kimi-...)."""
    return bool(api_key and api_key.startswith("sk-kimi-"))


def resolve_kimi_base_url(api_key: str | None, base_url: str | None = None) -> str | None:
    """Pick the correct Kimi base URL from env override or key prefix."""
    env_base = os.environ.get("KIMI_BASE_URL", "").strip()
    if env_base:
        return env_base
    if base_url:
        return base_url
    if is_kimi_code_key(api_key):
        return KIMI_CODE_BASE_URL
    kimi_key = os.environ.get("KIMI_API_KEY", "").strip()
    if kimi_key and is_kimi_code_key(kimi_key):
        return KIMI_CODE_BASE_URL
    moonshot_key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if moonshot_key:
        return KIMI_MOONSHOT_BASE_URL
    return None


def extract_message_content(message: Any) -> str:
    """Return assistant text, including Kimi reasoning_content when content is empty."""
    content = getattr(message, "content", None) or ""
    if content:
        return content

    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        return reasoning

    model_extra = getattr(message, "model_extra", None) or {}
    if isinstance(model_extra, dict):
        extra_reasoning = model_extra.get("reasoning_content")
        if extra_reasoning:
            return extra_reasoning

    return ""


def apply_kimi_headers(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Inject User-Agent for Kimi Code API when required."""
    api_key = kwargs.get("api_key")
    api_base = kwargs.get("api_base") or ""
    if "api.kimi.com/coding" in api_base or is_kimi_code_key(api_key):
        headers = dict(kwargs.get("extra_headers") or {})
        headers.setdefault("User-Agent", KIMI_CODE_USER_AGENT)
        kwargs["extra_headers"] = headers
    return kwargs
