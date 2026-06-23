"""CLI: Version 6 advanced orchestration workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import BASE_DIR
from orchestrator_v6 import run_v6_workflow


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V6: route + verify + conflict resolve")
    parser.add_argument("--intake", type=str, default="")
    parser.add_argument("--retrieval-mode", type=str, default="")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--output-dir", type=str, default="")
    parser.add_argument("--v5-baseline-run", type=str, default="artifacts/v5_runs/demo_v5_001")
    args = parser.parse_args(argv)

    intake_path = Path(args.intake) if args.intake else None
    if intake_path and not intake_path.is_absolute():
        intake_path = BASE_DIR / intake_path
    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir and not output_dir.is_absolute():
        output_dir = BASE_DIR / output_dir
    v5_base = Path(args.v5_baseline_run)
    if not v5_base.is_absolute():
        v5_base = BASE_DIR / v5_base

    print("V6 workflow starting...")
    result = run_v6_workflow(
        intake_path=intake_path,
        retrieval_mode=args.retrieval_mode or None,
        top_k=args.top_k,
        run_id=args.run_id or None,
        output_dir=output_dir,
        v5_baseline_run=v5_base,
    )

    verified_examples = []
    for r in result["profile"].get("records", []):
        if r.get("verified_by_v6") or r.get("conflict_resolved"):
            verified_examples.append(
                {
                    "field": r.get("field"),
                    "value": r.get("value"),
                    "status": r.get("status"),
                    "source": r.get("source"),
                    "strategy": r.get("verification_strategy"),
                }
            )

    out = {
        "v6_status": result["v6_status"],
        "roadmap_decision": result["roadmap_decision"],
        "v6_metrics": result["v6_metrics"],
        "delta": result["delta"],
        "run_dir": result["run_dir"],
        "report_path": result["report_path"],
        "compare_path": result["compare_path"],
        "verified_examples": verified_examples[:8],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
