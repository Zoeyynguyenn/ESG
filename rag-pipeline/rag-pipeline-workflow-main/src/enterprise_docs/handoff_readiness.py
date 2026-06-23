"""Family handoff schema, readiness promotion, and handoff package evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.doc_router import build_evidence_plan
from enterprise_docs.family_generalization import bucket_for_probe
from enterprise_docs.confidence_policy import export_confidence_policy, resolve_extraction_confidence
from enterprise_docs.doc_mapping import build_logical_to_corpus_map
from enterprise_docs.holdout_harness import load_corpus_for_company, run_probe as feasibility_probe
from enterprise_docs.registries import is_holdout_company
from enterprise_docs.langgraph_handoff import build_handoff
from enterprise_docs.readiness_model import assess_readiness

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data/enterprise_docs/family_handoff_registry.json"

PROMOTION_BLOCKERS = frozenset({
    "coverage_gap",
    "needs_sme_review",
    "honest_abstain",
    "not_ready_for_synthesis",
    "unresolved_conflict",
    "wrong_row_risk",
    "qualitative_kind",
    "missing_predicted_value",
    "missing_predicted_unit",
    "evidence_bundle_insufficient",
    "confidence_below_min",
    "primary_doc_missing",
    "handoff_blocked_state",
})


@lru_cache(maxsize=1)
def load_family_handoff_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def export_family_handoff_schema() -> dict[str, Any]:
    reg = load_family_handoff_registry()
    return {
        "version": reg.get("version"),
        "description": reg.get("description"),
        "promotion_rules": reg.get("promotion_rules"),
        "families": reg.get("families"),
    }


def export_readiness_promotion_doc() -> dict[str, Any]:
    reg = load_family_handoff_registry()
    families_out: dict[str, Any] = {}
    for fid, spec in (reg.get("families") or {}).items():
        families_out[fid] = {
            "promotion_conditions": reg.get("promotion_rules"),
            "family_schema": spec,
            "blockers": list(spec.get("handoff_blockers") or []),
            "examples_promoted": [],
            "examples_not_promoted": [],
        }
    return {
        "version": reg.get("version"),
        "global_promotion_rules": reg.get("promotion_rules"),
        "families": families_out,
    }


def family_for_demo_plan(plan: dict[str, Any]) -> str | None:
    item = str(plan.get("item") or "")
    domain = str(plan.get("domain") or "")
    category = str(plan.get("category") or "")
    if item == "총 구성원 수":
        return "employee_headcount"
    if domain == "환경":
        return "environment_ghg"
    if domain == "거버넌스":
        return "governance"
    return None


def family_for_probe(probe: dict[str, Any]) -> str:
    bucket = bucket_for_probe(probe)
    if bucket in ("employee_headcount", "environment_ghg", "governance"):
        return bucket
    return bucket


def _family_schema(family_id: str) -> dict[str, Any]:
    reg = load_family_handoff_registry()
    return dict((reg.get("families") or {}).get(family_id) or {})


def _evidence_bundle_quality(handoff: dict[str, Any], *, min_count: int) -> str:
    bundle = handoff.get("evidence_bundle") or []
    val = handoff.get("predicted_value")
    conf = float(handoff.get("confidence") or 0.0)
    primary = handoff.get("primary_doc")
    suff = handoff.get("sufficiency_status") or (handoff.get("handoff_package") or {}).get("sufficiency_status")
    if not val or not str(val).strip():
        return "missing_value"
    if len(bundle) < min_count:
        return "insufficient_bundle"
    if suff == "resolved_single_source_sufficient" and bundle:
        return "strong" if conf >= 0.25 else "adequate"
    if primary and conf >= 0.85:
        return "strong"
    if conf >= 0.25 and bundle:
        return "adequate"
    return "weak"


def _min_confidence(schema: dict[str, Any], *, narrative: bool) -> float:
    rules = schema.get("confidence_rule") or {}
    if narrative:
        return float(rules.get("min_narrative_extraction") or 0.25)
    return float(rules.get("min_table_extraction") or 0.85)


def promote_readiness(
    *,
    before_state: str,
    handoff: dict[str, Any],
    readiness: dict[str, Any],
    family_id: str,
    extraction_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Promote extraction_ready → single_source_sufficient when package rules pass."""
    schema = _family_schema(family_id)
    kind = str(handoff.get("kind") or "")
    blockers: list[str] = []
    extraction_meta = extraction_meta or {}

    if kind != "quantitative":
        blockers.append("qualitative_kind")

    terminal_before = frozenset({
        "coverage_gap",
        "needs_sme_review",
        "honest_abstain",
        "not_ready_for_synthesis",
    })
    if before_state in terminal_before:
        blockers.append(f"handoff_blocked_state:{before_state}")

    if before_state in ("single_source_sufficient", "multi_source_sufficient"):
        return {
            "before_state": before_state,
            "after_state": before_state,
            "promoted": False,
            "promotion_target": None,
            "blockers": [],
            "already_sufficient": True,
        }

    if readiness.get("sufficiency_status") == "resolved_single_source_sufficient":
        return {
            "before_state": before_state,
            "after_state": "single_source_sufficient",
            "promoted": before_state != "single_source_sufficient",
            "promotion_target": "single_source_sufficient",
            "blockers": [],
            "promotion_reason": "aggregator_sufficiency",
        }

    if before_state == "multi_source_sufficient" or (
        readiness.get("aggregation_status") == "success"
        and readiness.get("sufficiency_status") == "resolved"
        and str(handoff.get("answer_mode") or "") == "cross_document_answer"
    ):
        return {
            "before_state": before_state,
            "after_state": "multi_source_sufficient",
            "promoted": before_state not in ("multi_source_sufficient",),
            "promotion_target": "multi_source_sufficient",
            "blockers": [],
            "promotion_reason": "multi_role_aggregation",
        }

    val = handoff.get("predicted_value")
    if not val or not str(val).strip():
        blockers.append("missing_predicted_value")

    bundle = handoff.get("evidence_bundle") or []
    min_count = int(schema.get("required_evidence_count") or 1)
    if len(bundle) < min_count:
        blockers.append("evidence_bundle_insufficient")

    primary = handoff.get("primary_doc")
    narrative_anchor = bool(bundle) and schema.get("narrative_single_source_ok")
    if not primary and not narrative_anchor:
        blockers.append("primary_doc_missing")
    elif not primary and narrative_anchor and bundle:
        handoff["primary_doc"] = bundle[0].get("logical_document_id") or bundle[0].get("unit_id")

    narrative = bool(extraction_meta.get("narrative_metric_parse_used"))
    min_conf = _min_confidence(schema, narrative=narrative)
    conf = float(handoff.get("confidence") or 0.0)
    if conf < min_conf:
        blockers.append("confidence_below_min")

    if extraction_meta.get("wrong_row_risk"):
        blockers.append("wrong_row_risk")

    schema_unit_required = bool(schema.get("unit_required"))
    if schema_unit_required and not handoff.get("predicted_unit"):
        blockers.append("missing_predicted_unit")

    blockers = list(dict.fromkeys(blockers))

    if blockers:
        return {
            "before_state": before_state,
            "after_state": before_state,
            "promoted": False,
            "promotion_target": "single_source_sufficient",
            "blockers": blockers,
        }

    if before_state in ("extraction_ready", "aggregation_ready", "retrieval_ready") and kind == "quantitative":
        has_value = bool(val and str(val).strip())
        ext_ok = bool(readiness.get("extraction_success")) or has_value
        if ext_ok and not blockers:
            return {
                "before_state": before_state,
                "after_state": "single_source_sufficient",
                "promoted": True,
                "promotion_target": "single_source_sufficient",
                "blockers": [],
                "promotion_reason": "family_package_rules_met",
            }

    return {
        "before_state": before_state,
        "after_state": before_state,
        "promoted": False,
        "promotion_target": "single_source_sufficient",
        "blockers": blockers or ["promotion_conditions_not_met"],
    }


def normalize_handoff_package(
    handoff: dict[str, Any],
    *,
    logical_map: dict[str, str],
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Ensure handoff package has primary_doc and bundle anchors for promotion."""
    out = dict(handoff)
    primary = out.get("primary_doc")
    bundle = list(out.get("evidence_bundle") or [])

    if not primary and bundle:
        out["primary_doc"] = bundle[0].get("logical_document_id") or bundle[0].get("unit_id")

    if primary and primary in logical_map.values():
        for item in bundle:
            if not item.get("logical_document_id"):
                item["logical_document_id"] = next(
                    (lid for lid, cid in logical_map.items() if cid == primary),
                    primary,
                )

    planned_primary = (plan.get("primary_document_ids") or [None])[0]
    if planned_primary and planned_primary in logical_map and not out.get("primary_doc"):
        out["primary_doc"] = planned_primary

    out["evidence_bundle"] = bundle
    out["supporting_docs"] = list(out.get("supporting_docs") or [])
    return out


def audit_holdout_routing_alignment() -> dict[str, Any]:
    """Compare feasibility harness vs full pipeline readiness on holdout probes."""
    mismatches: list[dict[str, Any]] = []

    probe_files = {
        "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
        "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
    }

    for company_id, path in probe_files.items():
        if not path.exists():
            continue
        corpus = load_corpus_for_company(company_id)
        corpus_ids = sorted({str(u.get("document_id") or "") for u in corpus})
        logical_map = build_logical_to_corpus_map(corpus_ids, company_id=company_id)

        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                probe = json.loads(line)
                feas = feasibility_probe(probe, corpus, company_id=company_id).to_dict()
                row = run_case_handoff(probe, company_id=company_id, corpus_units=corpus)

                feas_ext = bool(feas.get("extraction_feasible"))
                full_state = str(row.get("readiness_state_before") or "")
                gap = feas_ext and full_state in ("coverage_gap", "retrieval_ready")

                mismatches.append(
                    {
                        "probe_id": probe.get("probe_id"),
                        "company_id": company_id,
                        "family_id": row.get("family_id"),
                        "feasibility_extraction": feas_ext,
                        "feasibility_readiness": feas.get("readiness_state"),
                        "full_pipeline_before": full_state,
                        "full_pipeline_after": row.get("readiness_state_after"),
                        "logical_map": logical_map,
                        "alignment_gap": gap,
                        "promoted": row.get("promoted"),
                        "handoff_candidate": row.get("handoff_candidate"),
                    }
                )

    gap_count = sum(1 for m in mismatches if m.get("alignment_gap"))
    return {
        "mismatches_found": [
            {
                "category": "path_hint_vs_corpus_document_id",
                "description": "Holdout logical path_hint did not match corpus IDs (Company_Evidence_*)",
                "status": "fixed",
                "fix": "corpus_match_tokens in company_doc_registry v1.3.0",
            },
            {
                "category": "multi_primary_cross_doc_on_holdout",
                "description": "Multi-domain routing triggered cross_document_answer on narrative SR corpus",
                "status": "fixed",
                "fix": "holdout_routing.force_single_doc_quant + max_primary_docs=1",
            },
            {
                "category": "supporting_doc_unmapped_coverage_gap",
                "description": "Unmapped supporting logical docs forced coverage_gap",
                "status": "fixed",
                "fix": "diagnostics require_primary_logical_map_only for holdout",
            },
            {
                "category": "build_index_company_id_not_passed_to_logical_map",
                "description": "build_index_from_units used demo_company for logical_to_corpus_map on all holdout runs",
                "status": "fixed",
                "fix": "cross_doc_retriever.build_logical_to_corpus_map(..., company_id=company_id)",
            },
        ],
        "still_open": (
            ["feasibility_vs_full_pipeline_readiness_gap"] if gap_count else []
        ),
        "probe_alignment": mismatches,
        "alignment_gap_count": gap_count,
        "alignment_gap_rate": round(gap_count / max(1, len(mismatches)), 4),
    }


def run_case_handoff(
    plan: dict[str, Any],
    *,
    company_id: str,
    corpus_units: list[dict[str, Any]],
    family_id: str | None = None,
) -> dict[str, Any]:
    """Full pipeline: route → retrieve → readiness → handoff → promote."""
    plan = dict(plan)
    plan.setdefault("company_id", company_id)

    if "answer_mode" not in plan:
        ev = build_evidence_plan(plan, company_id=company_id)
        plan.update(asdict(ev))

    lookup = {str(u["unit_id"]): u for u in corpus_units}
    index, logical_map = build_index_from_units(corpus_units, company_id=company_id)
    ret = retrieve_for_plan(plan, index, logical_map)
    readiness = assess_readiness(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
    handoff_obj = build_handoff(
        plan, ret, company_id=company_id, unit_lookup=lookup, logical_to_corpus=logical_map
    )
    handoff = handoff_obj.to_dict()
    handoff = normalize_handoff_package(handoff, logical_map=logical_map, plan=plan)
    handoff["sufficiency_status"] = handoff.get("sufficiency_status") or readiness.get("sufficiency_status")

    fid = family_id or family_for_demo_plan(plan) or family_for_probe(plan)
    before = str(readiness.get("readiness_state") or "unknown")

    from enterprise_docs.structured_extractor import extract_from_retrieval

    ext = extract_from_retrieval(
        plan, ret, unit_lookup=lookup, retrieval_ready=bool(readiness.get("retrieval_ok"))
    )
    conf, confidence_source = resolve_extraction_confidence(
        ext, company_id=company_id, family_id=fid, unit_lookup=lookup
    )
    handoff["confidence"] = conf
    handoff["confidence_source"] = confidence_source
    ext_meta = {
        "narrative_metric_parse_used": bool(getattr(ext, "narrative_metric_parse_used", False)),
        "wrong_row_risk": bool(getattr(ext, "wrong_row_risk", False)),
    }

    promo = promote_readiness(
        before_state=before,
        handoff=handoff,
        readiness=readiness,
        family_id=fid or "unknown",
        extraction_meta=ext_meta,
    )
    after = str(promo.get("after_state") or before)
    schema = _family_schema(fid) if fid else {}
    min_count = int(schema.get("required_evidence_count") or 1)
    quality = _evidence_bundle_quality(handoff, min_count=min_count)

    review_rule = schema.get("review_owner_rule") or {}
    needs_review = review_rule.get(after) or review_rule.get(before) or review_rule.get("default")

    from enterprise_docs.langgraph_handoff import handoff_allowed_for_state

    kind = str(plan.get("kind") or "")
    allowed_after, _ = handoff_allowed_for_state(after, kind=kind)
    handoff_candidate = (
        after in ("single_source_sufficient", "multi_source_sufficient")
        and allowed_after
        and kind == "quantitative"
        and quality in ("adequate", "strong")
        and not (promo.get("blockers") or [])
    )

    return {
        "question_id": plan.get("item_id") or plan.get("probe_id"),
        "probe_id": plan.get("probe_id") or plan.get("item_id"),
        "company_id": company_id,
        "family_id": fid,
        "kind": plan.get("kind"),
        "readiness_state_before": before,
        "readiness_state_after": after,
        "promoted": bool(promo.get("promoted")),
        "promotion": promo,
        "handoff_candidate": handoff_candidate,
        "handoff_blockers": promo.get("blockers") or [],
        "evidence_bundle_quality": quality,
        "primary_doc": handoff.get("primary_doc"),
        "supporting_docs": handoff.get("supporting_docs") or [],
        "predicted_value": handoff.get("predicted_value"),
        "predicted_unit": handoff.get("predicted_unit"),
        "confidence": handoff.get("confidence"),
        "confidence_source": handoff.get("confidence_source"),
        "answer_mode": plan.get("answer_mode"),
        "needs_review_by": needs_review,
        "handoff_allowed": handoff.get("handoff_allowed"),
        "handoff_package": {
            "schema_version": handoff.get("schema_version"),
            "evidence_bundle": handoff.get("evidence_bundle") or [],
            "evidence_bundle_count": len(handoff.get("evidence_bundle") or []),
            "sufficiency_status": handoff.get("sufficiency_status"),
        },
    }


def kind_allowed(handoff: dict[str, Any]) -> bool:
    return str(handoff.get("kind") or "") == "quantitative"


def run_handoff_readiness_matrix(
    *,
    include_demo: bool = True,
    demo_family_filter: bool = True,
) -> dict[str, Any]:
    """Run handoff readiness on holdout probes + optional demo dev quant plans."""
    import json as _json
    from pathlib import Path as _Path

    matrix: list[dict[str, Any]] = []
    promotion_doc = export_readiness_promotion_doc()

    probe_files = {
        "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
        "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
    }

    for company_id, path in probe_files.items():
        if not path.exists():
            continue
        corpus = load_corpus_for_company(company_id)
        probes: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    probes.append(_json.loads(line))
        for probe in probes:
            fid = family_for_probe(probe)
            row = run_case_handoff(probe, company_id=company_id, corpus_units=corpus, family_id=fid)
            matrix.append(row)
            fam_doc = promotion_doc["families"].setdefault(fid, {})
            ex_key = "examples_promoted" if row["promoted"] else "examples_not_promoted"
            fam_doc.setdefault(ex_key, []).append(
                {"probe_id": row["probe_id"], "after": row["readiness_state_after"], "blockers": row["handoff_blockers"]}
            )

    if include_demo:
        demo_corpus = load_corpus_for_company("demo_company")
        single = ROOT / "data/enterprise_docs/demo_company/eval_subset_single.jsonl"
        cross = ROOT / "data/enterprise_docs/demo_company/eval_subset_cross.jsonl"
        plans: list[dict[str, Any]] = []
        for p in (single, cross):
            if p.exists():
                with p.open(encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            plans.append(_json.loads(line))
        for plan in plans:
            if plan.get("kind") != "quantitative":
                continue
            fid = family_for_demo_plan(plan)
            if demo_family_filter and fid not in ("employee_headcount", "environment_ghg", "governance"):
                continue
            if not fid:
                continue
            row = run_case_handoff(
                plan, company_id="demo_company", corpus_units=demo_corpus, family_id=fid
            )
            matrix.append(row)
            fam_doc = promotion_doc["families"].setdefault(fid, {})
            ex_key = "examples_promoted" if row["promoted"] else "examples_not_promoted"
            fam_doc.setdefault(ex_key, []).append(
                {"question_id": row["question_id"], "after": row["readiness_state_after"], "blockers": row["handoff_blockers"]}
            )

    return summarize_handoff_matrix(matrix, promotion_doc=promotion_doc)


def summarize_handoff_matrix(
    matrix: list[dict[str, Any]],
    *,
    promotion_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from collections import Counter, defaultdict

    promotion_doc = promotion_doc or export_readiness_promotion_doc()
    by_company: dict[str, Any] = {}
    by_family: dict[str, Any] = {}
    by_promotion: Counter[str] = Counter()

    for company_id in sorted({r["company_id"] for r in matrix}):
        rows = [r for r in matrix if r["company_id"] == company_id]
        n = max(1, len(rows))
        by_company[company_id] = {
            "case_count": len(rows),
            "promoted_count": sum(1 for r in rows if r.get("promoted")),
            "handoff_candidate_count": sum(1 for r in rows if r.get("handoff_candidate")),
            "readiness_before": dict(Counter(r.get("readiness_state_before") for r in rows)),
            "readiness_after": dict(Counter(r.get("readiness_state_after") for r in rows)),
            "promotion_rate": round(sum(1 for r in rows if r.get("promoted")) / n, 4),
        }

    for fid in sorted({r.get("family_id") for r in matrix if r.get("family_id")}):
        rows = [r for r in matrix if r.get("family_id") == fid]
        n = max(1, len(rows))
        quant = [r for r in rows if r.get("kind") == "quantitative"]
        by_family[fid] = {
            "case_count": len(rows),
            "quantitative_count": len(quant),
            "promoted_count": sum(1 for r in rows if r.get("promoted")),
            "single_source_count": sum(
                1 for r in rows if r.get("readiness_state_after") == "single_source_sufficient"
            ),
            "multi_source_count": sum(
                1 for r in rows if r.get("readiness_state_after") == "multi_source_sufficient"
            ),
            "handoff_candidate_count": sum(1 for r in rows if r.get("handoff_candidate")),
            "still_extraction_ready": sum(
                1 for r in rows if r.get("readiness_state_after") == "extraction_ready"
            ),
            "not_handoff_ready": sum(1 for r in rows if not r.get("handoff_candidate")),
            "promotion_rate": round(sum(1 for r in rows if r.get("promoted")) / n, 4),
            "blocker_breakdown": dict(
                Counter(b for r in rows for b in (r.get("handoff_blockers") or []))
            ),
            "companies": sorted({r["company_id"] for r in rows}),
        }

    for r in matrix:
        key = "promoted" if r.get("promoted") else "not_promoted"
        by_promotion[key] += 1

    return {
        "matrix": matrix,
        "by_company": by_company,
        "by_family": by_family,
        "by_promotion": dict(by_promotion),
        "readiness_promotion": promotion_doc,
        "family_handoff_schema": export_family_handoff_schema(),
    }
