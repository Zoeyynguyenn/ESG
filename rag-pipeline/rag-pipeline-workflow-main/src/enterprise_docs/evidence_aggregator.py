"""Merge evidence from multiple documents for cross-doc questions (registry-driven)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from enterprise_docs.cross_doc_retriever import RetrievalResult
from enterprise_docs.diagnostics import NOT_DISCLOSED_RE
from enterprise_docs.registries import (
    corpus_path_patterns,
    governance_anchor_doc,
    governance_anchor_metrics,
    narrative_probe_config,
)
from enterprise_docs.structured_extractor import (
    RowMatchCandidate,
    _collect_row_candidates_from_text,
    _infer_target_unit,
    _normalize_phrase,
    probe_candidates_in_units,
)


def _company_id(plan_row: dict[str, Any]) -> str:
    return str(plan_row.get("company_id") or "demo_company")


def _governance_metrics(plan_row: dict[str, Any]) -> frozenset[str]:
    return governance_anchor_metrics(_company_id(plan_row))


def _governance_doc(plan_row: dict[str, Any]) -> str | None:
    return governance_anchor_doc(_company_id(plan_row))


def _narrative_probe(plan_row: dict[str, Any]) -> tuple[frozenset[str], str | None]:
    cfg = narrative_probe_config(_company_id(plan_row))
    metrics = cfg.get("metrics") or frozenset()
    logical = cfg.get("logical_doc")
    return metrics, logical


def _corpus_patterns(plan_row: dict[str, Any]) -> dict[str, str]:
    return corpus_path_patterns(_company_id(plan_row))


@dataclass
class AggregatedCandidate:
    logical_document_id: str
    unit_id: str
    metric_label: str
    value: str
    unit: str | None
    year: int | None
    role: str | None = None
    source_snippet: str = ""
    row_match_score: float = 0.0
    is_primary_doc: bool = False
    narrative_metric_parse_used: bool = False


@dataclass
class AggregationResult:
    question_id: str
    aggregation_status: str
    aggregated_evidence_units: list[AggregatedCandidate] = field(default_factory=list)
    conflict_flags: list[str] = field(default_factory=list)
    missing_roles: list[str] = field(default_factory=list)
    aggregation_reason: str = ""
    predicted_value: str | None = None
    predicted_unit: str | None = None
    fail_stage: str | None = None
    resolved_value: str | None = None
    resolution_status: str | None = None
    resolution_reason: str | None = None
    primary_doc_used: str | None = None
    sufficiency_status: str | None = None
    sufficiency_reason: str | None = None
    required_roles: list[str] = field(default_factory=list)
    optional_roles: list[str] = field(default_factory=list)
    roles_with_metric: list[str] = field(default_factory=list)
    roles_absent_by_design: list[str] = field(default_factory=list)
    missing_numeric_roles: list[str] = field(default_factory=list)
    multi_source_confirmed: bool = False
    confirming_logical_docs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["aggregated_evidence_units"] = [asdict(c) for c in self.aggregated_evidence_units]
        return d


def _normalize_value(val: str) -> str:
    return val.replace(",", "").replace("약", "").strip()


def _normalize_metric_key(label: str) -> str:
    key = _normalize_phrase(label)
    key = re.sub(r"\d{4}", "", key)
    key = re.sub(r"[^a-z0-9가-힣]+", " ", key)
    return " ".join(key.split())


def _values_conflict(
    a: str,
    b: str,
    *,
    item: str | None = None,
    family_id: str | None = None,
    tolerance_pct: float = 0.05,
) -> bool:
    from enterprise_docs.fusion_equivalence import values_conflict

    return values_conflict(a, b, item=item, family_id=family_id)


def _classify_roles(plan_row: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return required_roles, optional_roles for aggregation expectation."""
    roles: dict[str, str] = plan_row.get("roles") or {}
    primary_ids = list(plan_row.get("primary_document_ids") or [])
    item = str(plan_row.get("item") or "")

    required: list[str] = []
    optional: list[str] = []

    if item in _governance_metrics(plan_row):
        anchor_doc = _governance_doc(plan_row)
        if anchor_doc and anchor_doc in roles:
            required.append(anchor_doc)
            for lid in roles:
                if lid != anchor_doc:
                    optional.append(lid)
            return required, optional

    for lid, desc in roles.items():
        desc_l = (desc or "").lower()
        if lid == "doc_evidence_csv" or "numeric table evidence" in desc_l:
            optional.append(lid)
        elif lid in primary_ids[:1]:
            required.append(lid)
        elif "supporting" in desc_l or "context" in desc_l:
            optional.append(lid)
        else:
            required.append(lid)

    return list(dict.fromkeys(required)), list(dict.fromkeys(optional))


def _logical_doc_for_unit(
    unit: dict[str, Any],
    logical_to_corpus: dict[str, str],
    *,
    path_patterns: dict[str, str] | None = None,
) -> str | None:
    corpus_id = str(unit.get("document_id") or "")
    for logical, mapped in logical_to_corpus.items():
        if mapped == corpus_id:
            return logical
    patterns = path_patterns or _corpus_patterns(
        {"company_id": str(unit.get("company_id") or "demo_company")}
    )
    for logical, hint in patterns.items():
        if hint in corpus_id:
            return logical
    return None


def _units_for_logical(
    logical_id: str,
    unit_lookup: dict[str, dict[str, Any]],
    logical_to_corpus: dict[str, str],
) -> list[dict[str, Any]]:
    corpus_id = logical_to_corpus.get(logical_id)
    if not corpus_id:
        return []
    return [
        u for u in unit_lookup.values()
        if str(u.get("document_id") or "") == corpus_id
    ]


def _metric_absent_in_role(
    logical_id: str,
    plan_row: dict[str, Any],
    unit_lookup: dict[str, dict[str, Any]],
    logical_to_corpus: dict[str, str],
) -> bool:
    """True when corpus for role has no parseable candidate even at low threshold."""
    units = _units_for_logical(logical_id, unit_lookup, logical_to_corpus)
    if not units:
        return True
    probes = probe_candidates_in_units(plan_row, units, logical_doc=logical_id, min_score=0.1)
    return len(probes) == 0


def _narrative_probe_candidates(
    plan_row: dict[str, Any],
    unit_lookup: dict[str, dict[str, Any]],
    logical_to_corpus: dict[str, str],
) -> list[RowMatchCandidate]:
    """Registry-configured narrative probe when retrieval cluster lacks value."""
    item = str(plan_row.get("item") or "")
    probe_metrics, probe_logical = _narrative_probe(plan_row)
    if item not in probe_metrics or not probe_logical:
        return []
    units = _units_for_logical(probe_logical, unit_lookup, logical_to_corpus)
    return probe_candidates_in_units(
        plan_row, units, logical_doc=probe_logical, min_score=0.75
    )


def _candidate_from_row(
    row: RowMatchCandidate,
    *,
    role: str | None,
    is_primary: bool,
) -> AggregatedCandidate:
    return AggregatedCandidate(
        logical_document_id=row.logical_doc or "",
        unit_id=row.unit_id or "",
        metric_label=row.label,
        value=row.value,
        unit=row.unit,
        year=row.year,
        role=role,
        source_snippet=row.label,
        row_match_score=row.row_match_score,
        is_primary_doc=is_primary,
        narrative_metric_parse_used=row.narrative_metric_parse_used,
    )


def _confirming_logical_docs(
    candidates: list[AggregatedCandidate],
    resolved_value: str | None,
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> list[str]:
    from enterprise_docs.fusion_equivalence import fusion_confirming_docs

    return fusion_confirming_docs(
        candidates, resolved_value, item=item, family_id=family_id
    )


def _resolve_candidates(
    candidates: list[AggregatedCandidate],
    *,
    primary_logical: str | None,
    target_year: int | None = None,
    item: str | None = None,
    family_id: str | None = None,
) -> tuple[str | None, str, str, list[str], str | None, AggregatedCandidate | None]:
    if not candidates:
        return None, "failed", "no_candidates", [], None, None

    conflict_flags: list[str] = []
    years = [c.year for c in candidates if c.year]
    if target_year is None and years:
        target_year = max(years)

    year_filtered = [c for c in candidates if c.year is None or c.year == target_year]
    pool = year_filtered if year_filtered else candidates

    primary_pool = [c for c in pool if c.logical_document_id == primary_logical]
    supporting_pool = [c for c in pool if c.logical_document_id != primary_logical]

    disclosed_pool = [c for c in pool if not NOT_DISCLOSED_RE.search(c.value)]
    if disclosed_pool:
        pool = disclosed_pool
        primary_pool = [c for c in primary_pool if not NOT_DISCLOSED_RE.search(c.value)]
        supporting_pool = [c for c in supporting_pool if not NOT_DISCLOSED_RE.search(c.value)]

    if primary_pool:
        best_primary = max(primary_pool, key=lambda c: c.row_match_score)
        for sup in supporting_pool:
            if NOT_DISCLOSED_RE.search(sup.value):
                continue
            if _values_conflict(best_primary.value, sup.value, item=item, family_id=family_id):
                conflict_flags.append(
                    f"numeric_mismatch_primary_vs_{sup.logical_document_id}"
                )
        if conflict_flags:
            return (
                best_primary.value,
                "resolved_with_preference_rule",
                "primary_doc_numeric_preferred_over_conflicting_supporting",
                conflict_flags,
                best_primary.logical_document_id,
                best_primary,
            )
        return (
            best_primary.value,
            "resolved",
            "primary_doc_best_row_match",
            [],
            best_primary.logical_document_id,
            best_primary,
        )

    disclosed = [c for c in pool if not NOT_DISCLOSED_RE.search(c.value)]
    if not disclosed:
        return None, "conflict_unresolved", "all_candidates_not_disclosed", ["all_not_disclosed"], None, None

    by_metric: dict[str, list[AggregatedCandidate]] = {}
    plan_stub = {"item": item or "", "family_id": family_id or ""}
    for c in disclosed:
        from enterprise_docs.fusion_equivalence import canonical_metric_label_key

        by_metric.setdefault(canonical_metric_label_key(c.metric_label, plan_stub), []).append(c)

    best_group = max(by_metric.values(), key=lambda g: max(x.row_match_score for x in g))
    if len(best_group) == 1:
        c = best_group[0]
        return c.value, "resolved", "single_supporting_candidate", [], c.logical_document_id, c

    vals = [c.value for c in best_group]
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            if _values_conflict(vals[i], vals[j], item=item, family_id=family_id):
                conflict_flags.append(f"numeric_mismatch:{vals[i]}_vs_{vals[j]}")
    best = max(best_group, key=lambda c: c.row_match_score)
    if conflict_flags:
        return (
            best.value,
            "resolved_with_preference_rule",
            "highest_row_match_amid_conflict",
            conflict_flags,
            best.logical_document_id,
            best,
        )
    return best.value, "resolved", "metric_group_consensus", [], best.logical_document_id, best


def _assess_sufficiency(
    plan_row: dict[str, Any],
    *,
    resolved_value: str | None,
    best_candidate: AggregatedCandidate | None,
    roles_with_metric: list[str],
    roles_absent_by_design: list[str],
    missing_numeric_roles: list[str],
    required_roles: list[str],
    optional_roles: list[str],
    conflict_flags: list[str],
    resolution_status: str,
) -> tuple[str, str, str]:
    """Returns sufficiency_status, sufficiency_reason, legacy aggregation_status."""
    item = str(plan_row.get("item") or "")

    if resolution_status == "conflict_unresolved":
        return "conflict_unresolved", "unresolved_numeric_conflict", "conflict"

    if not resolved_value or not best_candidate:
        return "failed", "no_resolved_value", "failed"

    if conflict_flags and resolution_status != "resolved_with_preference_rule":
        return "conflict_unresolved", "unresolved_after_conflict_detect", "conflict"

    strong = best_candidate.row_match_score >= 0.85 or best_candidate.narrative_metric_parse_used
    only_one_source = len(roles_with_metric) == 1
    anchor_doc = _governance_doc(plan_row)
    anchor_case = (
        item in _governance_metrics(plan_row)
        and anchor_doc is not None
        and anchor_doc in roles_with_metric
    )

    if strong and (only_one_source or anchor_case):
        blockers = [r for r in missing_numeric_roles if r in required_roles]
        if not blockers:
            absent_ok = all(
                r in roles_absent_by_design or r in optional_roles
                for r in (plan_row.get("roles") or {})
                if r not in roles_with_metric
            )
            if absent_ok or anchor_case:
                return (
                    "resolved_single_source_sufficient",
                    "single_authoritative_source_metric_absent_elsewhere",
                    "success",
                )

    if missing_numeric_roles:
        real_gaps = [r for r in missing_numeric_roles if r in required_roles]
        if real_gaps:
            return (
                "partial_missing_numeric_role",
                f"missing_numeric_roles:{','.join(real_gaps)}",
                "partial",
            )
        if roles_absent_by_design:
            return (
                "partial_metric_absent_in_role",
                f"metric_absent_in_roles:{','.join(roles_absent_by_design)}",
                "partial",
            )

    if resolution_status in ("resolved", "resolved_with_preference_rule"):
        return "resolved", resolution_status, "success"

    return "failed", "unclassified", "failed"


def aggregate_cross_doc(
    plan_row: dict[str, Any],
    retrieval: RetrievalResult,
    *,
    unit_lookup: dict[str, dict[str, Any]] | None = None,
    logical_to_corpus: dict[str, str] | None = None,
) -> AggregationResult:
    qid = str(plan_row.get("item_id") or "")
    question = str(plan_row.get("question") or "")
    roles: dict[str, str] = plan_row.get("roles") or {}
    primary_logical = (plan_row.get("primary_document_ids") or [None])[0]
    unit_lookup = unit_lookup or {}
    logical_to_corpus = logical_to_corpus or {}

    required_roles, optional_roles = _classify_roles(plan_row)

    if plan_row.get("kind") == "qualitative":
        return AggregationResult(
            question_id=qid,
            aggregation_status="failed",
            fail_stage="synthesis_gap",
            aggregation_reason="qualitative_aggregation_deferred_to_synthesis_phase",
            missing_roles=list(roles.keys()),
            resolution_status="failed",
            sufficiency_status="failed",
        )

    if retrieval.parser_fail:
        return AggregationResult(
            question_id=qid,
            aggregation_status="failed",
            fail_stage="parser_gap",
            aggregation_reason="parser_fail",
            resolution_status="failed",
            sufficiency_status="failed",
        )

    if not retrieval.top_units:
        return AggregationResult(
            question_id=qid,
            aggregation_status="failed",
            fail_stage="retrieval_gap",
            aggregation_reason="no_units_retrieved",
            missing_roles=list(roles.keys()),
            resolution_status="failed",
            sufficiency_status="failed",
        )

    candidates: list[AggregatedCandidate] = []
    roles_with_value: set[str] = set()
    item = str(plan_row.get("item") or "")
    family_id = str(plan_row.get("family_id") or plan_row.get("pattern_family") or "") or None
    from enterprise_docs.narrative_table_fusion import filter_candidates_for_plan_item

    for hit in retrieval.top_units:
        role = roles.get(hit.logical_document_id, "supporting")
        text = hit.evidence_text
        if unit_lookup and hit.unit_id in unit_lookup:
            text = str(
                unit_lookup[hit.unit_id].get("evidence_text")
                or unit_lookup[hit.unit_id].get("text")
                or text
            )
        rows = _collect_row_candidates_from_text(
            text, plan_row, unit_id=hit.unit_id, logical_doc=hit.logical_document_id, min_score=0.25
        )
        if not rows:
            rows = _collect_row_candidates_from_text(
                text, plan_row, unit_id=hit.unit_id, logical_doc=hit.logical_document_id, min_score=0.0
            )
            rows = [r for r in rows if r.row_match_score >= 0.1][:5]
        rows = filter_candidates_for_plan_item(rows, plan_row, min_score=0.2)
        for row in rows:
            cand = _candidate_from_row(
                row, role=role, is_primary=hit.logical_document_id == primary_logical
            )
            candidates.append(cand)
            if hit.logical_document_id in roles:
                roles_with_value.add(hit.logical_document_id)

    # Hardening: scan all planned role corpora for cross-doc confirmation (not retrieval-only)
    seen_unit_ids = {c.unit_id for c in candidates}
    for lid in roles:
        for u in _units_for_logical(lid, unit_lookup, logical_to_corpus)[:12]:
            uid = str(u.get("unit_id") or "")
            if uid in seen_unit_ids:
                continue
            text = str(u.get("evidence_text") or u.get("text") or "")
            rows = _collect_row_candidates_from_text(
                text, plan_row, unit_id=uid, logical_doc=lid, min_score=0.25
            )
            rows = filter_candidates_for_plan_item(rows, plan_row, min_score=0.2)
            for row in rows[:3]:
                cand = _candidate_from_row(
                    row, role=roles.get(lid, "supporting"), is_primary=lid == primary_logical
                )
                candidates.append(cand)
                seen_unit_ids.add(uid)
                roles_with_value.add(lid)

    if not candidates and unit_lookup:
        for row in _narrative_probe_candidates(plan_row, unit_lookup, logical_to_corpus):
            role = roles.get(row.logical_doc or "", "supporting")
            cand = _candidate_from_row(
                row, role=role, is_primary=(row.logical_doc == primary_logical)
            )
            candidates.append(cand)
            if row.logical_doc:
                roles_with_value.add(row.logical_doc)

    roles_with_metric = sorted(roles_with_value)
    roles_absent_by_design: list[str] = []
    missing_numeric_roles: list[str] = []

    for lid in roles:
        if lid in roles_with_value:
            continue
        if not retrieval.role_hits.get(lid, True):
            missing_numeric_roles.append(lid)
        elif _metric_absent_in_role(lid, plan_row, unit_lookup, logical_to_corpus):
            roles_absent_by_design.append(lid)
        else:
            missing_numeric_roles.append(lid)

    if not candidates:
        return AggregationResult(
            question_id=qid,
            aggregation_status="failed",
            fail_stage="extraction_gap",
            aggregation_reason="no_numeric_candidates_from_units",
            missing_roles=missing_numeric_roles,
            missing_numeric_roles=missing_numeric_roles,
            roles_absent_by_design=roles_absent_by_design,
            roles_with_metric=roles_with_metric,
            required_roles=required_roles,
            optional_roles=optional_roles,
            resolution_status="failed",
            sufficiency_status="failed",
            sufficiency_reason="no_candidates",
        )

    best_by_doc: dict[str, AggregatedCandidate] = {}
    for c in candidates:
        prev = best_by_doc.get(c.logical_document_id)
        if prev is None or c.row_match_score > prev.row_match_score:
            best_by_doc[c.logical_document_id] = c
    candidates = list(best_by_doc.values())
    roles_with_value = {c.logical_document_id for c in candidates if c.logical_document_id in roles}

    resolved_value, resolution_status, resolution_reason, conflict_flags, primary_used, best_cand = (
        _resolve_candidates(
            candidates,
            primary_logical=primary_logical,
            item=item,
            family_id=family_id,
        )
    )

    confirming_docs = _confirming_logical_docs(
        candidates,
        resolved_value,
        item=item,
        family_id=family_id,
    )
    multi_confirmed = len(confirming_docs) >= 2 and bool(resolved_value) and not any(
        "numeric_mismatch" in f for f in conflict_flags
    )
    if plan_row.get("kind") == "quantitative" and str(resolved_value or "").strip().lower() in (
        "present",
        "yes",
        "o",
    ):
        multi_confirmed = False

    sufficiency_status, sufficiency_reason, legacy_status = _assess_sufficiency(
        plan_row,
        resolved_value=resolved_value,
        best_candidate=best_cand,
        roles_with_metric=roles_with_metric,
        roles_absent_by_design=roles_absent_by_design,
        missing_numeric_roles=missing_numeric_roles,
        required_roles=required_roles,
        optional_roles=optional_roles,
        conflict_flags=conflict_flags,
        resolution_status=resolution_status,
    )

    fail_stage = "ready" if legacy_status == "success" else "aggregation_gap"
    if legacy_status == "failed":
        fail_stage = "extraction_gap"

    return AggregationResult(
        question_id=qid,
        aggregation_status=legacy_status,
        aggregated_evidence_units=candidates,
        conflict_flags=conflict_flags,
        missing_roles=missing_numeric_roles,
        aggregation_reason=sufficiency_reason,
        predicted_value=resolved_value,
        predicted_unit=_infer_target_unit(question, best_cand.unit if best_cand else None),
        resolved_value=resolved_value,
        resolution_status=resolution_status,
        resolution_reason=resolution_reason,
        primary_doc_used=primary_used,
        fail_stage=fail_stage,
        sufficiency_status=sufficiency_status,
        sufficiency_reason=sufficiency_reason,
        required_roles=required_roles,
        optional_roles=optional_roles,
        roles_with_metric=roles_with_metric,
        roles_absent_by_design=roles_absent_by_design,
        missing_numeric_roles=missing_numeric_roles,
        multi_source_confirmed=multi_confirmed,
        confirming_logical_docs=confirming_docs,
    )
