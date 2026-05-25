"""Showcase lead capture — writes to JSONL for investor demo follow-up."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(tags=["leads"])

LEADS_FILE = Path("data/showcase_leads.jsonl")


class ShowcaseLeadRequest(BaseModel):
    """Lead form payload from /showcase CTA."""

    telegram: str = Field(..., min_length=2, max_length=64)
    vertical: str = Field(..., min_length=2, max_length=64)
    email: str = Field(..., min_length=5, max_length=128)


@router.post("/api/leads/showcase")
async def submit_showcase_lead(body: ShowcaseLeadRequest) -> dict[str, str]:
    """Persist showcase lead and return Telegram deep-link preset."""
    telegram = body.telegram.strip()
    if not telegram.startswith("@"):
        telegram = f"@{telegram.lstrip('@')}"

    entry = {
        "telegram": telegram,
        "vertical": body.vertical.strip(),
        "email": body.email.strip().lower(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LEADS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Failed to write showcase lead: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save lead") from exc

    vertical = body.vertical.strip()
    return {
        "status": "ok",
        "telegram_link": f"https://t.me/my_agent_demo_bot?start=preset_{vertical}",
    }
