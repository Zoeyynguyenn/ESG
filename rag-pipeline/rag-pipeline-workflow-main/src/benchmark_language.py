"""Language controls for benchmark/eval runtime."""

from __future__ import annotations

import os
from typing import Tuple


LANG_KO = "ko"
LANG_VI = "vi"

_INSUFFICIENT_BY_LANG = {
    LANG_KO: "컨텍스트에 답할 정보가 부족합니다.",
    LANG_VI: "Khong du du lieu trong context.",
}

_PHRASES_BY_LANG = {
    LANG_KO: (
        "컨텍스트에 답할 정보가 부족합니다",
        "컨텍스트에 정보가 부족합니다",
        "해당 정보를 찾을 수 없습니다",
        "주어진 문맥에서 확인할 수 없습니다",
    ),
    LANG_VI: (
        "khong du du lieu trong context",
        "khong du thong tin trong context",
        "khong du du lieu",
        "không đủ dữ liệu trong context",
        "không đủ thông tin",
    ),
}


def benchmark_language() -> str:
    lang = (os.getenv("RAG_BENCHMARK_LANGUAGE", LANG_KO) or LANG_KO).strip().lower()
    if lang not in (LANG_KO, LANG_VI):
        return LANG_KO
    return lang


def insufficient_answer(lang: str | None = None) -> str:
    use_lang = lang or benchmark_language()
    return _INSUFFICIENT_BY_LANG.get(use_lang, _INSUFFICIENT_BY_LANG[LANG_KO])


def insufficient_phrases(lang: str | None = None) -> Tuple[str, ...]:
    use_lang = lang or benchmark_language()
    ordered = list(_PHRASES_BY_LANG.get(use_lang, ()))
    for group in _PHRASES_BY_LANG.values():
        for phrase in group:
            if phrase not in ordered:
                ordered.append(phrase)
    return tuple(ordered)


def answer_language_label(lang: str | None = None) -> str:
    use_lang = lang or benchmark_language()
    return "한국어" if use_lang == LANG_KO else "tieng Viet"
