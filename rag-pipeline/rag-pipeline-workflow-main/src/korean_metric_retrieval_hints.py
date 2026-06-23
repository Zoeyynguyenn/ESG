"""Deterministic KO headcount metric hints: BM25 expansion + hybrid ranking boost."""

from __future__ import annotations

import re
from typing import Any, List

# Block headcount path for governance / finance / executive-count style queries.
_NON_HEADCOUNT_GUARD = re.compile(
    r"사외이사|외부이사|사내이사|이사회|위원회|기부금|기부|"
    r"탄소|온실|배출|매출|영업이익|임원진|"
    r"이사\s*수|사외\s*이사|내부이사",
)

# Strong headcount intent — workforce size / employee count.
_HEADCOUNT_STRONG = re.compile(
    r"인원|직원|구성원|임직원|근로자|종업원|"
    r"사람\s*수|총\s*직원|총직원|전체\s*인원|고용\s*인원|"
    r"총\s*인력|전체\s*인력|고용\s*규모|"
    r"인력\s*규모|임직원\s*규모",
)

# Soft headcount — 규모 paired with a workforce noun (not bare 규모).
_HEADCOUNT_SOFT = re.compile(
    r"(?:인력|고용|사람|인원|종업원|임직원|직원|근로자|구성원)\s*규모",
)

# Canonical synonyms appended to BM25 query when absent (token overlap with evidence).
_HEADCOUNT_SYNONYMS: tuple[str, ...] = (
    "인원",
    "직원",
    "구성원",
    "임직원",
    "근로자",
    "총직원",
    "전체인원",
    "사람수",
    "직원수",
    "임직원수",
    "종업원",
    "인력규모",
    "고용인원",
)

# Evidence patterns near a headcount number.
_HEADCOUNT_NEAR_NUMBER = re.compile(
    r"총\s*직원|총직원|임직원\s*수|직원\s*수|구성원\s*수|인원|근로자|사람\s*수|전체\s*인원|종업원",
)
_COUNT_MYEONG = re.compile(r"(\d{2,5})\s*명")

# Light penalty for SME table noise (e.g. mss.go.kr decimal grids) — not corpus filtering.
_TABLE_NOISE = re.compile(r"0\.\d{2}")


def is_non_headcount_metric_query(question: str) -> bool:
    return bool(_NON_HEADCOUNT_GUARD.search(question or ""))


def is_headcount_metric_query(question: str) -> bool:
    q = question or ""
    if not q.strip():
        return False
    if is_non_headcount_metric_query(q):
        return False
    if _HEADCOUNT_STRONG.search(q):
        return True
    if _HEADCOUNT_SOFT.search(q):
        return True
    return False


def _normalized_compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def expand_headcount_synonyms(question: str) -> str:
    """Append missing headcount synonyms for BM25 recall (deterministic, conditional)."""
    if not is_headcount_metric_query(question):
        return question
    compact = _normalized_compact(question)
    extras: List[str] = []
    for syn in _HEADCOUNT_SYNONYMS:
        if syn not in compact:
            extras.append(syn)
    if not extras:
        return question
    return f"{question} {' '.join(extras)}"


def prepare_bm25_query(question: str, *, lane_expand: bool = False) -> str:
    """BM25 query after optional lane expand + headcount synonym expansion."""
    q = question
    if lane_expand:
        from export_json_retrieval_hints import expand_query

        q = expand_query(q)
    return expand_headcount_synonyms(q)


def _number_headcount_bonus(text: str, match: re.Match[str], prefer_total: bool) -> float:
    num = int(match.group(1))
    if num < 80:
        return -0.08
    start = max(0, match.start() - 48)
    window = text[start : match.end() + 8]
    bonus = 0.06
    if _HEADCOUNT_NEAR_NUMBER.search(window):
        bonus += 0.10
    if "총직원" in window or "총 직원" in window or "총직원" in _normalized_compact(window):
        bonus += 0.14 if prefer_total else 0.08
    elif "직원 수" in window or "직원수" in _normalized_compact(window):
        bonus += 0.06
    elif "임직원" in window:
        bonus += 0.05
    small_counts = len(re.findall(r"\d{1,2}\s*명", window[: match.start() - start + 1]))
    if small_counts >= 2:
        bonus -= 0.12
    return bonus


def headcount_chunk_bonus(text: str, *, prefer_total: bool) -> float:
    if not text:
        return 0.0
    bonus = 0.0
    for m in _COUNT_MYEONG.finditer(text):
        bonus += _number_headcount_bonus(text, m, prefer_total)
    bonus = min(bonus, 0.45)
    decimals = len(_TABLE_NOISE.findall(text))
    if decimals >= 6:
        bonus -= min(0.20, 0.03 * decimals)
    return bonus


def apply_headcount_metric_boost(question: str, hits: List[Any]) -> List[Any]:
    """Pre-rerank boost for KO headcount metric queries (no hardcoded answers)."""
    if not hits or not is_headcount_metric_query(question):
        return hits
    prefer_total = bool(re.search(r"총|전체", question or ""))
    for h in hits:
        bonus = headcount_chunk_bonus(h.text or "", prefer_total=prefer_total)
        if bonus:
            h.score = float(h.score) + bonus
            h.score_breakdown["headcount_boost"] = round(bonus, 4)
    hits.sort(key=lambda x: x.score, reverse=True)
    return hits


def headcount_rerank_blend_alpha(default_alpha: float) -> float:
    """Slightly trust hybrid pre-score more for headcount (competing numeric evidence)."""
    return max(0.35, min(default_alpha, default_alpha - 0.12))
