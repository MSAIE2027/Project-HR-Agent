from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any, Callable
from urllib.parse import urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_hosted_demo.py"
TOOL_NAMES = [
    "check_policy_compliance",
    "check_pto_balance",
    "create_mock_hr_ticket",
    "draft_hr_email",
    "get_policy_section",
    "lookup_benefits_status",
    "lookup_employee_profile",
    "search_policy_documents",
]
REMOTE_TOOL_ARGUMENTS = {
    "search_policy_documents": {"document_prefix": "POL-RW-"},
    "lookup_employee_profile": {"employee_id": "E1001"},
    "check_policy_compliance": {
        "workflow": "remote_work",
        "employee_id": "E1001",
        "requested_days": 10,
        "destination": None,
    },
}
PTO_TOOL_ARGUMENTS = {
    "search_policy_documents": {"document_prefix": "POL-PTO-"},
    "lookup_employee_profile": {"employee_id": "E1002"},
    "check_pto_balance": {"employee_id": "E1002", "requested_days": 3},
    "check_policy_compliance": {
        "workflow": "pto",
        "employee_id": "E1002",
        "requested_days": 3,
        "destination": None,
    },
}
PRIVATE_ANSWER_SENTINEL = "PRIVATE_SYNTHETIC_ANSWER_MUST_NOT_BE_PRINTED"
PROVIDER_BODY_SENTINEL = "RAW_PROVIDER_BODY_MUST_NOT_BE_PRINTED"


def _chat_response(
    *,
    status: str,
    answer: str = PRIVATE_ANSWER_SENTINEL,
    tools: list[str] | None = None,
    citations: list[str] | None = None,
    tool_arguments: dict[str, dict[str, Any]] | None = None,
    refinement_status: str | None = None,
    refinement_provider: str = "openrouter",
    template_key: str | None = None,
) -> dict[str, Any]:
    trace = [
        {"step": 1, "event": "discover_tools", "tools": TOOL_NAMES, "transport": "stdio"}
    ]
    for number, name in enumerate(tools or [], start=2):
        trace.append(
            {
                "step": number,
                "event": "tool_call",
                "tool": name,
                "arguments": (tool_arguments or {}).get(name, {}),
                "status": "ok",
            }
        )
    citation_rows = [{"document_id": name} for name in citations or []]
    refinement: dict[str, Any] = {"status": "not_called", "model": None}
    if refinement_status:
        if refinement_status == "cached_template":
            refinement = {
                "status": refinement_status,
                "provider": refinement_provider,
                "upstream_provider": "openrouter+opencode-zen",
                "model": None,
                "cache_hit": True,
                "response_mode": "sqlite_template",
                "template_key": template_key or "remote_work_positive_v1",
                "template_version": "1",
                "attempted_models": ["qwen/qwen3.8-27b:free", "opencode/space-bunny-free"],
            }
        else:
            refinement = {
                "status": refinement_status,
                "provider": refinement_provider,
                "model": "qwen/qwen3.8-27b:free",
                "attempted_models": ["qwen/qwen3.8-27b:free"],
            }
        trace.append({"step": len(trace) + 1, "event": "llm_refinement", **refinement})
    return {
        "answer": answer,
        "citations": citation_rows,
        "trace": trace,
        "status": status,
        "requires_confirmation": status == "confirmation_required",
        "llm": {"refinement": refinement},
    }


@contextmanager
def _hosted_app(
    chat_handler: Callable[[dict[str, Any]], tuple[int, dict[str, Any]]],
):
    chat_requests: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/health/ready":
                payload = {"status": "ok"}
                status = 200
            elif self.path == "/health?deep=true":
                payload = {
                    "status": "ok",
                    "mcp": {"status": "available", "tools": TOOL_NAMES},
                    "rag_index": {"status": "ready"},
                    "llm_provider": {"status": "configured"},
                }
                status = 200
            else:
                payload = {"detail": "not found"}
                status = 404
            self._write_json(status, payload)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/chat":
                self._write_json(404, {"detail": "not found"})
                return
            size = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(size))
            chat_requests.append(request)
            status, payload = chat_handler(request)
            self._write_json(status, payload)

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.chat_requests = chat_requests  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _run_smoke(
    server: ThreadingHTTPServer,
    *,
    confirm_mock_email: bool = False,
) -> subprocess.CompletedProcess[str]:
    base_url = f"http://127.0.0.1:{server.server_port}"
    command = [sys.executable, str(SMOKE_SCRIPT), "--base-url", base_url]
    if confirm_mock_email:
        command.append("--confirm-mock-email")
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_hosted_smoke_cli_reports_demo_gates_without_printing_answers() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        message = request["message"]
        confirmed = request.get("confirm_action", False)
        if "E1004 and E1003" in message and "medical" in message.lower():
            return 200, _chat_response(
                status="refused",
                answer="Use the confidential HR channel; no employee records were accessed.",
            )
        if "E1004 and E1003" in message:
            return 200, _chat_response(
                status="refused",
                answer="Please ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        if "overseas" in message.lower():
            return 200, _chat_response(
                status="provisionally_eligible",
                answer=(
                    "E1001 is provisionally eligible, subject to manager, HR, tax, information security, "
                    "and immigration review."
                ),
                tools=["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                citations=["POL-RW-01", "POL-SEC-01", "POL-APR-01"],
                tool_arguments=REMOTE_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        if "draft an email" in message.lower() and confirmed:
            return 200, _chat_response(
                status="mock_action_completed",
                answer="A fictional mock email draft was created; no email was sent.",
                tools=[
                    "search_policy_documents",
                    "lookup_employee_profile",
                    "check_pto_balance",
                    "check_policy_compliance",
                    "draft_hr_email",
                ],
                citations=["POL-PTO-01"],
                tool_arguments={
                    **PTO_TOOL_ARGUMENTS,
                    "draft_hr_email": {
                        "employee_id": "E1002",
                        "purpose": "PTO request",
                        "requested_days": 3,
                        "confirmed": True,
                    },
                },
                refinement_status="completed",
            )
        if "draft an email" in message.lower():
            return 200, _chat_response(
                status="confirmation_required",
                answer="Explicit confirmation is required before a mock email draft can be created.",
                tools=[
                    "search_policy_documents",
                    "lookup_employee_profile",
                    "check_pto_balance",
                    "check_policy_compliance",
                ],
                citations=["POL-PTO-01"],
                tool_arguments=PTO_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        raise AssertionError(f"Unexpected smoke request: {message}")

    with _hosted_app(respond) as server:
        result = _run_smoke(server, confirm_mock_email=True)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "passed"
    assert report["readiness"] == "ok"
    assert report["mcp_tool_count"] == 8
    assert [check["name"] for check in report["checks"]] == [
        "medical_privacy",
        "multiple_employee_privacy",
        "remote_work",
        "pto_confirmation_gate",
        "confirmed_mock_email",
    ]
    assert report["checks"][2]["model"] == "qwen/qwen3.8-27b:free"
    assert report["checks"][2]["citation_count"] == 3
    assert report["checks"][3]["status"] == "confirmation_required"
    assert "draft_hr_email" not in report["checks"][3]["tools"]
    assert report["checks"][4]["status"] == "mock_action_completed"
    assert "draft_hr_email" in report["checks"][4]["tools"]
    assert len(server.chat_requests) == 5
    assert server.chat_requests[-2]["confirm_action"] is False
    assert server.chat_requests[-1]["confirm_action"] is True
    assert PRIVATE_ANSWER_SENTINEL not in result.stdout


def test_hosted_smoke_cli_does_not_confirm_mock_email_by_default() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        message = request["message"]
        if "E1004 and E1003" in message and "medical" in message.lower():
            return 200, _chat_response(
                status="refused",
                answer="Use the confidential HR channel; no employee records were accessed.",
            )
        if "E1004 and E1003" in message:
            return 200, _chat_response(
                status="refused",
                answer="Please ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        if "overseas" in message.lower():
            return 200, _chat_response(
                status="provisionally_eligible",
                answer="Provisionally eligible after manager, HR, tax, information security, and immigration review.",
                tools=["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                citations=["POL-RW-01"],
                tool_arguments=REMOTE_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        if "draft an email" in message.lower() and request["confirm_action"] is False:
            return 200, _chat_response(
                status="confirmation_required",
                answer="Explicit confirmation is required before creating the mock email.",
                tools=[
                    "search_policy_documents",
                    "lookup_employee_profile",
                    "check_pto_balance",
                    "check_policy_compliance",
                ],
                citations=["POL-PTO-01"],
                tool_arguments=PTO_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        return 409, {"detail": "The smoke command should not confirm this mock action."}

    with _hosted_app(respond) as server:
        result = _run_smoke(server)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "passed"
    assert report["confirmed_mock_action"] == "skipped"
    assert len(server.chat_requests) == 4
    assert all(request["confirm_action"] is False for request in server.chat_requests)
    assert PRIVATE_ANSWER_SENTINEL not in result.stdout


def test_hosted_smoke_cli_accepts_traced_sqlite_template_for_read_only_case() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        message = request["message"]
        if "medical" in message.lower():
            return 200, _chat_response(
                status="refused",
                answer="Use the confidential HR channel; no employee records were accessed.",
            )
        if "E1004 and E1003" in message:
            return 200, _chat_response(
                status="refused",
                answer="Ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        if "overseas" in message.lower():
            return 200, _chat_response(
                status="provisionally_eligible",
                answer=(
                    "E1001 is provisionally eligible after manager, HR, tax, information security, "
                    "and immigration review."
                ),
                tools=["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                citations=["POL-RW-01", "POL-SEC-01", "POL-APR-01"],
                tool_arguments=REMOTE_TOOL_ARGUMENTS,
                refinement_status="cached_template",
                refinement_provider="sqlite",
                template_key="remote_work_eligible",
            )
        if "draft an email" in message.lower():
            return 200, _chat_response(
                status="confirmation_required",
                answer="Explicit confirmation is required before a mock email draft can be created.",
                tools=[
                    "search_policy_documents",
                    "lookup_employee_profile",
                    "check_pto_balance",
                    "check_policy_compliance",
                ],
                citations=["POL-PTO-01"],
                tool_arguments=PTO_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        raise AssertionError(f"Unexpected smoke request: {message}")

    with _hosted_app(respond) as server:
        result = _run_smoke(server)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "passed"
    remote_work = report["checks"][2]
    assert remote_work["status"] == "provisionally_eligible"
    assert remote_work["response_source"] == "sqlite_template"
    assert remote_work["provider"] == "sqlite"
    assert remote_work["template_key"] == "remote_work_eligible"
    assert report["checks"][3]["response_source"] == "live_model"
    assert len(server.chat_requests) == 4


def test_hosted_smoke_cli_rejects_sqlite_template_for_confirmation_gated_pto() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        message = request["message"]
        if "medical" in message.lower():
            return 200, _chat_response(
                status="refused",
                answer="Use the confidential HR channel; no employee records were accessed.",
            )
        if "E1004 and E1003" in message:
            return 200, _chat_response(
                status="refused",
                answer="Ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        if "overseas" in message.lower():
            return 200, _chat_response(
                status="provisionally_eligible",
                answer="Provisionally eligible after manager, HR, tax, information security, and immigration review.",
                tools=["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                citations=["POL-RW-01"],
                tool_arguments=REMOTE_TOOL_ARGUMENTS,
                refinement_status="completed",
            )
        if "draft an email" in message.lower():
            return 200, _chat_response(
                status="confirmation_required",
                answer="Explicit confirmation is required before a mock email draft can be created.",
                tools=[
                    "search_policy_documents",
                    "lookup_employee_profile",
                    "check_pto_balance",
                    "check_policy_compliance",
                ],
                citations=["POL-PTO-01"],
                tool_arguments=PTO_TOOL_ARGUMENTS,
                refinement_status="cached_template",
                refinement_provider="sqlite",
                template_key="pto_request",
            )
        raise AssertionError(f"Unexpected smoke request: {message}")

    with _hosted_app(respond) as server:
        result = _run_smoke(server)

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["status"] == "failed"
    assert report["failed_check"]["name"] == "pto_confirmation_gate"
    assert report["failed_check"]["reason"] == "llm_refinement_incomplete"
    assert report["failed_check"]["llm_status"] == "cached_template"
    assert PRIVATE_ANSWER_SENTINEL not in result.stdout
    assert len(server.chat_requests) == 4


def test_hosted_smoke_cli_checks_structured_tool_arguments() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        message = request["message"]
        if "E1004 and E1003" in message and "medical" in message.lower():
            return 200, _chat_response(
                status="refused",
                answer="Use the confidential HR channel; no employee records were accessed.",
            )
        if "E1004 and E1003" in message:
            return 200, _chat_response(
                status="refused",
                answer="Please ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        if "overseas" in message.lower():
            wrong_arguments = {name: dict(values) for name, values in REMOTE_TOOL_ARGUMENTS.items()}
            wrong_arguments["check_policy_compliance"]["requested_days"] = 9
            return 200, _chat_response(
                status="provisionally_eligible",
                answer="Provisionally eligible after manager, HR, tax, information security, and immigration review.",
                tools=["search_policy_documents", "lookup_employee_profile", "check_policy_compliance"],
                citations=["POL-RW-01"],
                tool_arguments=wrong_arguments,
                refinement_status="completed",
            )
        return 409, {"detail": "The smoke command should stop after the wrong remote-work arguments."}

    with _hosted_app(respond) as server:
        result = _run_smoke(server)

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["failed_check"]["name"] == "remote_work"
    assert report["failed_check"]["reason"] == "unexpected_tool_arguments"
    assert report["failed_check"]["tool"] == "check_policy_compliance"
    assert report["failed_check"]["argument_keys"] == ["requested_days"]
    assert len(server.chat_requests) == 3


def test_hosted_smoke_cli_fails_closed_and_redacts_provider_body() -> None:
    def respond(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if "E1004 and E1003" in request["message"]:
            return 200, _chat_response(
                status="refused",
                answer="Please ask about one synthetic employee ID per request; no employee records were accessed.",
            )
        return 503, {
            "detail": PROVIDER_BODY_SENTINEL,
            "answer": PROVIDER_BODY_SENTINEL,
            "status": "llm_unavailable",
            "trace": [{"event": "llm_refinement", "status": "unavailable"}],
            "llm": {
                "refinement": {
                    "status": "unavailable",
                    "model": None,
                    "attempts": 4,
                    "model_attempts": [
                        {
                            "model": "qwen/qwen3.8-27b:free",
                            "outcome": "unavailable",
                            "error_type": "HTTPStatusError",
                            "http_status": "429",
                            "provider_body": PROVIDER_BODY_SENTINEL,
                        },
                        {
                            "model": "nvidia/nemotron-3.5-lightning:free",
                            "outcome": "unavailable",
                            "error_type": "ReadTimeout",
                        },
                        {
                            "model": "google/gemma-4-26b-a4b-it:free",
                            "outcome": "unavailable",
                            "error_type": "HTTPStatusError",
                            "http_status": "429",
                        },
                        {
                            "model": "openrouter/free",
                            "outcome": "unavailable",
                            "error_type": "HTTPStatusError",
                            "http_status": "429",
                        },
                    ],
                }
            },
        }

    with _hosted_app(respond) as server:
        result = _run_smoke(server)

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["status"] == "failed"
    assert report["failed_check"]["name"] == "remote_work"
    assert report["failed_check"]["http_status"] == 503
    assert report["failed_check"]["model_attempts"] == [
        {
            "model": "qwen/qwen3.8-27b:free",
            "outcome": "unavailable",
            "error_type": "HTTPStatusError",
            "http_status": "429",
        },
        {
            "model": "nvidia/nemotron-3.5-lightning:free",
            "outcome": "unavailable",
            "error_type": "ReadTimeout",
        },
        {
            "model": "google/gemma-4-26b-a4b-it:free",
            "outcome": "unavailable",
            "error_type": "HTTPStatusError",
            "http_status": "429",
        },
        {
            "model": "openrouter/free",
            "outcome": "unavailable",
            "error_type": "HTTPStatusError",
            "http_status": "429",
        },
    ]
    assert PROVIDER_BODY_SENTINEL not in result.stdout
    assert PRIVATE_ANSWER_SENTINEL not in result.stdout
    assert len(server.chat_requests) == 3
