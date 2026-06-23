"""Deterministic corpus-unit pre-filter for Golden Set Distillation R2.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl

# --- Pattern libraries -------------------------------------------------------

COMPANY_ALIASES: Dict[str, List[str]] = {
    "한샘": ["한샘", "㈜한샘", "HANSSEM", "Hanssem", "(주)한샘"],
    "레이시온": ["레이시온", "RAYSOLUTION", "Raysolution", "레이 시 온"],
    "무신사": ["무신사", "MUSINSA", "Musinsa"],
}

CROSS_COMPANY_MARKERS: List[str] = [
    "삼성전기",
    "여수광양항만공사",
    "여수광양항만",
    "여수항",
    "현대트랜시스",
    "기아자동차",
    "기아 ",
    "에이피알",
    "APR ",
    "Samsung Electro",
    "현대트랜시스",
]

NAV_MENU_KEYWORDS: List[str] = [
    "정보공개제도",
    "정보공개",
    "민원서비스",
    "민원신청",
    "온라인 민원",
    "지면보기",
    "사이트맵",
    "바로가기",
    "메뉴",
    "로그인",
    "회원가입",
    "어디서 확인",
    "어디에서 찾",
    "Table of Contents",
    "TABLE OF CONTENTS",
    "목차",
]

LISTING_KEYWORDS: List[str] = [
    "접수번호",
    "파일 크기",
    "공시일",
    "작성일",
    "발표일",
    "발행일",
    "접수되었",
    "DART",
    "dart.fss",
    "전자공시",
    "공시 ",
]

VENDOR_KEYWORDS: List[str] = [
    "제작 과정",
    "제작 교육",
    "검증 대응 교육",
    "품질 향상 및 검증",
    "안정적인 업체",
    "보고서 제작",
    "ESG 담당자에게 추천",
]

NEWS_UI_KEYWORDS: List[str] = [
    "뉴스 듣기",
    "기사 공유",
    "네이버 채널구독",
    "다음 채널구독",
    "주소복사",
    "다크모드",
    "페이스북",
    "카카오톡",
]

NON_ESG_FINANCIAL_KEYWORDS: List[str] = [
    "Equity Research",
    "Target price",
    "Analysts who prepared",
    "Current price",
    "Downside",
    "Consensus OP",
]

PRIMARY_ESG_KEYWORDS: List[str] = [
    "Sustainability Report",
    "SUSTAINABILITY REPORT",
    "지속가능경영 보고서",
    "지속가능경영보고서",
    "지속가능경영 활동",
    "ESG Factbook",
    "ESG Management",
    "지속가능경영 전략",
]

GOVERNANCE_POLICY_KEYWORDS: List[str] = [
    "거버넌스",
    "이사회",
    "윤리",
    "컴플라이언스",
    "Governance",
    "정책",
    "컴플라이언스",
    "내부통제",
]

METRIC_RE = re.compile(
    r"\d+[\.,]?\d*\s*(%|명|건|톤|tco2|tco₂|mwh|억|원|gj|kwh|mw|㎏|kg|liters?)",
    re.IGNORECASE,
)
DATE_TOKEN_RE = re.compile(r"\d{4}년|\d{1,2}월|\d{1,2}일")
KOREAN_CHUNK_RE = re.compile(r"[가-힣]{4,}")
TOC_RE = re.compile(r"Table of Contents|TABLE OF CONTENTS|목차|Contents", re.IGNORECASE)
PAGE_NUM_RE = re.compile(r"\b\d{3}\b")
PORTAL_MENU_RE = re.compile(
    r"(인물|사회 일반|지면보기|문화/생활|증권|부동산|정치 일반|경제|IT/과학|사회적책임투자)"
)
TOC_OUTLINE_RE = re.compile(
    r"(Topic \d|Part \d\.|INTRODUCTION|Appendix|MATERIAL FOCUS|· CEO)",
    re.IGNORECASE,
)


@dataclass
class UnitSignals:
    primary_esg: bool = False
    metric_disclosure: bool = False
    governance_policy: bool = False
    risk_strategy: bool = False
    nav_noise: bool = False
    listing_noise: bool = False
    toc_heavy: bool = False
    cross_company: bool = False
    vendor_noise: bool = False
    news_ui: bool = False
    non_esg_financial: bool = False
    non_esg_annual: bool = False
    date_only: bool = False
    too_short: bool = False
    korean_chunks: int = 0
    patterns: List[str] = field(default_factory=list)


@dataclass
class PrefilterOutcome:
    decision: str  # keep | drop | conditional
    rule_id: str
    reason: str
    notes: str
    patterns: List[str]


def _blob(unit: Dict[str, Any]) -> str:
    text = unit.get("text") or ""
    section = unit.get("section_path") or ""
    return f"{section}\n{text}"


def _company_aliases(company: str) -> List[str]:
    return COMPANY_ALIASES.get(company, [company])


def _mentions_other_company(company: str, blob: str) -> bool:
    own = _company_aliases(company)
    for marker in CROSS_COMPANY_MARKERS:
        if marker not in blob:
            continue
        if any(marker in alias or alias in marker for alias in own):
            continue
        return True
    for other, aliases in COMPANY_ALIASES.items():
        if other == company:
            continue
        for alias in aliases:
            if len(alias) >= 3 and alias in blob:
                return True
    return False


def _is_portal_category_menu(text: str) -> bool:
    head = text[:600]
    return len(PORTAL_MENU_RE.findall(head)) >= 4


def _is_news_article_rewrite(text: str) -> bool:
    head = text[:500]
    markers = sum(1 for k in ("기자", "발행일", "댓글") if k in head)
    return markers >= 2


def _is_toc_heavy(text: str) -> bool:
    head = text[:2000]
    if not TOC_RE.search(head):
        return False
    if len(PAGE_NUM_RE.findall(head)) >= 4:
        return True
    return len(TOC_OUTLINE_RE.findall(head)) >= 5


def _is_nav_dominant(text: str, has_esg_body: bool) -> bool:
    head = text[:800]
    nav_hits = sum(1 for k in NAV_MENU_KEYWORDS if k in head)
    if nav_hits >= 2:
        return True
    if nav_hits >= 1 and not has_esg_body:
        return True
    if _is_toc_heavy(text) and not has_esg_body:
        return True
    return False


def _is_listing_dominant(text: str, has_metric: bool) -> bool:
    listing_hits = sum(1 for k in LISTING_KEYWORDS if k in text)
    if listing_hits >= 2 and not has_metric:
        return True
    if listing_hits >= 1 and len(text) < 400 and not has_metric:
        return True
    return False


def _is_date_only(text: str, has_metric: bool) -> bool:
    if has_metric:
        return False
    date_tokens = len(DATE_TOKEN_RE.findall(text))
    korean_chunks = len(KOREAN_CHUNK_RE.findall(text))
    if date_tokens >= 3 and korean_chunks < 35:
        esg_kw = sum(1 for k in PRIMARY_ESG_KEYWORDS + GOVERNANCE_POLICY_KEYWORDS if k in text)
        return esg_kw < 2
    return False


def _is_non_esg_annual(text: str) -> bool:
    head = text[:600]
    if "ANNUAL REPORT" in head or "ANNUALREPORT" in head.replace(" ", ""):
        if not any(k in head for k in ("지속가능", "Sustainability", "ESG")):
            return True
    return False


def detect_signals(unit: Dict[str, Any]) -> UnitSignals:
    text = unit.get("text") or ""
    blob = _blob(unit)
    company = unit.get("company") or ""
    source_type = (unit.get("source_type") or "").lower()

    sig = UnitSignals()
    sig.korean_chunks = len(KOREAN_CHUNK_RE.findall(text))
    sig.too_short = len(text.strip()) < 200

    sig.primary_esg = any(k in blob for k in PRIMARY_ESG_KEYWORDS)
    sig.metric_disclosure = bool(METRIC_RE.search(text))
    sig.governance_policy = any(k in blob for k in GOVERNANCE_POLICY_KEYWORDS)
    sig.risk_strategy = any(
        k in blob for k in ("전략", "리스크", "중대성", "materiality", "이해관계자", "TCFD", "Net zero")
    )

    sig.cross_company = _mentions_other_company(company, blob)
    sig.news_ui = (
        source_type == "news"
        or any(k in text for k in NEWS_UI_KEYWORDS)
        or _is_news_article_rewrite(text)
        or _is_portal_category_menu(text)
    )
    sig.vendor_noise = any(k in blob for k in VENDOR_KEYWORDS)
    sig.non_esg_financial = any(k in text for k in NON_ESG_FINANCIAL_KEYWORDS)
    sig.non_esg_annual = _is_non_esg_annual(text)

    has_esg_body = sig.primary_esg or sig.metric_disclosure or sig.governance_policy
    sig.nav_noise = _is_nav_dominant(text, has_esg_body) or (
        any(k in text for k in NAV_MENU_KEYWORDS) and not has_esg_body
    )
    sig.toc_heavy = _is_toc_heavy(text)
    sig.listing_noise = _is_listing_dominant(text, sig.metric_disclosure)
    sig.date_only = _is_date_only(text, sig.metric_disclosure)

    if sig.primary_esg:
        sig.patterns.append("primary_esg_narrative")
    if sig.metric_disclosure:
        sig.patterns.append("metric_disclosure")
    if sig.governance_policy:
        sig.patterns.append("governance_or_policy_statement")
    if sig.risk_strategy:
        sig.patterns.append("risk_strategy_narrative")
    if sig.nav_noise or sig.toc_heavy:
        sig.patterns.append("nav_or_menu_noise")
    if sig.listing_noise:
        sig.patterns.append("listing_or_index_noise")
    if sig.date_only:
        sig.patterns.append("date_only_disclosure")
    if sig.cross_company:
        sig.patterns.append("cross_company_mismatch")
    if sig.vendor_noise:
        sig.patterns.append("vendor_or_training_content")
    if sig.news_ui:
        sig.patterns.append("secondary_news_rewrite")
    if sig.non_esg_financial:
        sig.patterns.append("non_esg_financial_research")
    if sig.non_esg_annual:
        sig.patterns.append("non_esg_annual_report")

    return sig


def _is_mixed_section(sig: UnitSignals) -> bool:
    has_positive = sig.primary_esg or sig.metric_disclosure or sig.governance_policy
    if not has_positive:
        return False
    return sig.toc_heavy or sig.nav_noise or sig.listing_noise


def classify_unit(unit: Dict[str, Any]) -> PrefilterOutcome:
    sig = detect_signals(unit)

    if sig.cross_company:
        return PrefilterOutcome(
            "drop",
            "R1_cross_company_mismatch",
            "cross_company_mismatch",
            "Text mentions another company/organization not matching package company.",
            sig.patterns,
        )

    if sig.news_ui:
        return PrefilterOutcome(
            "drop",
            "R6_secondary_news_rewrite_ui_noise",
            "secondary_news_rewrite",
            "News article UI or rewrite, not primary sustainability report body.",
            sig.patterns,
        )

    if sig.nav_noise and not (sig.primary_esg and sig.korean_chunks >= 50 and not sig.toc_heavy):
        return PrefilterOutcome(
            "drop",
            "R2_nav_or_menu_noise",
            "nav_or_menu_noise",
            "Navigation, menu, or TOC-dominant chunk without usable ESG body.",
            sig.patterns,
        )

    if sig.listing_noise:
        return PrefilterOutcome(
            "drop",
            "R3_listing_or_index_noise",
            "listing_or_index_noise",
            "DART/listing metadata or file index without ESG metric substance.",
            sig.patterns,
        )

    if sig.date_only:
        return PrefilterOutcome(
            "drop",
            "R4_date_only_disclosure",
            "date_only_disclosure",
            "Mostly dates/disclosure metadata without meaningful ESG fact.",
            sig.patterns,
        )

    if sig.vendor_noise:
        return PrefilterOutcome(
            "drop",
            "R5_vendor_or_training_content",
            "vendor_or_training_content",
            "Generic vendor/training/promotional content about report production.",
            sig.patterns,
        )

    if sig.non_esg_financial or sig.non_esg_annual:
        return PrefilterOutcome(
            "drop",
            "R7_non_esg_financial_or_annual_irrelevant",
            "non_esg_financial_or_annual_irrelevant",
            "Equity research or non-ESG annual report marketing content.",
            sig.patterns,
        )

    if sig.too_short or sig.korean_chunks < 8:
        return PrefilterOutcome(
            "drop",
            "R7_non_esg_financial_or_annual_irrelevant",
            "insufficient_substance",
            "Chunk too short or lacks substantive Korean/ESG text.",
            sig.patterns,
        )

    if sig.primary_esg and not _is_mixed_section(sig):
        return PrefilterOutcome(
            "keep",
            "R8_primary_esg_narrative_keep",
            "primary_esg_narrative",
            "Clean sustainability report narrative suitable for Distillation.",
            sig.patterns,
        )

    if (sig.metric_disclosure or sig.governance_policy) and not _is_mixed_section(sig):
        return PrefilterOutcome(
            "keep",
            "R9_metric_or_policy_keep",
            "metric_or_policy_disclosure",
            "Metric or governance/policy disclosure with clear grounding potential.",
            sig.patterns,
        )

    if _is_mixed_section(sig) and (sig.primary_esg or sig.metric_disclosure or sig.governance_policy):
        return PrefilterOutcome(
            "conditional",
            "R10_conditional_intro_or_mixed_section",
            "conditional_mixed_section",
            "ESG signal present but mixed with TOC/listing/nav — pilot/review only.",
            sig.patterns,
        )

    return PrefilterOutcome(
        "drop",
        "R7_non_esg_financial_or_annual_irrelevant",
        "insufficient_substance",
        "No clear ESG narrative, metric, or policy substance after filtering.",
        sig.patterns,
    )


def _enrich_unit(unit: Dict[str, Any], outcome: PrefilterOutcome) -> Dict[str, Any]:
    row = dict(unit)
    row["prefilter_decision"] = outcome.decision
    row["prefilter_reason"] = outcome.reason
    row["prefilter_rule_id"] = outcome.rule_id
    row["prefilter_notes"] = outcome.notes
    row["unit_taxonomy"] = outcome.patterns
    row["prefilter_version"] = "2.1.0"
    return row


def _fact_fingerprint(unit: Dict[str, Any]) -> str:
    text = (unit.get("text") or "")[:500]
    for kw in PRIMARY_ESG_KEYWORDS:
        idx = text.find(kw)
        if idx >= 0:
            text = text[idx : idx + 200]
            break
    norm = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()[:12]


def select_pilot_hanssem(
    eligible: List[Dict[str, Any]],
    *,
    n: int = 15,
) -> List[Dict[str, Any]]:
    pool = [u for u in eligible if u.get("company") == "한샘"]
    if not pool:
        return []

    def bucket(u: Dict[str, Any]) -> str:
        tax = set(u.get("unit_taxonomy") or [])
        rule = u.get("prefilter_rule_id") or ""
        if rule == "R9_metric_or_policy_keep" and "metric_disclosure" in tax:
            return "metric"
        if rule == "R9_metric_or_policy_keep" and "governance_or_policy_statement" in tax:
            return "governance"
        if "metric_disclosure" in tax and "primary_esg_narrative" not in tax:
            return "metric"
        if "governance_or_policy_statement" in tax and "primary_esg_narrative" not in tax:
            return "governance"
        if "primary_esg_narrative" in tax:
            return "primary"
        if "metric_disclosure" in tax:
            return "metric"
        if "governance_or_policy_statement" in tax:
            return "governance"
        return "other"

    target = {"primary": 9, "metric": 4, "governance": 2}
    chosen: List[Dict[str, Any]] = []
    seen_fp: set[str] = set()
    by_bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for u in pool:
        by_bucket[bucket(u)].append(u)

    for b in ("primary", "metric", "governance", "other"):
        rows = sorted(by_bucket[b], key=lambda x: -len(x.get("text") or ""))
        for u in rows:
            if len(chosen) >= n:
                break
            if bucket(u) == "other" and sum(1 for c in chosen if bucket(c) != "other") < n - 1:
                continue
            need = target.get(bucket(u), 0) - sum(1 for c in chosen if bucket(c) == bucket(u))
            if bucket(u) in target and need <= 0:
                continue
            fp = _fact_fingerprint(u)
            if fp in seen_fp:
                continue
            seen_fp.add(fp)
            chosen.append(u)
        if len(chosen) >= n:
            break

    if len(chosen) < n:
        for u in sorted(pool, key=lambda x: -len(x.get("text") or "")):
            if len(chosen) >= n:
                break
            if u in chosen:
                continue
            fp = _fact_fingerprint(u)
            if fp in seen_fp:
                continue
            seen_fp.add(fp)
            chosen.append(u)

    return chosen[:n]


def run_prefilter(
    *,
    input_path: Path,
    output_dir: Path,
    pilot_path: Optional[Path] = None,
    pilot_size: int = 15,
) -> Dict[str, Any]:
    units = read_jsonl(input_path)
    keep_rows: List[Dict[str, Any]] = []
    drop_rows: List[Dict[str, Any]] = []
    conditional_rows: List[Dict[str, Any]] = []

    rule_counts: Counter = Counter()
    company_counts: Dict[str, Counter] = defaultdict(Counter)
    source_type_counts: Dict[str, Counter] = defaultdict(Counter)
    pattern_counts: Counter = Counter()
    examples: Dict[str, List[Dict[str, Any]]] = {"keep": [], "drop": [], "conditional": []}

    for unit in units:
        outcome = classify_unit(unit)
        enriched = _enrich_unit(unit, outcome)
        rule_counts[outcome.rule_id] += 1
        company = unit.get("company") or "unknown"
        company_counts[company][outcome.decision] += 1
        st = unit.get("source_type") or "unknown"
        source_type_counts[st][outcome.decision] += 1
        for p in outcome.patterns:
            pattern_counts[p] += 1

        if outcome.decision == "keep":
            keep_rows.append(enriched)
        elif outcome.decision == "conditional":
            conditional_rows.append(enriched)
        else:
            drop_rows.append(enriched)

        bucket = examples[outcome.decision]
        if len(bucket) < 5:
            bucket.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "company": company,
                    "record_id": unit.get("record_id"),
                    "prefilter_rule_id": outcome.rule_id,
                    "prefilter_reason": outcome.reason,
                    "text_preview": (unit.get("text") or "")[:220].replace("\n", " "),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    eligible_path = output_dir / "corpus_units_eligible.jsonl"
    rejected_path = output_dir / "corpus_units_rejected_r2_1.jsonl"
    conditional_path = output_dir / "corpus_units_conditional_r2_1.jsonl"

    write_jsonl(eligible_path, keep_rows)
    write_jsonl(rejected_path, drop_rows)
    if conditional_rows:
        write_jsonl(conditional_path, conditional_rows)

    pilot_rows: List[Dict[str, Any]] = []
    if pilot_path is not None:
        pilot_rows = select_pilot_hanssem(keep_rows, n=pilot_size)
        if pilot_rows:
            write_jsonl(pilot_path, pilot_rows)

    summary = {
        "prefilter_version": "2.1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "total": len(units),
        "keep_count": len(keep_rows),
        "drop_count": len(drop_rows),
        "conditional_count": len(conditional_rows),
        "by_rule_id": dict(rule_counts),
        "by_company": {c: dict(v) for c, v in company_counts.items()},
        "by_source_type": {s: dict(v) for s, v in source_type_counts.items()},
        "by_pattern": dict(pattern_counts.most_common()),
        "output_files": {
            "eligible": str(eligible_path),
            "rejected": str(rejected_path),
            "conditional": str(conditional_path) if conditional_rows else None,
            "pilot_hanssem": str(pilot_path) if pilot_path and pilot_rows else None,
        },
        "pilot_hanssem_count": len(pilot_rows),
        "examples": examples,
        "company_keep_totals": {
            c: company_counts[c].get("keep", 0) for c in company_counts
        },
    }

    summary_path = output_dir / "prefilter_r2_1_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def write_report(summary: Dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Golden Set — Pre-filter Round 2.1 Report",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu",
        "",
        "Lọc deterministic corpus unit trước Distillation R2.1; tách `keep` / `drop` / `conditional`.",
        "",
        "## Rule set đã implement",
        "",
        "| Rule ID | Hành vi |",
        "|---------|---------|",
        "| `R1_cross_company_mismatch` | drop |",
        "| `R2_nav_or_menu_noise` | drop |",
        "| `R3_listing_or_index_noise` | drop |",
        "| `R4_date_only_disclosure` | drop |",
        "| `R5_vendor_or_training_content` | drop |",
        "| `R6_secondary_news_rewrite_ui_noise` | drop |",
        "| `R7_non_esg_financial_or_annual_irrelevant` | drop |",
        "| `R8_primary_esg_narrative_keep` | keep |",
        "| `R9_metric_or_policy_keep` | keep |",
        "| `R10_conditional_intro_or_mixed_section` | conditional |",
        "",
        "## Tổng số unit đầu vào",
        "",
        f"- **total:** {summary['total']}",
        f"- **keep:** {summary['keep_count']}",
        f"- **drop:** {summary['drop_count']}",
        f"- **conditional:** {summary['conditional_count']}",
        "",
        "## Breakdown theo `prefilter_rule_id`",
        "",
        "| rule_id | count |",
        "|---------|------:|",
    ]
    for rule_id, count in sorted(summary.get("by_rule_id", {}).items()):
        lines.append(f"| `{rule_id}` | {count} |")

    lines.extend(["", "## Breakdown theo công ty", "", "| company | keep | drop | conditional |", "|---------|-----:|-----:|------------:|"])
    for company, decisions in sorted(summary.get("by_company", {}).items()):
        lines.append(
            f"| {company} | {decisions.get('keep', 0)} | {decisions.get('drop', 0)} | {decisions.get('conditional', 0)} |"
        )

    lines.extend(["", "## Breakdown theo pattern (unit_taxonomy)", "", "| pattern | count |", "|---------|------:|"])
    for pat, count in summary.get("by_pattern", {}).items():
        lines.append(f"| `{pat}` | {count} |")

    for label, key in [("keep", "keep"), ("drop", "drop"), ("conditional", "conditional")]:
        lines.extend([f"", f"## Ví dụ tiêu biểu — {label}", ""])
        for ex in summary.get("examples", {}).get(key, [])[:5]:
            lines.append(f"- **{ex['unit_id']}** (`{ex['prefilter_rule_id']}`): {ex['text_preview']}…")

    ck = summary.get("company_keep_totals", {})
    lines.extend(
        [
            "",
            "## Đánh giá pilot",
            "",
            f"- **한샘** eligible keep: **{ck.get('한샘', 0)}** — pilot 15 unit: **{'ĐỦ' if ck.get('한샘', 0) >= 15 else 'CHƯA ĐỦ'}**",
            f"- **레이시온** eligible keep: **{ck.get('레이시온', 0)}**",
            f"- **무신사** eligible keep: **{ck.get('무신사', 0)}**",
            f"- Pilot file: `{summary.get('output_files', {}).get('pilot_hanssem', 'n/a')}` ({summary.get('pilot_hanssem_count', 0)} rows)",
            "",
            "## Kết luận và bước kế tiếp",
            "",
            "1. Dùng `corpus_units_eligible.jsonl` làm input Distillation R2.1 pilot (15 unit `한샘`).",
            "2. `corpus_units_conditional_r2_1.jsonl` chỉ dùng khi review/pilot có cờ strict.",
            "3. Chưa chạy step 2 full; chưa mở Evol/Judge/benchmark.",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Golden Set corpus pre-filter R2.1")
    parser.add_argument(
        "--input",
        default="data/golden_set/v2/step1_corpus_units/corpus_units.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        default="data/golden_set/v2/step1_corpus_units",
    )
    parser.add_argument(
        "--pilot-out",
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible.jsonl",
    )
    parser.add_argument("--pilot-size", type=int, default=15)
    parser.add_argument(
        "--report",
        default="reports/golden_set_prefilter_round2_1.md",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    input_path = root / args.input
    output_dir = root / args.output_dir
    pilot_path = root / args.pilot_out
    report_path = root / args.report

    summary = run_prefilter(
        input_path=input_path,
        output_dir=output_dir,
        pilot_path=pilot_path,
        pilot_size=args.pilot_size,
    )
    write_report(summary, report_path)

    # Avoid Windows console encoding issues
    print(json.dumps(
        {
            "total": summary["total"],
            "keep_count": summary["keep_count"],
            "drop_count": summary["drop_count"],
            "conditional_count": summary["conditional_count"],
            "by_company_keep": summary["company_keep_totals"],
            "pilot_hanssem_count": summary["pilot_hanssem_count"],
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
