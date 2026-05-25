"""Google OAuth login routes (separate from integration OAuth)."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from core.auth import create_access_token
from core.teams.store import team_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

GOOGLE_AUTH_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]


def _auth_client_config() -> dict | None:
    client_id = os.environ.get("GOOGLE_AUTH_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_AUTH_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id:
        return None
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _redirect_uri(request: Request) -> str:
    explicit = os.environ.get("GOOGLE_AUTH_REDIRECT_URI", "")
    if explicit:
        return explicit
    return str(request.base_url).rstrip("/") + "/api/auth/google/callback"


@router.get("/api/auth/google")
async def google_auth_start(request: Request):
    """Redirect to Google OAuth for login."""
    cfg = _auth_client_config()
    if not cfg:
        raise HTTPException(status_code=501, detail="Google auth not configured")

    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        raise HTTPException(status_code=501, detail="google-auth-oauthlib not installed")

    flow = Flow.from_client_config(cfg, scopes=GOOGLE_AUTH_SCOPES, redirect_uri=_redirect_uri(request))
    auth_url, _ = flow.authorization_url(access_type="online", prompt="select_account")
    return RedirectResponse(auth_url)


@router.get("/api/auth/google/callback")
async def google_auth_callback(request: Request, code: str = "", error: str = ""):
    """Exchange Google code for JWT session."""
    if error:
        return RedirectResponse("/login?error=google_denied")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    cfg = _auth_client_config()
    if not cfg:
        raise HTTPException(status_code=501, detail="Google auth not configured")

    try:
        from google_auth_oauthlib.flow import Flow
        import google.oauth2.id_token
        import google.auth.transport.requests
    except ImportError:
        raise HTTPException(status_code=501, detail="Google auth libraries not installed")

    from core.auth import create_access_token, set_auth_cookie

    flow = Flow.from_client_config(cfg, scopes=GOOGLE_AUTH_SCOPES, redirect_uri=_redirect_uri(request))
    flow.fetch_token(code=code)
    credentials = flow.credentials
    if not credentials or not credentials.id_token:
        raise HTTPException(status_code=400, detail="Failed to obtain Google token")

    idinfo = google.oauth2.id_token.verify_oauth2_token(
        credentials.id_token,
        google.auth.transport.requests.Request(),
        cfg["web"]["client_id"],
    )
    email = idinfo.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    from web.server import user_manager

    user = await user_manager.get_or_create_from_google(email, name=idinfo.get("name"))
    if not user:
        return RedirectResponse("/login?error=email_exists_use_password")

    team_store.ensure_personal_team(user["id"], user["username"])
    token = create_access_token({
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
    })
    resp = RedirectResponse("/app")
    set_auth_cookie(resp, token)
    return resp
