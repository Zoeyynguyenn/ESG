"""V2.1: cleanup eval set + re-eval gate + enhanced reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import BASE_DIR, EMBEDDING_MODEL, TOP_K
from eval_scoring_v2 import (
    aggregate_metrics_v2,
    confusion_summary,
    format_per_question_score,
    score_result_v2,
    top_error_patterns,
)
from eval_set_io import parse_eval_set, validate_eval_set, write_validation_report
from run_v2_eval import (
    dataset_snapshot,
    decide_v2_status,
    get_chunk_count,
    make_query_fn,
    run_eval,
)

V2_BASELINE_METRICS = {
    "retrieval_hit_rate": 0.72,
    "citation_correctness": 0.46,
    "citation_topk_rate": 0.72,
    "groundedness": 1.0,
    "answer_correctness": 0.58,
    "insufficient_information_handling": 1.0,
    "pass_rate": 0.36,
    "partial_rate": 0.54,
    "fail_rate": 0.1,
}
REGRESSION_TOLERANCE = 0.02  # cho phep dao dong nho


def compare_regression(current: Dict[str, float]) -> Dict[str, str]:
    out = {}
    for k, base in V2_BASELINE_METRICS.items():
        cur = current.get(k, 0)
        if cur > base + REGRESSION_TOLERANCE:
            out[k] = "tot_hon"
        elif cur < base - REGRESSION_TOLERANCE:
            out[k] = "xau_hon"
        else:
            out[k] = "khong_doi"
    return out


def notable_cases(evaluated: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, str]]:
    picked = []
    for item in evaluated:
        if item["metrics"]["overall"] in ("fail", "partial"):
            row = item["row"]
            m = item["metrics"]
            picked.append(
                {
                    "id": row["id"],
                    "overall": m["overall"],
                    "reason": ", ".join(m.get("reason_codes", [])[:3]) or "-",
                    "question": row["question"][:80],
                }
            )
    picked.sort(key=lambda x: (0 if x["overall"] == "fail" else 1, x["id"]))
    return picked[:limit]


def write_v2_1_extractive_report(
    evaluated: List[Dict[str, Any]],
    run_meta: Dict[str, Any],
    chunk_count: int,
    regression: Dict[str, str],
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v2_1-eval-extractive-{ts}.md"
    metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated])
    conf = confusion_summary(evaluated)
    patterns = top_error_patterns(evaluated, 5)
    notable = notable_cases(evaluated, 10)
    st, adv, reason = decide_v2_status(metrics, run_meta.get("eval_mode", "extractive"), False)

    lines = [
        "# V2.1 Eval — Extractive (Re-eval)",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## V2.1 ket luan (extractive)",
        "",
        f"- status heuristic: `{st}`",
        f"- ly do: {reason}",
        "",
        "## Stack config",
        "",
        "```json",
        json.dumps({**run_meta, "chunk_count": chunk_count, "dataset": dataset_snapshot()}, indent=2),
        "```",
        "",
        "## Metrics (5 chinh)",
        "",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
        "",
        "## Confusion summary (pass/partial/fail)",
        "",
        "```json",
        json.dumps(conf, indent=2),
        "```",
        "",
        f"- pass: {conf.get('pass', 0)} | partial: {conf.get('partial', 0)} | fail: {conf.get('fail', 0)}",
        "",
        "## Regression vs V2 (20260522-105327)",
        "",
        "```json",
        json.dumps(regression, indent=2),
        "```",
        "",
        "## Top 5 error patterns",
        "",
        "| Code | Count |",
        "|---|---:|",
    ]
    for code, cnt in patterns.items():
        lines.append(f"| `{code}` | {cnt} |")

    lines.extend(["", "## 10 cau fail/partial dang chu y", ""])
    for n in notable:
        lines.append(f"- **{n['id']}** ({n['overall']}): {n['reason']} — {n['question']}")

    lines.extend(["", "## Per-question scores (chuan)", ""])
    for item in evaluated:
        pq = format_per_question_score(item["row"], item["result"], item["metrics"])
        lines.append(f"### {pq['id']} — **{pq['overall']}**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(pq, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_re_eval_gate(
    eval_valid: bool,
    metrics: Dict[str, float],
    regression: Dict[str, str],
    generative_blocker: str,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v2_1-re-eval-gate-{ts}.md"

    metrics_ok = all(
        k in metrics
        for k in (
            "retrieval_hit_rate",
            "citation_correctness",
            "groundedness",
            "answer_correctness",
            "insufficient_information_handling",
        )
    )
    reg_worse = [k for k, v in regression.items() if v == "xau_hon"]
    reg_better = [k for k, v in regression.items() if v == "tot_hon"]

    gate1 = eval_valid
    gate2 = metrics_ok
    gate3 = len(reg_worse) <= 2 and metrics.get("insufficient_information_handling", 0) >= 0.95
    gate4 = (
        gate1
        and gate2
        and gate3
        and metrics.get("citation_correctness", 0) >= 0.45
        and metrics.get("pass_rate", 0) >= 0.34
    )

    advance_v3 = "no"
    pre_v3 = []
    if gate4 and metrics.get("retrieval_hit_rate", 0) >= 0.7:
        advance_v3 = "yes"
    else:
        if metrics.get("citation_correctness", 0) < 0.5:
            pre_v3.append("Cai thien citation (top-1 retrieval alignment) truoc V3")
        if not generative_blocker:
            pre_v3.append("Chay generative eval de co baseline day du")
        else:
            pre_v3.append(f"Generative blocker: {generative_blocker}")
        if metrics.get("pass_rate", 0) < 0.4:
            pre_v3.append("Tang answer_correctness / pass_rate tren eval 50 cau")

    if advance_v3 == "yes":
        v21_status = "pass_with_limits"
        risks = "Semantic-only retrieval; extractive answer; generative chua do"
    elif gate1 and gate2 and gate3:
        v21_status = "pass_with_limits"
        risks = "Chua du metric citation/pass de V3 toi uu"
    else:
        v21_status = "not_pass" if not gate1 else "pass_with_limits"
        risks = "Gate chua dat day du"

    lines = [
        "# V2.1 Re-eval Gate",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Gates",
        "",
        f"| Gate | Ket qua | Mo ta |",
        f"|---|---|---|",
        f"| Gate 1 — Eval set consistency | **{'PASS' if gate1 else 'FAIL'}** | validate eval_set + ESG-E14 synced sources |",
        f"| Gate 2 — Metrics available | **{'PASS' if gate2 else 'FAIL'}** | 5 metric chinh co mat |",
        f"| Gate 3 — Regression vs V2 | **{'PASS' if gate3 else 'FAIL'}** | worse={reg_worse}; better={reg_better} |",
        f"| Gate 4 — V3 readiness | **{'PASS' if gate4 else 'FAIL'}** | citation>=0.45, pass>=0.34, insuf>=0.95 |",
        "",
        "## Metrics snapshot",
        "",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
        "",
        "## Quyet dinh V2.1",
        "",
        f"- **V2.1 status:** `{v21_status}`",
        f"- **Advance V3 ngay:** `{advance_v3}`",
        f"- **Rui ro/gia dinh:** {risks}",
        "",
    ]
    if advance_v3 == "no":
        lines.append("### Viec can xong truoc V3 (2-3)")
        for i, item in enumerate(pre_v3[:3], 1):
            lines.append(f"{i}. {item}")
    else:
        lines.append("### Gia dinh khi vao V3")
        lines.append("1. V2.1 eval pipeline on dinh, co the lap lai.")
        lines.append("2. V3 chi them retrieval (BM25/hybrid/rerank), khong doi eval set.")
        lines.append(f"3. {risks}")

    if generative_blocker:
        lines.extend(["", "## Generative blocker", "", generative_blocker])

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    vr = validate_eval_set()
    vp = write_validation_report(vr, filename_prefix="v2_1-evalset-validation")
    print(f"Validation: {vp} valid={vr.valid}")

    rows = parse_eval_set()
    chunk_count = get_chunk_count()
    qfn, meta = make_query_fn("extractive")
    meta["v2_1"] = True
    meta["eval_set_fix"] = "ESG-E14 expected_answer: manual_download_required -> downloaded"

    evaluated = run_eval(rows, qfn)
    metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated])
    regression = compare_regression(metrics)

    ep = write_v2_1_extractive_report(evaluated, meta, chunk_count, regression)
    print(f"Extractive report: {ep}")

    env = meta.get("environment", {})
    gen_blocker = "ollama/API khong san sang" if not (
        env.get("ollama") or env.get("openai_api_key_set")
    ) else ""

    gp = write_re_eval_gate(vr.valid, metrics, regression, gen_blocker)
    print(f"Gate report: {gp}")
    print(json.dumps({"metrics": metrics, "regression": regression}, indent=2))


if __name__ == "__main__":
    main()
