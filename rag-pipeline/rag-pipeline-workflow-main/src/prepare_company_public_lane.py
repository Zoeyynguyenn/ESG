"""Curate lane 04_company_public_curated tu Downloads/data-company."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ALLOWED_EXT = {".pdf", ".html", ".htm", ".json", ".md"}
KEYWORDS = (
    "sustainability",
    "esg",
    "annual",
    "report",
    "ir",
    "지속가능",
    "사업보고서",
    "environment",
    "financial",
    "governance",
    "social",
)

SKIP_PATH_PARTS = ("__macosx", "_run_logs")
SKIP_NAME_PREFIX = "._"


@dataclass
class Candidate:
    source: Path
    company: str
    company_slug: str
    score: int
    size: int
    ext: str
    category: str


def _slug_company(name: str) -> str:
    mapping = {
        "현대자동차": "hyundai_motor",
        "한샘": "hanssem",
        "넥스트아이": "nexteye",
        "두나무": "dunamu",
        "무신사": "musinsa",
        "리디": "ridi",
        "왓챠": "watcha",
        "레이시온": "raysition",
        "스마트스코어": "smartscore",
        "케이론": "kiron",
    }
    for key, slug in mapping.items():
        if key in name:
            return slug
    safe = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_").lower()
    return safe[:40] or "company"


def _category_from_path(rel: str) -> str:
    low = rel.lower()
    if "ir" in low or "ir자료" in low:
        return "ir"
    if any(k in low for k in ("sustainability", "esg", "지속가능", "environment")):
        return "sustainability"
    if any(k in low for k in ("annual", "사업보고서", "report")):
        return "annual_report"
    return "general"


def _should_skip(path: Path, min_size: int) -> Optional[str]:
    parts = [p.lower() for p in path.parts]
    if any(s in parts for s in SKIP_PATH_PARTS):
        return "skip_path_pattern"
    if path.name.startswith(SKIP_NAME_PREFIX):
        return "skip_dot_underscore"
    if path.suffix.lower() not in ALLOWED_EXT:
        return "skip_extension"
    try:
        size = path.stat().st_size
    except OSError:
        return "skip_unreadable"
    if size < min_size:
        return "skip_too_small"
    return None


def _keyword_score(path: Path, rel: str) -> int:
    hay = f"{rel} {path.name}".lower()
    return sum(1 for k in KEYWORDS if k in hay)


def scan_source(root: Path, min_size: int) -> Tuple[List[Candidate], Counter]:
    rejected: Counter = Counter()
    candidates: List[Candidate] = []
    for company_dir in sorted(root.iterdir()):
        if not company_dir.is_dir():
            continue
        if company_dir.name.startswith("_") or company_dir.name == "__MACOSX":
            rejected["skip_top_level"] += 1
            continue
        slug = _slug_company(company_dir.name)
        for f in company_dir.rglob("*"):
            if not f.is_file():
                continue
            reason = _should_skip(f, min_size)
            if reason:
                rejected[reason] += 1
                continue
            rel = str(f.relative_to(company_dir)).replace("\\", "/")
            candidates.append(
                Candidate(
                    source=f,
                    company=company_dir.name,
                    company_slug=slug,
                    score=_keyword_score(f, rel),
                    size=f.stat().st_size,
                    ext=f.suffix.lower(),
                    category=_category_from_path(rel),
                )
            )
    return candidates, rejected


def select_candidates(
    candidates: List[Candidate],
    *,
    max_companies: int,
    max_per_company: int,
) -> List[Candidate]:
    by_company: Dict[str, List[Candidate]] = defaultdict(list)
    for c in candidates:
        by_company[c.company_slug].append(c)
    ranked = sorted(
        by_company.items(),
        key=lambda x: (sum(c.score for c in x[1]), len(x[1])),
        reverse=True,
    )[:max_companies]
    selected: List[Candidate] = []
    for _slug, items in ranked:
        items.sort(key=lambda c: (-c.score, -c.size, c.source.name))
        selected.extend(items[:max_per_company])
    return selected


def copy_to_lane(
    selected: List[Candidate],
    dest_root: Path,
    *,
    dry_run: bool,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for c in selected:
        target_rel = f"{c.company_slug}/{c.category}/{c.source.name}"
        target = dest_root / target_rel
        reason = "keyword_match" if c.score > 0 else "representative_fill"
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c.source, target)
        rows.append(
            {
                "company": c.company_slug,
                "source_path": str(c.source),
                "target_path": str(target_rel).replace("\\", "/"),
                "ext": c.ext,
                "size_bytes": str(c.size),
                "selected_reason": reason,
            }
        )
    return rows


def write_summary(
    path: Path,
    *,
    selected: List[Candidate],
    rejected: Counter,
    manifest_rows: List[Dict[str, str]],
    source_root: Path,
    dest_root: Path,
) -> None:
    by_ext = Counter(r["ext"] for r in manifest_rows)
    by_co = Counter(r["company"] for r in manifest_rows)
    lines = [
        "# Company Public Lane Summary",
        "",
        f"- Nguon: `{source_root}`",
        f"- Dich: `{dest_root}`",
        f"- So file da chon: **{len(manifest_rows)}**",
        f"- So company: **{len(by_co)}**",
        "",
        "## Breakdown theo company",
        "",
        "| company | files |",
        "|---|---:|",
    ]
    for co, n in sorted(by_co.items()):
        lines.append(f"| {co} | {n} |")
    lines.extend(["", "## Breakdown theo extension", "", "| ext | count |", "|---|---:|"])
    for ext, n in sorted(by_ext.items()):
        lines.append(f"| {ext} | {n} |")
    lines.extend(["", "## File bi loai (top reasons)", "", "| reason | count |", "|---|---:|"])
    for reason, n in rejected.most_common(12):
        lines.append(f"| {reason} | {n} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    from config import BASE_DIR

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=r"C:\Users\nguye\Downloads\data-company",
    )
    parser.add_argument(
        "--dest",
        default=str(BASE_DIR / "data" / "rag_dataset" / "04_company_public_curated"),
    )
    parser.add_argument("--max-companies", type=int, default=5)
    parser.add_argument("--max-per-company", type=int, default=40)
    parser.add_argument("--min-size-bytes", type=int, default=2048)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    source_root = Path(args.source)
    dest_root = Path(args.dest)
    if not source_root.exists():
        raise SystemExit(f"Khong tim thay nguon: {source_root}")

    candidates, rejected = scan_source(source_root, args.min_size_bytes)
    selected = select_candidates(
        candidates,
        max_companies=args.max_companies,
        max_per_company=args.max_per_company,
    )
    if args.dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)
    manifest_rows = copy_to_lane(selected, dest_root, dry_run=args.dry_run)

    manifest_path = dest_root / "manifest.csv"
    if not args.dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["company", "source_path", "target_path", "ext", "size_bytes", "selected_reason"],
            )
            writer.writeheader()
            writer.writerows(manifest_rows)

    summary_path = BASE_DIR / "reports" / "company_public_lane_summary.md"
    write_summary(
        summary_path,
        selected=selected,
        rejected=rejected,
        manifest_rows=manifest_rows,
        source_root=source_root,
        dest_root=dest_root,
    )
    print(
        {
            "selected": len(manifest_rows),
            "companies": len({r["company"] for r in manifest_rows}),
            "manifest": str(manifest_path),
            "summary": str(summary_path),
            "dry_run": args.dry_run,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
