"""Standardized holdout harness for enterprise internal-doc lane."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from collections import Counter

from enterprise_docs.cross_doc_retriever import build_index_from_units
from enterprise_docs.family_generalization import summarize_holdout_by_family
from enterprise_docs.registries import company_config, load_company_doc_registry
from enterprise_docs.retrieval_index import score_units
from enterprise_docs.structured_extractor import probe_candidates_in_units

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class HoldoutProbeResult:
    company_id: str
    probe_id: str
    document_type: str
    family_guess: str
    parser_ok: bool
    retrieval_feasible: bool
    extraction_feasible: bool
    aggregation_feasible: bool
    readiness_state: str
    fail_stage: str
    kind: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _golden_to_unit(row: dict[str, Any], company_id: str) -> dict[str, Any]:
    doc_id = re.sub(r"[^0-9a-zA-Z가-힣_]+", "_", str(row.get("section_path") or "evidence"))[:80]
    text = str(row.get("text") or "")
    rid = str(row.get("record_id") or row.get("unit_id") or "unit")
    doc_type = str(row.get("source_type") or "narrative")
    return {
        "unit_id": f"{company_id}::{doc_id}::{rid[:12]}",
        "company_id": company_id,
        "document_id": doc_id,
        "source_type": doc_type,
        "text": text,
        "search_text": text,
        "evidence_text": text,
        "section": row.get("section_path"),
        "metadata": {"document_type": doc_type},
    }


def load_corpus_for_company(
    company_id: str,
    *,
    use_reingested: bool = False,
    use_filtered: bool = False,
    holdout_corpus: str | None = None,
) -> list[dict[str, Any]]:
    """Load corpus for holdout/demo evaluation.

    holdout_corpus overrides flags: baseline | reingested | filtered
    """
    if holdout_corpus:
        use_reingested = holdout_corpus in ("reingested", "filtered", "family_scoped", "overlap_strengthened")
        use_filtered = holdout_corpus in ("filtered", "family_scoped", "overlap_strengthened")

    cfg = company_config(company_id)
    if use_filtered:
        artifact_key = "corpus_filtered_artifact"
    elif use_reingested:
        artifact_key = "corpus_reingested_artifact"
    else:
        artifact_key = "corpus_artifact"
    artifact = cfg.get(artifact_key) or (cfg.get("corpus_artifact") if not use_reingested and not use_filtered else None)
    if not artifact:
        return []
    path = ROOT / str(artifact)
    if not path.exists():
        return []

    if company_id == "demo_company" or use_reingested or use_filtered:
        return _load_jsonl(path)

    rows = _load_jsonl(path)
    filt = cfg.get("corpus_filter") or {}
    if filt.get("company"):
        rows = [r for r in rows if r.get("company") == filt["company"]]
    elif company_id == "musinsa":
        rows = [r for r in rows if str(r.get("company") or "") == "무신사"][:20]

    return [_golden_to_unit(r, company_id) for r in rows if r.get("text")]


def _probe_has_signal(text: str, expected: str) -> bool:
    for part in (expected or "").split("|"):
        part = part.strip()
        if part and part.lower() in (text or "").lower():
            return True
    return False


def _guess_document_type(units: list[dict[str, Any]]) -> str:
    types: dict[str, int] = {}
    for u in units:
        t = str((u.get("metadata") or {}).get("document_type") or u.get("source_type") or "unknown")
        types[t] = types.get(t, 0) + 1
    return max(types, key=types.get) if types else "unknown"


def run_probe(
    probe: dict[str, Any],
    corpus_units: list[dict[str, Any]],
    *,
    company_id: str,
) -> HoldoutProbeResult:
    index, _ = build_index_from_units(corpus_units, company_id=company_id)
    doc_type = _guess_document_type(corpus_units)
    family = str(probe.get("pattern_family") or "unknown")
    kind = str(probe.get("kind") or "quantitative")

    parser_ok = bool(corpus_units) and all(
        bool(str(u.get("evidence_text") or u.get("text") or "").strip()) for u in corpus_units[:3]
    )

    ranked = score_units(str(probe.get("question") or ""), index, pool=16)
    top_texts = [str(u.get("evidence_text") or u.get("text") or "") for u, _ in ranked[:5]]
    retrieval_feasible = bool(ranked) and any(
        _probe_has_signal(t, str(probe.get("expected_signal") or "")) for t in top_texts
    )

    plan = {
        "item_id": probe.get("probe_id"),
        "question": probe.get("question"),
        "item": probe.get("item"),
        "subcategory": probe.get("subcategory"),
        "category": probe.get("category"),
        "company_id": company_id,
        "kind": kind,
    }
    candidates = probe_candidates_in_units(plan, [u for u, _ in ranked[:8]], min_score=0.1)
    extraction_feasible = bool(candidates) or (
        kind == "quantitative"
        and retrieval_feasible
        and any(re.search(r"\d+", t) for t in top_texts)
    )

    if kind == "qualitative" and retrieval_feasible:
        readiness_state = "not_ready_for_synthesis"
        fail_stage = "synthesis_gap"
        aggregation_feasible = False
    elif extraction_feasible:
        readiness_state = "extraction_ready"
        fail_stage = "ready"
        aggregation_feasible = True
    elif retrieval_feasible:
        readiness_state = "retrieval_ready"
        fail_stage = "ready"
        aggregation_feasible = False
    else:
        readiness_state = "coverage_gap"
        fail_stage = "retrieval_gap"
        aggregation_feasible = False

    return HoldoutProbeResult(
        company_id=company_id,
        probe_id=str(probe.get("probe_id") or ""),
        document_type=doc_type,
        family_guess=family,
        parser_ok=parser_ok,
        retrieval_feasible=retrieval_feasible,
        extraction_feasible=extraction_feasible,
        aggregation_feasible=aggregation_feasible,
        readiness_state=readiness_state,
        fail_stage=fail_stage,
        kind=kind,
        note="feasibility_only_no_gold_answer",
    )


def run_holdout_matrix(
    *,
    include_demo: bool = False,
) -> dict[str, Any]:
    """Run standardized holdout probes for configured companies."""
    reg = load_company_doc_registry()
    matrix: list[dict[str, Any]] = []
    by_company: dict[str, dict[str, Any]] = {}

    probe_files = {
        "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
        "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
    }

    if include_demo:
        probe_files["demo_company"] = ROOT / "data/enterprise_docs/demo_company/eval_subset_cross.jsonl"

    for company_id, probe_path in probe_files.items():
        if company_id not in (reg.get("companies") or {}):
            continue
        if not probe_path.exists():
            continue
        corpus = load_corpus_for_company(company_id)
        probes = _load_jsonl(probe_path)
        if company_id == "demo_company":
            probes = probes[:5]

        results = [run_probe(p, corpus, company_id=company_id).to_dict() for p in probes]
        matrix.extend(results)
        n = max(1, len(results))
        by_company[company_id] = {
            "probe_count": len(results),
            "parser_ok_rate": round(sum(1 for r in results if r["parser_ok"]) / n, 4),
            "retrieval_feasible_rate": round(sum(1 for r in results if r["retrieval_feasible"]) / n, 4),
            "extraction_feasible_rate": round(sum(1 for r in results if r["extraction_feasible"]) / n, 4),
            "aggregation_feasible_rate": round(sum(1 for r in results if r["aggregation_feasible"]) / n, 4),
            "readiness_distribution": dict(Counter(r["readiness_state"] for r in results)),
            "corpus_units": len(corpus),
            "role": company_config(company_id).get("role"),
        }

    family_view = summarize_holdout_by_family(matrix)
    return {"matrix": matrix, "by_company": by_company, "by_family": family_view}
