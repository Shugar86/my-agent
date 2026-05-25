import requests
import json
from core.tool_registry import registry


class MCPClient:
    def __init__(self, server_url, timeout=30):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._tools = {}

    def connect(self):
        try:
            response = requests.get(f"{self.server_url}/tools", timeout=self.timeout)
            response.raise_for_status()
            tools_data = response.json()
            for tool in tools_data:
                self._register_mcp_tool(tool)
            return True
        except Exception as e:
            return False

    def _register_mcp_tool(self, tool_info):
        name = f"mcp_{tool_info['name']}"

        def execute_fn(**kwargs):
            return self._call_tool(tool_info["name"], kwargs)

        registry.register(
            name=name,
            description=tool_info.get("description", ""),
            parameters=tool_info.get("inputSchema", {"type": "object", "properties": {}}),
            execute_fn=execute_fn,
        )
        self._tools[name] = tool_info["name"]

    def _call_tool(self, tool_name, args):
        try:
            response = requests.post(
                f"{self.server_url}/tools/{tool_name}",
                json=args,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def list_tools(self):
        return list(self._tools.keys())

    def disconnect(self):
        for name in self._tools:
            registry.unregister(name)
        self._tools.clear()


def register_tools():
    pass


def unregister_tools():
    pass
