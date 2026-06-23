#!/usr/bin/env python3
"""Chay LangGraph Evidence API staging.

Ví dụ:
  set LANGGRAPH_API_KEY=dev-secret
  python scripts/run_langgraph_evidence_api.py --host 0.0.0.0 --port 8787

Swagger: http://127.0.0.1:8787/docs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _bootstrap_env() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def _port_in_use(port: int) -> int | None:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return port
    return None


def main() -> int:
    _bootstrap_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    if _port_in_use(args.port):
        print(
            f"ERROR: port {args.port} dang duoc dung (API co the da chay).\n"
            f"  - Dung server cu: .\\scripts\\stop_langgraph_evidence_api.ps1\n"
            f"  - Hoac doi port: python scripts/run_langgraph_evidence_api.py --port 8788\n"
            f"  - Hoac dung server dang chay: http://127.0.0.1:{args.port}/docs",
            file=sys.stderr,
        )
        return 1

    import uvicorn

    uvicorn.run(
        "evidence_api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(ROOT / "src"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
