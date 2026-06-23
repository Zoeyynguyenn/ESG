#!/usr/bin/env python3
"""Reconcile missing local financial source references for dataset-excel intake artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _discover_financial_docs(downloads_root: Path, company_dir_name: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in downloads_root.rglob("*.json"):
        if company_dir_name not in str(path):
            continue
        name = path.name
        if not re.match(r"^20\d{2}_재무_(CFS|OFS)\.json$", name):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        first = payload[0] if payload else {}
        rcept_no = str(first.get("rcept_no") or "").strip()
        source_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else None
        relative = path.relative_to(downloads_root).parts
        if len(relative) >= 2 and relative[0] == relative[1]:
            relative = relative[1:]
        relative_path = Path(*relative).as_posix()
        result[name] = {
            "doc_title": name,
            "source_url": source_url,
            "file_url": f"colletor-ai/{relative_path}",
            "local_path": str(path),
        }
    return result


def _normalize_file_url(file_url: str | None) -> str | None:
    if not file_url:
        return file_url
    normalized = file_url.replace("\\", "/").strip()
    if normalized.startswith("collector-ai/"):
        normalized = "colletor-ai/" + normalized[len("collector-ai/") :]
    if not normalized.startswith("colletor-ai/"):
        normalized = "colletor-ai/" + normalized.lstrip("/")
    parts = normalized.split("/")
    if len(parts) >= 3 and parts[1] == parts[2]:
        parts.pop(1)
    return "/".join(parts)


def _resolve_doc(doc_title: str | None, discovered: dict[str, dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    if not doc_title:
        return None, None
    if doc_title in discovered:
        return discovered[doc_title], None
    cfs_match = re.match(r"^(20\d{2})_재무_CFS\.json$", doc_title)
    if cfs_match:
        alias = f"{cfs_match.group(1)}_재무_OFS.json"
        if alias in discovered:
            return discovered[alias], alias
    return None, None


def _reconcile_company(company_dir: Path, downloads_root: Path, company_dir_name: str) -> dict[str, Any]:
    sources_path = company_dir / "sources.jsonl"
    registry_path = company_dir / "source_registry.jsonl"

    sources = _read_jsonl(sources_path)
    registry = _read_jsonl(registry_path)
    discovered = _discover_financial_docs(downloads_root, company_dir_name)

    patched_source_rows = 0
    added_registry_rows = 0
    patched_questions: list[str] = []

    for row in sources:
        row["file_url"] = _normalize_file_url(row.get("file_url"))
        if (row.get("source_url") or row.get("file_url")):
            continue
        resolved, alias = _resolve_doc(row.get("doc_title"), discovered)
        if not resolved:
            continue
        row["source_url"] = resolved["source_url"]
        row["file_url"] = resolved["file_url"]
        row["crawl_allowed"] = bool(resolved["source_url"])
        if alias:
            row["doc_title"] = alias
            row["page_or_section"] = alias
            note = row.get("source_detail_note")
            alias_note = f"reconciled_from:{Path(row.get('page_or_section') or '').name or 'unknown'}-> {alias}"
            row["source_detail_note"] = f"{note}; {alias_note}" if note else alias_note
        patched_source_rows += 1
        patched_questions.append(row["question_id"])

    normalized_registry: list[dict[str, Any]] = []
    existing_keys: set[tuple[Any, Any, Any]] = set()
    for item in registry:
        item["file_url"] = _normalize_file_url(item.get("file_url"))
        key = (item.get("doc_title"), item.get("source_url"), item.get("file_url"))
        if key in existing_keys:
            continue
        existing_keys.add(key)
        normalized_registry.append(item)
    registry = normalized_registry
    for row in sources:
        if not row.get("file_url") and not row.get("source_url"):
            continue
        key = (row.get("doc_title"), row.get("source_url"), row.get("file_url"))
        if key in existing_keys:
            continue
        registry.append(
            {
                "company_id": row["company_id"],
                "company_name": next((r.get("company_name") for r in registry if r.get("company_name")), None),
                "source_url": row.get("source_url"),
                "file_url": row.get("file_url"),
                "doc_title": row.get("doc_title"),
                "source_type": row.get("source_type", "dataset_excel_reference"),
                "link_check": row.get("link_check"),
                "confidence": row.get("confidence"),
            }
        )
        existing_keys.add(key)
        added_registry_rows += 1

    _write_jsonl(sources_path, sources)
    _write_jsonl(registry_path, registry)
    return {
        "patched_source_rows": patched_source_rows,
        "patched_question_ids": patched_questions,
        "added_registry_rows": added_registry_rows,
        "discovered_financial_docs": sorted(discovered),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-dir", required=True)
    parser.add_argument("--downloads-root", required=True)
    parser.add_argument("--company-dir-name", required=True)
    args = parser.parse_args()

    result = _reconcile_company(
        company_dir=Path(args.company_dir),
        downloads_root=Path(args.downloads_root),
        company_dir_name=args.company_dir_name,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
