from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from production_config import apply_production_env, index_dir, index_ready, repo_root

DEFAULT_STAGING_CONFIG = "configs/langgraph_staging.yaml"


def load_staging_config(path: str | Path | None = None) -> Dict[str, Any]:
    cfg_path = repo_root() / (path or os.getenv("LANGGRAPH_STAGING_CONFIG", DEFAULT_STAGING_CONFIG))
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def company_registry(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return dict(cfg.get("registry") or {})


def company_cfg(cfg: Dict[str, Any], company_id: str) -> Dict[str, Any]:
    reg = company_registry(cfg)
    if company_id not in reg:
        raise KeyError(company_id)
    out = deepcopy(cfg)
    entry = reg[company_id]
    out["stack"] = deepcopy(cfg["stack"])
    out["stack"]["company_filter"] = entry["package"]
    if entry.get("lane"):
        out["stack"]["lane"] = entry["lane"]
    if entry.get("corpus_version"):
        out["stack"]["corpus_version"] = entry["corpus_version"]
    if entry.get("benchmark_language"):
        out["stack"]["benchmark_language"] = entry["benchmark_language"]
    out["_company_id"] = company_id
    out["_record_split"] = entry.get("record_split", "full")
    out["_legacy_cache_only"] = bool(entry.get("legacy_cache_only"))
    return out


def list_registry_companies(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    ready_set = set(indexed_companies(cfg)[0])
    items: List[Dict[str, Any]] = []
    for company_id, entry in sorted(company_registry(cfg).items()):
        items.append(
            {
                "company_id": company_id,
                "indexed": company_id in ready_set,
                "record_split": entry.get("record_split", "full"),
                "legacy_cache_only": bool(entry.get("legacy_cache_only")),
            }
        )
    return items


def package_jsonl_paths(base: Path, package: str, split: str) -> List[Path]:
    if package.startswith("06_rtx") or split == "rtx_chunked":
        rtx = base / "data" / "rag_dataset" / package / "chunks" / "rtx_chunked_corpus.jsonl"
        return [rtx] if rtx.exists() else []
    root = base / "data" / "rag_dataset" / "05_company_export_json" / package
    paths = [root / "splits" / f"{split}.jsonl"]
    records_dir = root / "records"
    if records_dir.exists():
        paths.extend(sorted(records_dir.glob("*.jsonl")))
    return paths


def apply_company_env(cfg: Dict[str, Any], company_id: str, *, base_dir: Path | None = None) -> Tuple[Dict[str, Any], Path]:
    """Apply RAG env cho mot company staging ma khong doi production default."""
    base = base_dir or repo_root()
    company = company_cfg(cfg, company_id)
    os.environ["RAG_METADATA_AWARE_RETRIEVAL"] = "false"
    manifest = apply_production_env(company, base_dir=base)
    from evidence_api.env_bootstrap import sanitize_runtime_env

    sanitize_runtime_env()
    return company, manifest


def reset_retrieval_runtime_caches() -> None:
    from production_config import sync_runtime_config_paths

    sync_runtime_config_paths()
    import retrieval_v3 as r3

    r3._bm25_index = None
    r3._corpus_chunks = None
    r3._reranker = None
    r3._rerank_status = "not_loaded"
    r3._rerank_effective_model = ""


def indexed_companies(cfg: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    ready: List[str] = []
    pending: List[str] = []
    for company_id in company_registry(cfg):
        try:
            ccfg = company_cfg(cfg, company_id)
            if index_ready(ccfg):
                ready.append(company_id)
            else:
                pending.append(company_id)
        except KeyError:
            pending.append(company_id)
    return ready, pending


def company_index_path(cfg: Dict[str, Any], company_id: str) -> Path:
    return index_dir(company_cfg(cfg, company_id))
