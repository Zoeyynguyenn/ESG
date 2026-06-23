"""Run Distillation R2.1 prompt on Hansem pilot R2.3 eligible units."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INPUT_JSONL = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible_r2_3.jsonl"
OUTPUT_JSONL = ROOT / "data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled_r2_3.jsonl"
SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_3_summary.json"
R22_SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_2_summary.json"
REPORT_MD = ROOT / "reports/golden_set_distillation_pilot_hanssem_round2_3.md"
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


def _load_r22_summary() -> dict:
    if R22_SUMMARY_JSON.exists():
        return json.loads(R22_SUMMARY_JSON.read_text(encoding="utf-8"))
    return {}


def write_report(summary: dict, rows: list, units: list, r22: dict) -> None:
    lines = [
        "# Golden Set — Distillation Pilot Hansem Round 2.3",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu pilot R2.3",
        "",
        "Chạy Distillation R2.1 (prompt/guardrails không đổi) trên pilot Hansem sau selector R2.3; xác nhận gate **≥8 keep usable** trước Silver QC pilot.",
        "",
        "## Input pilot",
        "",
        f"- File: `{INPUT_JSONL.relative_to(ROOT)}`",
        f"- Số unit: **{summary['input_units']}**",
        f"- Proven anchors (selector): **{summary.get('proven_anchor_count', 0)}**",
        f"- Corpus fill (selector): **{summary.get('corpus_fill_count', 0)}**",
        "",
        "| # | record_id | pilot_source | grounding_risk | selector_rank |",
        "|---|-----------|--------------|----------------|--------------:|",
    ]
    for i, u in enumerate(units, 1):
        lines.append(
            f"| {i} | `{u.get('record_id', '')}` | `{u.get('pilot_source', '')}` | "
            f"`{u.get('grounding_risk', '')}` | {u.get('selector_rank', '')} |"
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

    cmp = summary.get("comparison_r22", {})
    lines.extend(
        [
            "",
            "## So sánh với R2.2",
            "",
            "| Metric | R2.2 | R2.3 | Delta |",
            "|--------|-----:|-----:|------:|",
            f"| keep | {cmp.get('r22_keep', 'n/a')} | {summary['keep_count']} | {cmp.get('keep_delta', 'n/a'):+} |",
            f"| drop | {cmp.get('r22_drop', 'n/a')} | {summary['drop_count']} | {cmp.get('drop_delta', 'n/a'):+} |",
            f"| usable | {cmp.get('r22_usable', 'n/a')} | {summary['usable_count']} | {cmp.get('usable_delta', 'n/a'):+} |",
            f"| duplicate_same_fact drops | {r22.get('duplicate_same_fact_drops', 'n/a')} | {summary.get('duplicate_same_fact_drops', 0)} |",
            f"| ambiguous_grounding drops | {r22.get('ambiguous_grounding_drops', 'n/a')} | {summary.get('ambiguous_grounding_drops', 0)} |",
            "",
            "### Pattern đã giảm",
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
            f"- Keep weak/generic: **{summary.get('weak_or_generic_keep', 0)}**",
            f"- Keep grounding tốt: **{summary.get('good_grounding_keep', 0)}**",
            f"- Drop duplicate same fact: **{summary.get('duplicate_same_fact_drops', 0)}**",
            f"- Drop ambiguous grounding: **{summary.get('ambiguous_grounding_drops', 0)}**",
            f"- Silver QC ready: **{summary.get('silver_qc_ready_count', 0)}**",
            "",
        ]
    )

    if summary.get("pass_threshold_8_usable"):
        lines.extend(["### Silver QC pilot candidates", ""])
        for c in summary.get("silver_qc_candidates", []):
            lines.append(
                f"- **{c['silver_id']}** — unit `{c['unit_id']}` · `{c['question_type']}` · "
                f"`{c.get('difficulty', '')}` · {c['why_usable']}"
            )

    lines.extend(["", "### Mẫu keep", ""])
    for r in [x for x in rows if x.get("decision") == "keep"][:10]:
        lines.append(
            f"- **{r.get('silver_id')}** (`{r.get('ground_truth_record_id')}`): "
            f"{(r.get('question') or '')[:90]}…"
        )

    lines.extend(["", "### Mẫu drop", ""])
    for r in [x for x in rows if x.get("decision") == "drop"][:10]:
        lines.append(
            f"- **{r.get('silver_id')}** `{r.get('drop_reason')}` record=`{r.get('ground_truth_record_id')}` "
            f"note={r.get('validation_note')}"
        )

    lines.extend(["", "## Các lỗi còn lại", ""])
    for p in summary.get("error_patterns", []):
        lines.append(f"- {p}")

    passed = summary.get("pass_threshold_8_usable", False)
    lines.extend(
        [
            "",
            "## Kết luận",
            "",
            f"- **Đạt ngưỡng ≥8 keep usable?** {'**Có**' if passed else '**Chưa**'} ({summary['usable_count']}/8)",
            f"- **Đủ mở Silver QC pilot?** {'**Có**' if summary.get('silver_qc_recommended') else '**Chưa**'}",
        ]
    )
    if not passed:
        lines.append(f"- **Root cause:** {summary.get('root_cause_hint', 'selector hoặc distillation')}")
    else:
        lines.extend(
            [
                "",
                "### Bước tiếp theo",
                "",
                "1. Mở **Silver QC pilot** trên các candidate ở trên (chưa Evol/Judge).",
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
    from golden_set.step2_distill_r2_1 import run_distill_r2_1

    units = read_jsonl(INPUT_JSONL)
    summary = run_distill_r2_1(
        input_path=INPUT_JSONL,
        output_path=OUTPUT_JSONL,
        model=model,
        max_chars=int(gen.get("text_max_chars", 4000)),
        id_prefix="SV2-P23",
    )
    rows = read_jsonl(OUTPUT_JSONL)
    r22 = _load_r22_summary()

    proven_anchors = {
        "rec_3adad134db5cb9c2",
        "rec_66100907c00656ec",
        "rec_41a160ead0ae1be6",
        "rec_5edea297fe4ab1d8",
    }

    patterns: list[str] = []
    remaining: list[str] = []
    insufficient_drops = 0
    nav_drops = 0
    ambiguous_drops = 0

    for r in rows:
        if r.get("decision") != "drop":
            continue
        dr = r.get("drop_reason") or ""
        if "insufficient" in dr or dr == "unanswerable_from_unit":
            insufficient_drops += 1
        if "nav" in dr:
            nav_drops += 1
        if dr == "ambiguous_grounding":
            ambiguous_drops += 1
        if r.get("validation_note"):
            patterns.append(f"{r.get('ground_truth_record_id')}: {r.get('validation_note')}")

    r22_ambiguous = sum(
        1 for k, v in (r22.get("by_drop_reason") or {}).items() if k == "ambiguous_grounding" for _ in range(v)
    )
    if not r22_ambiguous and r22.get("by_drop_reason", {}).get("ambiguous_grounding"):
        r22_ambiguous = r22["by_drop_reason"]["ambiguous_grounding"]

    improved = [
        f"keep usable: R2.2={r22.get('usable_count', 6)} → R2.3={summary['usable_count']} (Δ{summary['usable_count'] - r22.get('usable_count', 6):+d})",
        f"duplicate_same_fact: R2.2={r22.get('duplicate_same_fact_drops', 2)} → R2.3={summary.get('duplicate_same_fact_drops', 0)}",
        f"ambiguous_grounding: R2.2={r22_ambiguous} → R2.3={ambiguous_drops}",
        f"insufficient_substance: R2.2={r22.get('by_drop_reason', {}).get('insufficient_substance / unanswerable_from_unit', 2)} → R2.3={insufficient_drops}",
    ]

    if summary.get("duplicate_same_fact_drops", 0):
        remaining.append(f"duplicate_same_fact: {summary['duplicate_same_fact_drops']}")
    if ambiguous_drops:
        remaining.append(f"ambiguous_grounding: {ambiguous_drops}")
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
                "pilot_source": u.get("pilot_source"),
                "grounding_risk": u.get("grounding_risk"),
                "why_usable": (
                    f"evidence_span grounded; overlap validation pass; "
                    f"type={r.get('question_type')}; difficulty={r.get('difficulty')}"
                ),
            }
        )

    passed = summary["usable_count"] >= 8
    if passed:
        root_hint = "n/a — đạt gate"
    elif summary["usable_count"] >= 6 and ambiguous_drops + summary.get("duplicate_same_fact_drops", 0) > 2:
        root_hint = "selector — tail corpus-fill units vẫn noisy; có thể thu pilot xuống ~10 anchor+unique"
    elif insufficient_drops > 3:
        root_hint = "selector — unit substance thấp"
    else:
        root_hint = "distillation/validation — kiểm tra drop cụ thể"

    summary.update(
        {
            "pilot_version": "2.3",
            "proven_anchor_count": sum(1 for u in units if u.get("record_id") in proven_anchors),
            "corpus_fill_count": sum(1 for u in units if (u.get("pilot_source") or "").startswith("corpus")),
            "ambiguous_grounding_drops": ambiguous_drops,
            "comparison_r22": {
                "r22_keep": r22.get("keep_count"),
                "r22_drop": r22.get("drop_count"),
                "r22_usable": r22.get("usable_count"),
                "keep_delta": summary["keep_count"] - r22.get("keep_count", 0),
                "drop_delta": summary["drop_count"] - r22.get("drop_count", 0),
                "usable_delta": summary["usable_count"] - r22.get("usable_count", 0),
            },
            "improved_patterns": improved,
            "remaining_patterns": remaining,
            "error_patterns": patterns,
            "silver_qc_candidates": silver_candidates,
            "silver_qc_ready_count": len(silver_candidates),
            "pass_threshold_8_usable": passed,
            "silver_qc_recommended": passed,
            "root_cause_hint": root_hint,
        }
    )

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, rows, units, r22)

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
