"""Async-native Orchestrator with no run_in_executor wrappers."""
from core.builder import AgentBuilder
from core.sub_agents import run_parallel_agents, run_parallel_agents_async
from core.config import resolve_env_vars


class Orchestrator:
    def __init__(self, agent_store):
        self.store = agent_store

    async def run(self, user_input, agent_id, session_id=None):
        """Async-native entry point (used by CLI and Web API)."""
        agent_config = self.store.get_agent(agent_id)
        if not agent_config:
            return {"error": f"Agent '{agent_id}' not found"}

        sub_agents = agent_config.get("sub_agents", [])

        if len(sub_agents) > 0:
            return await self._parallel_delegate(user_input, agent_config, sub_agents)
        else:
            return await self._handoff(user_input, agent_config, session_id)

    async def run_with_auto_agents(self, user_input, agent_id, factory):
        """Async wrapper for auto-agent factory spawning."""
        return await factory.spawn_for_task(user_input, agent_id)

    async def _handoff(self, user_input, agent_config, session_id=None):
        raw_model = agent_config.get("model", {})
        if isinstance(raw_model, str):
            # Model is specified as a string ID, load default config
            from core.config import DEFAULT_CONFIG
            raw_model = DEFAULT_CONFIG.get("model", {})
        model_config = resolve_env_vars(raw_model)
        builder = (AgentBuilder()
            .set_model(model_config)
            .set_role(agent_config.get("role", ""))
            .set_skills(agent_config.get("skills", []))
            .set_tools(agent_config.get("tools", []))
            .set_memory(agent_config.get("memory", {"enabled": False}))
            .enable_events(True)
            .enable_compression(True)
            .enable_plugins(True)
        )
        agent = builder.build()
        return await agent.run(user_input, session_id=session_id)

    async def _parallel_delegate(self, user_input, agent_config, sub_agent_ids):
        """Async parallel delegate using asyncio.gather."""
        sub_configs = []
        for sub_id in sub_agent_ids:
            sub_config = self.store.get_agent(sub_id)
            if sub_config:
                sub_config["model"] = resolve_env_vars(sub_config.get("model", {}))
                sub_configs.append(sub_config)

        if not sub_configs:
            return await self._handoff(user_input, agent_config)

        results = await run_parallel_agents_async(user_input, sub_configs)
        return self._synthesize_results(results, agent_config)

    def _synthesize_results(self, results, agent_config):
        parts = []
        for sub_id, result in results.items():
            parts.append(f"### {sub_id}\n\n{result}")
        return "\n\n---\n\n".join(parts)
