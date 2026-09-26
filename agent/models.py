from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentResult:
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    supporting_snippets: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    requires_confirmation: bool = False
    confidence: str = "medium"
    mcp: dict[str, Any] = field(default_factory=dict)
    structured_facts: dict[str, Any] = field(default_factory=dict, repr=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "supporting_snippets": self.supporting_snippets,
            "trace": self.trace,
            "status": self.status,
            "requires_confirmation": self.requires_confirmation,
            "confidence": self.confidence,
            "mcp": self.mcp,
        }
