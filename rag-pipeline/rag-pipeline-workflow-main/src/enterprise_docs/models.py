"""Data models for enterprise / internal-document RAG lane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SourceType = Literal[
    "markdown",
    "html",
    "json",
    "jsonl",
    "xml",
    "csv",
    "pdf",
    "text",
    "unknown",
]

AnswerMode = Literal["single_document_answer", "cross_document_answer", "unknown"]


@dataclass
class EvidenceUnit:
    """Normalized evidence chunk for retrieval / extraction."""

    unit_id: str
    company_id: str
    document_id: str
    source_path: str
    source_type: SourceType
    text: str
    search_text: str
    evidence_text: str
    section: str | None = None
    topic: str | None = None
    year: int | None = None
    esg_domain: str | None = None
    esg_category: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentDescriptor:
    document_id: str
    source_path: str
    source_type: SourceType
    title: str
    esg_domains: list[str] = field(default_factory=list)
    year_hint: int | None = None
    byte_size: int = 0


@dataclass
class EvidencePlan:
    """Planned evidence sources for a question (prototype, not gold)."""

    item_id: str
    answer_mode: AnswerMode
    primary_document_ids: list[str]
    supporting_document_ids: list[str]
    roles: dict[str, str]
    needs_merge: bool
    needs_conflict_resolution: bool
    notes: str = ""
