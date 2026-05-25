import json
import os
import uuid
from datetime import datetime
from copy import deepcopy


class AgentStore:
    def __init__(self, registry_path="agents/registry.json"):
        self.registry_path = registry_path
        self._ensure_registry()

    def _ensure_registry(self):
        if not os.path.exists(self.registry_path):
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            self._save({"agents": []})

    def _load(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_agents(self):
        data = self._load()
        return data.get("agents", [])

    def get_agent(self, agent_id):
        data = self._load()
        for agent in data.get("agents", []):
            if agent["id"] == agent_id:
                return deepcopy(agent)
        return None

    def save_agent(self, agent_config):
        data = self._load()
        agent_id = agent_config.get("id", str(uuid.uuid4())[:8])
        agent_config["id"] = agent_id
        agent_config["updated_at"] = datetime.now().strftime("%Y-%m-%d")

        for i, existing in enumerate(data["agents"]):
            if existing["id"] == agent_id:
                if "created_at" not in agent_config:
                    agent_config["created_at"] = existing.get("created_at", datetime.now().strftime("%Y-%m-%d"))
                data["agents"][i] = agent_config
                self._save(data)
                return agent_id

        if "created_at" not in agent_config:
            agent_config["created_at"] = datetime.now().strftime("%Y-%m-%d")
        data["agents"].append(agent_config)
        self._save(data)
        return agent_id

    def delete_agent(self, agent_id):
        data = self._load()
        data["agents"] = [a for a in data["agents"] if a["id"] != agent_id]
        self._save(data)

    def duplicate_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        new_id = f"{agent['id']}-copy-{str(uuid.uuid4())[:4]}"
        agent["id"] = new_id
        agent["name"] = f"{agent['name']} (copy)"
        agent["created_at"] = datetime.now().strftime("%Y-%m-%d")
        agent["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        self.save_agent(agent)
        return new_id

    def get_agent_ids(self):
        return [a["id"] for a in self.list_agents()]
