"""Abstain / reliability gate for retrieve API (post-ranking, pre-response)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Sequence, Tuple

from evidence_api.schemas import ConfidenceLevel, EvidenceItem

MetricKind = Literal["percentage", "count"]

# Specific metric topics override generic headcount triggers (e.g. 육아휴직 + 인원).
_SPECIFIC_METRIC = re.compile(
    r"육아휴직|장애인|복귀율|고용률|여성\s*비율|남성\s*비율|여성기업|"
    r"탄소|온실|매출|영업이익|사외이사|임원진|이사회",
)

# Gender-ratio (subset of percentage intent).
_GENDER_RATIO_QUERY = re.compile(
    r"(남성|여성).{0,20}(비율|구성|비중|성비)"
    r"|(남성|여성).{0,12}퍼센트"
    r"|남녀\s*비율"
    r"|성비",
)

# Percentage / rate metric queries (excludes bare headcount).
_PERCENTAGE_QUERY = re.compile(
    r"[%％]"
    r"|(?:비율|고용률|비중|퍼센트|복귀율|달성률|증가율|점유율|비중)"
    r"|(?:남성|여성).{0,12}(?:비율|구성|비중)",
)

# Count metric queries — specific headcount phrasing excluded via headcount bypass.
_COUNT_QUERY = re.compile(
    r"몇\s*명"
    r"|(?:대상자|인원|인원수|사용\s*인원|복귀\s*인원).{0,12}수"
    r"|(?:수|인원).{0,8}(?:몇|얼마|은\s*몇|는\s*몇)"
    r"|몇\s*수",
)

# Topic extraction from query (metric nouns, not generic wrappers).
_TOPIC_NOISE = re.compile(
    r"해당\s*기업|해당\s*회사|이\s*회사|이\s*기업|"
    r"몇\s*[%％]?인가요\?|은\s*몇|는\s*몇|몇\s*명|몇\s*퍼센트|"
    r"얼마|입니까|인가요|알려|해\s*주|무신사|레이시온|한샘",
)

_PERCENT_ANCHOR = re.compile(r"\d+[\.,]?\d*\s*[%％]")
_COUNT_ANCHOR = re.compile(r"\d+[\.,]?\d*\s*(?:명|수|대|건|명\b)")
_GENDER_RATIO_ANCHOR = re.compile(
    r"(?:남성|여성|남녀).{0,48}\d+[\.,]?\d*\s*[%％]"
    r"|\d+[\.,]?\d*\s*[%％].{0,48}(?:남성|여성|남녀|구성원|임직원|직원)",
)

_DOMAIN_MISMATCH = re.compile(
    r"여성기업|여성\s*패션|거래액|댓글\s*입력|퀴즈\s*문항|0\s*/\s*300\s*등록|"
    r"IBK기업은행|IBK은행|성별\s*:\s*공용|"
    r"우리나라\s*장애인|전체\s*인구.{0,40}(?:장애인|고용률)|"
    r"장애인기업\s*현황|장애인기업제품|국가\s*통계",
)

_RELIABILITY_MESSAGES = {
    "metric_anchor_missing": (
        "Top candidates lack numeric anchors matching the requested metric."
    ),
    "domain_mismatch": (
        "Top candidates appear to be policy, national statistics, or off-domain content."
    ),
    "no_answerable_evidence": (
        "Top candidates are high lexical matches but do not contain answerable evidence "
        "for the requested company metric."
    ),
    "no_candidates": "No retrieval candidates were returned.",
    "entity_mismatch": (
        "Top candidates mention related topics but not the requested company entity."
    ),
}

_HEADCOUNT_ANSWERABLE_BONUS = 0.08


@dataclass
class CandidateAssessment:
    answerable_candidate: bool = False
    candidate_confidence: ConfidenceLevel = "low"
    candidate_flags: List[str] = field(default_factory=list)


@dataclass
class AbstainDecision:
    abstain_recommended: bool = False
    no_relevant_evidence: bool = False
    retrieval_confidence: ConfidenceLevel = "high"
    abstain_reason: Optional[str] = None
    reliability_reason: Optional[str] = None
    reliability_flags: List[str] = field(default_factory=list)
    item_assessments: List[CandidateAssessment] = field(default_factory=list)


@dataclass
class MetricIntent:
    kind: MetricKind
    topic_terms: List[str]
    gender: Optional[str] = None  # percentage gender-ratio subset


def is_gender_ratio_query(query: str) -> bool:
    return bool(_GENDER_RATIO_QUERY.search(query or ""))


def _gender_from_query(query: str) -> Optional[str]:
    if "남성" in query and "여성" not in query:
        return "남성"
    if "여성" in query and "남성" not in query:
        return "여성"
    return None


def _extract_topic_terms(query: str) -> List[str]:
    q = _TOPIC_NOISE.sub(" ", query or "")
    q = re.sub(r"[%％]", " ", q)
    terms: List[str] = []
    for m in re.finditer(r"[가-힣]{2,}", q):
        tok = m.group(0)
        if tok in ("비율", "고용률", "비중", "대상자", "인원", "복귀율"):
            continue
        if tok not in terms:
            terms.append(tok)
    for compound in ("장애인", "육아휴직", "남성", "여성", "복귀", "휴직"):
        if compound in (query or "") and compound not in terms:
            terms.insert(0, compound)
    for marker in ("고용률", "육아휴직", "장애인", "복귀율", "남성", "여성"):
        if marker in (query or "") and marker not in terms:
            terms.append(marker)
    return terms[:6]


def parse_metric_intent(query: str) -> Optional[MetricIntent]:
    """Quantitative metric intent; None if not gated (includes headcount bypass)."""
    from korean_metric_retrieval_hints import is_headcount_metric_query

    q = query or ""
    if not q.strip():
        return None

    if is_gender_ratio_query(q):
        return MetricIntent(
            kind="percentage",
            topic_terms=_extract_topic_terms(q),
            gender=_gender_from_query(q),
        )

    has_specific = bool(_SPECIFIC_METRIC.search(q))
    if not has_specific and is_headcount_metric_query(q):
        return None

    if _PERCENTAGE_QUERY.search(q):
        return MetricIntent(kind="percentage", topic_terms=_extract_topic_terms(q))

    if _COUNT_QUERY.search(q):
        return MetricIntent(kind="count", topic_terms=_extract_topic_terms(q))

    return None


def metric_anchor_passes(text: str, intent: MetricIntent) -> bool:
    """Chunk has numeric anchor matching metric kind + topic terms."""
    t = text or ""
    if intent.kind == "percentage":
        if intent.gender:
            if not _GENDER_RATIO_ANCHOR.search(t):
                return False
            if intent.gender not in t:
                return False
        elif not _PERCENT_ANCHOR.search(t):
            return False
    else:
        if not _COUNT_ANCHOR.search(t):
            return False

    if not intent.topic_terms:
        return True
    return any(term in t for term in intent.topic_terms)


def domain_mismatch(text: str, source: str, company_display: str) -> bool:
    body = _text_body_for_entity_check(text)
    t = body
    src = (source or "").lower()
    if "mss.go.kr" in src or "mss.go.kr" in (text or ""):
        if company_display and company_display not in body:
            return True
    if _DOMAIN_MISMATCH.search(t):
        return True
    if re.search(r"여성비율\s*\(\d", t) and company_display and company_display not in t:
        return True
    return False


def _text_body_for_entity_check(text: str) -> str:
    """Strip export-json metadata lines so company: slug in header does not fake entity match."""
    lines: List[str] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(
            ("record_id:", "doc_id:", "company:", "year:", "source:", "source_path:")
        ):
            continue
        lines.append(line)
    return "\n".join(lines)


def entity_mismatch(text: str, company_display: str, intent: MetricIntent) -> bool:
    """Topic overlap without company entity — likely wrong-company or generic stat."""
    body = _text_body_for_entity_check(text)
    if not company_display or company_display in body:
        return False
    if not intent.topic_terms:
        return False
    t = text or ""
    topic_hit = any(term in t for term in intent.topic_terms)
    anchor_hit = (
        _PERCENT_ANCHOR.search(t)
        if intent.kind == "percentage"
        else _COUNT_ANCHOR.search(t)
    )
    return topic_hit and bool(anchor_hit)


def chunk_is_answerable(
    text: str, source: str, company_display: str, intent: MetricIntent
) -> bool:
    body = _text_body_for_entity_check(text)
    if not metric_anchor_passes(text, intent):
        return False
    if domain_mismatch(text, source, company_display):
        return False
    if entity_mismatch(text, company_display, intent):
        return False
    if intent.gender and company_display and company_display not in body:
        return False
    return True


def _national_stat_flag(text: str, source: str) -> bool:
    src = (source or "").lower()
    return "mss.go.kr" in src or "mss.go.kr" in (text or "")


def _headcount_answerable(text: str, source: str, company_display: str, query: str) -> Tuple[bool, List[str]]:
    from korean_metric_retrieval_hints import headcount_chunk_bonus, is_headcount_metric_query

    if not is_headcount_metric_query(query):
        return True, []
    flags: List[str] = []
    prefer_total = bool(re.search(r"총|전체", query or ""))
    bonus = headcount_chunk_bonus(text or "", prefer_total=prefer_total)
    if domain_mismatch(text, source, company_display):
        flags.append("domain_mismatch")
    if bonus < _HEADCOUNT_ANSWERABLE_BONUS:
        flags.append("missing_metric_anchor")
        flags.append("headcount_anchor_weak")
    answerable = bonus >= _HEADCOUNT_ANSWERABLE_BONUS and "domain_mismatch" not in flags
    return answerable, flags


def _candidate_confidence(answerable: bool, flags: Sequence[str]) -> ConfidenceLevel:
    if answerable:
        return "high" if not flags else "medium"
    if any(f in flags for f in ("domain_mismatch", "entity_mismatch", "national_stat_not_company_metric")):
        return "low"
    if "missing_metric_anchor" in flags or "metric_anchor_missing" in flags:
        return "low"
    return "low"


def assess_candidate(
    text: str,
    source: str,
    company_display: str,
    *,
    intent: Optional[MetricIntent] = None,
    query: str = "",
) -> CandidateAssessment:
    """Per-item trust annotation — independent of retrieval score."""
    flags: List[str] = []

    if intent is not None:
        if not metric_anchor_passes(text, intent):
            flags.append("missing_metric_anchor")
        if domain_mismatch(text, source, company_display):
            flags.append("domain_mismatch")
            if _national_stat_flag(text, source):
                flags.append("national_stat_not_company_metric")
        if entity_mismatch(text, company_display, intent):
            flags.append("entity_mismatch")
        answerable = chunk_is_answerable(text, source, company_display, intent)
    elif query:
        answerable, flags = _headcount_answerable(text, source, company_display, query)
    else:
        answerable = True
        flags = []

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_flags = [f for f in flags if not (f in seen or seen.add(f))]

    return CandidateAssessment(
        answerable_candidate=answerable,
        candidate_confidence=_candidate_confidence(answerable, unique_flags),
        candidate_flags=unique_flags,
    )


def _reliability_message(primary_flag: str) -> str:
    return _RELIABILITY_MESSAGES.get(primary_flag, _RELIABILITY_MESSAGES["no_answerable_evidence"])


def evaluate_retrieval_reliability(
    query: str,
    company_display: str,
    items: Sequence[EvidenceItem],
    *,
    top_k_check: int = 3,
) -> AbstainDecision:
    """Response-level abstain decision + per-item trust annotations."""
    intent = parse_metric_intent(query)
    assessments = [
        assess_candidate(
            it.text or "",
            it.source or "",
            company_display,
            intent=intent,
            query=query,
        )
        for it in items
    ]

    if intent is None:
        from korean_metric_retrieval_hints import is_headcount_metric_query

        if is_headcount_metric_query(query):
            pool = assessments[:top_k_check]
            has_answerable = any(a.answerable_candidate for a in pool)
            top = pool[0] if pool else None
            if top and top.answerable_candidate:
                conf: ConfidenceLevel = top.candidate_confidence
            elif has_answerable:
                conf = "medium"
            else:
                # Keep items + no abstain for headcount; confidence reflects weak anchors only.
                conf = "medium"
            return AbstainDecision(
                retrieval_confidence=conf,
                item_assessments=assessments,
            )
        return AbstainDecision(item_assessments=assessments)

    pool = list(items[:top_k_check])
    pool_assessments = assessments[:top_k_check]

    if not pool:
        flags = ["no_candidates"]
        return AbstainDecision(
            abstain_recommended=True,
            no_relevant_evidence=True,
            retrieval_confidence="low",
            abstain_reason="no_candidates",
            reliability_reason=_reliability_message("no_candidates"),
            reliability_flags=flags,
            item_assessments=assessments,
        )

    reliability_flags: List[str] = []
    has_anchor = any(metric_anchor_passes(it.text or "", intent) for it in pool)
    has_answerable = any(a.answerable_candidate for a in pool_assessments)
    top1 = pool[0]
    top1_ann = pool_assessments[0]
    top1_mismatch = domain_mismatch(
        top1.text or "", top1.source or "", company_display
    )

    if not has_anchor:
        reliability_flags.append("metric_anchor_missing")
    if any(domain_mismatch(it.text or "", it.source or "", company_display) for it in pool):
        reliability_flags.append("domain_mismatch")
    if any(entity_mismatch(it.text or "", company_display, intent) for it in pool):
        reliability_flags.append("entity_mismatch")
    if not has_answerable:
        reliability_flags.append("no_answerable_evidence")

    if has_answerable:
        conf = "high" if top1_ann.answerable_candidate and top1_ann.candidate_confidence == "high" else "medium"
        return AbstainDecision(
            retrieval_confidence=conf,
            item_assessments=assessments,
        )

    reason = "no_answerable_evidence"
    if not has_anchor:
        reason = "metric_anchor_missing"
    elif top1_mismatch or "domain_mismatch" in reliability_flags:
        reason = "domain_mismatch"
    elif "entity_mismatch" in reliability_flags:
        reason = "entity_mismatch"

    if reason not in reliability_flags:
        reliability_flags.insert(0, reason)

    return AbstainDecision(
        abstain_recommended=True,
        no_relevant_evidence=True,
        retrieval_confidence="low",
        abstain_reason=reason,
        reliability_reason=_reliability_message(reason),
        reliability_flags=reliability_flags,
        item_assessments=assessments,
    )


def evaluate_abstain(
    query: str,
    company_display: str,
    items: Sequence[EvidenceItem],
    *,
    top_k_check: int = 3,
) -> AbstainDecision:
    """Backward-compatible wrapper (response fields only)."""
    decision = evaluate_retrieval_reliability(
        query, company_display, items, top_k_check=top_k_check
    )
    return AbstainDecision(
        abstain_recommended=decision.abstain_recommended,
        no_relevant_evidence=decision.no_relevant_evidence,
        retrieval_confidence=decision.retrieval_confidence,
        abstain_reason=decision.abstain_reason,
        reliability_reason=decision.reliability_reason,
        reliability_flags=decision.reliability_flags,
        item_assessments=decision.item_assessments,
    )
