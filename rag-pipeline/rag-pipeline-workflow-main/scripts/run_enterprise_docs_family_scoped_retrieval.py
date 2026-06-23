#!/usr/bin/env python3
"""Family-scoped retrieval pool round — per-family logical-doc pools + overlap audit."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.family_retrieval_pool import (  # noqa: E402
    audit_logical_doc_overlap_matrix,
    build_family_pool_matrix,
    write_family_scoped_corpus,
)
from enterprise_docs.holdout_harness import load_corpus_for_company  # noqa: E402
from enterprise_docs.retrieval_scope_policy import write_filtered_corpus  # noqa: E402
from enterprise_docs.structured_esg_mapper import run_structured_esg_pipeline  # noqa: E402

PRIOR = ROOT / "reports/enterprise_docs_retrieval_scope_narrowing_20260619-092751/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")
HOLDOUT_COMPANIES = ("hanssem", "musinsa")
PROBE_PATHS = {
    "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
    "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
}


def _load_probes() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for cid, path in PROBE_PATHS.items():
        if path.exists():
            out[cid] = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    return out


def _holdout_metrics(result: dict[str, Any]) -> dict[str, Any]:
    records = [r for r in (result.get("records") or []) if r.get("company_id") in HOLDOUT_COMPANIES]
    n = max(1, len(records))
    return {
        "case_count": len(records),
        "structured_record_coverage": round(
            sum(1 for r in records if r.get("value") and r.get("value_type") not in ("unknown",)) / n, 4
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
            sum(1 for r in records if r.get("conflict_status") == "insufficient_cross_doc_support") / n, 4
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
    return {k: round(float(b[k]) - float(a[k]), 4) for k in keys if k in a and k in b}


def _by_company_holdout(result: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cid in HOLDOUT_COMPANIES:
        rows = [r for r in (result.get("records") or []) if r.get("company_id") == cid]
        n = max(1, len(rows))
        out[cid] = {
            "structured_record_coverage": round(
                sum(1 for r in rows if r.get("value") and r.get("value_type") not in ("unknown",)) / n, 4
            ),
            "case_count": len(rows),
        }
    return out


def _blocker_analysis(
    family_scoped: dict[str, Any],
    overlap: dict[str, Any],
) -> dict[str, Any]:
    m = _holdout_metrics(family_scoped)
    blockers: list[str] = []
    if m.get("multi_source_confirmed_count", 0) == 0:
        agg_overlap = (overlap.get("aggregate") or {}).get("logical_doc_overlap_rate", 0)
        agree = (overlap.get("aggregate") or {}).get("multi_doc_agreeing_value_rate", 0)
        if agg_overlap == 0:
            blockers.append("corpus_lacks_real_multi_logical_doc_metric_overlap")
        elif agree == 0:
            blockers.append("extraction_alias_cross_role_insufficient")
        elif m.get("insufficient_cross_doc_support_rate", 0) > 0:
            blockers.append("retrieval_pool_or_aggregation_wiring_gap")
        else:
            blockers.append("aggregation_no_confirming_values")
    return {
        "multi_source_confirmed_count": m.get("multi_source_confirmed_count"),
        "primary_blockers_if_zero": blockers,
    }


def _mandatory_answers(
    reingested: dict[str, Any],
    filtered: dict[str, Any],
    family_scoped: dict[str, Any],
    overlap: dict[str, Any],
    pool_matrix: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    f_m = _holdout_metrics(family_scoped)
    fl_m = _holdout_metrics(filtered)
    rec_delta = _delta(fl_m, f_m)

    best_family = None
    best_delta = -1.0
    for fid in PILOT_FAMILIES:
        f_rows = [r for r in (family_scoped.get("records") or []) if r.get("family_id") == fid and r.get("company_id") in HOLDOUT_COMPANIES]
        fl_rows = [r for r in (filtered.get("records") or []) if r.get("family_id") == fid and r.get("company_id") in HOLDOUT_COMPANIES]
        fn = max(1, len(f_rows))
        fln = max(1, len(fl_rows))
        fc = sum(1 for r in f_rows if r.get("value")) / fn
        flc = sum(1 for r in fl_rows if r.get("value")) / fln
        d = fc - flc
        if d > best_delta:
            best_delta = d
            best_family = fid

    musinsa_pools = (pool_matrix.get("families") or {}).get("environment_ghg", {}).get("musinsa", {})
    hanssem_gov = (pool_matrix.get("families") or {}).get("governance", {}).get("hanssem", {})

    return {
        "1_family_scoped_vs_filtered_scoped": {
            "better_than_filtered": rec_delta.get("structured_record_coverage", 0) > 0,
            "coverage_delta": rec_delta,
            "filtered_coverage": fl_m.get("structured_record_coverage"),
            "family_scoped_coverage": f_m.get("structured_record_coverage"),
            "by_company_delta": {
                cid: _delta(
                    _holdout_metrics({"records": [r for r in filtered.get("records", []) if r.get("company_id") == cid]}),
                    _holdout_metrics({"records": [r for r in family_scoped.get("records", []) if r.get("company_id") == cid]}),
                )
                for cid in HOLDOUT_COMPANIES
            },
        },
        "2_family_most_benefit_from_logical_doc_pools": best_family,
        "3_logical_doc_overlap_rate_by_family": (overlap.get("by_family") or {}),
        "4_multi_source_confirmed": {
            "increased": f_m.get("multi_source_confirmed_count", 0)
            > fl_m.get("multi_source_confirmed_count", 0),
            "count": f_m.get("multi_source_confirmed_count"),
            "real_blockers": blockers.get("primary_blockers_if_zero"),
        },
        "5_musinsa_primary_issue": {
            "family_pool_units_environment_ghg": musinsa_pools.get("unit_count"),
            "family_pool_units_governance_hanssem_reference": hanssem_gov.get("unit_count"),
            "diagnosis": (
                "Thiếu source slice mạnh (SR PDF / DART ESG xml) trong package; "
                "family policy đã fallback annual_report + html nhưng overlap ESG probe vẫn yếu"
                if (musinsa_pools.get("unit_count") or 0) < 100
                else "Retrieval family policy chưa đủ; package có pool nhưng metric overlap thấp"
            ),
        },
        "6_next_step_without_synthesis_langgraph": (
            "Overlap strengthening: mở rộng alias/family bridge giữa SR PDF pool và DART ESG xml pool; "
            "giữ family-scoped retrieval; chưa LangGraph/synthesis."
        ),
    }


def write_artifacts(
    out_dir: Path,
    *,
    reingested: dict[str, Any],
    filtered: dict[str, Any],
    family_scoped: dict[str, Any],
    pool_matrix: dict[str, Any],
    overlap: dict[str, Any],
    build_summary: dict[str, Any],
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    blockers = _blocker_analysis(family_scoped, overlap)
    answers = _mandatory_answers(reingested, filtered, family_scoped, overlap, pool_matrix, blockers)

    coverage_delta = {
        "lanes": ["reingested_full", "filtered_scoped", "family_scoped_pool"],
        "holdout_metrics": {
            "reingested_full": _holdout_metrics(reingested),
            "filtered_scoped": _holdout_metrics(filtered),
            "family_scoped_pool": _holdout_metrics(family_scoped),
        },
        "filtered_to_family_scoped": _delta(_holdout_metrics(filtered), _holdout_metrics(family_scoped)),
        "reingested_to_family_scoped": _delta(_holdout_metrics(reingested), _holdout_metrics(family_scoped)),
        "by_company_family_scoped": _by_company_holdout(family_scoped),
    }

    summary = {
        "artifact": "enterprise_docs_family_scoped_retrieval",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "family_scoped_retrieval_pool",
        "prior_artifact": str(PRIOR.parent.name) if PRIOR.exists() else None,
        "build_summary": build_summary,
        "family_pool_matrix": pool_matrix,
        "logical_doc_overlap": overlap,
        "holdout_comparison": coverage_delta["holdout_metrics"],
        "mandatory_answers": answers,
        "cross_doc_confirmation": {
            "matrix": family_scoped.get("cross_doc_confirmation_matrix") or [],
            **blockers,
        },
        "constraints": {"no_synthesis": True, "no_langgraph_trial": True, "no_case_tuning": True},
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "family_pool_matrix.json").write_text(json.dumps(pool_matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "logical_doc_overlap_matrix.json").write_text(json.dumps(overlap, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "coverage_delta.json").write_text(json.dumps(coverage_delta, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "cross_doc_confirmation_matrix.json").write_text(
        json.dumps(family_scoped.get("cross_doc_confirmation_matrix") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(_report(out_dir, summary, answers, coverage_delta), encoding="utf-8")
    return summary


def _report(
    out_dir: Path,
    summary: dict[str, Any],
    answers: dict[str, Any],
    coverage_delta: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "# Enterprise internal-doc — Family-scoped retrieval pool",
            "",
            f"Artifact: `{out_dir.relative_to(ROOT)}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Coverage delta (3 lanes)",
            "",
            json.dumps(coverage_delta, ensure_ascii=False, indent=2),
            "",
            "## Logical-doc overlap by family",
            "",
            json.dumps(summary.get("logical_doc_overlap", {}).get("by_family"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_family_scoped_retrieval_{ts}")).resolve()

    build_summary: dict[str, Any] = {}
    units_by_company: dict[str, list] = {}
    filtered_by_company: dict[str, list] = {}

    for cid in HOLDOUT_COMPANIES:
        reingested_units = load_corpus_for_company(cid, holdout_corpus="reingested")
        units_by_company[cid] = reingested_units
        build_summary[f"{cid}_filtered"] = write_filtered_corpus(cid, reingested_units)
        filtered_by_company[cid] = load_corpus_for_company(cid, holdout_corpus="filtered")
        build_summary[f"{cid}_family_scoped_union"] = write_family_scoped_corpus(cid, filtered_by_company[cid])

    pool_matrix = build_family_pool_matrix(filtered_by_company)
    probes = _load_probes()
    overlap_filtered = audit_logical_doc_overlap_matrix(probes, filtered_by_company, use_family_pool=False)
    overlap_family = audit_logical_doc_overlap_matrix(probes, filtered_by_company, use_family_pool=True)
    overlap = {
        "filtered_corpus_scan": overlap_filtered,
        "family_pool_scan": overlap_family,
        "by_family": overlap_family.get("by_family"),
        "aggregate": overlap_family.get("aggregate"),
    }

    reingested = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="reingested", enrich_holdout_plans=True
    )
    filtered = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="filtered", enrich_holdout_plans=True
    )
    family_scoped = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="family_scoped", enrich_holdout_plans=True
    )

    summary = write_artifacts(
        out_dir,
        reingested=reingested,
        filtered=filtered,
        family_scoped=family_scoped,
        pool_matrix=pool_matrix,
        overlap=overlap,
        build_summary=build_summary,
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "mandatory_answers": summary.get("mandatory_answers")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
