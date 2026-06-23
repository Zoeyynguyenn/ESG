"""Deterministic guard before LLM generation (LangGraph / client downstream).

Uses retrieve reliability flags — does not change retrieval ranking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from evidence_api.schemas import EvidenceItem, RetrieveResponse

LlmGenerateFn = Callable[[str, str], str]

# Safe fields for LLM context (answerable items only).
_PROMPT_ITEM_FIELDS = (
    "text",
    "source",
    "record_id",
    "page",
    "section_path",
    "candidate_confidence",
    "metric_name",
    "value",
    "unit",
)

# Never pass these for non-answerable items; also stripped from answerable prompt dicts
# when building minimal context (score / legacy confidence mislead the model).
_BLOCKED_PROMPT_FIELDS = frozenset({"score", "confidence", "evidence_type"})


@dataclass
class GuardedAnswer:
    abstained: bool
    answer: str
    used_llm: bool
    prompt_item_count: int
    abstain_reason: str = ""
    reliability_flags: List[str] = field(default_factory=list)
    prompt_context: str = ""


def should_abstain(resp: RetrieveResponse) -> bool:
    """True when LLM must not produce a numeric answer from retrieved items."""
    if resp.abstain_recommended:
        return True
    if not resp.items:
        return True
    return not any(item.answerable_candidate for item in resp.items)


def abstain_reason(resp: RetrieveResponse) -> str:
    if resp.abstain_reason:
        return resp.abstain_reason
    if resp.abstain_recommended and resp.reliability_flags:
        return resp.reliability_flags[0]
    if not resp.items:
        return "no_candidates"
    return "no_answerable_evidence"


def abstain_message(query: str, company_display: str = "") -> str:
    """Korean template — deterministic, no LLM."""
    q = (query or "").strip()
    if company_display and company_display in q:
        subject = q
    elif q:
        subject = q.rstrip("?").rstrip("？")
    else:
        subject = "요청하신 지표"
    return f"{subject}에 대한 신뢰할 수 있는 수치 근거를 찾지 못했습니다."


def answerable_items(items: Sequence[EvidenceItem]) -> List[EvidenceItem]:
    return [it for it in items if it.answerable_candidate]


def item_for_prompt(item: EvidenceItem) -> Dict[str, Any]:
    """Serialize one answerable item for LLM context — no ranking noise fields."""
    raw = item.model_dump()
    out: Dict[str, Any] = {}
    for key in _PROMPT_ITEM_FIELDS:
        val = raw.get(key)
        if val is not None and val != "" and val != []:
            out[key] = val
    return out


def build_safe_context(items: Sequence[EvidenceItem]) -> str:
    """Context string from answerable items only."""
    usable = answerable_items(items)
    if not usable:
        return ""
    blocks: List[str] = []
    for i, item in enumerate(usable, 1):
        payload = item_for_prompt(item)
        lines = [f"[{i}]"]
        for key, val in payload.items():
            if key == "text":
                lines.append(str(val)[:1200])
            else:
                lines.append(f"{key}={val}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def resolve_answer(
    resp: RetrieveResponse,
    query: str,
    *,
    company_display: str = "",
    llm_generate: Optional[LlmGenerateFn] = None,
) -> GuardedAnswer:
    """Guard + optional LLM. Abstains deterministically before any LLM call."""
    flags = list(resp.reliability_flags)
    if should_abstain(resp):
        return GuardedAnswer(
            abstained=True,
            answer=abstain_message(query, company_display=company_display),
            used_llm=False,
            prompt_item_count=0,
            abstain_reason=abstain_reason(resp),
            reliability_flags=flags,
        )

    prompt_items = answerable_items(resp.items)
    context = build_safe_context(prompt_items)
    if not context.strip():
        return GuardedAnswer(
            abstained=True,
            answer=abstain_message(query, company_display=company_display),
            used_llm=False,
            prompt_item_count=0,
            abstain_reason="no_answerable_evidence",
            reliability_flags=flags,
        )

    if llm_generate is None:
        return GuardedAnswer(
            abstained=False,
            answer="",
            used_llm=False,
            prompt_item_count=len(prompt_items),
            reliability_flags=flags,
            prompt_context=context,
        )

    answer = llm_generate(context, query)
    return GuardedAnswer(
        abstained=False,
        answer=answer,
        used_llm=True,
        prompt_item_count=len(prompt_items),
        reliability_flags=flags,
        prompt_context=context,
    )
