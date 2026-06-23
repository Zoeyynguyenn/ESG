"""Sanction lane helpers for dataset-excel RAG."""

from __future__ import annotations

from typing import Any

from dataset_excel.constants import SANCTION_LANE_BY_DOMAIN


def sanction_lane_from_url(url: str | None) -> str | None:
    text = (url or "").lower()
    for domain, lane in SANCTION_LANE_BY_DOMAIN.items():
        if domain in text:
            return lane
    return None


def sanction_lane_from_evidence(item: dict[str, Any]) -> str | None:
    meta = item.get("metadata") or {}
    lane = meta.get("sanction_lane")
    if lane:
        return str(lane)
    doc_title = str(meta.get("doc_title") or "")
    if doc_title.startswith("제재이력_") and doc_title.endswith(".json"):
        return doc_title[len("제재이력_") : -len(".json")]
    return sanction_lane_from_url(str(meta.get("source_url") or ""))
