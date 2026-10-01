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
from agent.response_cache import cached_response
from mcp_client.client import MCPGateway, MCPGatewayError
from rag.index import (
    DEFAULT_LOCAL_MODEL,
    HF_EMBEDDING_BACKEND,
    HF_EMBEDDING_MAX_LENGTH,
    HF_EMBEDDING_REVISION,
    get_index,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index = get_index().ensure()
    gateway = MCPGateway()
    app.state.mcp_gateway = gateway
    try:
        await gateway.start()
        app.state.mcp = await gateway.discover()
    except MCPGatewayError as exc:
        app.state.mcp = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    try:
        yield
    finally:
        await gateway.close()


app = FastAPI(
    title="MSAIE HR Agent",
    version="2.1.0",
    description="A synthetic agentic HR assistant with policy RAG, MCP workflows, and required OpenRouter answer generation.",
    lifespan=lifespan,
)


def _pinned_index_ready(index_status: dict[str, Any]) -> bool:
    return (
        index_status.get("status") == "ready"
        and index_status.get("semantic_embeddings") is True
        and index_status.get("embedding_provider") == "huggingface"
        and index_status.get("embedding_model") == DEFAULT_LOCAL_MODEL
        and index_status.get("embedding_backend") == HF_EMBEDDING_BACKEND
        and index_status.get("embedding_revision") == HF_EMBEDDING_REVISION
        and index_status.get("embedding_max_length") == HF_EMBEDDING_MAX_LENGTH
        and index_status.get("dimensions") == 384
        and index_status.get("chunk_words") == 120
        and index_status.get("overlap_words") == 20
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
    # The created artifact, returned verbatim. The narrative answer is
    # model-composed and may summarise; this field is the deliverable itself.
    mock_action: dict[str, Any] | None = None


def _mcp_gateway() -> MCPGateway:
    return getattr(app.state, "mcp_gateway", None) or MCPGateway()


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
            "citations": result.citations,
            "supporting_snippets": result.supporting_snippets,
            "requires_confirmation": result.requires_confirmation,
            "confidence": "low",
            "trace": trace,
            "llm": {"provider": provider_status(), "refinement": refinement},
            # An action may already have been created before composition failed.
            # Withholding it here would tell the user a draft exists while hiding it.
            "mock_action": result.mock_action,
        },
    )


def _cached_refinement(result: AgentResult, failure: dict[str, Any]) -> dict[str, Any] | None:
    """Use only a current-facts SQLite template when live answer generation failed."""
    try:
        rendered = cached_response(get_index(), result)
    except Exception:
        return None
    if rendered is None:
        return None

    answer, cache_metadata = rendered
    result.answer = answer
    refinement: dict[str, Any] = {
        "status": "cached_template",
        "provider": "sqlite",
        "upstream_provider": failure.get("provider", "openrouter"),
        "model": None,
        "attempted_models": failure.get("attempted_models", []),
        "model_attempts": failure.get("model_attempts", []),
        "attempts": failure.get("attempts", 0),
        "fallback_from_status": failure.get("status", "unavailable"),
        **cache_metadata,
    }
    for field in ("failure_scope", "http_status", "error_type", "validation_issue"):
        if field in failure:
            refinement[field] = failure[field]
    result.trace.append(
        {"step": len(result.trace) + 1, "event": "llm_refinement", **refinement}
    )
    return refinement


@app.get("/health")
async def health(deep: bool = Query(False)) -> dict[str, Any]:
    mcp_status = getattr(app.state, "mcp", {"status": "unknown", "tools": []})
    if deep:
        gateway = _mcp_gateway()
        try:
            mcp_status = await gateway.discover()
            app.state.mcp = mcp_status
        except MCPGatewayError as exc:
            mcp_status = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    index_status = get_index().stats()
    llm_status = provider_status()
    ready = (
        _pinned_index_ready(index_status)
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
            detail="The pinned semantic index, required OpenRouter configuration, and MCP tools must be ready before serving traffic.",
        )
    return report


@app.get("/api/tools")
async def tools() -> dict[str, Any]:
    gateway = _mcp_gateway()
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
                "embedding_backend",
                "embedding_revision",
                "dimensions",
                "chunk_words",
                "overlap_words",
            )
        },
        "documents": index.list_documents(),
        "response_templates": index.list_response_templates(),
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
    orchestrator = MSAIEOrchestrator(_mcp_gateway())
    result = await orchestrator.handle(request.message, request.confirm_action)
    if result.mcp.get("status") in {"available", "unavailable"}:
        current_mcp = getattr(app.state, "mcp", {})
        app.state.mcp = {**current_mcp, **result.mcp}
        if result.mcp.get("status") == "available":
            app.state.mcp.pop("error", None)

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
        else:
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
                cached = _cached_refinement(result, refinement)
                if cached is None:
                    return _llm_failure_response(
                        "Required model answer generation failed; no unrefined policy response was returned.",
                        result=result,
                        refinement=refinement,
                    )
                refinement = cached
            else:
                refinement = get_refinement_status()
                if refinement.get("status") != "completed":
                    cached = _cached_refinement(result, refinement)
                    if cached is None:
                        return _llm_failure_response(
                            "Required model answer generation did not pass response validation.",
                            result=result,
                            refinement=refinement,
                        )
                    refinement = cached

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
