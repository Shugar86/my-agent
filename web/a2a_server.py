"""A2A (Agent-to-Agent) Protocol endpoints.

Implements basic A2A messaging for agent-to-agent communication.
Endpoints:
  POST /api/a2a/send     — Send message to another agent
  POST /api/a2a/receive  — Receive messages for this agent
  GET  /api/a2a/agents   — List discoverable agents
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/a2a", tags=["a2a"])

# In-memory message queue (production: use Redis or DB)
_message_queue: List[Dict] = []


class A2AMessage(BaseModel):
    sender: str
    recipient: str
    type: str = "request"  # request, response, broadcast
    content: str
    task_id: Optional[str] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    ttl: int = 3600  # seconds


class A2ASendResponse(BaseModel):
    message_id: str
    status: str
    timestamp: str


@router.post("/send")
async def a2a_send(request: Request, msg: A2AMessage):
    """Send a message to another agent."""
    message_id = f"a2a-{uuid.uuid4().hex[:12]}"
    
    message = {
        "id": message_id,
        "sender": msg.sender,
        "recipient": msg.recipient,
        "type": msg.type,
        "content": msg.content,
        "task_id": msg.task_id or message_id,
        "skills": msg.skills or [],
        "tools": msg.tools or [],
        "ttl": msg.ttl,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    
    _message_queue.append(message)
    
    # If recipient is local agent, try to process immediately
    if msg.type == "request":
        from core.agent_store import AgentStore
        store = AgentStore()
        recipient_agent = store.get_agent(msg.recipient)
        
        if recipient_agent:
            # Auto-process with recipient agent
            try:
                from core.builder import AgentBuilder
                from core.config import resolve_env_vars
                
                model_config = resolve_env_vars(recipient_agent.get("model", {}))
                builder = (AgentBuilder()
                    .set_model(model_config)
                    .set_role(recipient_agent.get("role", ""))
                    .set_skills(recipient_agent.get("skills", []))
                    .set_tools(recipient_agent.get("tools", []))
                    .set_memory({"enabled": False}))
                agent = builder.build()
                
                import asyncio
                result = await agent.run(msg.content)
                
                # Send response back
                response_msg = {
                    "id": f"a2a-{uuid.uuid4().hex[:12]}",
                    "sender": msg.recipient,
                    "recipient": msg.sender,
                    "type": "response",
                    "content": result,
                    "task_id": message["task_id"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed",
                }
                _message_queue.append(response_msg)
                message["status"] = "completed"
                
            except Exception as e:
                message["status"] = "failed"
                message["error"] = str(e)
    
    return {
        "message_id": message_id,
        "status": message["status"],
        "timestamp": message["timestamp"],
    }


@router.post("/receive")
async def a2a_receive(request: Request, body: Dict[str, Any]):
    """Receive messages for an agent."""
    recipient = body.get("recipient")
    msg_type = body.get("type")  # filter by type
    since = body.get("since")
    
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient required")
    
    messages = []
    for msg in _message_queue:
        # Skip expired messages
        if msg.get("ttl", 3600) <= 0:
            continue
        
        # Filter by recipient
        if msg.get("recipient") != recipient and msg.get("type") != "broadcast":
            continue
        
        # Filter by type
        if msg_type and msg.get("type") != msg_type:
            continue
        
        # Filter by timestamp
        if since and msg.get("timestamp", "") < since:
            continue
        
        messages.append(msg)
    
    # Mark as delivered
    for msg in messages:
        if msg.get("status") == "pending":
            msg["status"] = "delivered"
    
    return {"messages": messages, "count": len(messages)}


@router.get("/agents")
async def a2a_list_agents(request: Request):
    """List discoverable agents."""
    from core.agent_store import AgentStore
    store = AgentStore()
    agents = store.list_agents()
    
    result = []
    for agent in agents:
        result.append({
            "id": agent["id"],
            "name": agent.get("name", agent["id"]),
            "description": agent.get("description", ""),
            "skills": agent.get("skills", []),
            "tools": agent.get("tools", []),
            "capabilities": ["text", "tools", "skills"],
        })
    
    return {"agents": result, "count": len(result)}


@router.post("/broadcast")
async def a2a_broadcast(request: Request, msg: A2AMessage):
    """Broadcast a message to all agents."""
    message_id = f"a2a-broadcast-{uuid.uuid4().hex[:12]}"
    
    message = {
        "id": message_id,
        "sender": msg.sender,
        "recipient": "*",
        "type": "broadcast",
        "content": msg.content,
        "task_id": msg.task_id or message_id,
        "skills": msg.skills or [],
        "tools": msg.tools or [],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    
    _message_queue.append(message)
    
    return {
        "message_id": message_id,
        "status": "broadcast",
        "timestamp": message["timestamp"],
    }
