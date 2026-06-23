"""Unit tests for enterprise internal-doc answerability classification.

Locks the behaviour added 2026-06-22: unclear / out-of-scope / no-information
questions are separated from corpus_limited and system_gap, the new cases do NOT
disturb the constructed regression gate, and the known heuristic limitations
(adversarial ADV-* cases) are documented as tests rather than hidden.

Run: python -m pytest tests/unit/test_answerability_classification.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from enterprise_docs.crossdoc_capability_benchmark import (  # noqa: E402
    evaluate_case,
    run_capability_benchmark,
)
from enterprise_docs.crossdoc_case_builder import (  # noqa: E402
    all_capability_cases,
    answerability_cases,
)

REGRESSION_METRICS = (
    "cross_role_extraction_alignment_rate",
    "cross_doc_equivalence_match_rate",
    "evidence_fusion_success_rate",
    "conflict_classification_accuracy",
    "single_source_to_multi_source_promotion_rate",
)


@pytest.fixture(scope="module")
def bench() -> dict:
    return run_capability_benchmark(all_capability_cases())


def _by_id() -> dict:
    return {c["case_id"]: c for c in answerability_cases()}


@pytest.mark.parametrize(
    "case_id",
    [
        "ANSWERABILITY-CONTROL-GHG",
        "ANSWERABILITY-OUT-OF-SCOPE-PERSONAL",
        "ANSWERABILITY-NO-INFORMATION-GHG",
        "ANS-EMP-HEADCOUNT",
        "ANS-GOV-BOARD",
        "OOS-WEATHER",
        "NOINFO-GOV-MAT",
    ],
)
def test_clean_cases_classified_correctly(case_id):
    case = _by_id()[case_id]
    out = evaluate_case(case)
    assert out["predicted_answerability"] == case["expected_answerability"]


def test_known_adversarial_limitations_are_documented():
    """These ADV-* cases currently misclassify; the test pins the known behaviour so a
    future fix is detected (the heuristic depends on keywords / token presence / exact
    item phrasing)."""
    by = _by_id()
    # env question without keywords -> falls through to out_of_scope (should be no_information)
    assert evaluate_case(by["ADV-NO-KEYWORD"])["predicted_answerability"] == "out_of_scope"
    # corpus mentions the token but no value -> wrongly answerable, and abstain-unsafe
    tok = evaluate_case(by["ADV-TOKEN-FALSEPOS"])
    assert tok["predicted_answerability"] == "answerable"
    assert tok["abstain_safe"] is False
    # value present under different phrasing -> no_information (should be answerable)
    assert evaluate_case(by["ADV-PHRASING"])["predicted_answerability"] == "no_information"


def test_answerability_metrics_shape(bench):
    am = bench["answerability_metrics"]
    assert am["case_count"] >= 18
    assert 0.0 <= am["answerability_accuracy"] <= 1.0
    assert am["abstain_safety_rate"] is not None
    # current honest baseline: 15/18 correct, 10/11 abstain-safe
    assert am["answerability_accuracy"] == pytest.approx(0.8333, abs=0.01)
    assert am["abstain_safety_rate"] == pytest.approx(0.9091, abs=0.01)


def test_regression_gate_unchanged_by_answerability_cases(bench):
    cm = bench["constructed_metrics"]
    for metric in REGRESSION_METRICS:
        assert cm[metric] == 1.0, f"{metric} regressed to {cm[metric]}"
