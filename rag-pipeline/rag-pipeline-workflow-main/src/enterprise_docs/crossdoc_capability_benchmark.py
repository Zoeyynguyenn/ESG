"""Cross-document core capability benchmark — natural vs constructed split."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from enterprise_docs.conflict_classifier import classify_conflict_status
from enterprise_docs.crossdoc_case_builder import (
    CASES_PATH,
    _family_for_probe,
    all_capability_cases,
    case_to_plan,
    synthetic_corpus_from_case,
)
from enterprise_docs.cross_doc_retriever import RetrievalResult, UnitHit
from enterprise_docs.evidence_aggregator import aggregate_cross_doc
from enterprise_docs.family_retrieval_pool import units_for_family_pool
from enterprise_docs.handoff_readiness import family_for_probe, promote_readiness
from enterprise_docs.holdout_harness import load_corpus_for_company
from enterprise_docs.cross_role_extraction import probe_candidates_cross_role
from enterprise_docs.overlap_strengthening import canonical_metric_value, measure_probe_overlap_enhanced, values_equivalent
from enterprise_docs.structured_extractor import probe_candidates_in_units

ROOT = Path(__file__).resolve().parents[2]
PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_overlap_strengthening_20260619-095735/summary.json"

CAPABILITY_METRICS = (
    "alias_normalization_success_rate",
    "cross_doc_equivalence_match_rate",
    "cross_role_extraction_alignment_rate",
    "evidence_fusion_success_rate",
    "conflict_classification_accuracy",
    "conflict_resolution_readiness_rate",
    "single_source_to_multi_source_promotion_rate",
)

PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


def _rate(success: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(success / total, 4)


def _evaluate_value_pair_case(case: dict[str, Any]) -> dict[str, Any]:
    fid = str(case.get("family_id") or "")
    item = str(case.get("item") or "")
    pairs = case.get("value_pairs") or []
    expect_equiv = bool(case.get("expected_all_equivalent"))
    results = []
    ok = 0
    for pair in pairs:
        if len(pair) < 2:
            continue
        a, b = str(pair[0]), str(pair[1])
        eq = values_equivalent(a, b, item=item, family_id=fid)
        match = eq == expect_equiv
        if match:
            ok += 1
        results.append({"a": a, "b": b, "equivalent": eq, "expected_match": match})
    total = max(1, len(results))
    return {
        "case_id": case.get("case_id"),
        "case_origin": case.get("case_origin"),
        "capability": case.get("capability"),
        "capability_tags": case.get("capability_tags") or [],
        "passed": ok == len(results) if results else False,
        "alias_normalization_ok": ok == len(results) if results else None,
        "pair_results": results,
        "score": _rate(ok, len(results) if results else 0),
    }


def _evaluate_canonical_case(case: dict[str, Any]) -> dict[str, Any]:
    fid = str(case.get("family_id") or "")
    item = str(case.get("item") or "")
    values = [str(v) for v in (case.get("values") or [])]
    keys = [canonical_metric_value(v, item=item, family_id=fid) for v in values]
    unique = len(set(k for k in keys if k))
    expect_same = bool(case.get("expected_same_canonical"))
    same = unique <= 1 if values else False
    passed = same == expect_same
    return {
        "case_id": case.get("case_id"),
        "case_origin": case.get("case_origin"),
        "capability": "cross_doc_equivalence",
        "capability_tags": case.get("capability_tags") or [],
        "passed": passed,
        "canonical_keys": keys,
        "expected_same_canonical": expect_same,
        "score": 1.0 if passed else 0.0,
    }


def _retrieval_from_case(case: dict[str, Any]) -> tuple[dict[str, Any], RetrievalResult, dict[str, str]]:
    plan = case_to_plan(case)
    units, logical_map = synthetic_corpus_from_case(case)
    lookup = {str(u["unit_id"]): u for u in units}
    hits: list[UnitHit] = []
    for u in units:
        lid = str((u.get("metadata") or {}).get("logical_doc") or "")
        hits.append(
            UnitHit(
                unit_id=str(u["unit_id"]),
                corpus_document_id=str(u["document_id"]),
                logical_document_id=lid,
                score=1.0,
                evidence_text=str(u.get("evidence_text") or u.get("text") or ""),
            )
        )
    ret = RetrievalResult(
        item_id=str(plan.get("item_id") or ""),
        answer_mode=str(plan.get("answer_mode") or "cross_document_answer"),
        question=str(plan.get("question") or ""),
        top_units=hits,
        role_hits={lid: True for lid in logical_map},
        role_coverage=1.0,
    )
    return plan, ret, logical_map


def _has_alignable_candidate(candidates: list[Any]) -> bool:
    for c in candidates:
        val = str(getattr(c, "value", None) or "")
        val_l = val.strip().lower()
        if val_l in ("not disclosed", "n/a", "-"):
            continue
        if val_l in ("scope_3", "present") or re.search(r"\d", val) or re.fullmatch(r"[A-Z][+]?", val, re.I):
            return True
    return False


def _evaluate_multi_source_case(case: dict[str, Any]) -> dict[str, Any]:
    plan, ret, logical_map = _retrieval_from_case(case)
    units, _ = synthetic_corpus_from_case(case)
    lookup = {str(u["unit_id"]): u for u in units}
    fid = str(case.get("family_id") or "")
    item = str(case.get("item") or "")

    extract_per_doc: dict[str, bool] = {}
    expected_extract = dict(case.get("expected_extract_per_doc") or {})
    for lid, expected in expected_extract.items():
        src_units = [
            u
            for u in (case.get("source_units") or [])
            if str(u.get("logical_doc") or "") == lid
        ]
        if not src_units:
            extract_per_doc[lid] = False
            continue
        doc_units = [u for u in units if str(u.get("document_id")) == str(src_units[0].get("document_id"))]
        cands = probe_candidates_cross_role(plan, doc_units, logical_doc=lid, min_score=0.15)
        extract_per_doc[lid] = _has_alignable_candidate(cands)

    agg = aggregate_cross_doc(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
    from enterprise_docs.fusion_equivalence import (
        equivalence_collapse_success,
        fusion_success,
        promotion_integrity_ok,
    )

    collapse = equivalence_collapse_success(
        agg.aggregated_evidence_units,
        item=item,
        family_id=fid or None,
    )
    equivalence_collapse_ok = bool(collapse.get("collapse_ok"))
    status, reason = classify_conflict_status(
        aggregation=agg,
        sufficiency_status=agg.sufficiency_status,
        conflict_flags=agg.conflict_flags,
        roles_with_metric=agg.roles_with_metric,
        resolved_value=agg.resolved_value,
        answer_mode=str(plan.get("answer_mode") or ""),
        multi_source_confirmed=agg.multi_source_confirmed,
        confirming_logical_docs=agg.confirming_logical_docs,
    )

    expected_extract = dict(case.get("expected_extract_per_doc") or {})
    extract_ok = all(extract_per_doc.get(k) == v for k, v in expected_extract.items()) if expected_extract else True
    expect_multi = case.get("expected_multi_source_confirmed")
    multi_ok = expect_multi is None or bool(agg.multi_source_confirmed) == bool(expect_multi)
    fusion_ok = fusion_success(
        multi_source_confirmed=bool(agg.multi_source_confirmed),
        confirming_docs=list(agg.confirming_logical_docs or []),
        expected_multi=expect_multi if expect_multi is not None else None,
        equivalence_collapse=collapse,
    )
    expect_status = case.get("expected_conflict_status")
    status_ok = expect_status is None or status == expect_status

    promotion = promote_readiness(
        before_state="extraction_ready",
        handoff={
            "kind": plan.get("kind"),
            "predicted_value": agg.resolved_value,
            "answer_mode": plan.get("answer_mode"),
            "evidence_bundle": [{"logical_document_id": d} for d in agg.confirming_logical_docs],
            "confidence": 0.9,
            "primary_doc": agg.primary_doc_used,
        },
        readiness={
            "sufficiency_status": agg.sufficiency_status,
            "aggregation_status": agg.aggregation_status,
        },
        family_id=fid,
    )

    expect_promo_multi = case.get("expected_multi_source_confirmed")
    promo_ok = promotion_integrity_ok(
        fusion_ok=fusion_ok,
        promotion=promotion,
        expected_multi=expect_promo_multi,
    )

    passed = extract_ok and fusion_ok and status_ok

    return {
        "case_id": case.get("case_id"),
        "case_origin": case.get("case_origin"),
        "capability": case.get("capability"),
        "capability_tags": case.get("capability_tags") or [],
        "family_id": fid,
        "item": item,
        "passed": passed,
        "extract_per_doc": extract_per_doc,
        "extract_alignment_ok": extract_ok,
        "equivalence_collapse": collapse,
        "equivalence_collapse_ok": equivalence_collapse_ok,
        "aggregation": {
            "resolved_value": agg.resolved_value,
            "multi_source_confirmed": agg.multi_source_confirmed,
            "confirming_logical_docs": agg.confirming_logical_docs,
            "conflict_flags": agg.conflict_flags,
            "sufficiency_status": agg.sufficiency_status,
        },
        "conflict_status": status,
        "conflict_reason": reason,
        "classification_ok": status_ok,
        "fusion_ok": fusion_ok,
        "resolution_status": agg.resolution_status,
        "promotion": promotion,
        "promotion_ok": promo_ok,
    }


def _evaluate_natural_case(case: dict[str, Any]) -> dict[str, Any]:
    company_id = str(case.get("company_id") or "")
    probe = dict(case.get("probe") or {})
    fid = str(case.get("family_id") or family_for_probe(probe) or "")
    corpus = load_corpus_for_company(company_id, holdout_corpus="overlap_strengthened")
    pool = units_for_family_pool(corpus, fid, company_id) if fid else corpus
    overlap = measure_probe_overlap_enhanced(probe, pool, company_id=company_id, family_id=fid, use_family_pool=True)

    multi_doc = bool(overlap.get("multi_logical_doc_candidate"))
    multi_confirm = bool(overlap.get("multi_logical_doc_agreeing_values"))
    has_candidate = overlap.get("logical_doc_overlap_count", 0) > 0

    failure_mode = "none"
    if not has_candidate:
        failure_mode = "corpus_limited_no_candidate"
    elif not multi_doc:
        failure_mode = "corpus_limited_single_logical_doc"
    elif not multi_confirm:
        failure_mode = "system_extraction_or_equivalence_gap"

    return {
        "case_id": case.get("case_id"),
        "case_origin": "natural",
        "company_id": company_id,
        "family_id": fid,
        "item": case.get("item"),
        "cross_doc_eligible": case.get("cross_doc_eligible"),
        "overlap": overlap,
        "failure_mode": failure_mode,
        "corpus_limited": failure_mode.startswith("corpus_limited"),
        "system_gap": failure_mode == "system_extraction_or_equivalence_gap",
        "passed": has_candidate,
    }


_SCOPE_RE_LATIN = re.compile(r"scope\s*([123])", re.IGNORECASE)
_SCOPE_RE_KO = re.compile(r"스코프\s*([123])")


def _metric_anchor_tokens(text: str) -> set[str]:
    """Extract distinctive metric anchors (e.g. scope1/2/3) so a question about Scope 3
    is not falsely matched by a corpus that only discloses Scope 1."""
    toks: set[str] = set()
    for m in _SCOPE_RE_LATIN.findall(text or ""):
        toks.add(f"scope{m}")
    for m in _SCOPE_RE_KO.findall(text or ""):
        toks.add(f"scope{m}")
    return toks


def _evaluate_answerability_case(case: dict[str, Any]) -> dict[str, Any]:
    """Classify a question as answerable / out_of_scope / no_information.

    Separates a *question problem* (unclear or out-of-scope) and an *honest abstain*
    (recognized metric but value simply not disclosed) from a real corpus_limited or
    system_gap. Routing uses the same `_family_for_probe` the lane uses in production.
    """
    probe = dict(case.get("probe") or {})
    expected = str(case.get("expected_answerability") or "")
    corpus = case.get("inline_corpus") or []
    corpus_text = " ".join(str(u.get("text") or "") for u in corpus)
    item = str(probe.get("item") or "")

    fid = _family_for_probe(probe)
    if not fid:
        predicted = "out_of_scope"
        reason = "question_not_mapped_to_metric_family"
    else:
        q_tokens = _metric_anchor_tokens(str(probe.get("question") or "") + " " + item)
        c_tokens = _metric_anchor_tokens(corpus_text)
        if q_tokens:
            info_present = bool(q_tokens & c_tokens)
        else:
            info_present = bool(item) and item in corpus_text
        if info_present:
            predicted = "answerable"
            reason = "metric_family_recognized_and_value_present"
        else:
            predicted = "no_information"
            reason = "metric_family_recognized_but_value_not_disclosed"

    passed = predicted == expected
    # Safety signal: never confidently answer something that is not answerable.
    abstain_safe = not (expected in ("out_of_scope", "no_information") and predicted == "answerable")
    return {
        "case_id": case.get("case_id"),
        "case_origin": case.get("case_origin"),
        "capability": "answerability_classification",
        "family_id": fid,
        "expected_answerability": expected,
        "predicted_answerability": predicted,
        "answerability_reason": reason,
        "answerability_ok": passed,
        "abstain_safe": abstain_safe,
        "passed": passed,
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    test_type = case.get("test_type")
    if test_type == "value_pair_equivalence":
        out = _evaluate_value_pair_case(case)
    elif test_type == "canonical_key_match":
        out = _evaluate_canonical_case(case)
    elif test_type == "multi_source_extraction":
        out = _evaluate_multi_source_case(case)
    elif test_type == "natural_holdout_probe":
        out = _evaluate_natural_case(case)
    elif test_type == "answerability_probe":
        out = _evaluate_answerability_case(case)
    else:
        out = {"case_id": case.get("case_id"), "passed": False, "error": "unknown_test_type"}
    out.setdefault("case_origin", case.get("case_origin"))
    out.setdefault("family_id", case.get("family_id"))
    return out


def _answerability_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ans = [r for r in rows if r.get("capability") == "answerability_classification"]
    n = len(ans)
    if not n:
        return {"case_count": 0}
    correct = sum(1 for r in ans if r.get("answerability_ok"))
    unanswerable = [r for r in ans if r.get("expected_answerability") in ("out_of_scope", "no_information")]
    abstain_safe = sum(1 for r in unanswerable if r.get("abstain_safe"))
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in ans:
        confusion[str(r.get("expected_answerability"))][str(r.get("predicted_answerability"))] += 1
    return {
        "case_count": n,
        "answerability_accuracy": _rate(correct, n),
        "abstain_safety_rate": _rate(abstain_safe, len(unanswerable)) if unanswerable else None,
        "by_expected_predicted": {k: dict(v) for k, v in confusion.items()},
    }


def _aggregate_capability_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alias_ok = alias_total = 0
    equiv_ok = equiv_total = 0
    extract_ok = extract_total = 0
    fusion_ok = fusion_total = 0
    class_ok = class_total = 0
    resolve_ok = resolve_total = 0
    promo_ok = promo_total = 0

    for row in rows:
        if row.get("case_origin") == "natural":
            continue
        tags = set(row.get("capability_tags") or [])
        if row.get("capability"):
            tags.add(str(row.get("capability")))
        if row.get("alias_normalization_ok") is not None:
            alias_total += 1
            if row.get("passed"):
                alias_ok += 1
        if "cross_doc_equivalence" in tags:
            equiv_total += 1
            if row.get("passed"):
                equiv_ok += 1
        if row.get("extract_alignment_ok") is not None:
            extract_total += 1
            if row.get("extract_alignment_ok"):
                extract_ok += 1
        if row.get("fusion_ok") is not None:
            fusion_total += 1
            if row.get("fusion_ok"):
                fusion_ok += 1
        if row.get("classification_ok") is not None:
            class_total += 1
            if row.get("classification_ok"):
                class_ok += 1
        if row.get("resolution_status"):
            resolve_total += 1
            if row.get("resolution_status") in ("resolved", "resolved_with_preference_rule"):
                resolve_ok += 1
        if row.get("promotion_ok") is not None:
            promo_total += 1
            if row.get("promotion_ok"):
                promo_ok += 1

    return {
        "alias_normalization_success_rate": _rate(alias_ok, alias_total),
        "cross_doc_equivalence_match_rate": _rate(equiv_ok, equiv_total),
        "cross_role_extraction_alignment_rate": _rate(extract_ok, extract_total),
        "evidence_fusion_success_rate": _rate(fusion_ok, fusion_total),
        "conflict_classification_accuracy": _rate(class_ok, class_total),
        "conflict_resolution_readiness_rate": _rate(resolve_ok, resolve_total),
        "single_source_to_multi_source_promotion_rate": _rate(promo_ok, promo_total),
        "counts": {
            "alias": {"ok": alias_ok, "total": alias_total},
            "equivalence": {"ok": equiv_ok, "total": equiv_total},
            "extraction": {"ok": extract_ok, "total": extract_total},
            "fusion": {"ok": fusion_ok, "total": fusion_total},
            "classification": {"ok": class_ok, "total": class_total},
            "resolution": {"ok": resolve_ok, "total": resolve_total},
            "promotion": {"ok": promo_ok, "total": promo_total},
        },
        "metric_notes": {
            "alias_normalization_success_rate": "constructed value_pair cases",
            "cross_doc_equivalence_match_rate": "constructed canonical/equiv cases",
            "cross_role_extraction_alignment_rate": "constructed multi-source extract per logical doc",
            "evidence_fusion_success_rate": "constructed multi_source_confirmed expectation",
            "conflict_classification_accuracy": "constructed expected_conflict_status match",
            "conflict_resolution_readiness_rate": "proxy: aggregation resolution_status resolved*",
            "single_source_to_multi_source_promotion_rate": "constructed promotion_ok heuristic",
        },
    }


def _natural_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    natural = [r for r in rows if r.get("case_origin") == "natural"]
    n = max(1, len(natural))
    return {
        "case_count": len(natural),
        "candidate_found_rate": round(sum(1 for r in natural if r.get("passed")) / n, 4),
        "corpus_limited_rate": round(sum(1 for r in natural if r.get("corpus_limited")) / n, 4),
        "system_gap_rate": round(sum(1 for r in natural if r.get("system_gap")) / n, 4),
        "by_failure_mode": _failure_mode_counts(natural),
    }


def _failure_mode_counts(natural_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in natural_rows:
        counts[str(r.get("failure_mode") or "unknown")] += 1
    return dict(counts)


def run_capability_benchmark(
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cases = cases or all_capability_cases(include_natural=True)
    results = [evaluate_case(c) for c in cases]
    constructed_rows = [r for r in results if r.get("case_origin") != "natural" or r.get("test_type") != "natural_holdout_probe"]
    constructed_pipeline = [r for r in results if r.get("case_origin") == "constructed" and r.get("fusion_ok") is not None]
    natural_rows = [r for r in results if r.get("case_origin") == "natural"]

    capability_metrics = _aggregate_capability_metrics(results)
    natural_metrics = _natural_metrics(natural_rows)
    natural_metrics["by_failure_mode"] = _failure_mode_counts(natural_rows)
    answerability_metrics = _answerability_metrics(results)

    by_capability: dict[str, list] = defaultdict(list)
    for r in results:
        cap = r.get("capability") or "unknown"
        by_capability[cap].append(r)

    by_family: dict[str, list] = defaultdict(list)
    for r in constructed_pipeline:
        by_family[str(r.get("family_id") or "unknown")].append(r)

    family_scores = {}
    for fid, rows in by_family.items():
        family_scores[fid] = {
            "case_count": len(rows),
            "fusion_success_rate": _rate(sum(1 for r in rows if r.get("fusion_ok")), len(rows)),
            "classification_accuracy": _rate(sum(1 for r in rows if r.get("classification_ok")), len(rows)),
        }

    promotion_matrix = []
    for r in results:
        if r.get("promotion") is None:
            continue
        cid = r.get("case_id")
        src = next((c for c in cases if c.get("case_id") == cid), {})
        promotion_matrix.append(
            {
                "case_id": cid,
                "expected_multi_source": src.get("expected_multi_source_confirmed"),
                "promotion": r.get("promotion"),
                "promotion_ok": r.get("promotion_ok"),
                "conflict_status": r.get("conflict_status"),
            }
        )

    return {
        "case_results": results,
        "capability_metrics": capability_metrics,
        "natural_metrics": natural_metrics,
        "answerability_metrics": answerability_metrics,
        "constructed_metrics": capability_metrics,
        "by_capability": {k: v for k, v in by_capability.items()},
        "by_family_constructed": family_scores,
        "promotion_matrix": promotion_matrix,
        "natural_vs_constructed_split": {
            "natural_overlap_cases": {
                "count": len(natural_rows),
                "metrics": natural_metrics,
            },
            "constructed_overlap_cases": {
                "count": sum(1 for c in cases if c.get("case_origin") == "constructed"),
                "metrics": capability_metrics,
            },
        },
    }


def _mandatory_answers(bench: dict[str, Any]) -> dict[str, Any]:
    cm = bench.get("capability_metrics") or {}
    nm = bench.get("natural_metrics") or {}
    ff = bench.get("by_family_constructed") or {}

    best_family = None
    best_score = -1.0
    for fid, stats in ff.items():
        fs = float(stats.get("fusion_success_rate") or 0) + float(stats.get("classification_accuracy") or 0)
        if fs > best_score:
            best_score = fs
            best_family = fid

    constructed_fusion = cm.get("evidence_fusion_success_rate")
    natural_corpus_limited = nm.get("corpus_limited_rate")

    conflict_class = cm.get("conflict_classification_accuracy")
    conflict_resolve = cm.get("conflict_resolution_readiness_rate")
    strongest_conflict = "classification"
    if conflict_resolve is not None and conflict_class is not None:
        if conflict_resolve > conflict_class:
            strongest_conflict = "resolution"
        elif conflict_class > conflict_resolve:
            strongest_conflict = "classification"
        else:
            strongest_conflict = "classification_tie_resolution"

    return {
        "1_core_capability_strength_by_area": {
            cap: cm.get(cap)
            for cap in CAPABILITY_METRICS
        },
        "2_corpus_vs_system_failure_split": {
            "natural_corpus_limited_rate": natural_corpus_limited,
            "natural_system_gap_rate": nm.get("system_gap_rate"),
            "constructed_shows_system_capability": constructed_fusion,
            "interpretation": (
                "Natural fail chủ yếu do corpus_limited; constructed cases đo capability riêng"
            ),
        },
        "3_constructed_multi_source_fusion": {
            "evidence_fusion_success_rate": constructed_fusion,
            "cross_role_extraction_alignment_rate": cm.get("cross_role_extraction_alignment_rate"),
            "promotion_rate": cm.get("single_source_to_multi_source_promotion_rate"),
        },
        "4_conflict_handling_strength": {
            "strongest": strongest_conflict,
            "classification_accuracy": conflict_class,
            "resolution_readiness_rate": conflict_resolve,
            "promotion_rate": cm.get("single_source_to_multi_source_promotion_rate"),
        },
        "5_best_family_for_real_docs": best_family,
        "6_next_step_for_real_enterprise_docs": (
            "Plug-in readiness: giữ capability benchmark làm regression gate; "
            "khi có tài liệu mới chỉ cần thêm natural cases — không rebuild pipeline; "
            "tiếp tục harden equivalence/fusion/conflict trên constructed suite"
        ),
    }


def write_benchmark_artifacts(out_dir: Path, bench: dict[str, Any], *, cases_meta: dict[str, Any]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    answers = _mandatory_answers(bench)
    prior = {}
    if PRIOR_ARTIFACT.exists():
        prior = json.loads(PRIOR_ARTIFACT.read_text(encoding="utf-8"))

    capability_case_matrix = {
        "cases_path": cases_meta.get("path"),
        "total_cases": cases_meta.get("total"),
        "results": bench.get("case_results"),
        "by_capability": bench.get("by_capability"),
    }

    summary = {
        "artifact": "enterprise_docs_crossdoc_core_capability",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "crossdoc_core_capability_benchmark",
        "prior_artifact": prior.get("artifact") or "enterprise_docs_overlap_strengthening_20260619-095735",
        "cases_meta": cases_meta,
        "capability_metrics": bench.get("capability_metrics"),
        "natural_vs_constructed": bench.get("natural_vs_constructed_split"),
        "mandatory_answers": answers,
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
            "constructed_not_production_benchmark": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "capability_case_matrix.json").write_text(
        json.dumps(capability_case_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "natural_vs_constructed_split.json").write_text(
        json.dumps(bench.get("natural_vs_constructed_split"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "capability_metrics.json").write_text(
        json.dumps(bench.get("capability_metrics"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "readiness_promotion_matrix.json").write_text(
        json.dumps(bench.get("promotion_matrix"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "report.md").write_text(_report(out_dir, summary, answers), encoding="utf-8")
    return summary


def _report(out_dir: Path, summary: dict[str, Any], answers: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enterprise internal-doc — Cross-doc core capability benchmark",
            "",
            f"Artifact: `{out_dir.relative_to(ROOT)}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Capability metrics (constructed — proxy/heuristic)",
            "",
            json.dumps(summary.get("capability_metrics"), ensure_ascii=False, indent=2),
            "",
        ]
    )
