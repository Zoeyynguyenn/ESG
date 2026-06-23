"""Shared constants for dataset-excel extractive RAG (goldns/emni baseline v5)."""

from __future__ import annotations

import re

NUM_RE = re.compile(r"-?[\d,]+(?:\.\d+)?")
KV_RE = re.compile(r"([^|=]+)=([^|]+)")
PERIOD_KEY_RE = re.compile(r"제\s*(\d+)\s*기")
RECALL_DATA_SIGNAL_RE = re.compile(r"(자발|비자발|명령|권고|회수|리콜종류)")

MILLION_UNITS = {"백만 원", "백만원"}
NOISE_DOC_PATTERNS = ("제재이력", "최저임금", "minimumwage")

SANCTION_LANE_BY_DOMAIN = {
    "www.safetykorea.kr": "safetykorea",
    "www.pipc.go.kr": "pipc",
    "case.ftc.go.kr": "ftc",
}

FTC_BLOCKED_URL = "case.ftc.go.kr"

V2_BASELINE_METRICS = {
    "retrieval_hit_top1": 0.7612,
    "retrieval_hit_topk": 0.8507,
    "source_match_top1": 0.7612,
    "source_match_topk": 0.8507,
    "answer_accuracy": 0.8657,
    "abstain_accuracy": 1.0,
    "overall_score": 0.8470,
}
V3_BASELINE_METRICS = {
    "retrieval_hit_top1": 0.8507,
    "retrieval_hit_topk": 0.8507,
    "source_match_top1": 0.8507,
    "source_match_topk": 0.8507,
    "answer_accuracy": 0.8955,
    "abstain_accuracy": 1.0,
    "overall_score": 0.8992,
}
V4_BASELINE_METRICS = {
    "retrieval_hit_top1": 0.9403,
    "retrieval_hit_topk": 0.9403,
    "source_match_top1": 0.9403,
    "source_match_topk": 0.9403,
    "answer_accuracy": 0.9254,
    "abstain_accuracy": 1.0,
    "overall_score": 0.9515,
}

BASELINE_VERSION = "v5"
