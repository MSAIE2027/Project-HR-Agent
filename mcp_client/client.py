from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from mcp_server.tools import TOOL_REGISTRY

ROOT = Path(__file__).resolve().parents[1]


class MCPGatewayError(RuntimeError):
    pass


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]

    def trace_entry(self, step: int) -> dict[str, Any]:
        return {
            "step": step,
            "event": "tool_call",
            "tool": self.name,
            "arguments": self.arguments,
            "result": _summarise(self.result),
            "status": "ok" if self.result.get("ok") else "error",
        }


def _summarise(value: Any, limit: int = 1200) -> Any:
    serialised = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(serialised) <= limit:
        return value
    return {"truncated": True, "preview": serialised[:limit] + "…"}


class _InProcessSession:
    async def list_tools(self) -> list[str]:
        return sorted(TOOL_REGISTRY)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        function = TOOL_REGISTRY.get(name)
        if function is None:
            raise MCPGatewayError(f"Unknown MCP tool: {name}")
        try:
            return function(**arguments)
        except TypeError as exc:
            raise MCPGatewayError(f"Invalid arguments for {name}: {exc}") from exc


class _StdioSession:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def list_tools(self) -> list[str]:
        response = await self.session.list_tools()
        return sorted(tool.name for tool in response.tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self.session.call_tool(name, arguments)
        if getattr(result, "isError", False):
            message = " ".join(getattr(item, "text", "") for item in result.content)
            raise MCPGatewayError(message or f"MCP tool {name} returned an error")
        structured = getattr(result, "structuredContent", None)
        if structured is None:
            structured = getattr(result, "structured_content", None)
        if structured is not None:
            if isinstance(structured, dict) and set(structured) == {"result"}:
                return structured["result"]
            return structured
        text = "\n".join(getattr(item, "text", "") for item in result.content if getattr(item, "text", ""))
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"ok": True, "data": {"text": text}, "error": None}
        return parsed


class MCPGateway:
    def __init__(self, transport: str | None = None) -> None:
        self.transport = (transport or os.getenv("MSAIE_MCP_TRANSPORT", "stdio")).lower()
        if self.transport not in {"stdio", "inprocess"}:
            raise ValueError("MSAIE_MCP_TRANSPORT must be 'stdio' or 'inprocess'")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Any]:
        if self.transport == "inprocess":
            yield _InProcessSession()
            return
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise MCPGatewayError("The official MCP Python SDK is not installed") from exc
        environment = dict(os.environ)
        existing = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = str(ROOT) + (os.pathsep + existing if existing else "")
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            env=environment,
        )
        try:
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield _StdioSession(session)
        except MCPGatewayError:
            raise
        except Exception as exc:
            raise MCPGatewayError(f"MCP stdio connection failed: {type(exc).__name__}: {exc}") from exc

    async def discover(self) -> dict[str, Any]:
        async with self.session() as session:
            tools = await session.list_tools()
        return {"status": "available", "transport": self.transport, "server": "MSAIE HR Tools", "tools": tools}
