"""Family-level generalization view for holdout robustness rounds."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

# Map holdout pattern_family → metric_family_registry family_id (or bucket)
FAMILY_MAP: dict[str, str] = {
    "governance_narrative": "governance",
    "governance_numeric_narrative": "governance",
    "governance_dart": "governance",
    "governance_materiality": "governance",
    "governance_board": "governance",
    "climate_narrative": "environment_ghg",
    "scope_expansion": "environment_ghg",
    "environment_cdp": "environment_ghg",
    "environment_narrative": "environment_ghg",
    "environment_certification": "environment_ghg",
    "environment_esg_grade": "environment_ghg",
    "employee_safety": "employee",
    "employee_hr": "employee",
    "employee_headcount": "employee_headcount",
    "supply_chain": "other",
    "esg_rating_narrative": "governance",
    "report_meta": "other",
    "impact_report_meta": "other",
    "business_narrative": "financial",
    "platform_metric": "employee",
    "esg_report_listing": "other",
    "narrative_esg": "other",
    "financial_narrative": "financial",
}

BUCKET_META: dict[str, dict[str, Any]] = {
    "employee": {"registry_families": ["employee_headcount", "employee_ratio", "hr_welfare"], "scope": "generic"},
    "employee_headcount": {"registry_families": ["employee_headcount"], "scope": "generic"},
    "environment_ghg": {"registry_families": ["environment_ghg"], "scope": "generic"},
    "governance": {"registry_families": ["governance_financial_anchor", "governance_narrative"], "scope": "generic"},
    "financial": {"registry_families": ["financial_en_bridge"], "scope": "generic"},
    "narrative_investment": {"registry_families": ["narrative_investment"], "scope": "pilot_only"},
    "other": {"registry_families": [], "scope": "narrative_only"},
}


def bucket_for_probe(probe: dict[str, Any]) -> str:
    pf = str(probe.get("pattern_family") or probe.get("family_guess") or "other")
    return FAMILY_MAP.get(pf, "other")


def summarize_holdout_by_family(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matrix:
        bucket = bucket_for_probe(row)
        by_family[bucket].append(row)

    families_out: dict[str, Any] = {}
    for bucket, rows in sorted(by_family.items()):
        n = max(1, len(rows))
        readiness = Counter(r.get("readiness_state") or "unknown" for r in rows)
        companies = sorted({r.get("company_id") for r in rows})
        meta = BUCKET_META.get(bucket, BUCKET_META["other"])

        retrieval_rate = sum(1 for r in rows if r.get("retrieval_feasible")) / n
        extraction_rate = sum(1 for r in rows if r.get("extraction_feasible")) / n
        aggregation_rate = sum(1 for r in rows if r.get("aggregation_feasible")) / n

        handoff_ok = readiness.get("single_source_sufficient", 0) + readiness.get(
            "multi_source_sufficient", 0
        ) + readiness.get("aggregation_ready", 0)

        quant_rows = [r for r in rows if r.get("kind") == "quantitative"]
        qn = max(1, len(quant_rows)) if quant_rows else 0
        quant_extraction = (
            sum(1 for r in quant_rows if r.get("extraction_feasible")) / qn if quant_rows else None
        )

        if meta["scope"] == "pilot_only":
            reusability = "pilot_only"
        elif retrieval_rate >= 0.7 and extraction_rate >= 0.5:
            reusability = "reusable_holdout"
        elif retrieval_rate >= 0.5:
            reusability = "retrieval_only"
        else:
            reusability = "weak"

        families_out[bucket] = {
            "probe_count": len(rows),
            "companies": companies,
            "registry_families": meta["registry_families"],
            "scope": meta["scope"],
            "driver": "registry" if meta["registry_families"] and meta["scope"] != "pilot_only" else (
                "code_fallback" if meta["scope"] == "pilot_only" else "narrative_retrieval_only"
            ),
            "parser_ok_rate": round(sum(1 for r in rows if r.get("parser_ok")) / n, 4),
            "retrieval_feasible_rate": round(retrieval_rate, 4),
            "extraction_feasible_rate": round(extraction_rate, 4),
            "aggregation_feasible_rate": round(aggregation_rate, 4),
            "readiness_distribution": dict(readiness),
            "dominant_readiness_state": readiness.most_common(1)[0][0] if readiness else "unknown",
            "reusability_level": reusability,
            "holdout_runs": len(rows) > 0,
            "handoff_candidate": handoff_ok > 0 and meta["scope"] != "pilot_only",
            "quant_extraction_rate": round(quant_extraction, 4) if quant_extraction is not None else None,
            "synthesis_allowed": False,
            "probe_ids": [r.get("probe_id") for r in rows],
        }

    ranked = sorted(
        families_out.items(),
        key=lambda x: (x[1]["retrieval_feasible_rate"], x[1]["extraction_feasible_rate"]),
        reverse=True,
    )
    strongest = ranked[0][0] if ranked else None
    weakest = ranked[-1][0] if ranked else None

    return {
        "families": families_out,
        "strongest_family": strongest,
        "weakest_family": weakest,
        "family_count": len(families_out),
    }
