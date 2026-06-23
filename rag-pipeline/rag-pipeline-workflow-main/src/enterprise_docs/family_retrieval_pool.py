"""Family-scoped retrieval pools + logical-doc overlap visibility."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from enterprise_docs.doc_mapping import build_logical_to_corpus_map, matching_corpus_documents_for_logical
from enterprise_docs.registries import logical_documents
from enterprise_docs.retrieval_scope_policy import (
    _passes_scope_spec,
    _scope_spec,
    filter_units_by_scope,
    load_retrieval_scope_policy,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "data/enterprise_docs/family_retrieval_pool_policy.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


@lru_cache(maxsize=1)
def load_family_pool_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _pool_applies(pool: dict[str, Any], company_id: str) -> bool:
    companies = pool.get("companies") or []
    return not companies or company_id in companies


def _pool_spec(pool_id: str, pool: dict[str, Any], company_id: str) -> dict[str, Any]:
    if pool.get("scope_ref"):
        return _scope_spec(str(pool["scope_ref"]), company_id)
    spec = {k: v for k, v in pool.items() if k not in ("label", "logical_documents", "companies", "scope_ref")}
    return spec


def filter_units_by_pool(
    units: list[dict[str, Any]],
    pool_id: str,
    *,
    company_id: str,
) -> list[dict[str, Any]]:
    reg = load_family_pool_policy()
    scope_reg = load_retrieval_scope_policy()
    pool = dict((reg.get("pools") or {}).get(pool_id) or {})
    if not pool or not _pool_applies(pool, company_id):
        return []

    spec = _pool_spec(pool_id, pool, company_id)
    cap = int(spec.get("max_units_per_document") or pool.get("max_units_per_document") or 0) or None
    kept: list[dict[str, Any]] = []
    per_doc: Counter[str] = Counter()
    for unit in units:
        if not _passes_scope_spec(unit, spec, scope_reg):
            continue
        doc_id = str(unit.get("document_id") or "")
        if cap and per_doc[doc_id] >= cap:
            continue
        row = dict(unit)
        tags = set(row.get("retrieval_pool_tags") or [])
        tags.add(pool_id)
        row["retrieval_pool_tags"] = sorted(tags)
        kept.append(row)
        per_doc[doc_id] += 1
    return kept


def family_pool_ids(family_id: str, company_id: str) -> list[str]:
    reg = load_family_pool_policy()
    fam = dict((reg.get("families") or {}).get(family_id) or {})
    over = ((reg.get("company_pool_overrides") or {}).get(company_id) or {}).get(family_id) or {}
    if over.get("pool_ids"):
        return list(over["pool_ids"])
    return list(fam.get("pool_ids") or [])


def units_for_family_pool(
    units: list[dict[str, Any]],
    family_id: str,
    company_id: str,
) -> list[dict[str, Any]]:
    """Union of registry pools for a metric family (dedupe by unit_id)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for pool_id in family_pool_ids(family_id, company_id):
        for unit in filter_units_by_pool(units, pool_id, company_id=company_id):
            uid = str(unit.get("unit_id") or "")
            if uid and uid in seen:
                continue
            if uid:
                seen.add(uid)
            out.append(unit)
    return out


def units_for_logical_doc(
    units: list[dict[str, Any]],
    logical_doc_id: str,
    company_id: str,
    *,
    family_id: str | None = None,
) -> list[dict[str, Any]]:
    corpus_ids = sorted({str(u.get("document_id") or "") for u in units})
    matched_ids = matching_corpus_documents_for_logical(
        logical_doc_id, corpus_ids, company_id=company_id, min_score=1.0
    )
    if matched_ids:
        matched_set = set(matched_ids)
        matched = [u for u in units if str(u.get("document_id") or "") in matched_set]
        if matched:
            return matched

    logical_map = build_logical_to_corpus_map(corpus_ids, company_id=company_id)
    mapped = logical_map.get(logical_doc_id)
    if mapped:
        matched = [u for u in units if str(u.get("document_id") or "") == mapped]
        if matched:
            return matched

    reg = load_family_pool_policy()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pool_id, pool in (reg.get("pools") or {}).items():
        lids = pool.get("logical_documents") or []
        if logical_doc_id not in lids:
            continue
        if family_id and pool_id not in family_pool_ids(family_id, company_id):
            continue
        for unit in filter_units_by_pool(units, pool_id, company_id=company_id):
            uid = str(unit.get("unit_id") or "")
            if uid in seen:
                continue
            seen.add(uid)
            out.append(unit)
    return out


def build_family_pool_matrix(
    units_by_company: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    reg = load_family_pool_policy()
    matrix: dict[str, Any] = {"pools": {}, "families": {}}

    for pool_id in (reg.get("pools") or {}):
        matrix["pools"][pool_id] = {}
        for company_id, units in units_by_company.items():
            filtered = filter_units_by_pool(units, pool_id, company_id=company_id)
            matrix["pools"][pool_id][company_id] = {
                "unit_count": len(filtered),
                "document_count": len({u.get("document_id") for u in filtered}),
                "by_source_type": dict(Counter(str(u.get("source_type") or "") for u in filtered)),
            }

    for family_id in PILOT_FAMILIES:
        matrix["families"][family_id] = {}
        for company_id, units in units_by_company.items():
            fam_units = units_for_family_pool(units, family_id, company_id)
            matrix["families"][family_id][company_id] = {
                "pool_ids": family_pool_ids(family_id, company_id),
                "unit_count": len(fam_units),
                "document_count": len({u.get("document_id") for u in fam_units}),
                "by_source_type": dict(Counter(str(u.get("source_type") or "") for u in fam_units)),
            }
    matrix["policy_path"] = str(POLICY_PATH.relative_to(ROOT)).replace("\\", "/")
    return matrix


def measure_probe_logical_overlap(
    probe: dict[str, Any],
    corpus_units: list[dict[str, Any]],
    *,
    company_id: str,
    family_id: str,
    use_family_pool: bool = True,
) -> dict[str, Any]:
    from enterprise_docs.structured_extractor import probe_candidates_in_units

    probe = dict(probe)
    probe.setdefault("company_id", company_id)
    base = (
        units_for_family_pool(corpus_units, family_id, company_id)
        if use_family_pool
        else list(corpus_units)
    )
    docs = logical_documents(company_id)
    by_doc: dict[str, list[dict[str, Any]]] = {}
    values_by_doc: dict[str, set[str]] = {}

    for lid in docs:
        role_units = units_for_logical_doc(base, lid, company_id, family_id=family_id)
        if not role_units:
            continue
        cands = probe_candidates_in_units(probe, role_units[:50], logical_doc=lid, min_score=0.2)
        if cands:
            by_doc[lid] = [c.to_dict() for c in cands[:3]]
            values_by_doc[lid] = {str(c.value) for c in cands if c.value}

    overlap_docs = sorted(by_doc.keys())
    agreeing = 0
    if len(overlap_docs) >= 2:
        vals = [v for v in values_by_doc.values() if v]
        if vals:
            common = set.intersection(*vals) if len(vals) >= 2 else set()
            agreeing = 1 if common else 0

    return {
        "probe_id": probe.get("probe_id"),
        "company_id": company_id,
        "family_id": family_id,
        "item": probe.get("item"),
        "logical_docs_with_candidates": overlap_docs,
        "logical_doc_overlap_count": len(overlap_docs),
        "multi_logical_doc_candidate": len(overlap_docs) >= 2,
        "multi_logical_doc_agreeing_values": bool(agreeing),
        "candidate_preview": {k: v for k, v in list(by_doc.items())[:4]},
    }


def audit_logical_doc_overlap_matrix(
    probes_by_company: dict[str, list[dict[str, Any]]],
    corpus_by_company: dict[str, list[dict[str, Any]]],
    *,
    use_family_pool: bool = True,
) -> dict[str, Any]:
    from enterprise_docs.handoff_readiness import family_for_probe

    rows: list[dict[str, Any]] = []
    by_family: dict[str, list[dict[str, Any]]] = {f: [] for f in PILOT_FAMILIES}

    for company_id, probes in probes_by_company.items():
        corpus = corpus_by_company.get(company_id) or []
        for probe in probes:
            if probe.get("kind") != "quantitative":
                continue
            fid = family_for_probe(probe)
            if fid not in PILOT_FAMILIES:
                continue
            row = measure_probe_logical_overlap(
                probe, corpus, company_id=company_id, family_id=fid, use_family_pool=use_family_pool
            )
            rows.append(row)
            by_family[fid].append(row)

    family_rates: dict[str, Any] = {}
    for fid, fam_rows in by_family.items():
        n = max(1, len(fam_rows))
        multi = sum(1 for r in fam_rows if r.get("multi_logical_doc_candidate"))
        agree = sum(1 for r in fam_rows if r.get("multi_logical_doc_agreeing_values"))
        family_rates[fid] = {
            "quant_probe_count": len(fam_rows),
            "logical_doc_overlap_rate": round(multi / n, 4),
            "multi_doc_agreeing_value_rate": round(agree / n, 4),
            "single_doc_only_rate": round(
                sum(1 for r in fam_rows if r.get("logical_doc_overlap_count") == 1) / n, 4
            ),
            "zero_overlap_rate": round(
                sum(1 for r in fam_rows if r.get("logical_doc_overlap_count") == 0) / n, 4
            ),
        }

    all_quant = [r for r in rows if r.get("logical_doc_overlap_count") is not None]
    n_all = max(1, len(all_quant))
    return {
        "rows": rows,
        "by_family": family_rates,
        "aggregate": {
            "logical_doc_overlap_rate": round(
                sum(1 for r in all_quant if r.get("multi_logical_doc_candidate")) / n_all, 4
            ),
            "multi_doc_agreeing_value_rate": round(
                sum(1 for r in all_quant if r.get("multi_logical_doc_agreeing_values")) / n_all, 4
            ),
        },
        "use_family_pool": use_family_pool,
    }


def write_family_scoped_corpus(
    company_id: str,
    units: list[dict[str, Any]],
    *,
    output: Path | None = None,
) -> dict[str, Any]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    by_family: dict[str, int] = {}
    for fid in PILOT_FAMILIES:
        fam_units = units_for_family_pool(units, fid, company_id)
        by_family[fid] = len(fam_units)
        for unit in fam_units:
            uid = str(unit.get("unit_id") or "")
            if uid in seen:
                continue
            seen.add(uid)
            merged.append(unit)

    out = output or (ROOT / f"data/enterprise_docs/{company_id}/corpus_units_family_scoped.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "company_id": company_id,
        "input_units": len(units),
        "output_units": len(merged),
        "document_count": len({u.get("document_id") for u in merged}),
        "by_family_pool_units": by_family,
        "output": str(out.relative_to(ROOT)).replace("\\", "/"),
        "status": "ok" if merged else "empty",
    }
    (out.parent / "family_scoped_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary
