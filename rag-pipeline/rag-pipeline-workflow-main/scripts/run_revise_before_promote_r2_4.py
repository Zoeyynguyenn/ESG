"""Run revise-before-promote on 5-row Silver QC pilot."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QC_RESULT = ROOT / "data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_qc_result_r2_4.jsonl"
PILOT_UNITS = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_10_compact_r2_4.jsonl"
OUTPUT = ROOT / "data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_qc_revised_r2_4.jsonl"
REPORT = ROOT / "reports/golden_set_revise_before_promote_r2_4.md"


def main() -> int:
    from golden_set.io_utils import read_jsonl
    from golden_set.revise_before_promote_r2_4 import run_revise_before_promote, write_revise_report

    summary = run_revise_before_promote(
        qc_result_path=QC_RESULT,
        pilot_units_path=PILOT_UNITS,
        output_path=OUTPUT,
    )
    rows = read_jsonl(OUTPUT)
    write_revise_report(summary, rows, REPORT)
    (ROOT / "reports/_revise_before_promote_r2_4_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(
        {
            "salvaged": summary["salvaged_from_revise"],
            "after_promo": summary["after_promotion_candidate"],
            "ids": summary["promote_ready_ids"],
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
