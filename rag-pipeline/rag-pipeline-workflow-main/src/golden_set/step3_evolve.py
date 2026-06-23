"""Step 3: Evol-Instruct — evolve a subset of Silver questions."""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, List

from golden_set.io_utils import read_jsonl, write_jsonl

EVOLVE_PROMPT = """Biến câu hỏi SIMPLE thành câu hỏi {mode} cho RAG ESG.
Câu hỏi mới PHẢI trả lời được chỉ từ CONTEXT. Giữ ngôn ngữ tiếng Hàn (ko) nếu context là tiếng Hàn.

Câu hỏi gốc: {question}
Đáp án gốc: {answer}

CONTEXT:
\"\"\"
{context}
\"\"\"

Trả JSON:
{{
  "question": "...",
  "ground_truth_answer": "...",
  "question_type": "{mode}",
  "difficulty": "medium|hard"
}}"""


def _openai_chat(prompt: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return (resp.choices[0].message.content or "").strip()


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def run_step3(
    *,
    input_path: Path,
    output_path: Path,
    model: str,
    evolve_ratio: float = 0.25,
    modes: List[str] | None = None,
    seed: int = 42,
) -> Dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit("OPENAI_API_KEY missing for step 3 evolve")

    modes = modes or ["reasoning", "multi_context"]
    rows = read_jsonl(input_path)
    rng = random.Random(seed)
    n_evolve = max(1, int(len(rows) * evolve_ratio)) if rows else 0
    indices = set(rng.sample(range(len(rows)), min(n_evolve, len(rows)))) if rows else set()

    out: List[Dict[str, Any]] = []
    evolved = 0
    for i, row in enumerate(rows):
        base = dict(row)
        base["pipeline_stage"] = "silver_merged"
        if i not in indices:
            out.append(base)
            continue
        mode = modes[i % len(modes)]
        ctx = row.get("context_excerpt") or ""
        prompt = EVOLVE_PROMPT.format(
            mode=mode,
            question=row.get("question", ""),
            answer=row.get("ground_truth_answer", ""),
            context=ctx,
        )
        try:
            body = _parse_json(_openai_chat(prompt, model))
            ev = dict(row)
            ev["silver_id"] = f"{row.get('silver_id', 'SV')}-E{i+1}"
            ev["pipeline_stage"] = "silver_evolved"
            ev["question"] = body.get("question", row.get("question", "")).strip()
            ev["ground_truth_answer"] = body.get("ground_truth_answer", row.get("ground_truth_answer", "")).strip()
            ev["question_type"] = body.get("question_type", mode)
            ev["difficulty"] = body.get("difficulty", "medium")
            ev["evolved_from"] = row.get("silver_id")
            ev["evolve_mode"] = mode
            out.append(ev)
            evolved += 1
        except Exception:
            out.append(base)

    write_jsonl(output_path, out)
    return {"total": len(out), "evolved": evolved, "output": str(output_path)}
