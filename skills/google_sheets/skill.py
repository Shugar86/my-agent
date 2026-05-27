"""Google Sheets integration skill."""

from __future__ import annotations

import logging
from typing import Any

from core.integration_credentials import get_credentials

logger = logging.getLogger(__name__)


def _get_sheets_service(user_id: str | None = None):
    """Build Google Sheets API service client."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("google-api-python-client not installed") from exc

    creds_data = get_credentials(user_id, "google")
    credentials = Credentials(
        token=None,
        refresh_token=creds_data.get("refresh_token", ""),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data.get("client_id", ""),
        client_secret=creds_data.get("client_secret", ""),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=credentials)


def sheets_read(
    spreadsheet_id: str, range_name: str = "Sheet1!A1:Z100", user_id: str | None = None
) -> dict[str, Any]:
    """Read values from a Google Sheet range."""
    try:
        service = _get_sheets_service(user_id)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get("values", [])
        return {"success": True, "values": values, "range": range_name}
    except Exception as exc:
        logger.exception("Sheets read failed")
        return {"success": False, "error": str(exc)}


def sheets_write(
    spreadsheet_id: str,
    range_name: str,
    values: list,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Write values to a Google Sheet range."""
    try:
        if not values:
            return {"success": False, "error": "values cannot be empty"}
        service = _get_sheets_service(user_id)
        body = {"values": values if isinstance(values[0], list) else [values]}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()
        return {"success": True, "updated_cells": result.get("updatedCells", 0)}
    except Exception as exc:
        logger.exception("Sheets write failed")
        return {"success": False, "error": str(exc)}


def register_tools() -> None:
    """Register Google Sheets tools."""
    from core.tool_registry import registry

    registry.register(
        name="sheets_read",
        description="Read data from Google Sheets",
        parameters={"type": "object", "properties": {
            "spreadsheet_id": {"type": "string"}, "range": {"type": "string"},
        }},
        execute_fn=lambda spreadsheet_id="", range_name="Sheet1!A1:Z100", user_id=None:
            sheets_read(spreadsheet_id, range_name, user_id),
    )
    registry.register(
        name="sheets_write",
        description="Write data to Google Sheets",
        parameters={"type": "object", "properties": {
            "spreadsheet_id": {"type": "string"}, "range": {"type": "string"}, "values": {"type": "array"},
        }},
        execute_fn=lambda spreadsheet_id="", range_name="Sheet1!A1", values=None, user_id=None:
            sheets_write(spreadsheet_id, range_name, values or [], user_id),
    )
