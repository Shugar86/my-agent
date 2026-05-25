"""Agent/skill node handler."""

from __future__ import annotations

import logging
from typing import Any

from core.agent_store import AgentStore
from core.builder import AgentBuilder
from core.config import resolve_env_vars, load_config
from core.workflow.models import RunContext
from core.workflow.registry import register_node_handler

logger = logging.getLogger(__name__)
_store = AgentStore()


async def handle_agent_skill(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Run an agent with optional role/skills override."""
    resolved = ctx.resolve_config(config)
    prompt = resolved.get("prompt", "")
    agent_id = resolved.get("agent_id") or resolved.get("role", "universal")

    agent_config = _store.get_agent(agent_id)
    if not agent_config:
        agent_config = _store.get_agent("universal") or {}

    raw_model = agent_config.get("model") or load_config().get("model", {})
    if isinstance(raw_model, str):
        raw_model = load_config().get("model", {})
    model_config = resolve_env_vars(raw_model)

    skills = resolved.get("skills") or agent_config.get("skills", [])
    tools = resolved.get("tools") or agent_config.get("tools", [])
    role = resolved.get("role_text") or agent_config.get("role", "You are a helpful assistant.")

    builder = (
        AgentBuilder()
        .set_model(model_config)
        .set_role(role)
        .set_skills(skills)
        .set_tools(tools)
        .set_memory({"enabled": False})
        .enable_events(False)
        .enable_compression(True)
    )
    agent = builder.build()
    result = await agent.run(prompt)
    output = {"output": result, "agent_id": agent_id}
    return output


def register_agent_handlers() -> None:
    """Register agent node handlers."""
    register_node_handler("agent.skill", handle_agent_skill)
