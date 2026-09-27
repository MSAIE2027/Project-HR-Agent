from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_client.client import MCPGateway


async def run() -> None:
    gateway = MCPGateway("stdio")
    async with gateway.session() as session:
        tools = await session.list_tools()
        assert "search_policy_documents" in tools
        assert "lookup_employee_profile" in tools
        policy = await session.call_tool("search_policy_documents", {"query": "international remote work", "limit": 2})
        employee = await session.call_tool("lookup_employee_profile", {"employee_id": "E1001"})
        assert policy["ok"] and policy["data"]["results"]
        assert employee["ok"] and employee["data"]["employee_id"] == "E1001"
        print(json.dumps({"server": "MSAIE HR Tools", "tools": tools, "policy_call": policy, "employee_call": employee}, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
