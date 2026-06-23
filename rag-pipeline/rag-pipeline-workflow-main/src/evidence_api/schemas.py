from __future__ import annotations

import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

EvidenceType = Literal["metric", "policy", "strategy", "risk", "text"]
ConfidenceLevel = Literal["low", "medium", "high"]


class RetrieveFilters(BaseModel):
    evidence_type: Optional[EvidenceType] = None
    taxonomy_item_id: Optional[str] = None
    language: Optional[str] = None


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["What is the ticker?"])
    company_id: str = Field(..., min_length=1, examples=["musinsa"])
    top_k: int = Field(default=8, ge=1, le=32)
    year: Optional[int] = Field(default=None, description="Filter cung; package nexteye chua co year metadata")
    filters: Optional[RetrieveFilters] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "ESG carbon emissions",
                    "company_id": "musinsa",
                    "top_k": 8,
                },
                {
                    "query": "governance policy",
                    "company_id": "hanssem",
                    "top_k": 8,
                    "filters": {"evidence_type": "policy"},
                },
                {
                    "query": "ESG 지속가능경영",
                    "company_id": "rayshion",
                    "top_k": 5,
                },
            ]
        }
    }

    @field_validator("company_id")
    @classmethod
    def normalize_company_id(cls, value: str) -> str:
        slug = value.strip().lower()
        if not _SLUG_RE.match(slug):
            raise ValueError("company_id phai la slug lowercase (vd. musinsa)")
        return slug


class EvidenceItem(BaseModel):
    text: str
    source: str
    score: float
    confidence: ConfidenceLevel
    page: Optional[int] = None
    section_path: Optional[str] = None
    metric_name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    record_id: Optional[str] = None
    evidence_type: Optional[EvidenceType] = None
    answerable_candidate: bool = False
    candidate_confidence: ConfidenceLevel = "low"
    candidate_flags: List[str] = Field(default_factory=list)


class RetrieveResponse(BaseModel):
    items: List[EvidenceItem]
    company_id: str
    query: str
    abstain_recommended: bool = False
    no_relevant_evidence: bool = False
    retrieval_confidence: ConfidenceLevel = "high"
    reliability_reason: Optional[str] = Field(
        default=None,
        description="Human-readable explanation when retrieval is not trustworthy for answering",
    )
    reliability_flags: List[str] = Field(
        default_factory=list,
        description="Structured reliability signals (metric_anchor_missing, domain_mismatch, ...)",
    )
    abstain_reason: Optional[str] = Field(
        default=None,
        description="Primary reliability flag; kept for backward compatibility with reliability_flags[0]",
    )


class CompanyNotIndexedError(BaseModel):
    error: Literal["company_not_indexed"] = "company_not_indexed"
    company_id: str


class CompanyListItem(BaseModel):
    company_id: str
    indexed: bool
    record_split: str = "full"
    legacy_cache_only: bool = False


class CompaniesResponse(BaseModel):
    items: List[CompanyListItem]
    count: int
    indexed_count: int


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    mode: str = "langgraph_staging"
    rerank_enabled: bool = False
    gpu: bool = False
    index_version: Optional[str] = None
    companies_indexed: List[str] = Field(default_factory=list)
    companies_pending: List[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    company_id: str
    package_path: Optional[str] = None
    record_split: Optional[str] = "full"


class IngestJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"


class IngestJobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    company_id: Optional[str] = None
    message: Optional[str] = None
