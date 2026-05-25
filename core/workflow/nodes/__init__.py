"""Workflow node handlers package."""

from core.workflow.nodes.action import register_action_handlers
from core.workflow.nodes.agent import register_agent_handlers
from core.workflow.nodes.condition import register_condition_handlers
from core.workflow.nodes.trigger import register_trigger_handlers


def register_all_handlers() -> None:
    """Register all workflow node handlers."""
    register_trigger_handlers()
    register_agent_handlers()
    register_condition_handlers()
    register_action_handlers()
