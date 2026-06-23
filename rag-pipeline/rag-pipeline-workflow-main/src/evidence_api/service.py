from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from evidence_api.abstain import evaluate_retrieval_reliability
from evidence_api.confidence import compute_confidence
from evidence_api.query_rewrite import company_display_name, rewrite_query_for_company
from evidence_api.record_catalog import RecordCatalog, infer_evidence_type
from evidence_api.schemas import EvidenceItem, RetrieveRequest, RetrieveResponse
from evidence_api.staging_config import (
    apply_company_env,
    company_cfg,
    company_registry,
    load_staging_config,
    package_jsonl_paths,
    reset_retrieval_runtime_caches,
)
from production_config import index_ready, repo_root


class CompanyNotIndexed(Exception):
    def __init__(self, company_id: str) -> None:
        self.company_id = company_id
        super().__init__(company_id)


class EvidenceRetrievalService:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self._root = repo_root()
        self._cfg = load_staging_config(config_path)
        self._catalog_cache: dict[str, RecordCatalog] = {}
        self._active_company: Optional[str] = None

    @property
    def config(self) -> dict:
        return self._cfg

    def known_company_ids(self) -> List[str]:
        return sorted(company_registry(self._cfg))

    def is_indexed(self, company_id: str) -> bool:
        if company_id not in company_registry(self._cfg):
            return False
        return index_ready(company_cfg(self._cfg, company_id))

    def _ensure_company_runtime(self, company_id: str) -> RecordCatalog:
        if company_id not in company_registry(self._cfg):
            raise CompanyNotIndexed(company_id)
        if not self.is_indexed(company_id):
            raise CompanyNotIndexed(company_id)

        if self._active_company != company_id:
            apply_company_env(self._cfg, company_id, base_dir=self._root)
            reset_retrieval_runtime_caches()
            self._active_company = company_id

        if company_id not in self._catalog_cache:
            entry = company_registry(self._cfg)[company_id]
            split = entry.get("record_split", "full")
            paths = package_jsonl_paths(self._root, entry["package"], split)
            self._catalog_cache[company_id] = RecordCatalog(paths)
        return self._catalog_cache[company_id]

    @staticmethod
    def _stack_retrieval_mode(stack: dict) -> str:
        mode = (stack.get("retrieval_mode") or "hybrid_dense_bm25").strip()
        if mode:
            return mode
        reranker = (stack.get("reranker") or "none").strip().lower()
        if reranker not in ("none", ""):
            return "hybrid_dense_bm25_rerank"
        return "hybrid_dense_bm25"

    def retrieve(self, req: RetrieveRequest) -> RetrieveResponse:
        catalog = self._ensure_company_runtime(req.company_id)
        stack = self._cfg["stack"]
        pool = int(stack.get("candidate_pool", 64))
        mode = self._stack_retrieval_mode(stack)
        registry_entry = company_registry(self._cfg)[req.company_id]
        search_query = rewrite_query_for_company(req.query, req.company_id, registry_entry)
        from retrieval_v3 import retrieve

        hits, _note = retrieve(search_query, mode, pool, pool)
        evidence_type = req.filters.evidence_type if req.filters else None

        items: List[EvidenceItem] = []
        for hit in hits:
            record = catalog.resolve_from_chunk(hit.text)
            if not catalog.passes_filters(record, year=req.year, evidence_type=evidence_type):
                continue
            metric = (record or {}).get("metric") if record else None
            metric_name = None
            value = None
            unit = None
            if isinstance(metric, dict):
                metric_name = metric.get("metric_name")
                raw = metric.get("value_raw")
                norm = metric.get("value_normalized")
                value = str(raw if raw is not None else norm if norm is not None else "")
                unit = metric.get("unit")
            items.append(
                EvidenceItem(
                    text=hit.text,
                    source=hit.source,
                    score=round(float(hit.score), 4),
                    confidence=compute_confidence(float(hit.score), record),
                    page=(record or {}).get("page"),
                    section_path=(record or {}).get("section_path"),
                    metric_name=metric_name,
                    value=value or None,
                    unit=unit,
                    record_id=(record or {}).get("record_id"),
                    evidence_type=infer_evidence_type(record) if record else "text",
                )
            )
            if len(items) >= req.top_k:
                break

        display = company_display_name(req.company_id, registry_entry)
        reliability = evaluate_retrieval_reliability(req.query, display, items)

        annotated: List[EvidenceItem] = []
        for item, assessment in zip(items, reliability.item_assessments):
            annotated.append(
                item.model_copy(
                    update={
                        "answerable_candidate": assessment.answerable_candidate,
                        "candidate_confidence": assessment.candidate_confidence,
                        "candidate_flags": list(assessment.candidate_flags),
                    }
                )
            )
        # Pad if assessments shorter than items (should not happen)
        if len(annotated) < len(items):
            annotated.extend(items[len(annotated) :])

        return RetrieveResponse(
            items=annotated,
            company_id=req.company_id,
            query=req.query,
            abstain_recommended=reliability.abstain_recommended,
            no_relevant_evidence=reliability.no_relevant_evidence,
            retrieval_confidence=reliability.retrieval_confidence,
            reliability_reason=reliability.reliability_reason,
            reliability_flags=list(reliability.reliability_flags),
            abstain_reason=reliability.abstain_reason,
        )
