"""Run Silver QC pilot hạn chế on 5 compact usable rows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DISTILLED = ROOT / "data/golden_set/v2/step2_silver/pilot_hanssem_10_compact_distilled_r2_4.jsonl"
PILOT_UNITS = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_10_compact_r2_4.jsonl"
QC_INPUT = ROOT / "data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_usable_for_qc_r2_4.jsonl"
QC_OUTPUT = ROOT / "data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_qc_result_r2_4.jsonl"
QC_CSV = ROOT / "data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_qc_review.csv"
REPORT = ROOT / "reports/golden_set_silver_qc_pilot_r2_4.md"
SUMMARY_JSON = ROOT / "reports/_silver_qc_pilot_r2_4_summary.json"


def main() -> int:
    from golden_set.io_utils import read_jsonl
    from golden_set.step4_silver_qc_pilot_r2_4 import run_silver_qc_pilot_r24, write_qc_report

    usable_ids = {
        "SV2-P24-0001",
        "SV2-P24-0002",
        "SV2-P24-0003",
        "SV2-P24-0004",
        "SV2-P24-0005",
    }

    summary = run_silver_qc_pilot_r24(
        distilled_path=DISTILLED,
        pilot_units_path=PILOT_UNITS,
        qc_input_path=QC_INPUT,
        qc_output_path=QC_OUTPUT,
        csv_path=QC_CSV,
        usable_ids=usable_ids,
    )
    qc_rows = read_jsonl(QC_OUTPUT)
    write_qc_report(summary, qc_rows, REPORT)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(
        {
            "pass": summary["pass_count"],
            "revise": summary["revise_count"],
            "reject": summary["reject_count"],
            "promotion_candidate": summary["promotion_candidate_count"],
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
