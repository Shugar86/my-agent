import json
import os
import yaml

DEFAULT_CONFIG = {
    "name": "",
    "description": "",
    "model": {
        "primary": "openrouter/mistralai/mistral-large",
        "fallback": "openai/gpt-4o-mini",
    },
    "role": "Ты — полезный ассистент.",
    "skills": [],
    "tools": [],
    "integrations": {},
    "memory": {
        "enabled": True,
        "scope": "task",
    },
    "output": {
        "format": "markdown",
        "path": "",
    },
}

SKILLS_DIRS = [
    "skills/",
    os.path.expanduser("~/.agent/skills/"),
]


def load_config(path="config/agent.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}
    return _merge(DEFAULT_CONFIG, user_config)


def load_models_config(path="config/models.yaml"):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config, path):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _merge(default, override):
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_agent_config(path="config/agent.json"):
    """Load agent config from JSON (primary) or YAML (legacy fallback)."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback to YAML
    yaml_path = path.replace(".json", ".yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def resolve_env_vars(config):
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            resolved[key] = os.environ.get(env_var, value)
        elif isinstance(value, dict):
            resolved[key] = resolve_env_vars(value)
        else:
            resolved[key] = value
    return resolved
