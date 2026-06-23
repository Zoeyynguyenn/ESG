"""Family-level cross-document extraction surface audit."""

from __future__ import annotations

from collections import Counter
from typing import Any

from enterprise_docs.holdout_harness import load_corpus_for_company
from enterprise_docs.registries import logical_documents
from enterprise_docs.structured_extractor import probe_candidates_in_units

PILOT_FAMILIES = ("environment_ghg", "governance", "employee_headcount")


def _logical_overlap(company_id: str, corpus_units: list[dict[str, Any]]) -> dict[str, Any]:
    corpus_ids = sorted({str(u.get("document_id") or "") for u in corpus_units})
    from enterprise_docs.doc_mapping import build_logical_to_corpus_map

    logical_map = build_logical_to_corpus_map(corpus_ids, company_id=company_id)
    docs = logical_documents(company_id)
    return {
        "logical_documents": list(docs.keys()),
        "mapped_logical_docs": logical_map,
        "unmapped_logical_docs": [lid for lid in docs if lid not in logical_map],
        "corpus_document_count": len(corpus_ids),
    }


def audit_family_crossdoc_surface(
    *,
    company_ids: list[str],
    probe_paths: dict[str, str],
    use_reingested: bool,
) -> dict[str, Any]:
    """Measure extraction candidate overlap across logical docs per family."""
    by_family: dict[str, Any] = {}
    by_company: dict[str, Any] = {}

    for company_id in company_ids:
        corpus = load_corpus_for_company(company_id, use_reingested=use_reingested)
        overlap = _logical_overlap(company_id, corpus)
        by_company[company_id] = {
            **overlap,
            "corpus_units": len(corpus),
            "by_source_type": dict(Counter(str(u.get("source_type") or "unknown") for u in corpus)),
        }

        import json
        from pathlib import Path

        probe_path = Path(probe_paths.get(company_id, ""))
        if not probe_path.exists():
            continue
        probes = [json.loads(line) for line in probe_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        for fid in PILOT_FAMILIES:
            fam_probes = [p for p in probes if p.get("kind") == "quantitative"]
            from enterprise_docs.handoff_readiness import family_for_probe

            fam_probes = [p for p in fam_probes if family_for_probe(p) == fid]
            logical_hits: Counter[str] = Counter()
            multi_doc_probes = 0
            for probe in fam_probes:
                probe.setdefault("company_id", company_id)
                cands = probe_candidates_in_units(probe, corpus[:200], min_score=0.2)
                docs = {c.logical_doc for c in cands if c.logical_doc}
                for d in docs:
                    logical_hits[d] += 1
                if len(docs) >= 2:
                    multi_doc_probes += 1
            key = f"{company_id}::{fid}"
            by_family[key] = {
                "company_id": company_id,
                "family_id": fid,
                "quant_probe_count": len(fam_probes),
                "logical_docs_with_candidates": dict(logical_hits),
                "multi_logical_doc_probe_count": multi_doc_probes,
                "logical_doc_overlap": len(logical_hits),
            }

    return {
        "holdout_corpus": "reingested" if use_reingested else "baseline",
        "by_company": by_company,
        "by_family_company": by_family,
        "pilot_families": list(PILOT_FAMILIES),
    }
