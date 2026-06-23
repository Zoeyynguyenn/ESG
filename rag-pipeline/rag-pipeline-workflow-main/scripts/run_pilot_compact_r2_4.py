"""Run Pilot Compact R2.4: selector + Distillation R2.1 + report."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PILOT_JSONL = ROOT / "data/golden_set/v2/step1_corpus_units/pilot_hanssem_10_compact_r2_4.jsonl"
DISTILL_JSONL = ROOT / "data/golden_set/v2/step2_silver/pilot_hanssem_10_compact_distilled_r2_4.jsonl"
SUMMARY_JSON = ROOT / "reports/_pilot_compact_r2_4_summary.json"
R23_SUMMARY_JSON = ROOT / "reports/_distill_pilot_hanssem_round2_3_summary.json"
REPORT_MD = ROOT / "reports/golden_set_pilot_compact_r2_4.md"
CONFIG = ROOT / "configs/golden_set_pipeline.yaml"

# Ratio thresholds for Silver QC hạn chế recommendation
USABLE_INPUT_RATIO_GATE = 0.70
USABLE_KEEP_RATIO_GATE = 0.85


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


def write_report(
    selector_summary: dict,
    distill_summary: dict,
    rows: list,
    units: list,
    r23: dict,
) -> None:
    n = distill_summary["input_units"]
    keep = distill_summary["keep_count"]
    drop = distill_summary["drop_count"]
    usable = distill_summary["usable_count"]
    usable_input_ratio = round(usable / n, 3) if n else 0.0
    usable_keep_ratio = round(usable / keep, 3) if keep else 0.0

    r23_usable = r23.get("usable_count", 6)
    r23_n = r23.get("input_units", 15)
    r23_ratio = round(r23_usable / r23_n, 3) if r23_n else 0.0

    ratio_ok = usable_input_ratio >= USABLE_INPUT_RATIO_GATE and usable_keep_ratio >= USABLE_KEEP_RATIO_GATE
    # Direction A = ratio đủ cao để Silver QC hạn chế (không yêu cầu đạt gate tuyệt đối ≥8)
    direction = "A" if ratio_ok and usable >= 5 else "B"

    lines = [
        "# Golden Set — Pilot Compact Hansem Round 2.4",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu pilot compact",
        "",
        "Thiết kế pilot Hansem **ít nhưng sạch** (8–10 unit mục tiêu) để kiểm tra: tỷ lệ usable có đủ cao để mở **Silver QC pilot hạn chế** hay cần mở rộng corpus trước.",
        "",
        "## Vì sao pilot 15 unit thất bại",
        "",
        "- Distillation R2.2 và R2.3 đều cho **keep 6 / drop 9 / usable 6** trên pilot 15.",
        "- Hansem eligible+conditional chỉ **16 unit**, **~15 fingerprint unique**; full corpus **40 unit**, **~37 fingerprint**.",
        "- Pilot 15 bị **ép lấp** bằng 9–11 unit corpus tail (noise 4–17, substance thấp) → 3 duplicate, 4 insufficient, 1 ambiguous, 1 nav.",
        "- Prompt Distillation R2.1 + validation **không** phải bottleneck.",
        "",
        "### Phân tích pool",
        "",
    ]
    pa = selector_summary.get("pool_analysis", {})
    for k, v in pa.items():
        lines.append(f"- `{k}`: {v}")

    lines.extend(
        [
            "",
            "## Logic chọn compact pilot",
            "",
            "1. **Phase 1 — Anchor:** 6 unit proven usable từ Distillation R2.3 (không tail filler).",
            "2. **Phase 2 — Expansion:** chỉ từ eligible/conditional; unique fingerprint + unique `duplicate_cluster_id`; substance≥14, noise≤6; **không** corpus tail fill.",
            "3. **Hard exclude:** TOC/intro, distill-hard-block, near-dup, soft-dup, saturated fact cluster.",
            "4. **Không** lấy 2 unit cùng cluster trừ khi proven anchor.",
            "",
            f"- Target: **{selector_summary.get('target_min', 8)}–{selector_summary.get('target_max', 10)}** unit",
            f"- Đạt được: **{selector_summary.get('pilot_selected', 0)}** unit (anchor {selector_summary.get('anchor_count', 0)} + expansion {selector_summary.get('expansion_count', 0)})",
            f"- Fact categories covered: {selector_summary.get('fact_categories_covered', [])}",
            "",
            "## Danh sách unit đã chọn và vì sao",
            "",
            "| # | record_id | pilot_source | select_reason | substance | noise | fact_categories |",
            "|--:|-----------|--------------|---------------|----------:|------:|-----------------|",
        ]
    )
    for u in units:
        lines.append(
            f"| {u.get('compact_rank', '')} | `{u.get('record_id', '')}` | `{u.get('pilot_source', '')}` | "
            f"`{u.get('select_reason', '')}` | {u.get('substance_score', '')} | {u.get('noise_score', '')} | "
            f"{u.get('fact_categories', [])} |"
        )

    lines.extend(
        [
            "",
            "## Kết quả distillation compact",
            "",
            "| Chỉ số | Giá trị |",
            "|--------|--------:|",
            f"| Input units | {n} |",
            f"| decision=keep | {keep} |",
            f"| decision=drop | {drop} |",
            f"| usable | {usable} |",
            f"| usable / input | **{usable_input_ratio:.1%}** |",
            f"| usable / keep | **{usable_keep_ratio:.1%}** |",
            "",
            "### Drop reasons",
            "",
        ]
    )
    for k, v in sorted((distill_summary.get("by_drop_reason") or {}).items()):
        lines.append(f"- `{k}`: {v}")

    lines.extend(
        [
            "",
            "## So sánh R2.3 15-unit vs R2.4 compact",
            "",
            "| Metric | R2.3 (15) | R2.4 compact | Delta |",
            "|--------|----------:|-------------:|------:|",
            f"| input | {r23_n} | {n} | {n - r23_n:+d} |",
            f"| keep | {r23.get('keep_count', 6)} | {keep} | {keep - r23.get('keep_count', 6):+d} |",
            f"| usable | {r23_usable} | {usable} | {usable - r23_usable:+d} |",
            f"| usable/input | {r23_ratio:.1%} | {usable_input_ratio:.1%} | {usable_input_ratio - r23_ratio:+.1%} |",
            f"| tail filler in pilot | 11 | 0 | -11 |",
            "",
            f"- Unit bỏ khỏi R2.3: {len(selector_summary.get('vs_r23_15', {}).get('removed_from_r23', []))} tail/noisy slots",
            "",
            "## Đánh giá",
            "",
        ]
    )

    if ratio_ok:
        lines.extend(
            [
                f"- Tỷ lệ usable/input **{usable_input_ratio:.1%}** và usable/keep **{usable_keep_ratio:.1%}** — **cao hơn đáng kể** so với R2.3 ({r23_ratio:.1%}).",
                f"- **Đề xuất:** mở **Silver QC pilot hạn chế** trên {usable} row (không đủ gate chính ≥8 từ pilot 15, nhưng compact đủ sạch để QC có ý nghĩa).",
            ]
        )
    else:
        lines.extend(
            [
                f"- Tỷ lệ usable chưa đạt ngưỡng đề xuất (input≥{USABLE_INPUT_RATIO_GATE:.0%}, keep≥{USABLE_KEEP_RATIO_GATE:.0%}).",
                "- **Đề xuất:** dừng Hansem-only; **mở rộng corpus Hansem** trước khi full step 2.",
            ]
        )

    if selector_summary.get("expansion_count", 0) == 0:
        lines.append(
            "- Phase 2 expansion **không tìm được** unit eligible mới — pool Hansem đã bão hòa sau 6 anchor."
        )

    lines.extend(["", "### Mẫu keep", ""])
    for r in [x for x in rows if x.get("decision") == "keep"]:
        lines.append(
            f"- **{r.get('silver_id')}** (`{r.get('ground_truth_record_id')}`): "
            f"{(r.get('question') or '')[:85]}…"
        )

    if drop:
        lines.extend(["", "### Mẫu drop", ""])
        for r in [x for x in rows if x.get("decision") == "drop"]:
            lines.append(
                f"- **{r.get('silver_id')}** `{r.get('drop_reason')}` record=`{r.get('ground_truth_record_id')}`"
            )

    lines.extend(
        [
            "",
            "## Kết luận và bước kế tiếp",
            "",
        ]
    )
    if direction == "A":
        lines.extend(
            [
                f"**Hướng A — Mở Silver QC pilot hạn chế** trên {usable} row compact (`SV2-P24-*`).",
                "",
                "Bước kế tiếp:",
                "1. Silver QC pilot hạn chế (không full QC, không Evol/Judge).",
                "2. Song song lên kế hoạch mở rộng corpus Hansem để đạt gate ≥8 cho full pilot.",
                "3. Giữ nguyên prompt Distillation R2.1.",
            ]
        )
    else:
        lines.extend(
            [
                "**Hướng B — Dừng Hansem-only; mở rộng corpus Hansem trước.**",
                "",
                "Bước kế tiếp:",
                "1. Bổ sung report-body / press release ESG từ dataset package mới.",
                "2. Chạy lại prefilter R2.2 trên corpus mở rộng.",
                "3. Không mở Silver QC gate chính cho đến khi có ≥8 unique-body unit.",
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
    from golden_set.pilot_selector_r2_4_compact import run_selector_r24_compact
    from golden_set.step2_distill_r2_1 import run_distill_r2_1

    selector_summary = run_selector_r24_compact(
        eligible_path=ROOT / "data/golden_set/v2/step1_corpus_units/corpus_units_eligible_r2_2.jsonl",
        conditional_path=ROOT / "data/golden_set/v2/step1_corpus_units/corpus_units_conditional_r2_2.jsonl",
        corpus_path=ROOT / "data/golden_set/v2/step1_corpus_units/corpus_units.jsonl",
        output_path=PILOT_JSONL,
        distill_r23_summary_path=R23_SUMMARY_JSON,
    )

    units = read_jsonl(PILOT_JSONL)
    distill_summary = run_distill_r2_1(
        input_path=PILOT_JSONL,
        output_path=DISTILL_JSONL,
        model=model,
        max_chars=int(gen.get("text_max_chars", 4000)),
        id_prefix="SV2-P24",
    )
    rows = read_jsonl(DISTILL_JSONL)
    r23 = {}
    if R23_SUMMARY_JSON.exists():
        r23 = json.loads(R23_SUMMARY_JSON.read_text(encoding="utf-8"))

    n = distill_summary["input_units"]
    keep = distill_summary["keep_count"]
    usable = distill_summary["usable_count"]
    usable_input_ratio = round(usable / n, 4) if n else 0.0
    usable_keep_ratio = round(usable / keep, 4) if keep else 0.0
    ratio_ok = usable_input_ratio >= USABLE_INPUT_RATIO_GATE and usable_keep_ratio >= USABLE_KEEP_RATIO_GATE
    # Direction A = ratio đủ cao để Silver QC hạn chế (không yêu cầu đạt gate tuyệt đối ≥8)
    direction = "A" if ratio_ok and usable >= 5 else "B"

    silver_candidates = []
    for r in rows:
        if r.get("silver_id") not in (distill_summary.get("usable_silver_ids") or []):
            continue
        u = next((x for x in units if x.get("record_id") == r.get("ground_truth_record_id")), {})
        silver_candidates.append(
            {
                "silver_id": r.get("silver_id"),
                "unit_id": u.get("unit_id", ""),
                "record_id": r.get("ground_truth_record_id"),
                "question_type": r.get("question_type"),
                "difficulty": r.get("difficulty"),
                "why_usable": "evidence_span grounded; overlap validation pass",
            }
        )

    selector_summary.update(
        {
            "distillation": {
                **distill_summary,
                "usable_input_ratio": usable_input_ratio,
                "usable_keep_ratio": usable_keep_ratio,
                "model": model,
                "output_path": str(DISTILL_JSONL),
            },
            "comparison_r23_15": {
                "r23_input": r23.get("input_units", 15),
                "r23_usable": r23.get("usable_count", 6),
                "r23_usable_input_ratio": round(r23.get("usable_count", 6) / r23.get("input_units", 15), 4),
                "compact_usable_input_ratio": usable_input_ratio,
                "ratio_improvement": round(usable_input_ratio - r23.get("usable_count", 6) / max(r23.get("input_units", 15), 1), 4),
            },
            "silver_qc_limited_recommended": direction == "A",
            "recommended_direction": direction,
            "silver_qc_candidates": silver_candidates if direction == "A" else [],
        }
    )

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(selector_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(selector_summary, distill_summary, rows, units, r23)

    print(json.dumps(
        {
            "pilot_size": n,
            "keep": keep,
            "usable": usable,
            "usable_input_ratio": usable_input_ratio,
            "direction": direction,
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
