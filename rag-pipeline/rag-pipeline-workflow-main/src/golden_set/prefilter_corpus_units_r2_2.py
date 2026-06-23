"""Corpus pre-filter R2.2 — tighter news/portal rejection + scored pilot selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl
from golden_set.prefilter_corpus_units_r2_1 import (
    COMPANY_ALIASES,
    CROSS_COMPANY_MARKERS,
    GOVERNANCE_POLICY_KEYWORDS,
    KOREAN_CHUNK_RE,
    LISTING_KEYWORDS,
    METRIC_RE,
    NAV_MENU_KEYWORDS,
    NON_ESG_FINANCIAL_KEYWORDS,
    PRIMARY_ESG_KEYWORDS,
    VENDOR_KEYWORDS,
    PrefilterOutcome,
    _blob,
    _company_aliases,
    _is_news_article_rewrite,
    _is_non_esg_annual,
    _is_portal_category_menu,
    _is_toc_heavy,
    _mentions_other_company,
)

PREFILTER_VERSION = "2.2.0"

# --- R2.2 extensions ---------------------------------------------------------

NEWS_UI_KEYWORDS_R22 = [
    "뉴스 듣기",
    "기사 공유",
    "네이버 채널",
    "다음 채널",
    "주소복사",
    "다크모드",
    "프린트",
    "글자 크기",
    "글자크기",
    "본문크기",
    "스크롤 이동",
    "이전 기사보기",
    "다음 기사보기",
    "URL 복사",
    "읽기모드",
    "기사듣기",
    "댓글입력",
    "Copyright",
    "All rights reserved",
    "무단전재",
    "다른기사 보기",
]

PORTAL_NAV_KEYWORDS_R22 = [
    "사이트맵",
    "홈 >",
    "기업소개",
    "경영이념",
    "IR자료실",
    "공시정보",
    "고객지원",
    "한샘서비스센터",
    "보고서&자료실",
    "정기보고서",
    "전자공고",
    "Language: Korean",
]

ARCHIVE_LISTING_KEYWORDS = [
    "다운로드",
    "국문 영문",
    "국문\n영문",
    "2020년 한샘",
    "2021년 한샘",
    "2022년 한샘",
    "2023년 한샘",
    "2024년 한샘",
    "2025 한샘",
    "보고서 정책 및 인증서",
]

BYLINE_RE = re.compile(r"기자|기자\]|\[.*기자\]|@dailyt|@100ssd|kih@")
REPORT_MENTION_RE = re.compile(
    r"지속가능경영보고서.{0,20}발간|발간.{0,20}지속가능경영보고서",
    re.IGNORECASE,
)
JSON_METADATA_RE = re.compile(r'^\s*\[\{"CODE_TYPE"')
URL_HEAVY_RE = re.compile(r"https?://|www\.\w+\.(co\.kr|com)", re.I)

ESG_FACT_SIGNALS = [
    (r"\d+\s*개\s*중대", 3),
    (r"중대\s*이슈", 2),
    (r"이중\s*중대성", 2),
    (r"탄소중립|Net\s*Zero|넷제로", 3),
    (r"이사회", 2),
    (r"ESG\s*위원회", 2),
    (r"Scope\s*[123]", 2),
    (r"CDP", 2),
    (r"ESRS|ISSB|GRI\s*Standard", 2),
    (r"온실가스", 2),
    (r"인권", 1),
    (r"협력사\s*동반", 1),
    (r"\d{4}년\s*까지", 2),
    (r"[A-Z]\+?'?\s*등급", 2),
    (r"다섯\s*번째|여섯\s*번째|세\s*번째", 2),
    (r"보고기간", 2),
    (r"K-ESG|KGCS", 2),
]


@dataclass
class UnitSignalsR22:
    primary_esg_keyword: bool = False
    substantive_esg: bool = False
    substance_score: int = 0
    noise_score: int = 0
    metric_disclosure: bool = False
    governance_policy: bool = False
    risk_strategy: bool = False
    news_chrome: bool = False
    portal_nav: bool = False
    archive_listing: bool = False
    report_mention_only: bool = False
    byline_heavy: bool = False
    url_chrome: bool = False
    cross_company: bool = False
    vendor_noise: bool = False
    toc_heavy: bool = False
    listing_noise: bool = False
    date_only: bool = False
    too_short: bool = False
    korean_chunks: int = 0
    patterns: List[str] = field(default_factory=list)


@dataclass
class ScoredUnit:
    unit: Dict[str, Any]
    outcome: PrefilterOutcome
    substance_score: int = 0
    noise_score: int = 0
    selection_priority: float = 0.0
    duplicate_cluster_id: str = ""
    pilot_candidate: bool = False
    pilot_candidate_notes: str = ""


def _count_noise(text: str) -> Tuple[int, List[str]]:
    head = text[:700]
    flags: List[str] = []
    score = 0
    for k in NEWS_UI_KEYWORDS_R22:
        if k in text:
            score += 2
            if "news_ui" not in flags:
                flags.append("news_ui")
    for k in PORTAL_NAV_KEYWORDS_R22:
        if k in head:
            score += 2
            if "portal_nav" not in flags:
                flags.append("portal_nav")
    for k in ARCHIVE_LISTING_KEYWORDS:
        if k in text:
            score += 2
            if "archive_listing" not in flags:
                flags.append("archive_listing")
    if BYLINE_RE.search(head):
        score += 3
        flags.append("byline")
    if JSON_METADATA_RE.search(text[:200]):
        score += 4
        flags.append("json_metadata")
    if len(URL_HEAVY_RE.findall(head)) >= 2:
        score += 3
        flags.append("url_chrome")
    # repeated title block
    title_hits = text.count("지속가능경영보고서 발간")
    if title_hits >= 3:
        score += 3
        flags.append("repeated_title")
    return score, flags


def _substance_score(text: str) -> Tuple[int, bool]:
    score = 0
    for pat, weight in ESG_FACT_SIGNALS:
        if re.search(pat, text, re.IGNORECASE):
            score += weight
    if METRIC_RE.search(text):
        score += 3
    chunks = len(KOREAN_CHUNK_RE.findall(text))
    if chunks >= 40:
        score += 2
    elif chunks >= 20:
        score += 1
    return score, score >= 4


def _is_report_mention_only(text: str, substance: int) -> bool:
    mentions = len(REPORT_MENTION_RE.findall(text))
    generic = text.count("발간했다") + text.count("발간하였")
    return mentions >= 1 and substance < 4 and generic >= 1


def _is_listing_dominant_r22(text: str, has_metric: bool) -> bool:
    if has_metric and _substance_score(text)[0] >= 5:
        return False
    listing_hits = sum(1 for k in LISTING_KEYWORDS if k in text)
    archive_hits = sum(1 for k in ARCHIVE_LISTING_KEYWORDS if k in text)
    if archive_hits >= 2:
        return True
    if listing_hits >= 2 and not has_metric:
        return True
    return False


def _is_date_only_r22(text: str, substance: int) -> bool:
    if substance >= 4:
        return False
    date_tokens = len(re.findall(r"\d{4}년|\d{1,2}월|\d{1,2}일", text))
    return date_tokens >= 3 and substance < 3


def detect_signals_r22(unit: Dict[str, Any]) -> UnitSignalsR22:
    text = unit.get("text") or ""
    blob = _blob(unit)
    company = unit.get("company") or ""
    source_type = (unit.get("source_type") or "").lower()

    sig = UnitSignalsR22()
    sig.korean_chunks = len(KOREAN_CHUNK_RE.findall(text))
    sig.too_short = len(text.strip()) < 200

    sig.primary_esg_keyword = any(k in blob for k in PRIMARY_ESG_KEYWORDS)
    sig.substance_score, sig.substantive_esg = _substance_score(text)
    sig.noise_score, noise_flags = _count_noise(text)
    sig.metric_disclosure = bool(METRIC_RE.search(text))
    sig.governance_policy = any(k in blob for k in GOVERNANCE_POLICY_KEYWORDS)
    sig.risk_strategy = any(
        k in blob for k in ("전략", "리스크", "중대성", "materiality", "이해관계자", "TCFD", "Net zero")
    )

    sig.news_chrome = "news_ui" in noise_flags or source_type == "news"
    sig.portal_nav = "portal_nav" in noise_flags
    sig.archive_listing = "archive_listing" in noise_flags
    sig.byline_heavy = "byline" in noise_flags
    sig.url_chrome = "url_chrome" in noise_flags
    sig.report_mention_only = _is_report_mention_only(text, sig.substance_score)
    sig.cross_company = _mentions_other_company(company, blob)
    sig.vendor_noise = any(k in blob for k in VENDOR_KEYWORDS)
    sig.toc_heavy = _is_toc_heavy(text)
    sig.listing_noise = _is_listing_dominant_r22(text, sig.metric_disclosure)
    sig.date_only = _is_date_only_r22(text, sig.substance_score)

    if sig.substantive_esg and not sig.report_mention_only:
        sig.patterns.append("primary_esg_narrative")
    if sig.metric_disclosure:
        sig.patterns.append("metric_disclosure")
    if sig.governance_policy:
        sig.patterns.append("governance_or_policy_statement")
    if sig.risk_strategy:
        sig.patterns.append("risk_strategy_narrative")
    if sig.news_chrome or sig.byline_heavy:
        sig.patterns.append("secondary_news_rewrite")
    if sig.portal_nav or sig.toc_heavy:
        sig.patterns.append("nav_or_menu_noise")
    if sig.archive_listing or sig.listing_noise:
        sig.patterns.append("listing_or_index_noise")
    if sig.report_mention_only:
        sig.patterns.append("report_mention_only")
    if sig.cross_company:
        sig.patterns.append("cross_company_mismatch")

    return sig


def classify_unit_r22(unit: Dict[str, Any]) -> PrefilterOutcome:
    sig = detect_signals_r22(unit)
    text = unit.get("text") or ""

    if sig.cross_company:
        return PrefilterOutcome(
            "drop", "R1_cross_company_mismatch", "cross_company_mismatch",
            "Cross-company content.", sig.patterns,
        )

    # R6 / R10 R2.2: news chrome — conditional when facts strong; drop when noisy
    if sig.news_chrome or sig.byline_heavy:
        if _is_portal_category_menu(text):
            return PrefilterOutcome(
                "drop", "R6_secondary_news_rewrite_ui_noise", "secondary_news_rewrite",
                "News portal category menu chrome (R2.2).", sig.patterns,
            )
        if sig.substance_score >= 16 and sig.noise_score <= 8:
            return PrefilterOutcome(
                "conditional", "R10_conditional_intro_or_mixed_section", "conditional_news_with_facts",
                f"News/chrome mixed but strong ESG facts (sub={sig.substance_score}, noise={sig.noise_score}).",
                sig.patterns,
            )
        if sig.noise_score >= 9 or (sig.byline_heavy and sig.noise_score >= 6):
            return PrefilterOutcome(
                "drop", "R6_secondary_news_rewrite_ui_noise", "secondary_news_rewrite",
                "Article UI chrome or byline-heavy rewrite (R2.2).", sig.patterns,
            )

    # R2 R2.2: portal / archive
    if sig.portal_nav or sig.archive_listing:
        return PrefilterOutcome(
            "drop", "R2_nav_or_menu_noise", "nav_or_menu_noise",
            "Corporate portal, archive, or list page (R2.2).", sig.patterns,
        )

    if sig.url_chrome and sig.substance_score < 5:
        return PrefilterOutcome(
            "drop", "R6_secondary_news_rewrite_ui_noise", "url_chrome_only",
            "URL/share chrome without substantive body.", sig.patterns,
        )

    if sig.listing_noise:
        return PrefilterOutcome(
            "drop", "R3_listing_or_index_noise", "listing_or_index_noise",
            "Listing/index metadata.", sig.patterns,
        )

    if sig.date_only:
        return PrefilterOutcome(
            "drop", "R4_date_only_disclosure", "date_only_disclosure",
            "Date-only without ESG fact.", sig.patterns,
        )

    if sig.vendor_noise:
        return PrefilterOutcome(
            "drop", "R5_vendor_or_training_content", "vendor_or_training_content",
            "Vendor/training content.", sig.patterns,
        )

    if any(k in text for k in NON_ESG_FINANCIAL_KEYWORDS) or _is_non_esg_annual(text):
        return PrefilterOutcome(
            "drop", "R7_non_esg_financial_or_annual_irrelevant",
            "non_esg_financial_or_annual_irrelevant", "Non-ESG financial/annual.", sig.patterns,
        )

    if sig.too_short or sig.korean_chunks < 8:
        return PrefilterOutcome(
            "drop", "R7_non_esg_financial_or_annual_irrelevant", "insufficient_substance",
            "Too short.", sig.patterns,
        )

    if sig.report_mention_only:
        return PrefilterOutcome(
            "drop", "R8_primary_esg_narrative_keep", "report_mention_only",
            "Only report publication mention, no substantive ESG fact (R2.2).", sig.patterns,
        )

    noise_ratio = sig.noise_score / max(sig.substance_score, 1)

    # R8 R2.2: keep only with substantive facts + acceptable noise
    if sig.substantive_esg and sig.substance_score >= 4 and noise_ratio < 0.75:
        if not (sig.toc_heavy and sig.substance_score < 6):
            return PrefilterOutcome(
                "keep", "R8_primary_esg_narrative_keep", "primary_esg_narrative",
                f"Substantive ESG narrative (substance={sig.substance_score}, noise={sig.noise_score}).",
                sig.patterns,
            )

    if (sig.metric_disclosure or sig.governance_policy) and sig.substance_score >= 3 and noise_ratio < 0.75:
        if not sig.toc_heavy and not sig.portal_nav:
            return PrefilterOutcome(
                "keep", "R9_metric_or_policy_keep", "metric_or_policy_disclosure",
                f"Metric/policy with substance (substance={sig.substance_score}).", sig.patterns,
            )

    # R10 R2.2: conditional — mixed but extractable fact
    if sig.substantive_esg and sig.substance_score >= 3:
        if sig.toc_heavy or noise_ratio >= 0.75:
            return PrefilterOutcome(
                "conditional", "R10_conditional_intro_or_mixed_section", "conditional_mixed_section",
                f"Mixed/noisy but has facts (substance={sig.substance_score}, noise={sig.noise_score}).",
                sig.patterns,
            )

    return PrefilterOutcome(
        "drop", "R7_non_esg_financial_or_annual_irrelevant", "insufficient_substance",
        f"No qualifying substance (substance={sig.substance_score}, noise={sig.noise_score}).",
        sig.patterns,
    )


def _text_fingerprint(unit: Dict[str, Any]) -> str:
    text = re.sub(r"\s+", " ", (unit.get("text") or "")[:400]).strip().lower()
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


def _duplicate_cluster_id(unit: Dict[str, Any]) -> str:
    """Broad fact family for reporting; pilot dedupe uses `_text_fingerprint`."""
    text = (unit.get("text") or "")[:2000]
    clusters = []
    if re.search(r"탄소중립|Net\s*Zero|넷제로", text, re.I):
        clusters.append("fact_net_zero_2050")
    if re.search(r"\d+\s*개\s*중대|8개\s*중대", text):
        clusters.append("fact_8_material_issues")
    if re.search(r"이사회\s*중심|ESG\s*위원회", text):
        clusters.append("fact_board_esg_2021")
    if re.search(r"다섯\s*번째\s*발간|여섯\s*번째", text):
        clusters.append("fact_report_edition")
    if re.search(r"3년\s*연속|4년\s*연속", text):
        clusters.append("fact_consecutive_publish_years")
    if not clusters:
        clusters.append(_text_fingerprint(unit))
    return "|".join(sorted(set(clusters)))


def _enrich_r22(
    unit: Dict[str, Any],
    outcome: PrefilterOutcome,
    scored: ScoredUnit,
) -> Dict[str, Any]:
    row = dict(unit)
    row["prefilter_decision"] = outcome.decision
    row["prefilter_reason"] = outcome.reason
    row["prefilter_rule_id"] = outcome.rule_id
    row["prefilter_notes"] = outcome.notes
    row["unit_taxonomy"] = outcome.patterns
    row["prefilter_version"] = PREFILTER_VERSION
    row["substance_score"] = scored.substance_score
    row["noise_score"] = scored.noise_score
    row["selection_priority"] = round(scored.selection_priority, 2)
    row["duplicate_cluster_id"] = scored.duplicate_cluster_id
    row["pilot_candidate"] = scored.pilot_candidate
    row["pilot_candidate_notes"] = scored.pilot_candidate_notes
    return row


def _score_unit(unit: Dict[str, Any], outcome: PrefilterOutcome) -> ScoredUnit:
    sig = detect_signals_r22(unit)
    priority = sig.substance_score * 10.0 - sig.noise_score * 5.0
    if outcome.decision == "keep":
        priority += 20
    elif outcome.decision == "conditional":
        priority += 5
    cluster = _duplicate_cluster_id(unit)
    pilot_ok = False
    notes = ""
    if outcome.decision == "keep":
        pilot_ok = sig.substance_score >= 4 and sig.noise_score <= 4
        notes = "eligible keep"
    elif outcome.decision == "conditional" and sig.substance_score >= 16 and sig.noise_score <= 8:
        pilot_ok = True
        notes = "conditional with strong fact — pilot allowed"
    return ScoredUnit(
        unit=unit,
        outcome=outcome,
        substance_score=sig.substance_score,
        noise_score=sig.noise_score,
        selection_priority=priority,
        duplicate_cluster_id=cluster,
        pilot_candidate=pilot_ok,
        pilot_candidate_notes=notes,
    )


def _pilot_bucket(u: Dict[str, Any]) -> str:
    tax = set(u.get("unit_taxonomy") or [])
    if "metric_disclosure" in tax and u.get("substance_score", 0) >= 5:
        return "metric"
    if "governance_or_policy_statement" in tax:
        return "governance"
    if "primary_esg_narrative" in tax:
        return "primary"
    return "other"


def _supplement_from_rejected(
    rejected: List[Dict[str, Any]],
    *,
    need: int,
    seen_fp: Set[str],
    seen_net_zero: bool,
) -> List[Dict[str, Any]]:
    """Controlled pull from R2.2 rejected — borderline news with strong facts only."""
    rows = [u for u in rejected if u.get("company") == "한샘"]
    scored: List[Tuple[float, Dict[str, Any], str]] = []
    for u in rows:
        text = u.get("text") or ""
        sig = detect_signals_r22(u)
        out = classify_unit_r22(u)
        if out.reason in ("nav_or_menu_noise", "listing_or_index_noise", "url_chrome_only"):
            continue
        max_noise = 8 if sig.substance_score >= 18 else 7
        if sig.substance_score < 14 or sig.noise_score > max_noise:
            continue
        if sig.portal_nav or sig.archive_listing:
            continue
        if _is_portal_category_menu(text):
            continue
        if _is_news_article_rewrite(text) and sig.noise_score >= 6:
            continue
        fp = _text_fingerprint(u)
        if fp in seen_fp:
            continue
        if seen_net_zero and re.search(r"탄소중립|Net\s*Zero|넷제로", u.get("text") or "", re.I):
            continue
        note = (
            f"supplement from rejected: {out.reason}, "
            f"sub={sig.substance_score}, noise={sig.noise_score}"
        )
        prio = sig.substance_score * 10.0 - sig.noise_score * 5.0
        scored.append((prio, u, note))
    scored.sort(key=lambda x: -x[0])
    out_rows: List[Dict[str, Any]] = []
    for prio, u, note in scored:
        if len(out_rows) >= need:
            break
        fp = _text_fingerprint(u)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        row = dict(u)
        row["prefilter_decision"] = "conditional"
        row["prefilter_rule_id"] = "R10_conditional_intro_or_mixed_section"
        row["prefilter_reason"] = "pilot_supplement_borderline"
        row["prefilter_notes"] = note
        row["prefilter_version"] = PREFILTER_VERSION
        row["substance_score"] = detect_signals_r22(u).substance_score
        row["noise_score"] = detect_signals_r22(u).noise_score
        row["selection_priority"] = round(prio, 2)
        row["duplicate_cluster_id"] = _duplicate_cluster_id(u)
        row["pilot_candidate"] = True
        row["pilot_candidate_notes"] = note
        row["pilot_source"] = "rejected_supplement_r2_2"
        out_rows.append(row)
    return out_rows


def select_pilot_hanssem_r22(
    keep_pool: List[Dict[str, Any]],
    conditional_pool: Optional[List[Dict[str, Any]]] = None,
    rejected_pool: Optional[List[Dict[str, Any]]] = None,
    *,
    n: int = 15,
) -> List[Dict[str, Any]]:
    pool = list(keep_pool)
    if conditional_pool:
        pool.extend(conditional_pool)
    candidates = [u for u in pool if u.get("company") == "한샘" and u.get("pilot_candidate")]
    candidates.sort(key=lambda u: -float(u.get("selection_priority") or 0))

    targets = {"primary": 9, "metric": 3, "governance": 2, "other": 1}
    chosen: List[Dict[str, Any]] = []
    seen_fp: Set[str] = set()

    for b in ("primary", "metric", "governance", "other"):
        for u in candidates:
            if len(chosen) >= n:
                break
            if _pilot_bucket(u) != b:
                continue
            if sum(1 for c in chosen if _pilot_bucket(c) == b) >= targets.get(b, 0):
                continue
            fp = _text_fingerprint(u)
            if fp in seen_fp:
                continue
            seen_fp.add(fp)
            row = dict(u)
            src = "eligible_keep_r2_2" if u.get("prefilter_decision") == "keep" else "conditional_r2_2"
            row["pilot_source"] = src
            chosen.append(row)
        if len(chosen) >= n:
            break

    if len(chosen) < n:
        for u in candidates:
            if len(chosen) >= n:
                break
            if u in chosen:
                continue
            fp = _text_fingerprint(u)
            if fp in seen_fp:
                continue
            seen_fp.add(fp)
            row = dict(u)
            row["pilot_source"] = (
                "eligible_keep_r2_2" if u.get("prefilter_decision") == "keep" else "conditional_r2_2"
            )
            chosen.append(row)

    if len(chosen) < n and rejected_pool:
        has_net_zero = any(
            re.search(r"탄소중립|Net\s*Zero|넷제로", c.get("text") or "", re.I) for c in chosen
        )
        supplements = _supplement_from_rejected(
            rejected_pool,
            need=n - len(chosen),
            seen_fp=seen_fp,
            seen_net_zero=has_net_zero,
        )
        chosen.extend(supplements)

    return chosen[:n]


def run_prefilter_r22(
    *,
    input_path: Path,
    output_dir: Path,
    pilot_path: Optional[Path] = None,
    pilot_size: int = 15,
    r21_eligible_path: Optional[Path] = None,
    old_pilot_path: Optional[Path] = None,
) -> Dict[str, Any]:
    units = read_jsonl(input_path)
    keep_rows: List[Dict[str, Any]] = []
    drop_rows: List[Dict[str, Any]] = []
    conditional_rows: List[Dict[str, Any]] = []

    rule_counts: Counter = Counter()
    company_counts: Dict[str, Counter] = defaultdict(Counter)
    pattern_counts: Counter = Counter()
    scored_pool_for_pilot: List[Dict[str, Any]] = []

    for unit in units:
        outcome = classify_unit_r22(unit)
        scored = _score_unit(unit, outcome)
        enriched = _enrich_r22(unit, outcome, scored)

        rule_counts[outcome.rule_id] += 1
        company = unit.get("company") or "unknown"
        company_counts[company][outcome.decision] += 1
        for p in outcome.patterns:
            pattern_counts[p] += 1

        if outcome.decision == "keep":
            keep_rows.append(enriched)
            if scored.pilot_candidate:
                scored_pool_for_pilot.append(enriched)
        elif outcome.decision == "conditional":
            conditional_rows.append(enriched)
            if scored.pilot_candidate:
                scored_pool_for_pilot.append(enriched)
        else:
            drop_rows.append(enriched)

    output_dir.mkdir(parents=True, exist_ok=True)
    eligible_path = output_dir / "corpus_units_eligible_r2_2.jsonl"
    rejected_path = output_dir / "corpus_units_rejected_r2_2.jsonl"
    conditional_path = output_dir / "corpus_units_conditional_r2_2.jsonl"

    write_jsonl(eligible_path, keep_rows)
    write_jsonl(rejected_path, drop_rows)
    if conditional_rows:
        write_jsonl(conditional_path, conditional_rows)

    pilot_rows = select_pilot_hanssem_r22(
        keep_rows,
        conditional_pool=conditional_rows,
        rejected_pool=drop_rows,
        n=pilot_size,
    )
    if pilot_path and pilot_rows:
        write_jsonl(pilot_path, pilot_rows)

    # Compare with R2.1
    r21_hanssem_keep = 0
    if r21_eligible_path and r21_eligible_path.exists():
        r21_hanssem_keep = sum(
            1 for u in read_jsonl(r21_eligible_path) if u.get("company") == "한샘"
        )

    old_pilot_ids: List[str] = []
    if old_pilot_path and old_pilot_path.exists():
        old_pilot_ids = [u.get("record_id", "") for u in read_jsonl(old_pilot_path)]

    new_pilot_ids = [u.get("record_id", "") for u in pilot_rows]
    overlap = set(old_pilot_ids) & set(new_pilot_ids)

    summary = {
        "prefilter_version": PREFILTER_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "total": len(units),
        "keep_count": len(keep_rows),
        "drop_count": len(drop_rows),
        "conditional_count": len(conditional_rows),
        "pilot_candidate_pool": len(scored_pool_for_pilot),
        "pilot_selected": len(pilot_rows),
        "by_rule_id": dict(rule_counts),
        "by_company": {c: dict(v) for c, v in company_counts.items()},
        "by_pattern": dict(pattern_counts.most_common()),
        "company_keep_totals": {c: company_counts[c].get("keep", 0) for c in company_counts},
        "hanssem_keep_r21": r21_hanssem_keep,
        "hanssem_keep_r22": company_counts.get("한샘", Counter()).get("keep", 0),
        "old_pilot_record_ids": old_pilot_ids,
        "new_pilot_record_ids": new_pilot_ids,
        "pilot_overlap_count": len(overlap),
        "pilot_overlap_ids": sorted(overlap),
        "output_files": {
            "eligible_r2_2": str(eligible_path),
            "rejected_r2_2": str(rejected_path),
            "conditional_r2_2": str(conditional_path) if conditional_rows else None,
            "pilot_r2_2": str(pilot_path) if pilot_path and pilot_rows else None,
        },
        "pilot_supplement_count": sum(
            1 for u in pilot_rows if u.get("pilot_source") == "rejected_supplement_r2_2"
        ),
        "pilot_selection": [
            {
                "record_id": u.get("record_id"),
                "prefilter_decision": u.get("prefilter_decision"),
                "pilot_source": u.get("pilot_source"),
                "substance_score": u.get("substance_score"),
                "noise_score": u.get("noise_score"),
                "selection_priority": u.get("selection_priority"),
                "duplicate_cluster_id": u.get("duplicate_cluster_id"),
                "pilot_candidate_notes": u.get("pilot_candidate_notes"),
            }
            for u in pilot_rows
        ],
    }
    return summary


def write_report_r22(summary: Dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Golden Set — Pre-filter Round 2.2 + Pilot Selection",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu R2.2",
        "",
        "Siết prefilter sau pilot Distillation R2.1 (yield 3/15): loại news chrome, portal/archive, report-mention-only; chọn pilot Hansem 15 unit sạch hơn với mục tiêu Distillation **8–10 keep**.",
        "",
        "## Vì sao pilot R2.1 fail",
        "",
        "- R8 R2.1 `keep` nhầm khi chỉ có keyword `지속가능경영보고서` trên article rewrite / portal.",
        "- 10/15 pilot unit có news UI, byline, portal nav, hoặc archive listing.",
        "- LLM Distillation drop đúng 8 case `insufficient_substance` — input noisy, không phải prompt.",
        "",
        "### Phân loại 15 unit pilot R2.1",
        "",
        "| record_id | Distill | Vấn đề input | R2.2 pilot |",
        "|-----------|---------|--------------|------------|",
        "| `rec_2ac36b6aa8233480` | keep | news-mixed, trùng body với unit khác | **Loại** (text dup) |",
        "| `rec_2d0cf95b00a0fefc` | drop | news UI chrome | **Loại** |",
        "| `rec_6d11be8f9ba7006c` | drop | news UI + ESRS body | **Giữ** (conditional) |",
        "| `rec_80928c7327855bfa` | drop | portal nav | **Loại** |",
        "| `rec_80472635b427982e` | drop | URL chrome only | **Loại** |",
        "| `rec_86c98b945fc03e6d` | drop | news duplicate chrome | **Loại** |",
        "| `rec_adf521a49feec751` | drop | report intro / nav | **Giữ** (keep) |",
        "| `rec_abdc38fe1d1a8be1` | keep | news + Net Zero (trùng cluster) | **Loại** |",
        "| `rec_0f7c7247e048a21e` | drop | JSON metadata + news lead | **Giữ** (keep, noise thấp) |",
        "| `rec_770c772d010352ff` | drop | IR portal listing | **Loại** |",
        "| `rec_ce1fb6e4651850d3` | drop | news title repeat | **Loại** |",
        "| `rec_39fe9a810a0d6923` | keep | excerpt 8 material issues — **strong** | **Giữ** (conditional) |",
        "| `rec_cece4f8f062194a3` | drop | news chrome | **Loại** |",
        "| `rec_030916ba7f52fe4d` | drop | report archive listing | **Loại** |",
        "| `rec_41a160ead0ae1be6` | drop | duplicate Net Zero | **Giữ** (conditional, 1 slot) |",
        "",
        "**Strong candidates R2.1:** `rec_39fe9a810a0d6923`, `rec_2ac36b6aa8233480` (body), `rec_adf521a49feec751` (intro).",
        "",
        "## Rule siết thêm (R2.2)",
        "",
        "| Rule | Thay đổi |",
        "|------|----------|",
        "| **R6** | Drop portal category menu + noise cao (`noise>=9` hoặc byline+`noise>=6`); url/json chrome |",
        "| **R2** | Drop portal nav + archive list (`다운로드`, `국문 영문`, `보고서&자료실`) |",
        "| **R8** | Keep chỉ khi `substance_score >= 4` và `noise_ratio < 0.75`; drop `report_mention_only` |",
        "| **R10** | Conditional news mixed + `substance>=16`, `noise<=8` — pilot được nếu đủ substance |",
        "",
        "## Hansem eligible trước và sau R2.2",
        "",
        f"| Metric | R2.1 | R2.2 |",
        f"|--------|-----:|-----:|",
        f"| Hansem keep | {summary.get('hanssem_keep_r21', 'n/a')} | {summary.get('hanssem_keep_r22', 'n/a')} |",
        f"| Pilot candidate pool | — | {summary.get('pilot_candidate_pool', 0)} |",
        f"| Pilot selected | 15 (R2.1) | {summary.get('pilot_selected', 0)} |",
        "",
        "## Pilot selection strategy mới",
        "",
        "- Score: `selection_priority = substance*10 - noise*5` (+20 keep, +5 conditional).",
        "- `pilot_candidate=yes` khi keep sạch hoặc conditional có `substance >= 16`, `noise <= 8`.",
        "- Dedupe theo text fingerprint (không loại hết unit cùng fact family).",
        "- Bucket: ~9 primary, ~3 metric, ~2 governance.",
        f"- Supplement từ rejected (borderline): **{summary.get('pilot_supplement_count', 0)}** unit — `substance>=14`, `noise<=7`, không portal/archive.",
        "",
        "## So sánh pilot cũ vs mới",
        "",
        f"- Overlap record_id: **{summary.get('pilot_overlap_count', 0)}** `{summary.get('pilot_overlap_ids', [])}`",
        "",
        "### Pilot R2.1 (cũ)",
        "",
    ]
    for rid in summary.get("old_pilot_record_ids", []):
        lines.append(f"- `{rid}`")

    lines.extend(["", "### Pilot R2.2 (mới)", ""])
    for item in summary.get("pilot_selection", []):
        lines.append(
            f"- `{item['record_id']}` — {item['prefilter_decision']}, "
            f"sub={item['substance_score']}, noise={item['noise_score']}, "
            f"prio={item['selection_priority']}, cluster=`{item['duplicate_cluster_id']}`"
        )

    lines.extend(
        [
            "",
            "## Rủi ro còn lại",
            "",
            "- Một số unit conditional (TOC mixed) vẫn có thể vào pilot — cần Distillation strict.",
            "- Hansem pool nhỏ hơn R2.1 — có thể thiếu metric diversity.",
            "- Chưa chạy Distillation validation trên pilot mới trong task này.",
            "",
            "## Điều kiện sang Distillation pilot lần 2",
            "",
            "1. Review `pilot_hanssem_15_eligible_r2_2.jsonl` — ưu tiên unit `keep` + conditional có substance cao.",
            "2. Chạy `run_distill_pilot_hanssem_r2_1.py` (hoặc step 2 `--distill-r2-1`) với input pilot R2.2.",
            "3. Ngưỡng pass: **>= 8 keep usable** trước khi mở Silver QC.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Golden Set pre-filter R2.2")
    parser.add_argument("--input", default="data/golden_set/v2/step1_corpus_units/corpus_units.jsonl")
    parser.add_argument("--output-dir", default="data/golden_set/v2/step1_corpus_units")
    parser.add_argument(
        "--pilot-out",
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible_r2_2.jsonl",
    )
    parser.add_argument("--pilot-size", type=int, default=15)
    parser.add_argument("--report", default="reports/golden_set_prefilter_round2_2.md")
    parser.add_argument(
        "--r21-eligible",
        default="data/golden_set/v2/step1_corpus_units/corpus_units_eligible.jsonl",
    )
    parser.add_argument(
        "--old-pilot",
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible.jsonl",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    summary = run_prefilter_r22(
        input_path=root / args.input,
        output_dir=root / args.output_dir,
        pilot_path=root / args.pilot_out,
        pilot_size=args.pilot_size,
        r21_eligible_path=root / args.r21_eligible,
        old_pilot_path=root / args.old_pilot,
    )
    write_report_r22(summary, root / args.report)
    out_json = root / "reports/_prefilter_r2_2_summary.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(
        {
            "keep": summary["keep_count"],
            "drop": summary["drop_count"],
            "conditional": summary["conditional_count"],
            "hanssem_keep_r22": summary["hanssem_keep_r22"],
            "pilot_selected": summary["pilot_selected"],
            "pilot_pool": summary["pilot_candidate_pool"],
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
