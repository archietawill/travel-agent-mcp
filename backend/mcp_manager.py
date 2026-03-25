from typing import Dict, List, Optional, Tuple
from mcp_client import MCPClient
from config import settings

class MultiMCPManager:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.tool_mapping: Dict[str, Tuple[MCPClient, str]] = {}
        self.server_prefixes: Dict[str, str] = {}

    def add_server(self, name: str, url: str) -> List[dict]:
        print(f"[MCP] Connecting to {name} MCP server...")
        client = MCPClient(url)
        client.initialize()
        self.clients[name] = client
        self.server_prefixes[name] = name
        
        tools = client.list_tools()
        print(f"[MCP] {name} provides {len(tools)} tools:")
        for tool in tools:
            prefixed_name = f"{name}_{tool['name']}"
            self.tool_mapping[prefixed_name] = (client, tool['name'])
            print(f"  - {prefixed_name}")
        
        return tools

    def get_all_tools(self) -> List[dict]:
        all_tools = []
        for server_name, client in self.clients.items():
            try:
                tools = client.list_tools()
                for tool in tools:
                    tool_copy = tool.copy()
                    tool_copy['name'] = f"{server_name}_{tool['name']}"
                    all_tools.append(tool_copy)
            except Exception as e:
                print(f"[MCP ERROR] Failed to list tools for {server_name}: {e}")
        return all_tools

    def call_tool(self, prefixed_name: str, arguments: dict = None) -> str:
        if arguments is None:
            arguments = {}
        if prefixed_name not in self.tool_mapping:
            raise ValueError(f"Unknown tool: {prefixed_name}")
        
        client, original_name = self.tool_mapping[prefixed_name]
        print(f"[MCP] Calling {prefixed_name} -> {original_name}")
        return client.call_tool(original_name, arguments)

    def get_server_for_tool(self, prefixed_name: str) -> Optional[str]:
        if prefixed_name not in self.tool_mapping:
            return None
        for prefix in self.server_prefixes:
            if prefixed_name.startswith(prefix + "_"):
                return prefix
        return None

_mcp_manager: Optional[MultiMCPManager] = None

def get_mcp_manager() -> MultiMCPManager:
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MultiMCPManager()
        _mcp_manager.add_server("tavily", settings.TAVILY_REMOTE_SSE_URL)
        _mcp_manager.add_server("amap", settings.AMAP_REMOTE_SSE_URL)
        _mcp_manager.add_server("railway", settings.RAILWAY_REMOTE_SSE_URL)
    return _mcp_manager
