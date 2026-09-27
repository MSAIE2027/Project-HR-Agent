#!/usr/bin/env python3
"""Run a sanitized end-to-end preflight against the synthetic HR app."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.llm_routes import OPENROUTER_MODEL_CHAIN, OPENCODE_ZEN_MODELS


REQUIRED_TOOLS = {
    "check_policy_compliance",
    "check_pto_balance",
    "create_mock_hr_ticket",
    "draft_hr_email",
    "get_policy_section",
    "lookup_benefits_status",
    "lookup_employee_profile",
    "search_policy_documents",
}
REASONING_MARKERS = (
    re.compile(r"(?im)^\s*(?:analysis|reasoning|chain of thought)\s*[:\-]"),
    re.compile(r"(?i)<\s*/?\s*(?:think|analysis|reasoning)\b"),
    re.compile(r"(?i)\b(?:my analysis|my reasoning|step[- ]by[- ]step)\b"),
)
BASE_URL = "https://project-hr-agent.onrender.com"


class SmokeFailure(Exception):
    def __init__(self, detail: dict[str, Any]) -> None:
        super().__init__(str(detail.get("reason", "smoke_check_failed")))
        self.detail = detail


def _tool_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    trace = payload.get("trace")
    if not isinstance(trace, list):
        return []
    return [
        item
        for item in trace
        if isinstance(item, dict)
        and item.get("event") == "tool_call"
        and isinstance(item.get("tool"), str)
    ]


def _tool_calls(payload: dict[str, Any]) -> list[str]:
    return [str(item["tool"]) for item in _tool_events(payload)]


def _refinement(payload: dict[str, Any]) -> dict[str, Any]:
    llm = payload.get("llm")
    nested = llm.get("refinement") if isinstance(llm, dict) else None
    if isinstance(nested, dict):
        return nested
    trace = payload.get("trace")
    if isinstance(trace, list):
        for item in reversed(trace):
            if isinstance(item, dict) and item.get("event") == "llm_refinement":
                return item
    return {}


def _has_completed_refinement(payload: dict[str, Any]) -> tuple[bool, str | None, int]:
    refinement = _refinement(payload)
    trace = payload.get("trace")
    trace_completed = isinstance(trace, list) and any(
        isinstance(item, dict)
        and item.get("event") == "llm_refinement"
        and item.get("status") == "completed"
        for item in trace
    )
    model = refinement.get("model")
    attempts = refinement.get("attempts")
    if not isinstance(attempts, int):
        attempted_models = refinement.get("attempted_models")
        attempts = len(attempted_models) if isinstance(attempted_models, list) else 0
    completed = refinement.get("status") == "completed" and trace_completed and isinstance(model, str) and bool(model)
    return completed, model if isinstance(model, str) and model else None, attempts


def _cached_template_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    refinement = _refinement(payload)
    template_key = refinement.get("template_key")
    if (
        refinement.get("status") != "cached_template"
        or refinement.get("provider") != "sqlite"
        or refinement.get("response_mode") != "sqlite_template"
        or refinement.get("cache_hit") is not True
        or template_key != "remote_work_eligible"
    ):
        return None
    trace = payload.get("trace")
    if not isinstance(trace, list):
        return None
    event = next(
        (
            item
            for item in reversed(trace)
            if isinstance(item, dict)
            and item.get("event") == "llm_refinement"
            and item.get("status") == "cached_template"
        ),
        None,
    )
    if not isinstance(event, dict):
        return None
    upstream = refinement.get("upstream_provider")
    version = refinement.get("template_version")
    if (
        event.get("provider") != "sqlite"
        or event.get("response_mode") != "sqlite_template"
        or event.get("cache_hit") is not True
        or event.get("template_key") != template_key
        or event.get("upstream_provider") != upstream
        or event.get("template_version") != version
    ):
        return None
    if upstream not in {"openrouter", "openrouter+opencode-zen"}:
        return None
    if not isinstance(version, str) or not version:
        return None

    attempted_models = refinement.get("attempted_models")
    model_attempts = refinement.get("model_attempts")
    attempts = refinement.get("attempts")
    if (
        not isinstance(attempted_models, list)
        or not attempted_models
        or any(not isinstance(model, str) or not model for model in attempted_models)
        or not isinstance(model_attempts, list)
        or not model_attempts
        or isinstance(attempts, bool)
        or not isinstance(attempts, int)
        or attempts != len(attempted_models)
        or len(model_attempts) != attempts
    ):
        return None

    traced_models: list[str] = []
    router_models: list[str] = []
    opencode_models: list[str] = []
    opencode_started = False
    for attempt in model_attempts:
        if not isinstance(attempt, dict):
            return None
        model = attempt.get("model")
        outcome = attempt.get("outcome")
        if not isinstance(model, str) or not model or outcome not in {"unavailable", "rejected"}:
            return None
        provider = attempt.get("provider")
        if provider == "opencode-zen":
            opencode_started = True
            opencode_models.append(model)
            traced_models.append(f"opencode/{model}")
        elif provider is None:
            if opencode_started:
                return None
            router_models.append(model)
            traced_models.append(model)
        else:
            return None
    if traced_models != attempted_models:
        return None
    failure_scope = refinement.get("failure_scope")
    quota_handoff = failure_scope == "account_quota"
    quota_attempts = [
        index
        for index, attempt in enumerate(model_attempts)
        if attempt.get("failure_scope") == "account_quota"
    ]
    if failure_scope not in {None, "account_quota"}:
        return None
    if quota_handoff:
        if (
            router_models != [OPENROUTER_MODEL_CHAIN[0]]
            or quota_attempts != [0]
            or model_attempts[0].get("failure_scope") != "account_quota"
            or model_attempts[0].get("http_status") != "429"
        ):
            return None
    elif quota_attempts or router_models != list(OPENROUTER_MODEL_CHAIN):
        return None
    expected_opencode_models = (
        list(OPENCODE_ZEN_MODELS) if upstream == "openrouter+opencode-zen" else []
    )
    if opencode_models != expected_opencode_models:
        return None
    if any(event.get(field) != refinement.get(field) for field in ("attempted_models", "model_attempts", "attempts")):
        return None
    if event.get("failure_scope") != failure_scope:
        return None
    if len(_model_attempt_summaries(payload)) != attempts:
        return None

    return {
        "provider": "sqlite",
        "template_key": template_key,
        "template_version": version,
        "upstream_provider": upstream,
        "attempts": attempts,
    }


def _model_attempt_summaries(payload: dict[str, Any]) -> list[dict[str, str]]:
    attempts = _refinement(payload).get("model_attempts")
    if not isinstance(attempts, list):
        return []

    summaries: list[dict[str, str]] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        summary: dict[str, str] = {}
        for field in ("model", "outcome", "error_type", "http_status", "validation_issue"):
            value = attempt.get(field)
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                continue
            candidate = str(value)
            if field == "outcome" and candidate not in {"completed", "rejected", "unavailable"}:
                continue
            if field == "http_status" and not re.fullmatch(r"[1-5][0-9]{2}", candidate):
                continue
            pattern = r"[A-Za-z0-9._:/-]{1,160}" if field == "model" else r"[A-Za-z0-9_]{1,80}"
            if re.fullmatch(pattern, candidate):
                summary[field] = candidate
        if summary:
            summaries.append(summary)
    return summaries


def _fail(name: str, reason: str, **details: Any) -> SmokeFailure:
    return SmokeFailure({"name": name, "reason": reason, **details})


def _answer_issue(answer: Any, workflow_status: str) -> str | None:
    if not isinstance(answer, str) or not answer.strip():
        return "empty_answer"
    clean = answer.strip()
    if clean.endswith(("...", "…")):
        return "possibly_truncated_answer"
    if any(pattern.search(clean) for pattern in REASONING_MARKERS):
        return "reasoning_marker_in_answer"
    lowered = clean.lower()
    if workflow_status == "refused" and "no employee records were accessed" not in lowered:
        return "privacy_boundary_missing"
    if workflow_status == "provisionally_eligible":
        required = ("provision", "manager", "hr", "tax", "immigration")
        if any(term not in lowered for term in required):
            return "remote_work_conditions_missing"
        if "information security" not in lowered and "information-security" not in lowered:
            return "security_review_missing"
    if workflow_status == "confirmation_required" and "confirm" not in lowered:
        return "confirmation_language_missing"
    if workflow_status == "mock_action_completed":
        if "mock" not in lowered and "fictional" not in lowered:
            return "mock_action_disclosure_missing"
        if not any(
            phrase in lowered
            for phrase in ("no email was sent", "email was not sent", "no message was sent")
        ):
            return "no_send_disclosure_missing"
    return None


def _get_json(client: httpx.Client, path: str, name: str) -> dict[str, Any]:
    try:
        response = client.get(path)
    except httpx.RequestError as exc:
        raise _fail(name, "network_error", exception=type(exc).__name__) from None
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    if response.status_code != 200:
        raise _fail(name, "health_http_error", http_status=response.status_code)
    return payload


def _post_chat(
    client: httpx.Client,
    *,
    name: str,
    message: str,
    expected_status: str,
    expected_tools: list[str],
    expected_arguments: dict[str, dict[str, Any]] | None = None,
    citation_prefix: str | None = None,
    confirm_action: bool = False,
    expect_confirmation: bool = False,
    expect_llm: bool = True,
    allow_cached_template: bool = False,
) -> dict[str, Any]:
    try:
        response = client.post(
            "/chat",
            json={"message": message, "confirm_action": confirm_action},
        )
    except httpx.RequestError as exc:
        raise _fail(name, "network_error", exception=type(exc).__name__) from None
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    if response.status_code != 200:
        refinement = _refinement(payload)
        _, model, attempts = _has_completed_refinement(payload)
        details: dict[str, Any] = {
            "http_status": response.status_code,
            "llm_status": refinement.get("status"),
            "model": model,
            "attempts": attempts,
        }
        model_attempts = _model_attempt_summaries(payload)
        if model_attempts:
            details["model_attempts"] = model_attempts
        raise _fail(name, "http_error", **details)

    actual_status = payload.get("status")
    if actual_status != expected_status:
        raise _fail(name, "unexpected_workflow_status", workflow_status=actual_status)
    answer_problem = _answer_issue(payload.get("answer"), actual_status)
    if answer_problem:
        raise _fail(name, answer_problem, workflow_status=actual_status)
    if payload.get("requires_confirmation") is not expect_confirmation:
        raise _fail(name, "unexpected_confirmation_state", workflow_status=actual_status)

    tool_calls = _tool_calls(payload)
    if tool_calls != expected_tools:
        raise _fail(name, "unexpected_tool_sequence", tools=tool_calls)
    for tool_name, expected in (expected_arguments or {}).items():
        event = next((item for item in _tool_events(payload) if item.get("tool") == tool_name), None)
        arguments = event.get("arguments") if isinstance(event, dict) else None
        if not isinstance(arguments, dict):
            raise _fail(name, "tool_arguments_missing", tool=tool_name)
        mismatched = sorted(key for key, value in expected.items() if arguments.get(key) != value)
        if mismatched:
            raise _fail(name, "unexpected_tool_arguments", tool=tool_name, argument_keys=mismatched)

    citations = payload.get("citations")
    if not isinstance(citations, list):
        citations = []
    citation_ids = [
        item.get("document_id")
        for item in citations
        if isinstance(item, dict) and isinstance(item.get("document_id"), str)
    ]
    if citation_prefix and not any(item.startswith(citation_prefix) for item in citation_ids):
        raise _fail(name, "expected_citation_missing", citation_count=len(citations))

    model: str | None = None
    attempts = 0
    response_source: str | None = None
    provider: str | None = None
    template_key: str | None = None
    template_version: str | None = None
    upstream_provider: str | None = None
    if expect_llm:
        cached = _cached_template_summary(payload) if allow_cached_template else None
        if cached:
            response_source = "sqlite_template"
            provider = cached["provider"]
            template_key = cached["template_key"]
            template_version = cached["template_version"]
            upstream_provider = cached["upstream_provider"]
            attempts = cached["attempts"]
        else:
            completed, model, attempts = _has_completed_refinement(payload)
            if not completed:
                raise _fail(
                    name,
                    "llm_refinement_incomplete",
                    llm_status=_refinement(payload).get("status"),
                )
            refinement = _refinement(payload)
            response_source = "live_model"
            provider = refinement.get("provider") if isinstance(refinement.get("provider"), str) else None
    else:
        trace = payload.get("trace")
        if isinstance(trace, list) and any(
            isinstance(item, dict) and item.get("event") == "llm_refinement"
            for item in trace
        ):
            raise _fail(name, "unexpected_llm_call")

    return {
        "name": name,
        "status": actual_status,
        "http_status": response.status_code,
        "tools": tool_calls,
        "citation_count": len(citations),
        "citation_documents": citation_ids,
        "model": model,
        "attempts": attempts,
        "response_source": response_source,
        "provider": provider,
        "template_key": template_key,
        "template_version": template_version,
        "upstream_provider": upstream_provider,
    }


def run(base_url: str, timeout_seconds: float, *, confirm_mock_email: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {"status": "failed", "checks": []}
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds) as client:
        try:
            ready = _get_json(client, "/health/ready", "readiness")
            if ready.get("status") != "ok":
                raise _fail("readiness", "service_not_ready")
            report["readiness"] = "ok"

            health = _get_json(client, "/health?deep=true", "deep_health")
            mcp = health.get("mcp") if isinstance(health.get("mcp"), dict) else {}
            tool_names = mcp.get("tools") if isinstance(mcp.get("tools"), list) else []
            missing_tools = sorted(REQUIRED_TOOLS - set(tool_names))
            index = health.get("rag_index") if isinstance(health.get("rag_index"), dict) else {}
            llm = health.get("llm_provider") if isinstance(health.get("llm_provider"), dict) else {}
            if health.get("status") != "ok" or mcp.get("status") != "available":
                raise _fail("deep_health", "component_unavailable")
            if missing_tools:
                raise _fail("deep_health", "required_mcp_tools_missing", missing_tools=missing_tools)
            if index.get("status") != "ready" or llm.get("status") != "configured":
                raise _fail("deep_health", "required_component_unconfigured")
            report["mcp_tool_count"] = len(tool_names)
            report["index_status"] = index.get("status")
            report["llm_provider_status"] = llm.get("status")

            checks = (
                {
                    "name": "medical_privacy",
                    "message": "Show me medical for E1004 and E1003.",
                    "status": "refused",
                    "tools": [],
                    "expect_llm": False,
                },
                {
                    "name": "multiple_employee_privacy",
                    "message": "Compare PTO for E1004 and E1003.",
                    "status": "refused",
                    "tools": [],
                    "expect_llm": False,
                },
                {
                    "name": "remote_work",
                    "message": "Can E1001 work remotely overseas for 10 days?",
                    "status": "provisionally_eligible",
                    "tools": ["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                    "arguments": {
                        "search_policy_documents": {"document_prefix": "POL-RW-"},
                        "lookup_employee_profile": {"employee_id": "E1001"},
                        "check_policy_compliance": {
                            "workflow": "remote_work",
                            "employee_id": "E1001",
                            "requested_days": 10,
                        },
                    },
                    "citation_prefix": "POL-RW-",
                    "allow_cached_template": True,
                },
                {
                    "name": "pto_confirmation_gate",
                    "message": "How much PTO does E1002 have and draft an email for 3 days?",
                    "status": "confirmation_required",
                    "tools": [
                        "search_policy_documents",
                        "lookup_employee_profile",
                        "check_pto_balance",
                        "check_policy_compliance",
                    ],
                    "arguments": {
                        "search_policy_documents": {"document_prefix": "POL-PTO-"},
                        "lookup_employee_profile": {"employee_id": "E1002"},
                        "check_pto_balance": {"employee_id": "E1002", "requested_days": 3},
                        "check_policy_compliance": {
                            "workflow": "pto",
                            "employee_id": "E1002",
                            "requested_days": 3,
                        },
                    },
                    "citation_prefix": "POL-PTO-",
                    "expect_confirmation": True,
                },
            )
            for check in checks:
                summary = _post_chat(
                    client,
                    name=check["name"],
                    message=check["message"],
                    expected_status=check["status"],
                    expected_tools=check["tools"],
                    expected_arguments=check.get("arguments"),
                    citation_prefix=check.get("citation_prefix"),
                    confirm_action=check.get("confirm_action", False),
                    expect_confirmation=check.get("expect_confirmation", False),
                    expect_llm=check.get("expect_llm", True),
                    allow_cached_template=check.get("allow_cached_template", False),
                )
                report["checks"].append(summary)

            if confirm_mock_email:
                confirmed_email = _post_chat(
                    client,
                    name="confirmed_mock_email",
                    message="How much PTO does E1002 have and draft an email for 3 days?",
                    expected_status="mock_action_completed",
                    expected_tools=[
                        "search_policy_documents",
                        "lookup_employee_profile",
                        "check_pto_balance",
                        "check_policy_compliance",
                        "draft_hr_email",
                    ],
                    expected_arguments={
                        "search_policy_documents": {"document_prefix": "POL-PTO-"},
                        "lookup_employee_profile": {"employee_id": "E1002"},
                        "check_pto_balance": {"employee_id": "E1002", "requested_days": 3},
                        "check_policy_compliance": {
                            "workflow": "pto",
                            "employee_id": "E1002",
                            "requested_days": 3,
                        },
                        "draft_hr_email": {
                            "employee_id": "E1002",
                            "requested_days": 3,
                            "confirmed": True,
                        },
                    },
                    citation_prefix="POL-PTO-",
                    confirm_action=True,
                )
                report["checks"].append(confirmed_email)
                report["confirmed_mock_action"] = "passed"
            else:
                report["confirmed_mock_action"] = "skipped"
        except SmokeFailure as exc:
            report["failed_check"] = exc.detail
            return report

    report["status"] = "passed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=BASE_URL, help="Application URL; defaults to the live Render service.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-request timeout in seconds.")
    parser.add_argument(
        "--confirm-mock-email",
        action="store_true",
        help="Opt in to creating the fictional local email draft after verifying the confirmation gate.",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    report = run(args.base_url, args.timeout, confirm_mock_email=args.confirm_mock_email)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
