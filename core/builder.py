import time
import functools
from core.llm_gateway import LLMGateway
from core.skill_loader import SkillLoader
from core.memory_manager import MemoryManager
from core.event_bus import EventBus
from core.context_compressor import ContextCompressor
from core.plugin_manager import PluginManager
from core.config import SKILLS_DIRS


# Module-level skill loader cache — loaded once, reused across builds.
# This avoids ~50-200ms of YAML parsing + module import on every request.
_skill_loader_cache = None
_skill_loader_timestamp = 0
_SKILL_CACHE_TTL = 300  # 5 minutes


def _get_cached_skill_loader():
    """Return a cached SkillLoader, refreshing only after TTL expires."""
    global _skill_loader_cache, _skill_loader_timestamp
    now = time.time()
    if _skill_loader_cache is None or (now - _skill_loader_timestamp) > _SKILL_CACHE_TTL:
        loader = SkillLoader(SKILLS_DIRS)
        loader.load_all()
        _skill_loader_cache = loader
        _skill_loader_timestamp = now
    return _skill_loader_cache


def invalidate_skill_cache():
    """Force refresh of the skill loader cache (e.g. after skill install)."""
    global _skill_loader_cache, _skill_loader_timestamp
    _skill_loader_cache = None
    _skill_loader_timestamp = 0


class AgentBuilder:
    def __init__(self):
        self._model_config = None
        self._role = ""
        self._skill_names = []
        self._tool_names = []
        self._memory_config = {"enabled": False, "scope": "none"}
        self._integrations = {}
        self._enable_events = True
        self._enable_compression = True
        self._enable_plugins = True

    def set_model(self, model_config):
        self._model_config = model_config
        return self

    def set_role(self, role_text):
        self._role = role_text
        return self

    def add_skills(self, skill_names):
        self._skill_names.extend(skill_names)
        return self

    def set_skills(self, skill_names):
        self._skill_names = skill_names
        return self

    def set_tools(self, tool_names):
        self._tool_names = tool_names
        return self

    def set_memory(self, memory_config):
        self._memory_config = memory_config
        return self

    def add_integration(self, name, config):
        self._integrations[name] = config
        return self

    def enable_events(self, enabled=True):
        self._enable_events = enabled
        return self

    def enable_compression(self, enabled=True, max_tokens=4000):
        self._enable_compression = enabled
        self._max_tokens = max_tokens
        return self

    def enable_plugins(self, enabled=True):
        self._enable_plugins = enabled
        return self

    def build(self):
        from core.runtime import AgentRuntime

        llm = LLMGateway(self._model_config or {})

        # Use cached skill loader to avoid reloading from disk on every build
        skills = _get_cached_skill_loader()

        for name in self._skill_names:
            if name not in skills.skills:
                print(f"Warning: skill '{name}' not found")
            else:
                skills.enable(name)

        memory = MemoryManager(self._memory_config)

        events = EventBus() if self._enable_events else None

        compressor = None
        if self._enable_compression:
            compressor = ContextCompressor(
                llm,
                max_tokens=getattr(self, "_max_tokens", 4000),
            )

        plugins = PluginManager() if self._enable_plugins else None
        if plugins:
            plugins.discover()

        return AgentRuntime(
            llm=llm,
            role=self._role,
            skills=skills,
            memory=memory,
            tool_names=self._tool_names,
            integrations=self._integrations,
            events=events,
            compressor=compressor,
            plugins=plugins,
        )
