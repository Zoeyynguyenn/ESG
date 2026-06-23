"""Run Distillation R2.1 pilot on Hanssem 15 eligible units."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INPUT_JSONL = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible.jsonl"
OUTPUT_JSONL = ROOT / "data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled.jsonl"
SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_1_summary.json"
REPORT_MD = ROOT / "reports/golden_set_distillation_pilot_hanssem_round2_1.md"
CONFIG = ROOT / "configs/golden_set_pipeline.yaml"


def _load_dotenv() -> None:
    for name in (".env.local", ".env"):
        p = ROOT / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k, v)


def write_report(summary: dict, rows: list, units: list) -> None:
    unit_map = {u["unit_id"]: u for u in units}
    lines = [
        "# Golden Set — Distillation Pilot Hansem Round 2.1",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu pilot",
        "",
        "Kiểm tra chất lượng Distillation R2.1 trên 15 corpus unit `한샘` đã pre-filter, trước khi mở full step 2.",
        "",
        "## Input pilot",
        "",
        f"- File: `{INPUT_JSONL.relative_to(ROOT)}`",
        f"- Số unit: **{summary['input_units']}**",
        "",
        "| # | unit_id | record_id | prefilter_rule |",
        "|---|---------|-----------|----------------|",
    ]
    for i, u in enumerate(units, 1):
        lines.append(
            f"| {i} | `{u.get('unit_id', '')}` | `{u.get('record_id', '')}` | `{u.get('prefilter_rule_id', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Prompt / setup",
            "",
            f"- Distillation version: `{summary.get('distillation_version')}`",
            f"- Model: `{summary.get('model')}`",
            f"- Temperature: `0.1`",
            f"- Prompt: `reports/golden_set_distillation_prompt_round2_1.md` (runtime: `src/golden_set/step2_distill_r2_1.py`)",
            f"- Post-validation: evidence_span ⊆ unit, answer-span overlap, dedupe fingerprint, weak-question heuristics",
            "",
            "## Kết quả tổng quan",
            "",
            f"| Chỉ số | Giá trị |",
            f"|--------|--------:|",
            f"| Input units | {summary['input_units']} |",
            f"| Output rows | {summary['output_rows']} |",
            f"| decision=keep | {summary['keep_count']} |",
            f"| decision=drop | {summary['drop_count']} |",
            f"| usable (sau audit) | {summary['usable_count']} |",
            "",
            "### Breakdown question_type (keep)",
            "",
            "| question_type | count |",
            "|---------------|------:|",
        ]
    )
    for k, v in sorted(summary.get("by_question_type", {}).items()):
        lines.append(f"| `{k}` | {v} |")

    lines.extend(["", "### Breakdown difficulty (keep)", "", "| difficulty | count |", "|------------|------:|"])
    for k, v in sorted(summary.get("by_difficulty", {}).items()):
        lines.append(f"| `{k}` | {v} |")

    lines.extend(
        [
            "",
            "### Drop reasons",
            "",
            "| drop_reason | count |",
            "|-------------|------:|",
        ]
    )
    for k, v in sorted(summary.get("by_drop_reason", {}).items()):
        lines.append(f"| `{k}` | {v} |")

    lines.extend(
        [
            "",
            "## Phân tích chất lượng output",
            "",
            f"- Thiếu `ground_truth_answer` (keep): **{summary.get('missing_ground_truth_answer', 0)}**",
            f"- Thiếu `evidence_span` (keep): **{summary.get('missing_evidence_span', 0)}**",
            f"- Thiếu `why_grounded` (keep): **{summary.get('missing_why_grounded', 0)}**",
            f"- Keep yếu/generic (heuristic): **{summary.get('weak_or_generic_keep', 0)}**",
            f"- Keep grounding tốt: **{summary.get('good_grounding_keep', 0)}**",
            f"- Drop duplicate same fact: **{summary.get('duplicate_same_fact_drops', 0)}**",
            "",
            "### Mẫu keep (tối đa 5)",
            "",
        ]
    )
    for r in [x for x in rows if x.get("decision") == "keep"][:5]:
        lines.append(f"- **{r.get('silver_id')}** — Q: {(r.get('question') or '')[:80]}…")
        lines.append(f"  - span: `{(r.get('evidence_span') or '')[:100]}…`")

    lines.extend(["", "### Mẫu drop (tối đa 5)", ""])
    for r in [x for x in rows if x.get("decision") == "drop"][:5]:
        lines.append(
            f"- **{r.get('silver_id')}** (`{r.get('drop_reason')}`) record=`{r.get('ground_truth_record_id')}` "
            f"llm={r.get('llm_decision')} note={r.get('validation_note')}"
        )

    lines.extend(
        [
            "",
            "## Các lỗi còn gặp",
            "",
        ]
    )
    error_patterns = summary.get("error_patterns") or []
    if error_patterns:
        for p in error_patterns:
            lines.append(f"- {p}")
    else:
        lines.append("- (xem drop_reason và validation_note trong summary JSON)")

    lines.extend(
        [
            "",
            "## Đánh giá",
            "",
            f"- **Đủ sạch cho Silver QC?** {'Có — với tập keep hiện tại' if summary['usable_count'] >= 8 else 'Chưa — cần siết thêm trước QC'}",
            f"- **Siết prompt?** {'Có thể cần nhẹ' if summary.get('weak_or_generic_keep', 0) > 0 else 'Chưa bắt buộc ngay'}",
            f"- **Siết prefilter?** {'Có — một số unit news-mixed vẫn vào pilot' if summary.get('drop_count', 0) < 5 else 'Ưu tiên thấp — LLM drop đã bắt được phần lớn'}",
            "",
            "## Kết luận và bước kế tiếp",
            "",
            "1. Review thủ công các row `usable` trong `pilot_hanssem_15_distilled.jsonl`.",
            "2. Nếu usable ≥ 8: mở **Silver QC** trên subset keep (chưa Evol/Judge).",
            "3. Nếu nhiều drop do news-mixed unit: **siết prefilter** loại article chrome trước pilot.",
            "4. Chưa chạy full step 2 / benchmark.",
        ]
    )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    _load_dotenv()
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    gen = cfg.get("generation") or {}
    model = str(gen.get("llm_model", "gpt-4o-mini"))

    from golden_set.io_utils import read_jsonl
    from golden_set.step2_distill_r2_1 import run_distill_r2_1

    units = read_jsonl(INPUT_JSONL)
    summary = run_distill_r2_1(
        input_path=INPUT_JSONL,
        output_path=OUTPUT_JSONL,
        model=model,
        max_chars=int(gen.get("text_max_chars", 4000)),
    )
    rows = read_jsonl(OUTPUT_JSONL)

    patterns: list[str] = []
    for r in rows:
        if r.get("decision") == "drop" and r.get("validation_note"):
            patterns.append(f"{r.get('ground_truth_record_id')}: {r.get('validation_note')}")

    news_mixed = 0
    for r in rows:
        if r.get("decision") != "keep":
            continue
        u = next((x for x in units if x.get("record_id") == r.get("ground_truth_record_id")), None)
        text = (u.get("text") or "") if u else ""
        if "기자" in text or "뉴스 듣기" in text or "Copyright" in text:
            news_mixed += 1
    if news_mixed:
        patterns.append(
            f"news_mixed_unit_kept_by_llm: {news_mixed} row(s) — cân nhắc siết prefilter R6"
        )
    summary["error_patterns"] = patterns
    summary["news_mixed_keep_count"] = news_mixed

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, rows, units)

    print(json.dumps(
        {
            "keep": summary["keep_count"],
            "drop": summary["drop_count"],
            "usable": summary["usable_count"],
            "output": str(OUTPUT_JSONL),
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
