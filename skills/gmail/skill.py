"""Gmail API integration skill."""

from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from typing import Any

from core.integration_credentials import get_credentials

logger = logging.getLogger(__name__)


def _get_gmail_service(user_id: str | None = None):
    """Build Gmail API service client."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("google-api-python-client not installed") from exc

    creds_data = get_credentials(user_id, "google")
    refresh_token = creds_data.get("refresh_token", "")
    client_id = creds_data.get("client_id", "")
    client_secret = creds_data.get("client_secret", "")

    if not refresh_token:
        raise ValueError("Google refresh token not configured")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"],
    )
    return build("gmail", "v1", credentials=credentials)


def gmail_send(to: str, subject: str, body: str, user_id: str | None = None) -> dict[str, Any]:
    """Send email via Gmail API."""
    try:
        service = _get_gmail_service(user_id)
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"success": True, "message_id": result.get("id"), "to": to}
    except ValueError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Gmail send failed")
        return {"success": False, "error": str(exc)}


def gmail_list_unread(max_results: int = 5, user_id: str | None = None) -> dict[str, Any]:
    """List unread Gmail messages."""
    try:
        service = _get_gmail_service(user_id)
        results = service.users().messages().list(
            userId="me", q="is:unread", maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        return {"success": True, "count": len(messages), "messages": messages}
    except Exception as exc:
        logger.exception("Gmail list failed")
        return {"success": False, "error": str(exc)}


def register_tools() -> None:
    """Register Gmail tools."""
    from core.tool_registry import registry

    registry.register(
        name="gmail_send",
        description="Send email via Gmail API",
        parameters={"type": "object", "properties": {
            "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"},
        }},
        execute_fn=lambda to="", subject="", body="", user_id=None: gmail_send(to, subject, body, user_id),
    )
