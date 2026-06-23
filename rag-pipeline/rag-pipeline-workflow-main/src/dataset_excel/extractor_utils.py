"""Shared parsing, filtering, and numeric helpers for extractors."""

from __future__ import annotations

import math
import re
from typing import Any

from dataset_excel.constants import KV_RE, MILLION_UNITS, NUM_RE, PERIOD_KEY_RE
from dataset_excel.profile import QuestionProfile


def normalize_path(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("\\", "/").lower().strip()


def unit_search_text(unit: dict[str, Any]) -> str:
    return str(unit.get("search_text") or unit.get("text") or "")


def unit_evidence_text(unit: dict[str, Any]) -> str:
    return str(unit.get("evidence_text") or unit.get("search_text") or unit.get("text") or "")


def parse_kv_record(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in KV_RE.findall(text or ""):
        fields[key.strip()] = value.strip()
    return fields


def to_int(value: str | None) -> int:
    if not value or value == "-":
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return 0


def amount_from_field_value(raw: str) -> float | None:
    cleaned = (raw or "").replace("KRW", "").replace(",", "").strip()
    if not cleaned or cleaned == "-":
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not m:
        return None
    return float(m.group(0))


def period_value(fields: dict[str, str], question_year: int | None, doc_year: int | None) -> float | None:
    period_items: list[tuple[int, str]] = []
    for key, value in fields.items():
        m = PERIOD_KEY_RE.search(key)
        if m:
            period_items.append((int(m.group(1)), value))
    if not period_items:
        return None
    period_items.sort(key=lambda x: x[0], reverse=True)
    if question_year is None or doc_year is None:
        return amount_from_field_value(period_items[0][1])
    offset = max(0, int(doc_year) - int(question_year))
    if offset >= len(period_items):
        return amount_from_field_value(period_items[-1][1])
    return amount_from_field_value(period_items[offset][1])


def numbers_in_text(text: str) -> list[float]:
    out: list[float] = []
    for m in NUM_RE.findall(text or ""):
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            continue
    return out


def expand_evidence_from_index(
    evidence: list[dict[str, Any]],
    index: dict[str, Any],
    profile: QuestionProfile,
    question_year: int | None,
) -> list[dict[str, Any]]:
    seen = {item.get("chunk_id") for item in evidence}
    expanded = list(evidence)
    for unit in index.get("units", []):
        doc_title = str(unit.get("doc_title") or "")
        unit_year = unit.get("year")
        if profile.preferred_doc_patterns and not any(p in doc_title for p in profile.preferred_doc_patterns):
            continue
        if question_year is not None and unit_year not in (None, "", question_year):
            continue
        chunk_id = unit.get("chunk_id")
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        expanded.append(
            {
                "chunk_id": chunk_id,
                "evidence_text": unit_evidence_text(unit),
                "metadata": {
                    "company_id": unit.get("company_id"),
                    "doc_title": unit.get("doc_title"),
                    "source_url": unit.get("source_url"),
                    "file_url": unit.get("file_url"),
                    "source_kind": unit.get("source_kind"),
                    "year": unit.get("year"),
                    "schema": unit.get("schema"),
                },
            }
        )
    return expanded


def filter_evidence_by_profile(evidence: list[dict[str, Any]], profile: QuestionProfile) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for item in evidence:
        meta = item.get("metadata") or {}
        doc_title = str(meta.get("doc_title") or "")
        if profile.preferred_doc_patterns and not any(p in doc_title for p in profile.preferred_doc_patterns):
            continue
        if profile.year is not None and meta.get("year") not in (None, "", profile.year):
            continue
        filtered.append(item)
    return filtered or evidence


def records_from_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in evidence:
        text = item.get("evidence_text") or ""
        for line in text.splitlines():
            line = line.strip().lstrip("- ").strip()
            if not line or ("=" not in line):
                continue
            if line in seen:
                continue
            seen.add(line)
            records.append(parse_kv_record(line))
    return records


def format_number(value: float, unit: str | None) -> str:
    if unit == "%":
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text if "." in text else f"{value:.1f}"
    if unit in MILLION_UNITS:
        rounded = int(round(value))
        return str(rounded)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def close_enough(predicted: float, gold: float, unit: str | None) -> bool:
    if unit == "%":
        return math.isclose(predicted, gold, rel_tol=0, abs_tol=0.15)
    if unit in MILLION_UNITS:
        return math.isclose(predicted, gold, rel_tol=0, abs_tol=1.0)
    return math.isclose(predicted, gold, rel_tol=0, abs_tol=0.05)
