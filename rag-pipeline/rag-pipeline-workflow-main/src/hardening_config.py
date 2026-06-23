"""Post-roadmap hardening test matrix configurations."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from extraction_v4 import DEFAULT_RETRIEVAL_MODE


@dataclass
class HardeningConfig:
    config_id: str
    label: str
    retrieval_mode: str
    enable_policy_boost: bool
    corpus_scope: str  # mixed | public_only
    strict_conflict: bool
    top_k: int = 4
    pool: int = 24
    verification_max_attempts: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


HARDENING_MATRIX: List[HardeningConfig] = [
    HardeningConfig(
        config_id="v6_current",
        label="V6 current (router + verify + policy_boost)",
        retrieval_mode=DEFAULT_RETRIEVAL_MODE,
        enable_policy_boost=True,
        corpus_scope="mixed",
        strict_conflict=False,
    ),
    HardeningConfig(
        config_id="v6_no_policy_boost",
        label="V6 no_policy_boost",
        retrieval_mode=DEFAULT_RETRIEVAL_MODE,
        enable_policy_boost=False,
        corpus_scope="mixed",
        strict_conflict=False,
    ),
    HardeningConfig(
        config_id="v6_public_only",
        label="V6 public_only_corpus (02+03 buckets)",
        retrieval_mode=DEFAULT_RETRIEVAL_MODE,
        enable_policy_boost=False,
        corpus_scope="public_only",
        strict_conflict=False,
    ),
    HardeningConfig(
        config_id="v6_mixed_strict",
        label="V6 mixed_corpus_strict_conflict",
        retrieval_mode=DEFAULT_RETRIEVAL_MODE,
        enable_policy_boost=False,
        corpus_scope="mixed",
        strict_conflict=True,
    ),
]

PUBLIC_SOURCE_MARKERS = ("02_esg_public_core", "03_esg_public_complex")


def corpus_scope_allows_source(source: str, scope: str) -> bool:
    s = source.lower().replace("\\", "/")
    if scope == "mixed":
        return True
    if scope == "public_only":
        return any(m in s for m in PUBLIC_SOURCE_MARKERS)
    return True
