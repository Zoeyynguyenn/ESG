"""Map pipeline outputs to structured ESG records."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from enterprise_docs.confidence_policy import resolve_extraction_confidence
from enterprise_docs.conflict_classifier import classify_conflict_status
from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.diagnostics import NOT_DISCLOSED_RE
from enterprise_docs.evidence_aggregator import aggregate_cross_doc
from enterprise_docs.esg_field_normalizer import normalize_structured_record
from enterprise_docs.handoff_readiness import family_for_demo_plan, family_for_probe
from enterprise_docs.holdout_harness import load_corpus_for_company
from enterprise_docs.readiness_model import assess_readiness
from enterprise_docs.review_owner_policy import resolve_review_owner
from enterprise_docs.structured_extractor import extract_from_retrieval

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "data/enterprise_docs/esg_target_schema.json"


@lru_cache(maxsize=1)
def load_esg_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def export_esg_schema() -> dict[str, Any]:
    return load_esg_schema()


def _infer_value_type(value: str | None) -> str:
    if not value or not str(value).strip():
        return "unknown"
    if NOT_DISCLOSED_RE.search(str(value)):
        return "not_disclosed"
    v = str(value).strip()
    if re.match(r"^-?\d[\d,.]*$", v.replace(",", "")):
        return "numeric"
    if v.lower() in ("true", "false", "yes", "no"):
        return "boolean"
    return "text"


def _family_esg_map(family_id: str | None) -> dict[str, str]:
    schema = load_esg_schema()
    return dict((schema.get("family_esg_mapping") or {}).get(family_id or "") or {
        "esg_domain": "General",
        "category": "Unmapped",
        "subcategory": "",
    })


def _evidence_ref(unit_id: str, doc_id: str, snippet: str, *, role: str | None = None) -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "document_id": doc_id,
        "snippet": (snippet or "")[:300],
        "role": role,
    }


def build_structured_esg_record(
    plan: dict[str, Any],
    *,
    company_id: str,
    corpus_units: list[dict[str, Any]],
    family_id: str | None = None,
) -> dict[str, Any]:
    """Full pipeline → one structured ESG record."""
    plan = dict(plan)
    plan.setdefault("company_id", company_id)
    fid = family_id or family_for_demo_plan(plan) or family_for_probe(plan)
    esg_map = _family_esg_map(fid)
    pool_units = corpus_units
    if plan.get("_retrieval_mode") in ("family_scoped", "overlap_strengthened") and fid:
        from enterprise_docs.family_retrieval_pool import units_for_family_pool

        pool_units = units_for_family_pool(corpus_units, fid, company_id)
    lookup = {str(u["unit_id"]): u for u in pool_units}
    index, logical_map = build_index_from_units(pool_units, company_id=company_id)
    ret = retrieve_for_plan(plan, index, logical_map)
    readiness = assess_readiness(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
    ext = extract_from_retrieval(
        plan, ret, unit_lookup=lookup, retrieval_ready=bool(readiness.get("retrieval_ok"))
    )
    conf, conf_src = resolve_extraction_confidence(
        ext, company_id=company_id, family_id=fid, unit_lookup=lookup
    )

    agg = None
    roles = plan.get("roles") or {}
    multi_role = len(roles) >= 2 or len(plan.get("primary_document_ids") or []) >= 2
    if plan.get("answer_mode") == "cross_document_answer" or multi_role:
        agg = aggregate_cross_doc(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)

    value = ext.predicted_value if ext.success else None
    unit = ext.predicted_unit
    primary_doc = ext.selected_doc
    supporting: list[dict[str, Any]] = []
    source_docs: list[str] = []
    source_format = None

    if agg is not None:
        value = agg.resolved_value or agg.predicted_value or value
        unit = agg.predicted_unit or unit
        primary_doc = agg.primary_doc_used or primary_doc
        for c in agg.aggregated_evidence_units or []:
            ref = _evidence_ref(c.unit_id, c.logical_document_id, c.source_snippet, role=c.role)
            if c.logical_document_id and c.logical_document_id != primary_doc:
                supporting.append(ref)
            if c.logical_document_id and c.logical_document_id not in source_docs:
                source_docs.append(c.logical_document_id)
        suff = agg.sufficiency_status
        conflict_flags = agg.conflict_flags
        roles_with = agg.roles_with_metric
        multi_confirmed = agg.multi_source_confirmed
        confirming_docs = agg.confirming_logical_docs
        for c in agg.aggregated_evidence_units or []:
            uid = c.unit_id
            u = lookup.get(uid, {})
            st = str(u.get("source_type") or "")
            if st and st not in (source_format or ""):
                source_format = st if not source_format else source_format
    else:
        suff = readiness.get("sufficiency_status")
        conflict_flags = []
        roles_with = [primary_doc] if primary_doc else []
        multi_confirmed = False
        confirming_docs = []
        if ext.success and ext.selected_unit_ids:
            uid = ext.selected_unit_ids[0]
            u = lookup.get(uid, {})
            source_format = str(u.get("source_type") or "")
            if u.get("document_id") and str(u["document_id"]) not in source_docs:
                source_docs.append(str(u["document_id"]))

    conflict_status, conflict_reason = classify_conflict_status(
        aggregation=agg,
        sufficiency_status=suff,
        conflict_flags=conflict_flags,
        roles_with_metric=roles_with,
        resolved_value=value,
        answer_mode=str(plan.get("answer_mode") or "single_document_answer"),
        multi_source_confirmed=multi_confirmed,
        confirming_logical_docs=confirming_docs,
    )

    state = str(readiness.get("readiness_state") or "unknown")
    if multi_confirmed:
        state = "multi_source_sufficient"
    elif suff == "resolved_single_source_sufficient":
        state = "single_source_sufficient"

    narrative = bool(getattr(ext, "narrative_metric_parse_used", False))
    fam_min = 0.25 if narrative else 0.85
    owner_res = resolve_review_owner(
        readiness_state=state,
        kind=str(plan.get("kind") or "quantitative"),
        promoted=state in ("single_source_sufficient", "multi_source_sufficient"),
        confidence=conf,
        family_min_confidence=fam_min,
        wrong_row_risk=bool(getattr(ext, "wrong_row_risk", False)),
        family_id=fid,
    )

    primary_evidence = None
    if ext.success and ext.selected_unit_ids:
        uid = ext.selected_unit_ids[0]
        u = lookup.get(uid, {})
        primary_evidence = _evidence_ref(
            uid,
            primary_doc or str(u.get("document_id") or ""),
            ext.raw_snippet or "",
        )

    metric_name = str(plan.get("item") or plan.get("metric") or plan.get("probe_id") or "")

    record = {
        "schema_version": load_esg_schema().get("version"),
        "company_id": company_id,
        "question_id": plan.get("item_id") or plan.get("probe_id"),
        "field_id": f"{fid}::{metric_name}" if fid else metric_name,
        "plan_domain": plan.get("domain"),
        "plan_category": plan.get("category"),
        "plan_subcategory": plan.get("subcategory"),
        "esg_domain": esg_map.get("esg_domain"),
        "category": esg_map.get("category"),
        "subcategory": esg_map.get("subcategory"),
        "metric_name": metric_name,
        "year": getattr(ext, "selected_year", None) or (agg.aggregated_evidence_units[0].year if agg and agg.aggregated_evidence_units else None),
        "value": value,
        "unit": unit,
        "value_type": _infer_value_type(value),
        "confidence": conf,
        "confidence_source": conf_src,
        "primary_evidence": primary_evidence,
        "supporting_evidence": supporting,
        "source_documents": source_docs,
        "source_format": source_format,
        "readiness_state": state,
        "conflict_status": conflict_status,
        "conflict_reason": conflict_reason,
        "review_owner": owner_res.get("needs_review_by"),
        "family_id": fid,
        "answer_mode": plan.get("answer_mode"),
        "extraction_success": bool(ext.success),
        "aggregation_status": getattr(agg, "aggregation_status", None) if agg else None,
        "sufficiency_status": suff,
        "multi_source_confirmed": multi_confirmed,
        "confirming_logical_docs": confirming_docs,
    }
    return normalize_structured_record(record, schema=load_esg_schema())


def run_structured_esg_pipeline(
    *,
    include_demo: bool = True,
    holdout_corpus: str = "baseline",
    enrich_holdout_plans: bool = True,
) -> dict[str, Any]:
    """Build structured ESG records for demo + holdout probes.

    holdout_corpus: ``baseline`` | ``reingested`` | ``filtered`` | ``family_scoped`` | ``overlap_strengthened``
    enrich_holdout_plans: apply registry evidence plan (incl. controlled cross-doc probes)
    """
    from enterprise_docs.probe_plan import enrich_holdout_probe

    records: list[dict[str, Any]] = []

    probe_files = {
        "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
        "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
    }
    for company_id, path in probe_files.items():
        if not path.exists():
            continue
        corpus = load_corpus_for_company(company_id, holdout_corpus=holdout_corpus)
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    probe = json.loads(line)
                    if enrich_holdout_plans:
                        probe = enrich_holdout_probe(probe, company_id=company_id)
                    if holdout_corpus in ("family_scoped", "overlap_strengthened"):
                        probe["_retrieval_mode"] = holdout_corpus
                    fid = family_for_probe(probe)
                    if fid not in ("employee_headcount", "environment_ghg", "governance"):
                        continue
                    records.append(
                        build_structured_esg_record(
                            probe, company_id=company_id, corpus_units=corpus, family_id=fid
                        )
                    )

    if include_demo:
        corpus = load_corpus_for_company("demo_company")
        for rel in (
            "data/enterprise_docs/demo_company/eval_subset_single.jsonl",
            "data/enterprise_docs/demo_company/eval_subset_cross.jsonl",
        ):
            p = ROOT / rel
            if not p.exists():
                continue
            with p.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    plan = json.loads(line)
                    if plan.get("kind") != "quantitative":
                        continue
                    fid = family_for_demo_plan(plan)
                    if fid not in ("employee_headcount", "environment_ghg", "governance"):
                        continue
                    records.append(
                        build_structured_esg_record(
                            plan, company_id="demo_company", corpus_units=corpus, family_id=fid
                        )
                    )

    use_reingested = holdout_corpus in ("reingested", "filtered", "family_scoped", "overlap_strengthened")
    phase = "structured_esg_hardening"
    if holdout_corpus == "overlap_strengthened":
        phase = "overlap_strengthening"
    elif holdout_corpus == "family_scoped":
        phase = "family_scoped_retrieval_pool"
    elif holdout_corpus == "filtered":
        phase = "structured_esg_retrieval_scope_narrowing"
    elif use_reingested:
        phase = "structured_esg_reingest"
    out = summarize_structured_esg(records)
    out["system_focus"] = {
        "phase": phase,
        "holdout_corpus": holdout_corpus,
        "enrich_holdout_plans": enrich_holdout_plans,
        "langgraph_handoff_priority": False,
        "primary_goals": [
            "multi_format_transformation",
            "esg_schema_mapping",
            "cross_document_conflict_handling",
        ],
    }
    return out


def summarize_structured_esg(records: list[dict[str, Any]]) -> dict[str, Any]:
    from collections import Counter

    def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n = max(1, len(rows))
        mapped = [r for r in rows if r.get("esg_domain") != "General"]
        with_value = [r for r in rows if r.get("value") and r.get("value_type") not in ("unknown",)]
        return {
            "case_count": len(rows),
            "structured_record_coverage": round(len(with_value) / n, 4),
            "esg_field_mapping_rate": round(len(mapped) / n, 4),
            "single_source_sufficient_rate": round(
                sum(1 for r in rows if r.get("conflict_status") == "single_source_sufficient") / n, 4
            ),
            "multi_source_confirmed_rate": round(
                sum(1 for r in rows if r.get("conflict_status") == "multi_source_confirmed") / n, 4
            ),
            "conflict_rate": round(
                sum(1 for r in rows if r.get("conflict_status") in ("conflict_numeric", "conflict_semantic")) / n,
                4,
            ),
            "not_disclosed_detection_rate": round(
                sum(1 for r in rows if r.get("value_type") == "not_disclosed" or r.get("conflict_status") == "not_disclosed") / n,
                4,
            ),
            "review_required_rate": round(
                sum(1 for r in rows if r.get("review_owner") in ("RAG", "SME", "Dataset")) / n, 4
            ),
            "metric_absent_rate": round(
                sum(1 for r in rows if r.get("conflict_status") == "metric_absent") / n, 4
            ),
            "insufficient_cross_doc_support_rate": round(
                sum(1 for r in rows if r.get("conflict_status") == "insufficient_cross_doc_support") / n, 4
            ),
            "conflict_status_distribution": dict(Counter(r.get("conflict_status") for r in rows)),
            "readiness_distribution": dict(Counter(r.get("readiness_state") for r in rows)),
            "family_distribution": dict(Counter(r.get("family_id") for r in rows)),
        }

    by_company: dict[str, Any] = {}
    by_family: dict[str, Any] = {}
    by_format: dict[str, Any] = {}

    for cid in sorted({r["company_id"] for r in records}):
        rows = [r for r in records if r["company_id"] == cid]
        by_company[cid] = _metrics(rows)

    for fid in sorted({r.get("family_id") for r in records if r.get("family_id")}):
        rows = [r for r in records if r.get("family_id") == fid]
        by_family[fid] = _metrics(rows)

    fmt_rows: dict[str, list] = {}
    for r in records:
        fmt = r.get("source_format") or "narrative_holdout"
        fmt_rows.setdefault(fmt, []).append(r)
    for fmt, rows in fmt_rows.items():
        by_format[fmt] = _metrics(rows)

    # Cross-doc conflict matrix
    cross = [r for r in records if r.get("answer_mode") == "cross_document_answer"]
    conflict_matrix = []
    confirmation_matrix = []
    for r in cross:
        conflict_matrix.append({
            "question_id": r.get("question_id"),
            "company_id": r.get("company_id"),
            "family_id": r.get("family_id"),
            "conflict_status": r.get("conflict_status"),
            "conflict_reason": r.get("conflict_reason"),
            "value": r.get("value"),
            "readiness_state": r.get("readiness_state"),
            "source_documents": r.get("source_documents"),
        })
        confirmation_matrix.append({
            "question_id": r.get("question_id"),
            "company_id": r.get("company_id"),
            "multi_source_confirmed": r.get("multi_source_confirmed"),
            "confirming_logical_docs": r.get("confirming_logical_docs"),
            "conflict_status": r.get("conflict_status"),
            "value": r.get("value"),
        })

    format_audit = None
    try:
        from enterprise_docs.format_transformation_audit import audit_format_transformation
        format_audit = audit_format_transformation()
        parse_cov = sum(
            1 for f in (format_audit.get("by_format") or {}).values()
            if f.get("document_count", 0) > 0 and f.get("parser_status") == "implemented"
        )
        total_fmts = sum(1 for f in (format_audit.get("by_format") or {}).values() if f.get("document_count", 0) > 0)
        format_parse_coverage = round(parse_cov / max(1, total_fmts), 4)
    except Exception:  # noqa: BLE001
        format_parse_coverage = None

    return {
        "records": records,
        "by_company": by_company,
        "by_family": by_family,
        "by_format": by_format,
        "cross_doc_conflict_matrix": conflict_matrix,
        "cross_doc_confirmation_matrix": confirmation_matrix,
        "format_parse_coverage": format_parse_coverage,
        "esg_schema": export_esg_schema(),
        "conflict_taxonomy": __import__(
            "enterprise_docs.conflict_classifier", fromlist=["export_conflict_taxonomy"]
        ).export_conflict_taxonomy(),
        "system_focus": {
            "phase": "structured_esg_hardening",
            "langgraph_handoff_priority": False,
            "primary_goals": [
                "multi_format_transformation",
                "esg_schema_mapping",
                "cross_document_conflict_handling",
            ],
        },
        "metric_types": {
            "exact": ["case_count", "conflict_status per record", "value when extracted"],
            "heuristic": [
                "structured_record_coverage",
                "esg_field_mapping_rate",
                "format_parse_coverage",
            ],
            "proxy": ["confidence", "review_required_rate without SME validation"],
        },
    }
