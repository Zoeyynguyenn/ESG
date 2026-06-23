#!/usr/bin/env python3
"""Smoke: gender-ratio query must abstain (empty items + flags) on Musinsa."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--api-key", default="langgraph-staging-dev")
    parser.add_argument("--company-id", default="musinsa")
    args = parser.parse_args()

    import httpx

    queries = [
        "해당 기업의 남성 비율은 몇 %인가요?",
        "해당 기업의 여성 비율은 몇 %인가요?",
    ]
    headers = {"X-API-Key": args.api_key}
    failed = 0

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=120.0) as client:
        for q in queries:
            resp = client.post(
                "/retrieve",
                json={"query": q, "company_id": args.company_id, "top_k": 5},
                headers=headers,
            )
            data = resp.json()
            ok = (
                resp.status_code == 200
                and data.get("abstain_recommended") is True
                and data.get("no_relevant_evidence") is True
                and data.get("retrieval_confidence") == "low"
                and len(data.get("items") or []) == 0
            )
            print(f"\n{'PASS' if ok else 'FAIL'} {q}")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            if not ok:
                failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
