#!/usr/bin/env python3
"""Build a curated eval subset for demo_company cross-doc diagnostic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Curated IDs: traceable, diverse domains, avoid deep SME ambiguity
SINGLE_SUBSET_IDS = [
    # HR — doc_04
    "QUANT-0001",  # 총 구성원 수
    "QUANT-0006",  # 정규직 직원 비율
    "QUANT-0013",  # 팀장 남성
    "QUANT-0019",  # 총 신규 채용
    "QUANT-0028",  # 자발적 이직률
    # Environment — doc_02
    "QUANT-0146",  # 총 온실가스
    "QUANT-0147",  # Scope 1
    "QUANT-0151",  # 총 에너지 소비량
    "QUANT-0200",  # 폐수 배출량
    # Governance — doc_06
    "QUANT-0215",  # 평가 사업장 수
    "QUANT-0219",  # 윤리 위반 제보
    "QUANT-0224",  # 반부패/뇌물
    # Business — doc_01
    "QUANT-0207",  # 매출액
    # Social — doc_05
    "QUANT-0083",  # 연간 인당 근로시간
    "QUANT-0086",  # 노사협의회 운영 횟수
    "QUANT-0126",  # 사회공헌 지출액
    # Certification — doc_07
    "QUANT-0144",  # 친환경 인증 원부자재
    # HR diversity
    "QUANT-0017",  # 장애인
    "QUANT-0031",  # 산업재해 건수 (if exists - check)
    "QUANT-0220",  # 윤리 위반 처리 건수
    "QUANT-0150",  # 에너지 사용량 집약도
]

CROSS_SUBSET_IDS = [
    # Qualitative — narrative cross-doc
    "QUAL-0001",  # ESG 비전 — business+governance+cert
    "QUAL-0002",  # ESG 거버넌스
    "QUAL-0005",  # 안전보건 조직 — HR+governance
    "QUAL-0008",  # 인권경영 정책 — social
    "QUAL-0020",  # 환경경영 정책 — env+cert
    # Quantitative cross — merge / multi-source
    "QUANT-0042",  # 매출부서 여성비율 — HR+CSV, needs_merge=false
    "QUANT-0044",  # 복리후생비 — 4 docs, needs_merge=true
    "QUANT-0133",  # 환경투자액 — env cluster
    "QUANT-0134",  # 매출 대비 환경투자 — ratio cross
    "QUANT-0208",  # 유형자산 취득 — business+csv+gov
    "QUANT-0210",  # 급여+복리 — economic distribution
    "QUANT-0209",  # 이자비용
    "QUANT-0213",  # 법인세
    "QUANT-0155",  # 재생에너지 (if exists)
    "QUANT-0046",  # 육아휴직 대상자 — HR+social+cert+csv
]

SUBSET_CRITERIA_NOTE = """
# Tiêu chí chọn eval subset demo_company

**Nguyên tắc:** heuristic plan chỉ là bootstrap — subset này chọn tay để traceable, không phải gold cuối.

## Single-doc (20 câu)
- Mỗi câu có **một** `primary_document_id` rõ (HR/env/gov/business/social/cert).
- Tránh câu semantic mơ hồ hoặc label lệch workbook.
- Cân bằng domain: HR×5, Environment×4, Governance×3, Business×1, Social×3, Certification×1, bổ sung×3.

## Cross-doc (15 câu)
- 5 qualitative: narrative span nhiều file (ESG, governance, safety, human rights, environment).
- 10 quantitative: có `needs_merge` hoặc CSV supporting, đại diện HR+CSV, env cluster, economic distribution.
- Mỗi câu ghi rõ trong plan: primary docs, supporting, `needs_merge`.

## Không dùng làm
- Gold answer scoring
- So sánh với `overall_score` lane Dataset-Excel v5
"""


def _load_plans(path: Path) -> dict[str, dict]:
    plans: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            plans[str(row["item_id"])] = row
    return plans


def _pick(plans: dict[str, dict], ids: list[str], mode: str, limit: int) -> list[dict]:
    out: list[dict] = []
    missing: list[str] = []
    for item_id in ids:
        row = plans.get(item_id)
        if not row:
            missing.append(item_id)
            continue
        if row.get("answer_mode") != mode:
            continue
        enriched = dict(row)
        enriched["subset_reason"] = _reason_for(item_id, mode)
        enriched["expected_evidence_plan"] = {
            "primary_document_ids": row.get("primary_document_ids"),
            "supporting_document_ids": row.get("supporting_document_ids"),
            "roles": row.get("roles"),
            "needs_merge": row.get("needs_merge"),
            "needs_conflict_resolution": row.get("needs_conflict_resolution"),
        }
        out.append(enriched)
        if len(out) >= limit:
            break
    if missing:
        print(f"warning: missing item_ids for {mode}: {missing}", file=sys.stderr)
    return out


def _reason_for(item_id: str, mode: str) -> str:
    reasons = {
        "QUANT-0001": "HR headcount — single table doc_04",
        "QUANT-0146": "GHG total — single env table doc_02",
        "QUANT-0207": "Revenue — single business table doc_01",
        "QUAL-0001": "ESG strategy narrative — multi-doc synthesis",
        "QUANT-0042": "HR metric + CSV summary — 2-source cross",
        "QUANT-0133": "Env investment — env doc cluster merge",
        "QUANT-0044": "Benefits — 4-doc merge pattern",
    }
    return reasons.get(item_id, f"curated_{mode}_pilot")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plans",
        default="data/enterprise_docs/demo_company/question_evidence_plans.jsonl",
    )
    parser.add_argument("--single-limit", type=int, default=20)
    parser.add_argument("--cross-limit", type=int, default=15)
    args = parser.parse_args()

    plans_path = ROOT / args.plans
    plans = _load_plans(plans_path)

    single = _pick(plans, SINGLE_SUBSET_IDS, "single_document_answer", args.single_limit)
    cross = _pick(plans, CROSS_SUBSET_IDS, "cross_document_answer", args.cross_limit)

    # Backfill if an ID missing
    if len(single) < args.single_limit:
        for row in plans.values():
            if row.get("answer_mode") != "single_document_answer":
                continue
            if any(r["item_id"] == row["item_id"] for r in single):
                continue
            single.append({**row, "subset_reason": "backfill_single", "expected_evidence_plan": {
                "primary_document_ids": row.get("primary_document_ids"),
                "supporting_document_ids": row.get("supporting_document_ids"),
                "roles": row.get("roles"),
                "needs_merge": row.get("needs_merge"),
            }})
            if len(single) >= args.single_limit:
                break

    if len(cross) < args.cross_limit:
        for row in plans.values():
            if row.get("answer_mode") != "cross_document_answer":
                continue
            if any(r["item_id"] == row["item_id"] for r in cross):
                continue
            cross.append({**row, "subset_reason": "backfill_cross", "expected_evidence_plan": {
                "primary_document_ids": row.get("primary_document_ids"),
                "supporting_document_ids": row.get("supporting_document_ids"),
                "roles": row.get("roles"),
                "needs_merge": row.get("needs_merge"),
            }})
            if len(cross) >= args.cross_limit:
                break

    out_dir = ROOT / "data/enterprise_docs/demo_company"
    out_dir.mkdir(parents=True, exist_ok=True)

    single_path = out_dir / "eval_subset_single.jsonl"
    cross_path = out_dir / "eval_subset_cross.jsonl"
    summary_path = out_dir / "eval_subset_summary.json"
    note_path = out_dir / "eval_subset_criteria.md"

    for path, rows in ((single_path, single), (cross_path, cross)):
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "single_count": len(single),
        "cross_count": len(cross),
        "single_item_ids": [r["item_id"] for r in single],
        "cross_item_ids": [r["item_id"] for r in cross],
        "single_by_domain": _domain_counts(single),
        "cross_by_kind": {
            "quantitative": sum(1 for r in cross if r.get("kind") == "quantitative"),
            "qualitative": sum(1 for r in cross if r.get("kind") == "qualitative"),
        },
        "criteria_note_path": str(note_path.relative_to(ROOT)),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    note_path.write_text(SUBSET_CRITERIA_NOTE.strip() + "\n", encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _domain_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        d = str(r.get("domain") or "unknown")
        counts[d] = counts.get(d, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
