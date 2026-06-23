"""Source / record matching for benchmark eval (company_export_json lane)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Match outcome labels for audit
MATCH_EXACT_RECORD = "exact_record_match"
MATCH_SAME_DOC = "same_doc_match"
MATCH_SPLIT_ALIAS = "split_alias_match"
MATCH_PACKAGE_SPLIT = "package_split_match"
MATCH_PATH_ALIAS = "path_alias_match"
MATCH_NO = "no_match"

RC_RETRIEVAL_ALIAS_MISS = "retrieval_alias_miss"
RC_RETRIEVAL_NO_EVIDENCE = "retrieval_no_evidence"
RC_RETRIEVAL_TRUE_MISS = "retrieval_true_miss"

_RECORD_ID_RE = re.compile(r"record_id:\s*(\S+)", re.I)
_DOC_ID_RE = re.compile(r"doc_id:\s*(\S+)", re.I)
_PACKAGE_TS_RE = re.compile(r"dataset_package_(\d{8}t\d+)", re.I)


def normalize_source(s: str) -> str:
    """Slash, lowercase, Unicode NFKC — comparable paths across encodings."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s).strip())
    s = s.replace("\\", "/")
    s = re.sub(r"/+", "/", s).lower()
    if s.startswith("./"):
        s = s[2:]
    return s


def _package_timestamp(norm: str) -> str:
    m = _PACKAGE_TS_RE.search(norm)
    return m.group(1).lower() if m else ""


def _package_folder(norm: str) -> str:
    m = re.search(r"05_company_export_json/([^/]+)/", norm)
    return m.group(1) if m else ""


def _split_basename(norm: str) -> str:
    if "/splits/" not in norm:
        return ""
    return Path(norm).name


def is_export_json_path(norm: str) -> bool:
    return "05_company_export_json/" in norm


def parse_expected_targets(expected_source: str) -> Dict[str, Any]:
    norm = normalize_source(expected_source)
    return {
        "norm": norm,
        "package_ts": _package_timestamp(norm),
        "package_folder": _package_folder(norm),
        "split": _split_basename(norm),
        "is_split_file": "/splits/" in norm and norm.endswith(".jsonl"),
        "is_export_json": is_export_json_path(norm),
    }


def _parse_chunk_meta(text: str) -> Dict[str, str]:
    rid = (_RECORD_ID_RE.search(text or "") or [None, ""])[1]
    did = (_DOC_ID_RE.search(text or "") or [None, ""])[1]
    return {"record_id": rid.strip(), "doc_id": did.strip()}


def _parse_row_record_hints(row: Dict[str, str]) -> Dict[str, str]:
    """Record/doc id from extracted_field (golden v2) or expected_source tail."""
    exp = row.get("expected_source") or ""
    rid = ""
    did = ""
    field = (row.get("extracted_field") or "").strip()
    if field.startswith("rec_"):
        rid = field
    m = re.search(r"record_id[=:](\S+)", exp, re.I)
    if m:
        rid = m.group(1)
    m = re.search(r"doc_id[=:](\S+)", exp, re.I)
    if m:
        did = m.group(1)
    return {"record_id": rid, "doc_id": did}


def _legacy_aliases(expected_source: str) -> List[str]:
    """ESG / public lane aliases (existing kw_map behaviour)."""
    from eval_scoring_v2 import source_aliases

    return source_aliases(expected_source)


def _legacy_path_match(src_norm: str, aliases: List[str]) -> bool:
    for a in aliases:
        if len(a) < 3:
            continue
        if a in src_norm or src_norm.endswith(a) or a in src_norm.split("/")[-1]:
            return True
    return False


def _package_match(exp: Dict[str, Any], src_norm: str) -> bool:
    """Same export package folder (timestamp) even if Unicode folder name differs."""
    if not exp.get("is_export_json"):
        return False
    ts_exp = exp.get("package_ts") or ""
    ts_src = _package_timestamp(src_norm)
    if ts_exp and ts_src and ts_exp == ts_src:
        return True
    folder_exp = exp.get("package_folder") or ""
    folder_src = _package_folder(src_norm)
    if folder_exp and folder_src and normalize_source(folder_exp) == normalize_source(folder_src):
        return True
    return False


def _match_one_source(
    exp: Dict[str, Any],
    src_norm: str,
    chunk_meta: Dict[str, str],
    row_hints: Dict[str, str],
) -> str:
    if not src_norm:
        return MATCH_NO

    # Record-level (when eval specifies ids)
    if row_hints.get("record_id") and chunk_meta.get("record_id"):
        if row_hints["record_id"] == chunk_meta["record_id"]:
            return MATCH_EXACT_RECORD
    if row_hints.get("doc_id") and chunk_meta.get("doc_id"):
        if row_hints["doc_id"] == chunk_meta["doc_id"]:
            return MATCH_SAME_DOC

    # Export JSON: expected points at splits/*.jsonl — accept same package, any split lane file
    if exp.get("is_export_json") and exp.get("is_split_file"):
        if is_export_json_path(src_norm) and _package_match(exp, src_norm):
            exp_split = exp.get("split") or ""
            src_split = _split_basename(src_norm)
            if exp_split and src_split and exp_split == src_split:
                return MATCH_SPLIT_ALIAS
            if exp_split and src_split and exp_split != src_split:
                # dev.jsonl in eval vs validation.jsonl in corpus — same package content
                return MATCH_PACKAGE_SPLIT
            return MATCH_PACKAGE_SPLIT

    if _package_match(exp, src_norm):
        return MATCH_PACKAGE_SPLIT

    aliases = _legacy_aliases(exp.get("norm", ""))
    if _legacy_path_match(src_norm, aliases):
        return MATCH_PATH_ALIAS

    return MATCH_NO


def match_evidence_to_expected(
    row: Dict[str, str],
    evidence: List[dict],
    *,
    top1_only: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns (hit, match_reason, detail dict for audit).
    top1_only: citation — only rank-1 chunk must match.
    """
    exp = parse_expected_targets(row.get("expected_source", ""))
    row_hints = _parse_row_record_hints(row)
    if not evidence:
        return False, MATCH_NO, {
            "normalized_expected_source": exp["norm"],
            "normalized_top_sources": [],
            "expected_record_id": row_hints.get("record_id", ""),
            "expected_doc_id": row_hints.get("doc_id", ""),
            "match_reason": MATCH_NO,
            "fail_kind": "retrieval_miss",
        }

    scan = evidence[:1] if top1_only else evidence
    norm_tops: List[str] = []
    best_reason = MATCH_NO
    hit = False
    hit_positions: List[int] = []

    for i, e in enumerate(evidence):
        src = e.get("source", "") or ""
        src_norm = normalize_source(src)
        if i < 5:
            norm_tops.append(src_norm)
        meta = _parse_chunk_meta(e.get("text", "") or "")
        reason = _match_one_source(exp, src_norm, meta, row_hints)
        if reason != MATCH_NO:
            hit = True
            best_reason = reason
            if not top1_only:
                hit_positions.append(i)
            if top1_only:
                break
    if top1_only and not norm_tops and evidence:
        norm_tops = [normalize_source(evidence[0].get("source", ""))]

    if not hit and evidence:
        # Near-miss: same package but matcher failed on path string only
        top_norm = normalize_source(evidence[0].get("source", ""))
        if exp.get("is_export_json") and is_export_json_path(top_norm) and _package_match(exp, top_norm):
            fail_kind = "alias_mismatch"
        else:
            fail_kind = "retrieval_miss"
    else:
        fail_kind = "ok" if hit else "retrieval_miss"

    detail = {
        "normalized_expected_source": exp["norm"],
        "normalized_top_sources": norm_tops[:5],
        "expected_record_id": row_hints.get("record_id", ""),
        "expected_doc_id": row_hints.get("doc_id", ""),
        "match_reason": best_reason if hit else MATCH_NO,
        "fail_kind": fail_kind,
        "package_ts_expected": exp.get("package_ts", ""),
        "package_ts_top": _package_timestamp(norm_tops[0]) if norm_tops else "",
        "hit_positions": hit_positions,
        "logic": "export_json_record_then_package_split_then_path_alias",
    }
    return hit, best_reason if hit else MATCH_NO, detail


def retrieval_reason_codes(hit: bool, detail: Dict[str, Any]) -> List[str]:
    if hit:
        return []
    if not detail.get("normalized_top_sources"):
        return [RC_RETRIEVAL_NO_EVIDENCE]
    if detail.get("fail_kind") == "alias_mismatch":
        return [RC_RETRIEVAL_ALIAS_MISS]
    return [RC_RETRIEVAL_TRUE_MISS]
