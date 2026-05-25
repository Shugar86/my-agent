"""Security helpers: public route policy and rate-limit rules."""

from __future__ import annotations

from dataclasses import dataclass


# Exact paths accessible without authentication (any method).
PUBLIC_EXACT_PATHS = {
    "/",
    "/login",
    "/welcome",
    "/onboarding",
    "/api/login",
    "/api/register",
    "/api/health",
    "/metrics",
}

# Prefixes accessible without authentication (any method).
PUBLIC_PREFIXES = (
    "/static",
    "/welcome-assets",
    "/api/workflows/webhook/",
    "/api/integrations/telegram/webhook",
    "/api/integrations/google/callback",
    "/api/auth/google",
)

# Prefixes accessible without authentication for GET only (marketplace preview).
PUBLIC_GET_PREFIXES = (
    "/api/marketplace",
    "/api/workflow-templates",
)


def is_public_path(path: str, method: str) -> bool:
    """Return True if the request may proceed without a JWT."""
    if path in PUBLIC_EXACT_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return True
    if method.upper() == "GET" and any(
        path == prefix or path.startswith(prefix + "/")
        for prefix in PUBLIC_GET_PREFIXES
    ):
        return True
    return False


@dataclass(frozen=True)
class RateLimitRule:
    """Sliding-window rate limit for an API action."""

    action: str
    limit: int
    window: int = 60


def resolve_rate_limit(path: str, method: str) -> RateLimitRule | None:
    """Return rate-limit rule for expensive endpoints, or None."""
    if method.upper() != "POST":
        return None

    if path == "/api/ask":
        return RateLimitRule("api_ask", 30)
    if path == "/api/chat":
        return RateLimitRule("api_chat", 20)
    if path == "/api/chat/stream":
        return RateLimitRule("api_chat_stream", 20)
    if (
        path.startswith("/api/workflows/")
        and path.endswith("/run")
        and path != "/api/workflows/validate"
    ):
        return RateLimitRule("workflow_run", 10)
    if path.startswith("/api/workflows/webhook/"):
        return RateLimitRule("workflow_webhook", 60)

    return None
