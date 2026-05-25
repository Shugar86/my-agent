"""MCP (Model Context Protocol) Manager.

Manages the lifecycle of MCP servers using the MCP Python SDK.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.tool_registry import registry

logger = logging.getLogger(__name__)

MCP_CONFIG_PATH = Path("config/mcp_servers.json")


class MCPServerHandle:
    """Handle for a single MCP server connection using proper async context managers."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.session: Optional[ClientSession] = None
        self._streams = None
        self._stdio_cm = None
        self._session_cm = None
        self._tools_registered = 0

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", False)

    async def start(self):
        cmd = self.config["command"]
        args = self.config.get("args", [])
        env = self._resolve_env(self.config.get("env", {}))

        params = StdioServerParameters(
            command=cmd,
            args=args,
            env=env if env else None,
        )

        try:
            self._stdio_cm = stdio_client(params)
            self._streams = await self._stdio_cm.__aenter__()
            read, write = self._streams

            self._session_cm = ClientSession(read, write)
            self.session = await self._session_cm.__aenter__()
            await self.session.initialize()

            logger.info("MCP server '%s' connected", self.name)
            await self._register_tools()
            return True
        except Exception as e:
            logger.warning("MCP server '%s' failed to start: %s", self.name, e)
            await self._cleanup()
            return False

    async def stop(self):
        await self._unregister_tools()
        await self._cleanup()
        logger.info("MCP server '%s' disconnected", self.name)

    async def _cleanup(self):
        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
            self.session = None
        if self._stdio_cm:
            try:
                await self._stdio_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._stdio_cm = None
            self._streams = None

    async def _register_tools(self):
        if not self.session:
            return
        try:
            tools_result = await self.session.list_tools()
            count = 0
            for tool in tools_result.tools:
                mcp_name = f"mcp_{self.name}_{tool.name}"
                schema = getattr(tool, 'inputSchema', None) or getattr(tool, 'input_schema', {"type": "object", "properties": {}})
                desc = tool.description or tool.name

                async def _execute(tool_name=tool.name, s=self.session):
                    try:
                        result = await s.call_tool(tool_name, {})
                        if hasattr(result, 'content'):
                            texts = []
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    texts.append(item.text)
                                elif isinstance(item, dict):
                                    texts.append(str(item.get('text', item)))
                            return "\n".join(texts)
                        return str(result)
                    except Exception as e:
                        return f"MCP error: {e}"

                registry.register(
                    name=mcp_name,
                    description=f"[MCP {self.name}] {desc}",
                    parameters=schema,
                    execute_fn=_execute,
                )
                count += 1
            self._tools_registered = count
            logger.info("MCP '%s': registered %d tools", self.name, count)
        except Exception as e:
            logger.warning("MCP '%s' tool registration failed: %s", self.name, e)
            self._tools_registered = 0

    async def _unregister_tools(self):
        prefix = f"mcp_{self.name}_"
        for t in registry.list_all():
            if t["name"].startswith(prefix):
                registry.unregister(t["name"])
        self._tools_registered = 0

    def _resolve_env(self, env: dict) -> dict:
        resolved = {}
        for key, val in env.items():
            if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
                resolved[key] = os.environ.get(val[2:-1], "")
            else:
                resolved[key] = val
        return resolved


class MCPServerManager:
    """Manages all configured MCP servers."""

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path or MCP_CONFIG_PATH)
        self.servers: dict[str, MCPServerHandle] = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            logger.warning("MCP config not found: %s", self.config_path)
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for name, cfg in data.get("servers", {}).items():
            self.servers[name] = MCPServerHandle(name, cfg)

    def get_server(self, name: str) -> Optional[MCPServerHandle]:
        return self.servers.get(name)

    def list_servers(self) -> list[dict]:
        results = []
        for name, handle in self.servers.items():
            results.append({
                "name": name,
                "enabled": handle.enabled,
                "connected": handle.session is not None,
                "tools_count": handle._tools_registered,
                "command": handle.config.get("command", ""),
            })
        return results

    async def start_server(self, name: str) -> bool:
        handle = self.servers.get(name)
        if not handle:
            logger.error("Unknown MCP server: %s", name)
            return False
        if handle.session:
            logger.info("MCP server '%s' already connected", name)
            return True
        return await handle.start()

    async def stop_server(self, name: str):
        handle = self.servers.get(name)
        if handle:
            await handle.stop()

    async def start_all(self):
        results = {}
        for name in self.servers:
            results[name] = await self.start_server(name)
        return results

    async def stop_all(self):
        for name in list(self.servers.keys()):
            await self.stop_server(name)

    def reload_config(self):
        self.servers.clear()
        self._load_config()
