"""Reusable capability regression + natural onboarding gate runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from enterprise_docs.crossdoc_capability_benchmark import (
    CAPABILITY_METRICS,
    run_capability_benchmark,
)
from enterprise_docs.crossdoc_case_builder import all_capability_cases, load_cases_jsonl

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE_PATH = ROOT / "data/enterprise_docs/natural_onboarding_gate_definition.json"
PRIOR_FUSION_ARTIFACT = ROOT / "reports/enterprise_docs_fusion_equivalence_hardening_20260619-102350/summary.json"

CONSTRUCTED_REGRESSION_METRICS = (
    "cross_role_extraction_alignment_rate",
    "cross_doc_equivalence_match_rate",
    "evidence_fusion_success_rate",
    "conflict_classification_accuracy",
    "single_source_to_multi_source_promotion_rate",
)

LAYER_KEYS = (
    "extraction",
    "equivalence_collapse",
    "fusion",
    "conflict_classification",
    "readiness_promotion",
)


def default_gate_definition() -> dict[str, Any]:
    """Draft acceptance thresholds — constructed regression strict, natural exploratory."""
    return {
        "version": "natural_onboarding_gate_draft_v1",
        "prior_constructed_baseline_artifact": str(
            PRIOR_FUSION_ARTIFACT.relative_to(ROOT)
        ).replace("\\", "/"),
        "layers": {
            "extraction": {
                "metric": "cross_role_extraction_alignment_rate",
                "scope": "constructed",
                "minimum": 1.0,
                "description": "Per logical-doc extraction alignment on constructed multi-source cases",
            },
            "equivalence_collapse": {
                "metric": "cross_doc_equivalence_match_rate",
                "scope": "constructed",
                "minimum": 1.0,
                "description": "Canonical key / alias equivalence on constructed cases",
            },
            "fusion": {
                "metric": "evidence_fusion_success_rate",
                "scope": "constructed",
                "minimum": 1.0,
                "description": "multi_source_confirmed + fusion contract on constructed cases",
            },
            "conflict_classification": {
                "metric": "conflict_classification_accuracy",
                "scope": "constructed",
                "minimum": 1.0,
                "description": "Expected conflict status match on constructed conflict cases",
            },
            "readiness_promotion": {
                "metric": "single_source_to_multi_source_promotion_rate",
                "scope": "constructed",
                "minimum": 1.0,
                "ghost_pass_maximum": 0,
                "description": "Promotion must track fusion_ok; ghost_pass_count must be 0",
            },
        },
        "natural_onboarding_draft": {
            "parser_coverage_minimum": 0.5,
            "candidate_found_rate_minimum": 0.3,
            "corpus_limited_rate_maximum": 0.9,
            "system_gap_rate_maximum": 0.2,
            "cross_doc_eligible_fusion_minimum": None,
            "notes": (
                "Natural thresholds are draft — primary signal is failure_mode split "
                "(corpus_limited vs system_gap), not headline pass rate"
            ),
        },
        "regression_suite": {
            "constructed_must_pass": True,
            "natural_runs_for_diagnostics": True,
            "no_core_pipeline_changes_required": True,
        },
    }


def load_gate_definition(path: Path | None = None) -> dict[str, Any]:
    gate_path = path or DEFAULT_GATE_PATH
    if gate_path.exists():
        return json.loads(gate_path.read_text(encoding="utf-8"))
    return default_gate_definition()


def _ghost_pass_count(case_results: list[dict[str, Any]], cases: list[dict[str, Any]]) -> int:
    case_by_id = {c.get("case_id"): c for c in cases}
    ghost = 0
    for row in case_results:
        if row.get("promotion_ok") is None:
            continue
        src = case_by_id.get(row.get("case_id")) or {}
        promoted = bool((row.get("promotion") or {}).get("promoted"))
        fusion_ok = bool(row.get("fusion_ok"))
        if promoted and not fusion_ok and src.get("expected_multi_source_confirmed") is True:
            ghost += 1
    return ghost


def _layer_report(
    bench: dict[str, Any],
    *,
    cases: list[dict[str, Any]],
    gate: dict[str, Any],
) -> dict[str, Any]:
    cm = bench.get("capability_metrics") or {}
    nm = bench.get("natural_metrics") or {}
    results = bench.get("case_results") or []
    ghost = _ghost_pass_count(results, cases)
    layers_cfg = gate.get("layers") or {}

    by_layer: dict[str, Any] = {}
    for layer in LAYER_KEYS:
        cfg = layers_cfg.get(layer) or {}
        metric = cfg.get("metric")
        value = cm.get(metric) if metric else None
        minimum = cfg.get("minimum")
        passed = value is not None and minimum is not None and float(value) >= float(minimum)
        if layer == "readiness_promotion":
            ghost_max = cfg.get("ghost_pass_maximum", 0)
            passed = passed and ghost <= int(ghost_max)
        by_layer[layer] = {
            "metric": metric,
            "value": value,
            "minimum": minimum,
            "passed": passed,
            "ghost_pass_count": ghost if layer == "readiness_promotion" else None,
        }

    constructed_rows = [r for r in results if r.get("case_origin") == "constructed"]
    natural_rows = [r for r in results if r.get("case_origin") == "natural"]

    return {
        "by_capability_layer": by_layer,
        "constructed_regression": {
            "case_count": len(constructed_rows),
            "all_layers_passed": all(v.get("passed") for v in by_layer.values()),
            "metrics": {m: cm.get(m) for m in CONSTRUCTED_REGRESSION_METRICS},
            "ghost_pass_count": ghost,
        },
        "natural_diagnostics": {
            "case_count": nm.get("case_count", len(natural_rows)),
            "candidate_found_rate": nm.get("candidate_found_rate"),
            "corpus_limited_rate": nm.get("corpus_limited_rate"),
            "system_gap_rate": nm.get("system_gap_rate"),
            "by_failure_mode": nm.get("by_failure_mode"),
        },
    }


def evaluate_gate(
    bench: dict[str, Any],
    *,
    cases: list[dict[str, Any]],
    gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = gate or default_gate_definition()
    layer_report = _layer_report(bench, cases=cases, gate=gate)
    natural_draft = gate.get("natural_onboarding_draft") or {}
    nm = bench.get("natural_metrics") or {}

    natural_checks: dict[str, Any] = {}
    for key, threshold in natural_draft.items():
        if key.endswith("_minimum") and threshold is not None:
            metric_key = key.replace("_minimum", "_rate").replace("parser_coverage", "candidate_found")
            val = nm.get(metric_key.replace("parser_coverage_rate", "candidate_found_rate"))
            if val is not None:
                natural_checks[key] = {"value": val, "threshold": threshold, "passed": float(val) >= float(threshold)}
        elif key.endswith("_maximum") and threshold is not None:
            metric_key = key.replace("_maximum", "_rate")
            val = nm.get(metric_key)
            if val is not None:
                natural_checks[key] = {"value": val, "threshold": threshold, "passed": float(val) <= float(threshold)}

    regression_ok = layer_report["constructed_regression"]["all_layers_passed"]
    return {
        "gate_version": gate.get("version"),
        "regression_gate_passed": regression_ok,
        "natural_onboarding_draft_checks": natural_checks,
        "natural_onboarding_informational_only": True,
        "layer_report": layer_report,
        "overall_status": "ready_for_natural_plug_in" if regression_ok else "constructed_regression_failed",
    }


def run_capability_gate(
    *,
    cases: list[dict[str, Any]] | None = None,
    cases_path: Path | None = None,
    include_constructed: bool = True,
    include_natural: bool = True,
    gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run benchmark harness and evaluate against gate definition."""
    if cases is None:
        if cases_path and cases_path.exists():
            cases = load_cases_jsonl(cases_path)
        else:
            cases = all_capability_cases(include_natural=include_natural)
    if not include_constructed:
        cases = [c for c in cases if c.get("case_origin") != "constructed"]
    if not include_natural:
        cases = [c for c in cases if c.get("case_origin") != "natural"]

    bench = run_capability_benchmark(cases)
    gate_eval = evaluate_gate(bench, cases=cases, gate=gate)
    return {
        "benchmark": bench,
        "gate_evaluation": gate_eval,
        "cases_meta": {
            "total": len(cases),
            "constructed": sum(1 for c in cases if c.get("case_origin") == "constructed"),
            "natural": sum(1 for c in cases if c.get("case_origin") == "natural"),
        },
    }


def report_by_capability_layer(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize case outcomes grouped by pipeline layer fields."""
    layers: dict[str, list[dict[str, Any]]] = {k: [] for k in LAYER_KEYS}
    for row in case_results:
        layers["extraction"].append(
            {
                "case_id": row.get("case_id"),
                "origin": row.get("case_origin"),
                "ok": row.get("extract_alignment_ok"),
            }
        )
        layers["equivalence_collapse"].append(
            {
                "case_id": row.get("case_id"),
                "origin": row.get("case_origin"),
                "ok": row.get("equivalence_collapse_ok"),
            }
        )
        layers["fusion"].append(
            {
                "case_id": row.get("case_id"),
                "origin": row.get("case_origin"),
                "ok": row.get("fusion_ok"),
            }
        )
        layers["conflict_classification"].append(
            {
                "case_id": row.get("case_id"),
                "origin": row.get("case_origin"),
                "ok": row.get("classification_ok"),
            }
        )
        layers["readiness_promotion"].append(
            {
                "case_id": row.get("case_id"),
                "origin": row.get("case_origin"),
                "ok": row.get("promotion_ok"),
                "promoted": (row.get("promotion") or {}).get("promoted"),
            }
        )
    return layers
