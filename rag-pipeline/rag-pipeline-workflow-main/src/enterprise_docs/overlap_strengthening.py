"""Overlap strengthening — registry bridges, pair matrix, system overlap metrics."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from enterprise_docs.family_retrieval_pool import (
    PILOT_FAMILIES,
    audit_logical_doc_overlap_matrix,
    measure_probe_logical_overlap,
    units_for_family_pool,
    units_for_logical_doc,
)
from enterprise_docs.registries import load_metric_overlap_registry

ROOT = Path(__file__).resolve().parents[2]
OVERLAP_REGISTRY_PATH = ROOT / "data/enterprise_docs/metric_overlap_registry.json"
PRIOR_ARTIFACT = (
    ROOT / "reports/enterprise_docs_family_scoped_retrieval_20260619-094309/summary.json"
)


@lru_cache(maxsize=1)
def load_overlap_registry() -> dict[str, Any]:
    if OVERLAP_REGISTRY_PATH.exists():
        return json.loads(OVERLAP_REGISTRY_PATH.read_text(encoding="utf-8"))
    return load_metric_overlap_registry()


from enterprise_docs.value_equivalence import canonical_metric_value, values_equivalent


def pair_bridge_aliases(
    family_id: str,
    logical_doc_id: str,
    company_id: str | None = None,
) -> dict[str, list[str]]:
    reg = load_overlap_registry()
    fam = ((reg.get("pair_bridge_aliases") or {}).get(family_id) or {}).get(logical_doc_id) or {}
    out: dict[str, list[str]] = {}
    for k, v in fam.items():
        out[k] = list(v)
    return out


def logical_doc_pairs_for_family(family_id: str) -> list[dict[str, Any]]:
    reg = load_overlap_registry()
    return list((reg.get("logical_doc_pairs") or {}).get(family_id) or [])


def source_limitation(company_id: str, family_id: str) -> dict[str, Any]:
    reg = load_overlap_registry()
    return dict(
        ((reg.get("source_limitations") or {}).get(company_id) or {}).get(family_id) or {}
    )


def measure_probe_overlap_enhanced(
    probe: dict[str, Any],
    corpus_units: list[dict[str, Any]],
    *,
    company_id: str,
    family_id: str,
    use_family_pool: bool = True,
) -> dict[str, Any]:
    """Overlap row with canonical value agreement + candidate overlap."""
    row = measure_probe_logical_overlap(
        probe, corpus_units, company_id=company_id, family_id=family_id, use_family_pool=use_family_pool
    )
    item = str(probe.get("item") or "")
    preview = row.get("candidate_preview") or {}
    canonical_by_doc: dict[str, set[str]] = {}
    for lid, cands in preview.items():
        canonical_by_doc[lid] = {
            str(canonical_metric_value(c.get("value"), item=item, family_id=family_id) or "")
            for c in cands
            if c.get("value")
        }
        canonical_by_doc[lid].discard("")

    overlap_docs = [lid for lid, vals in canonical_by_doc.items() if vals]
    agreeing_pairs: list[tuple[str, str]] = []
    docs = sorted(overlap_docs)
    for i, a in enumerate(docs):
        for b in docs[i + 1 :]:
            va, vb = canonical_by_doc.get(a) or set(), canonical_by_doc.get(b) or set()
            if va & vb:
                agreeing_pairs.append((a, b))

    row["candidate_overlap_rate"] = 1.0 if len(overlap_docs) >= 2 else 0.0
    row["canonical_values_by_doc"] = {k: sorted(v) for k, v in canonical_by_doc.items()}
    row["agreeing_logical_doc_pairs"] = [list(p) for p in agreeing_pairs]
    row["multi_logical_doc_agreeing_values"] = len(agreeing_pairs) > 0
    row["single_source_only"] = len(overlap_docs) == 1
    row["zero_overlap"] = len(overlap_docs) == 0
    return row


def compute_overlap_system_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(1, len(rows))
    return {
        "probe_count": len(rows),
        "logical_doc_overlap_rate": round(
            sum(1 for r in rows if r.get("multi_logical_doc_candidate")) / n, 4
        ),
        "candidate_overlap_rate": round(
            sum(1 for r in rows if r.get("candidate_overlap_rate", 0) >= 1) / n, 4
        ),
        "multi_doc_agreeing_value_rate": round(
            sum(1 for r in rows if r.get("multi_logical_doc_agreeing_values")) / n, 4
        ),
        "single_source_only_rate": round(
            sum(1 for r in rows if r.get("single_source_only")) / n, 4
        ),
        "zero_overlap_rate": round(sum(1 for r in rows if r.get("zero_overlap")) / n, 4),
    }


def audit_overlap_by_family_company(
    probes_by_company: dict[str, list[dict[str, Any]]],
    corpus_by_company: dict[str, list[dict[str, Any]]],
    *,
    use_family_pool: bool = True,
) -> dict[str, Any]:
    from enterprise_docs.handoff_readiness import family_for_probe

    rows: list[dict[str, Any]] = []
    by_family: dict[str, list[dict[str, Any]]] = {f: [] for f in PILOT_FAMILIES}
    by_company: dict[str, list[dict[str, Any]]] = {}

    for company_id, probes in probes_by_company.items():
        corpus = corpus_by_company.get(company_id) or []
        by_company[company_id] = []
        for probe in probes:
            if probe.get("kind") != "quantitative":
                continue
            fid = family_for_probe(probe)
            if fid not in PILOT_FAMILIES:
                continue
            row = measure_probe_overlap_enhanced(
                probe, corpus, company_id=company_id, family_id=fid, use_family_pool=use_family_pool
            )
            row["source_limitation"] = source_limitation(company_id, fid)
            rows.append(row)
            by_family[fid].append(row)
            by_company[company_id].append(row)

    family_rates = {fid: compute_overlap_system_metrics(fam_rows) for fid, fam_rows in by_family.items()}
    company_rates = {cid: compute_overlap_system_metrics(crows) for cid, crows in by_company.items()}
    return {
        "rows": rows,
        "by_family": family_rates,
        "by_company": company_rates,
        "aggregate": compute_overlap_system_metrics(rows),
        "use_family_pool": use_family_pool,
    }


def audit_logical_doc_pair_matrix(
    probes_by_company: dict[str, list[dict[str, Any]]],
    corpus_by_company: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    from enterprise_docs.handoff_readiness import family_for_probe
    from enterprise_docs.structured_extractor import probe_candidates_in_units

    reg = load_overlap_registry()
    matrix: dict[str, Any] = {"families": {}, "pairs": []}

    for family_id in PILOT_FAMILIES:
        matrix["families"][family_id] = {"pairs": []}
        for pair_spec in logical_doc_pairs_for_family(family_id):
            pair_id = str(pair_spec.get("pair_id") or "")
            lids = list(pair_spec.get("logical_docs") or [])
            pair_row: dict[str, Any] = {
                "pair_id": pair_id,
                "family_id": family_id,
                "logical_docs": lids,
                "label": pair_spec.get("label"),
                "by_company": {},
            }
            for company_id, probes in probes_by_company.items():
                corpus = corpus_by_company.get(company_id) or []
                base = units_for_family_pool(corpus, family_id, company_id)
                probe_hits = 0
                agreeing = 0
                candidate_overlap = 0
                quant = 0
                for probe in probes:
                    if probe.get("kind") != "quantitative":
                        continue
                    if family_for_probe(probe) != family_id:
                        continue
                    quant += 1
                    item = str(probe.get("item") or "")
                    docs_with: dict[str, list] = {}
                    for lid in lids:
                        role_units = units_for_logical_doc(base, lid, company_id, family_id=family_id)
                        cands = probe_candidates_in_units(
                            probe, role_units[:60], logical_doc=lid, min_score=0.15
                        )
                        if cands:
                            docs_with[lid] = cands
                    if len(docs_with) >= 2:
                        candidate_overlap += 1
                    if len(docs_with) >= 2:
                        vals = [
                            canonical_metric_value(c.value, item=item, family_id=family_id)
                            for cands in docs_with.values()
                            for c in cands[:2]
                            if c.value
                        ]
                        vals = [v for v in vals if v]
                        if len(set(vals)) == 1 and vals:
                            agreeing += 1
                            probe_hits += 1
                    elif len(docs_with) == 1:
                        pass
                n = max(1, quant)
                pair_row["by_company"][company_id] = {
                    "quant_probe_count": quant,
                    "candidate_overlap_rate": round(candidate_overlap / n, 4),
                    "agreeing_value_rate": round(agreeing / n, 4),
                    "source_limitation": source_limitation(company_id, family_id),
                }
            matrix["families"][family_id]["pairs"].append(pair_row)
            matrix["pairs"].append(pair_row)
    matrix["registry_path"] = str(OVERLAP_REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/")
    return matrix


def write_overlap_ready_corpus(
    company_id: str,
    units: list[dict[str, Any]],
    *,
    output: Path | None = None,
) -> dict[str, Any]:
    """Tag filtered units with overlap-ready pool metadata (union of family pools)."""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for fid in PILOT_FAMILIES:
        for unit in units_for_family_pool(units, fid, company_id):
            uid = str(unit.get("unit_id") or "")
            if uid in seen:
                continue
            seen.add(uid)
            row = dict(unit)
            tags = set(row.get("overlap_ready_tags") or [])
            tags.add("overlap_ready")
            tags.add(f"family:{fid}")
            row["overlap_ready_tags"] = sorted(tags)
            merged.append(row)

    out = output or (ROOT / f"data/enterprise_docs/{company_id}/corpus_units_overlap_ready.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "company_id": company_id,
        "input_units": len(units),
        "output_units": len(merged),
        "document_count": len({u.get("document_id") for u in merged}),
        "output": str(out.relative_to(ROOT)).replace("\\", "/"),
        "status": "ok" if merged else "empty",
    }
    (out.parent / "overlap_ready_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def registry_snapshot() -> dict[str, Any]:
    reg = load_overlap_registry()
    return {
        "path": str(OVERLAP_REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "version": reg.get("version"),
        "logical_doc_pair_count": sum(len(v) for v in (reg.get("logical_doc_pairs") or {}).values()),
        "canonical_key_families": list((reg.get("metric_canonical_keys") or {}).keys()),
        "source_limitations": reg.get("source_limitations"),
        "cross_doc_value_equivalence_keys": list((reg.get("cross_doc_value_equivalence") or {}).keys()),
    }
