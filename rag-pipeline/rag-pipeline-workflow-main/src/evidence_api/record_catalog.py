from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from evidence_api.schemas import EvidenceType

RECORD_ID_RE = re.compile(r"record_id:\s*(\S+)", re.IGNORECASE)

TRUSTED_SOURCE_TYPES = {
    "annual_report",
    "sustainability_report",
    "policy",
    "governance_report",
}


def infer_evidence_type(record: Dict[str, Any]) -> EvidenceType:
    metric = record.get("metric")
    if isinstance(metric, dict) and metric.get("metric_name"):
        return "metric"
    tags = [str(t).lower() for t in (record.get("esg_tags") or [])]
    source_type = str(record.get("source_type") or "").lower()
    section = str(record.get("section_path") or "").lower()
    if source_type in {"policy", "governance_report"}:
        return "policy"
    if any(k in section for k in ("strategy", "chiến lược", "전략")) or any(
        "strategy" in t for t in tags
    ):
        return "strategy"
    if any(k in section for k in ("risk", "rủi ro", "리스크")) or any("risk" in t for t in tags):
        return "risk"
    if any(t.startswith("e.") for t in tags):
        return "metric"
    return "text"


def record_matches_evidence_type(record: Dict[str, Any], evidence_type: EvidenceType) -> bool:
    if evidence_type == "text":
        return True
    inferred = infer_evidence_type(record)
    if evidence_type == "metric":
        metric = record.get("metric")
        if isinstance(metric, dict) and metric.get("metric_name"):
            return True
        tags = [str(t).lower() for t in (record.get("esg_tags") or [])]
        return any(t.startswith("e.") or "emission" in t or "climate" in t for t in tags)
    if evidence_type == "policy":
        return str(record.get("source_type") or "").lower() in {"policy", "governance_report"}
    if evidence_type == "strategy":
        section = str(record.get("section_path") or "").lower()
        tags = [str(t).lower() for t in (record.get("esg_tags") or [])]
        return any("strategy" in x for x in [section, *tags])
    if evidence_type == "risk":
        section = str(record.get("section_path") or "").lower()
        tags = [str(t).lower() for t in (record.get("esg_tags") or [])]
        return any("risk" in x or "governance" in x for x in [section, *tags])
    return inferred == evidence_type


class RecordCatalog:
    def __init__(self, jsonl_paths: List[Path]) -> None:
        self._by_id: Dict[str, Dict[str, Any]] = {}
        for path in jsonl_paths:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(item, dict):
                    continue
                rid = str(item.get("record_id") or item.get("chunk_id") or "").strip()
                if rid:
                    norm = dict(item)
                    norm.setdefault("record_id", rid)
                    if norm.get("section_hint") and not norm.get("section_path"):
                        norm["section_path"] = norm["section_hint"]
                    meta = norm.get("metadata") if isinstance(norm.get("metadata"), dict) else {}
                    year_hint = meta.get("year_hint") or norm.get("year")
                    if year_hint and norm.get("year") is None:
                        try:
                            norm["year"] = int(str(year_hint)[:4])
                        except ValueError:
                            pass
                    self._by_id[rid] = norm

    @property
    def size(self) -> int:
        return len(self._by_id)

    def resolve_from_chunk(self, chunk_text: str) -> Optional[Dict[str, Any]]:
        match = RECORD_ID_RE.search(chunk_text or "")
        if not match:
            return None
        return self._by_id.get(match.group(1))

    def passes_filters(
        self,
        record: Optional[Dict[str, Any]],
        *,
        year: Optional[int],
        evidence_type: Optional[EvidenceType],
    ) -> bool:
        if record is None:
            return year is None and evidence_type is None
        if year is not None:
            rec_year = record.get("year")
            if rec_year is None or int(rec_year) != int(year):
                return False
        if evidence_type is not None and not record_matches_evidence_type(record, evidence_type):
            return False
        return True
