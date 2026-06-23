#!/usr/bin/env python3
"""Audit rule reusability for dataset-excel extractive RAG (baseline v5 freeze)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_excel.reusability_audit import analyze_reusability  # noqa: E402
from dataset_excel.rule_registry import export_rule_inventory  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit dataset-excel rule reusability")
    parser.add_argument(
        "--results",
        default="reports/goldns_emni_rag_eval_latest.json",
        help="Path to latest eval summary JSON (used for baseline metrics only if --results-jsonl not set)",
    )
    parser.add_argument(
        "--results-jsonl",
        default=None,
        help="Per-question results JSONL from eval run",
    )
    parser.add_argument(
        "--output",
        default="reports/dataset_excel_reusability_audit.json",
    )
    args = parser.parse_args()

    inventory_path = ROOT / "data/dataset_excel/rule_inventory.json"
    export_rule_inventory(inventory_path)

    results_path = ROOT / args.results
    summary = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
    baseline_metrics = {
        k: summary[k]
        for k in (
            "retrieval_hit_top1",
            "answer_accuracy",
            "abstain_accuracy",
            "overall_score",
        )
        if k in summary
    }

    if args.results_jsonl:
        results = _read_jsonl(ROOT / args.results_jsonl)
    else:
        # Find latest results.jsonl under reports/
        candidates = sorted((ROOT / "reports").glob("goldns_emni_rag_eval_*/results.jsonl"))
        if not candidates:
            raise SystemExit("No results.jsonl found; run eval first or pass --results-jsonl")
        results = _read_jsonl(candidates[-1])

    audit = analyze_reusability(results, baseline_metrics=baseline_metrics or None)
    audit["rule_inventory_path"] = str(inventory_path.relative_to(ROOT)).replace("\\", "/")
    audit["results_source"] = str(args.results_jsonl or candidates[-1].relative_to(ROOT)).replace("\\", "/")

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
