from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.tools import (
    check_policy_compliance,
    check_pto_balance,
    create_mock_hr_ticket,
    draft_hr_email,
    get_policy_section,
    lookup_benefits_status,
    lookup_employee_profile,
    search_policy_documents,
)

mcp = FastMCP(
    "MSAIE HR Tools",
    instructions=(
        "Fictional HR policy and structured-data tools. All records and actions are synthetic. "
        "Write-like tools require explicit confirmation and never contact a production service."
    ),
    json_response=True,
)

mcp.tool()(search_policy_documents)
mcp.tool()(get_policy_section)
mcp.tool()(lookup_employee_profile)
mcp.tool()(check_pto_balance)
mcp.tool()(lookup_benefits_status)
mcp.tool()(check_policy_compliance)
mcp.tool()(draft_hr_email)
mcp.tool()(create_mock_hr_ticket)


if __name__ == "__main__":
    mcp.run(transport="stdio")
