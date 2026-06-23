"""Structured numeric extraction from retrieved evidence units (registry-driven)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from enterprise_docs.cross_doc_retriever import RetrievalResult
from enterprise_docs.diagnostics import NOT_DISCLOSED_RE
from enterprise_docs.registries import (
    compile_narrative_patterns,
    row_aliases,
    semantic_bridge,
)
from rag_common import tokenize

YEAR_RE = re.compile(r"\b(20\d{2})\b")
NUMERIC_RE = re.compile(r"[\d,]+(?:\.\d+)?")
PCT_QUESTION_RE = re.compile(r"%|비율|율")
COUNT_QUESTION_RE = re.compile(r"몇 명|인원|건수|회|개")
MONEY_QUESTION_RE = re.compile(r"얼마|백만|원|USD|\$|B\b")

# pilot_only: generic tokens excluded from row matching (not company-specific)
GENERIC_TOKENS = frozenset({
    "구성원", "총", "비율", "율", "수", "명", "해당", "기업", "의", "몇", "인가요",
    "employee", "employees", "total", "the", "and", "or", "net", "partial", "proxy",
})


def _company_id(plan_row: dict[str, Any]) -> str:
    return str(plan_row.get("company_id") or "demo_company")


def _row_aliases_for(plan_row: dict[str, Any]) -> dict[str, list[str]]:
    return row_aliases(_company_id(plan_row))


def _semantic_bridge_for(plan_row: dict[str, Any]) -> dict[str, list[str]]:
    return semantic_bridge(_company_id(plan_row))


def _narrative_patterns_for(plan_row: dict[str, Any]) -> list[tuple[str, re.Pattern[str]]]:
    return compile_narrative_patterns(_company_id(plan_row))


def _narrative_value_ok(raw: str) -> bool:
    """Accept numeric or grade-like narrative captures (family-level, not probe-specific)."""
    if not raw or not raw.strip():
        return False
    return bool(re.search(r"\d", raw) or re.search(r"^[A-Z][+]?$", raw.strip()))


@dataclass
class RowMatchCandidate:
    label: str
    value: str
    unit: str | None
    year: int | None
    row_match_score: float
    row_match_reason: str
    unit_id: str | None = None
    logical_doc: str | None = None
    semantic_bridge_used: bool = False
    bridge_reason: str | None = None
    narrative_metric_parse_used: bool = False
    narrative_parse_reason: str | None = None
    narrative_confidence: float = 0.0
    normalized_numeric_value: str | None = None
    normalized_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def probe_candidates_in_units(
    plan_row: dict[str, Any],
    units: list[dict[str, Any]],
    *,
    logical_doc: str | None = None,
    min_score: float = 0.1,
    include_narrative: bool = True,
) -> list[RowMatchCandidate]:
    """Scan corpus units for metric candidates (pilot — sufficiency / narrative probe)."""
    from enterprise_docs.cross_role_extraction import enrich_plan_for_cross_role, probe_candidates_cross_role

    plan = enrich_plan_for_cross_role(plan_row)
    company_id = str(plan.get("company_id") or "")
    if plan.get("family_id") or company_id in ("capability_synthetic",):
        cross = probe_candidates_cross_role(plan, units, logical_doc=logical_doc, min_score=min_score)
        if cross:
            return cross

    out: list[RowMatchCandidate] = []
    for u in units:
        uid = str(u.get("unit_id") or "")
        text = str(u.get("evidence_text") or u.get("text") or "")
        if not text.strip():
            continue
        doc_logical = logical_doc
        out.extend(
            _collect_row_candidates_from_text(
                text,
                plan_row,
                unit_id=uid,
                logical_doc=doc_logical,
                min_score=min_score,
            )
        )
    return out


@dataclass
class ExtractionResult:
    question_id: str
    success: bool
    predicted_value: str | None = None
    predicted_unit: str | None = None
    selected_doc: str | None = None
    selected_unit_ids: list[str] = field(default_factory=list)
    extraction_reason: str = ""
    extraction_confidence: float = 0.0
    fail_stage: str | None = None
    year_used: int | None = None
    raw_snippet: str | None = None
    row_match_score: float = 0.0
    row_match_reason: str = ""
    selected_row_label: str | None = None
    top_row_candidates: list[dict[str, Any]] = field(default_factory=list)
    wrong_row_risk: bool = False
    wrong_row_risk_reason: str | None = None
    semantic_bridge_used: bool = False
    bridge_reason: str | None = None
    narrative_metric_parse_used: bool = False
    narrative_parse_reason: str | None = None
    narrative_confidence: float = 0.0
    normalized_numeric_value: str | None = None
    normalized_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _question_blob(plan_row: dict[str, Any]) -> str:
    parts = [
        plan_row.get("question") or "",
        plan_row.get("item") or "",
        plan_row.get("subcategory") or "",
        plan_row.get("category") or "",
    ]
    return " ".join(str(p) for p in parts if p)


def _specific_tokens(text: str) -> set[str]:
    return {t for t in tokenize(text) if t not in GENERIC_TOKENS and len(t) >= 2}


def _bridge_keys_for_question(plan_row: dict[str, Any]) -> list[str]:
    blob = _question_blob(plan_row)
    item = str(plan_row.get("item") or "")
    sub = str(plan_row.get("subcategory") or "")
    keys: list[str] = []
    for key in _semantic_bridge_for(plan_row):
        if key in item or key in sub or key in blob:
            keys.append(key)
    return keys


def _alias_phrases(plan_row: dict[str, Any]) -> list[str]:
    phrases: list[str] = []
    item = str(plan_row.get("item") or "").strip()
    sub = str(plan_row.get("subcategory") or "").strip()
    cat = str(plan_row.get("category") or "").strip()
    if item:
        phrases.append(item)
    if sub:
        phrases.append(sub)
    if sub and item:
        phrases.append(f"{sub} {item}")
    if cat and item:
        phrases.append(f"{cat} {item}")
    for key, aliases in _row_aliases_for(plan_row).items():
        blob = _question_blob(plan_row)
        if key in blob or key in item or key in sub:
            phrases.extend(aliases)
    for key in _bridge_keys_for_question(plan_row):
        phrases.extend(_semantic_bridge_for(plan_row).get(key, []))
    seen: set[str] = set()
    out: list[str] = []
    for p in phrases:
        pn = _normalize_phrase(p)
        if pn and pn not in seen:
            seen.add(pn)
            out.append(p)
    return out


def _semantic_bridge_match(label: str, plan_row: dict[str, Any]) -> tuple[float, str] | None:
    label_n = _normalize_phrase(label)
    for key in _bridge_keys_for_question(plan_row):
        for en_label in _semantic_bridge_for(plan_row).get(key, []):
            en_n = _normalize_phrase(en_label)
            if not en_n:
                continue
            if en_n == label_n or en_n in label_n or label_n in en_n:
                return 0.87, f"semantic_bridge:{en_label}"
    return None


def score_row_match(label: str, plan_row: dict[str, Any]) -> tuple[float, str]:
    """Strong → weak: item exact, subcategory, phrase, alias, semantic bridge, token overlap."""
    label_n = _normalize_phrase(label)
    item = _normalize_phrase(str(plan_row.get("item") or ""))
    sub = _normalize_phrase(str(plan_row.get("subcategory") or ""))

    if item and item == label_n:
        return 1.0, "item_exact"
    if sub and (sub == label_n or sub in label_n or label_n in sub):
        return 0.92, "subcategory_exact"
    if item and item in label_n:
        return 0.88, "item_in_label"
    for phrase in _alias_phrases(plan_row):
        pn = _normalize_phrase(phrase)
        if pn and (pn == label_n or pn in label_n or label_n in pn):
            return 0.85, f"alias:{phrase[:40]}"

    bridge = _semantic_bridge_match(label, plan_row)
    if bridge:
        return bridge

    q_specific = _specific_tokens(_question_blob(plan_row))
    l_specific = _specific_tokens(label)
    if not q_specific:
        return 0.0, "no_specific_query_tokens"
    overlap = q_specific.intersection(l_specific)
    if not overlap:
        return 0.0, "no_specific_overlap"

    row_extra = l_specific - q_specific
    penalty = 0.15 * len(row_extra)
    base = len(overlap) / max(1, len(q_specific))
    score = max(0.0, base - penalty)
    if score < 0.35:
        return score, "token_overlap_weak"
    return min(0.75, score), "token_overlap"


def _wrong_row_risk(label: str, plan_row: dict[str, Any], score: float, reason: str) -> tuple[bool, str | None]:
    if score >= 0.85:
        return False, None
    if reason in ("item_exact", "subcategory_exact", "item_in_label") or reason.startswith(
        ("alias:", "semantic_bridge:")
    ):
        return False, None
    q_tokens = _specific_tokens(_question_blob(plan_row))
    label_tokens = _specific_tokens(label)
    extra = label_tokens - q_tokens
    if extra:
        return True, f"row_has_extra_tokens:{','.join(sorted(extra)[:5])}"
    if reason == "token_overlap_weak":
        return True, "weak_token_overlap_only"
    return False, None


def _normalize_numeric_unit(value: str, unit_hint: str | None) -> tuple[str, str | None]:
    val = value.replace(",", "").strip()
    unit = (unit_hint or "").strip() or None
    if unit and unit.lower() in ("mil", "million"):
        unit = "USD million"
    elif unit and unit.lower() == "billion":
        unit = "USD billion"
    return val, unit


def _infer_target_unit(question: str, table_unit: str | None) -> str | None:
    if table_unit and table_unit.strip() and table_unit.lower() not in ("nan", "-"):
        return table_unit.strip()
    if PCT_QUESTION_RE.search(question):
        return "%"
    if COUNT_QUESTION_RE.search(question):
        return "count"
    if MONEY_QUESTION_RE.search(question):
        return "currency"
    return None


def _parse_md_table_rows(text: str) -> list[tuple[list[str], list[str]]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows: list[tuple[list[str], list[str]]] = []
    for ln in lines[2:]:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) >= 2:
            rows.append((header, cells))
    return rows


def _year_columns(header: list[str]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for i, h in enumerate(header):
        m = YEAR_RE.search(h)
        if m:
            out.append((int(m.group(1)), i))
    return sorted(out, reverse=True)


def _check_not_disclosed_for_question(text: str, plan_row: dict[str, Any]) -> bool:
    """Honest fail when source explicitly says Not disclosed for the asked metric."""
    item = str(plan_row.get("item") or "")
    sub = str(plan_row.get("subcategory") or "")
    for line in text.splitlines():
        if "not disclosed" not in line.lower():
            continue
        line_l = line.lower()
        if "육아휴직" in item or "육아휴직" in sub:
            if "육아휴직" in line and "not disclosed" in line_l:
                return True
    return False


def _collect_narrative_candidates(
    text: str,
    plan_row: dict[str, Any],
    *,
    unit_id: str | None,
    logical_doc: str | None,
    min_score: float,
) -> list[RowMatchCandidate]:
    out: list[RowMatchCandidate] = []
    bridge_keys = _bridge_keys_for_question(plan_row)
    question_blob = _question_blob(plan_row)
    item = str(plan_row.get("item") or "")

    def _append_match(raw_val: str, snippet: str, hint: str, unit_hint: str | None = None) -> None:
        if not _narrative_value_ok(raw_val):
            return
        norm_val, norm_unit = _normalize_numeric_unit(raw_val, unit_hint)
        score, reason = score_row_match(hint, plan_row)
        bridge = _semantic_bridge_match(snippet, plan_row) or _semantic_bridge_match(hint, plan_row)
        if bridge:
            score, reason = bridge
        if score < min_score * 0.75:
            return
        ym = YEAR_RE.search(snippet)
        out.append(
            RowMatchCandidate(
                label=snippet.strip()[:120],
                value=raw_val,
                unit=unit_hint,
                year=int(ym.group(1)) if ym else None,
                row_match_score=score,
                row_match_reason=f"narrative_metric:{reason}",
                unit_id=unit_id,
                logical_doc=logical_doc,
                semantic_bridge_used=reason.startswith("semantic_bridge:"),
                bridge_reason=reason if reason.startswith("semantic_bridge:") else None,
                narrative_metric_parse_used=True,
                narrative_parse_reason=f"narrative_pattern:{hint}",
                narrative_confidence=round(score, 3),
                normalized_numeric_value=norm_val,
                normalized_unit=norm_unit,
            )
        )

    for hint, pattern in _narrative_patterns_for(plan_row):
        if bridge_keys and hint not in bridge_keys and hint not in question_blob:
            if hint not in item and hint not in str(plan_row.get("subcategory") or ""):
                continue
        seen_spans: set[tuple[int, int]] = set()
        for line in text.splitlines():
            m = pattern.search(line)
            if not m:
                continue
            if "not disclosed" in m.group(0).lower():
                continue
            groups = m.groups()
            raw_val = groups[0] if groups and groups[0] else m.group(0)
            unit_hint = groups[1] if len(groups) > 1 else None
            _append_match(raw_val, line, hint, unit_hint)
        for m in pattern.finditer(text):
            span = m.span()
            if span in seen_spans:
                continue
            seen_spans.add(span)
            if "not disclosed" in m.group(0).lower():
                continue
            groups = m.groups()
            raw_val = groups[0] if groups and groups[0] else m.group(0)
            unit_hint = groups[1] if len(groups) > 1 else None
            start = max(0, span[0] - 40)
            end = min(len(text), span[1] + 40)
            _append_match(raw_val, text[start:end], hint, unit_hint)

    out.extend(
        _collect_xml_concept_candidates(
            text, plan_row, unit_id=unit_id, logical_doc=logical_doc, min_score=min_score
        )
    )
    return out


def _collect_xml_concept_candidates(
    text: str,
    plan_row: dict[str, Any],
    *,
    unit_id: str | None,
    logical_doc: str | None,
    min_score: float,
) -> list[RowMatchCandidate]:
    from enterprise_docs.registries import load_metric_overlap_registry

    item = str(plan_row.get("item") or "")
    family_id = str(plan_row.get("family_id") or "")
    if not family_id:
        pf = str(plan_row.get("pattern_family") or "")
        if "governance" in pf or "esg_rating" in pf or "materiality" in pf:
            family_id = "governance"
        elif "climate" in pf or "scope" in pf or "environment" in pf:
            family_id = "environment_ghg"
        elif "employee" in pf or "headcount" in pf:
            family_id = "employee_headcount"
    reg = load_metric_overlap_registry()
    out: list[RowMatchCandidate] = []
    for spec in reg.get("xml_concept_patterns") or []:
        if family_id and spec.get("family_id") != family_id:
            continue
        if item not in (spec.get("items") or []):
            continue
        if plan_row.get("kind") == "quantitative" and spec.get("qualitative_only"):
            continue
        hint = str(spec.get("concept_hint") or "")
        if not hint or not re.search(hint, text, re.I):
            continue
        presence = str(spec.get("presence_value") or "present")
        score = max(min_score, 0.5)
        out.append(
            RowMatchCandidate(
                label=f"xml_concept:{hint[:40]}",
                value=presence,
                unit=None,
                year=None,
                row_match_score=score,
                row_match_reason="xml_concept:presence",
                unit_id=unit_id,
                logical_doc=logical_doc,
                narrative_metric_parse_used=True,
                narrative_parse_reason="xml_concept_pattern",
                normalized_numeric_value=presence,
            )
        )
    return out


def _collect_row_candidates_from_text(
    text: str,
    plan_row: dict[str, Any],
    *,
    unit_id: str | None = None,
    logical_doc: str | None = None,
    prefer_years: list[int] | None = None,
    min_score: float = 0.35,
) -> list[RowMatchCandidate]:
    prefer_years = prefer_years or [2025, 2024, 2023, 2022]
    candidates: list[RowMatchCandidate] = []

    if _check_not_disclosed_for_question(text, plan_row):
        return candidates

    from enterprise_docs.cross_role_extraction import (
        enrich_plan_for_cross_role,
        resolve_family_id,
        _collect_cross_role_narrative,
        _collect_cross_role_table,
    )

    plan = enrich_plan_for_cross_role(plan_row)
    family_id = resolve_family_id(plan)
    if family_id:
        candidates.extend(
            _collect_cross_role_table(
                text, plan, family_id=family_id, unit_id=unit_id, logical_doc=logical_doc, min_score=min_score
            )
        )
        candidates.extend(
            _collect_cross_role_narrative(
                text, plan, family_id=family_id, unit_id=unit_id, logical_doc=logical_doc, min_score=min_score
            )
        )
        if candidates:
            return candidates

    if "|" in text and text.count("|") >= 4:
        for header, cells in _parse_md_table_rows(text):
            label = cells[0]
            score, reason = score_row_match(label, plan_row)
            bridge = _semantic_bridge_match(label, plan_row)
            bridge_used = False
            bridge_reason = None
            if bridge and score < bridge[0]:
                score, reason = bridge
                bridge_used = True
                bridge_reason = reason
            if score < min_score:
                continue
            years = _year_columns(header)
            table_unit = cells[-1] if len(cells) == len(header) else (header[-1] if header else None)
            for year in prefer_years:
                for y, idx in years:
                    if y != year or idx >= len(cells):
                        continue
                    val = cells[idx].strip()
                    if val and not NOT_DISCLOSED_RE.search(val):
                        norm_val, norm_unit = _normalize_numeric_unit(val, table_unit)
                        candidates.append(
                            RowMatchCandidate(
                                label=label,
                                value=val,
                                unit=table_unit,
                                year=y,
                                row_match_score=score,
                                row_match_reason=reason,
                                unit_id=unit_id,
                                logical_doc=logical_doc,
                                semantic_bridge_used=bridge_used,
                                bridge_reason=bridge_reason,
                                normalized_numeric_value=norm_val,
                                normalized_unit=norm_unit or table_unit,
                            )
                        )
            if not years and len(cells) >= 2:
                val = cells[1].strip()
                if val and not NOT_DISCLOSED_RE.search(val) and NUMERIC_RE.search(val):
                    candidates.append(
                        RowMatchCandidate(
                            label=label,
                            value=val,
                            unit=table_unit,
                            year=None,
                            row_match_score=score,
                            row_match_reason=reason,
                            unit_id=unit_id,
                            logical_doc=logical_doc,
                            semantic_bridge_used=bridge_used,
                            bridge_reason=bridge_reason,
                        )
                    )

    candidates.extend(
        _collect_narrative_candidates(
            text, plan_row, unit_id=unit_id, logical_doc=logical_doc, min_score=min_score
        )
    )

    return candidates


def extract_from_retrieval(
    plan_row: dict[str, Any],
    retrieval: RetrievalResult,
    *,
    unit_lookup: dict[str, dict[str, Any]] | None = None,
    retrieval_ready: bool = True,
) -> ExtractionResult:
    qid = str(plan_row.get("item_id") or "")
    question = str(plan_row.get("question") or "")

    if plan_row.get("kind") != "quantitative":
        return ExtractionResult(
            question_id=qid,
            success=False,
            fail_stage="extraction_gap",
            extraction_reason="qualitative_not_supported_in_pilot",
        )

    if retrieval.parser_fail:
        return ExtractionResult(
            question_id=qid,
            success=False,
            fail_stage="parser_gap",
            extraction_reason="parser_fail_on_retrieval",
        )

    if not retrieval_ready or not retrieval.top_units:
        return ExtractionResult(
            question_id=qid,
            success=False,
            fail_stage="retrieval_gap",
            extraction_reason="not_single_doc_ready_or_empty_units",
        )

    primary_logical = (plan_row.get("primary_document_ids") or [None])[0]
    all_candidates: list[RowMatchCandidate] = []
    not_disclosed_hit = False

    ordered_units = sorted(
        retrieval.top_units,
        key=lambda u: (
            0 if u.logical_document_id == primary_logical else 1,
            0 if getattr(u, "is_table_unit", False) else 1,
            -u.score,
        ),
    )

    for hit in ordered_units:
        full_text = hit.evidence_text
        if unit_lookup and hit.unit_id in unit_lookup:
            full_text = str(
                unit_lookup[hit.unit_id].get("evidence_text")
                or unit_lookup[hit.unit_id].get("text")
                or full_text
            )
        if _check_not_disclosed_for_question(full_text, plan_row):
            not_disclosed_hit = True
        all_candidates.extend(
            _collect_row_candidates_from_text(
                full_text,
                plan_row,
                unit_id=hit.unit_id,
                logical_doc=hit.logical_document_id,
            )
        )

    if not all_candidates:
        if not_disclosed_hit:
            return ExtractionResult(
                question_id=qid,
                success=False,
                fail_stage="extraction_gap",
                extraction_reason="source_not_disclosed_for_metric",
                selected_unit_ids=[u.unit_id for u in retrieval.top_units[:3]],
            )
        if any(hit.evidence_text.strip() for hit in retrieval.top_units):
            return ExtractionResult(
                question_id=qid,
                success=False,
                fail_stage="extraction_gap",
                extraction_reason="units_retrieved_but_no_parseable_numeric_row",
                selected_unit_ids=[u.unit_id for u in retrieval.top_units[:3]],
            )
        return ExtractionResult(
            question_id=qid,
            success=False,
            fail_stage="parser_gap",
            extraction_reason="empty_unit_text",
        )

    def sort_key(c: RowMatchCandidate) -> tuple:
        primary_bonus = 0 if c.logical_doc == primary_logical else 1
        return (primary_bonus, -c.row_match_score, -(c.year or 0))

    all_candidates.sort(key=sort_key)
    best = all_candidates[0]
    top_preview = [
        {
            "label": c.label,
            "value": c.value,
            "row_match_score": c.row_match_score,
            "row_match_reason": c.row_match_reason,
            "logical_doc": c.logical_doc,
            "semantic_bridge_used": c.semantic_bridge_used,
        }
        for c in all_candidates[:5]
    ]

    risk, risk_reason = _wrong_row_risk(best.label, plan_row, best.row_match_score, best.row_match_reason)
    pred_val = best.normalized_numeric_value or best.value
    pred_unit = best.normalized_unit or _infer_target_unit(question, best.unit)

    ext_conf = round(best.row_match_score, 3)
    if best.narrative_metric_parse_used:
        ext_conf = max(ext_conf, float(best.narrative_confidence or 0.0))

    return ExtractionResult(
        question_id=qid,
        success=True,
        predicted_value=pred_val,
        predicted_unit=pred_unit,
        selected_doc=best.logical_doc,
        selected_unit_ids=[best.unit_id] if best.unit_id else [],
        extraction_reason=f"matched_row:{best.label[:80]}",
        extraction_confidence=ext_conf,
        year_used=best.year,
        raw_snippet=best.label,
        row_match_score=best.row_match_score,
        row_match_reason=best.row_match_reason,
        selected_row_label=best.label,
        top_row_candidates=top_preview,
        wrong_row_risk=risk,
        wrong_row_risk_reason=risk_reason,
        semantic_bridge_used=best.semantic_bridge_used,
        bridge_reason=best.bridge_reason,
        narrative_metric_parse_used=best.narrative_metric_parse_used,
        narrative_parse_reason=best.narrative_parse_reason,
        narrative_confidence=best.narrative_confidence,
        normalized_numeric_value=best.normalized_numeric_value,
        normalized_unit=best.normalized_unit,
    )


def extract_batch(
    plan_rows: list[dict[str, Any]],
    retrievals: dict[str, RetrievalResult],
    *,
    unit_lookup: dict[str, dict[str, Any]] | None = None,
    ready_flags: dict[str, bool] | None = None,
) -> list[ExtractionResult]:
    out: list[ExtractionResult] = []
    for row in plan_rows:
        qid = str(row.get("item_id") or "")
        ret = retrievals.get(qid)
        if not ret:
            out.append(
                ExtractionResult(
                    question_id=qid,
                    success=False,
                    fail_stage="retrieval_gap",
                    extraction_reason="missing_retrieval",
                )
            )
            continue
        ready = (ready_flags or {}).get(qid, True)
        out.append(extract_from_retrieval(row, ret, unit_lookup=unit_lookup, retrieval_ready=ready))
    return out
