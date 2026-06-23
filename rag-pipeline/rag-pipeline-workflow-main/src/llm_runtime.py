"""LLM runtime cho V3 generative baseline (Ollama / OpenAI)."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from benchmark_language import answer_language_label, benchmark_language, insufficient_answer, insufficient_phrases
from config import OLLAMA_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from evidence_rag import INSUFFICIENT_ANSWER

INSUFFICIENT_VARIANTS = insufficient_phrases()


@dataclass
class LlmRuntimeInfo:
    status: str  # ready | blocked
    provider: Optional[str]  # ollama | openai_api
    model_name: Optional[str]
    temperature: float
    blocker_reason: Optional[str] = None
    setup_checklist: Optional[list] = None


def _ollama_paths() -> list:
    import os
    from pathlib import Path

    paths = ["ollama"]
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        paths.append(str(Path(local) / "Programs" / "Ollama" / "ollama.exe"))
    paths.append(r"C:\Program Files\Ollama\ollama.exe")
    return paths


def detect_llm_runtime() -> LlmRuntimeInfo:
    import os

    prefer = os.getenv("RAG_BENCHMARK_LLM_PROVIDER", "").strip().lower()
    if prefer == "openai_api" and OPENAI_API_KEY:
        return LlmRuntimeInfo(
            status="ready",
            provider="openai_api",
            model_name=OPENAI_MODEL,
            temperature=0.0,
        )

    for exe in _ollama_paths():
        try:
            r = subprocess.run(
                [exe, "list"],
                capture_output=True,
                text=True,
                timeout=12,
            )
            if r.returncode == 0:
                return LlmRuntimeInfo(
                    status="ready",
                    provider="ollama",
                    model_name=OLLAMA_MODEL,
                    temperature=0.0,
                )
        except Exception:
            continue

    if OPENAI_API_KEY:
        return LlmRuntimeInfo(
            status="ready",
            provider="openai_api",
            model_name=OPENAI_MODEL,
            temperature=0.0,
        )

    return LlmRuntimeInfo(
        status="blocked",
        provider=None,
        model_name=None,
        temperature=0.0,
        blocker_reason="Khong tim thay Ollama trong PATH va OPENAI_API_KEY chua set",
        setup_checklist=[
            "Cai Ollama: https://ollama.com/download — them vao PATH",
            f"Chay: ollama pull {OLLAMA_MODEL}",
            "Hoac set bien moi truong: OPENAI_API_KEY=<key> (tuy chon OPENAI_BASE_URL, OPENAI_MODEL)",
            "Chay lai: python src/run_v3_1_eval.py",
        ],
    )


def evidence_prompt(context: str, question: str) -> str:
    lang = benchmark_language()
    insufficient = insufficient_answer(lang)
    answer_lang = answer_language_label(lang)
    return f"""당신은 evidence-based RAG 도우미입니다.
필수 규칙:
1. 아래 Context 안의 정보만 사용하세요.
2. Context만으로 답할 수 없으면 정확히 "{insufficient}" 라고 답하세요.
3. Context 밖의 사실을 추측하거나 추가하지 마세요.
4. 답변은 1~2문장으로 짧고 직접적으로, 반드시 {answer_lang}로 작성하세요.
5. 질문이 사실(숫자, 날짜, 횟수)을 묻으면 context에서 해당 사실만 추출해 답하세요.

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(
    context: str,
    question: str,
    runtime: LlmRuntimeInfo,
) -> Tuple[str, str]:
    if runtime.status != "ready" or not runtime.provider:
        raise RuntimeError(runtime.blocker_reason or "LLM runtime blocked")

    if runtime.provider == "ollama":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(model=runtime.model_name or OLLAMA_MODEL, temperature=runtime.temperature)
        out = llm.invoke(evidence_prompt(context, question))
        text = out.content if hasattr(out, "content") else str(out)
        return text.strip(), "ollama"

    if runtime.provider == "openai_api":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": runtime.model_name or OPENAI_MODEL,
            "temperature": runtime.temperature,
            "api_key": OPENAI_API_KEY,
        }
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        llm = ChatOpenAI(**kwargs)
        out = llm.invoke(evidence_prompt(context, question))
        text = out.content if hasattr(out, "content") else str(out)
        return text.strip(), "openai_api"

    raise RuntimeError(f"Unknown provider: {runtime.provider}")


def normalize_answer(text: str) -> Tuple[str, bool]:
    if not text or not text.strip():
        return INSUFFICIENT_ANSWER, True
    low = text.lower()
    if any(v in low for v in INSUFFICIENT_VARIANTS):
        return INSUFFICIENT_ANSWER, True
    return text.strip(), False


def try_parse_json_answer(raw: str) -> Optional[Dict[str, Any]]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None
