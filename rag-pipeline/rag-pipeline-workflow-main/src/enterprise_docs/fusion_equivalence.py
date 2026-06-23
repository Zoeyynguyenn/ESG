"""Fusion + equivalence contract — collapse, confirm, promote with integrity."""

from __future__ import annotations

import re
from typing import Any

from enterprise_docs.value_equivalence import canonical_metric_value, values_equivalent

NUMERIC_RE = re.compile(r"[\d,]+(?:\.\d+)?")
UNIT_SUFFIX_RE = re.compile(
    r"\s*(?:tco2e|tco2|co2e|명|회|건|개|%|usd|krw|원|million|mil|billion|조|억)\b",
    re.I,
)


def normalize_numeric_value(value: str | None) -> str | None:
    """Strip formatting/units for numeric comparison."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    low = raw.lower()
    if low in ("not disclosed", "n/a", "-", "present", "scope_3"):
        return low
    cleaned = UNIT_SUFFIX_RE.sub("", raw)
    cleaned = cleaned.replace(",", "").replace(" ", "")
    m = NUMERIC_RE.search(cleaned)
    if m:
        return m.group(0).replace(",", "")
    return cleaned or raw


def numeric_values_equivalent(
    a: str | None,
    b: str | None,
    *,
    item: str | None = None,
    family_id: str | None = None,
    tolerance_pct: float = 0.001,
) -> bool:
    if values_equivalent(a, b, item=item, family_id=family_id):
        return True
    na, nb = normalize_numeric_value(a), normalize_numeric_value(b)
    if na is None or nb is None:
        return False
    if na == nb:
        return True
    try:
        fa, fb = float(na), float(nb)
        denom = max(abs(fa), abs(fb), 1.0)
        if abs(fa - fb) / denom <= tolerance_pct:
            return True
        if abs(fa * 1000 - fb) / max(abs(fb), 1.0) <= tolerance_pct:
            return True
        if abs(fb * 1000 - fa) / max(abs(fa), 1.0) <= tolerance_pct:
            return True
    except ValueError:
        return na.lower() == nb.lower()
    return False


def values_conflict(
    a: str,
    b: str,
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> bool:
    return not numeric_values_equivalent(a, b, item=item, family_id=family_id)


def canonical_metric_label_key(label: str, plan_row: dict[str, Any]) -> str:
    """Group narrative/table labels under the same plan metric item when possible."""
    item = str(plan_row.get("item") or "").strip()
    label_n = re.sub(r"\s+", " ", (label or "").strip().lower())
    if item:
        item_n = item.lower()
        if item_n in label_n or label_n in item_n:
            return f"item:{item}"
        ca = canonical_metric_value(label, item=item, family_id=str(plan_row.get("family_id") or "") or None)
        if ca and ca.startswith("item:"):
            return ca
    key = re.sub(r"\d{4}", "", label_n)
    key = re.sub(r"[^a-z0-9가-힣+]+", " ", key)
    return " ".join(key.split()) or label_n


def equivalence_collapse_success(
    candidates: list[Any],
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> dict[str, Any]:
    """Check whether extracted candidates collapse to a consistent canonical value set."""
    by_doc: dict[str, list[str]] = {}
    raw_values: list[str] = []
    for c in candidates:
        lid = str(getattr(c, "logical_document_id", None) or getattr(c, "logical_doc", "") or "")
        val = str(getattr(c, "value", None) or "")
        if not lid or not val or val.lower() in ("not disclosed",):
            continue
        ck = canonical_metric_value(val, item=item, family_id=family_id) or normalize_numeric_value(val) or val
        by_doc.setdefault(lid, []).append(str(ck))
        raw_values.append(val)

    collapse_ok = True
    if len(raw_values) >= 2:
        for i in range(len(raw_values)):
            for j in range(i + 1, len(raw_values)):
                if values_conflict(raw_values[i], raw_values[j], item=item, family_id=family_id):
                    collapse_ok = False
                    break
            if not collapse_ok:
                break

    canonical: set[str] = set()
    for val in raw_values:
        ck = canonical_metric_value(val, item=item, family_id=family_id) or normalize_numeric_value(val) or val
        canonical.add(str(ck))

    return {
        "unique_canonical_values": sorted(canonical),
        "unique_count": len(canonical),
        "collapse_ok": collapse_ok,
        "by_logical_doc": by_doc,
        "raw_values": raw_values,
    }


def fusion_confirming_docs(
    candidates: list[Any],
    resolved_value: str | None,
    *,
    item: str | None = None,
    family_id: str | None = None,
) -> list[str]:
    if not resolved_value:
        return []
    docs: set[str] = set()
    for c in candidates:
        lid = str(getattr(c, "logical_document_id", None) or getattr(c, "logical_doc", "") or "")
        val = str(getattr(c, "value", None) or "")
        if not lid or not val or val.lower() in ("not disclosed",):
            continue
        if not values_conflict(val, resolved_value, item=item, family_id=family_id):
            docs.add(lid)
    return sorted(docs)


def fusion_success(
    *,
    multi_source_confirmed: bool,
    confirming_docs: list[str],
    expected_multi: bool | None,
    equivalence_collapse: dict[str, Any] | None = None,
) -> bool:
    if expected_multi is None:
        return True
    if expected_multi:
        collapse_ok = equivalence_collapse.get("collapse_ok") if equivalence_collapse else True
        return bool(multi_source_confirmed) and len(confirming_docs) >= 2 and collapse_ok
    return not multi_source_confirmed


def promotion_integrity_ok(
    *,
    fusion_ok: bool,
    promotion: dict[str, Any],
    expected_multi: bool | None,
) -> bool:
    if expected_multi is True:
        return fusion_ok and bool(promotion.get("promoted"))
    if expected_multi is False:
        return True
    return bool(promotion.get("promoted")) if promotion.get("promoted") else True
