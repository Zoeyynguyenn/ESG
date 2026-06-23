from __future__ import annotations

import os
from pathlib import Path

from production_config import repo_root


def sanitize_runtime_env() -> None:
    """Xoa gia tri rong gay loi SDK (vd. OPENAI_BASE_URL='')."""
    for key in ("OPENAI_BASE_URL", "OPENROUTER_BASE_URL"):
        if not (os.getenv(key) or "").strip():
            os.environ.pop(key, None)


def _apply_dotenv_file(path: Path, *, override: bool = False) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            continue
        if override or key not in os.environ:
            os.environ[key] = value


def load_repo_dotenv() -> None:
    """Load .env (+ .env.local) tu repo root."""
    base = repo_root()
    _apply_dotenv_file(base / ".env")
    _apply_dotenv_file(base / ".env.local")
    sanitize_runtime_env()
