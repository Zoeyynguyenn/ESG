#!/usr/bin/env python3
"""Retrieval scope narrowing round — filtered holdout corpus + cross-doc probe path."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.holdout_harness import load_corpus_for_company  # noqa: E402
from enterprise_docs.retrieval_scope_policy import (  # noqa: E402
    build_scope_policy_matrix,
    list_scope_names,
    load_retrieval_scope_policy,
    summarize_scope,
    write_filtered_corpus,
)
from enterprise_docs.structured_esg_mapper import run_structured_esg_pipeline  # noqa: E402

PRIOR = ROOT / "reports/enterprise_docs_structured_esg_reingest_20260619-091843/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")
HOLDOUT_COMPANIES = ("hanssem", "musinsa")


def _holdout_metrics(result: dict[str, Any]) -> dict[str, Any]:
    records = [
        r
        for r in (result.get("records") or [])
        if r.get("company_id") in HOLDOUT_COMPANIES
    ]
    n = max(1, len(records))
    return {
        "case_count": len(records),
        "structured_record_coverage": round(
            sum(
                1
                for r in records
                if r.get("value") and r.get("value_type") not in ("unknown",)
            )
            / n,
            4,
        ),
        "single_source_sufficient_rate": round(
            sum(1 for r in records if r.get("conflict_status") == "single_source_sufficient") / n, 4
        ),
        "multi_source_confirmed_rate": round(
            sum(1 for r in records if r.get("conflict_status") == "multi_source_confirmed") / n, 4
        ),
        "metric_absent_rate": round(
            sum(1 for r in records if r.get("conflict_status") == "metric_absent") / n, 4
        ),
        "insufficient_cross_doc_support_rate": round(
            sum(1 for r in records if r.get("conflict_status") == "insufficient_cross_doc_support") / n,
            4,
        ),
        "cross_doc_probe_count": sum(1 for r in records if r.get("answer_mode") == "cross_document_answer"),
        "multi_source_confirmed_count": sum(1 for r in records if r.get("multi_source_confirmed")),
    }


def _delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "structured_record_coverage",
        "single_source_sufficient_rate",
        "multi_source_confirmed_rate",
        "metric_absent_rate",
        "insufficient_cross_doc_support_rate",
    ]
    out: dict[str, Any] = {}
    for k in keys:
        if k in a and k in b:
            out[k] = round(float(b[k]) - float(a[k]), 4)
    return out


def _family_recovery(filtered: dict[str, Any], reingested: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fid in PILOT_FAMILIES:
        f_rows = [r for r in (filtered.get("records") or []) if r.get("family_id") == fid]
        r_rows = [r for r in (reingested.get("records") or []) if r.get("family_id") == fid]
        fh = [c for c in f_rows if c.get("company_id") in HOLDOUT_COMPANIES]
        rh = [c for c in r_rows if c.get("company_id") in HOLDOUT_COMPANIES]
        fn = max(1, len(fh))
        rn = max(1, len(rh))
        fc = round(sum(1 for r in fh if r.get("value")) / fn, 4)
        rc = round(sum(1 for r in rh if r.get("value")) / rn, 4)
        out[fid] = {
            "filtered_holdout_coverage": fc,
            "reingested_full_holdout_coverage": rc,
            "recovery_delta": round(fc - rc, 4),
            "case_count": len(fh),
        }
    best = max(out.items(), key=lambda x: x[1].get("recovery_delta", 0))[0] if out else None
    return {"by_family": out, "most_recovered_family": best}


def _scope_ranking(
    units_by_company: dict[str, list[dict[str, Any]]],
    *,
    baseline_holdout: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for scope in list_scope_names():
        total_units = 0
        for units in units_by_company.values():
            total_units += summarize_scope(units, scope).get("output_units", 0)
        rows.append(
            {
                "scope_name": scope,
                "total_filtered_units": total_units,
                "policy": summarize_scope(
                    units_by_company.get("hanssem") or [], scope
                ),
            }
        )
    return {"scopes": rows, "default_scope": load_retrieval_scope_policy().get("default_scope")}


def _blocker_analysis(
    baseline: dict[str, Any],
    reingested: dict[str, Any],
    filtered: dict[str, Any],
) -> dict[str, Any]:
    b = _holdout_metrics(baseline)
    r = _holdout_metrics(reingested)
    f = _holdout_metrics(filtered)
    multi = f.get("multi_source_confirmed_count", 0)
    blockers: list[str] = []
    if multi == 0:
        cross = f.get("cross_doc_probe_count", 0)
        if cross == 0:
            blockers.append("cross_doc_probe_path_not_activated")
        elif f.get("insufficient_cross_doc_support_rate", 0) > 0:
            blockers.append("logical_doc_overlap_or_extraction_cross_role")
        elif f.get("metric_absent_rate", 0) > 0.4:
            blockers.append("extraction_alias_or_corpus_overlap_gap")
        else:
            blockers.append("aggregation_no_agreeing_values_across_logical_docs")
    bottlenecks: list[str] = []
    if f.get("structured_record_coverage", 0) < b.get("structured_record_coverage", 0):
        bottlenecks.append("retrieval_policy_still_suboptimal_vs_golden_baseline")
    if r.get("structured_record_coverage", 0) > f.get("structured_record_coverage", 0):
        bottlenecks.append("filter_too_aggressive")
    if f.get("structured_record_coverage", 0) >= r.get("structured_record_coverage", 0):
        bottlenecks.append("retrieval_scope_was_primary_bottleneck_on_full_reingest")
    if f.get("multi_source_confirmed_rate", 0) == 0 and f.get("cross_doc_probe_count", 0) > 0:
        bottlenecks.append("logical_doc_overlap")
    return {
        "holdout_metrics": {"baseline": b, "reingested_full": r, "filtered_scoped": f},
        "multi_source_confirmed_count": multi,
        "primary_blockers_if_zero": blockers,
        "bottleneck_ranking": bottlenecks,
    }


def _mandatory_answers(
    baseline: dict[str, Any],
    reingested: dict[str, Any],
    filtered: dict[str, Any],
    recovery: dict[str, Any],
    blockers: dict[str, Any],
    scope_matrix: dict[str, Any],
) -> dict[str, Any]:
    b = blockers["holdout_metrics"]
    rec = _delta(b["reingested_full"], b["filtered_scoped"])
    vs_base = _delta(b["baseline"], b["filtered_scoped"])

    recovered = rec.get("structured_record_coverage", 0) > 0
    vs_baseline_ok = (b["filtered_scoped"].get("structured_record_coverage") or 0) >= (
        b["baseline"].get("structured_record_coverage") or 0
    )

    best_scope = "structured_esg_retrieval_ready"
    hanssem_scopes = (scope_matrix.get("scopes") or {}).get("sr_pdf_only", {}).get("hanssem", {})
    gov_scopes = (scope_matrix.get("scopes") or {}).get("governance_dart_xml", {}).get("hanssem", {})
    structured = (scope_matrix.get("scopes") or {}).get("structured_esg_retrieval_ready", {}).get("hanssem", {})

    return {
        "1_coverage_recovery_on_holdout": {
            "recovered_vs_full_reingest": recovered,
            "recovery_delta": rec,
            "vs_golden_baseline_delta": vs_base,
            "reaches_baseline_level": vs_baseline_ok,
            "by_company_reingested_to_filtered": {
                cid: _delta(
                    _holdout_metrics(
                        {
                            "records": [
                                r
                                for r in reingested.get("records", [])
                                if r.get("company_id") == cid
                            ]
                        }
                    ),
                    _holdout_metrics(
                        {
                            "records": [
                                r
                                for r in filtered.get("records", [])
                                if r.get("company_id") == cid
                            ]
                        }
                    ),
                )
                for cid in HOLDOUT_COMPANIES
            },
        },
        "2_best_scope_slices": {
            "recommended_default": best_scope,
            "sr_pdf_only_units_hanssem": hanssem_scopes.get("output_units"),
            "governance_dart_xml_units_hanssem": gov_scopes.get("output_units"),
            "structured_esg_retrieval_ready_units_hanssem": structured.get("output_units"),
            "note": "SR PDF giúp extraction khi retrieval trúng; combined slice cân bằng SR PDF + DART ESG xml",
        },
        "3_multi_source_confirmed": {
            "increased": (b["filtered_scoped"].get("multi_source_confirmed_count") or 0)
            > (b["reingested_full"].get("multi_source_confirmed_count") or 0),
            "count_filtered": b["filtered_scoped"].get("multi_source_confirmed_count"),
            "cross_doc_probes_filtered": b["filtered_scoped"].get("cross_doc_probe_count"),
            "real_blockers": blockers.get("primary_blockers_if_zero"),
        },
        "4_primary_bottleneck_after_round": blockers.get("bottleneck_ranking"),
        "5_family_most_benefit": recovery.get("most_recovered_family"),
        "6_next_step_without_synthesis_langgraph": (
            "Tinh chỉnh retrieval policy theo logical-doc + family source expectations; "
            "mở rộng overlap corpus giữa SR PDF và DART ESG xml; giữ cross-doc probe subset có kiểm soát."
        ),
    }


def write_artifacts(
    out_dir: Path,
    *,
    baseline: dict[str, Any],
    reingested: dict[str, Any],
    filtered: dict[str, Any],
    scope_matrix: dict[str, Any],
    filter_build: dict[str, Any],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    recovery = _family_recovery(filtered, reingested)
    blockers = _blocker_analysis(baseline, reingested, filtered)
    answers = _mandatory_answers(baseline, reingested, filtered, recovery, blockers, scope_matrix)

    recovery_delta = {
        "comparison_axes": ["baseline_narrative", "reingested_full", "filtered_scoped"],
        "holdout_aggregate": blockers["holdout_metrics"],
        "reingested_to_filtered_delta": _delta(
            blockers["holdout_metrics"]["reingested_full"],
            blockers["holdout_metrics"]["filtered_scoped"],
        ),
        "baseline_to_filtered_delta": _delta(
            blockers["holdout_metrics"]["baseline"],
            blockers["holdout_metrics"]["filtered_scoped"],
        ),
        "by_company": answers["1_coverage_recovery_on_holdout"]["by_company_reingested_to_filtered"],
        "prior_reingest_artifact": prior.get("reingested_metrics") if prior else None,
    }

    summary = {
        "artifact": "enterprise_docs_retrieval_scope_narrowing",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "structured_esg_retrieval_scope_narrowing",
        "prior_artifact": str(PRIOR.parent.name) if PRIOR.exists() else None,
        "filter_build": filter_build,
        "scope_policy_matrix": scope_matrix,
        "holdout_comparison": blockers["holdout_metrics"],
        "family_scope_recovery": recovery,
        "cross_doc_confirmation": {
            "matrix": filtered.get("cross_doc_confirmation_matrix") or [],
            "multi_source_confirmed_count": blockers.get("multi_source_confirmed_count"),
            "blockers": blockers.get("primary_blockers_if_zero"),
        },
        "mandatory_answers": answers,
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "scope_policy_matrix.json").write_text(
        json.dumps(scope_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "coverage_recovery_delta.json").write_text(
        json.dumps(recovery_delta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "cross_doc_confirmation_matrix.json").write_text(
        json.dumps(filtered.get("cross_doc_confirmation_matrix") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "family_scope_recovery_summary.json").write_text(
        json.dumps(recovery, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = _report(out_dir, summary, answers, recovery_delta, blockers)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    return summary


def _report(
    out_dir: Path,
    summary: dict[str, Any],
    answers: dict[str, Any],
    recovery_delta: dict[str, Any],
    blockers: dict[str, Any],
) -> str:
    lines = [
        "# Enterprise internal-doc — Retrieval scope narrowing",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "> Thu hẹp retrieval scope trên holdout reingested; mở cross-doc probe path có kiểm soát.",
        "",
        "## Câu trả lời bắt buộc",
        "",
        json.dumps(answers, ensure_ascii=False, indent=2),
        "",
        "## Coverage recovery delta",
        "",
        json.dumps(recovery_delta, ensure_ascii=False, indent=2),
        "",
        "## Holdout comparison (baseline / full / filtered)",
        "",
        json.dumps(blockers.get("holdout_metrics"), ensure_ascii=False, indent=2),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--skip-filter-build", action="store_true")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_retrieval_scope_narrowing_{ts}")).resolve()

    filter_build: dict[str, Any] = {}
    units_by_company: dict[str, list] = {}
    scope = load_retrieval_scope_policy().get("default_scope") or "structured_esg_retrieval_ready"

    for cid in HOLDOUT_COMPANIES:
        units = load_corpus_for_company(cid, holdout_corpus="reingested")
        units_by_company[cid] = units
        if not args.skip_filter_build:
            filter_build[cid] = write_filtered_corpus(cid, units, scope_name=scope)

    scope_matrix = build_scope_policy_matrix(units_by_company)

    baseline = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="baseline", enrich_holdout_plans=True
    )
    reingested = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="reingested", enrich_holdout_plans=True
    )
    filtered = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="filtered", enrich_holdout_plans=True
    )

    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else None
    summary = write_artifacts(
        out_dir,
        baseline=baseline,
        reingested=reingested,
        filtered=filtered,
        scope_matrix=scope_matrix,
        filter_build=filter_build,
        prior=prior,
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "mandatory_answers": summary.get("mandatory_answers")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
