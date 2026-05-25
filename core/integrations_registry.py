"""Integrations registry — single source of truth for connector metadata.

Each integration is described declaratively so the frontend can render the
connection UI, the marketplace can show relevant tags, and the workflow
validator can suggest available actions.

Trade-off: registry is in-memory and code-defined (vs. database-backed). This
is fine while the catalog evolves with releases; a multi-tenant SaaS would
move it to a versioned config file or DB table once partners contribute
connectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.integration_credentials import get_credentials


@dataclass(frozen=True)
class IntegrationField:
    """Describes a single credential field for an integration."""

    name: str
    label: str
    type: str = "text"
    required: bool = True
    help: str = ""


@dataclass(frozen=True)
class Integration:
    """Connector metadata used by the UI and workflow nodes."""

    provider: str
    name: str
    category: str
    description: str
    auth_method: str
    actions: list[str] = field(default_factory=list)
    fields: list[IntegrationField] = field(default_factory=list)
    docs_url: str = ""


_REGISTRY: list[Integration] = [
    Integration(
        provider="google",
        name="Google (Gmail + Sheets)",
        category="productivity",
        description="OAuth-powered access to Gmail (send/read) and Google Sheets.",
        auth_method="oauth",
        actions=["action.gmail_send", "action.sheets_read", "action.sheets_write", "trigger.email"],
        fields=[
            IntegrationField("client_id", "OAuth Client ID", help="From Google Cloud Console"),
            IntegrationField("client_secret", "OAuth Client Secret", type="password"),
            IntegrationField("refresh_token", "Refresh Token", required=False, type="password"),
        ],
        docs_url="https://developers.google.com/identity/protocols/oauth2",
    ),
    Integration(
        provider="telegram",
        name="Telegram",
        category="messaging",
        description="Bot API for sending messages and receiving updates.",
        auth_method="api_key",
        actions=["action.telegram", "trigger.telegram"],
        fields=[
            IntegrationField("bot_token", "Bot Token", type="password", help="From @BotFather"),
        ],
        docs_url="https://core.telegram.org/bots",
    ),
    Integration(
        provider="slack",
        name="Slack",
        category="messaging",
        description="Post messages to channels via Slack Bot Token.",
        auth_method="api_key",
        actions=["action.slack"],
        fields=[
            IntegrationField("bot_token", "Bot Token", type="password", help="xoxb-... from app config"),
        ],
        docs_url="https://api.slack.com/authentication/token-types",
    ),
    Integration(
        provider="notion",
        name="Notion",
        category="productivity",
        description="Create pages and update databases via Notion API.",
        auth_method="api_key",
        actions=["action.notion_page", "action.notion_db_update"],
        fields=[
            IntegrationField("api_key", "Internal Integration Token", type="password"),
        ],
        docs_url="https://developers.notion.com/docs/create-a-notion-integration",
    ),
    Integration(
        provider="webhook",
        name="Generic Webhook",
        category="protocol",
        description="Inbound webhook trigger and outbound POST. No credentials required.",
        auth_method="none",
        actions=["trigger.webhook", "action.webhook", "action.http"],
        fields=[],
        docs_url="",
    ),
]


def list_integrations(user_id: str | None = None) -> list[dict[str, Any]]:
    """Return all integrations with per-user configured status."""
    result: list[dict[str, Any]] = []
    for integ in _REGISTRY:
        creds = get_credentials(user_id, integ.provider) if integ.fields else {}
        configured = bool(creds and any(creds.values()))
        result.append({
            "provider": integ.provider,
            "name": integ.name,
            "category": integ.category,
            "description": integ.description,
            "auth_method": integ.auth_method,
            "actions": list(integ.actions),
            "fields": [
                {
                    "name": f.name,
                    "label": f.label,
                    "type": f.type,
                    "required": f.required,
                    "help": f.help,
                }
                for f in integ.fields
            ],
            "docs_url": integ.docs_url,
            "configured": configured or integ.auth_method == "none",
        })
    return result


def get_integration(provider: str) -> Integration | None:
    """Lookup a single integration by provider key."""
    return next((i for i in _REGISTRY if i.provider == provider), None)
