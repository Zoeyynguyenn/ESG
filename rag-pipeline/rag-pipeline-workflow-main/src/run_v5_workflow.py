"""CLI: Version 5 product-oriented workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import BASE_DIR
from workflow_v5 import run_v5_workflow, assess_v5_status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V5 Workflow: intake -> extract -> gap -> report")
    parser.add_argument("--intake", type=str, default="", help="Duong dan intake JSON")
    parser.add_argument("--retrieval-mode", type=str, default="")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--output-dir", type=str, default="", help="artifacts/v5_runs/<run_id>")
    args = parser.parse_args(argv)

    intake_path = Path(args.intake) if args.intake else None
    if intake_path and not intake_path.is_absolute():
        intake_path = BASE_DIR / intake_path

    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = BASE_DIR / output_dir

    print("V5 workflow starting...")
    result = run_v5_workflow(
        intake_path=intake_path,
        retrieval_mode=args.retrieval_mode or None,
        top_k=args.top_k,
        run_id=args.run_id or None,
        output_dir=output_dir,
    )

    gap = result.get("gap_analysis", {})
    sample = {
        "missing_fields_top3": [m["field"] for m in gap.get("missing_fields", [])[:3]],
        "conflict_fields": [c["field"] for c in gap.get("conflict_fields", [])],
        "priority_risk_high": [
            p for p in gap.get("priority_risk", []) if p.get("risk_level") == "high"
        ],
    }

    advance = "co_the" if result["v5_status"] == "pass_with_limits" else "chua"
    result["advance_v6"] = advance

    out = {
        "v5_status": result["v5_status"],
        "advance_v6": advance,
        "workflow_metrics": result["workflow_metrics"],
        "run_dir": result["run_dir"],
        "report_path": result["report_path"],
        "gap_sample": sample,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
