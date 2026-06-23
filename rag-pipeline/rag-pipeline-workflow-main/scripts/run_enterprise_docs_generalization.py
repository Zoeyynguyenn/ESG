#!/usr/bin/env python3
"""Enterprise internal-doc lane: generalization hardening + holdout sanity check."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.doc_router import build_evidence_plan
from enterprise_docs.readiness_model import assess_readiness, summarize_readiness
from enterprise_docs.reusability_audit import analyze_reusability
from enterprise_docs.retrieval_index import score_units
from enterprise_docs.rule_inventory import export_rule_inventory
from enterprise_docs.structured_extractor import probe_candidates_in_units

HANSSEM_CORPUS_SOURCE = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible.jsonl"
HOLDOUT_PROBES = ROOT / "data/enterprise_docs/holdout_sanity_probes.jsonl"
DEMO_SINGLE = ROOT / "data/enterprise_docs/demo_company/eval_subset_single.jsonl"
DEMO_CROSS = ROOT / "data/enterprise_docs/demo_company/eval_subset_cross.jsonl"
DEMO_CORPUS = ROOT / "data/enterprise_docs/demo_company/corpus_units.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _golden_to_enterprise_unit(row: dict[str, Any], company_id: str = "hanssem") -> dict[str, Any]:
    doc_id = re.sub(r"[^0-9a-zA-Z가-힣_]+", "_", str(row.get("section_path") or "evidence"))[:80]
    text = str(row.get("text") or "")
    rid = str(row.get("record_id") or row.get("unit_id") or "unit")
    return {
        "unit_id": f"{company_id}::{doc_id}::{rid[:12]}",
        "company_id": company_id,
        "document_id": doc_id,
        "source_type": str(row.get("source_type") or "narrative"),
        "text": text,
        "search_text": text,
        "evidence_text": text,
        "section": row.get("section_path"),
        "metadata": {"golden_record_id": rid},
    }


def _probe_has_signal(text: str, expected: str) -> bool:
    if not text or not expected:
        return False
    for part in expected.split("|"):
        part = part.strip()
        if part and part.lower() in text.lower():
            return True
    return False


def _run_holdout_sanity(
    probes: list[dict[str, Any]],
    corpus_units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index, logical_map = build_index_from_units(corpus_units, company_id="hanssem")
    unit_lookup = {str(u["unit_id"]): u for u in corpus_units}
    results: list[dict[str, Any]] = []

    for probe in probes:
        plan = asdict(build_evidence_plan(probe))
        plan["item_id"] = probe["probe_id"]
        plan["question"] = probe["question"]
        plan["kind"] = probe["kind"]
        plan["answer_mode"] = "single_document_answer"

        parser_ok = all(
            bool(str(u.get("evidence_text") or u.get("text") or "").strip())
            for u in corpus_units[:3]
        ) and len(corpus_units) > 0

        ranked = score_units(probe["question"], index, pool=16)
        top_texts = [
            str(u.get("evidence_text") or u.get("text") or "")
            for u, _ in ranked[:5]
        ]
        top_text = top_texts[0] if top_texts else ""

        retrieval_feasible = bool(ranked) and any(
            _probe_has_signal(t, str(probe.get("expected_signal") or ""))
            for t in top_texts
        )

        candidates = probe_candidates_in_units(
            plan,
            [u for u, _ in ranked[:8]],
            min_score=0.1,
            include_narrative=True,
        )
        extraction_feasible = (
            len(candidates) > 0
            or (
                probe["kind"] == "quantitative"
                and any(re.search(r"\d+", t) for t in top_texts)
                and retrieval_feasible
            )
        )

        # Holdout: assess readiness from retrieval layer only (no demo logical map)
        if retrieval_feasible and probe["kind"] == "qualitative":
            readiness_state = "not_ready_for_synthesis"
            readiness_reason = "qualitative_requires_synthesis_gate"
            aggregation_feasible = False
        elif extraction_feasible:
            readiness_state = "extraction_ready"
            readiness_reason = "holdout_narrative_or_table_feasible"
            aggregation_feasible = True
        elif retrieval_feasible:
            readiness_state = "retrieval_ready"
            readiness_reason = "holdout_retrieval_signal_hit"
            aggregation_feasible = False
        else:
            readiness_state = "coverage_gap"
            readiness_reason = "holdout_no_signal_in_top5"
            aggregation_feasible = False

        reuse_tags: list[str] = []
        if parser_ok:
            reuse_tags.append("reusable:ED-PARSE-001")
        if ranked:
            reuse_tags.append("reusable:ED-RETR-001")
        if not logical_map:
            reuse_tags.append("corpus_specific:ED-MAP-001_no_logical_mapping")
        if probe["kind"] == "qualitative":
            reuse_tags.append("reusable:ED-QUAL-001")
            reuse_tags.append("needs_abstraction:synthesis_gate")
        if probe["pattern_family"] in ("climate_narrative", "governance_numeric_narrative"):
            reuse_tags.append("needs_abstraction:ED-EXT-005_narrative_patterns")
        if not extraction_feasible and probe["kind"] == "quantitative":
            reuse_tags.append("corpus_specific:narrative_only_no_table")

        results.append({
            "probe_id": probe["probe_id"],
            "company": probe["company"],
            "pattern_family": probe["pattern_family"],
            "kind": probe["kind"],
            "parser_ok": parser_ok,
            "retrieval_feasible": retrieval_feasible,
            "extraction_feasible": extraction_feasible,
            "aggregation_feasible": aggregation_feasible,
            "readiness_state": readiness_state,
            "readiness_reason": readiness_reason,
            "top_unit_preview": top_text[:200],
            "reuse_tags": reuse_tags,
            "note": "feasibility_only_no_gold_answer",
        })
    return results


def _run_demo_readiness() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units = _load_jsonl(DEMO_CORPUS)
    lookup = {str(u["unit_id"]): u for u in units}
    index, logical_map = build_index_from_units(units)
    rows: list[dict[str, Any]] = []

    for plan in _load_jsonl(DEMO_SINGLE) + _load_jsonl(DEMO_CROSS):
        ret = retrieve_for_plan(plan, index, logical_map)
        rows.append(
            assess_readiness(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
        )
    return rows, summarize_readiness(rows)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    arch = summary.get("architecture_decision") or {}
    hold = summary.get("holdout_summary") or {}
    demo = summary.get("demo_readiness") or {}

    lines = [
        "# Enterprise Internal-Doc — Generalization Hardening",
        "",
        f"Generated: {summary['timestamp']}",
        "",
        "## Rule inventory",
        "",
        f"- Total rules: **{summary['rule_inventory']['rule_count']}**",
        f"- Reusable generic: **{summary['rule_inventory']['by_class'].get('reusable_generic_rule', 0)}**",
        f"- Pilot-only: **{summary['rule_inventory']['by_class'].get('pilot_only_rule', 0)}**",
        f"- `reusable_system_coverage`: **{summary['reusability_audit']['reusable_system_coverage']}**",
        "",
        "## Demo readiness (development set)",
        "",
        f"- Cases: **{demo.get('total', 0)}**",
        f"- Quant synthesis-gate allowed rate: **{demo.get('synthesis_gate_allowed_rate_quant', 0)}**",
        "",
        "### Readiness counts",
        "",
    ]
    for state, count in sorted((demo.get("readiness_counts") or {}).items()):
        lines.append(f"- `{state}`: {count}")

    lines.extend([
        "",
        "## Holdout sanity (한샘)",
        "",
        f"- Probes: **{hold.get('probe_count', 0)}**",
        f"- Parser OK rate: **{hold.get('parser_ok_rate', 0)}**",
        f"- Retrieval feasible: **{hold.get('retrieval_feasible_rate', 0)}**",
        f"- Extraction feasible: **{hold.get('extraction_feasible_rate', 0)}**",
        "",
        "## Architecture decision",
        "",
        f"- Expand holdout: **{arch.get('expand_to_hanssem_musinsa_holdout')}**",
        f"- Open synthesis: **{arch.get('open_synthesis_yet')}**",
        f"- Weakest layer: **{arch.get('weakest_layer')}**",
        f"- Priority next: **{arch.get('priority_next')}**",
        "",
        summary.get("conclusion", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"enterprise_docs_generalization_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    inventory_path = ROOT / "data/enterprise_docs/rule_inventory.json"
    inventory = export_rule_inventory(str(inventory_path))

    demo_rows, demo_summary = _run_demo_readiness()

    hanssem_units = [
        _golden_to_enterprise_unit(r) for r in _load_jsonl(HANSSEM_CORPUS_SOURCE)
    ]
    holdout_results = _run_holdout_sanity(_load_jsonl(HOLDOUT_PROBES), hanssem_units)

    audit = analyze_reusability(holdout_results, demo_readiness_summary=demo_summary)
    audit_path = ROOT / "reports/enterprise_docs_reusability_audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    arch = audit["architecture_recommendation"]
    summary = {
        "timestamp": ts,
        "rule_inventory": {
            "path": str(inventory_path.relative_to(ROOT)).replace("\\", "/"),
            "rule_count": inventory["rule_count"],
            "by_class": inventory["by_class"],
        },
        "reusability_audit": {
            "path": str(audit_path.relative_to(ROOT)).replace("\\", "/"),
            "reusable_system_coverage": audit["reusable_system_coverage"],
            "pilot_only_dependency": audit["pilot_only_dependency"],
            "productize_candidates": audit["productize_candidates"],
            "abstraction_backlog": audit["abstraction_backlog"],
        },
        "demo_readiness": demo_summary,
        "demo_readiness_rows": demo_rows,
        "holdout_summary": audit["holdout_sanity"],
        "holdout_corpus_note": (
            "Holdout corpus = pilot_hanssem_15_eligible (narrative SR chunks); "
            "feasibility only, no gold answer scoring"
        ),
        "architecture_decision": arch,
        "open_synthesis": False,
        "conclusion": (
            f"Lane co {audit['reusable_generic_count']} reusable rules / {audit['rule_count']} total; "
            f"demo quant synthesis-gate {demo_summary.get('synthesis_gate_allowed_rate_quant')}; "
            f"holdout retrieval {audit['holdout_sanity']['retrieval_feasible_rate']}; "
            f"chua mo synthesis; can abstraction truoc full holdout."
        ),
        "answers": {
            "expand_beyond_demo_company": arch.get("expand_to_hanssem_musinsa_holdout"),
            "open_synthesis": arch.get("open_synthesis_yet"),
            "weakest_layer": arch.get("weakest_layer"),
            "next_system_step": arch.get("priority_next"),
        },
    }

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (out_dir / "holdout_sanity_results.jsonl").open("w", encoding="utf-8") as f:
        for row in holdout_results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out_dir / "demo_readiness.jsonl").open("w", encoding="utf-8") as f:
        for row in demo_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _write_report(out_dir / "report.md", summary)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
