"""Workflow and integration API routes."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.integration_credentials import delete_credentials, get_credentials, save_credentials
from core.integrations_registry import list_integrations
from core.workflow.executor import WorkflowExecutor
from core.workflow.models import WorkflowDefinition
from core.workflow.store import workflow_store
from core.workflow.validator import validate_workflow

logger = logging.getLogger(__name__)
router = APIRouter(tags=["workflows"])
executor = WorkflowExecutor()




class WorkflowCreateRequest(BaseModel):
    """Create workflow request body."""

    name: str
    definition: dict[str, Any] = {}
    status: str = "draft"


class WorkflowUpdateRequest(BaseModel):
    """Update workflow request body."""

    name: str | None = None
    definition: dict[str, Any] | None = None
    status: str | None = None


class WorkflowValidateRequest(BaseModel):
    """Validate workflow definition."""

    definition: dict[str, Any]


class IntegrationCredentialsRequest(BaseModel):
    """Save integration credentials."""

    provider: str
    credentials: dict[str, Any]


class OnboardingCompleteRequest(BaseModel):
    """Mark onboarding complete."""

    complete: bool = True


class TemplateRateRequest(BaseModel):
    """Rate a workflow template."""

    score: int


class TemplatePublishRequest(BaseModel):
    """Publish a workflow template."""

    name: str
    description: str = ""
    category: str = "general"
    definition: dict[str, Any] = {}
    tags: list[str] = []
    published: bool = True


@router.get("/api/workflows")
async def list_workflows(request: Request):
    """List workflows for current workspace."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    if workspace_id:
        workflows = workflow_store.list_workflows(workspace_id=workspace_id)
    else:
        workflows = workflow_store.list_workflows(owner_id=user_id)
    return {"workflows": workflows, "total": len(workflows)}


@router.post("/api/workflows")
async def create_workflow(request: Request, body: WorkflowCreateRequest):
    """Create a new workflow."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    from core.teams.permissions import has_min_role

    team_role = getattr(request.state, "team_role", "member")
    if not has_min_role(team_role, "admin"):
        raise HTTPException(status_code=403, detail="Admin role required to create workflows")
    wf = workflow_store.create_workflow(
        name=body.name,
        definition=body.definition,
        owner_id=user_id,
        status=body.status,
        workspace_id=workspace_id,
    )
    if body.status == "active":
        await executor.sync_all_triggers(wf["id"])
    return wf


@router.get("/api/workflows/{workflow_id}")
async def get_workflow(request: Request, workflow_id: str):
    """Get workflow by ID."""
    user_id = getattr(request.state, "user_id", None)
    wf = workflow_store.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return wf


@router.put("/api/workflows/{workflow_id}")
async def update_workflow(request: Request, workflow_id: str, body: WorkflowUpdateRequest):
    """Update workflow."""
    user_id = getattr(request.state, "user_id", None)
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id, min_role="admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    wf = workflow_store.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    fields = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.definition is not None:
        fields["definition_json"] = body.definition
    if body.status is not None:
        fields["status"] = body.status
    updated = workflow_store.update_workflow(workflow_id, **fields)
    if updated:
        await executor.sync_all_triggers(workflow_id)
    return updated


@router.delete("/api/workflows/{workflow_id}")
async def delete_workflow(request: Request, workflow_id: str):
    """Delete workflow."""
    user_id = getattr(request.state, "user_id", None)
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id, min_role="admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    await executor.unregister_all_triggers(workflow_id)
    if not workflow_store.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"success": True}


@router.post("/api/workflows/validate")
async def validate_workflow_endpoint(request: Request, body: WorkflowValidateRequest):
    """Validate workflow definition structure."""
    definition = WorkflowDefinition.from_dict(body.definition)
    return validate_workflow(definition)


@router.post("/api/workflows/{workflow_id}/run")
async def run_workflow(request: Request, workflow_id: str):
    """Manually trigger workflow execution (background by default)."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id, min_role="member"):
        raise HTTPException(status_code=403, detail="Forbidden")
    body: dict[str, Any] = {}
    try:
        body = await request.json()
    except Exception:
        pass
    if not isinstance(body, dict):
        body = {}
    payload = body.get("payload", {})

    from core.billing.plans import check_workflow_run_allowed
    from core.teams.store import team_store

    plan = "free"
    if workspace_id:
        team = team_store.get_team(workspace_id)
        plan = (team or {}).get("plan", "free")
    quota = check_workflow_run_allowed(workspace_id, plan)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Plan limit reached: {quota['used']}/{quota['limit']} workflow runs this month",
        )

    wait = body.get("wait", False) is True
    if wait:
        result = await executor.run(workflow_id, trigger_payload=payload, user_id=user_id)
        if not result.get("success") and result.get("run_id"):
            return result
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Execution failed"))
        return result

    result = await executor.start_background(workflow_id, trigger_payload=payload, user_id=user_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Execution failed"))
    return result


@router.get("/api/workflows/{workflow_id}/runs/{run_id}")
async def get_workflow_run(request: Request, workflow_id: str, run_id: str):
    """Get a single workflow run with logs."""
    user_id = getattr(request.state, "user_id", None)
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id, min_role="member"):
        raise HTTPException(status_code=403, detail="Forbidden")
    run = workflow_store.get_run(run_id)
    if not run or run["workflow_id"] != workflow_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/api/workflows/{workflow_id}/runs")
async def list_workflow_runs(request: Request, workflow_id: str):
    """List execution history for a workflow."""
    user_id = getattr(request.state, "user_id", None)
    if user_id and not workflow_store.user_can_access_workflow(workflow_id, user_id, min_role="member"):
        raise HTTPException(status_code=403, detail="Forbidden")
    runs = workflow_store.list_runs(workflow_id)
    return {"runs": runs, "total": len(runs)}


@router.post("/api/workflows/webhook/{workflow_id}")
async def webhook_trigger(request: Request, workflow_id: str):
    """Public webhook trigger (token in query param)."""
    token = request.query_params.get("token", "")
    wf = workflow_store.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if wf.get("webhook_token") and token != wf["webhook_token"]:
        raise HTTPException(status_code=403, detail="Invalid webhook token")
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    result = await executor.run(workflow_id, trigger_payload=payload)
    return result


@router.get("/api/workflow-templates")
async def list_templates(
    request: Request,
    category: str | None = None,
    sort: str = "popular",
    q: str | None = None,
):
    """List marketplace workflow templates with optional search and category filters."""
    templates = workflow_store.list_templates(category=category, sort=sort)
    if q:
        needle = q.strip().lower()
        templates = [
            t for t in templates
            if needle in t["name"].lower()
            or needle in (t.get("description") or "").lower()
            or any(needle in str(tag).lower() for tag in t.get("tags") or [])
        ]
    return {"templates": templates, "total": len(templates)}


@router.get("/api/workflow-templates/{template_id}")
async def get_template_endpoint(request: Request, template_id: str):
    """Fetch a single template with full definition (for preview)."""
    tpl = workflow_store.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@router.get("/api/public/templates")
async def list_public_templates(featured: bool = False, limit: int = 12):
    """Anonymous list of published templates (optionally featured only)."""
    templates = workflow_store.list_templates(sort="popular")
    if featured:
        templates = [
            tpl for tpl in templates
            if "featured" in (tpl.get("tags") or [])
        ]
    sanitized = [
        {
            "id": tpl["id"],
            "name": tpl["name"],
            "description": tpl["description"],
            "category": tpl["category"],
            "tags": tpl.get("tags") or [],
            "installs": tpl.get("installs", 0),
            "nodes": len((tpl.get("definition") or {}).get("nodes") or []),
        }
        for tpl in templates[: max(1, min(limit, 50))]
    ]
    return {"templates": sanitized, "total": len(sanitized)}


@router.get("/api/public/templates/{template_id}")
async def public_template(template_id: str):
    """Anonymous read-only template view. Used for shareable links.

    Returns a sanitized payload (no author IDs, no internal flags).
    """
    tpl = workflow_store.get_template(template_id)
    if not tpl or not tpl.get("published", True):
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": tpl["id"],
        "name": tpl["name"],
        "description": tpl["description"],
        "category": tpl["category"],
        "definition": tpl["definition"],
        "tags": tpl.get("tags") or [],
        "installs": tpl.get("installs", 0),
        "rating_avg": tpl.get("rating_avg", 0),
        "rating_count": tpl.get("rating_count", 0),
    }


@router.post("/api/workflow-templates")
async def publish_template(request: Request, body: TemplatePublishRequest):
    """Publish a workflow template to marketplace (admin only)."""
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    user_id = getattr(request.state, "user_id", None)
    tpl = workflow_store.create_template(
        name=body.name,
        description=body.description,
        category=body.category,
        definition=body.definition,
        tags=body.tags,
        author_id=user_id,
        published=body.published,
    )
    return {"success": True, "template": tpl}


@router.post("/api/workflow-templates/{template_id}/rate")
async def rate_template(request: Request, template_id: str, body: TemplateRateRequest):
    """Rate a workflow template 1-5."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tpl = workflow_store.rate_template(template_id, user_id, body.score)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "template": tpl}


@router.post("/api/workflow-templates/{template_id}/demo-run")
async def template_demo_run(request: Request, template_id: str):
    """Return a mock successful run for template preview (no integrations required)."""
    from core.workflow.template_demo import build_template_demo_run

    tpl = workflow_store.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return build_template_demo_run(tpl)


@router.get("/api/billing/plan")
async def get_billing_plan(request: Request):
    """Return current workspace plan and usage limits."""
    from core.billing.plans import check_workflow_run_allowed
    from core.teams.store import team_store

    workspace_id = getattr(request.state, "workspace_id", None)
    plan = "free"
    team_name = ""
    if workspace_id:
        team = team_store.get_team(workspace_id)
        if team:
            plan = team.get("plan", "free")
            team_name = team.get("name", "")
    quota = check_workflow_run_allowed(workspace_id, plan)
    return {
        "workspace_id": workspace_id,
        "workspace_name": team_name,
        "plan": quota["plan"],
        "label": quota.get("label", "Free"),
        "workflow_runs_used": quota["used"],
        "workflow_runs_limit": quota["limit"],
        "allowed": quota["allowed"],
    }


@router.post("/api/workflow-templates/{template_id}/install")
async def install_template(request: Request, template_id: str):
    """Clone template into user's workspace."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    wf = workflow_store.clone_template(template_id, owner_id=user_id, workspace_id=workspace_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "workflow": wf}


@router.get("/api/workflow-node-types")
async def node_types(request: Request):
    """List available workflow node types."""
    from core.workflow.registry import list_node_types
    from core.workflow.nodes import register_all_handlers
    register_all_handlers()
    return {"node_types": list_node_types()}


# ---------------------------------------------------------------------------
# Integrations API
# ---------------------------------------------------------------------------

@router.get("/api/integrations")
async def list_all_integrations(request: Request):
    """List supported integrations with per-user connection status."""
    user_id = getattr(request.state, "user_id", None)
    return {"integrations": list_integrations(user_id)}


@router.post("/api/integrations/{provider}/test")
async def test_integration(request: Request, provider: str):
    """Run a non-destructive sanity check on configured credentials."""
    user_id = getattr(request.state, "user_id", None)
    creds = get_credentials(user_id, provider)
    if not creds or not any(creds.values()):
        raise HTTPException(status_code=400, detail="Integration not configured")

    if provider == "telegram":
        token = creds.get("bot_token", "")
        if not token:
            return {"success": False, "error": "bot_token missing"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                data = resp.json()
            ok = bool(data.get("ok"))
            return {"success": ok, "info": data.get("result") if ok else data.get("description")}
        except Exception as exc:  # noqa: BLE001 — network surface
            return {"success": False, "error": str(exc)}
    if provider == "slack":
        token = creds.get("bot_token", "")
        if not token:
            return {"success": False, "error": "bot_token missing"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {token}"},
                )
                data = resp.json()
            return {"success": bool(data.get("ok")), "info": data}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}
    if provider == "notion":
        key = creds.get("api_key", "")
        if not key:
            return {"success": False, "error": "api_key missing"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.notion.com/v1/users/me",
                    headers={"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"},
                )
            return {"success": resp.is_success, "info": resp.json() if resp.is_success else resp.text[:500]}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}
    if provider == "google":
        # We mark as configured if refresh_token is present; full sanity test
        # requires a real Gmail/Sheets call which we leave to the user's first run.
        return {
            "success": bool(creds.get("refresh_token")),
            "info": "OAuth credentials present" if creds.get("refresh_token") else "Re-run OAuth",
        }
    return {"success": True, "info": "No-op test"}


@router.post("/api/integrations/credentials")
async def save_integration_credentials(request: Request, body: IntegrationCredentialsRequest):
    """Save integration OAuth/API credentials."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ok = save_credentials(user_id, body.provider, body.credentials)
    return {"success": ok, "provider": body.provider}


@router.get("/api/integrations/credentials/{provider}")
async def get_integration_status(request: Request, provider: str):
    """Check if integration is configured (masked)."""
    user_id = getattr(request.state, "user_id", None)
    creds = get_credentials(user_id, provider)
    configured = bool(creds and any(creds.values()))
    masked = {k: "***" if v else "" for k, v in creds.items()} if configured else {}
    return {"provider": provider, "configured": configured, "fields": masked}


@router.delete("/api/integrations/credentials/{provider}")
async def remove_integration(request: Request, provider: str):
    """Remove integration credentials."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ok = delete_credentials(user_id, provider)
    return {"success": ok}


@router.get("/api/integrations/google/auth")
async def google_oauth_start(request: Request):
    """Start Google OAuth flow."""
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        raise HTTPException(status_code=501, detail="google-auth-oauthlib not installed")

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id:
        raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID not configured")

    redirect_uri = str(request.base_url).rstrip("/") + "/api/integrations/google/callback"
    flow = Flow.from_client_config(
        {"web": {"client_id": client_id, "client_secret": client_secret,
                 "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                 "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=[
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return {"auth_url": auth_url}


@router.get("/api/integrations/google/callback")
async def google_oauth_callback(request: Request, code: str = "", state: str = ""):
    """Google OAuth callback — exchange code for refresh token."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"error": "Login required before OAuth callback"}

    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        raise HTTPException(status_code=501, detail="google-auth-oauthlib not installed")

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = str(request.base_url).rstrip("/") + "/api/integrations/google/callback"
    flow = Flow.from_client_config(
        {"web": {"client_id": client_id, "client_secret": client_secret,
                 "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                 "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=[
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_credentials(user_id, "google", {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": creds.refresh_token or "",
    })
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/onboarding?step=2&google=connected")


@router.post("/api/integrations/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates and trigger matching workflows."""
    try:
        update = await request.json()
    except Exception:
        update = {}

    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    workflows = workflow_store.list_workflows()
    triggered = []
    for wf in workflows:
        if wf.get("status") != "active":
            continue
        definition = wf.get("definition", {})
        for node in definition.get("nodes", []):
            if node.get("type") == "trigger.telegram":
                result = await executor.run(
                    wf["id"],
                    trigger_payload={"text": text, "chat_id": chat_id, "update": update},
                )
                triggered.append({"workflow_id": wf["id"], "result": result})

    return {"ok": True, "triggered": len(triggered)}


# ---------------------------------------------------------------------------
# Onboarding API
# ---------------------------------------------------------------------------

@router.get("/api/onboarding/status")
async def onboarding_status(request: Request):
    """Get onboarding status for current user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = workflow_store.get_user_profile(user_id)
    return profile


@router.post("/api/onboarding/complete")
async def onboarding_complete(request: Request, body: OnboardingCompleteRequest):
    """Mark onboarding as complete."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    workflow_store.set_onboarding_complete(user_id, body.complete)
    return {"success": True, "onboarding_complete": body.complete}
