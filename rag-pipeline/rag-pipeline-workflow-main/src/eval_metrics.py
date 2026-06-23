"""Backward-compatible exports; V2 scoring trong eval_scoring_v2."""

from eval_scoring_v2 import (
    aggregate_metrics_v2 as aggregate_metrics,
    parse_eval_set,
    score_result_v2 as score_result,
)
from eval_set_io import parse_eval_set_rows, validate_eval_set

__all__ = [
    "parse_eval_set",
    "parse_eval_set_rows",
    "validate_eval_set",
    "score_result",
    "aggregate_metrics",
]
