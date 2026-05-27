import os
import sys
import logging
import yaml
import importlib.util
from pathlib import Path

logger = logging.getLogger(__name__)

# Skills blocked in production unless explicitly enabled.
PRODUCTION_BLOCKED_SKILLS = {"self_dev"}
_IS_PRODUCTION = os.environ.get("ENV", "").lower() == "production"
_SELF_DEV_ENABLED = os.environ.get("ENABLE_SELF_DEV", "false").lower() in ("true", "1", "yes")


def _skill_allowed(name: str) -> bool:
    """Return False if a skill must not load in the current environment."""
    if name not in PRODUCTION_BLOCKED_SKILLS:
        return True
    if not _IS_PRODUCTION:
        return True
    return _SELF_DEV_ENABLED


class SkillLoader:
    def __init__(self, skills_dirs=None):
        self.skills_dirs = skills_dirs or ["skills/"]
        self.skills = {}

    def load_all(self):
        for skills_dir in self.skills_dirs:
            dir_path = Path(skills_dir)
            if not dir_path.exists():
                continue
            for skill_dir in dir_path.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    self._load_skill(skill_dir)

    def _load_skill(self, skill_dir):
        metadata = self._parse_skill_md(skill_dir / "SKILL.md")
        name = metadata["name"]

        if not _skill_allowed(name):
            self.skills[name] = {
                "metadata": metadata,
                "module": None,
                "enabled": False,
                "path": str(skill_dir),
                "blocked": True,
            }
            return

        try:
            module = None
            skill_py = skill_dir / "skill.py"
            if skill_py.exists():
                module = self._import_module(skill_py)

            self.skills[name] = {
                "metadata": metadata,
                "module": module,
                "enabled": True,
                "path": str(skill_dir),
            }

            if module and hasattr(module, "register_tools"):
                module.register_tools()
        except Exception as exc:
            logger.warning("Failed to load skill %s from %s: %s", name, skill_dir, exc)
            self.skills[name] = {
                "metadata": metadata,
                "module": None,
                "enabled": False,
                "path": str(skill_dir),
                "error": str(exc),
            }

    def _parse_skill_md(self, path):
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1])
        return {"name": path.parent.name, "description": ""}

    def _import_module(self, path):
        project_root = str(Path(__file__).resolve().parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        spec = importlib.util.spec_from_file_location("skill_" + path.parent.name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def enable(self, name):
        if name in self.skills and not _skill_allowed(name):
            return
        if name in self.skills:
            self.skills[name]["enabled"] = True
            if self.skills[name]["module"] and hasattr(self.skills[name]["module"], "register_tools"):
                self.skills[name]["module"].register_tools()

    def disable(self, name):
        if name in self.skills:
            self.skills[name]["enabled"] = False
            if self.skills[name]["module"] and hasattr(self.skills[name]["module"], "unregister_tools"):
                self.skills[name]["module"].unregister_tools()

    def get_active(self):
        return {n: s for n, s in self.skills.items() if s["enabled"]}

    def get_context(self):
        parts = []
        for name, skill in self.get_active().items():
            meta = skill["metadata"]
            parts.append(f"## Skill: {name}")
            parts.append(f"Description: {meta.get('description', '')}")
            tools = meta.get("tools", [])
            if tools:
                parts.append(f"Available tools: {', '.join(tools)}")
        return "\n\n".join(parts)

    def get_schemas(self, tool_names=None):
        from core.tool_registry import registry
        if tool_names:
            schemas = []
            for name in tool_names:
                if registry.has(name):
                    t = registry.get(name)
                    schemas.append({
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["parameters"],
                        },
                    })
            return schemas
        return registry.get_schemas()

    def execute_tool(self, name, **kwargs):
        from core.tool_registry import registry
        return registry.execute(name, **kwargs)
