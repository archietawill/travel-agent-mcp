"""
Multi-MCP Client: Connect to both Tavily and Railway MCP servers
This demonstrates how to manage multiple MCP servers and route tool calls appropriately

Usage: python multi_mcp_test.py
"""
import json
import os
import re
import sys
from urllib import parse, request
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    def __init__(self, url):
        self.url = url.strip().strip("`").strip()
        self._id = 0
        self._sse_resp = None
        self._message_url = None
        self._pending = {}
        self._connect_sse()

    def _connect_sse(self):
        req = request.Request(self.url, headers={"Accept": "text/event-stream"}, method="GET")
        self._sse_resp = request.urlopen(req, timeout=120)
        self._wait_for_endpoint()

    def _wait_for_endpoint(self):
        while not self._message_url:
            event, data = self._read_event()
            if event == "endpoint" and data:
                self._message_url = parse.urljoin(self.url, data)

    def _read_event(self):
        event = "message"
        data_lines = []
        while True:
            raw = self._sse_resp.readline()
            if not raw:
                raise RuntimeError("Remote SSE stream closed")
            line = raw.decode("utf-8", errors="ignore").rstrip("\r\n")
            if line == "":
                if data_lines:
                    return event, "\n".join(data_lines)
                event = "message"
                data_lines = []
                continue
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event = line[6:].strip()
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
                continue

    def send(self, method, params={}):
        if not self._message_url:
            self._wait_for_endpoint()
        self._id += 1
        req_id = self._id
        body = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self._message_url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(f"Unexpected HTTP status: {resp.status}")
        if req_id in self._pending:
            msg = self._pending.pop(req_id)
        else:
            while True:
                event, data = self._read_event()
                if event == "endpoint" and data:
                    self._message_url = parse.urljoin(self.url, data)
                    continue
                if not data:
                    continue
                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == req_id:
                    break
                if "id" in msg:
                    self._pending[msg["id"]] = msg
        if "error" in msg:
            raise RuntimeError(msg["error"]["message"])
        return msg["result"]

    def initialize(self):
        self.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "nanomcp-multi-server-client", "version": "0.1.0"},
        })
        self.notify("notifications/initialized", {})

    def list_tools(self):
        return self.send("tools/list")["tools"]

    def call_tool(self, name, arguments={}):
        return self.send("tools/call", {"name": name, "arguments": arguments})["content"][0]["text"]

    def notify(self, method, params={}):
        if not self._message_url:
            self._wait_for_endpoint()
        body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params}, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self._message_url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(f"Unexpected HTTP status for notification: {resp.status}")


class MultiMCPManager:
    def __init__(self):
        self.clients = {}
        self.tool_mapping = {}
        self.server_prefixes = {}

    def add_server(self, name, url):
        print(f"[MultiMCP] Connecting to {name} MCP server...")
        client = MCPClient(url)
        client.initialize()
        self.clients[name] = client
        self.server_prefixes[name] = name
        
        tools = client.list_tools()
        print(f"[MultiMCP] {name} provides {len(tools)} tools:")
        for tool in tools:
            prefixed_name = f"{name}_{tool['name']}"
            self.tool_mapping[prefixed_name] = (client, tool['name'])
            print(f"  - {prefixed_name}: {tool['description'][:60]}...")
        
        return tools

    def get_all_tools(self):
        all_tools = []
        for server_name, client in self.clients.items():
            tools = client.list_tools()
            for tool in tools:
                tool_copy = tool.copy()
                tool_copy['name'] = f"{server_name}_{tool['name']}"
                all_tools.append(tool_copy)
        return all_tools

    def call_tool(self, prefixed_name, arguments):
        if prefixed_name not in self.tool_mapping:
            raise ValueError(f"Unknown tool: {prefixed_name}")
        
        client, original_name = self.tool_mapping[prefixed_name]
        print(f"[MultiMCP] Routing {prefixed_name} to {original_name}")
        return client.call_tool(original_name, arguments)

    def get_server_for_tool(self, prefixed_name):
        if prefixed_name not in self.tool_mapping:
            return None
        for prefix in self.server_prefixes:
            if prefixed_name.startswith(prefix + "_"):
                return prefix
        return None


def _extract_tool_call_budget(user_message: str):
    patterns = [
        r"(?:search|query|call)\s*(?:for\s*)?(\d{1,2})\s*(?:times|searches|queries|rounds|iterations)\b",
        r"(\d{1,2})\s*(?:times|searches|queries|rounds|iterations)\b",
        r"(\d{1,2})\s*次(?:查询|搜索|工具调用)?",
    ]
    for p in patterns:
        m = re.search(p, user_message, flags=re.IGNORECASE)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= 20:
            return n
    return None


def run_multi_server_agent(user_message, max_iterations=8, default_tool_calls=4):
    tavily_url = os.environ.get("TAVILY_REMOTE_SSE_URL")
    railway_url = os.environ.get("RAILWAY_REMOTE_SSE_URL")
    
    api_key = os.environ.get("OPENAI_API_KEY") 
    base_url = os.environ.get("OPENAI_API_URL") or "https://api.openrouter.ai/v1"
    model = os.environ.get("OPENAI_API_MODEL")
    llm = OpenAI(api_key=api_key, base_url=base_url)
    
    multi_mcp = MultiMCPManager()
    
    tavily_tools = multi_mcp.add_server("tavily", tavily_url)
    railway_tools = multi_mcp.add_server("railway", railway_url)
    
    all_tools = multi_mcp.get_all_tools()
    print(f"\n[MultiMCP] Total tools available: {len(all_tools)}")
    
    openai_tools = [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["inputSchema"]}}
        for t in all_tools
    ]
    
    tool_call_budget = _extract_tool_call_budget(user_message) or default_tool_calls
    messages = [
        {"role": "system", "content": "You are a multi-domain assistant with access to both web search (Tavily) and China railway information (12306) tools.\n\nAvailable tools are prefixed with their server name:\n- tavily_*: Web search tools\n- railway_*: Railway/train information tools\n\nYou can call MCP tools multiple times.\n- If the user requests N results, you must call tools enough times and return complete information.\n- If the user specifies how many searches/tool calls to run, follow that number.\n- Otherwise, default to 4 tool calls.\n- Use appropriate tools based on the user's query (web search for general info, railway tools for train/travel queries)."},
        {"role": "user", "content": user_message},
    ]
    
    tool_calls_made = 0
    budget_notice_added = False
    
    for iteration in range(max_iterations):
        print(f"\n[MultiMCP] Iteration {iteration + 1}/{max_iterations}")
        resp = llm.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools,
        )
        msg = resp.choices[0].message
        messages.append(msg)
        
        if not msg.tool_calls:
            print(f"[MultiMCP] LLM provided final answer (no tool calls)")
            return msg.content or ""
        
        print(f"[MultiMCP] LLM requested {len(msg.tool_calls)} tool call(s)")
        
        for tc in msg.tool_calls:
            if tool_calls_made >= tool_call_budget:
                print(f"[MultiMCP] Tool call budget ({tool_call_budget}) exceeded")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "Tool call budget exceeded. Do not call any more tools; answer using the information already gathered.",
                })
                continue
            
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            server = multi_mcp.get_server_for_tool(tc.function.name)
            print(f"[MCP] {tc.function.name}({args}) [Server: {server}]")
            
            try:
                result = multi_mcp.call_tool(tc.function.name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
                tool_calls_made += 1
                print(f"[MultiMCP] Tool call successful (total: {tool_calls_made}/{tool_call_budget})")
            except Exception as e:
                print(f"[MultiMCP] Tool call failed: {e}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": f"Error calling tool: {str(e)}",
                })
        
        if tool_calls_made >= tool_call_budget and not budget_notice_added:
            messages.append({"role": "system", "content": "Tool call budget reached. Produce the final answer now without calling any tools."})
            budget_notice_added = True
    
    return "Max iterations reached"


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "I want to travel from Beijing to Shanghai tomorrow. Find available trains and search for popular attractions and restaurants to visit in Shanghai"
    print("=" * 80)
    print("Multi-MCP Client: Tavily + Railway")
    print("=" * 80)
    print(run_multi_server_agent(query))
