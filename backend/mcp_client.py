import json
from urllib import parse, request
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self, url: str):
        self.url = url.strip().strip("`").strip()
        self._id = 0
        self._sse_resp = None
        self._message_url = None
        self._pending: Dict[int, dict] = {}
        try:
            self._connect_sse()
        except Exception as e:
            print(f"[MCP ERROR] Failed to connect to SSE at {self.url}: {e}")

    def _connect_sse(self):
        req = request.Request(
            self.url,
            headers={"Accept": "text/event-stream"},
            method="GET"
        )
        print(f"[MCP DEBUG] Connecting to SSE at {self.url}")
        self._sse_resp = request.urlopen(req, timeout=120)
        self._wait_for_endpoint()

    def _wait_for_endpoint(self):
        while not self._message_url:
            event, data = self._read_event()
            if event == "endpoint" and data:
                # Handle both relative and absolute paths correctly
                if data.startswith("http"):
                    self._message_url = data
                elif data.startswith("/"):
                    # Relative to host root
                    base_parts = parse.urlparse(self.url)
                    self._message_url = f"{base_parts.scheme}://{base_parts.netloc}{data}"
                else:
                    # Relative to the SSE path (ensuring it doesn't replace the last segment)
                    if not self.url.endswith("/"):
                        base_url = self.url.rsplit("/", 1)[0] + "/"
                    else:
                        base_url = self.url
                    self._message_url = parse.urljoin(base_url, data)
                
                print(f"[MCP DEBUG] Assigned message endpoint: {self._message_url}")

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

    def send(self, method: str, params: dict = None) -> Any:
        if params is None:
            params = {}
        if not self._message_url:
            self._wait_for_endpoint()
        self._id += 1
        req_id = self._id
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self._message_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
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
            "clientInfo": {"name": "travel-mcp-client", "version": "1.0.0"},
        })
        self.notify("notifications/initialized", {})

    def list_tools(self) -> list:
        return self.send("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict = None) -> str:
        if arguments is None:
            arguments = {}
        return self.send("tools/call", {"name": name, "arguments": arguments})["content"][0]["text"]

    def notify(self, method: str, params: dict = None):
        if params is None:
            params = {}
        if not self._message_url:
            self._wait_for_endpoint()
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self._message_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(f"Unexpected HTTP status for notification: {resp.status}")
