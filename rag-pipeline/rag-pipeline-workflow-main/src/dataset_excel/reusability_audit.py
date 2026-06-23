"""Reusability diagnostic view: reusable_system_coverage vs company_specific_dependency."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from dataset_excel.rule_registry import FAMILY_SPECS, RULE_INVENTORY

# Rule IDs counted toward reusable vs company-specific buckets (qualitative, evidence-based).
REUSABLE_RULE_IDS = {
    r["rule_id"]
    for r in RULE_INVENTORY
    if r["class"] in ("reusable_generic_rule", "pattern_specific_rule")
}
COMPANY_SPECIFIC_RULE_IDS = {r["rule_id"] for r in RULE_INVENTORY if r["class"] == "company_specific_rule"}
EXCEPTION_RULE_IDS = {r["rule_id"] for r in RULE_INVENTORY if r["class"] == "semantic_or_coverage_exception"}

# Families primarily driven by reusable pattern rules (not company tuning).
REUSABLE_FAMILIES = {
    "employee_status",
    "executive_diversity",
    "board_director",
    "financial_revenue",
    "financial_capex",
    "financial_interest",
    "financial_generic",
    "sanction_safetykorea",
    "sanction_pipc",
    "minimum_wage",
}

COMPANY_TUNED_FAMILIES = {
    "fair_trade_sanction",  # FTC blocked + zero assumption tuned on goldns
    "financial_tax",  # semantic ambiguity cases on both companies
}


def analyze_reusability(
    results: list[dict[str, Any]],
    *,
    baseline_metrics: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build diagnostic view without changing v5 metric definitions."""
    answerable = [r for r in results if r.get("scoring_rule") != "abstain_expected"]
    n_ans = max(1, len(answerable))

    by_family = Counter(r.get("question_family") or "unknown" for r in answerable)
    correct_by_family = Counter(
        r.get("question_family") or "unknown" for r in answerable if r.get("answer_correct")
    )

    reusable_family_questions = sum(by_family.get(f, 0) for f in REUSABLE_FAMILIES)
    company_tuned_questions = sum(by_family.get(f, 0) for f in COMPANY_TUNED_FAMILIES)
    other_questions = len(answerable) - reusable_family_questions - company_tuned_questions

    reusable_correct = sum(correct_by_family.get(f, 0) for f in REUSABLE_FAMILIES)
    company_tuned_correct = sum(correct_by_family.get(f, 0) for f in COMPANY_TUNED_FAMILIES)

    # Questions with only reusable-pattern success path (no diagnostic exception tags).
    exception_tags = {"coverage_gap", "semantic_ambiguity", "rule_extractor_gap"}
    reusable_clean = [
        r
        for r in answerable
        if (r.get("question_family") in REUSABLE_FAMILIES)
        and not (set(r.get("diagnostic_tags") or []) & exception_tags)
    ]
    company_dependency = [
        r
        for r in answerable
        if (r.get("question_family") in COMPANY_TUNED_FAMILIES)
        or (set(r.get("diagnostic_tags") or []) & exception_tags)
        or r.get("company_id") in ("goldns", "emni")
        and r.get("predict_reason") in ("fair_trade_zero_without_source",)
    ]

    reusable_system_coverage = round(len(reusable_clean) / n_ans, 4)
    company_specific_dependency = round(len(company_dependency) / n_ans, 4)

    fail_by_tag = Counter(tag for r in answerable for tag in (r.get("diagnostic_tags") or []))

    family_coverage: dict[str, dict[str, Any]] = {}
    for family, total in sorted(by_family.items()):
        correct = correct_by_family.get(family, 0)
        spec = FAMILY_SPECS.get(family, {})
        family_coverage[family] = {
            "total_answerable": total,
            "answer_correct": correct,
            "answer_accuracy": round(correct / max(1, total), 4),
            "reusability_tier": (
                "reusable_pattern"
                if family in REUSABLE_FAMILIES
                else "company_or_semantic_tuned"
                if family in COMPANY_TUNED_FAMILIES
                else "generic_fallback"
            ),
            "display_family": spec.get("display_name", family),
        }

    rule_class_counts = Counter(r["class"] for r in RULE_INVENTORY)

    qualitative = {
        "reusable_system_coverage_interpretation": (
            f"~{reusable_system_coverage:.1%} answerable questions answered via reusable families "
            f"({', '.join(sorted(REUSABLE_FAMILIES))}) without coverage/semantic exception tags."
        ),
        "company_specific_dependency_interpretation": (
            f"~{company_specific_dependency:.1%} answerable questions touch company-tuned families, "
            f"FTC blocked paths, or SME ambiguity tags."
        ),
        "rule_inventory": {
            "reusable_generic_rule": rule_class_counts.get("reusable_generic_rule", 0),
            "pattern_specific_rule": rule_class_counts.get("pattern_specific_rule", 0),
            "company_specific_rule": rule_class_counts.get("company_specific_rule", 0),
            "semantic_or_coverage_exception": rule_class_counts.get("semantic_or_coverage_exception", 0),
        },
        "v5_residual_not_baseline_gaps": {
            "coverage_gap_ftc_blocked": fail_by_tag.get("coverage_gap", 0),
            "semantic_ambiguity": fail_by_tag.get("semantic_ambiguity", 0),
            "retrieval_top1_miss_with_correct_answer": sum(
                1
                for r in answerable
                if not r.get("retrieval_hit_top1") and r.get("answer_correct")
            ),
        },
    }

    out: dict[str, Any] = {
        "diagnostic_view": "generalization_hardening_v5_freeze",
        "answerable_count": len(answerable),
        "reusable_system_coverage": reusable_system_coverage,
        "company_specific_dependency": company_specific_dependency,
        "reusable_family_answer_accuracy": round(reusable_correct / max(1, reusable_family_questions), 4),
        "company_tuned_family_answer_accuracy": round(
            company_tuned_correct / max(1, company_tuned_questions), 4
        ),
        "family_coverage": family_coverage,
        "counts": {
            "reusable_family_questions": reusable_family_questions,
            "company_tuned_family_questions": company_tuned_questions,
            "other_questions": other_questions,
            "reusable_clean_questions": len(reusable_clean),
            "company_dependency_questions": len(company_dependency),
        },
        "qualitative_summary": qualitative,
        "reusable_rule_ids": sorted(REUSABLE_RULE_IDS),
        "company_specific_rule_ids": sorted(COMPANY_SPECIFIC_RULE_IDS),
        "exception_rule_ids": sorted(EXCEPTION_RULE_IDS),
    }
    if baseline_metrics:
        out["baseline_v5_metrics"] = baseline_metrics
    return out
