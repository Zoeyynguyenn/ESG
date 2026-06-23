"""Light normalization for RTX corpus units before Golden Set candidate generation."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from golden_set.io_utils import read_jsonl, write_jsonl

# UTF-8 read as Latin-1/CP1252 (common PDF/HTML extraction artifacts)
MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u20ac\u00a2": "\u2022",  # bullet
    "\u00e2\u20ac\u02dc": "'",      # left single quote mojibake
    "\u00e2\u20ac\u2122": "'",      # right single quote mojibake
    "\u00e2\u20ac\u0153": '"',      # left double quote mojibake
    "\u00e2\u20ac\u009d": '"',      # right double quote mojibake
    "\u00e2\u20ac\u201d": "\u2014",  # em dash mojibake
    "\u00e2\u20ac\u201c": "\u2013",  # en dash mojibake
    "\u00c2\u00b7": "\u00b7",
    "\u00c2 ": " ",
    "\u00c2": "",
}

HTML_RESIDUE_RE = re.compile(
    r"<!--.*?-->|<\/?(?:image|table|tr|td|th|div|span|p|br)\b[^>]*>",
    re.IGNORECASE | re.DOTALL,
)


def normalize_text(text: str) -> str:
    t = text or ""
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        t = t.replace(bad, good)
    t = html.unescape(t)
    t = HTML_RESIDUE_RE.sub(" ", t)
    t = re.sub(r"\|{2,}", " | ", t)
    t = re.sub(r"-{5,}", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_unit(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    raw = row.get("text") or ""
    cleaned = normalize_text(raw)
    out["text"] = cleaned
    out["text_raw_chars"] = len(raw)
    out["text_normalized_chars"] = len(cleaned)
    fixes = []
    if "â€" in raw or "Â" in raw:
        fixes.append("mojibake_bullet")
    if "&amp;" in raw or "&lt;" in raw or "&gt;" in raw:
        fixes.append("html_entity")
    if "<!--" in raw or "<image" in raw.lower():
        fixes.append("html_residue")
    out["normalization_fixes"] = fixes
    return out


def run_normalize(
    *,
    input_path: Path,
    output_path: Path,
    min_chars: int = 40,
) -> Dict[str, Any]:
    rows = read_jsonl(input_path)
    normalized: List[Dict[str, Any]] = []
    dropped = 0
    fix_counts: Counter = Counter()

    for row in rows:
        unit = normalize_unit(row)
        for f in unit.get("normalization_fixes", []):
            fix_counts[f] += 1
        if len(unit.get("text") or "") < min_chars:
            dropped += 1
            continue
        normalized.append(unit)

    write_jsonl(output_path, normalized)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_units": len(rows),
        "normalized_units": len(normalized),
        "dropped_too_short": dropped,
        "fix_counts": dict(fix_counts),
        "output_path": str(output_path),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Normalize RTX corpus units")
    parser.add_argument(
        "--input",
        default="data/golden_set/v2/rtx_step1_corpus_units/corpus_units_rtx.jsonl",
    )
    parser.add_argument(
        "--output",
        default="data/golden_set/v2/rtx_step1_corpus_units/corpus_units_rtx_normalized.jsonl",
    )
    args = parser.parse_args(argv)

    summary = run_normalize(
        input_path=root / args.input,
        output_path=root / args.output,
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
