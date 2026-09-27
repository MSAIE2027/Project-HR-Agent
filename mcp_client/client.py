from __future__ import annotations

import json
import os
import sys
from asyncio import Lock
from contextlib import AsyncExitStack, asynccontextmanager
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
        try:
            response = await self.session.list_tools()
        except Exception as exc:
            raise MCPGatewayError(
                f"MCP tool discovery failed: {type(exc).__name__}: {exc}"
            ) from exc
        return sorted(tool.name for tool in response.tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = await self.session.call_tool(name, arguments)
        except MCPGatewayError:
            raise
        except Exception as exc:
            raise MCPGatewayError(
                f"MCP tool call {name} failed: {type(exc).__name__}: {exc}"
            ) from exc
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
        self._session_lock = Lock()
        self._persistent_stack: AsyncExitStack | None = None
        self._persistent_session: _StdioSession | None = None
        self._persistent_mode = False

    def _stdio_parameters(self) -> Any:
        from mcp import StdioServerParameters

        environment = dict(os.environ)
        existing = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = str(ROOT) + (os.pathsep + existing if existing else "")
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            env=environment,
        )

    async def start(self) -> None:
        """Start one stdio server for this gateway's managed application lifetime."""
        if self.transport == "inprocess":
            self._persistent_mode = True
            return
        self._persistent_mode = True
        try:
            from mcp import ClientSession
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise MCPGatewayError("The official MCP Python SDK is not installed") from exc

        async with self._session_lock:
            if self._persistent_session is not None:
                return
            stack = AsyncExitStack()
            try:
                read_stream, write_stream = await stack.enter_async_context(
                    stdio_client(self._stdio_parameters())
                )
                session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
                await session.initialize()
            except Exception as exc:
                await stack.aclose()
                if isinstance(exc, MCPGatewayError):
                    raise
                raise MCPGatewayError(
                    f"MCP stdio connection failed: {type(exc).__name__}: {exc}"
                ) from exc
            self._persistent_stack = stack
            self._persistent_session = _StdioSession(session)

    async def close(self) -> None:
        """Stop the managed stdio process when its owning application shuts down."""
        if not self._persistent_mode or self.transport == "inprocess":
            self._persistent_mode = False
            return
        async with self._session_lock:
            stack = self._persistent_stack
            self._persistent_stack = None
            self._persistent_session = None
            self._persistent_mode = False
            if stack is not None:
                await stack.aclose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Any]:
        if self.transport == "inprocess":
            yield _InProcessSession()
            return
        if self._persistent_mode:
            await self.start()
            async with self._session_lock:
                if self._persistent_session is None:
                    raise MCPGatewayError("The managed MCP stdio session is unavailable")
                yield self._persistent_session
            return
        try:
            from mcp import ClientSession
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise MCPGatewayError("The official MCP Python SDK is not installed") from exc
        try:
            async with stdio_client(self._stdio_parameters()) as (read_stream, write_stream):
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
