#!/usr/bin/env python3
"""Cross-document core capability benchmark — system hardening, not demo score chase."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.crossdoc_capability_benchmark import (  # noqa: E402
    run_capability_benchmark,
    write_benchmark_artifacts,
)
from enterprise_docs.crossdoc_case_builder import write_capability_cases_jsonl  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_crossdoc_core_capability_{ts}")).resolve()

    cases_meta = write_capability_cases_jsonl()
    bench = run_capability_benchmark()
    summary = write_benchmark_artifacts(out_dir, bench, cases_meta=cases_meta)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(
        json.dumps(
            {"out_dir": str(out_dir), "mandatory_answers": summary.get("mandatory_answers")},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
