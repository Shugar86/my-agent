import copy
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


def load_config(path=None):
    """Load merged agent config from JSON (primary) or YAML (legacy fallback)."""
    if path is None:
        path = "config/agent.json"
    user_config = load_agent_config(path)
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
    result = copy.deepcopy(default)
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


def resolve_agent_model_config(
    agent_config: dict,
    *,
    default_path: str = "config/agent.json",
) -> dict:
    """Resolve LLM model config from an agent registry entry.

    Supports:
    - full model dict (``config/agent.json`` style)
    - profile name (``kimi``, ``fast``, …)
    - legacy model id string + agent-level api_key/base_url
    - fallback to ``config/agent.json`` then DEFAULT_CONFIG
    """
    from core.configurator import MODEL_PROFILES, resolve_profile

    raw_model = agent_config.get("model")

    if isinstance(raw_model, dict) and raw_model:
        return resolve_env_vars(raw_model)

    if isinstance(raw_model, str) and raw_model in MODEL_PROFILES:
        profile = resolve_profile(raw_model)
        if profile:
            return profile

    if isinstance(raw_model, str) and raw_model:
        return resolve_env_vars({
            "primary": raw_model,
            "api_key": agent_config.get("api_key", ""),
            "base_url": agent_config.get("base_url", ""),
        })

    defaults = load_agent_config(default_path)
    fallback = defaults.get("model") or DEFAULT_CONFIG.get("model", {})
    return resolve_env_vars(fallback)
