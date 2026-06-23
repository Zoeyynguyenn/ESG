#!/usr/bin/env python3
"""Overlap strengthening round — registry bridges, pair matrix, cross-doc metrics."""

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
from enterprise_docs.overlap_strengthening import (  # noqa: E402
    PRIOR_ARTIFACT,
    audit_logical_doc_pair_matrix,
    audit_overlap_by_family_company,
    registry_snapshot,
    write_overlap_ready_corpus,
)
from enterprise_docs.retrieval_scope_policy import write_filtered_corpus  # noqa: E402
from enterprise_docs.structured_esg_mapper import run_structured_esg_pipeline  # noqa: E402

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
        "multi_source_confirmed_count": sum(1 for r in records if r.get("multi_source_confirmed")),
    }


def _prior_baseline() -> dict[str, Any]:
    if PRIOR_ARTIFACT.exists():
        data = json.loads(PRIOR_ARTIFACT.read_text(encoding="utf-8"))
        return {
            "artifact": PRIOR_ARTIFACT.parent.name,
            "holdout_comparison": data.get("holdout_comparison") or {},
            "logical_doc_overlap": data.get("logical_doc_overlap", {}).get("aggregate") or {},
        }
    return {}


def _blocker_analysis(overlap: dict[str, Any], pipeline: dict[str, Any]) -> dict[str, Any]:
    m = _holdout_metrics(pipeline)
    agg = overlap.get("aggregate") or {}
    blockers: list[str] = []
    if m.get("multi_source_confirmed_count", 0) == 0:
        if agg.get("zero_overlap_rate", 1) >= 0.8:
            blockers.append("corpus_lacks_real_multi_logical_doc_metric_overlap")
        elif agg.get("candidate_overlap_rate", 0) > 0 and agg.get("multi_doc_agreeing_value_rate", 0) == 0:
            blockers.append("extraction_value_normalization_gap")
        elif agg.get("logical_doc_overlap_rate", 0) == 0:
            blockers.append("retrieval_pool_or_logical_doc_mapping_gap")
        else:
            blockers.append("aggregation_wiring_or_probe_subset")
    return {"multi_source_confirmed_count": m.get("multi_source_confirmed_count"), "primary_blockers": blockers}


def _mandatory_answers(
    prior: dict[str, Any],
    overlap_audit: dict[str, Any],
    pair_matrix: dict[str, Any],
    pipeline: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    prior_agg = (prior.get("logical_doc_overlap") or {})
    new_agg = overlap_audit.get("aggregate") or {}
    pm = _holdout_metrics(pipeline)
    prior_cov = ((prior.get("holdout_comparison") or {}).get("family_scoped_pool") or {}).get(
        "structured_record_coverage"
    )

    best_pair = None
    best_rate = -1.0
    for pair in pair_matrix.get("pairs") or []:
        for company_id, stats in (pair.get("by_company") or {}).items():
            rate = float(stats.get("agreeing_value_rate") or 0)
            if rate > best_rate:
                best_rate = rate
                best_pair = {
                    "pair_id": pair.get("pair_id"),
                    "family_id": pair.get("family_id"),
                    "company_id": company_id,
                    "agreeing_value_rate": rate,
                }

    multi_viable = []
    single_only = []
    for fid in PILOT_FAMILIES:
        h_stats = ((pair_matrix.get("families") or {}).get(fid) or {}).get("pairs") or []
        hanssem_lim = (
            ((h_stats[0] if h_stats else {}).get("by_company") or {}).get("hanssem") or {}
        ).get("source_limitation") or {}
        musinsa_lim = (
            ((h_stats[0] if h_stats else {}).get("by_company") or {}).get("musinsa") or {}
        ).get("source_limitation") or {}
        if hanssem_lim.get("multi_source_viable"):
            multi_viable.append(f"hanssem:{fid}")
        if musinsa_lim.get("multi_source_viable") is False:
            single_only.append(f"musinsa:{fid}")

    return {
        "1_logical_doc_overlap_rate_increased": {
            "increased": float(new_agg.get("logical_doc_overlap_rate") or 0)
            > float(prior_agg.get("logical_doc_overlap_rate") or 0),
            "prior": prior_agg.get("logical_doc_overlap_rate"),
            "current": new_agg.get("logical_doc_overlap_rate"),
            "candidate_overlap_rate": new_agg.get("candidate_overlap_rate"),
        },
        "2_best_logical_doc_pairs_by_family": best_pair,
        "3_multi_source_confirmed": {
            "increased": pm.get("multi_source_confirmed_count", 0) > 0,
            "count": pm.get("multi_source_confirmed_count"),
            "blockers": blockers.get("primary_blockers"),
            "diagnosis": (
                "overlap_that" if "corpus_lacks" in str(blockers.get("primary_blockers"))
                else "extraction_normalization"
                if "normalization" in str(blockers.get("primary_blockers"))
                else "mixed"
            ),
        },
        "4_multi_source_viable_vs_single_source": {
            "multi_source_viable": multi_viable,
            "accept_single_source": single_only,
        },
        "5_musinsa_overlap_from_current_package": {
            "viable": False,
            "reason": "source_limited — thiếu SR PDF / DART ESG xml; chỉ annual report xml",
            "by_family": {
                fid: ((overlap_audit.get("by_family") or {}).get(fid) or {})
                for fid in PILOT_FAMILIES
            },
        },
        "6_next_step_without_synthesis_langgraph": (
            "Source acquisition cho musinsa (SR PDF / impact report); "
            "hanssem: corpus enrichment DART ESG xml body (không chỉ TOC); "
            "giữ overlap registry + extraction bridges; chưa LangGraph/synthesis"
        ),
        "coverage_delta_vs_family_scoped": {
            "prior_family_scoped_coverage": prior_cov,
            "overlap_strengthened_coverage": pm.get("structured_record_coverage"),
            "delta": round(
                float(pm.get("structured_record_coverage") or 0) - float(prior_cov or 0), 4
            )
            if prior_cov is not None
            else None,
        },
    }


def write_artifacts(
    out_dir: Path,
    *,
    prior: dict[str, Any],
    overlap_audit: dict[str, Any],
    pair_matrix: dict[str, Any],
    pipeline: dict[str, Any],
    build_summary: dict[str, Any],
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    blockers = _blocker_analysis(overlap_audit, pipeline)
    answers = _mandatory_answers(prior, overlap_audit, pair_matrix, pipeline, blockers)

    overlap_delta = {
        "prior_artifact": prior.get("artifact"),
        "prior_overlap_aggregate": prior.get("logical_doc_overlap"),
        "current_overlap_aggregate": overlap_audit.get("aggregate"),
        "delta": {
            k: round(
                float((overlap_audit.get("aggregate") or {}).get(k) or 0)
                - float((prior.get("logical_doc_overlap") or {}).get(k) or 0),
                4,
            )
            for k in (
                "logical_doc_overlap_rate",
                "candidate_overlap_rate",
                "multi_doc_agreeing_value_rate",
                "single_source_only_rate",
                "zero_overlap_rate",
            )
        },
        "holdout_pipeline": _holdout_metrics(pipeline),
        "prior_holdout": prior.get("holdout_comparison", {}).get("family_scoped_pool"),
    }

    summary = {
        "artifact": "enterprise_docs_overlap_strengthening",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "overlap_strengthening",
        "prior_artifact": prior.get("artifact"),
        "build_summary": build_summary,
        "metric_overlap_registry_snapshot": registry_snapshot(),
        "overlap_system_metrics": overlap_audit,
        "logical_doc_pair_matrix": pair_matrix,
        "overlap_delta": overlap_delta,
        "mandatory_answers": answers,
        "cross_doc_confirmation": {
            "matrix": pipeline.get("cross_doc_confirmation_matrix") or [],
            **blockers,
        },
        "constraints": {"no_synthesis": True, "no_langgraph_trial": True, "no_case_tuning": True},
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "logical_doc_pair_matrix.json").write_text(
        json.dumps(pair_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "metric_overlap_registry_snapshot.json").write_text(
        json.dumps(registry_snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "overlap_delta.json").write_text(json.dumps(overlap_delta, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "cross_doc_confirmation_matrix.json").write_text(
        json.dumps(pipeline.get("cross_doc_confirmation_matrix") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(_report(out_dir, summary, answers), encoding="utf-8")
    return summary


def _report(out_dir: Path, summary: dict[str, Any], answers: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enterprise internal-doc — Overlap strengthening",
            "",
            f"Artifact: `{out_dir.relative_to(ROOT)}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Overlap system metrics",
            "",
            json.dumps(summary.get("overlap_system_metrics", {}).get("aggregate"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_overlap_strengthening_{ts}")).resolve()

    prior = _prior_baseline()
    build_summary: dict[str, Any] = {}
    filtered_by_company: dict[str, list] = {}

    for cid in HOLDOUT_COMPANIES:
        reingested = load_corpus_for_company(cid, holdout_corpus="reingested")
        build_summary[f"{cid}_filtered"] = write_filtered_corpus(cid, reingested)
        filtered_by_company[cid] = load_corpus_for_company(cid, holdout_corpus="filtered")
        build_summary[f"{cid}_overlap_ready"] = write_overlap_ready_corpus(cid, filtered_by_company[cid])

    probes = _load_probes()
    overlap_audit = audit_overlap_by_family_company(probes, filtered_by_company, use_family_pool=True)
    pair_matrix = audit_logical_doc_pair_matrix(probes, filtered_by_company)

    pipeline = run_structured_esg_pipeline(
        include_demo=False, holdout_corpus="overlap_strengthened", enrich_holdout_plans=True
    )

    summary = write_artifacts(
        out_dir,
        prior=prior,
        overlap_audit=overlap_audit,
        pair_matrix=pair_matrix,
        pipeline=pipeline,
        build_summary=build_summary,
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "mandatory_answers": summary.get("mandatory_answers")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
