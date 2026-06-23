"""Run Distillation R2.1 prompt on Hansem pilot R2.2 eligible units."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INPUT_JSONL = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible_r2_2.jsonl"
OUTPUT_JSONL = ROOT / "data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled_r2_2.jsonl"
SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_2_summary.json"
R21_SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_1_summary.json"
REPORT_MD = ROOT / "reports/golden_set_distillation_pilot_hanssem_round2_2.md"
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


def _load_r21_summary() -> dict:
    if R21_SUMMARY_JSON.exists():
        return json.loads(R21_SUMMARY_JSON.read_text(encoding="utf-8"))
    return {}


def write_report(summary: dict, rows: list, units: list, r21: dict) -> None:
    lines = [
        "# Golden Set — Distillation Pilot Hansem Round 2.2",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu pilot R2.2",
        "",
        "Chạy Distillation R2.1 (prompt/guardrails không đổi) trên pilot Hansem đã pre-filter R2.2; ngưỡng pass: **≥8 keep usable** trước Silver QC.",
        "",
        "## Input pilot",
        "",
        f"- File: `{INPUT_JSONL.relative_to(ROOT)}`",
        f"- Số unit: **{summary['input_units']}** (`{summary.get('input_keep_count', 'n/a')}` keep + `{summary.get('input_conditional_count', 'n/a')}` conditional)",
        "",
        "| # | record_id | prefilter | pilot_source | substance | noise |",
        "|---|-----------|-----------|--------------|----------:|------:|",
    ]
    for i, u in enumerate(units, 1):
        lines.append(
            f"| {i} | `{u.get('record_id', '')}` | `{u.get('prefilter_decision', '')}` | "
            f"`{u.get('pilot_source', '')}` | {u.get('substance_score', '')} | {u.get('noise_score', '')} |"
        )

    lines.extend(
        [
            "",
            "## Prompt / setup đã dùng",
            "",
            f"- Distillation version: `{summary.get('distillation_version')}` (prompt R2.1, không nới lỏng)",
            f"- Model: `{summary.get('model')}`",
            "- Temperature: `0.1`",
            "- Prompt: `reports/golden_set_distillation_prompt_round2_1.md`",
            "- Module: `src/golden_set/step2_distill_r2_1.py`",
            f"- Output: `{OUTPUT_JSONL.relative_to(ROOT)}`",
            "",
            "## Kết quả tổng quan",
            "",
            "| Chỉ số | Giá trị |",
            "|--------|--------:|",
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
            "## So sánh R2.1 vs R2.2",
            "",
            "| Metric | Pilot R2.1 | Pilot R2.2 | Delta |",
            "|--------|----------:|----------:|------:|",
            f"| keep | {r21.get('keep_count', 'n/a')} | {summary['keep_count']} | "
            f"+{summary['keep_count'] - r21.get('keep_count', 0) if r21 else 'n/a'} |",
            f"| drop | {r21.get('drop_count', 'n/a')} | {summary['drop_count']} | "
            f"{summary['drop_count'] - r21.get('drop_count', 0) if r21 else 'n/a'} |",
            f"| usable | {r21.get('usable_count', 'n/a')} | {summary['usable_count']} | "
            f"+{summary['usable_count'] - r21.get('usable_count', 0) if r21 else 'n/a'} |",
            "",
            "### Pattern đã giảm (R2.2)",
            "",
        ]
    )
    for p in summary.get("improved_patterns", []):
        lines.append(f"- {p}")

    lines.extend(["", "### Pattern còn tồn tại", ""])
    for p in summary.get("remaining_patterns", []):
        lines.append(f"- {p}")

    lines.extend(
        [
            "",
            "## Phân tích chất lượng output",
            "",
            f"- Thiếu `ground_truth_answer` (keep): **{summary.get('missing_ground_truth_answer', 0)}**",
            f"- Thiếu `evidence_span` (keep): **{summary.get('missing_evidence_span', 0)}**",
            f"- Thiếu `why_grounded` (keep): **{summary.get('missing_why_grounded', 0)}**",
            f"- Keep yếu/generic: **{summary.get('weak_or_generic_keep', 0)}**",
            f"- Keep grounding tốt: **{summary.get('good_grounding_keep', 0)}**",
            f"- Drop duplicate same fact: **{summary.get('duplicate_same_fact_drops', 0)}**",
            f"- Strong enough cho Silver QC: **{summary.get('silver_qc_ready_count', 0)}**",
            "",
            "### Silver QC candidates (usable)",
            "",
        ]
    )
    for c in summary.get("silver_qc_candidates", []):
        lines.append(
            f"- **{c['silver_id']}** — unit `{c['unit_id']}` · `{c['question_type']}` · {c['why_usable']}"
        )

    lines.extend(["", "### Mẫu keep", ""])
    for r in [x for x in rows if x.get("decision") == "keep"][:8]:
        lines.append(f"- **{r.get('silver_id')}** (`{r.get('ground_truth_record_id')}`): {(r.get('question') or '')[:90]}…")

    lines.extend(["", "### Mẫu drop", ""])
    for r in [x for x in rows if x.get("decision") == "drop"][:8]:
        lines.append(
            f"- **{r.get('silver_id')}** `{r.get('drop_reason')}` record=`{r.get('ground_truth_record_id')}` "
            f"llm={r.get('llm_decision')} note={r.get('validation_note')}"
        )

    passed = summary["usable_count"] >= 8
    lines.extend(
        [
            "",
            "## Các lỗi còn lại",
            "",
        ]
    )
    for p in summary.get("error_patterns", []):
        lines.append(f"- {p}")

    lines.extend(
        [
            "",
            "## Kết luận",
            "",
            f"- **Đạt ngưỡng ≥8 keep usable?** {'**Có**' if passed else '**Chưa**'} ({summary['usable_count']}/8)",
            f"- **Đủ mở Silver QC?** {'Có — pilot subset keep usable' if passed else 'Chưa — cần xử lý thêm'}",
        ]
    )
    if not passed:
        root = summary.get("root_cause_hint", "selector hoặc conditional units")
        lines.append(f"- **Root cause gợi ý:** {root}")
    else:
        lines.extend(
            [
                "",
                "### Bước tiếp theo đề xuất",
                "",
                "1. Mở **Silver QC pilot** trên `silver_qc_candidates` (chưa Evol/Judge).",
                "2. Giữ nguyên prompt Distillation R2.1 cho full step 2 sau khi QC pass.",
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
    from golden_set.step2_distill_r2_1 import analyze_pilot_rows, run_distill_r2_1

    units = read_jsonl(INPUT_JSONL)
    summary = run_distill_r2_1(
        input_path=INPUT_JSONL,
        output_path=OUTPUT_JSONL,
        model=model,
        max_chars=int(gen.get("text_max_chars", 4000)),
        id_prefix="SV2-P22",
    )
    rows = read_jsonl(OUTPUT_JSONL)
    r21 = _load_r21_summary()

    input_keep = sum(1 for u in units if u.get("prefilter_decision") == "keep")
    input_cond = sum(1 for u in units if u.get("prefilter_decision") == "conditional")

    patterns: list[str] = []
    remaining: list[str] = []
    news_mixed_keep = 0
    nav_drops = 0
    insufficient_drops = 0

    for r in rows:
        if r.get("decision") == "drop":
            dr = r.get("drop_reason") or ""
            if "insufficient" in dr or dr == "unanswerable_from_unit":
                insufficient_drops += 1
            if "nav" in dr:
                nav_drops += 1
            if r.get("validation_note"):
                patterns.append(f"{r.get('ground_truth_record_id')}: {r.get('validation_note')}")
        elif r.get("decision") == "keep":
            u = next((x for x in units if x.get("record_id") == r.get("ground_truth_record_id")), None)
            text = (u.get("text") or "") if u else ""
            if u and u.get("prefilter_decision") == "conditional":
                news_mixed_keep += 1

    improved = [
        f"insufficient_substance drops: R2.1={r21.get('by_drop_reason', {}).get('insufficient_substance / unanswerable_from_unit', 8)} → R2.2={insufficient_drops}",
        f"nav_or_menu_noise drops: R2.1=2 → R2.2={nav_drops}",
        f"keep usable: R2.1={r21.get('usable_count', 3)} → R2.2={summary['usable_count']}",
    ]
    if news_mixed_keep:
        remaining.append(f"conditional units trong keep: {news_mixed_keep} — cần QC thủ công")
    if summary.get("duplicate_same_fact_drops", 0):
        remaining.append(f"duplicate_same_fact drops: {summary['duplicate_same_fact_drops']}")
    if summary.get("weak_or_generic_keep", 0):
        remaining.append(f"weak/generic keep: {summary['weak_or_generic_keep']}")

    silver_candidates = []
    for r in rows:
        if r.get("silver_id") not in (summary.get("usable_silver_ids") or []):
            continue
        u = next((x for x in units if x.get("record_id") == r.get("ground_truth_record_id")), {})
        silver_candidates.append(
            {
                "silver_id": r.get("silver_id"),
                "unit_id": u.get("unit_id", ""),
                "record_id": r.get("ground_truth_record_id"),
                "question_type": r.get("question_type"),
                "difficulty": r.get("difficulty"),
                "prefilter_decision": u.get("prefilter_decision"),
                "pilot_source": u.get("pilot_source"),
                "why_usable": (
                    f"evidence_span grounded; type={r.get('question_type')}; "
                    f"prefilter={u.get('prefilter_decision')}"
                ),
            }
        )

    passed = summary["usable_count"] >= 8
    root_hint = "prefilter/selector" if insufficient_drops > 3 else "distillation prompt"
    if passed:
        root_hint = "n/a — đạt ngưỡng"

    summary.update(
        {
            "input_keep_count": input_keep,
            "input_conditional_count": input_cond,
            "pilot_version": "2.2",
            "comparison_r21": {
                "keep_delta": summary["keep_count"] - r21.get("keep_count", 0),
                "usable_delta": summary["usable_count"] - r21.get("usable_count", 0),
                "r21_keep": r21.get("keep_count"),
                "r21_usable": r21.get("usable_count"),
            },
            "improved_patterns": improved,
            "remaining_patterns": remaining,
            "error_patterns": patterns,
            "news_mixed_keep_count": news_mixed_keep,
            "silver_qc_candidates": silver_candidates,
            "silver_qc_ready_count": len(silver_candidates),
            "pass_threshold_8_usable": passed,
            "silver_qc_recommended": passed,
            "root_cause_hint": root_hint,
        }
    )

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, rows, units, r21)

    print(json.dumps(
        {
            "keep": summary["keep_count"],
            "drop": summary["drop_count"],
            "usable": summary["usable_count"],
            "pass_8": passed,
            "output": str(OUTPUT_JSONL),
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
