"""Family-scoped cross-role extraction — bypass company filter for capability / cross-doc alignment."""

from __future__ import annotations

import re
from typing import Any

from enterprise_docs.family_generalization import BUCKET_META
from enterprise_docs.registries import load_metric_family_registry
from enterprise_docs.structured_extractor import RowMatchCandidate, score_row_match
from enterprise_docs.value_equivalence import load_equivalence_registry


def resolve_family_id(plan_row: dict[str, Any]) -> str | None:
    fid = plan_row.get("family_id")
    if fid:
        return str(fid)
    pf = str(plan_row.get("pattern_family") or "")
    if pf in ("environment_ghg", "governance", "employee_headcount"):
        return pf
    from enterprise_docs.family_generalization import FAMILY_MAP

    return FAMILY_MAP.get(pf)


def _registry_family_ids(family_id: str) -> list[str]:
    meta = BUCKET_META.get(family_id) or {}
    ids = list(meta.get("registry_families") or [])
    if not ids:
        return [family_id]
    return ids


def _family_entries(family_id: str) -> list[dict[str, Any]]:
    reg = load_metric_family_registry()
    target_ids = set(_registry_family_ids(family_id))
    return [f for f in reg.get("families") or [] if str(f.get("family_id") or "") in target_ids]


def cross_role_row_aliases(family_id: str) -> dict[str, list[str]]:
    reg = load_equivalence_registry()
    out: dict[str, list[str]] = {}
    for item_key, aliases in ((reg.get("metric_item_aliases") or {}).get(family_id) or {}).items():
        out[item_key] = list(aliases)
    for family in _family_entries(family_id):
        for item_key, aliases in (family.get("row_aliases") or {}).items():
            existing = out.setdefault(item_key, [])
            for a in aliases or []:
                if a not in existing:
                    existing.append(a)
    return out


def cross_role_semantic_bridge(family_id: str) -> dict[str, list[str]]:
    reg = load_equivalence_registry()
    out: dict[str, list[str]] = {}
    for item_key, aliases in ((reg.get("semantic_equivalence") or {}).get(family_id) or {}).items():
        out[item_key] = list(aliases)
    for family in _family_entries(family_id):
        for item_key, aliases in (family.get("semantic_bridge") or {}).items():
            existing = out.setdefault(item_key, [])
            for a in aliases or []:
                if a not in existing:
                    existing.append(a)
    return out


def cross_role_label_phrases(family_id: str, item: str) -> list[str]:
    reg = load_equivalence_registry()
    phrases: list[str] = []
    if item:
        phrases.append(item)
    phrases.extend((reg.get("label_match_phrases") or {}).get(family_id, {}).get(item) or [])
    aliases = cross_role_row_aliases(family_id).get(item) or []
    phrases.extend(aliases)
    bridge = cross_role_semantic_bridge(family_id).get(item) or []
    phrases.extend(bridge)
    seen: set[str] = set()
    out: list[str] = []
    for p in phrases:
        pn = re.sub(r"\s+", " ", (p or "").strip().lower())
        if pn and pn not in seen:
            seen.add(pn)
            out.append(p)
    return out


def _compile_cross_role_patterns(family_id: str, item: str) -> list[tuple[str, re.Pattern[str], dict[str, Any]]]:
    reg = load_equivalence_registry()
    compiled: list[tuple[str, re.Pattern[str], dict[str, Any]]] = []
    seen: set[str] = set()
    reg_patterns = (reg.get("cross_role_narrative_patterns") or {}).get(family_id) or []
    has_item_registry = bool(
        item and any(item in (sp.get("items") or []) for sp in reg_patterns)
    )

    for spec in reg_patterns:
        items = spec.get("items") or []
        if item and item not in items:
            continue
        pattern = str(spec.get("pattern") or "")
        label = str(spec.get("label") or "")
        if not pattern or pattern in seen:
            continue
        seen.add(pattern)
        flags = re.IGNORECASE if spec.get("ignore_case", True) else 0
        compiled.append((label, re.compile(pattern, flags), dict(spec)))

    if has_item_registry:
        return compiled

    for family in _family_entries(family_id):
        for entry in family.get("narrative_patterns") or []:
            label = str(entry.get("label") or "")
            if item and label and label != item:
                aliases = cross_role_row_aliases(family_id).get(item) or []
                if label not in aliases and item not in label:
                    continue
            pattern = str(entry.get("pattern") or "")
            if not pattern or pattern in seen:
                continue
            seen.add(pattern)
            flags = re.IGNORECASE if entry.get("ignore_case", True) else 0
            compiled.append((label, re.compile(pattern, flags), {"value_group": 1}))

    return compiled


def _value_ok(raw: str, *, qualitative: bool = False) -> bool:
    if not raw or not str(raw).strip():
        return qualitative
    s = str(raw).strip()
    if qualitative:
        return True
    return bool(re.search(r"\d", s) or re.fullmatch(r"[A-Z][+]?", s, re.I))


def _text_matches_item(text: str, family_id: str, item: str) -> bool:
    text_l = text.lower()
    for phrase in cross_role_label_phrases(family_id, item):
        if phrase.lower() in text_l:
            return True
    return False


def _cross_role_bridge_match(text: str, plan_row: dict[str, Any], family_id: str) -> tuple[float, str] | None:
    item = str(plan_row.get("item") or "")
    text_l = re.sub(r"\s+", " ", text.lower())
    for phrase in cross_role_label_phrases(family_id, item):
        pn = phrase.lower()
        if pn and pn in text_l:
            return 0.88, f"cross_role_label:{phrase[:40]}"
    bridge = cross_role_semantic_bridge(family_id)
    for key, aliases in bridge.items():
        if key != item and item not in key:
            continue
        for alias in aliases:
            an = alias.lower()
            if an and an in text_l:
                return 0.87, f"cross_role_bridge:{alias[:40]}"
    return None


def _collect_cross_role_narrative(
    text: str,
    plan_row: dict[str, Any],
    *,
    family_id: str,
    unit_id: str | None,
    logical_doc: str | None,
    min_score: float,
) -> list[RowMatchCandidate]:
    item = str(plan_row.get("item") or "")
    out: list[RowMatchCandidate] = []
    patterns = _compile_cross_role_patterns(family_id, item)

    for label, pattern, spec in patterns:
        qualitative = bool(spec.get("qualitative_value"))
        value_group = int(spec.get("value_group") or 0)
        for m in pattern.finditer(text):
            snippet = m.group(0)
            if spec.get("not_disclosed"):
                out.append(
                    RowMatchCandidate(
                        label=label,
                        value="Not disclosed",
                        unit=None,
                        year=None,
                        row_match_score=max(min_score, 0.55),
                        row_match_reason="cross_role:not_disclosed",
                        unit_id=unit_id,
                        logical_doc=logical_doc,
                        narrative_metric_parse_used=True,
                        narrative_parse_reason=f"cross_role:{label}",
                    )
                )
                continue
            groups = m.groups()
            raw_val = ""
            if groups and value_group and value_group <= len(groups):
                raw_val = str(groups[value_group - 1] or "")
            elif groups and groups[0]:
                raw_val = str(groups[0])
            elif qualitative and spec.get("qualitative_value"):
                raw_val = str(spec.get("qualitative_value"))
            else:
                raw_val = snippet.strip()

            if "thousand" in snippet.lower() or label == "GHG thousand EN":
                try:
                    raw_val = str(int(float(str(raw_val).replace(",", "")) * 1000))
                except ValueError:
                    pass

            if not _value_ok(raw_val, qualitative=qualitative or bool(spec.get("qualitative_value"))):
                continue

            score, reason = score_row_match(label, plan_row)
            bridge = _cross_role_bridge_match(snippet, plan_row, family_id)
            if bridge and bridge[0] > score:
                score, reason = bridge
            if score < min_score * 0.65 and not bridge:
                if _text_matches_item(text, family_id, item):
                    score, reason = 0.82, "cross_role:item_context"
                else:
                    continue

            ym = re.search(r"\b(20\d{2})\b", snippet)
            out.append(
                RowMatchCandidate(
                    label=snippet.strip()[:120],
                    value=raw_val,
                    unit=None,
                    year=int(ym.group(1)) if ym else None,
                    row_match_score=score,
                    row_match_reason=f"cross_role:{reason}",
                    unit_id=unit_id,
                    logical_doc=logical_doc,
                    semantic_bridge_used=reason.startswith(("semantic_bridge:", "cross_role_bridge:")),
                    bridge_reason=reason if "bridge" in reason else None,
                    narrative_metric_parse_used=True,
                    narrative_parse_reason=f"cross_role:{label}",
                    narrative_confidence=round(score, 3),
                    normalized_numeric_value=raw_val.replace(",", ""),
                )
            )
    return out


def _collect_cross_role_table(
    text: str,
    plan_row: dict[str, Any],
    *,
    family_id: str,
    unit_id: str | None,
    logical_doc: str | None,
    min_score: float,
) -> list[RowMatchCandidate]:
    from enterprise_docs.structured_extractor import _parse_md_table_rows

    item = str(plan_row.get("item") or "")
    out: list[RowMatchCandidate] = []
    if "|" not in text or text.count("|") < 4:
        return out

    for header, cells in _parse_md_table_rows(text):
        label = cells[0]
        score, reason = score_row_match(label, plan_row)
        bridge = _cross_role_bridge_match(label, plan_row, family_id)
        if bridge and bridge[0] > score:
            score, reason = bridge
        if score < min_score and not _text_matches_item(label, family_id, item):
            for phrase in cross_role_label_phrases(family_id, item):
                if phrase.lower() in label.lower():
                    score, reason = 0.85, f"cross_role_table:{phrase[:30]}"
                    break
        if score < min_score:
            continue
        val = cells[1].strip() if len(cells) >= 2 else ""
        if val and "not disclosed" not in val.lower():
            out.append(
                RowMatchCandidate(
                    label=label,
                    value=val,
                    unit=cells[-1] if len(cells) == len(header) else None,
                    year=None,
                    row_match_score=score,
                    row_match_reason=f"cross_role_table:{reason}",
                    unit_id=unit_id,
                    logical_doc=logical_doc,
                    normalized_numeric_value=val.replace(",", ""),
                )
            )
    return out


def enrich_plan_for_cross_role(plan_row: dict[str, Any]) -> dict[str, Any]:
    """Attach family_id for downstream extraction without mutating caller dict."""
    row = dict(plan_row)
    fid = resolve_family_id(row)
    if fid:
        row["family_id"] = fid
    return row


def probe_candidates_cross_role(
    plan_row: dict[str, Any],
    units: list[dict[str, Any]],
    *,
    logical_doc: str | None = None,
    min_score: float = 0.1,
) -> list[RowMatchCandidate]:
    """Family-scoped candidate extraction for cross-document alignment."""
    from enterprise_docs.narrative_table_fusion import filter_candidates_for_plan_item

    plan = enrich_plan_for_cross_role(plan_row)
    family_id = resolve_family_id(plan)
    if not family_id:
        from enterprise_docs.structured_extractor import probe_candidates_in_units

        return probe_candidates_in_units(plan, units, logical_doc=logical_doc, min_score=min_score)

    out: list[RowMatchCandidate] = []
    for u in units:
        uid = str(u.get("unit_id") or "")
        text = str(u.get("evidence_text") or u.get("text") or "")
        if not text.strip():
            continue
        out.extend(
            _collect_cross_role_table(
                text, plan, family_id=family_id, unit_id=uid, logical_doc=logical_doc, min_score=min_score
            )
        )
        out.extend(
            _collect_cross_role_narrative(
                text, plan, family_id=family_id, unit_id=uid, logical_doc=logical_doc, min_score=min_score
            )
        )
    return filter_candidates_for_plan_item(out, plan, min_score=min_score)


def alignment_failure_summary(
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize why constructed cross-role cases fail alignment."""
    rows = []
    for r in case_results:
        if r.get("case_origin") != "constructed":
            continue
        if r.get("extract_alignment_ok") is None:
            continue
        expected = {}
        tags = r.get("capability_tags") or []
        mismatch = "unknown"
        extract = r.get("extract_per_doc") or {}
        if not r.get("extract_alignment_ok"):
            for doc, exp in expected.items() if (expected := {}) else []:
                pass
            failed_docs = [d for d, ok in extract.items() if not ok]
            if failed_docs:
                cid = str(r.get("case_id") or "")
                if "SCOPE3" in cid or "scope" in str(r.get("item") or "").lower():
                    mismatch = "en_kr_label"
                elif "GRADE" in cid or "등급" in str(r.get("item") or ""):
                    mismatch = "grade_normalization"
                elif "BOARD" in cid or "이사회" in str(r.get("item") or ""):
                    mismatch = "governance_numeric_form"
                elif "NARRATIVE-VS-TABLE" in cid or "총 온실가스" in str(r.get("item") or ""):
                    mismatch = "narrative_vs_table"
                elif "NOTDISC" in cid:
                    mismatch = "not_disclosed_vs_numeric"
                else:
                    mismatch = "cross_role_generic"
        rows.append(
            {
                "case_id": r.get("case_id"),
                "family_id": r.get("family_id"),
                "item": r.get("item"),
                "extract_per_doc": extract,
                "extract_alignment_ok": r.get("extract_alignment_ok"),
                "fusion_ok": r.get("fusion_ok"),
                "mismatch_type": mismatch if not r.get("extract_alignment_ok") else "none",
                "capability_tags": tags,
            }
        )
    return {"cases": rows, "by_mismatch_type": _count_mismatch(rows)}


def _count_mismatch(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        if not r.get("extract_alignment_ok"):
            key = str(r.get("mismatch_type") or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return counts
