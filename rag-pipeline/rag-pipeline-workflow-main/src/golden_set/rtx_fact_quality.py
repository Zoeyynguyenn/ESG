"""Shared fact-target quality checks and canonical fact catalog for RTX v2.1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from golden_set.build_reference_seed_workbook import METRIC_HINT_RE, NUMBER_RE, YEAR_RE

RESIDUE_PATTERNS = [
    re.compile(r"\bs Workforce\b", re.I),
    re.compile(r"What s ", re.I),
    re.compile(r"GHGemissions", re.I),
    re.compile(r"\|", re.I),
    re.compile(r"^What Certain\b"),
    re.compile(r"^What Direct economic value generate\b"),
    re.compile(r"^What Reductions from\b"),
]

UNNATURAL_PATTERNS = [
    re.compile(r"^What [A-Z][a-z]+(?:s|ing) from the \d{4}"),
    re.compile(r"^What Certain \d{4}"),
    re.compile(r"^What Direct economic value generate\b"),
    re.compile(r"^What s "),
    re.compile(r"does RTX report\?$"),  # ok ending
]

OVERLONG_FACT_LEN = 52
OVERLONG_QUESTION_LEN = 95


@dataclass
class CanonicalFact:
    fact_id: str
    match_pat: str
    fact_target: str
    fact_target_type: str
    align_tokens: Tuple[str, ...]
    question_metric: str
    question_trend: Optional[str] = None
    mismatch_blockers: Tuple[Tuple[str, str], ...] = ()  # (q_term, d_must_have)


CANONICAL_FACTS: List[CanonicalFact] = [
    CanonicalFact(
        "energy_intensity",
        r"energy intensity",
        "energy intensity (GJ per $M revenue)",
        "metric_specific",
        ("energy", "intensity", "gj"),
        "What energy intensity (GJ per $M revenue) does RTX report?",
        "How did RTX's energy intensity (GJ per $M revenue) change across reported years?",
    ),
    CanonicalFact(
        "energy_reduction_2019",
        r"reduction in energy consumption since 2019|energy consumption since 2019",
        "energy consumption reduction since 2019 baseline",
        "metric_specific",
        ("energy", "2019", "reduction", "consumption"),
        "What percentage reduction in energy consumption since the 2019 baseline does RTX report?",
        "How did RTX's energy consumption reduction since the 2019 baseline change across reported years?",
    ),
    CanonicalFact(
        "ergonomic_risk",
        r"ergonomic risk",
        "ergonomic workplace risk levels",
        "metric_specific",
        ("ergonomic", "risk"),
        "What ergonomic risk levels or reductions does RTX report?",
        "How have RTX's ergonomic risk metrics changed since the baseline year?",
        mismatch_blockers=(("high and elevated", "high"), ("medium ergonomic", "medium")),
    ),
    CanonicalFact(
        "scope12_ghg",
        r"scope\s*1(?:\s*(?:and|&)\s*2)?|scope\s*1[^.]{0,30}scope\s*2",
        "Scope 1 and Scope 2 GHG emissions",
        "metric_specific",
        ("scope", "emission", "ghg"),
        "What Scope 1 and Scope 2 GHG emissions does RTX report?",
        "How did RTX's Scope 1 and Scope 2 GHG emissions change across reported years?",
    ),
    CanonicalFact(
        "scope1_ghg",
        r"\bscope\s*1\b",
        "Scope 1 GHG emissions",
        "metric_specific",
        ("scope 1", "emission"),
        "What Scope 1 GHG emissions does RTX report?",
    ),
    CanonicalFact(
        "scope2_market",
        r"market-based scope\s*2",
        "market-based Scope 2 emissions",
        "metric_specific",
        ("scope 2", "market-based"),
        "What market-based Scope 2 GHG emissions does RTX report?",
    ),
    CanonicalFact(
        "scope3",
        r"\bscope\s*3\b",
        "Scope 3 GHG emissions",
        "metric_specific",
        ("scope 3", "emission"),
        "What Scope 3 GHG emissions does RTX report?",
    ),
    CanonicalFact(
        "renewable_energy",
        r"renewable (?:electricity|energy)",
        "renewable electricity use",
        "metric_specific",
        ("renewable", "electricity", "energy"),
        "What renewable electricity or energy use does RTX report?",
    ),
    CanonicalFact(
        "water",
        r"water (?:withdrawal|consumption|stress)",
        "water withdrawal or consumption",
        "metric_specific",
        ("water",),
        "What water withdrawal or consumption figures does RTX report?",
    ),
    CanonicalFact(
        "co2e_savings",
        r"co2e savings|metric tonnes co2e",
        "annual CO2e savings from initiatives",
        "metric_specific",
        ("co2e", "savings"),
        "What annual CO2e savings from energy or emissions initiatives does RTX report?",
    ),
    CanonicalFact(
        "gtf_efficiency",
        r"gtf engine|geared turbo fan",
        "GTF engine fuel efficiency and emissions",
        "metric_specific",
        ("gtf", "fuel", "emission"),
        "What fuel efficiency or CO2 emissions benefits does RTX report for the GTF engine?",
    ),
    CanonicalFact(
        "rd_investment",
        r"r&d|r&d investment|research and development",
        "R&D investment for sustainability technologies",
        "metric_specific",
        ("r&d", "research", "development"),
        "What R&D investment does RTX report for sustainability-related technologies?",
    ),
    CanonicalFact(
        "diversity",
        r"diversity and inclusion|underrepresented|female.*representation",
        "workforce diversity and inclusion",
        "metric_specific",
        ("diversity", "inclusion"),
        "What workforce diversity and inclusion metrics does RTX report?",
    ),
    CanonicalFact(
        "audit_committee",
        r"audit committee",
        "Audit Committee ESG oversight",
        "governance_specific",
        ("audit", "committee"),
        "What ESG oversight role does RTX's Audit Committee have?",
    ),
    CanonicalFact(
        "board_governance",
        r"board of directors",
        "Board of Directors governance",
        "governance_specific",
        ("board", "director"),
        "What Board of Directors governance practices does RTX disclose for ESG?",
    ),
    CanonicalFact(
        "code_ethics",
        r"code of (?:ethics|conduct)",
        "Code of Ethics and Conduct",
        "governance_specific",
        ("ethics", "conduct", "code"),
        "What does RTX disclose about its Code of Ethics or Conduct?",
    ),
    CanonicalFact(
        "data_security",
        r"data (?:privacy|security|protection)|cybersecurity",
        "data privacy and cybersecurity",
        "governance_specific",
        ("data", "privacy", "security", "cyber"),
        "What data privacy and cybersecurity practices does RTX disclose?",
    ),
    CanonicalFact(
        "stakeholder_engagement",
        r"stakeholder (?:engagement|group)",
        "stakeholder engagement",
        "stakeholder_materiality",
        ("stakeholder", "engagement"),
        "How does RTX engage stakeholders on ESG topics?",
    ),
    CanonicalFact(
        "materiality",
        r"material(?:ity)?(?:\s+topic|\s+issue)|double materiality",
        "material ESG topics",
        "stakeholder_materiality",
        ("materiality", "material"),
        "What material ESG topics does RTX identify?",
    ),
    CanonicalFact(
        "cdp",
        r"\bcdp\b",
        "CDP climate disclosure",
        "framework_report",
        ("cdp",),
        "What does RTX disclose in its CDP climate questionnaire responses?",
    ),
    CanonicalFact(
        "tcfd",
        r"\btcfd\b",
        "TCFD-aligned climate disclosure",
        "framework_report",
        ("tcfd",),
        "What TCFD-aligned climate disclosures does RTX provide?",
    ),
    CanonicalFact(
        "deferred_prosecution",
        r"deferred prosecution|fcpa|foreign corrupt practices",
        "FCPA / deferred prosecution compliance matter",
        "governance_specific",
        ("deferred", "prosecution", "fcpa", "bribery"),
        "What compliance resolution related to government contracts has RTX disclosed?",
    ),
    CanonicalFact(
        "ecovadis",
        r"ecovadis",
        "supplier EcoVadis assessments",
        "metric_specific",
        ("ecovadis", "supplier"),
        "How does RTX use EcoVadis assessments for suppliers?",
    ),
    CanonicalFact(
        "net_zero",
        r"net zero",
        "net zero climate commitment",
        "metric_specific",
        ("net zero",),
        "What net zero or climate neutrality commitments does RTX disclose?",
    ),
    CanonicalFact(
        "ghg_intensity",
        r"ghg emissions?/revenue|intensity decreased|scope 1&2 emissions/revenue",
        "GHG emissions intensity (per revenue)",
        "metric_specific",
        ("intensity", "emission", "revenue"),
        "What GHG emissions intensity (emissions per revenue) does RTX report?",
        "How did RTX's GHG emissions intensity change year over year?",
    ),
]


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def match_canonical_fact(sentence: str) -> Optional[CanonicalFact]:
    lower = sentence.lower()
    for cf in CANONICAL_FACTS:
        if re.search(cf.match_pat, lower, re.I):
            return cf
    return None


def _token_overlap(a: str, b: str) -> int:
    ta = set(re.findall(r"[a-z]{4,}", a.lower()))
    tb = set(re.findall(r"[a-z]{4,}", b.lower()))
    return len(ta & tb)


def audit_candidate_row(row: Dict) -> List[str]:
    """Return list of error codes (empty = usable)."""
    errors: List[str] = []
    q = row.get("question_draft") or ""
    d = _norm_ws(row.get("acceptable_disclosure") or row.get("source_excerpt") or "")
    ft = row.get("fact_target") or ""

    for pat in RESIDUE_PATTERNS:
        if pat.search(q) or pat.search(ft):
            errors.append("residue_led_question")
            break

    if len(ft) > OVERLONG_FACT_LEN or len(q) > OVERLONG_QUESTION_LEN:
        errors.append("overlong_fact_phrase")

    if any(pat.search(q) for pat in UNNATURAL_PATTERNS):
        errors.append("unnatural_question_wording")
    elif re.search(r"^What [A-Z][a-z]{4,} (?:from|in \d{4})", q) and "does RTX report" in q:
        errors.append("unnatural_question_wording")

    q_lower = q.lower()
    d_lower = d.lower()
    if "high and elevated ergonomic" in q_lower and "medium ergonomic" in d_lower and "high" not in d_lower:
        errors.append("fact_mismatch")
    if "scope 3" in q_lower and "scope 3" not in d_lower and "scope 3" not in ft.lower():
        errors.append("fact_mismatch")
    if "scope 3 emission" in q_lower and "reporting period" in d_lower and "emission" not in d_lower:
        errors.append("fact_mismatch")
    if "direct economic value generate" in q_lower and "direct economic value generated" not in d_lower:
        errors.append("fact_mismatch")

    overlap = _token_overlap(q, d)
    align = row.get("fact_target") or ""
    if overlap < 2 and _token_overlap(align, d) < 2:
        if not NUMBER_RE.search(q) or not NUMBER_RE.search(d):
            errors.append("fact_mismatch")

    if ft and ft[0].islower():
        errors.append("residue_led_question")

    return list(dict.fromkeys(errors))


DOC_KIND_LABELS = {
    "10k": "Form 10-K",
    "proxy_statement": "proxy statement",
    "appendix": "ESG appendix",
    "questionnaire": "CDP questionnaire",
    "data_table": "ESG data tables",
    "policy_page": "policy page",
    "press_release": "press release",
}


def _valid_years(sentence: str) -> List[str]:
    return sorted({y for y in YEAR_RE.findall(sentence) if 1995 <= int(y) <= 2035})


def build_natural_question(
    cf: CanonicalFact,
    qtype: str,
    sentence: str,
    *,
    document_kind: str = "",
    disclosure: str = "",
) -> str:
    years = _valid_years(sentence)
    doc = DOC_KIND_LABELS.get(document_kind, "disclosure")

    if qtype == "trend" and cf.question_trend and len(years) >= 2:
        return cf.question_trend.replace("across reported years", f"from {years[0]} to {years[-1]}")

    q = cf.question_metric.rstrip("?")
    suffix_parts: List[str] = []
    if years:
        suffix_parts.append(f"for {years[-1]}")
    elif document_kind:
        suffix_parts.append(f"in its {doc}")

    nums = [n for n in NUMBER_RE.findall(disclosure or sentence) if len(n) >= 1][:1]
    if qtype == "quantitative" and nums and "%" in (disclosure or sentence):
        suffix_parts.append(f"(disclosed figure includes {nums[0]}%)")

    if suffix_parts:
        return f"{q} {' '.join(suffix_parts)}?"
    return f"{q}?"


def passes_quality_gates(question: str, fact_target: str, disclosure: str, cf: CanonicalFact) -> Tuple[bool, str]:
    row = {
        "question_draft": question,
        "fact_target": fact_target,
        "acceptable_disclosure": disclosure,
    }
    errors = audit_candidate_row(row)
    if errors:
        return False, errors[0]

    d_lower = disclosure.lower()
    for q_term, d_must in cf.mismatch_blockers:
        if q_term in question.lower() and d_must not in d_lower:
            return False, "fact_mismatch"

    hits = sum(1 for t in cf.align_tokens if t in d_lower)
    if hits < 1:
        return False, "fact_mismatch"

    if not question.endswith("?"):
        return False, "unnatural_question_wording"
    if "RTX" not in question:
        return False, "unnatural_question_wording"

    return True, "usable"
