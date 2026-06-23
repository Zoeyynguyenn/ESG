#!/usr/bin/env python3
"""Prepare crawl/import manifests from dataset Excel source registries."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _classify_source(row: dict[str, Any]) -> dict[str, Any]:
    source_url = (row.get("source_url") or "").strip()
    file_url = (row.get("file_url") or "").strip()
    doc_title = row.get("doc_title")
    link_check = row.get("link_check")

    if file_url and file_url.lower().endswith(".json"):
        source_kind = "collector_file_reference"
        action = "resolve_local_file_first"
        review_reason = "" if source_url else "missing_source_url"
        domain = urlparse(source_url).netloc.lower() if source_url else None
    elif source_url:
        parsed = urlparse(source_url)
        domain = parsed.netloc.lower()
        if domain == "dart.fss.or.kr":
            source_kind = "web_dart"
        elif domain:
            source_kind = "web_public"
        else:
            source_kind = "web_unknown"
        action = "crawl_web"
        review_reason = ""
    elif file_url:
        source_kind = "collector_file_reference"
        action = "resolve_local_file_first"
        review_reason = "missing_source_url"
    else:
        source_kind = "missing_source_reference"
        action = "needs_review"
        review_reason = "missing_source_url_and_file_url"
        domain = ""

    return {
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "doc_title": doc_title,
        "source_url": source_url or None,
        "file_url": file_url or None,
        "link_check": link_check,
        "confidence": row.get("confidence"),
        "source_kind": source_kind,
        "recommended_action": action,
        "review_reason": review_reason,
        "domain": domain if source_url else None,
    }


def _dedupe_key(row: dict[str, Any]) -> str:
    return (row.get("file_url") or row.get("source_url") or row.get("doc_title") or "").strip()


def _summary_lines(rows: list[dict[str, Any]], by_company: dict[str, list[dict[str, Any]]]) -> str:
    action_counts = Counter(row["recommended_action"] for row in rows)
    kind_counts = Counter(row["source_kind"] for row in rows)
    lines = [
        "# Source Intake Prep Summary",
        "",
        "## Tong hop",
        "",
        f"- total_unique_sources: {len(rows)}",
        f"- crawl_web: {action_counts.get('crawl_web', 0)}",
        f"- resolve_local_file_first: {action_counts.get('resolve_local_file_first', 0)}",
        f"- needs_review: {action_counts.get('needs_review', 0)}",
        "",
        "## Theo company",
        "",
        "| Company | Unique sources | Crawl web | Resolve local file | Needs review |",
        "|---|---:|---:|---:|---:|",
    ]
    for company_id, company_rows in sorted(by_company.items()):
        local_counts = Counter(row["recommended_action"] for row in company_rows)
        company_name = company_rows[0]["company_name"] if company_rows else company_id
        lines.append(
            f"| {company_name} | {len(company_rows)} | {local_counts.get('crawl_web', 0)} | "
            f"{local_counts.get('resolve_local_file_first', 0)} | {local_counts.get('needs_review', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Theo source kind",
            "",
            "| Source kind | Count |",
            "|---|---:|",
        ]
    )
    for kind, count in sorted(kind_counts.items()):
        lines.append(f"| {kind} | {count} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="data/dataset_excel_intake/20260617_goldns_emni")
    parser.add_argument("--output-root", default="data/source_intake_prep/20260617_goldns_emni")
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)

    registry_rows: list[dict[str, Any]] = []
    for company_dir in sorted(p for p in input_root.iterdir() if p.is_dir()):
        registry_rows.extend(_read_jsonl(company_dir / "source_registry.jsonl"))

    deduped: dict[str, dict[str, Any]] = {}
    for row in registry_rows:
        normalized = _classify_source(row)
        key = _dedupe_key(normalized)
        if key and key not in deduped:
            deduped[key] = normalized

    all_rows = list(deduped.values())
    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        by_company[row["company_id"]].append(row)

    _write_jsonl(output_root / "all_sources_manifest.jsonl", all_rows)
    _write_csv(output_root / "all_sources_manifest.csv", all_rows)

    for company_id, company_rows in by_company.items():
        company_dir = output_root / company_id
        _write_jsonl(company_dir / "source_manifest.jsonl", company_rows)
        _write_csv(company_dir / "source_manifest.csv", company_rows)

        crawl_web = [row for row in company_rows if row["recommended_action"] == "crawl_web"]
        resolve_local = [row for row in company_rows if row["recommended_action"] == "resolve_local_file_first"]
        review = [row for row in company_rows if row["recommended_action"] == "needs_review"]

        _write_jsonl(company_dir / "crawl_web.jsonl", crawl_web)
        _write_jsonl(company_dir / "resolve_local_file_first.jsonl", resolve_local)
        _write_jsonl(company_dir / "needs_review.jsonl", review)

        _write_csv(company_dir / "crawl_web.csv", crawl_web)
        _write_csv(company_dir / "resolve_local_file_first.csv", resolve_local)
        _write_csv(company_dir / "needs_review.csv", review)

    (output_root / "README.md").write_text(_summary_lines(all_rows, by_company), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
