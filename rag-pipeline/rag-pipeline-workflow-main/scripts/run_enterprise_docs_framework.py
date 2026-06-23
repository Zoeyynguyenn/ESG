#!/usr/bin/env python3
"""Enterprise internal-doc lane: abstraction layer + holdout harness + LangGraph handoff contract."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.holdout_harness import run_holdout_matrix
from enterprise_docs.langgraph_handoff import build_handoff, export_handoff_schema
from enterprise_docs.readiness_model import assess_readiness, summarize_readiness
from enterprise_docs.registries import export_registry_snapshot, load_company_doc_registry
from enterprise_docs.reusability_audit import analyze_reusability
from enterprise_docs.rule_inventory import export_rule_inventory

DEMO_CORPUS = ROOT / "data/enterprise_docs/demo_company/corpus_units.jsonl"
DEMO_SINGLE = ROOT / "data/enterprise_docs/demo_company/eval_subset_single.jsonl"
DEMO_CROSS = ROOT / "data/enterprise_docs/demo_company/eval_subset_cross.jsonl"
GEN_BASELINE = ROOT / "reports/enterprise_docs_generalization_20260618-151707/summary.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _run_demo_handoffs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units = _load_jsonl(DEMO_CORPUS)
    lookup = {str(u["unit_id"]): u for u in units}
    index, logical_map = build_index_from_units(units, company_id="demo_company")
    plans = _load_jsonl(DEMO_SINGLE) + _load_jsonl(DEMO_CROSS)
    readiness_rows: list[dict[str, Any]] = []
    handoffs: list[dict[str, Any]] = []

    for plan in plans:
        plan = dict(plan)
        plan.setdefault("company_id", "demo_company")
        ret = retrieve_for_plan(plan, index, logical_map)
        readiness_rows.append(
            assess_readiness(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
        )
        handoffs.append(
            build_handoff(
                plan,
                ret,
                company_id="demo_company",
                unit_lookup=lookup,
                logical_to_corpus=logical_map,
            ).to_dict()
        )

    return handoffs, summarize_readiness(readiness_rows)


def _registry_audit() -> dict[str, Any]:
    reg = load_company_doc_registry()
    companies = reg.get("companies") or {}
    pilot_docs = 0
    generic_docs = 0
    for cfg in companies.values():
        for spec in (cfg.get("logical_documents") or {}).values():
            scope = str(spec.get("scope") or "")
            if scope == "pilot_only":
                pilot_docs += 1
            elif scope == "generic":
                generic_docs += 1
    inventory = export_rule_inventory(str(ROOT / "data/enterprise_docs/rule_inventory.json"))
    return {
        "company_count": len(companies),
        "logical_doc_pilot_only": pilot_docs,
        "logical_doc_generic": generic_docs,
        "rule_count": inventory["rule_count"],
        "pilot_only_rules": inventory["by_class"].get("pilot_only_rule", 0),
        "reusable_generic_rules": inventory["by_class"].get("reusable_generic_rule", 0),
    }


def _architecture_decision(
    holdout: dict[str, Any],
    demo_summary: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    by_co = holdout.get("by_company") or {}
    hanssem_ret = (by_co.get("hanssem") or {}).get("retrieval_feasible_rate", 0.0)
    musinsa_ret = (by_co.get("musinsa") or {}).get("retrieval_feasible_rate", 0.0)
    quant_gate = demo_summary.get("synthesis_gate_allowed_rate_quant", 0.0)

    expand_holdout = hanssem_ret >= 0.5 and musinsa_ret >= 0.4
    open_synthesis = quant_gate >= 0.6
    langgraph_integration = quant_gate >= 0.4 and hanssem_ret >= 0.5

    weakest = "extraction_aggregation_holdout"
    if hanssem_ret < 0.5:
        weakest = "retrieval_holdout"
    elif quant_gate < 0.3:
        weakest = "demo_aggregation_sufficiency"

    return {
        "keep_demo_company_as_dev_set": True,
        "expand_holdout_hanssem_musinsa": expand_holdout,
        "start_langgraph_handoff_integration": langgraph_integration,
        "open_synthesis_yet": open_synthesis,
        "weakest_layer": weakest,
        "priority_next": "langgraph_handoff_integration" if langgraph_integration else "holdout_harness_expansion",
        "synthesis_gate_threshold_quant": 0.6,
        "current_quant_synthesis_gate_rate": quant_gate,
        "holdout_retrieval_hanssem": hanssem_ret,
        "holdout_retrieval_musinsa": musinsa_ret,
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    arch = payload["architecture_decision"]
    reg = payload["registry_audit"]
    hold = payload["holdout_summary"]
    demo = payload["demo_readiness"]
    reusable = payload.get("reusability") or {}

    lines = [
        "# Enterprise Internal-Doc — Framework Contract",
        "",
        f"Generated: {payload['timestamp']}",
        "",
        "## 1. Abstraction layer",
        "",
        "Ba registry da tach:",
        "- `company_doc_registry` — logical documents theo cong ty",
        "- `metric_family_registry` — row aliases, semantic bridge, governance anchor, narrative probe",
        "- `source_role_registry` — role classification + synthesis gate",
        "",
        f"- So cong ty trong registry: **{reg['company_count']}**",
        f"- Logical doc generic: **{reg['logical_doc_generic']}** | pilot-only: **{reg['logical_doc_pilot_only']}**",
        f"- Rule inventory: **{reg['rule_count']}** (reusable generic **{reg['reusable_generic_rules']}**, pilot-only **{reg['pilot_only_rules']}**)",
        "",
        "### Pilot-only con lai (ly do)",
        "",
        "- `DEMO_DOCUMENTS` / `doc_evidence_csv` — CSV boost chi cho demo_company",
        "- `ROW_ALIASES` / `SEMANTIC_BRIDGE` trong code — fallback; registry merge khi co company_id",
        "- `financial_en_bridge`, `governance_financial_anchor`, `narrative_investment` — scope pilot_only trong metric_family_registry",
        "",
        "## 2. Holdout harness",
        "",
        "Harness chuan hoa: `src/enterprise_docs/holdout_harness.py`",
        "",
        "| company_id | role | probes | retrieval | extraction | aggregation |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for cid, stats in sorted((hold.get("by_company") or {}).items()):
        lines.append(
            f"| `{cid}` | {stats.get('role', '')} | {stats.get('probe_count', 0)} | "
            f"{stats.get('retrieval_feasible_rate', 0)} | {stats.get('extraction_feasible_rate', 0)} | "
            f"{stats.get('aggregation_feasible_rate', 0)} |"
        )

    lines.extend([
        "",
        "## 3. LangGraph handoff contract",
        "",
        f"- Schema version: **{payload['handoff_schema']['schema_version']}**",
        f"- Handoff allowed states: {', '.join(f'`{s}`' for s in payload['handoff_schema']['readiness_states']['handoff_allowed'])}",
        f"- Demo handoff samples: **{payload['handoff_sample_count']}**",
        f"- Demo handoff_allowed rate (quant): **{payload.get('handoff_allowed_rate_quant', 0)}**",
        "",
        "## 4. Reusability",
        "",
        f"- `reusable_system_coverage`: **{reusable.get('reusable_system_coverage', 'n/a')}**",
        "",
        "## 5. Quyet dinh he thong",
        "",
        f"- Giu `demo_company` lam dev set chinh: **{arch['keep_demo_company_as_dev_set']}**",
        f"- Mo rong holdout 한샘 / 무신사: **{arch['expand_holdout_hanssem_musinsa']}**",
        f"- Bat dau LangGraph handoff integration: **{arch['start_langgraph_handoff_integration']}**",
        f"- Mo synthesis: **{arch['open_synthesis_yet']}** (nguong quant gate >= {arch['synthesis_gate_threshold_quant']}, hien tai {arch['current_quant_synthesis_gate_rate']})",
        f"- Layer yeu nhat: **{arch['weakest_layer']}**",
        f"- Buoc tiep theo: **{arch['priority_next']}**",
        "",
        payload.get("conclusion", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"enterprise_docs_framework_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot = export_registry_snapshot()
    (out_dir / "registry_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    holdout = run_holdout_matrix(include_demo=False)
    (out_dir / "holdout_matrix.json").write_text(
        json.dumps(holdout, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    handoff_schema = export_handoff_schema()
    (out_dir / "langgraph_handoff_schema.json").write_text(
        json.dumps(handoff_schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    handoffs, demo_summary = _run_demo_handoffs()
    with (out_dir / "demo_handoff_samples.jsonl").open("w", encoding="utf-8") as f:
        for row in handoffs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    quant_handoffs = [h for h in handoffs if h.get("kind") == "quantitative"]
    allowed_quant = sum(1 for h in quant_handoffs if h.get("handoff_allowed"))
    handoff_allowed_rate_quant = round(
        allowed_quant / max(1, len(quant_handoffs)), 4
    )

    baseline = None
    if GEN_BASELINE.exists():
        baseline = json.loads(GEN_BASELINE.read_text(encoding="utf-8"))

    holdout_rows = holdout.get("matrix") or []
    reusability = analyze_reusability(
        [
            {
                "probe_id": r["probe_id"],
                "company": r["company_id"],
                "parser_ok": r["parser_ok"],
                "retrieval_feasible": r["retrieval_feasible"],
                "extraction_feasible": r["extraction_feasible"],
                "aggregation_feasible": r["aggregation_feasible"],
                "readiness_state": r["readiness_state"],
                "kind": r["kind"],
            }
            for r in holdout_rows
        ],
        demo_readiness_summary=demo_summary,
    )

    reg_audit = _registry_audit()
    arch = _architecture_decision(holdout, demo_summary, baseline)

    summary = {
        "timestamp": ts,
        "artifact_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
        "registry_paths": {
            "company_doc_registry": "data/enterprise_docs/company_doc_registry.json",
            "metric_family_registry": "data/enterprise_docs/metric_family_registry.json",
            "source_role_registry": "data/enterprise_docs/source_role_registry.json",
        },
        "registry_audit": reg_audit,
        "holdout_summary": holdout,
        "demo_readiness": demo_summary,
        "reusability": {
            "reusable_system_coverage": reusability.get("reusable_system_coverage"),
            "pilot_only_dependency": reusability.get("pilot_only_dependency"),
        },
        "handoff_schema": handoff_schema,
        "handoff_sample_count": len(handoffs),
        "handoff_allowed_rate_quant": handoff_allowed_rate_quant,
        "architecture_decision": arch,
        "baseline_generalization": str(GEN_BASELINE.relative_to(ROOT)).replace("\\", "/") if baseline else None,
        "conclusion": (
            f"Lane da co abstraction registry + holdout harness + LangGraph handoff schema; "
            f"reusable coverage {reusability.get('reusable_system_coverage')}; "
            f"quant synthesis-gate {demo_summary.get('synthesis_gate_allowed_rate_quant')}; "
            f"chua mo synthesis."
        ),
        "answers": {
            "expand_beyond_demo_company": arch["expand_holdout_hanssem_musinsa"],
            "open_synthesis": arch["open_synthesis_yet"],
            "langgraph_integration": arch["start_langgraph_handoff_integration"],
            "next_system_step": arch["priority_next"],
        },
    }

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_report(out_dir / "report.md", summary)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
