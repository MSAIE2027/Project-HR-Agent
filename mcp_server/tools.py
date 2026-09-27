from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

from rag.index import get_index

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "mock_data"
ACTION_LOG = Path(os.getenv("MSAIE_ACTION_LOG", str(Path(tempfile.gettempdir()) / "msaie-mock-actions.jsonl")))


def _load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def _ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data, "error": None}


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}


def _employee(employee_id: str) -> dict[str, Any] | None:
    employee_id = employee_id.upper().strip()
    return next((item for item in _load_json("employees.json") if item["employee_id"] == employee_id), None)


def search_policy_documents(query: str, limit: int = 4, document_prefix: str | None = None) -> dict[str, Any]:
    """Search the persistent policy index and return citation-ready chunks."""
    if not query.strip():
        return _error("invalid_query", "query must not be empty")
    index = get_index()
    results = index.search(query, limit=limit, document_prefix=document_prefix)
    retrieval_method = results[0].get("retrieval_method", "unknown") if results else "no_results"
    return _ok(
        {
            "query": query,
            "retrieval_method": retrieval_method,
            "results": results,
            "index": index.stats(),
        }
    )


def get_policy_section(document_id: str, section: str | None = None) -> dict[str, Any]:
    """Return one policy document section by document ID and optional section label."""
    results = get_index().get_section(document_id, section)
    if not results:
        return _error("not_found", f"No policy section was found for {document_id}")
    return _ok({"document_id": document_id.upper(), "section": section, "results": results})


def lookup_employee_profile(employee_id: str) -> dict[str, Any]:
    """Look up a fictional employee profile by synthetic employee ID."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    return _ok(employee)


def check_pto_balance(employee_id: str, requested_days: int = 0) -> dict[str, Any]:
    """Check a fictional PTO balance and whether a requested duration is available."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    record = next(
        (item for item in _load_json("pto_balances.json") if item["employee_id"] == employee["employee_id"]),
        None,
    )
    if record is None:
        return _error("pto_record_not_found", f"No PTO record exists for {employee_id.upper()}")
    requested_days = max(int(requested_days), 0)
    return _ok(
        {
            **record,
            "requested_days": requested_days,
            "sufficient_balance": requested_days <= record["available_days"],
            "remaining_if_approved": record["available_days"] - requested_days,
        }
    )


def lookup_benefits_status(employee_id: str) -> dict[str, Any]:
    """Look up fictional benefits eligibility and enrolment status."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    record = next(
        (item for item in _load_json("benefits.json") if item["employee_id"] == employee["employee_id"]),
        None,
    )
    if record is None:
        return _error("benefits_record_not_found", f"No benefits record exists for {employee_id.upper()}")
    return _ok(record)


def check_policy_compliance(
    workflow: str,
    employee_id: str,
    requested_days: int = 0,
    destination: str | None = None,
) -> dict[str, Any]:
    """Apply deterministic policy controls to a remote-work or PTO request."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    workflow = workflow.lower().strip()
    requested_days = max(int(requested_days), 0)
    if workflow == "remote_work":
        total = employee["remote_days_used_rolling_12m"] + requested_days
        reasons: list[str] = []
        if employee["employment_type"] not in {"full-time", "part-time"}:
            reasons.append("employment classification is not eligible for international remote work")
        if employee["months_service"] < 6:
            reasons.append("six months of service has not been completed")
        if total > 20:
            reasons.append(f"the request would reach {total} days, above the 20-day rolling limit")
        restricted = {"restricted-demo-state", "sanctioned-demo-state"}
        if destination and destination.lower().strip() in restricted:
            reasons.append("the synthetic destination is on the prohibited-location list")
        return _ok(
            {
                "workflow": workflow,
                "employee_id": employee["employee_id"],
                "eligible": not reasons,
                "reasons": reasons,
                "days_after_request": total,
                "limit_days": 20,
                "required_approvals": ["manager", "HR", "tax", "information security", "immigration"],
                "destination_review_required": not bool(destination),
                "policy_prefixes": ["POL-RW-", "POL-SEC-", "POL-APR-"],
            }
        )
    if workflow == "pto":
        pto = check_pto_balance(employee_id, requested_days)
        if not pto["ok"]:
            return pto
        data = pto["data"]
        reasons = []
        if employee["employment_type"] != "full-time":
            reasons.append("the standard full-time PTO policy does not apply to this classification")
        if not data["sufficient_balance"]:
            reasons.append("the requested duration exceeds the available PTO balance")
        return _ok(
            {
                "workflow": workflow,
                "employee_id": employee["employee_id"],
                "eligible": not reasons,
                "reasons": reasons,
                "available_days": data["available_days"],
                "requested_days": requested_days,
                "notice_days": 30 if requested_days >= 5 else 7,
                "manager_approval_required": True,
                "policy_prefixes": ["POL-PTO-", "POL-APR-"],
            }
        )
    return _error("unsupported_workflow", "workflow must be 'remote_work' or 'pto'")


def draft_hr_email(
    employee_id: str,
    purpose: str,
    requested_days: int = 0,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Create a fictional email draft only after explicit confirmation; no email is sent."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    if not confirmed:
        return _error("confirmation_required", "Explicit confirmation is required before creating a mock email draft")
    action_id = f"EMAIL-{uuid.uuid4().hex[:10].upper()}"
    requested_text = f" for {requested_days} day(s)" if requested_days else ""
    purpose_text = purpose.strip()
    request_label = purpose_text if purpose_text.lower().endswith(" request") else f"{purpose_text} request"
    draft = {
        "action_id": action_id,
        "action_type": "mock_email_draft",
        "sent": False,
        "to": employee["manager_email"],
        "subject": f"{purpose_text[:1].upper()}{purpose_text[1:]}{requested_text} — {employee['name']}",
        "body": (
            f"Please review {employee['name']}'s synthetic {request_label}{requested_text}. "
            "Confirm policy eligibility, operational coverage, and any required approvals. "
            "This is a demonstration draft; no email was sent."
        ),
    }
    _record_action(draft)
    return _ok(draft)


def create_mock_hr_ticket(
    employee_id: str,
    category: str,
    summary: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Create a fictional local ticket record only after explicit confirmation."""
    employee = _employee(employee_id)
    if employee is None:
        return _error("employee_not_found", f"No synthetic employee record was found for {employee_id.upper()}")
    if not confirmed:
        return _error("confirmation_required", "Explicit confirmation is required before creating a mock HR ticket")
    ticket = {
        "action_id": f"TKT-{uuid.uuid4().hex[:10].upper()}",
        "action_type": "mock_hr_ticket",
        "created": True,
        "employee_id": employee["employee_id"],
        "category": category,
        "summary": re.sub(r"\s+", " ", summary).strip()[:500],
        "production_system": False,
    }
    _record_action(ticket)
    return _ok(ticket)


def _record_action(record: dict[str, Any]) -> None:
    ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ACTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "search_policy_documents": search_policy_documents,
    "get_policy_section": get_policy_section,
    "lookup_employee_profile": lookup_employee_profile,
    "check_pto_balance": check_pto_balance,
    "lookup_benefits_status": lookup_benefits_status,
    "check_policy_compliance": check_policy_compliance,
    "draft_hr_email": draft_hr_email,
    "create_mock_hr_ticket": create_mock_hr_ticket,
}
