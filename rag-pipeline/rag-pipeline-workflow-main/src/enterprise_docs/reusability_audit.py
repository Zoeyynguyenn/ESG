"""Reusability audit for enterprise internal-doc rule inventory."""

from __future__ import annotations

from typing import Any

from enterprise_docs.rule_inventory import RULE_DEFINITIONS, RuleClass


def analyze_reusability(
    holdout_rows: list[dict[str, Any]] | None = None,
    *,
    demo_readiness_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    holdout_rows = holdout_rows or []

    by_class: dict[str, list[dict[str, Any]]] = {}
    for rule in RULE_DEFINITIONS:
        by_class.setdefault(str(rule["class"]), []).append(rule)

    reusable = [r for r in RULE_DEFINITIONS if r["class"] == "reusable_generic_rule"]
    pilot = [r for r in RULE_DEFINITIONS if r["class"] == "pilot_only_rule"]
    pattern = [r for r in RULE_DEFINITIONS if r["class"] == "pattern_specific_rule"]
    demo_dep = [r for r in RULE_DEFINITIONS if r.get("demo_company_dependent")]

    holdout_parser_ok = sum(1 for r in holdout_rows if r.get("parser_ok"))
    holdout_retrieval_ok = sum(1 for r in holdout_rows if r.get("retrieval_feasible"))
    holdout_extract_ok = sum(1 for r in holdout_rows if r.get("extraction_feasible"))
    n_hold = max(1, len(holdout_rows))

    reusable_from_holdout = []
    corpus_specific_from_holdout = []
    needs_abstraction = []
    for row in holdout_rows:
        for tag in row.get("reuse_tags") or []:
            if tag.startswith("reusable:"):
                reusable_from_holdout.append(tag)
            elif tag.startswith("corpus_specific:"):
                corpus_specific_from_holdout.append(tag)
            elif tag.startswith("needs_abstraction:"):
                needs_abstraction.append(tag)

    total_rules = len(RULE_DEFINITIONS)
    reusable_coverage = round(len(reusable) / max(1, total_rules), 4)
    pilot_dependency = round(len(pilot) / max(1, total_rules), 4)

    return {
        "lane": "enterprise_internal_doc",
        "rule_count": total_rules,
        "by_class_counts": {k: len(v) for k, v in by_class.items()},
        "reusable_generic_count": len(reusable),
        "pattern_specific_count": len(pattern),
        "pilot_only_count": len(pilot),
        "demo_company_dependent_count": len(demo_dep),
        "reusable_system_coverage": reusable_coverage,
        "pilot_only_dependency": pilot_dependency,
        "productize_candidates": [
            r["rule_id"] for r in RULE_DEFINITIONS if r.get("productize") is True
        ],
        "abstraction_backlog": [
            r["rule_id"] for r in RULE_DEFINITIONS if r.get("productize") not in (True, False)
        ],
        "holdout_sanity": {
            "probe_count": len(holdout_rows),
            "parser_ok_rate": round(holdout_parser_ok / n_hold, 4),
            "retrieval_feasible_rate": round(holdout_retrieval_ok / n_hold, 4),
            "extraction_feasible_rate": round(holdout_extract_ok / n_hold, 4),
            "aggregation_feasible_rate": round(
                sum(1 for r in holdout_rows if r.get("aggregation_feasible")) / n_hold, 4
            ),
            "reusable_signals": sorted(set(reusable_from_holdout)),
            "corpus_specific_signals": sorted(set(corpus_specific_from_holdout)),
            "abstraction_signals": sorted(set(needs_abstraction)),
        },
        "demo_readiness_baseline": demo_readiness_summary,
        "architecture_recommendation": _architecture_recommendation(
            reusable_coverage, holdout_rows, demo_readiness_summary
        ),
    }


def _architecture_recommendation(
    reusable_coverage: float,
    holdout_rows: list[dict[str, Any]],
    demo_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    holdout_retrieval = (
        sum(1 for r in holdout_rows if r.get("retrieval_feasible")) / max(1, len(holdout_rows))
        if holdout_rows
        else 0.0
    )
    quant_synthesis_rate = (demo_summary or {}).get("synthesis_gate_allowed_rate_quant", 0.0)

    expand_holdout = holdout_retrieval >= 0.5 and reusable_coverage >= 0.4
    open_synthesis = quant_synthesis_rate >= 0.6

    return {
        "continue_demo_company_dev": True,
        "expand_to_hanssem_musinsa_holdout": expand_holdout,
        "open_synthesis_yet": open_synthesis,
        "priority_next": (
            "abstraction_rule_registry"
            if reusable_coverage < 0.55
            else "benchmark_harness_holdout_expansion"
        ),
        "weakest_layer": _weakest_layer(holdout_rows, demo_summary),
    }


def _weakest_layer(
    holdout_rows: list[dict[str, Any]],
    demo_summary: dict[str, Any] | None,
) -> str:
    if not holdout_rows:
        return "holdout_not_run"
    rates = {
        "parser": sum(1 for r in holdout_rows if r.get("parser_ok")) / len(holdout_rows),
        "retrieval": sum(1 for r in holdout_rows if r.get("retrieval_feasible")) / len(holdout_rows),
        "extraction": sum(1 for r in holdout_rows if r.get("extraction_feasible")) / len(holdout_rows),
        "aggregation": sum(1 for r in holdout_rows if r.get("aggregation_feasible")) / len(holdout_rows),
    }
    qual_count = (demo_summary or {}).get("qualitative_count", 0)
    if qual_count and qual_count > 0:
        rates["synthesis"] = 0.0
    return min(rates, key=rates.get)  # type: ignore[arg-type]
