"""Normalization layer for extraction values (numeric, unit, year)."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

UNIT_ALIASES = {
    "kwh/san pham": "kWh/san pham",
    "kwh / san pham": "kWh/san pham",
    "gio/thang": "gio/thang",
    "lan/nam": "lan/nam",
    "ngay lam viec": "ngay lam viec",
}


def normalize_numeric(value: Any, field_id: str = "") -> Tuple[Any, Optional[str]]:
    """Chuan hoa so; tra (value, warning)."""
    if value is None:
        return None, None
    if isinstance(value, (int, float)):
        if field_id == "water_reuse_target" and value == 100:
            return None, "rejected_100_wastewater_confusion"
        return value, None
    s = str(value).strip()
    m = re.search(r"(\d+\.?\d*)", s.replace(",", "."))
    if not m:
        return value, None
    num_s = m.group(1)
    try:
        num = int(num_s) if "." not in num_s else float(num_s)
    except ValueError:
        return value, None
    if field_id == "water_reuse_target":
        if num == 100 and re.search(r"100\s*%.*nuoc\s*thai|nuoc\s*thai.*100", s, re.I):
            return None, "rejected_100_wastewater_confusion"
        if num > 50:
            return None, "rejected_unlikely_reuse_pct"
    return num, None


def normalize_unit_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    key = value.lower().strip()
    return UNIT_ALIASES.get(key, value.strip())


def normalize_year_in_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", value.strip())


def normalize_field_value(field_id: str, value: Any, expected_type: str) -> Dict[str, Any]:
    """Wrap normalized value + metadata."""
    warning = None
    if expected_type == "number":
        value, warning = normalize_numeric(value, field_id)
    elif expected_type == "string" and field_id == "energy_intensity_unit":
        value = normalize_unit_string(value)
    else:
        value = normalize_year_in_value(value)
    return {"value": value, "normalize_warning": warning}


def parse_water_reuse_target(text: str) -> Optional[int]:
    """
    Trich ty le tai su dung nuoc — tranh nham 100% xu ly nuoc thai.
    """
    if re.search(r"100\s*%\s*nuoc\s*thai\s*duoc\s*xu\s*ly", text, re.I):
        pass  # khong lay 100 tu dong nay
    m = re.search(
        r"Tai su dung toi thieu\s*(\d{1,2})\s*%",
        text,
        re.I,
    )
    if m:
        v = int(m.group(1))
        if v <= 50:
            return v
    m = re.search(
        r"Ty le nuoc tai su dung[^\d|]*\|\s*%\s*\|\s*>=\s*(\d{1,2})",
        text,
        re.I,
    )
    if m:
        return int(m.group(1))
    m = re.search(r"nuoc sau xu ly[^\d]*(\d{1,2})\s*%", text, re.I)
    if m and int(m.group(1)) <= 50:
        return int(m.group(1))
    return None


def parse_wastewater_boolean(text: str) -> Optional[bool]:
    t = text.lower()
    if re.search(r"100\s*%\s*nuoc\s*thai.*xu\s*ly|nuoc\s*thai.*100\s*%.*truoc", t):
        return True
    if "xu ly truoc khi xa thai" in t and "nuoc thai" in t:
        return True
    return None


def parse_third_party_audit(text: str) -> Optional[str]:
    m = re.search(
        r"Danh gia ben thu ba moi nam\s*(\d+)\s*lan",
        text,
        re.I,
    )
    if m:
        return f"Moi nam {m.group(1)} lan"
    m = re.search(r"danh gia ben thu ba[^\d]*(\d+)\s*lan", text, re.I)
    if m:
        return f"Moi nam {m.group(1)} lan"
    return None


def parse_overtime_hours(text: str) -> Optional[int]:
    m = re.search(r"lam them[^\d]*(\d{1,2})\s*gio\s*/?\s*thang", text, re.I)
    if m:
        v = int(m.group(1))
        if 20 <= v <= 60:
            return v
    m = re.search(r"(\d{1,2})\s*gio/thang", text, re.I)
    if m:
        v = int(m.group(1))
        if 20 <= v <= 60:
            return v
    return None
