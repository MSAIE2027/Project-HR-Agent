from __future__ import annotations

import asyncio

from mcp_client.client import MCPGateway


def test_genuine_mcp_discovery_and_calls() -> None:
    async def run() -> None:
        gateway = MCPGateway("stdio")
        async with gateway.session() as session:
            tools = await session.list_tools()
            assert len(tools) >= 8
            assert "search_policy_documents" in tools
            assert "lookup_employee_profile" in tools
            policy = await session.call_tool("search_policy_documents", {"query": "remote work", "limit": 2})
            employee = await session.call_tool("lookup_employee_profile", {"employee_id": "E1001"})
            assert policy["ok"] and policy["data"]["results"]
            assert employee["ok"] and employee["data"]["employee_id"] == "E1001"
    asyncio.run(run())
