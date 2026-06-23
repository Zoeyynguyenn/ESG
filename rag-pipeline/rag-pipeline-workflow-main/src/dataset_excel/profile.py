"""Question profile dataclass for dataset-excel routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuestionProfile:
    year: int | None
    preferred_doc_patterns: list[str]
    preferred_schemas: list[str]
    penalize_doc_patterns: list[str]
    account_keywords: list[str]
    wants_min_wage: bool
    family: str
