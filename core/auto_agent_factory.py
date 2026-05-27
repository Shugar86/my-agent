import json
import uuid
import os
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.agent_store import AgentStore
from core.orchestrator import Orchestrator
from core.llm_gateway import LLMGateway
from core.config import resolve_env_vars
from core.async_utils import run_coro_sync


def _run_async(coro):
    """Run an async coroutine from sync code."""
    return run_coro_sync(coro)


class AutoAgentFactory:
    def __init__(self, agent_store, llm_config=None):
        self.store = agent_store
        self.orchestrator = Orchestrator(agent_store)
        self.llm = LLMGateway(llm_config or {})
        self.temp_dir = "agents/temp"
        os.makedirs(self.temp_dir, exist_ok=True)

    def spawn_for_task(self, task_description, parent_agent_id=None):
        sub_agents = self._analyze_task(task_description)

        if not sub_agents:
            return _run_async(self.orchestrator.run(task_description, parent_agent_id or "researcher"))

        temp_ids = []
        for sa in sub_agents:
            config = self._create_temp_config(sa, parent_agent_id)
            temp_id = self.store.save_agent(config)
            temp_ids.append(temp_id)

        results = {}
        sub_configs = [self.store.get_agent(tid) for tid in temp_ids if self.store.get_agent(tid)]

        if len(sub_configs) == 1:
            results[temp_ids[0]] = _run_async(self.orchestrator.run(task_description, temp_ids[0]))
        else:
            with ThreadPoolExecutor(max_workers=len(sub_configs)) as executor:
                futures = {}
                for config in sub_configs:
                    future = executor.submit(_run_async, self.orchestrator.run(task_description, config["id"]))
                    futures[future] = config["id"]

                for future in as_completed(futures):
                    agent_id = futures[future]
                    try:
                        results[agent_id] = future.result()
                    except Exception as e:
                        results[agent_id] = f"Error: {str(e)}"

        for temp_id in temp_ids:
            self.store.delete_agent(temp_id)

        return self._synthesize(results, sub_agents)

    def _get_available_skills(self):
        """Dynamically load available skills from skill_loader."""
        try:
            from core.skill_loader import SkillLoader
            loader = SkillLoader()
            loader.load_all()
            return list(loader.skills.keys())
        except Exception:
            return ["deep_research", "research", "parsing", "template", "code_analysis", "code_execution", "web_automation", "api_integration"]

    def _analyze_task(self, task_description):
        skills = self._get_available_skills()
        prompt = f"""Analyze this task and determine what sub-agents are needed.
Return a JSON array of sub-agent definitions.

Task: {task_description}

Available skills: {', '.join(skills)}

Return JSON like:
[{{"name": "researcher", "role": "...", "skills": ["deep_research"], "tools": ["deep_search"]}}, ...]

If only one agent is needed, return empty array []."""

        try:
            response = _run_async(self.llm.chat([
                {"role": "system", "content": "You are an agent planner. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]))
            content = response.content or "[]"
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            sub_agents = json.loads(content.strip())
            return sub_agents if isinstance(sub_agents, list) else []
        except Exception:
            return []

    def _create_temp_config(self, sub_agent, parent_agent_id):
        parent = self.store.get_agent(parent_agent_id) if parent_agent_id else None
        model = resolve_env_vars(parent.get("model", {})) if parent else {}

        return {
            "id": f"temp-{sub_agent.get('name', 'agent')}-{str(uuid.uuid4())[:6]}",
            "name": sub_agent.get("name", "Sub-Agent"),
            "icon": "🤖",
            "description": f"Auto-created sub-agent: {sub_agent.get('name', '')}",
            "role": sub_agent.get("role", "You are a helpful assistant."),
            "model": {
                "primary": model.get("primary", "openrouter/deepseek/deepseek-v4-flash:free"),
                "api_key": model.get("api_key", ""),
                "fallback": model.get("fallback", "openrouter/deepseek/deepseek-chat"),
                "params": model.get("params", {"temperature": 0.5, "max_tokens": 4096})
            },
            "skills": sub_agent.get("skills", []),
            "tools": sub_agent.get("tools", []),
            "sub_agents": [],
            "memory": {"enabled": False},
            "output": {"format": "markdown", "path": ""},
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "_temp": True
        }

    def _synthesize(self, results, sub_agents):
        parts = []
        for i, (agent_id, result) in enumerate(results.items()):
            name = sub_agents[i].get("name", agent_id) if i < len(sub_agents) else agent_id
            parts.append(f"## {name}\n\n{result}")
        return "\n\n---\n\n".join(parts)
