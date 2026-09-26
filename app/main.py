from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent.llm import (
    get_provider,
    get_refinement_status,
    provider_status,
    reset_refinement_status,
)
from agent.orchestrator import MSAIEOrchestrator
from mcp_client.client import MCPGateway, MCPGatewayError
from rag.index import get_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index = get_index().ensure()
    gateway = MCPGateway()
    try:
        app.state.mcp = await gateway.discover()
    except MCPGatewayError as exc:
        app.state.mcp = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    yield


app = FastAPI(
    title="MSAIE HR Agent",
    version="2.1.0",
    description="A synthetic agentic HR assistant with persistent policy RAG, genuine MCP tool calls and constrained LLM refinement.",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    confirm_action: bool = False


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    supporting_snippets: list[str]
    trace: list[dict[str, Any]]
    status: str
    requires_confirmation: bool
    confidence: str
    mcp: dict[str, Any]
    llm: dict[str, Any]


@app.get("/health")
async def health(deep: bool = Query(False)) -> dict[str, Any]:
    mcp_status = getattr(app.state, "mcp", {"status": "unknown", "tools": []})
    if deep:
        gateway = MCPGateway()
        try:
            mcp_status = await gateway.discover()
            app.state.mcp = mcp_status
        except MCPGatewayError as exc:
            mcp_status = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    index_status = get_index().stats()
    return {
        "status": "ok" if index_status.get("status") == "ready" else "degraded",
        "service": "msaie-hr-agent",
        "version": app.version,
        "mode": "agentic-rag-mcp-llm",
        "mcp": mcp_status,
        "rag_index": index_status,
        "llm_provider": provider_status(),
        "synthetic_data_only": True,
    }


@app.get("/api/tools")
async def tools() -> dict[str, Any]:
    gateway = MCPGateway()
    try:
        return await gateway.discover()
    except MCPGatewayError as exc:
        return {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict[str, Any]:
    reset_refinement_status()
    orchestrator = MSAIEOrchestrator()
    result = await orchestrator.handle(request.message, request.confirm_action)

    provider = get_provider()
    refinement = get_refinement_status()
    refinable_statuses = {
        "completed",
        "provisionally_eligible",
        "not_eligible",
        "mock_action_completed",
        "escalated",
    }
    if (
        provider.configured
        and result.citations
        and result.status in refinable_statuses
        and refinement.get("status") == "not_called"
    ):
        result.answer = await provider.refine(
            result.answer,
            result.citations,
            status=result.status,
            structured_facts=result.structured_facts,
        )
        refinement = get_refinement_status()

    if provider.configured and refinement.get("status") in {
        "completed",
        "fallback_to_controlled_draft",
    }:
        trace_entry = {
            "step": len(result.trace) + 1,
            "event": "llm_refinement",
            **refinement,
        }
        result.trace.append(trace_entry)

    llm_status = dict(refinement)
    if not provider.configured and llm_status.get("status") == "not_called":
        llm_status = {
            "status": "not_configured",
            "provider": provider.provider_type,
            "model": provider.model,
            "temperature": None,
        }
    return {
        **result.as_dict(),
        "llm": {
            "provider": provider_status(),
            "refinement": llm_status,
        },
    }


_STATIC_UI = Path(__file__).resolve().parent / "static" / "index.html"


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _STATIC_UI.read_text(encoding="utf-8")
