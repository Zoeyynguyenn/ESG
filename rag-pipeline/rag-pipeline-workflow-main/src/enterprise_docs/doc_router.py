"""Heuristic routing from ESG question metadata to enterprise document IDs (registry-driven)."""

from __future__ import annotations

from typing import Any

from enterprise_docs.models import AnswerMode, EvidencePlan
from enterprise_docs.registries import (
    cross_document_signals,
    csv_supporting_logical_doc,
    fallback_logical_doc,
    holdout_routing_profile,
    is_holdout_company,
    logical_documents,
    role_label_for_doc,
    routing_profile,
)


def _blob(question: dict) -> str:
    parts = [
        question.get("domain") or "",
        question.get("category") or "",
        question.get("subcategory") or "",
        question.get("item") or "",
        question.get("question") or "",
        question.get("pillar") or "",
    ]
    return " ".join(parts).lower()


def _score_doc(blob: str, spec: dict[str, str]) -> int:
    score = 0
    for token in (spec.get("domains") or "").split(","):
        token = token.strip().lower()
        if token and token in blob:
            score += 3
    for token in (spec.get("topics") or "").split(","):
        token = token.strip().lower()
        if token and token in blob:
            score += 2
    return score


def _documents_for_company(company_id: str) -> dict[str, dict[str, Any]]:
    docs = logical_documents(company_id)
    return {
        lid: {
            "path_hint": str(spec.get("path_hint") or ""),
            "domains": str(spec.get("domains") or ""),
            "topics": str(spec.get("topics") or ""),
        }
        for lid, spec in docs.items()
    }


def _default_role(company_id: str, logical_id: str, *, kind: str) -> str:
    label = role_label_for_doc(company_id, logical_id, kind=kind)
    if label:
        return label
    profile = routing_profile()
    if kind == "qualitative":
        return str(profile.get("qualitative_default_role") or "primary narrative evidence")
    return str(profile.get("quantitative_default_role") or "numeric table evidence")


def _cross_doc_triggered(blob: str, primary: list[str], company_id: str) -> bool:
    docs = set(primary)
    for signal in cross_document_signals():
        stype = signal.get("type")
        if stype == "blob_tokens_all":
            tokens = signal.get("tokens") or []
            if tokens and all(str(t).lower() in blob for t in tokens):
                return True
        elif stype == "primary_logical_pair":
            pair = signal.get("logical_ids") or []
            if len(pair) >= 2 and all(p in docs for p in pair[:2]):
                return True
    return len(primary) >= 2


def _holdout_cross_doc_probe(question: dict, company_id: str) -> bool:
    holdout = holdout_routing_profile(company_id)
    fams = holdout.get("cross_doc_quant_probe_pattern_families") or []
    if not fams:
        return False
    if str(question.get("kind") or "") != "quantitative":
        return False
    pf = str(question.get("pattern_family") or "")
    return pf in fams


def route_documents(question: dict, *, company_id: str = "demo_company") -> list[str]:
    blob = _blob(question)
    scored: list[tuple[int, str]] = []
    for doc_id, spec in _documents_for_company(company_id).items():
        score = _score_doc(blob, spec)
        if score > 0:
            scored.append((score, doc_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    if not scored:
        fb = fallback_logical_doc(company_id)
        return [fb] if fb else []

    holdout = holdout_routing_profile(company_id)
    max_primary = int(holdout.get("max_primary_docs") or 4)
    if _holdout_cross_doc_probe(question, company_id):
        max_primary = int(holdout.get("cross_doc_max_primary_docs") or 2)
    elif is_holdout_company(company_id) and max_primary == 1:
        return [scored[0][1]]

    top_score = scored[0][0]
    primary = [doc_id for s, doc_id in scored if s >= max(1, top_score - 1)]
    return primary[:max_primary]


def build_evidence_plan(question: dict, *, company_id: str = "demo_company") -> EvidencePlan:
    item_id = str(question.get("item_id") or "")
    kind = question.get("kind") or ""
    blob = _blob(question)
    primary = route_documents(question, company_id=company_id)
    csv_doc = csv_supporting_logical_doc(company_id)

    roles: dict[str, str] = {}
    supporting: list[str] = []

    notes_cfg = routing_profile().get("quantitative_notes") or {}

    if kind == "qualitative":
        answer_mode: AnswerMode = "cross_document_answer"
        for doc_id in primary:
            roles[doc_id] = _default_role(company_id, doc_id, kind="qualitative")
        if csv_doc and csv_doc not in primary:
            supporting.append(csv_doc)
        needs_merge = True
        needs_conflict = False
        notes = str(notes_cfg.get("qualitative") or "Qualitative cross-document evidence plan.")
    else:
        holdout = holdout_routing_profile(company_id)
        force_single = bool(holdout.get("force_single_doc_quant"))
        if force_single and _holdout_cross_doc_probe(question, company_id):
            force_single = False
        cross = (not force_single) and (
            _cross_doc_triggered(blob, primary, company_id)
            or (_holdout_cross_doc_probe(question, company_id) and len(primary) >= 2)
        )
        if cross:
            answer_mode = "cross_document_answer"
            for doc_id in primary:
                roles[doc_id] = _default_role(company_id, doc_id, kind="quantitative")
            if csv_doc and csv_doc not in primary:
                supporting.append(csv_doc)
                roles[csv_doc] = str(
                    routing_profile().get("csv_supporting_role")
                    or "aggregated performance summary / year series"
                )
            needs_merge = len(primary) >= 2
            needs_conflict = "not disclosed" in blob
            notes = str(notes_cfg.get("cross_doc") or "Multi-domain metric — may need merge.")
        else:
            answer_mode = "single_document_answer"
            doc_id = primary[0]
            roles[doc_id] = _default_role(company_id, doc_id, kind="quantitative")
            needs_merge = False
            needs_conflict = False
            notes = str(notes_cfg.get("single_doc") or "Single primary document heuristic.")

    return EvidencePlan(
        item_id=item_id,
        answer_mode=answer_mode,
        primary_document_ids=primary,
        supporting_document_ids=supporting,
        roles=roles,
        needs_merge=needs_merge,
        needs_conflict_resolution=needs_conflict,
        notes=notes,
    )
