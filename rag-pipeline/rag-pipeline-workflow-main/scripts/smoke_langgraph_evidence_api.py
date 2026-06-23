#!/usr/bin/env python3
"""Smoke test LangGraph Evidence API (in-process hoac server remote)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def _print_retrieve_case(client, body: dict, label: str) -> bool:
    resp = client.post("/retrieve", json=body)
    print(f"\n{label} POST /retrieve -> {resp.status_code}")
    data = resp.json()
    if resp.status_code == 404:
        print(json.dumps(data, ensure_ascii=True, indent=2))
        return body.get("company_id") == "unknown_co"
    if resp.status_code != 200:
        print(data)
        return False
    items = data.get("items") or []
    print(f"items={len(items)}")
    if items:
        first = items[0]
        print(
            json.dumps(
                {
                    "score": first.get("score"),
                    "confidence": first.get("confidence"),
                    "record_id": first.get("record_id"),
                    "text_preview": (first.get("text") or "")[:100],
                },
                ensure_ascii=True,
                indent=2,
            )
        )
    return True


def run_inprocess() -> int:
    from fastapi.testclient import TestClient

    from evidence_api.app import app

    client = TestClient(app)

    companies = client.get("/companies")
    print("GET /companies", companies.status_code, companies.json())

    health = client.get("/health")
    health_body = health.json()
    print("GET /health", health.status_code, health_body)
    if health.status_code != 200:
        return 1
    if not health_body.get("rerank_enabled"):
        print("FAIL: /health rerank_enabled=false (expected Jina rerank ON in langgraph_staging.yaml)")
        return 1

    indexed = [x["company_id"] for x in companies.json().get("items", []) if x.get("indexed")]
    print("indexed:", indexed)

    failed = 0
    for cid in ["musinsa", "rayshion", "hanssem"]:
        if cid not in indexed:
            print(f"WARN: {cid} chua indexed — bo qua retrieve test")
            failed += 1
            continue
        ok = _print_retrieve_case(
            client,
            {"query": "ESG sustainability report", "company_id": cid, "top_k": 5},
            cid,
        )
        if not ok:
            failed += 1

    if "nexteye" in indexed:
        if not _print_retrieve_case(
            client,
            {"query": "ticker stock code", "company_id": "nexteye", "top_k": 3},
            "nexteye (legacy)",
        ):
            failed += 1
    else:
        print("WARN: nexteye legacy cache khong co — bo qua")

    if not _print_retrieve_case(
        client,
        {"query": "test", "company_id": "unknown_co", "top_k": 3},
        "unknown_co",
    ):
        failed += 1

    return 1 if failed else 0


def run_remote(base_url: str, api_key: str) -> int:
    import httpx

    headers = {"X-API-Key": api_key} if api_key else {}
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=60.0) as client:
        companies = client.get("/companies", headers=headers)
        print("GET /companies", companies.status_code, companies.text[:500])
        health = client.get("/health", headers=headers)
        print("GET /health", health.status_code, health.text[:500])
        resp = client.post(
            "/retrieve",
            json={"query": "ESG", "company_id": "musinsa", "top_k": 3},
            headers=headers,
        )
        preview = resp.text[:800].encode("ascii", errors="backslashreplace").decode("ascii")
        print("POST /retrieve musinsa", resp.status_code, preview)
    return 0 if health.status_code == 200 and resp.status_code == 200 else 1


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()
    if args.base_url:
        return run_remote(args.base_url, args.api_key)
    return run_inprocess()


if __name__ == "__main__":
    raise SystemExit(main())
