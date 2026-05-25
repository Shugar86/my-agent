import concurrent.futures
import threading
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._lock = threading.Lock()

    def register(self, name, description, parameters, execute_fn):
        with self._lock:
            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "execute": execute_fn,
            }

    def unregister(self, name):
        with self._lock:
            self._tools.pop(name, None)

    def get(self, name):
        return self._tools.get(name)

    def has(self, name):
        return name in self._tools

    def list_all(self):
        return list(self._tools.values())

    def get_schemas(self):
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        return schemas

    def execute(self, name, timeout: int = 60, **kwargs):
        """Execute tool with timeout and audit logging."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        logger.info("Tool execute: %s(args=%s)", name, {k: v for k, v in kwargs.items() if k not in ("password", "api_key", "token", "secret")})
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(tool["execute"], **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.error("Tool '%s' timed out after %ds", name, timeout)
                return {"error": f"Tool '{name}' timed out after {timeout}s"}


registry = ToolRegistry()
