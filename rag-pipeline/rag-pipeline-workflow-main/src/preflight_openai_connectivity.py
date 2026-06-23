"""Preflight OpenAI connectivity checks (DNS, TCP, HTTPS) for benchmark readiness."""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_TARGETS = [
    {"host": "api.openai.com", "port": 443, "https_url": "https://api.openai.com/v1/models"},
    {
        "host": "openaipublic.blob.core.windows.net",
        "port": 443,
        "https_url": "https://openaipublic.blob.core.windows.net",
    },
]


def _load_dotenv(base_dir: Path) -> None:
    for name in (".env", ".env.local"):
        p = base_dir / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            key = k.strip()
            val = v.strip().strip('"').strip("'")
            if not key or not val:
                continue
            os.environ.setdefault(key, val)
    if not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ.pop("OPENAI_BASE_URL", None)


def _dns_check(host: str) -> Tuple[bool, str, List[str]]:
    try:
        infos = socket.getaddrinfo(host, None)
        ips = sorted({i[4][0] for i in infos if i and i[4]})
        return True, "ok", ips
    except Exception as exc:
        return False, f"dns_error:{exc}", []


def _tcp_check(host: str, port: int, timeout: float) -> Tuple[bool, str, float]:
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            ms = (time.perf_counter() - t0) * 1000
            return True, "ok", round(ms, 1)
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000
        return False, f"tcp_error:{exc}", round(ms, 1)


def _tls_check(host: str, port: int, timeout: float) -> Tuple[bool, str]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True, "ok"
    except Exception as exc:
        return False, f"tls_error:{exc}"


def _https_check(url: str, timeout: float, api_key: str = "") -> Tuple[bool, str, int | None]:
    try:
        import requests

        headers = {}
        if "api.openai.com" in url and api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = requests.get(url, timeout=timeout, headers=headers)
        code = r.status_code
        # For OpenAI endpoint, 200/401/403 means network path works.
        if "api.openai.com" in url:
            ok = code in (200, 401, 403)
        else:
            ok = 200 <= code < 500
        return ok, f"http_status:{code}", code
    except Exception as exc:
        return False, f"https_error:{exc}", None


def run_checks(timeout: float, targets: List[Dict[str, Any]], api_key: str = "") -> Dict[str, Any]:
    rows = []
    for t in targets:
        host = t["host"]
        port = int(t.get("port", 443))
        https_url = t.get("https_url", f"https://{host}")

        dns_ok, dns_msg, ips = _dns_check(host)
        tcp_ok, tcp_msg, tcp_ms = _tcp_check(host, port, timeout)
        tls_ok, tls_msg = _tls_check(host, port, timeout) if tcp_ok else (False, "tls_skipped_no_tcp")
        https_ok, https_msg, http_status = _https_check(https_url, timeout, api_key=api_key)

        rows.append(
            {
                "host": host,
                "port": port,
                "dns_ok": dns_ok,
                "dns_msg": dns_msg,
                "ips": ips,
                "tcp_ok": tcp_ok,
                "tcp_msg": tcp_msg,
                "tcp_ms": tcp_ms,
                "tls_ok": tls_ok,
                "tls_msg": tls_msg,
                "https_url": https_url,
                "https_ok": https_ok,
                "https_msg": https_msg,
                "http_status": http_status,
            }
        )
    return {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "timeout_sec": timeout,
        "api_key_present": bool(api_key),
        "targets": rows,
    }


def write_markdown(report: Dict[str, Any], out_md: Path) -> None:
    lines = [
        "# OpenAI Connectivity Preflight",
        "",
        f"- checked_at: `{report['checked_at']}`",
        f"- timeout_sec: `{report['timeout_sec']}`",
        f"- openai_api_key_present: `{report['api_key_present']}`",
        "",
        "| host | port | dns | tcp | tls | https | note |",
        "|---|---:|---|---|---|---|---|",
    ]
    for t in report["targets"]:
        note = "; ".join(
            [
                t["dns_msg"],
                t["tcp_msg"],
                t["tls_msg"],
                t["https_msg"],
            ]
        )
        lines.append(
            f"| `{t['host']}` | {t['port']} | {t['dns_ok']} | {t['tcp_ok']} | {t['tls_ok']} | {t['https_ok']} | {note[:140]} |"
        )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-sec", type=float, default=8.0)
    parser.add_argument("--out-json", default="reports/openai_connectivity_preflight.json")
    parser.add_argument("--out-md", default="reports/openai_connectivity_preflight.md")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    _load_dotenv(base_dir)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    report = run_checks(args.timeout_sec, DEFAULT_TARGETS, api_key=api_key)

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, out_md)

    print(json.dumps({"json": str(out_json), "md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
