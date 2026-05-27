"""MCP Client Manager — connects to external MCP servers via stdio or HTTP/SSE.

Allows the agent to discover and use tools from external MCP servers
(e.g., Filesystem MCP, GitHub MCP, Slack MCP, etc.)
"""
import os
import json
import uuid
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path


def _resolve_env(env: dict) -> dict:
    """Substitute ${VAR} placeholders from os.environ."""
    resolved = {}
    for key, val in env.items():
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            resolved[key] = os.environ.get(val[2:-1], "")
        else:
            resolved[key] = val
    return resolved


class MCPClientConnection:
    """A single connection to an external MCP server."""

    def __init__(self, name: str, transport: str, config: Dict):
        self.name = name
        self.transport = transport  # "stdio" or "http"
        self.config = config
        self._tools: List[Dict] = []
        self._resources: List[Dict] = []
        self._prompts: List[Dict] = []
        self._process: Optional[subprocess.Popen] = None
        self._http_session = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the connection and discover capabilities."""
        if self.transport == "stdio":
            return await self._init_stdio()
        elif self.transport == "http":
            return await self._init_http()
        return False

    async def _init_stdio(self) -> bool:
        """Start stdio subprocess and perform MCP handshake."""
        command = self.config.get("command")
        args = self.config.get("args", [])
        env = {**os.environ, **_resolve_env(self.config.get("env", {}))}
        try:
            self._process = subprocess.Popen(
                [command, *args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                encoding="utf-8",
            )
            # Send initialize request
            init_req = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "my-agent", "version": "2.0.0"},
                },
            }
            await self._send_stdio_async(json.dumps(init_req))
            response = await self._recv_stdio_async(timeout=10)
            if not response:
                return False
            # Send initialized notification
            await self._send_stdio_async(
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            )
            # Discover tools
            await self._discover_stdio()
            self._initialized = True
            return True
        except Exception as e:
            print(f"[MCP Client] Failed to start {self.name}: {e}")
            return False

    def _send_stdio(self, data: str):
        """Send JSON-RPC line to stdio subprocess."""
        if self._process and self._process.stdin:
            self._process.stdin.write(data + "\n")
            self._process.stdin.flush()

    def _recv_stdio(self, timeout: int = 10) -> Optional[Dict]:
        """Receive single JSON-RPC response from stdio subprocess (blocking)."""
        if not self._process or not self._process.stdout:
            return None
        try:
            line = self._process.stdout.readline()
            if not line:
                return None
            return json.loads(line)
        except json.JSONDecodeError:
            return None
        except OSError as e:
            print(f"[MCP Client] stdio recv error: {e}")
            return None

    async def _send_stdio_async(self, data: str) -> None:
        """Send JSON-RPC without blocking the event loop."""
        await asyncio.to_thread(self._send_stdio, data)

    async def _recv_stdio_async(self, timeout: int = 10) -> Optional[Dict]:
        """Receive JSON-RPC without blocking the event loop."""
        return await asyncio.to_thread(self._recv_stdio, timeout)

    async def _discover_stdio(self):
        """Discover tools, resources, prompts via stdio."""
        req = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/list"}
        await self._send_stdio_async(json.dumps(req))
        resp = await self._recv_stdio_async(timeout=5)
        if resp and "result" in resp:
            self._tools = resp["result"].get("tools", [])
        # Resources
        req = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "resources/list"}
        await self._send_stdio_async(json.dumps(req))
        resp = await self._recv_stdio_async(timeout=5)
        if resp and "result" in resp:
            self._resources = resp["result"].get("resources", [])
        # Prompts
        req = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "prompts/list"}
        await self._send_stdio_async(json.dumps(req))
        resp = await self._recv_stdio_async(timeout=5)
        if resp and "result" in resp:
            self._prompts = resp["result"].get("prompts", [])

    async def _init_http(self) -> bool:
        """Connect to HTTP/SSE MCP server."""
        try:
            import httpx
        except ImportError:
            print("[MCP Client] httpx not installed, cannot use HTTP transport")
            return False
        base_url = self.config.get("url", "")
        try:
            async with httpx.AsyncClient() as client:
                # SSE endpoint discovery
                resp = await client.get(f"{base_url}/sse", timeout=10)
                if resp.status_code == 200:
                    pass  # SSE connected
                # Try JSON-RPC endpoint directly
                init_req = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "my-agent", "version": "2.0.0"},
                    },
                }
                resp = await client.post(
                    f"{base_url}/mcp",
                    json=init_req,
                    timeout=10,
                )
                if resp.status_code == 200:
                    await self._discover_http(client, base_url)
                    self._initialized = True
                    return True
            return False
        except Exception as e:
            print(f"[MCP Client] HTTP init failed for {self.name}: {e}")
            return False

    async def _discover_http(self, client, base_url: str):
        """Discover tools via HTTP."""
        req = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/list"}
        resp = await client.post(f"{base_url}/mcp", json=req, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data:
                self._tools = data["result"].get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool on this MCP server."""
        if not self._initialized:
            return {"error": "MCP client not initialized"}
        req = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        if self.transport == "stdio":
            await self._send_stdio_async(json.dumps(req))
            resp = await self._recv_stdio_async(timeout=30)
            return resp.get("result", {}) if resp else {"error": "No response from MCP server"}
        elif self.transport == "http":
            try:
                import httpx
                base_url = self.config.get("url", "")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(f"{base_url}/mcp", json=req, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("result", {})
                    return {"error": f"HTTP {resp.status_code}"}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Unknown transport"}

    @property
    def tools(self) -> List[Dict]:
        return self._tools

    @property
    def resources(self) -> List[Dict]:
        return self._resources

    @property
    def prompts(self) -> List[Dict]:
        return self._prompts

    def disconnect(self):
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                pass
            self._process = None
        self._initialized = False


class MCPClientManager:
    """Manages multiple MCP client connections."""

    def __init__(self):
        self._connections: Dict[str, MCPClientConnection] = {}
        self._config_path = Path("config/mcp_clients.json")

    def load_config(self) -> List[Dict]:
        """Load MCP client configurations."""
        if not self._config_path.exists():
            return []
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("clients", [])
        except Exception as e:
            print(f"[MCP Client Manager] Failed to load config: {e}")
            return []

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        clients = self.load_config()
        for client_cfg in clients:
            name = client_cfg.get("name", f"mcp-{len(self._connections)}")
            conn = MCPClientConnection(
                name=name,
                transport=client_cfg.get("transport", "stdio"),
                config=client_cfg.get("config", {}),
            )
            success = await conn.initialize()
            if success:
                self._connections[name] = conn
                print(f"[MCP Client Manager] Connected to {name} with {len(conn.tools)} tools")
            else:
                print(f"[MCP Client Manager] Failed to connect to {name}")

    async def disconnect_all(self):
        """Disconnect all MCP servers."""
        for conn in self._connections.values():
            conn.disconnect()
        self._connections.clear()

    def list_connections(self) -> List[Dict]:
        """List all active connections."""
        return [
            {
                "name": name,
                "transport": conn.transport,
                "tools_count": len(conn.tools),
                "resources_count": len(conn.resources),
                "prompts_count": len(conn.prompts),
            }
            for name, conn in self._connections.items()
        ]

    def get_all_tools(self) -> List[Dict]:
        """Aggregate tools from all connected MCP servers."""
        tools = []
        for name, conn in self._connections.items():
            for tool in conn.tools:
                tool_copy = dict(tool)
                tool_copy["_mcp_server"] = name
                tools.append(tool_copy)
        return tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool on a specific MCP server."""
        conn = self._connections.get(server_name)
        if not conn:
            return {"error": f"MCP server '{server_name}' not connected"}
        return await conn.call_tool(tool_name, arguments)

    def get_connection(self, name: str) -> Optional[MCPClientConnection]:
        return self._connections.get(name)


# Global instance
mcp_client_manager = MCPClientManager()


def register_mcp_tools_with_agent(registry):
    """Register all MCP tools as local tools in the agent's tool registry."""
    tools = mcp_client_manager.get_all_tools()
    for tool in tools:
        tool_name = tool.get("name", "")
        server = tool.get("_mcp_server", "")
        if not tool_name:
            continue
        # Create a proxy execute function
        def make_proxy(srv, tname):
            def proxy(**kwargs):
                from core.async_utils import run_coro_sync
                return run_coro_sync(mcp_client_manager.call_tool(srv, tname, kwargs))
            return proxy
        registry.register(
            name=f"mcp_{server}_{tool_name}",
            description=tool.get("description", f"MCP tool {tool_name} from {server}"),
            parameters=tool.get("inputSchema", {"type": "object", "properties": {}}),
            execute_fn=make_proxy(server, tool_name),
        )
