#!/usr/bin/env python3
"""Larger synthetic answerability eval (~200 cases) — coverage + adversarial tiers.

WARNING: this is a SYNTHETIC, self-generated eval. Ground truth is controlled, so the
"easy" tier passes by construction (it checks the mechanism across many family/metric
combinations). The real signal is the adversarial tier (known failure modes) and the
abstain-safety rate. A meaningful accuracy number still requires REAL company questions.

Run: python scripts/eval_answerability_suite.py
Writes: reports/enterprise_docs_answerability_eval_200_<date>/
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.crossdoc_capability_benchmark import evaluate_case  # noqa: E402

SEED = 7
YEARS = list(range(2018, 2025))
FAMS = [
    ("environment_narrative", ["재생에너지 사용 비율", "용수 재사용률", "폐기물 재활용률", "환경 ESG 등급",
                               "탄소중립 목표 연도", "대기오염물질 배출량", "녹색구매 비율"]),
    ("employee_hr", ["여성 직원 비율", "육아휴직 사용률", "산업재해율", "이직률", "1인당 교육 시간",
                     "장애인 고용률", "정규직 비율"]),
    ("employee_headcount", ["총 구성원 수"]),
    ("governance_board", ["이사회 규모", "사외이사 비율", "이사회 출석률", "감사위원 수", "여성 이사 수", "대표이사 보수"]),
]
VALS = ["12.3%", "45", "1,234명", "2050년", "0.21", "A등급", "98%", "3,210 tCO2e", "7명", "15.5%"]
OOS = [
    ("CEO 개인 휴대폰 번호는?", "개인 연락처", "unrelated_personal_info"),
    ("오늘 서울 날씨 어때요?", "날씨", "weather_smalltalk"),
    ("점심 메뉴 추천해줘", "메뉴", "chitchat"),
    ("본사 주차장 위치는?", "주차장", "facility_misc"),
    ("사내 와이파이 비밀번호는?", "와이파이", "facility_misc"),
    ("올해 공휴일이 며칠이야?", "공휴일", "calendar_misc"),
    ("회사 주식 지금 사도 될까?", "투자조언", "investment_tip"),
    ("드레스코드가 어떻게 되나요?", "복장", "hr_misc"),
    ("이 회사 어때요?", "", ""),
    ("엘리베이터 점검 시간은?", "엘리베이터", "facility_misc"),
    ("구내식당 운영 시간은?", "식당", "facility_misc"),
    ("주말에 출근 가능한가요?", "출근", "hr_misc"),
]


def build_cases() -> list[dict]:
    random.seed(SEED)
    cases: list[dict] = []
    i = 0

    def add(cid, exp, q, item, pf, corpus, tier):
        cases.append({
            "_tier": tier, "case_id": cid, "expected_answerability": exp,
            "test_type": "answerability_probe", "case_origin": "constructed",
            "capability": "answerability_classification",
            "capability_tags": ["answerability", "abstain_safety"],
            "company_id": "capability_synthetic", "kind": "quantitative",
            "probe": {"question": q, "item": item, "pattern_family": pf, "kind": "quantitative"},
            "inline_corpus": [{"logical_doc_id": "d", "text": t} for t in corpus],
        })

    for pf, items in FAMS:
        for it in items:
            for _ in range(2):
                add(f"GEN-ANS-{i}", "answerable", f"{random.choice(YEARS)}년 {it}은?", it, pf,
                    [f"{it}: {random.choice(VALS)}"], "easy"); i += 1
    for n in (1, 2, 3):
        for y in YEARS:
            add(f"GEN-ANSs{n}-{y}", "answerable", f"{y} Scope {n} 배출량은?", f"스코프 {n}",
                "environment_narrative", [f"Scope {n}: {random.randint(100, 9000)} tCO2e"], "easy")
    for pf, items in FAMS:
        for it in items:
            for _ in range(2):
                other = random.choice([x for x in items if x != it]) if len(items) > 1 else "기타 지표"
                add(f"GEN-NOI-{i}", "no_information", f"{it}은?", it, pf,
                    [f"{other}: {random.choice(VALS)}"], "easy"); i += 1
    for y in YEARS:
        add(f"GEN-NOIs3-{y}", "no_information", f"{y} Scope 3 배출량은?", "스코프 3",
            "scope_expansion", [f"Scope 1: {random.randint(100, 9000)} tCO2e"], "easy")
    for j, (q, it, pf) in enumerate(OOS):
        for k in range(5):
            add(f"GEN-OOS-{j}-{k}", "out_of_scope", q, it, pf,
                [f"Scope 1: {random.randint(100, 9000)} tCO2e"], "easy")
    for y in YEARS:
        add(f"GEN-ADVnokw-{y}", "no_information", f"{y}년에 탄소 얼마나 줄였나요?", "", "",
            [f"Scope 1: {random.randint(100, 9000)} tCO2e"], "adversarial")
        add(f"GEN-ADVtok-{y}", "no_information", f"{y} Scope 3 배출량은?", "스코프 3", "scope_expansion",
            ["스코프 3 측정 방법론은 별도 보고서를 참조하십시오"], "adversarial")
    for it, corp in [("여성 임원 비율", "이사회 내 여성 비중: 22%"),
                     ("탄소 배출", "온실가스 배출량 Scope 1: 1,200 tCO2e"),
                     ("직원 수", "총 구성원 수: 1,234명")]:
        pf = "governance_board" if "여성" in it else ("employee_hr" if "직원" in it else "environment_narrative")
        for k in range(5):
            add(f"GEN-ADVphr-{it}-{k}", "answerable", f"{it}은?", it, pf, [corp], "adversarial")
    return cases


def main() -> int:
    cases = build_cases()
    tt: dict = defaultdict(int); tk: dict = defaultdict(int)
    ok = 0; unans = 0; unsafe = 0
    conf: dict = defaultdict(lambda: defaultdict(int))
    for c in cases:
        o = evaluate_case(c)
        good = o["predicted_answerability"] == c["expected_answerability"]
        ok += good; tt[c["_tier"]] += 1; tk[c["_tier"]] += good
        conf[c["expected_answerability"]][o["predicted_answerability"]] += 1
        if c["expected_answerability"] in ("out_of_scope", "no_information"):
            unans += 1; unsafe += (0 if o.get("abstain_safe") else 1)
    n = len(cases)
    res = {
        "artifact_kind": "synthetic_answerability_eval",
        "warning": "Synthetic eval; easy tier passes by construction. Real signal = adversarial tier + abstain_safety. Real-data eval still required.",
        "seed": SEED,
        "total": n,
        "overall_accuracy": round(ok / n, 4),
        "by_tier": {t: {"correct": tk[t], "total": tt[t], "accuracy": round(tk[t] / tt[t], 4)} for t in tt},
        "abstain_safety_rate": round((unans - unsafe) / unans, 4),
        "confusion_expected_predicted": {k: dict(v) for k, v in conf.items()},
    }
    ts = datetime.now().strftime("%Y%m%d")
    out = ROOT / f"reports/enterprise_docs_answerability_eval_200_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
