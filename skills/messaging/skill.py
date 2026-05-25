"""Messaging gateways skill.

Unified interface to send messages via Telegram, Discord, Slack, and Email.
"""
import os
from core.tool_registry import registry
from skills.email.skill import send_email


def _telegram_send(bot_token: str, chat_id: str, message: str) -> dict:
    import httpx
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = httpx.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            return {"success": True, "message_id": data["result"]["message_id"]}
        return {"success": False, "error": data.get("description", "Unknown Telegram error")}
    except Exception as e:
        return {"success": False, "error": f"Telegram API error: {e}"}


def _discord_send(webhook_url: str, message: str) -> dict:
    import httpx
    try:
        resp = httpx.post(webhook_url, json={"content": message}, timeout=30)
        if resp.status_code == 204:
            return {"success": True}
        return {"success": False, "error": f"Discord returned {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Discord API error: {e}"}


def _slack_send(token: str, channel: str, message: str) -> dict:
    import httpx
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = httpx.post(url, headers=headers, json={"channel": channel, "text": message}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            return {"success": True, "ts": data.get("ts")}
        return {"success": False, "error": data.get("error", "Unknown Slack error")}
    except Exception as e:
        return {"success": False, "error": f"Slack API error: {e}"}


def send_message(platform: str, recipient: str, message: str,
                 bot_token: str = "", webhook_url: str = "",
                 slack_token: str = "", slack_channel: str = "",
                 email_config: dict | None = None) -> dict:
    """Send a message via supported platform.

    platform: telegram, discord, slack, email
    recipient: chat_id (tg), webhook_url (discord), channel (slack), or email address
    """
    if platform == "telegram":
        token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            return {"success": False, "error": "Missing bot_token or TELEGRAM_BOT_TOKEN env var"}
        return _telegram_send(token, recipient, message)

    if platform == "discord":
        url = webhook_url or recipient
        if not url:
            return {"success": False, "error": "Missing webhook_url"}
        return _discord_send(url, message)

    if platform == "slack":
        token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        channel = slack_channel or recipient
        if not token:
            return {"success": False, "error": "Missing slack_token or SLACK_BOT_TOKEN env var"}
        return _slack_send(token, channel, message)

    if platform == "email":
        cfg = email_config or {}
        return send_email(
            to=recipient,
            subject=cfg.get("subject", "Message from My Agent"),
            body=message,
            smtp_host=cfg.get("smtp_host"),
            smtp_port=cfg.get("smtp_port"),
            username=cfg.get("username"),
            password=cfg.get("password"),
        )

    return {"success": False, "error": f"Unknown platform: {platform}"}


def register_tools():
    registry.register(
        name="send_message",
        description="Send a message via Telegram, Discord, Slack, or Email.",
        parameters={
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["telegram", "discord", "slack", "email"], "description": "Messaging platform"},
                "recipient": {"type": "string", "description": "Recipient (chat_id, webhook_url, channel, or email)"},
                "message": {"type": "string", "description": "Message text"},
                "bot_token": {"type": "string", "description": "Telegram bot token (or env TELEGRAM_BOT_TOKEN)"},
                "webhook_url": {"type": "string", "description": "Discord webhook URL"},
                "slack_token": {"type": "string", "description": "Slack bot token (or env SLACK_BOT_TOKEN)"},
                "slack_channel": {"type": "string", "description": "Slack channel ID or name"},
                "email_config": {"type": "object", "description": "Email config dict with smtp_host, smtp_port, username, password, subject"},
            },
            "required": ["platform", "recipient", "message"],
        },
        execute_fn=send_message,
    )


def unregister_tools():
    registry.unregister("send_message")
