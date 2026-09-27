"""Build-seeded, fact-bound response templates used when live generation fails."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


RESPONSE_TEMPLATE_VERSION = "1"
RESPONSE_TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "template_key": "pto_balance",
        "description": "Current synthetic PTO balance and request guardrails",
        "document_prefix": "POL-PTO-",
        "required_facts": "employee_id,employee_name,available_days,notice_days,requested_days",
        "answer_template": (
            "{employee_name} ({employee_id}) has {available_days} synthetic PTO days available. "
            "The policy notice expectation is {notice_days} calendar days, and manager approval "
            "remains required for a request."
        ),
    },
    {
        "template_key": "pto_request",
        "description": "Eligible synthetic PTO request with balance-after-approval context",
        "document_prefix": "POL-PTO-",
        "required_facts": "employee_id,employee_name,available_days,notice_days,requested_days,remaining_if_approved",
        "answer_template": (
            "{employee_name} ({employee_id}) has {available_days} synthetic PTO days available. "
            "A request for {requested_days} day(s) would leave {remaining_if_approved} days if approved. "
            "The policy notice expectation is {notice_days} calendar days, and manager approval "
            "remains required."
        ),
    },
    {
        "template_key": "remote_work_eligible",
        "description": "Provisional international remote-work eligibility and outstanding reviews",
        "document_prefix": "POL-RW-",
        "required_facts": "employee_id,employee_name,requested_days,days_after_request,limit_days,required_approvals,destination_review_required",
        "answer_template": (
            "{employee_name} ({employee_id}) is provisionally eligible for {requested_days} calendar "
            "days of international remote work. The request would bring the rolling 12-month total "
            "to {days_after_request}/{limit_days} days. Final approval still requires {required_approvals}. "
            "Destination and data-access review remain required; this eligibility check is not approval."
        ),
    },
)
RESPONSE_TEMPLATE_SIGNATURE = hashlib.sha256(
    json.dumps(RESPONSE_TEMPLATES, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()


def cached_response(index: Any, result: Any) -> tuple[str, dict[str, Any]] | None:
    """Render a seeded template only when live workflow facts and citations match it."""
    facts = result.structured_facts
    if not result.citations or result.requires_confirmation:
        return None
    if result.status not in {"completed", "provisionally_eligible"}:
        return None

    template_key: str
    if facts.get("workflow") == "pto":
        requested_days = _bounded_integer(facts.get("requested_days"))
        if facts.get("eligible") is not True or requested_days is None:
            return None
        template_key = "pto_request" if requested_days > 0 else "pto_balance"
    elif facts.get("workflow") == "remote_work" and facts.get("eligible") is True:
        template_key = "remote_work_eligible"
    else:
        return None

    template = index.get_response_template(template_key)
    if not template:
        return None
    canonical = next(item for item in RESPONSE_TEMPLATES if item["template_key"] == template_key)
    if template.get("version") != RESPONSE_TEMPLATE_VERSION or any(
        template.get(field) != canonical[field]
        for field in ("description", "document_prefix", "required_facts", "answer_template")
    ):
        return None
    prefix = str(template.get("document_prefix", ""))
    if not any(
        isinstance(citation, dict)
        and str(citation.get("document_id", "")).startswith(prefix)
        and bool(str(citation.get("snippet", "")).strip())
        for citation in result.citations
    ):
        return None

    values: dict[str, str | int] = {}
    for field in str(template.get("required_facts", "")).split(","):
        value = facts.get(field)
        if field == "employee_id":
            if not isinstance(value, str) or not re.fullmatch(r"E\d{4}", value):
                return None
            values[field] = value
        elif field == "employee_name":
            clean_name = _clean_name(value)
            if clean_name is None:
                return None
            values[field] = clean_name
        elif field == "required_approvals":
            approvals = value
            allowed = {"manager", "HR", "tax", "information security", "immigration"}
            if (
                not isinstance(approvals, list)
                or not approvals
                or any(not isinstance(item, str) or item not in allowed for item in approvals)
            ):
                return None
            values[field] = ", ".join(approvals)
        elif field == "destination_review_required":
            if value is not True:
                return None
        else:
            number = _bounded_integer(value)
            if number is None:
                return None
            values[field] = number

    try:
        answer = str(template["answer_template"]).format_map(values)
    except (KeyError, ValueError):
        return None
    return answer, {
        "response_mode": "sqlite_template",
        "cache_hit": True,
        "template_key": template_key,
        "template_version": str(template.get("version", RESPONSE_TEMPLATE_VERSION)),
    }


def _bounded_integer(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 365:
        return None
    return value


def _clean_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    clean = re.sub(r"\s+", " ", value).strip()
    if not clean or len(clean) > 80 or any(ord(char) < 32 for char in clean):
        return None
    return clean
