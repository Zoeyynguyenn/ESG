"""Download 6 RTX web reference URLs as raw HTML into web_sources/."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/rag_dataset/06_rtx_references_raw/web_sources"
STATUS_JSON = ROOT / "data/rag_dataset/06_rtx_references_raw/web_sources_download_status.json"
SOURCE_JSON = ROOT / "data/rag_dataset/06_rtx_references_raw/source_urls.json"

USER_AGENT = "rag-pipeline-workflow/1.0 (research; contact: dataset-team@local)"

DOWNLOADS = [
    {
        "filename": "rtx_proxy_2025.html",
        "url": "https://www.sec.gov/Archives/edgar/data/101829/000130817925000067/rtx4383903-def14a.htm",
        "snapshot": "rtx_proxy_2025.md",
        "expected_in_title": ("RTX", "DEF 14A", "Proxy"),
    },
    {
        "filename": "rtx_10k_2025.html",
        "url": "https://www.sec.gov/Archives/edgar/data/101829/000010182926000006/rtx-20251231.htm",
        "snapshot": "rtx_10k_2025.md",
        "expected_in_title": ("RTX", "10-K", "2025"),
    },
    {
        "filename": "rtx_10k_2024.html",
        "url": "https://www.sec.gov/Archives/edgar/data/101829/000010182925000005/rtx-20241231.htm",
        "snapshot": "rtx_10k_2024.md",
        "expected_in_title": ("RTX", "10-K", "2024"),
    },
    {
        "filename": "rtx_data_security_privacy.html",
        "url": "https://www.rtx.com/our-responsibility/data-security-and-privacy",
        "snapshot": "rtx_data_security_privacy.md",
        "expected_in_title": ("Data", "Security", "Privacy"),
    },
    {
        "filename": "rtx_ethics_compliance.html",
        "url": "https://www.rtx.com/who-we-are/ethics-and-compliance",
        "snapshot": "rtx_ethics_compliance.md",
        "expected_in_title": ("Ethics", "Compliance"),
    },
    {
        "filename": "doj_rtx_resolution_press_release.html",
        "url": "https://www.justice.gov/archives/opa/pr/raytheon-company-pay-over-950m-connection-defective-pricing-foreign-bribery-and-export",
        "snapshot": "doj_rtx_resolution_press_release.md",
        "expected_in_title": ("Raytheon", "950"),
    },
]


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:200]
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()[:200]
    return ""


def _is_html(content: bytes) -> bool:
    head = content[:8000].lower()
    return b"<html" in head or b"<!doctype html" in head or b"<head" in head


def _validate(content: bytes, title: str, expected: tuple[str, ...]) -> str:
    if len(content) < 500:
        return "fail"
    if not _is_html(content):
        return "fail"
    blob = (title + " " + content[:12000].decode("utf-8", errors="replace")).lower()
    hits = sum(1 for e in expected if e.lower() in blob)
    if hits >= 1:
        return "ok"
    return "warning"


def download_one(item: dict) -> dict:
    url = item["url"]
    path = OUT_DIR / item["filename"]
    snapshot_path = OUT_DIR / item["snapshot"]
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=120) as resp:
            content = resp.read()
        path.write_bytes(content)
        title = _extract_title(content.decode("utf-8", errors="replace"))
        status = _validate(content, title, item["expected_in_title"])
        snapshot_removed = False
        if status in ("ok", "warning") and snapshot_path.exists():
            snapshot_path.unlink()
            snapshot_removed = True
        return {
            "url": url,
            "local_html": f"web_sources/{item['filename']}",
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "detected_title": title,
            "download_status": status,
            "snapshot_removed": snapshot_removed,
            "snapshot": item["snapshot"],
        }
    except Exception as exc:
        return {
            "url": url,
            "local_html": f"web_sources/{item['filename']}",
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "detected_title": "",
            "download_status": "fail",
            "snapshot_removed": False,
            "snapshot": item["snapshot"],
            "error": str(exc),
        }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [download_one(item) for item in DOWNLOADS]
    STATUS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r["download_status"] == "ok")
    warn = sum(1 for r in results if r["download_status"] == "warning")
    fail = sum(1 for r in results if r["download_status"] == "fail")
    print(json.dumps({"ok": ok, "warning": warn, "fail": fail, "total": len(results)}))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
