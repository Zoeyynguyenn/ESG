#!/usr/bin/env python3
"""Direct package/index audit for Musinsa headcount GT (no API retrieve)."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

PACKAGE = "무신사_dataset_package_20260608T092823"
PKG_ROOT = ROOT / "data" / "rag_dataset" / "05_company_export_json" / PACKAGE

HEADCOUNT_CTX = re.compile(
    r"(구성원|임직원|직원|인원|종업원|근로자|고용).{0,40}(1891|1,891|1\.891)"
    r"|(1891|1,891|1\.891).{0,40}(구성원|임직원|직원|인원|종업원|근로자|명)"
    r"|1891\s*명|1,891\s*명",
    re.DOTALL,
)


@dataclass
class Hit:
    lane: str
    path: str
    record_id: str
    doc_id: str
    source_url: str
    match_kind: str
    snippet: str


def _iter_jsonl_files() -> List[tuple[str, Path]]:
    out: List[tuple[str, Path]] = []
    splits = PKG_ROOT / "splits"
    if splits.exists():
        for p in sorted(splits.glob("*.jsonl")):
            out.append((f"splits/{p.name}", p))
    records = PKG_ROOT / "records"
    if records.exists():
        for p in sorted(records.glob("*.jsonl")):
            out.append((f"records/{p.name}", p))
    return out


def _scan_text_file(lane: str, path: Path) -> List[Hit]:
    hits: List[Hit] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return hits
    for pat, kind in [
        ("1891명", "1891명"),
        ("1,891명", "1,891명"),
        ("1891", "1891_substring"),
    ]:
        idx = 0
        while True:
            i = text.find(pat, idx)
            if i < 0:
                break
            snippet = text[max(0, i - 60) : i + len(pat) + 60].replace("\n", " ")
            hits.append(
                Hit(
                    lane=lane,
                    path=str(path.relative_to(ROOT)).replace("\\", "/"),
                    record_id="",
                    doc_id="",
                    source_url="",
                    match_kind=kind,
                    snippet=snippet,
                )
            )
            idx = i + len(pat)
    return hits


def _scan_jsonl(lane: str, path: Path) -> List[Hit]:
    hits: List[Hit] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = obj.get("text") or obj.get("content") or ""
            if not text and isinstance(obj.get("chunks"), list):
                text = "\n".join(str(c) for c in obj["chunks"])
            rid = str(obj.get("record_id") or "")
            did = str(obj.get("doc_id") or "")
            src = str(obj.get("source_url") or obj.get("url") or "")
            role = str(obj.get("record_role") or "")
            lane_tag = f"{lane}|role={role}"
            for pat, kind in [
                ("1891명", "1891명"),
                ("1,891명", "1,891명"),
                ("1891", "1891_substring"),
            ]:
                if pat in text:
                    for m in re.finditer(re.escape(pat), text):
                        i = m.start()
                        snippet = text[max(0, i - 80) : i + len(pat) + 80].replace("\n", " ")
                        hits.append(
                            Hit(
                                lane=lane_tag,
                                path=str(path.relative_to(ROOT)).replace("\\", "/"),
                                record_id=rid,
                                doc_id=did,
                                source_url=src,
                                match_kind=kind,
                                snippet=snippet,
                            )
                        )
            if HEADCOUNT_CTX.search(text):
                m = HEADCOUNT_CTX.search(text)
                assert m
                i = m.start()
                snippet = text[max(0, i - 80) : i + 120].replace("\n", " ")
                hits.append(
                    Hit(
                        lane=lane_tag,
                        path=str(path.relative_to(ROOT)).replace("\\", "/"),
                        record_id=rid,
                        doc_id=did,
                        source_url=src,
                        match_kind="headcount_context",
                        snippet=snippet,
                    )
                )
    return hits


def audit_package() -> Dict[str, Any]:
    pkg_hits: List[Hit] = []
    for lane, path in _iter_jsonl_files():
        pkg_hits.extend(_scan_jsonl(lane, path))

    sources = PKG_ROOT / "_sources"
    source_hits: List[Hit] = []
    if sources.exists():
        for p in sorted(sources.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json", ".jsonl", ".html"}:
                rel = f"_sources/{p.relative_to(sources).as_posix()}"
                if p.suffix.lower() == ".jsonl":
                    source_hits.extend(_scan_jsonl(rel, p))
                else:
                    source_hits.extend(_scan_text_file(rel, p))

    full_only = [h for h in pkg_hits if "/splits/full.jsonl" in h.path]
    records_lane = [h for h in pkg_hits if "/records/" in h.path]
    anchor_1891myeong = [h for h in pkg_hits if h.match_kind in ("1891명", "1,891명")]
    anchor_ctx = [h for h in pkg_hits if h.match_kind == "headcount_context"]

    if anchor_1891myeong or anchor_ctx:
        cls = "gt_present_in_package_and_indexable" if full_only else "gt_present_only_outside_indexed_lane"
    elif source_hits and (any(h.match_kind in ("1891명", "1,891명") for h in source_hits) or any(h.match_kind == "headcount_context" for h in source_hits)):
        cls = "gt_present_only_outside_indexed_lane"
    else:
        cls = "gt_not_present"

    return {
        "package": PACKAGE,
        "package_root": str(PKG_ROOT),
        "classification": cls,
        "counts": {
            "jsonl_hits_total": len(pkg_hits),
            "full_jsonl_hits": len(full_only),
            "records_lane_hits": len(records_lane),
            "_sources_hits": len(source_hits),
            "1891명_in_package": len(anchor_1891myeong),
            "headcount_context_in_package": len(anchor_ctx),
            "1891_substring_in_full": len([h for h in full_only if h.match_kind == "1891_substring"]),
        },
        "anchor_1891myeong": [asdict(h) for h in anchor_1891myeong[:20]],
        "headcount_context": [asdict(h) for h in anchor_ctx[:20]],
        "full_jsonl_1891_substring_sample": [asdict(h) for h in full_only if h.match_kind == "1891_substring"][:10],
        "_sources_sample": [asdict(h) for h in source_hits[:15]],
    }


def audit_index() -> Dict[str, Any]:
    from evidence_api.env_bootstrap import load_repo_dotenv
    from evidence_api.staging_config import apply_company_env, company_cfg, load_staging_config
    from production_config import index_dir, production_cache_key

    load_repo_dotenv()
    cfg = load_staging_config()
    cc = company_cfg(cfg, "musinsa")
    apply_company_env(cfg, "musinsa", base_dir=ROOT)
    idx = index_dir(cc)
    bm25_path = idx / "bm25_corpus.json"

    bm25_hits: List[Dict[str, Any]] = []
    bm25_chunk_count = 0
    if bm25_path.exists():
        data = json.loads(bm25_path.read_text(encoding="utf-8"))
        chunks = data if isinstance(data, list) else data.get("chunks", [])
        bm25_chunk_count = len(chunks)
        for i, c in enumerate(chunks):
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            src = c.get("source", "") if isinstance(c, dict) else ""
            for pat, kind in [("1891명", "1891명"), ("1,891명", "1,891명"), ("1891", "1891_substring")]:
                if pat in text:
                    pos = text.find(pat)
                    bm25_hits.append(
                        {
                            "chunk_index": i,
                            "match_kind": kind,
                            "source": src,
                            "snippet": text[max(0, pos - 80) : pos + len(pat) + 80].replace("\n", " "),
                        }
                    )

    qdrant_path = idx / "qdrant_db"
    return {
        "index_dir": str(idx),
        "cache_key": production_cache_key(cc),
        "bm25_path": str(bm25_path),
        "bm25_exists": bm25_path.exists(),
        "qdrant_path": str(qdrant_path),
        "qdrant_exists": qdrant_path.exists(),
        "bm25_chunk_count": bm25_chunk_count,
        "bm25_hits": bm25_hits,
        "bm25_1891myeong_count": sum(1 for h in bm25_hits if h["match_kind"] in ("1891명", "1,891명")),
        "bm25_1891_substring_count": sum(1 for h in bm25_hits if h["match_kind"] == "1891_substring"),
    }


def main() -> int:
    pkg = audit_package()
    idx = audit_index()
    out_pkg = ROOT / "reports" / "musinsa_headcount_gt_audit.json"
    out_idx = ROOT / "reports" / "musinsa_headcount_index_audit.json"
    out_pkg.parent.mkdir(parents=True, exist_ok=True)
    out_pkg.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    out_idx.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    print("package classification:", pkg["classification"])
    print("1891명 in package:", pkg["counts"]["1891명_in_package"])
    print("1891명 in BM25 index:", idx["bm25_1891myeong_count"])
    print("1891 substring in BM25:", idx["bm25_1891_substring_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
