from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.build_reference_seed_workbook import run_reference_seed_builder


def main() -> int:
    out_dir = ROOT / "data" / "golden_set" / "v2" / "reference_style"
    summary = run_reference_seed_builder(
        input_path=ROOT / "data" / "golden_set" / "v2" / "step1_corpus_units" / "corpus_units.jsonl",
        output_jsonl=out_dir / "reference_seed_candidates_v1.jsonl",
        output_xlsx=out_dir / "reference_seed_workbook_v1.xlsx",
        target_total=24,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
