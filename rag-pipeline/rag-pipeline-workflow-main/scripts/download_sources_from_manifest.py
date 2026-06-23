#!/usr/bin/env python3
"""Download raw web sources from source intake manifest."""

from __future__ import annotations

import argparse
import json
import re
import ssl
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import requests


USER_AGENT = "rag-pipeline-workflow/1.0 (source-intake; local research)"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _slug(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z._-]+", "_", text.strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "source"


def _filename_for(row: dict[str, Any]) -> str:
    parsed = urlparse(row["source_url"])
    domain = parsed.netloc.lower().replace(".", "_")
    title = _slug(str(row.get("doc_title") or "doc"))
    return f"{domain}__{title}.html"


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:200]
    return ""


def _download_one(row: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    out_file = output_dir / _filename_for(row)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = Request(row["source_url"], headers=headers)
    try:
        with urlopen(req, timeout=120) as resp:
            content = resp.read()
            status_code = getattr(resp, "status", None)
            content_type = resp.headers.get("Content-Type", "")
        out_file.write_bytes(content)
        title = _extract_title(content.decode("utf-8", errors="replace"))
        return {
            **row,
            "download_status": "ok",
            "http_status": status_code,
            "content_type": content_type,
            "bytes": len(content),
            "local_path": str(out_file),
            "detected_title": title,
            "download_method": "urllib",
        }
    except Exception as exc:
        first_error = str(exc)
        try:
            resp = requests.get(
                row["source_url"],
                timeout=120,
                allow_redirects=False,
                verify=False,
                headers=headers,
            )
            if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("location") == row["source_url"]:
                return {
                    **row,
                    "download_status": "fail",
                    "error": "self_redirect_loop_blocked_by_site",
                    "first_error": first_error,
                    "http_status": resp.status_code,
                    "location": resp.headers.get("location"),
                    "local_path": str(out_file),
                    "download_method": "requests_noverify",
                }
            content = resp.content
            out_file.write_bytes(content)
            title = _extract_title(resp.text)
            return {
                **row,
                "download_status": "ok",
                "http_status": resp.status_code,
                "content_type": resp.headers.get("content-type", ""),
                "bytes": len(content),
                "local_path": str(out_file),
                "detected_title": title,
                "download_method": "requests_noverify",
                "first_error": first_error,
            }
        except Exception as fallback_exc:
            final_error = f"{first_error} | fallback={fallback_exc}"
        else:
            final_error = first_error
        return {
            **row,
            "download_status": "fail",
            "error": final_error,
            "local_path": str(out_file),
        }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    ok = sum(1 for row in rows if row.get("download_status") == "ok")
    fail = total - ok
    lines = [
        "# Download Summary",
        "",
        f"- total: {total}",
        f"- ok: {ok}",
        f"- fail: {fail}",
        "",
        "| Company | Domain | Doc title | Status | Local path |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('company_name')} | {row.get('domain') or ''} | {row.get('doc_title') or ''} | "
            f"{row.get('download_status')} | {row.get('local_path')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/source_intake_prep/20260617_goldns_emni/all_sources_manifest.jsonl")
    parser.add_argument("--output-root", default="data/source_raw/20260617_goldns_emni")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_root = Path(args.output_root)

    rows = [row for row in _read_jsonl(manifest_path) if row.get("recommended_action") == "crawl_web" and row.get("source_url")]
    results: list[dict[str, Any]] = []
    for row in rows:
        company_dir = output_root / row["company_id"] / "web_sources"
        company_dir.mkdir(parents=True, exist_ok=True)
        results.append(_download_one(row, company_dir))

    _write_jsonl(output_root / "download_status.jsonl", results)
    _write_summary(output_root / "README.md", results)
    return 0 if all(row.get("download_status") == "ok" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
