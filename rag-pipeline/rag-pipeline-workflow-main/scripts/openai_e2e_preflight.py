#!/usr/bin/env python3
"""Preflight OpenAI lane: load .env, verify provider + API key before E2E benchmark."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load_dotenv() -> str | None:
    loaded = None
    for name in (".env.local", ".env"):
        p = BASE / name
        if not p.exists():
            continue
        loaded = str(p)
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k, v)
        break
    if not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ.pop("OPENAI_BASE_URL", None)
    return loaded


def main() -> int:
    dotenv_path = load_dotenv()
    os.environ["RAG_BENCHMARK_LLM_PROVIDER"] = "openai_api"

    sys.path.insert(0, str(BASE / "src"))
    import importlib

    import config as cfg

    importlib.reload(cfg)
    from llm_runtime import detect_llm_runtime

    key = os.getenv("OPENAI_API_KEY", "").strip()
    print("dotenv_loaded_from:", dotenv_path or "(none)")
    print("OPENAI_API_KEY_set:", bool(key))
    if key:
        print("OPENAI_API_KEY_len:", len(key))
        print("OPENAI_API_KEY_suffix:", key[-4:])
    print("OPENAI_BASE_URL:", os.getenv("OPENAI_BASE_URL") or "(default api.openai.com)")
    print("OPENAI_MODEL:", cfg.OPENAI_MODEL)
    print("embedding_model:", "openai:text-embedding-3-small")
    print("ragas_judge:", cfg.OPENAI_MODEL)

    runtime = detect_llm_runtime()
    print("llm_status:", runtime.status)
    print("llm_provider:", runtime.provider)

    if runtime.provider != "openai_api":
        print("PREFLIGHT_FAIL: expected openai_api, got", runtime.provider)
        print("hint: set OPENAI_API_KEY in .env or export before running")
        return 1

    if not key:
        print("PREFLIGHT_FAIL: OPENAI_API_KEY missing after dotenv load")
        return 1

    try:
        import httpx

        r = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30.0,
        )
        if r.status_code == 200:
            print("openai_api_check: ok (models list)")
            return 0
        print("openai_api_check: fail http", r.status_code)
        print("body_snip:", r.text[:240].replace("\n", " "))
        return 1
    except Exception as exc:
        print("openai_api_check: error", type(exc).__name__, str(exc)[:200])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
