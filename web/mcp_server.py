"""MCP (Model Context Protocol) Server for My Agent.

Implements JSON-RPC 2.0 style MCP endpoints compatible with Claude Desktop,
Cursor, and other MCP clients.

Endpoints:
  POST /mcp/v1/     — JSON-RPC 2.0 endpoint
  GET  /mcp/sse     — SSE streaming endpoint
"""
import json
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/mcp/v1", tags=["mcp"])


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPError(Exception):
    """MCP protocol error with code."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


def _make_response(request_id: Optional[str], result: Any = None, error: Optional[Dict] = None) -> Dict:
    response = {"jsonrpc": "2.0", "id": request_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response


def _make_error(request_id: Optional[str], code: int, message: str, data: Any = None) -> Dict:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return _make_response(request_id, error=error)


# ---------------------------------------------------------------------------
# Tool Discovery & Execution
# ---------------------------------------------------------------------------

def _list_tools() -> List[Dict]:
    """Return all registered tools in MCP format."""
    from core.tool_registry import registry
    tools = []
    for name, meta in registry._tools.items():
        tools.append({
            "name": name,
            "description": meta.get("description", ""),
            "inputSchema": meta.get("parameters", {"type": "object"}),
        })
    return tools


async def _call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a registered tool."""
    from core.tool_registry import registry
    meta = registry._tools.get(name)
    if not meta:
        raise MCPError(MCPError.METHOD_NOT_FOUND, f"Tool not found: {name}")
    
    fn = meta.get("execute")
    if not fn:
        raise MCPError(MCPError.INTERNAL_ERROR, f"Tool {name} has no execute handler")
    
    try:
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**arguments)
        else:
            result = fn(**arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}], "isError": False}
    except Exception as e:
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}


# ---------------------------------------------------------------------------
# Resource Discovery & Read
# ---------------------------------------------------------------------------

def _list_resources() -> List[Dict]:
    """Return available resources."""
    from core.agent_store import AgentStore
    store = AgentStore()
    agents = store.list_agents()
    resources = []
    
    # Agent configs as resources
    for agent in agents:
        resources.append({
            "uri": f"agent://{agent['id']}",
            "name": agent.get("name", agent["id"]),
            "mimeType": "application/json",
            "description": agent.get("description", f"Agent {agent['id']}"),
        })
    
    # Skills as resources
    from core.skill_loader import SkillLoader
    try:
        loader = SkillLoader()
        loader.load_all()
        for skill_name in loader.skills:
            resources.append({
                "uri": f"skill://{skill_name}",
                "name": skill_name,
                "mimeType": "text/markdown",
                "description": f"Skill: {skill_name}",
            })
    except Exception:
        pass
    
    return resources


async def _read_resource(uri: str) -> Dict:
    """Read a resource by URI."""
    if uri.startswith("agent://"):
        agent_id = uri.replace("agent://", "")
        from core.agent_store import AgentStore
        store = AgentStore()
        agent = store.get_agent(agent_id)
        if not agent:
            raise MCPError(MCPError.INVALID_PARAMS, f"Agent not found: {agent_id}")
        return {
            "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(agent, ensure_ascii=False, indent=2)}]
        }
    
    if uri.startswith("skill://"):
        skill_name = uri.replace("skill://", "").strip("/")
        if not skill_name or ".." in skill_name or "/" in skill_name or "\\" in skill_name:
            raise MCPError(MCPError.INVALID_PARAMS, f"Invalid skill URI: {uri}")
        from pathlib import Path

        skills_root = Path("skills").resolve()
        skill_path = (skills_root / skill_name / "README.md").resolve()
        if not str(skill_path).startswith(str(skills_root)):
            raise MCPError(MCPError.INVALID_PARAMS, f"Invalid skill URI: {uri}")
        try:
            text = skill_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            text = f"No README for skill: {skill_name}"
        return {
            "contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]
        }
    
    raise MCPError(MCPError.INVALID_PARAMS, f"Unknown resource URI: {uri}")


# ---------------------------------------------------------------------------
# Prompt Discovery & Get
# ---------------------------------------------------------------------------

def _list_prompts() -> List[Dict]:
    """Return available prompts."""
    return [
        {
            "name": "universal-assistant",
            "description": "Universal assistant system prompt",
            "arguments": [
                {"name": "task", "description": "Task description", "required": True},
            ],
        },
        {
            "name": "code-reviewer",
            "description": "Code review prompt",
            "arguments": [
                {"name": "code", "description": "Code to review", "required": True},
                {"name": "language", "description": "Programming language", "required": False},
            ],
        },
        {
            "name": "researcher",
            "description": "Deep research prompt",
            "arguments": [
                {"name": "topic", "description": "Research topic", "required": True},
            ],
        },
    ]


def _get_prompt(name: str, arguments: Optional[Dict] = None) -> Dict:
    """Get a prompt by name with substituted arguments."""
    arguments = arguments or {}
    
    prompts = {
        "universal-assistant": """You are a universal AI assistant with access to {skills_count} skills and {tools_count} tools.
Your task: {task}
Analyze the request, select appropriate skills and tools, and execute step by step.
Always return results in a structured format.""",
        "code-reviewer": """You are an expert code reviewer. Review the following {language} code:

{code}

Provide feedback on:
1. Correctness and bugs
2. Performance optimizations
3. Security issues
4. Code style and readability
5. Test coverage suggestions""",
        "researcher": """You are a deep research assistant. Research the topic: {topic}
Use web search and multiple sources. Provide a comprehensive summary with citations.
Structure your response with clear sections.""",
    }
    
    template = prompts.get(name)
    if not template:
        raise MCPError(MCPError.INVALID_PARAMS, f"Prompt not found: {name}")
    
    try:
        text = template.format(**arguments)
    except KeyError as e:
        raise MCPError(MCPError.INVALID_PARAMS, f"Missing argument: {e}")
    
    return {
        "description": f"Prompt: {name}",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": text}}
        ],
    }


# ---------------------------------------------------------------------------
# JSON-RPC Handler
# ---------------------------------------------------------------------------

@router.post("/")
async def mcp_endpoint(request: Request):
    """Main MCP JSON-RPC 2.0 endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_make_error(None, MCPError.PARSE_ERROR, "Parse error"))
    
    # Handle batch requests
    if isinstance(body, list):
        responses = []
        for req in body:
            responses.append(await _handle_single_request(req))
        return JSONResponse([r for r in responses if r is not None])
    
    response = await _handle_single_request(body)
    return JSONResponse(response)


async def _handle_single_request(body: Dict) -> Optional[Dict]:
    """Handle a single JSON-RPC request."""
    request_id = body.get("id")
    
    if not isinstance(body, dict):
        return _make_error(request_id, MCPError.INVALID_REQUEST, "Invalid Request")
    
    if body.get("jsonrpc") != "2.0":
        return _make_error(request_id, MCPError.INVALID_REQUEST, "Invalid JSON-RPC version")
    
    method = body.get("method")
    if not method or not isinstance(method, str):
        return _make_error(request_id, MCPError.INVALID_REQUEST, "Method must be a string")
    
    params = body.get("params", {})
    
    try:
        # Tool methods
        if method == "tools/list":
            return _make_response(request_id, {"tools": _list_tools()})
        
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                raise MCPError(MCPError.INVALID_PARAMS, "Tool name required")
            result = await _call_tool(name, arguments)
            return _make_response(request_id, result)
        
        # Resource methods
        if method == "resources/list":
            return _make_response(request_id, {"resources": _list_resources()})
        
        if method == "resources/read":
            uri = params.get("uri")
            if not uri:
                raise MCPError(MCPError.INVALID_PARAMS, "URI required")
            result = await _read_resource(uri)
            return _make_response(request_id, result)
        
        # Prompt methods
        if method == "prompts/list":
            return _make_response(request_id, {"prompts": _list_prompts()})
        
        if method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                raise MCPError(MCPError.INVALID_PARAMS, "Prompt name required")
            result = _get_prompt(name, arguments)
            return _make_response(request_id, result)
        
        # Utility methods
        if method == "initialize":
            return _make_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "my-agent-mcp",
                    "version": "2.1.0",
                },
            })
        
        if method == "ping":
            return _make_response(request_id, {})
        
        return _make_error(request_id, MCPError.METHOD_NOT_FOUND, f"Method not found: {method}")
    
    except MCPError as e:
        return _make_error(request_id, e.code, e.message, e.data)
    except Exception as e:
        return _make_error(request_id, MCPError.INTERNAL_ERROR, f"Internal error: {str(e)}")


# ---------------------------------------------------------------------------
# SSE Endpoint
# ---------------------------------------------------------------------------

@router.get("/sse")
async def mcp_sse():
    """SSE endpoint for MCP notifications."""
    async def event_stream():
        yield "event: endpoint\ndata: /mcp/v1/\n\n"
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield "event: ping\ndata: {}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
