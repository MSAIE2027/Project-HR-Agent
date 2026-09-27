from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from agent.llm import (
    LLMProviderError,
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
    description="A synthetic agentic HR assistant with policy RAG, MCP workflows, and required OpenRouter answer generation.",
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


def _llm_failure_response(
    detail: str,
    *,
    result: AgentResult,
    refinement: dict[str, Any],
) -> JSONResponse:
    trace = list(result.trace)
    trace.append({"step": len(trace) + 1, "event": "llm_refinement", **refinement})
    return JSONResponse(
        status_code=503,
        content={
            "detail": detail,
            "answer": detail,
            "status": "llm_unavailable",
            "requires_confirmation": result.requires_confirmation,
            "confidence": "low",
            "trace": trace,
            "llm": {"provider": provider_status(), "refinement": refinement},
        },
    )


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
    llm_status = provider_status()
    ready = (
        index_status.get("status") == "ready"
        and llm_status.get("status") == "configured"
        and mcp_status.get("status") == "available"
    )
    return {
        "status": "ok" if ready else "degraded",
        "service": "msaie-hr-agent",
        "version": app.version,
        "mode": "agentic-rag-mcp-llm",
        "mcp": mcp_status,
        "rag_index": index_status,
        "llm_provider": llm_status,
        "synthetic_data_only": True,
    }


@app.get("/health/ready")
async def readiness() -> dict[str, Any]:
    report = await health(deep=False)
    if report["status"] != "ok":
        raise HTTPException(
            status_code=503,
            detail="The policy index and required OpenRouter configuration must be ready before serving traffic.",
        )
    return report


@app.get("/api/tools")
async def tools() -> dict[str, Any]:
    gateway = MCPGateway()
    try:
        return await gateway.discover()
    except MCPGatewayError as exc:
        return {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}


@app.get("/api/index/documents")
def index_documents() -> dict[str, Any]:
    index = get_index()
    stats = index.stats()
    return {
        "storage": "SQLite",
        "vectors_exposed": False,
        "index": {
            key: stats.get(key)
            for key in (
                "status",
                "documents",
                "chunks",
                "embedding_model",
                "embedding_provider",
                "dimensions",
                "chunk_words",
                "overlap_words",
            )
        },
        "documents": index.list_documents(),
    }


@app.get("/api/index/documents/{document_id}/chunks")
def index_document_chunks(
    document_id: str,
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    if not re.fullmatch(r"POL-[A-Z0-9]+-\d{2}", document_id.upper()):
        raise HTTPException(status_code=404, detail="Policy document was not found.")
    chunks = get_index().get_chunks(document_id, limit=limit)
    if not chunks:
        raise HTTPException(status_code=404, detail="Policy document was not found.")
    return {"document_id": document_id.upper(), "chunks": chunks, "vectors_exposed": False}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict[str, Any]:
    reset_refinement_status()
    orchestrator = MSAIEOrchestrator()
    result = await orchestrator.handle(request.message, request.confirm_action)

    provider = get_provider()
    refinement = get_refinement_status()
    if result.citations:
        if not provider.configured:
            refinement = {
                "status": "not_configured",
                "provider": provider.provider_type,
                "model": None,
                "attempted_models": [],
                "attempts": 0,
            }
            return _llm_failure_response(
                "OpenRouter is required to generate evidence-backed answers, but it is not configured.",
                result=result,
                refinement=refinement,
            )
        structured_facts = dict(result.structured_facts)
        if result.requires_confirmation:
            structured_facts["requires_confirmation"] = True
        try:
            result.answer = await provider.refine(
                result.answer,
                result.citations,
                status=result.status,
                structured_facts=structured_facts,
            )
        except LLMProviderError:
            refinement = get_refinement_status()
            return _llm_failure_response(
                "Required OpenRouter answer generation failed; no unrefined policy response was returned.",
                result=result,
                refinement=refinement,
            )
        refinement = get_refinement_status()
        if refinement.get("status") != "completed":
            return _llm_failure_response(
                "Required OpenRouter answer generation did not pass response validation.",
                result=result,
                refinement=refinement,
            )

    if result.citations and refinement.get("status") == "completed":
        trace_entry = {
            "step": len(result.trace) + 1,
            "event": "llm_refinement",
            **refinement,
        }
        result.trace.append(trace_entry)

    llm_status = dict(refinement)
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
