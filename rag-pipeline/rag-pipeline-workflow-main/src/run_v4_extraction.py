"""Version 4: chay structured extraction + bao cao danh gia."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import BASE_DIR, FINAL_TOP_K, RETRIEVAL_MODES_V3
from eval_set_io import parse_eval_set
from extraction_v4 import (
    DEFAULT_RETRIEVAL_MODE,
    build_esg_profile,
    compute_extraction_metrics,
    load_schema,
    iter_schema_fields,
)

REPORTS_DIR = BASE_DIR / "reports"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_profile_json(profile: Dict[str, Any], output: Optional[Path] = None) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = output or (ARTIFACTS_DIR / f"v4_extracted_profile_{_ts()}.json")
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _sample_records(profile: Dict[str, Any], n: int = 10) -> List[Dict[str, Any]]:
    records = profile.get("records", [])
    priority = [r for r in records if r.get("status") == "verified"]
    rest = [r for r in records if r not in priority]
    picked = (priority + rest)[:n]
    return [
        {
            "field": r.get("field"),
            "value": r.get("value"),
            "source": r.get("source"),
            "confidence": r.get("confidence"),
            "status": r.get("status"),
        }
        for r in picked
    ]


def _field_comment(r: Dict[str, Any]) -> str:
    st = r.get("status")
    if st == "verified":
        return "Bằng chứng khớp pattern và điểm retrieval tốt."
    if st == "extracted":
        return "Có giá trị nhưng cần rà soát thêm (confidence medium/low)."
    if st == "conflict":
        return "Nhiều evidence cho giá trị khác nhau — cần human review."
    if st == "insufficient":
        return "Không đủ bằng chứng hoặc không parse được từ context."
    return ""


def write_extraction_report(
    profile: Dict[str, Any],
    metrics: Dict[str, Any],
    output: Optional[Path] = None,
) -> Path:
    path = output or (REPORTS_DIR / f"v4-extraction-report-{_ts()}.md")
    samples = _sample_records(profile, 10)
    lines = [
        "# V4 Extraction Report",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Run config",
        "",
        "```json",
        json.dumps(
            {
                "entity": profile.get("entity"),
                "schema_version": profile.get("schema_version"),
                "retrieval_mode": profile.get("retrieval_mode"),
                "retrieval_fallback_note": profile.get("retrieval_fallback_note"),
                "field_count": profile.get("field_count"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Extraction metrics",
        "",
        "```json",
        json.dumps(metrics, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 10 field tieu bieu",
        "",
        "| field | value | source | confidence | status | nhan xet |",
        "|---|---|---|---|---|---|",
    ]
    for s in samples:
        rec = next((x for x in profile["records"] if x["field"] == s["field"]), s)
        val = rec.get("value")
        val_s = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else str(val)
        lines.append(
            f"| {rec.get('field')} | {val_s} | {(rec.get('source') or '')[:60]} | {rec.get('confidence')} | {rec.get('status')} | {_field_comment(rec)} |"
        )

    lines.extend(
        [
            "",
            "## Nhom field",
            "",
        ]
    )
    schema = load_schema()
    for group, items in schema.get("groups", {}).items():
        lines.append(f"- **{group}**: {len(items)} field")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _eval_schema_vs_evalset(profile: Dict[str, Any]) -> Dict[str, Any]:
    """So khop field id trong eval_set (cot Expected Extracted Field)."""
    rows = parse_eval_set()
    by_field = {r["field"]: r for r in profile.get("records", [])}
    checks = []
    for row in rows:
        ef = (row.get("extracted_field") or row.get("expected_extracted_field") or "").strip()
        if not ef or ef == "insufficient_information_flag":
            continue
        rec = by_field.get(ef)
        if not rec:
            continue
        checks.append(
            {
                "eval_id": row.get("id"),
                "field": ef,
                "extracted_value": rec.get("value"),
                "status": rec.get("status"),
                "expected_notes": row.get("expected_answer_notes"),
            }
        )
    matched = sum(1 for c in checks if c.get("extracted_value") is not None)
    return {
        "eval_field_links": len(checks),
        "eval_fields_with_value": matched,
        "eval_field_match_rate": round(matched / max(len(checks), 1), 4),
        "samples": checks[:8],
    }


def write_eval_report(
    profile: Dict[str, Any],
    metrics: Dict[str, Any],
    eval_extra: Dict[str, Any],
    output: Optional[Path] = None,
) -> Path:
    path = output or (REPORTS_DIR / f"v4-extraction-eval-{_ts()}.md")
    lines = [
        "# V4 Extraction Eval",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| field_coverage_rate | {metrics.get('field_coverage_rate')} |",
        f"| verified_rate | {metrics.get('verified_rate')} |",
        f"| insufficient_rate | {metrics.get('insufficient_rate')} |",
        f"| conflict_rate | {metrics.get('conflict_rate')} |",
        f"| evidence_presence_rate | {metrics.get('evidence_presence_rate')} |",
        "",
        "## Lien ket eval_set (Expected Extracted Field)",
        "",
        "```json",
        json.dumps(eval_extra, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Acceptance gate V4",
        "",
    ]
    gate_pass = (
        metrics.get("field_coverage_rate", 0) >= 0.5
        and metrics.get("evidence_presence_rate", 0) >= 0.7
        and metrics.get("conflict_rate", 0) <= 0.15
    )
    status = "pass_with_limits" if gate_pass else "not_pass"
    lines.extend(
        [
            f"- **V4 status (heuristic):** `{status}`",
            f"- field_coverage >= 0.5: {metrics.get('field_coverage_rate', 0) >= 0.5}",
            f"- evidence_presence >= 0.7: {metrics.get('evidence_presence_rate', 0) >= 0.7}",
            f"- conflict_rate <= 0.15: {metrics.get('conflict_rate', 0) <= 0.15}",
            "",
            "## Rui ro",
            "",
            "- Rule/heuristic chua bao phu PDF public phuc tap.",
            "- Mot so field string can human verify (status extracted vs verified).",
            "- Khong dung LLM trong phien nay — chat luong phu thuoc retrieval V3.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def assess_v4_status(metrics: Dict[str, Any]) -> str:
    cov = metrics.get("field_coverage_rate", 0)
    ev = metrics.get("evidence_presence_rate", 0)
    ins = metrics.get("insufficient_rate", 1)
    conflict = metrics.get("conflict_rate", 1)
    if cov >= 0.75 and ev >= 0.85 and ins <= 0.25 and conflict <= 0.1:
        return "pass"
    if cov >= 0.5 and ev >= 0.7:
        return "pass_with_limits"
    return "not_pass"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="V4 Structured Extraction RAG")
    parser.add_argument(
        "--retrieval-mode",
        default=DEFAULT_RETRIEVAL_MODE,
        help=f"Mot trong: {', '.join(RETRIEVAL_MODES_V3)}",
    )
    parser.add_argument("--top-k", type=int, default=FINAL_TOP_K)
    parser.add_argument("--output", type=str, default="", help="Duong dan JSON profile tuy chon")
    args = parser.parse_args(argv)

    print(f"V4 extraction — retrieval_mode={args.retrieval_mode} top_k={args.top_k}")
    profile = build_esg_profile(retrieval_mode=args.retrieval_mode, top_k=args.top_k)
    metrics = compute_extraction_metrics(profile)
    eval_extra = _eval_schema_vs_evalset(profile)

    out_path = Path(args.output) if args.output else None
    json_path = write_profile_json(profile, out_path)
    report_path = write_extraction_report(profile, metrics)
    eval_path = write_eval_report(profile, metrics, eval_extra)

    v4_status = assess_v4_status(metrics)
    advance_v5 = "chua" if v4_status == "not_pass" else "co_the"

    summary = {
        "v4_status": v4_status,
        "advance_v5": advance_v5,
        "metrics": metrics,
        "artifacts": {
            "profile_json": str(json_path),
            "extraction_report": str(report_path),
            "eval_report": str(eval_path),
        },
        "schema_field_count": profile.get("field_count"),
        "retrieval_mode": profile.get("retrieval_mode"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
