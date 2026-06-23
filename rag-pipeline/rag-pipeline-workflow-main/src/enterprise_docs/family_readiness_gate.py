"""Family-level readiness gate with handoff likelihood heuristics."""

from __future__ import annotations

from typing import Any


def _quant_ratio(rows: list[dict[str, Any]]) -> float:
    quant = [r for r in rows if r.get("kind") == "quantitative"]
    if not quant:
        return 0.0
    return sum(1 for r in quant if r.get("extraction_feasible")) / len(quant)


def _handoff_likelihood(spec: dict[str, Any], *, quant_extraction: float) -> str:
    """Heuristic likelihood — not a production handoff gate."""
    if spec.get("scope") == "pilot_only":
        return "none"
    ext = spec.get("extraction_feasible_rate", 0.0)
    ret = spec.get("retrieval_feasible_rate", 0.0)
    probes = spec.get("probe_count", 0)
    companies = len(spec.get("companies") or [])
    tier = spec.get("reusability_level")

    if ext >= 0.6 and ret >= 0.8 and probes >= 3 and companies >= 2 and quant_extraction >= 0.6:
        return "high"
    if ext >= 0.5 and ret >= 0.7 and probes >= 2 and quant_extraction >= 0.5:
        return "medium"
    if ext >= 0.35 and ret >= 0.6:
        return "low"
    if tier == "reusable_holdout" and ext >= 0.45:
        return "low"
    return "none"


def build_family_readiness_gate(
    family_view: dict[str, Any],
    matrix: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Augment family summary with quant-only rates and handoff likelihood."""
    matrix = matrix or []
    by_bucket: dict[str, list[dict[str, Any]]] = {}
    for row in matrix:
        from enterprise_docs.family_generalization import bucket_for_probe

        by_bucket.setdefault(bucket_for_probe(row), []).append(row)

    families_in = family_view.get("families") or {}
    gated: dict[str, Any] = {}
    ranked_handoff: list[tuple[str, str, float]] = []

    for bucket, spec in sorted(families_in.items()):
        rows = by_bucket.get(bucket, [])
        quant_rows = [r for r in rows if r.get("kind") == "quantitative"]
        qual_rows = [r for r in rows if r.get("kind") != "quantitative"]
        qn = max(1, len(quant_rows))
        qual_n = max(1, len(qual_rows)) if qual_rows else 0

        quant_retrieval = (
            sum(1 for r in quant_rows if r.get("retrieval_feasible")) / qn if quant_rows else None
        )
        quant_extraction = (
            sum(1 for r in quant_rows if r.get("extraction_feasible")) / qn if quant_rows else None
        )
        qual_extraction = (
            sum(1 for r in qual_rows if r.get("extraction_feasible")) / qual_n if qual_rows else None
        )

        entry = dict(spec)
        entry["quantitative_probe_count"] = len(quant_rows)
        entry["qualitative_probe_count"] = len(qual_rows)
        entry["quant_retrieval_rate"] = round(quant_retrieval, 4) if quant_retrieval is not None else None
        entry["quant_extraction_rate"] = round(quant_extraction, 4) if quant_extraction is not None else None
        entry["qual_extraction_rate"] = round(qual_extraction, 4) if qual_rows else None
        entry["handoff_candidate_likelihood"] = _handoff_likelihood(
            entry, quant_extraction=quant_extraction or 0.0
        )
        entry["near_handoff"] = entry["handoff_candidate_likelihood"] in ("medium", "high")
        gated[bucket] = entry

        if entry["handoff_candidate_likelihood"] != "none":
            ranked_handoff.append(
                (bucket, entry["handoff_candidate_likelihood"], entry.get("quant_extraction_rate") or 0.0)
            )

    ranked_handoff.sort(key=lambda x: ({"high": 3, "medium": 2, "low": 1}.get(x[1], 0), x[2]), reverse=True)
    nearest = ranked_handoff[0][0] if ranked_handoff else None

    return {
        "version": "1.0.0",
        "description": "Family-level readiness gate — heuristic handoff likelihood, not production gate",
        "families": gated,
        "nearest_handoff_family": nearest,
        "handoff_ready_families": [b for b, lik, _ in ranked_handoff if lik == "high"],
        "strongest_family": family_view.get("strongest_family"),
        "weakest_family": family_view.get("weakest_family"),
        "notes": (
            "handoff_candidate_likelihood uses quant extraction + probe breadth; "
            "qualitative probes excluded from quant_extraction_rate"
        ),
    }
