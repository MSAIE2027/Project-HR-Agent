# ADR 0003: Use In-Process Locally and Stdio for Protocol Verification

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

The application must expose real MCP tools, but local development should remain quick to start. A direct in-process adapter is operationally convenient yet cannot establish MCP wire/protocol behavior.

## Decision

Keep `inprocess` as the local default and support `stdio` through the official MCP client and FastMCP subprocess. Use stdio for protocol smoke checks and the configured hosting transport.

## Consequences

- Local chat avoids subprocess overhead by default.
- Protocol discovery, serialization, and tool calls are independently checked over stdio.
- Deployment has a subprocess boundary and needs health/latency monitoring.
- The deployment transport is configured but still requires hosted verification.

## Evidence

`mcp_client/client.py`, `mcp_server/server.py`, `scripts/smoke_mcp.py`, `tests/test_mcp.py`, `render.yaml`.
