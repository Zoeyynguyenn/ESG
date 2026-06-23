"""Step 2: Distillation — LLM generates Silver Q&A from corpus units."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from golden_set.io_utils import append_jsonl, read_jsonl


DISTILL_PROMPT = """Bạn tạo cặp câu hỏi–trả lời cho đánh giá RAG ESG.
Chỉ dùng thông tin trong CONTEXT. Câu hỏi và câu trả lời PHẢI bằng tiếng Hàn (ko) nếu context là tiếng Hàn.
Không dùng tiếng Việt hay tiếng Anh trong question/answer.

CONTEXT:
\"\"\"
{context}
\"\"\"

METADATA: company={company}, GRI={gri}, item={item}

Tạo JSON (không markdown):
{{
  "question": "câu hỏi trực tiếp về nội dung context",
  "answer": "câu trả lời ngắn, chỉ từ context",
  "question_type": "simple",
  "difficulty": "easy|medium"
}}"""


def _openai_chat(prompt: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def run_step2(
    *,
    input_path: Path,
    output_path: Path,
    model: str,
    max_chars: int = 1200,
    limit: int = 0,
) -> Dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit("OPENAI_API_KEY missing for step 2 distillation")

    units = read_jsonl(input_path)
    if limit > 0:
        units = units[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    ok = 0
    fail = 0
    for i, unit in enumerate(units):
        ctx = (unit.get("text") or "")[:max_chars]
        prompt = DISTILL_PROMPT.format(
            context=ctx,
            company=unit.get("company", ""),
            gri=unit.get("gri_code", ""),
            item=unit.get("item", ""),
        )
        try:
            raw = _openai_chat(prompt, model)
            body = _parse_json(raw)
            row = {
                "silver_id": f"SV2-D-{i+1:04d}",
                "pipeline_stage": "silver_distilled",
                "question": body.get("question", "").strip(),
                "ground_truth_answer": body.get("answer", "").strip(),
                "ground_truth_context_ids": [unit.get("unit_id")],
                "ground_truth_record_id": unit.get("record_id", ""),
                "question_type": body.get("question_type", "simple"),
                "difficulty": body.get("difficulty", "easy"),
                "company": unit.get("company", ""),
                "package_name": unit.get("package_name", ""),
                "gri_code": unit.get("gri_code", ""),
                "context_excerpt": ctx[:400],
                "source_file": unit.get("source_file", ""),
            }
            if row["question"] and row["ground_truth_answer"]:
                append_jsonl(output_path, row)
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1

    return {"silver_written": ok, "failed": fail, "output": str(output_path)}
