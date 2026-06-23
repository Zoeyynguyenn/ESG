"""Canonical value normalization and cross-document value equivalence."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EQUIVALENCE_REGISTRY_PATH = ROOT / "data/enterprise_docs/metric_equivalence_registry.json"
OVERLAP_REGISTRY_PATH = ROOT / "data/enterprise_docs/metric_overlap_registry.json"


def _norm_token(val: str) -> str:
    return re.sub(r"\s+", " ", (val or "").strip().lower())


@lru_cache(maxsize=1)
def load_equivalence_registry() -> dict[str, Any]:
    if EQUIVALENCE_REGISTRY_PATH.exists():
        return json.loads(EQUIVALENCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


@lru_cache(maxsize=1)
def load_overlap_registry_fallback() -> dict[str, Any]:
    if OVERLAP_REGISTRY_PATH.exists():
        return json.loads(OVERLAP_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


def _merged_value_equivalence() -> dict[str, list[str]]:
    reg = load_equivalence_registry()
    out: dict[str, list[str]] = {}
    for key, variants in (reg.get("value_equivalence") or {}).items():
        out[key] = list(variants)
    overlap = load_overlap_registry_fallback()
    for key, variants in (overlap.get("cross_doc_value_equivalence") or {}).items():
        existing = out.setdefault(key, [])
        for v in variants or []:
            if v not in existing:
                existing.append(v)
    return out


def canonical_metric_value(
    value: str | None,
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> str | None:
    """Map surface values to canonical keys for cross-doc agreement."""
    if value is None:
        return None
    raw = _norm_token(str(value))
    if not raw:
        return None

    if re.fullmatch(r"a\+", raw):
        return "esg_grade_a_plus"
    if re.fullmatch(r"a\+?", raw):
        return "esg_grade_a"

    equiv = _merged_value_equivalence()
    for key, variants in equiv.items():
        variants_norm = {_norm_token(v) for v in variants}
        if raw in variants_norm:
            return key

    overlap = load_overlap_registry_fallback()
    if family_id:
        fam_keys = (overlap.get("metric_canonical_keys") or {}).get(family_id) or {}
        item_key = str(item or "")
        for metric_item, variants in fam_keys.items():
            variants_norm = {_norm_token(v) for v in variants}
            if raw in variants_norm:
                return f"{family_id}:{metric_item}"

    if re.fullmatch(r"[a-z][+]?", raw):
        return f"grade:{raw.upper()}"
    if re.fullmatch(r"scope\s*3", raw) or raw == "scope_3":
        return "scope_3"
    if re.fullmatch(r"20\d{2}", raw):
        return f"year:{raw}"
    if re.fullmatch(r"[\d,]+(?:\.\d+)?", raw):
        return raw.replace(",", "")
    return raw


def values_equivalent(
    a: str | None,
    b: str | None,
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> bool:
    if a is None or b is None:
        return False
    ca = canonical_metric_value(a, item=item, family_id=family_id)
    cb = canonical_metric_value(b, item=item, family_id=family_id)
    if ca and cb and ca == cb:
        return True
    na, nb = _norm_token(a), _norm_token(b)
    if na == nb:
        return True
    if na.replace(" ", "") == nb.replace(" ", ""):
        return True
    if na.replace(",", "") == nb.replace(",", ""):
        return True
    return False


def registry_snapshot() -> dict[str, Any]:
    reg = load_equivalence_registry()
    return {
        "path": str(EQUIVALENCE_REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "version": reg.get("version"),
        "family_buckets": list((reg.get("family_buckets") or {}).keys()),
        "value_equivalence_keys": list(_merged_value_equivalence().keys()),
        "cross_role_pattern_families": list((reg.get("cross_role_narrative_patterns") or {}).keys()),
    }
