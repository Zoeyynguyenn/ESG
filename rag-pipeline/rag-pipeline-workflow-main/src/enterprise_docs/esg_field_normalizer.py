"""System-level ESG field normalization for structured records."""

from __future__ import annotations

import re
from typing import Any

_UNIT_ALIASES = {
    "employees": "persons",
    "employee": "persons",
    "명": "persons",
    "persons": "persons",
    "usd million": "USD million",
    "usd billion": "USD billion",
    "mt co2e": "MT CO2e",
    "tj": "TJ",
    "gwh": "GWh",
    "%": "percent",
}


def normalize_unit(unit: str | None) -> str | None:
    if not unit or not str(unit).strip():
        return None
    key = str(unit).strip().lower()
    return _UNIT_ALIASES.get(key, str(unit).strip())


def normalize_year(year: Any, text: str | None = None) -> int | None:
    if year is not None:
        try:
            y = int(year)
            if 2015 <= y <= 2035:
                return y
        except (TypeError, ValueError):
            pass
    if text:
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text) if 2015 <= int(y) <= 2035]
        if years:
            return max(years)
    return None


def normalize_value_display(value: str | None) -> str | None:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    return v.replace("\u00a0", " ").strip()


def map_plan_esg_fields(plan: dict[str, Any], family_id: str | None, schema: dict[str, Any]) -> dict[str, str]:
    """Merge family registry mapping with plan domain/category when present."""
    fam_map = dict((schema.get("family_esg_mapping") or {}).get(family_id or "") or {})
    domain = str(plan.get("domain") or "").strip()
    category = str(plan.get("category") or "").strip()
    subcategory = str(plan.get("subcategory") or "").strip()

    domain_map = {
        "환경": "Environment",
        "사회": "Social",
        "지배구조": "Governance",
        "거버넌스": "Governance",
        "일반": "General",
        "경제": "Economic",
    }
    esg_domain = fam_map.get("esg_domain") or domain_map.get(domain, "General")
    return {
        "esg_domain": esg_domain,
        "category": category or fam_map.get("category") or "Unmapped",
        "subcategory": subcategory or fam_map.get("subcategory") or "",
    }


def normalize_structured_record(record: dict[str, Any], *, schema: dict[str, Any]) -> dict[str, Any]:
    """Apply system-level normalization to a structured ESG record."""
    out = dict(record)
    fid = out.get("family_id")
    plan_stub = {
        "domain": out.get("plan_domain"),
        "category": out.get("plan_category"),
        "subcategory": out.get("plan_subcategory"),
    }
    esg = map_plan_esg_fields(plan_stub, fid, schema)
    out["esg_domain"] = esg["esg_domain"]
    if esg["category"] != "Unmapped":
        out["category"] = esg["category"]
    if esg["subcategory"]:
        out["subcategory"] = esg["subcategory"]

    out["value"] = normalize_value_display(out.get("value"))
    out["unit"] = normalize_unit(out.get("unit"))
    out["year"] = normalize_year(out.get("year"), out.get("value"))
    return out
