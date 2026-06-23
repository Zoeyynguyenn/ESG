"""RAGAS batch eval for benchmark cases (OpenAI judge)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _mean(values: List[Optional[float]]) -> Optional[float]:
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 4)


def run_ragas_on_evaluated(
    evaluated: List[Dict[str, Any]],
    *,
    max_questions: int = 10,
    model_judge: str = "",
) -> Dict[str, Any]:
    """
    Run RAGAS on pre-scored eval rows.
    Each item: {"row": eval dict, "result": query_v3 result}.
    """
    from config import OPENAI_MODEL

    judge = model_judge or OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base = {
        "faithfulness": None,
        "answer_relevancy": None,
        "context_precision": None,
        "context_recall": None,
        "model_judge": judge,
        "ragas_samples": 0,
    }
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return {**base, "ragas_status": "disabled", "ragas_reason": "OPENAI_API_KEY_missing"}

    try:
        from datasets import Dataset
        from ragas import evaluate
    except Exception as exc:
        return {**base, "ragas_status": "fallback", "ragas_reason": f"ragas_unavailable:{exc}"}

    slice_ = evaluated[: max(1, max_questions)] if max_questions > 0 else evaluated
    questions: List[str] = []
    answers: List[str] = []
    contexts: List[List[str]] = []
    ground_truths: List[str] = []

    for item in slice_:
        row = item.get("row") or {}
        result = item.get("result") or {}
        ev = result.get("evidence") or []
        ctx = [str(e.get("text") or "") for e in ev if e.get("text")]
        if not ctx:
            ctx = [""]
        questions.append(str(row.get("question") or ""))
        answers.append(str(result.get("answer") or ""))
        contexts.append(ctx)
        ground_truths.append(str(row.get("expected_answer") or ""))

    if not questions:
        return {**base, "ragas_status": "skipped", "ragas_reason": "no_eval_rows"}

    # Metric imports — ragas 0.1.x vs 0.2.x
    metrics = []
    try:
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    except Exception:
        try:
            from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

            metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()]
        except Exception as exc:
            return {**base, "ragas_status": "fallback", "ragas_reason": f"ragas_metrics_import:{exc}"}

    ds = Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )
    try:
        os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        result = evaluate(ds, metrics=metrics)
        # ragas 0.1 returns dict-like; 0.2 EvaluationResult
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            row = df.mean(numeric_only=True)
            return {
                "faithfulness": _scalar(row.get("faithfulness")),
                "answer_relevancy": _scalar(row.get("answer_relevancy")),
                "context_precision": _scalar(row.get("context_precision")),
                "context_recall": _scalar(row.get("context_recall")),
                "model_judge": judge,
                "ragas_samples": len(questions),
                "ragas_status": "success",
                "ragas_reason": "",
            }
        scores = dict(result) if isinstance(result, dict) else {}
        return {
            "faithfulness": _scalar(scores.get("faithfulness")),
            "answer_relevancy": _scalar(scores.get("answer_relevancy")),
            "context_precision": _scalar(scores.get("context_precision")),
            "context_recall": _scalar(scores.get("context_recall")),
            "model_judge": judge,
            "ragas_samples": len(questions),
            "ragas_status": "success",
            "ragas_reason": "",
        }
    except Exception as exc:
        return {
            **base,
            "ragas_samples": len(questions),
            "ragas_status": "failed",
            "ragas_reason": f"ragas_eval_error:{exc}",
        }


def _scalar(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        if f != f:  # NaN
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None
