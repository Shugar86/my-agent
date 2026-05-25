"""FastAPI Web Server with async-native orchestration and live stats."""
import os
import json
import asyncio
import uuid
import traceback
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Dict, List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.agent_store import AgentStore
from core.orchestrator import Orchestrator
from core.auto_agent_factory import AutoAgentFactory
from core.config import load_config, DEFAULT_CONFIG, resolve_env_vars
from core.logging_setup import setup_logging, set_session_context
from core.llm_gateway import LLMGateway
from core.builder import AgentBuilder
from core.auth import create_access_token, decode_access_token
from core.user_manager import UserManager
from core.db_manager import db
from tools.vector_tools import _get_db as get_vector_db
from core.mcp_manager import MCPServerManager
from core.redis_client import redis_client
from core.scheduler_manager import scheduler_manager
from core.session_cache import SessionCache, ResponseCache, RateLimiter
from core.mcp_client_manager import mcp_client_manager
from core import feedback as feedback_module
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from web.mcp_server import router as mcp_router
from web.a2a_server import router as a2a_router
from web.workflow_router import router as workflow_router
from web.sessions_router import router as sessions_router
from core.db_migrate import run_migrations

setup_logging(mode="web", log_level="INFO")

# Prometheus metrics (use isolated registry to avoid duplicates in tests)
_prom_registry = CollectorRegistry()
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"], registry=_prom_registry)
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", registry=_prom_registry)
ACTIVE_SESSIONS = Gauge("active_sessions", "Number of active user sessions", registry=_prom_registry)
LLM_TOKEN_COUNT = Counter("llm_tokens_total", "Total LLM tokens generated", ["model"], registry=_prom_registry)
LLM_ERROR_COUNT = Counter("llm_errors_total", "Total LLM errors", ["error_type"], registry=_prom_registry)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="My Agent Web UI")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# MCP (Model Context Protocol) — Claude Desktop, Cursor, etc.
app.include_router(mcp_router)

# A2A (Agent-to-Agent) protocol
app.include_router(a2a_router)

# Workflow engine + integrations
app.include_router(workflow_router)

# Chat sessions API
app.include_router(sessions_router)

# CORS — allow localhost origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    max_size = 10 * 1024 * 1024  # 10 MB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(status_code=413, content={"error": "Request too large"})
    return await call_next(request)


@app.middleware("http")
async def redis_rate_limit_middleware(request: Request, call_next):
    """Redis sliding-window rate limiting for API endpoints."""
    if request.url.path.startswith("/api/ask") and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, reset_after = await RateLimiter.check(
            client_ip, "api_ask", limit=30, window=60
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "retry_after": reset_after,
                    "limit": 30,
                    "window": "1 minute"
                },
                headers={"Retry-After": str(reset_after)}
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "30"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
    return await call_next(request)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    """Record request metrics for Prometheus."""
    from time import time
    start = time()
    response = await call_next(request)
    duration = time() - start
    path = request.url.path
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=path, status=response.status_code).inc()
    return response


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

_WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "..", "website")
if os.path.isdir(_WEBSITE_DIR):
    app.mount("/welcome-assets", StaticFiles(directory=_WEBSITE_DIR), name="welcome")

user_manager = UserManager()

# Absolute path to static files (works regardless of CWD)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

PUBLIC_PATHS = {
    "/login", "/api/login", "/api/register", "/api/health", "/static", "/welcome-assets",
    "/welcome", "/api/marketplace", "/api/workflow-templates", "/metrics",
    "/api/workflows/webhook", "/api/integrations/telegram/webhook",
    "/api/integrations/google/callback",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        token = request.cookies.get("access_token")
        payload = None
        if token:
            payload = decode_access_token(token)

        if payload and "user_id" in payload:
            jti = payload.get("jti")
            if jti and await redis_client.is_token_revoked(jti):
                if path.startswith("/api/"):
                    return JSONResponse(status_code=401, content={"error": "Token revoked"})
                return RedirectResponse(url="/login")
            request.state.user_id = payload["user_id"]
            request.state.user_role = payload.get("role", "user")
            ACTIVE_SESSIONS.inc()
            try:
                if path == "/" and path != "/onboarding":
                    from core.workflow.store import workflow_store
                    profile = workflow_store.get_user_profile(payload["user_id"])
                    if not profile.get("onboarding_complete"):
                        return RedirectResponse(url="/onboarding")
                if path == "/":
                    return RedirectResponse(url="/app")
                legacy_redirects = {
                    "/chat": "/app/chat",
                    "/marketplace": "/app/marketplace",
                    "/builder": "/app/builder",
                    "/settings": "/app/settings",
                    "/workflows": "/app/workflows",
                }
                if path in legacy_redirects:
                    return RedirectResponse(url=legacy_redirects[path], status_code=301)
                if path.startswith("/workflows/"):
                    wf_id = path.split("/workflows/", 1)[1]
                    return RedirectResponse(url=f"/app/workflows/{wf_id}", status_code=301)
                return await call_next(request)
            finally:
                ACTIVE_SESSIONS.dec()

        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        return RedirectResponse(url="/login")


app.add_middleware(AuthMiddleware)

mcp_manager = MCPServerManager()


@app.on_event("startup")
async def startup():
    await redis_client.connect()
    run_migrations()
    await scheduler_manager.start()
    await user_manager.connect()
    await user_manager.create_default_admin()
    db.create_tables()
    # Ensure scheduled_jobs_log table exists
    db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_jobs_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            description TEXT,
            result TEXT,
            status TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    from core.workflow.executor import rehydrate_all_triggers
    await rehydrate_all_triggers()


@app.on_event("shutdown")
async def shutdown():
    await scheduler_manager.shutdown()
    await user_manager.close()
    await redis_client.close()
    db.close()


import logging
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception in %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": str(exc)}
    )


# ---------------------------------------------------------------------------
# Auth & Registration
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ApiKeysRequest(BaseModel):
    keys: dict


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open(os.path.join(_STATIC_DIR, "login.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
@limiter.limit("60/minute")
async def health(request: Request):
    agents = store.list_agents()
    redis_ok = await redis_client.ping()
    return {
        "status": "ok",
        "agents": len(agents),
        "skills": sum(len(a.get("skills", [])) for a in agents),
        "tools": sum(len(a.get("tools", [])) for a in agents),
        "redis": redis_ok,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return StreamingResponse(
        iter([generate_latest(_prom_registry)]),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------------------------
# API Keys Management
# ---------------------------------------------------------------------------

from core.api_keys import save_api_key, get_api_key, list_api_keys, delete_api_key, load_all_keys_to_env

# Load saved keys on startup
load_all_keys_to_env()


@app.get("/api/keys")
@limiter.limit("60/minute")
async def list_keys(request: Request):
    """List saved API key names (values masked)."""
    keys = list_api_keys()
    return {"keys": keys, "count": len(keys)}


@app.post("/api/keys")
@limiter.limit("30/minute")
async def save_key(request: Request, body: Dict[str, str]):
    """Save an API key (encrypted at rest)."""
    name = body.get("name")
    value = body.get("value")
    if not name or not value:
        raise HTTPException(status_code=400, detail="name and value required")
    
    success = save_api_key(name, value)
    return {"success": success, "name": name}


@app.delete("/api/keys/{name}")
@limiter.limit("30/minute")
async def remove_key(request: Request, name: str):
    """Delete an API key."""
    success = delete_api_key(name)
    return {"success": success, "name": name}


@app.post("/api/logout")
async def logout(request: Request):
    """Revoke current JWT token (logout)."""
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload and "jti" in payload:
            await redis_client.revoke_token(payload["jti"])
    resp = JSONResponse({"success": True})
    resp.delete_cookie("access_token")
    return resp


@app.post("/api/register")
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    if not body.username or len(body.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(body.password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    if not any(c.isupper() for c in body.password) or not any(c.islower() for c in body.password) or not any(c.isdigit() for c in body.password):
        raise HTTPException(status_code=400, detail="Password must contain uppercase, lowercase, and digit")

    user = await user_manager.create_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=409, detail="Username already exists")

    token = create_access_token({"sub": user["username"], "user_id": user["id"], "role": user["role"]})
    resp = JSONResponse({"success": True, "user": user})
    _set_auth_cookie(resp, token)
    return resp


def _set_auth_cookie(response: JSONResponse, token: str):
    secure = os.environ.get("ENV", "").lower() in ("production", "prod", "staging")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=86400,
    )


@app.post("/api/login")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    user = await user_manager.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user["username"], "user_id": user["id"], "role": user["role"]})
    resp = JSONResponse({"success": True, "redirect": "/"})
    _set_auth_cookie(resp, token)
    return resp


@app.get("/api/me")
@limiter.limit("20/minute")
async def get_me(request: Request):
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401)
    user = await user_manager.get_user_by_id(uid)
    if not user:
        raise HTTPException(status_code=404)
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@app.get("/api/users")
@limiter.limit("10/minute")
async def list_users(request: Request):
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return {"users": await user_manager.list_users()}


@app.put("/api/api-keys")
@limiter.limit("30/minute")
async def update_api_keys(request: Request, body: ApiKeysRequest):
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401)
    await user_manager.update_api_keys(uid, body.keys)
    return {"status": "updated"}


@app.get("/api/api-keys")
@limiter.limit("30/minute")
async def get_api_keys(request: Request):
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401)
    keys = await user_manager.get_api_keys(uid)
    return {"keys": keys}


store = AgentStore()

config_path = os.path.join("config", "agent.json")
if os.path.exists(config_path):
    config = load_config(config_path)
else:
    config = DEFAULT_CONFIG

orchestrator = Orchestrator(store)
llm_config = config.get("model", {})
factory = AutoAgentFactory(store, llm_config)


class ChatRequest(BaseModel):
    message: str
    agent_id: str = "universal"
    auto_agents: bool = False
    session_id: str | None = None


class AgentRequest(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    role: str
    model: dict
    skills: list
    tools: list
    sub_agents: list
    memory: dict
    output: dict


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Public landing for unauthenticated users."""
    website_path = os.path.join(os.path.dirname(__file__), "..", "website", "index.html")
    if os.path.exists(website_path):
        with open(website_path, "r", encoding="utf-8") as f:
            return f.read()
    with open(os.path.join(_STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/welcome", response_class=HTMLResponse)
async def welcome_page():
    """Marketing landing page."""
    website_path = os.path.join(os.path.dirname(__file__), "..", "website", "index.html")
    if os.path.exists(website_path):
        with open(website_path, "r", encoding="utf-8") as f:
            return f.read()
    return RedirectResponse(url="/")


@app.get("/app", response_class=HTMLResponse)
@app.get("/app/{path:path}", response_class=HTMLResponse)
async def app_spa(path: str = ""):
    """Serve unified React SPA."""
    spa_path = os.path.join(_STATIC_DIR, "app", "index.html")
    if os.path.exists(spa_path):
        with open(spa_path, "r", encoding="utf-8") as f:
            return f.read()
    with open(os.path.join(_STATIC_DIR, "workflow-fallback.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/chat", response_class=HTMLResponse)
async def chat():
    with open(os.path.join(_STATIC_DIR, "chat.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/agents", response_class=HTMLResponse)
async def agents_page():
    with open(os.path.join(_STATIC_DIR, "agents.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    with open(os.path.join(_STATIC_DIR, "settings.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/mcp", response_class=HTMLResponse)
async def mcp_page():
    with open(os.path.join(_STATIC_DIR, "mcp.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page():
    with open(os.path.join(_STATIC_DIR, "knowledge.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page():
    with open(os.path.join(_STATIC_DIR, "marketplace.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/builder", response_class=HTMLResponse)
async def builder_page():
    with open(os.path.join(_STATIC_DIR, "builder.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/workflows", response_class=HTMLResponse)
@app.get("/workflows/{workflow_id}", response_class=HTMLResponse)
async def workflows_spa(workflow_id: str = ""):
    """Serve React Flow workflow builder SPA."""
    spa_path = os.path.join(_STATIC_DIR, "workflow", "index.html")
    if os.path.exists(spa_path):
        with open(spa_path, "r", encoding="utf-8") as f:
            return f.read()
    with open(os.path.join(_STATIC_DIR, "workflow-fallback.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    with open(os.path.join(_STATIC_DIR, "onboarding.html"), "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Agents API
# ---------------------------------------------------------------------------

@app.get("/api/agents")
@limiter.limit("30/minute")
async def get_agents(request: Request):
    return store.list_agents()


@app.get("/api/agents/{agent_id}")
@limiter.limit("30/minute")
async def get_agent(request: Request, agent_id: str):
    agent = store.get_agent(agent_id)
    return agent if agent else {"error": "Not found"}


@app.post("/api/agents")
@limiter.limit("30/minute")
async def create_agent(request: Request, body: AgentRequest):
    agent_config = body.model_dump()
    agent_id = store.save_agent(agent_config)
    return {"id": agent_id, "status": "created"}


@app.put("/api/agents/{agent_id}")
@limiter.limit("30/minute")
async def update_agent(request: Request, agent_id: str, body: AgentRequest):
    agent_config = body.model_dump()
    agent_config["id"] = agent_id
    store.save_agent(agent_config)
    return {"status": "updated"}


@app.delete("/api/agents/{agent_id}")
@limiter.limit("30/minute")
async def delete_agent(request: Request, agent_id: str):
    store.delete_agent(agent_id)
    return {"status": "deleted"}


@app.post("/api/agents/{agent_id}/duplicate")
@limiter.limit("30/minute")
async def duplicate_agent(request: Request, agent_id: str):
    new_id = store.duplicate_agent(agent_id)
    return {"id": new_id, "status": "duplicated"} if new_id else {"error": "Not found"}


# ---------------------------------------------------------------------------
# Simple Ask API (hosted agent mode)
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str
    agent_id: str = "universal"
    model: str = "fast"


@app.post("/api/ask")
@limiter.limit("60/minute")
async def ask_endpoint(request: Request, body: AskRequest):
    """Simple request-response API for hosted agent usage.
    
    No auth required — perfect for integrations and simple usage.
    """
    from core.configurator import resolve_profile

    try:
        agent_config = store.get_agent(body.agent_id)
        if not agent_config:
            return JSONResponse(
                status_code=404,
                content={"error": f"Agent '{body.agent_id}' not found"}
            )

        # Resolve model profile
        model_config = resolve_profile(body.model)
        if not model_config:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown model profile: {body.model}"}
            )

        # Check response cache
        primary_model = model_config.get("primary", "unknown")
        cached = await ResponseCache.get(primary_model, body.question, agent_config.get("tools"))
        if cached:
            return {
                "answer": cached,
                "model": primary_model,
                "agent": body.agent_id,
                "cached": True,
            }

        builder = (AgentBuilder()
            .set_model(model_config)
            .set_role(agent_config.get("role", ""))
            .set_skills(agent_config.get("skills", []))
            .set_tools(agent_config.get("tools", []))
            .set_memory({"enabled": False}))  # Stateless for simple API
        agent = builder.build()

        result = await agent.run(body.question)

        # Cache the response
        await ResponseCache.set(primary_model, body.question, result, agent_config.get("tools"))

        return {
            "answer": result,
            "model": primary_model,
            "agent": body.agent_id,
            "cached": False,
        }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Ask endpoint error")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)[:200]}
        )


# ---------------------------------------------------------------------------
# Chat API (async-native)
# ---------------------------------------------------------------------------


def _user_session_id(user_id: str, raw_sid: str) -> str:
    return f"{user_id}::{raw_sid}"


@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, body: ChatRequest):
    uid = getattr(request.state, "user_id", "anon")
    session_id = _user_session_id(uid, body.agent_id)
    set_session_context(session_id)
    try:
        if body.auto_agents:
            result = await orchestrator.run_with_auto_agents(body.message, body.agent_id, factory)
        else:
            result = await orchestrator.run(body.message, body.agent_id)
        return {"response": result}
    finally:
        set_session_context("")


@app.post("/api/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, body: ChatRequest):
    uid = getattr(request.state, "user_id", "anon")

    async def event_stream():
        raw_sid = body.session_id or f"stream_{uuid.uuid4().hex[:12]}"
        sid = _user_session_id(uid, raw_sid)
        set_session_context(body.agent_id)
        from core.state_db import StateDB
        state_db = StateDB(os.environ.get("STATE_DB_PATH", "data/state.db"))
        if not state_db.get_session(sid):
            state_db.create_session(sid, source="web", user_id=uid, model=body.agent_id)
        if body.message.strip():
            state_db.set_session_title(sid, body.message.strip()[:100])
        try:
            yield f"data: {json.dumps({'type': 'session', 'session_id': raw_sid})}\n\n"
            agent_config = store.get_agent(body.agent_id)
            if not agent_config:
                yield f"data: {json.dumps({'type': 'error', 'content': f'Agent {body.agent_id} not found'})}\n\n"
                return

            model_config = resolve_env_vars(agent_config.get("model", {}))
            llm = LLMGateway(model_config)

            builder = (AgentBuilder()
                .set_model(model_config)
                .set_role(agent_config.get("role", ""))
                .set_skills(agent_config.get("skills", []))
                .set_tools(agent_config.get("tools", []))
                .set_memory(agent_config.get("memory", {"enabled": False})))
            agent = builder.build()
            session = agent.memory.get_session(sid)
            session.add_user_message(body.message)
            system_prompt = agent._build_system_prompt()
            tools = agent.skills.get_schemas(agent.tool_names) if agent.tool_names else agent.skills.get_schemas()

            max_turns = 10
            total_output_tokens = 0
            for turn in range(max_turns):
                messages = [{"role": "system", "content": system_prompt}] + session.messages
                tool_call_seen = False

                # Now async-native: await llm.chat_stream()
                async for event in llm.chat_stream(messages, tools=tools if tools else None):
                    yield f"data: {json.dumps(event)}\n\n"
                    if event["type"] == "token":
                        total_output_tokens += 1
                    elif event["type"] == "tool_call":
                        tool_call_seen = True
                        try:
                            args = json.loads(event["args"])
                            result = agent.skills.execute_tool(event["name"], **args)
                            result_str = str(result)[:2000]
                            yield f"data: {json.dumps({'type': 'tool_result', 'name': event['name'], 'content': result_str})}\n\n"
                            tid = uuid.uuid4().hex[:8]
                            session.messages.append({
                                "role": "assistant", "content": None,
                                "tool_calls": [{"id": tid, "type": "function",
                                    "function": {"name": event["name"], "arguments": event["args"]}}],
                            })
                            session.messages.append({
                                "role": "tool", "tool_call_id": tid, "content": result_str,
                            })
                        except Exception as exc:
                            yield f"data: {json.dumps({'type': 'tool_result', 'name': event['name'], 'content': f'Error: {exc}'})}\n\n"
                    elif event["type"] == "done":
                        estimated_cost = total_output_tokens * 0.15 / 1_000_000
                        try:
                            import httpx
                            async with httpx.AsyncClient() as client:
                                await client.post(
                                    f"http://{request.url.hostname}:{request.url.port}/api/cost/track",
                                    json={"tokens": total_output_tokens, "cost": estimated_cost},
                                    cookies=request.cookies,
                                )
                        except Exception:
                            pass
                        # Prometheus metrics
                        model_name = agent_config.get("model", {}).get("primary", "unknown").split("/")[-1]
                        LLM_TOKEN_COUNT.labels(model=model_name).inc(total_output_tokens)
                        break

                if not tool_call_seen:
                    break

            if agent.memory.enabled:
                agent.memory.save_session(session)
        except Exception as e:
            LLM_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            set_session_context("")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Config API
# ---------------------------------------------------------------------------

@app.get("/api/config")
@limiter.limit("30/minute")
async def get_config(request: Request):
    return config


@app.post("/api/config")
@limiter.limit("30/minute")
async def update_config(request: Request):
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    body = await request.json()
    config_path = os.path.join("config", "agent.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(body, f, indent=2, ensure_ascii=False)
    return {"status": "updated"}


# ---------------------------------------------------------------------------
# Cost / Usage API
# ---------------------------------------------------------------------------

_cost_store: dict = {}
_cost_lock = asyncio.Lock()


@app.get("/api/cost")
@limiter.limit("30/minute")
async def get_cost(request: Request):
    uid = getattr(request.state, "user_id", "anon")
    async with _cost_lock:
        user_cost = _cost_store.get(uid, {"tokens": 0, "cost": 0.0})
    return {"session_cost": user_cost}


@app.post("/api/cost/track")
@limiter.limit("60/minute")
async def track_cost(request: Request):
    uid = getattr(request.state, "user_id", "anon")
    body = await request.json()
    tokens = body.get("tokens", 0)
    cost = body.get("cost", 0.0)
    async with _cost_lock:
        if uid not in _cost_store:
            _cost_store[uid] = {"tokens": 0, "cost": 0.0}
        _cost_store[uid]["tokens"] += tokens
        _cost_store[uid]["cost"] += cost
    return {"status": "tracked"}


@app.post("/api/cost/reset")
@limiter.limit("10/minute")
async def reset_cost(request: Request):
    uid = getattr(request.state, "user_id", "anon")
    async with _cost_lock:
        _cost_store.pop(uid, None)
    return {"status": "reset"}


# ---------------------------------------------------------------------------
# Knowledge Base API
# ---------------------------------------------------------------------------

class KnowledgeUpload(BaseModel):
    content: str
    source: str = ""


class KnowledgeSearch(BaseModel):
    query: str
    n_results: int = 5


@app.post("/api/knowledge/upload")
@limiter.limit("30/minute")
async def knowledge_upload(request: Request, body: KnowledgeUpload):
    vdb = get_vector_db()
    doc_id = vdb.add_text(body.content, source=body.source)
    return {"status": "added", "id": doc_id}


@app.post("/api/knowledge/search")
@limiter.limit("30/minute")
async def knowledge_search(request: Request, body: KnowledgeSearch):
    vdb = get_vector_db()
    results = vdb.search(body.query, n_results=body.n_results)
    return {"results": [
        {"id": r["id"], "content": r["content"], "source": r.get("source", ""), "score": r.get("score", 0.0)}
        for r in results
    ]}


@app.get("/api/knowledge/list")
@limiter.limit("30/minute")
async def knowledge_list(request: Request):
    vdb = get_vector_db()
    docs = vdb.list_documents()
    return {"documents": docs, "count": len(docs)}


@app.delete("/api/knowledge/delete/{doc_id}")
@limiter.limit("30/minute")
async def knowledge_delete(request: Request, doc_id: str):
    vdb = get_vector_db()
    vdb.delete(doc_id)
    return {"status": "deleted", "id": doc_id}


# ---------------------------------------------------------------------------
# Marketplace API
# ---------------------------------------------------------------------------

@app.get("/api/marketplace")
async def marketplace_list(request: Request):
    """Return workflow templates and legacy skills from marketplace."""
    from core.workflow.store import workflow_store
    templates = workflow_store.list_templates()
    skills = [
        {"name": "sql_db", "version": "1.0", "description": "SQLite query execution and table listing", "tags": ["database", "sql"], "installs": 42, "type": "skill"},
        {"name": "ocr", "version": "1.0", "description": "Tesseract OCR for images and PDFs", "tags": ["image", "pdf", "text"], "installs": 128, "type": "skill"},
        {"name": "email", "version": "1.0", "description": "SMTP email sending with attachments", "tags": ["email", "communication"], "installs": 34, "type": "skill"},
    ]
    workflow_items = [
        {
            "name": t["id"],
            "version": "1.0",
            "description": t["description"],
            "tags": t.get("tags", []),
            "installs": t.get("installs", 0),
            "type": "workflow",
            "category": t.get("category", "general"),
        }
        for t in templates
    ]
    all_items = workflow_items + skills
    return {"skills": all_items, "templates": templates, "total": len(all_items)}


@app.post("/api/marketplace/install/{item_name}")
@limiter.limit("10/minute")
async def marketplace_install(request: Request, item_name: str):
    user_id = getattr(request.state, "user_id", None)
    from core.workflow.store import workflow_store

    template = workflow_store.get_template(item_name)
    if template:
        wf = workflow_store.clone_template(item_name, owner_id=user_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"status": "installed", "type": "workflow", "workflow": wf}

    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only for skill install")
    db.execute(
        "INSERT OR REPLACE INTO installed_skills (name, version, source) VALUES (?, ?, ?)",
        (item_name, "1.0", f"builtin:{item_name}"),
    )
    return {"status": "installed", "type": "skill", "skill": item_name}


# ---------------------------------------------------------------------------
# Scheduler API
# ---------------------------------------------------------------------------

class ScheduleRequest(BaseModel):
    description: str
    trigger_type: str = "interval"
    minutes: int = 0
    hours: int = 0
    days: int = 0
    cron: str = ""
    agent_role: str = "universal"


@app.post("/api/schedule")
@limiter.limit("10/minute")
async def schedule_create(request: Request, body: ScheduleRequest):
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if body.trigger_type == "interval":
        trigger_args = {}
        if body.minutes:
            trigger_args["minutes"] = body.minutes
        if body.hours:
            trigger_args["hours"] = body.hours
        if body.days:
            trigger_args["days"] = body.days
        if not trigger_args:
            raise HTTPException(status_code=400, detail="Interval requires minutes/hours/days")
    elif body.trigger_type == "cron":
        parts = body.cron.split()
        if len(parts) != 5:
            raise HTTPException(status_code=400, detail="Cron expression must have 5 fields")
        trigger_args = {
            "minute": parts[0], "hour": parts[1], "day": parts[2],
            "month": parts[3], "day_of_week": parts[4],
        }
    else:
        raise HTTPException(status_code=400, detail="Unknown trigger_type")

    import uuid
    job_id = f"task_{uuid.uuid4().hex[:8]}"
    result = await scheduler_manager.add_job(
        job_id, body.description, body.trigger_type, trigger_args, body.agent_role
    )
    if result.get("success"):
        return {"success": True, "job_id": job_id}
    raise HTTPException(status_code=500, detail=result.get("error"))


@app.get("/api/schedule")
@limiter.limit("30/minute")
async def schedule_list(request: Request):
    jobs = await scheduler_manager.list_jobs()
    return {"jobs": jobs}


@app.delete("/api/schedule/{job_id}")
@limiter.limit("10/minute")
async def schedule_delete(request: Request, job_id: str):
    if getattr(request.state, "user_role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    result = await scheduler_manager.remove_job(job_id)
    if result.get("success"):
        return {"success": True}
    raise HTTPException(status_code=404, detail=result.get("error"))


@app.get("/api/schedule/{job_id}/logs")
@limiter.limit("30/minute")
async def schedule_logs(request: Request, job_id: str):
    rows = db.fetchall(
        "SELECT * FROM scheduled_jobs_log WHERE job_id = ? ORDER BY executed_at DESC LIMIT 50",
        (job_id,),
    )
    return {"logs": [dict(r) for r in rows] if rows else []}


# ---------------------------------------------------------------------------
# Stats API
# ---------------------------------------------------------------------------

@app.get("/api/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request):
    agents = store.list_agents()
    total_skills = sum(len(a.get("skills", [])) for a in agents)
    total_tools = sum(len(a.get("tools", [])) for a in agents)
    installed = db.fetchall("SELECT * FROM installed_skills LIMIT 100")
    return {
        "agents": len(agents),
        "skills": total_skills,
        "tools": total_tools,
        "installed_skills": [dict(r) for r in installed] if installed else [],
        "model": config.get("model", {}).get("primary", "unknown"),
    }


# ---------------------------------------------------------------------------
# MCP Server API
# ---------------------------------------------------------------------------

@app.get("/api/mcp/list")
@limiter.limit("30/minute")
async def mcp_list(request: Request):
    servers = mcp_manager.list_servers()
    return {"servers": servers, "count": len(servers)}


@app.post("/api/mcp/start/{name}")
@limiter.limit("10/minute")
async def mcp_start(request: Request, name: str):
    success = await mcp_manager.start_server(name)
    handle = mcp_manager.get_server(name)
    return {
        "success": success,
        "tools": handle._tools_registered if handle else 0,
        "error": None if success else f"Failed to start {name}",
    }


@app.post("/api/mcp/stop/{name}")
@limiter.limit("10/minute")
async def mcp_stop(request: Request, name: str):
    await mcp_manager.stop_server(name)
    return {"success": True}


@app.post("/api/mcp/start-all")
@limiter.limit("5/minute")
async def mcp_start_all(request: Request):
    results = await mcp_manager.start_all()
    return {"success": all(results.values()), "results": results}


@app.post("/api/mcp/stop-all")
@limiter.limit("5/minute")
async def mcp_stop_all(request: Request):
    await mcp_manager.stop_all()
    return {"success": True}


# ---------------------------------------------------------------------------
# MCP Client API — connect to external MCP servers
# ---------------------------------------------------------------------------

@app.get("/api/mcp-clients")
@limiter.limit("30/minute")
async def mcp_clients_list(request: Request):
    """List connected external MCP servers."""
    connections = mcp_client_manager.list_connections()
    tools = mcp_client_manager.get_all_tools()
    return {
        "connections": connections,
        "tools": [{"name": t.get("name"), "description": t.get("description"), "server": t.get("_mcp_server")} for t in tools],
    }


@app.post("/api/mcp-clients/connect")
@limiter.limit("10/minute")
async def mcp_clients_connect(request: Request):
    """Connect to all configured external MCP servers."""
    await mcp_client_manager.connect_all()
    connections = mcp_client_manager.list_connections()
    return {"success": True, "connections": connections}


@app.post("/api/mcp-clients/{server_name}/call/{tool_name}")
@limiter.limit("60/minute")
async def mcp_clients_call(request: Request, server_name: str, tool_name: str):
    """Call a tool on an external MCP server."""
    body = await request.json()
    arguments = body.get("arguments", {})
    result = await mcp_client_manager.call_tool(server_name, tool_name, arguments)
    return {"result": result}


# ---------------------------------------------------------------------------
# Voice API — audio transcription and text-to-speech
# ---------------------------------------------------------------------------

from fastapi import UploadFile, File

@app.post("/api/transcribe")
@limiter.limit("30/minute")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    """Transcribe uploaded audio to text (requires OPENAI_API_KEY)."""
    import tempfile
    from skills.voice_io.skill import transcribe_audio as do_transcribe

    suffix = os.path.splitext(file.filename or ".mp3")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = do_transcribe(tmp_path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.post("/api/tts")
@limiter.limit("30/minute")
async def text_to_speech(request: Request):
    """Convert text to speech and return MP3 file."""
    from skills.voice_io.skill import speak_text as do_speak

    body = await request.json()
    text = body.get("text", "")
    voice = body.get("voice", "en-US-AriaNeural")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    import tempfile
    output_path = tempfile.mktemp(suffix=".mp3")
    try:
        result = await do_speak(text, voice, output_path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        from fastapi.responses import FileResponse
        return FileResponse(output_path, media_type="audio/mpeg", filename="tts.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Feedback API — thumbs up/down for training dataset
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    query: str
    response: str
    rating: int  # 1 or -1
    agent_id: str = "universal"
    model: str = ""
    tools_used: list = []


@app.post("/api/feedback")
@limiter.limit("60/minute")
async def submit_feedback_endpoint(request: Request, body: FeedbackRequest):
    """Submit user feedback on a response."""
    result = feedback_module.submit_feedback(
        session_id=body.session_id,
        message_id=body.message_id,
        query=body.query,
        response=body.response,
        rating=body.rating,
        agent_id=body.agent_id,
        model=body.model,
        tools_used=body.tools_used,
    )
    return result


@app.get("/api/feedback")
@limiter.limit("60/minute")
async def list_feedback_endpoint(request: Request, limit: int = 100, offset: int = 0, rating: int = None):
    """List feedback entries."""
    items = feedback_module.list_feedback(limit=limit, offset=offset, rating=rating)
    stats = feedback_module.get_feedback_stats()
    return {"items": items, "stats": stats}


@app.get("/api/feedback/export")
@limiter.limit("10/minute")
async def export_feedback_endpoint(request: Request):
    """Export feedback as training dataset (JSONL)."""
    filename = feedback_module.export_training_dataset()
    from fastapi.responses import FileResponse
    return FileResponse(filename, media_type="application/jsonl", filename="training_dataset.jsonl")


@app.get("/api/feedback/stats")
@limiter.limit("60/minute")
async def feedback_stats_endpoint(request: Request):
    """Get feedback statistics."""
    stats = feedback_module.get_feedback_stats()
    count = feedback_module.get_feedback_count()
    return {"stats": stats, "total_entries": count}


# ---------------------------------------------------------------------------
# WebSocket Chat (real-time alternative to SSE)
# ---------------------------------------------------------------------------

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Real-time bidirectional chat via WebSocket.

    Protocol:
      Client -> Server: {"type": "ask", "message": "...", "agent_id": "universal", "model": "fast"}
      Server -> Client: {"type": "chunk", "text": "..."}
      Server -> Client: {"type": "done", "text": "...", "model": "..."}
      Server -> Client: {"type": "error", "message": "..."}
      Client -> Server: {"type": "cancel"}
    """
    await websocket.accept()
    current_task = None

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "ask")

            if msg_type == "cancel":
                if current_task and not current_task.done():
                    current_task.cancel()
                    try:
                        await current_task
                    except asyncio.CancelledError:
                        pass
                await websocket.send_json({"type": "cancelled"})
                current_task = None
                continue

            if msg_type != "ask":
                await websocket.send_json({"type": "error", "message": "Unknown type. Use 'ask' or 'cancel'."})
                continue

            message = data.get("message", "")
            agent_id = data.get("agent_id", "universal")
            model_name = data.get("model", "fast")

            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            async def _run_agent():
                try:
                    from core.configurator import resolve_profile
                    agent_config = store.get_agent(agent_id)
                    if not agent_config:
                        await websocket.send_json({"type": "error", "message": f"Agent '{agent_id}' not found"})
                        return

                    model_config = resolve_profile(model_name)
                    if not model_config:
                        await websocket.send_json({"type": "error", "message": f"Unknown model: {model_name}"})
                        return

                    builder = (AgentBuilder()
                        .set_model(model_config)
                        .set_role(agent_config.get("role", ""))
                        .set_skills(agent_config.get("skills", []))
                        .set_tools(agent_config.get("tools", []))
                        .set_memory({"enabled": True}))
                    agent = builder.build()

                    # Send thinking indicator
                    await websocket.send_json({"type": "thinking", "model": model_config.get("primary", "unknown")})

                    # Run agent (async-native)
                    result = await agent.run(message)

                    # Stream result in chunks for better UX
                    chunk_size = 100
                    for i in range(0, len(result), chunk_size):
                        chunk = result[i:i + chunk_size]
                        await websocket.send_json({"type": "chunk", "text": chunk})

                    await websocket.send_json({
                        "type": "done",
                        "text": result,
                        "model": model_config.get("primary", "unknown"),
                        "agent": agent_id
                    })
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.exception("WebSocket agent error")
                    await websocket.send_json({"type": "error", "message": "Internal error occurred"})

            current_task = asyncio.create_task(_run_agent())

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error")
    finally:
        if current_task and not current_task.done():
            current_task.cancel()


# ---------------------------------------------------------------------------
# Real-time Collaboration — shared WebSocket rooms
# ---------------------------------------------------------------------------

_collab_rooms: Dict[str, List[WebSocket]] = {}

@app.websocket("/ws/room/{room_id}")
async def websocket_collaboration(websocket: WebSocket, room_id: str):
    """Real-time collaborative chat room.

    Multiple clients can join the same room_id to share a session.
    Messages broadcast to all connected clients in the room.

    Protocol:
      join  -> {"type": "join", "username": "Alice"}
      chat  -> {"type": "chat", "message": "Hello", "agent_id": "universal"}
      agent -> {"type": "agent_response", "text": "...", "model": "..."}
    """
    await websocket.accept()

    if room_id not in _collab_rooms:
        _collab_rooms[room_id] = []
    _collab_rooms[room_id].append(websocket)
    username = f"User-{len(_collab_rooms[room_id])}"

    async def _broadcast(room: str, message: Dict):
        """Send message to all clients in a room."""
        disconnected = []
        for ws in _collab_rooms.get(room, []):
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            if ws in _collab_rooms.get(room, []):
                _collab_rooms[room].remove(ws)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "join":
                username = data.get("username", username)
                await _broadcast(room_id, {"type": "system", "message": f"{username} joined the room"})
                continue

            if msg_type == "chat":
                message = data.get("message", "")
                agent_id = data.get("agent_id", "universal")
                await _broadcast(room_id, {
                    "type": "chat",
                    "username": username,
                    "message": message,
                    "agent_id": agent_id,
                })

                # Optionally run agent response automatically
                if data.get("auto_agent", False):
                    agent_config = store.get_agent(agent_id)
                    if agent_config:
                        from core.configurator import resolve_profile
                        model_config = resolve_profile(data.get("model", "fast"))
                        builder = (AgentBuilder()
                            .set_model(model_config or {})
                            .set_role(agent_config.get("role", ""))
                            .set_skills(agent_config.get("skills", []))
                            .set_tools(agent_config.get("tools", []))
                            .set_memory({"enabled": True}))
                        agent = builder.build()
                        result = await agent.run(message)
                        await _broadcast(room_id, {
                            "type": "agent_response",
                            "text": result,
                            "model": model_config.get("primary", "unknown") if model_config else "unknown",
                            "agent": agent_id,
                        })
                continue

    except WebSocketDisconnect:
        if websocket in _collab_rooms.get(room_id, []):
            _collab_rooms[room_id].remove(websocket)
        await _broadcast(room_id, {"type": "system", "message": f"{username} left the room"})
    except Exception:
        if websocket in _collab_rooms.get(room_id, []):
            _collab_rooms[room_id].remove(websocket)
