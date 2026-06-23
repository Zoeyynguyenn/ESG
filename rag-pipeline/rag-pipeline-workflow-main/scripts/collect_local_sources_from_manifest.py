#!/usr/bin/env python3
"""Collect and parse local collector JSON sources from resolve_local_file_first manifests."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


FINANCIAL_DOC_RE = re.compile(r"^20\d{2}_재무_(CFS|OFS)\.json$")
EMPLOYEE_DOC_RE = re.compile(r"^20\d{2}_empSttus\.json$")
EXECUTIVE_DOC_RE = re.compile(r"^20\d{2}_exctvSttus\.json$")
DIRECTOR_DOC_RE = re.compile(r"^20\d{2}_outcmpnyDrctrNdChangeSttus\.json$")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _slug(text: str) -> str:
    text = text.strip()
    if text.endswith(".json"):
        text = text[:-5]
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._")
    return text or "source"


def _normalize_file_url(file_url: str | None) -> str | None:
    if not file_url:
        return file_url
    parts = file_url.split("/")
    if len(parts) >= 3 and parts[1] == parts[2]:
        parts.pop(1)
    return "/".join(parts)


def _strip_collector_prefix(file_url: str) -> str:
    rel = file_url.strip()
    for prefix in ("colletor-ai/", "collector-ai/"):
        if rel.startswith(prefix):
            rel = rel[len(prefix) :]
    return rel


def _resolve_local_path(file_url: str, downloads_root: Path) -> tuple[Path | None, str | None]:
    rel = _strip_collector_prefix(_normalize_file_url(file_url) or "")
    if not rel:
        return None, "missing_file_url"

    candidates: list[Path] = [downloads_root / rel]
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] == parts[1]:
        candidates.append(downloads_root / Path(*parts[1:]))
    candidates.append(downloads_root / Path(rel).name)

    seen: set[Path] = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        if cand.is_file():
            return cand, None

    filename = Path(rel).name
    matches = sorted(downloads_root.rglob(filename))
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        rel_lower = rel.lower()
        for match in matches:
            if rel_lower in str(match).lower().replace("\\", "/"):
                return match, None
        return matches[0], "ambiguous_filename_match"
    return None, "local_file_not_found"


def _format_amount(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "-":
        return "-"
    if text.isdigit():
        return f"{int(text):,}"
    return text


def _detect_schema(doc_title: str | None, rows: list[dict[str, Any]]) -> str:
    title = doc_title or ""
    if FINANCIAL_DOC_RE.match(title):
        return "dart_financial_statement"
    if EMPLOYEE_DOC_RE.match(title):
        return "dart_employee_status"
    if EXECUTIVE_DOC_RE.match(title):
        return "dart_executive_status"
    if DIRECTOR_DOC_RE.match(title):
        return "dart_board_director_change"
    if rows:
        sample = rows[0]
        if "account_nm" in sample and "thstrm_amount" in sample:
            return "dart_financial_statement"
        if "fo_bbm" in sample and "sexdstn" in sample:
            return "dart_employee_status"
        if "ofcps" in sample and "nm" in sample:
            return "dart_executive_status"
    return "dart_generic_json"


def _record_text_financial(row: dict[str, Any]) -> str:
    parts = [
        f"statement={row.get('sj_nm')}",
        f"account={row.get('account_nm')}",
        f"account_id={row.get('account_id')}",
    ]
    if row.get("account_detail") not in (None, "", "-"):
        parts.append(f"detail={row.get('account_detail')}")
    parts.append(
        f"{row.get('thstrm_nm')}={_format_amount(row.get('thstrm_amount'))} {row.get('currency', 'KRW')}"
    )
    if row.get("frmtrm_nm"):
        parts.append(
            f"{row.get('frmtrm_nm')}={_format_amount(row.get('frmtrm_amount'))} {row.get('currency', 'KRW')}"
        )
    if row.get("bfefrmtrm_nm"):
        parts.append(
            f"{row.get('bfefrmtrm_nm')}={_format_amount(row.get('bfefrmtrm_amount'))} {row.get('currency', 'KRW')}"
        )
    return " | ".join(parts)


def _record_text_employee(row: dict[str, Any]) -> str:
    return " | ".join(
        [
            f"corp={row.get('corp_name')}",
            f"division={row.get('fo_bbm')}",
            f"sex={row.get('sexdstn')}",
            f"regular={row.get('rgllbr_co')}",
            f"contract={row.get('cnttk_co')}",
            f"total={row.get('sm')}",
            f"avg_tenure={row.get('avrg_cnwk_sdytrn')}",
            f"annual_salary={row.get('fyer_salary_totamt')}",
            f"monthly_salary={row.get('jan_salary_am')}",
            f"stlm_dt={row.get('stlm_dt')}",
        ]
    )


def _record_text_executive(row: dict[str, Any]) -> str:
    return " | ".join(
        [
            f"corp={row.get('corp_name')}",
            f"name={row.get('nm')}",
            f"sex={row.get('sexdstn')}",
            f"position={row.get('ofcps')}",
            f"registered_exec={row.get('rgist_exctv_at')}",
            f"full_time={row.get('fte_at')}",
            f"role={str(row.get('chrg_job') or '').replace(chr(10), ' / ')}",
            f"tenure={row.get('hffc_pd')}",
            f"stlm_dt={row.get('stlm_dt')}",
        ]
    )


def _record_text_generic(row: dict[str, Any]) -> str:
    return " | ".join(f"{key}={value}" for key, value in row.items() if value not in (None, "", "-"))


def _record_text(schema: str, row: dict[str, Any]) -> str:
    if schema == "dart_financial_statement":
        return _record_text_financial(row)
    if schema == "dart_employee_status":
        return _record_text_employee(row)
    if schema == "dart_executive_status":
        return _record_text_executive(row)
    return _record_text_generic(row)


def _build_extracted_text(
    *,
    manifest_row: dict[str, Any],
    schema: str,
    rows: list[dict[str, Any]],
    local_path: Path,
) -> tuple[str, list[dict[str, Any]]]:
    doc_title = manifest_row.get("doc_title") or local_path.name
    company_name = manifest_row.get("company_name") or ""
    source_url = manifest_row.get("source_url") or ""
    header_lines = [
        f"company_id: {manifest_row.get('company_id')}",
        f"company_name: {company_name}",
        f"doc_title: {doc_title}",
        f"source_url: {source_url}",
        f"file_url: {manifest_row.get('file_url')}",
        f"schema: {schema}",
        f"local_path: {local_path}",
        "",
    ]

    record_rows: list[dict[str, Any]] = []
    body_lines: list[str] = []

    if schema == "dart_financial_statement":
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get("sj_nm") or "unknown")].append(row)
        bsns_year = rows[0].get("bsns_year") if rows else ""
        body_lines.append(f"# DART financial statement ({doc_title}, year={bsns_year})")
        for sj_nm, group_rows in grouped.items():
            body_lines.append("")
            body_lines.append(f"## {sj_nm}")
            for idx, row in enumerate(group_rows, start=1):
                text = _record_text(schema, row)
                body_lines.append(f"- {text}")
                record_rows.append(
                    {
                        "record_id": f"{_slug(doc_title)}::{sj_nm}::{idx}",
                        "schema": schema,
                        "statement_name": sj_nm,
                        "account_nm": row.get("account_nm"),
                        "account_id": row.get("account_id"),
                        "text": text,
                    }
                )
    else:
        body_lines.append(f"# DART structured source ({doc_title}, schema={schema})")
        for idx, row in enumerate(rows, start=1):
            text = _record_text(schema, row)
            body_lines.append(f"- {text}")
            record_rows.append(
                {
                    "record_id": f"{_slug(doc_title)}::{idx}",
                    "schema": schema,
                    "text": text,
                }
            )

    return "\n".join(header_lines + body_lines).strip() + "\n", record_rows


def _collect_one(
    manifest_row: dict[str, Any],
    *,
    downloads_root: Path,
    output_root: Path,
    copy_raw: bool,
) -> dict[str, Any]:
    file_url = manifest_row.get("file_url") or ""
    doc_title = manifest_row.get("doc_title") or Path(file_url).name
    company_id = manifest_row.get("company_id") or "unknown"
    local_path, resolve_error = _resolve_local_path(file_url, downloads_root)

    result: dict[str, Any] = {
        **manifest_row,
        "collect_status": "fail",
        "resolve_error": resolve_error,
        "local_path": str(local_path) if local_path else None,
        "schema": None,
        "record_count": 0,
        "extracted_chars": 0,
        "artifact_dir": None,
        "extracted_txt": None,
        "records_jsonl": None,
        "source_manifest_json": None,
        "raw_json": None,
    }

    if not local_path:
        return result

    try:
        payload = json.loads(local_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["resolve_error"] = f"json_read_error: {exc}"
        return result

    if not isinstance(payload, list):
        result["resolve_error"] = "expected_json_array"
        return result

    schema = _detect_schema(doc_title, payload)
    extracted_text, record_rows = _build_extracted_text(
        manifest_row=manifest_row,
        schema=schema,
        rows=payload,
        local_path=local_path,
    )

    artifact_dir = output_root / company_id / "local_json" / _slug(doc_title)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    extracted_txt = artifact_dir / "extracted.txt"
    records_jsonl = artifact_dir / "records.jsonl"
    source_manifest_json = artifact_dir / "source_manifest.json"
    raw_json = artifact_dir / "raw.json"

    extracted_txt.write_text(extracted_text, encoding="utf-8")
    _write_jsonl(records_jsonl, record_rows)
    source_manifest_json.write_text(
        json.dumps(
            {
                **manifest_row,
                "schema": schema,
                "record_count": len(payload),
                "resolved_local_path": str(local_path),
                "artifact_dir": str(artifact_dir),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if copy_raw:
        shutil.copy2(local_path, raw_json)

    result.update(
        {
            "collect_status": "ok",
            "resolve_error": None,
            "schema": schema,
            "record_count": len(payload),
            "extracted_chars": len(extracted_text),
            "artifact_dir": str(artifact_dir),
            "extracted_txt": str(extracted_txt),
            "records_jsonl": str(records_jsonl),
            "source_manifest_json": str(source_manifest_json),
            "raw_json": str(raw_json) if copy_raw else None,
        }
    )
    return result


def _load_manifest_rows(input_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for company_dir in sorted(p for p in input_root.iterdir() if p.is_dir()):
        manifest_path = company_dir / "resolve_local_file_first.jsonl"
        if manifest_path.is_file():
            rows.extend(_read_jsonl(manifest_path))
    return rows


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    ok = sum(1 for row in rows if row.get("collect_status") == "ok")
    fail = total - ok
    schema_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        if row.get("collect_status") == "ok":
            schema_counts[str(row.get("schema"))] += 1

    lines = [
        "# Local Source Collect Summary",
        "",
        f"- total: {total}",
        f"- ok: {ok}",
        f"- fail: {fail}",
        "",
        "## Theo schema",
        "",
        "| Schema | Count |",
        "|---|---:|",
    ]
    for schema, count in sorted(schema_counts.items()):
        lines.append(f"| {schema} | {count} |")

    lines.extend(
        [
            "",
            "## Chi tiet",
            "",
            "| Company | Doc title | Status | Schema | Records | Artifact dir |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.get('company_name')} | {row.get('doc_title')} | {row.get('collect_status')} | "
            f"{row.get('schema') or ''} | {row.get('record_count') or 0} | {row.get('artifact_dir') or ''} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-root",
        default="data/source_intake_prep/20260617_goldns_emni",
        help="Source intake prep root containing company resolve_local_file_first manifests",
    )
    parser.add_argument(
        "--downloads-root",
        default=r"C:\Users\nguye\Downloads\data-company\dataset-excel",
        help="Root folder containing collector JSON files referenced by file_url",
    )
    parser.add_argument(
        "--output-root",
        default="data/source_raw/20260617_goldns_emni_local",
        help="Output root for parsed local source artifacts",
    )
    parser.add_argument(
        "--copy-raw",
        action="store_true",
        default=True,
        help="Copy original JSON into artifact dir as raw.json",
    )
    parser.add_argument(
        "--no-copy-raw",
        action="store_false",
        dest="copy_raw",
        help="Do not copy original JSON",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root)
    downloads_root = Path(args.downloads_root)
    output_root = Path(args.output_root)

    manifest_rows = _load_manifest_rows(input_root)
    results = [
        _collect_one(
            row,
            downloads_root=downloads_root,
            output_root=output_root,
            copy_raw=args.copy_raw,
        )
        for row in manifest_rows
    ]

    _write_jsonl(output_root / "collect_status.jsonl", results)
    _write_csv(output_root / "collect_status.csv", results)
    _write_summary(output_root / "README.md", results)

    ok_count = sum(1 for row in results if row.get("collect_status") == "ok")
    print(
        json.dumps(
            {
                "total": len(results),
                "ok": ok_count,
                "fail": len(results) - ok_count,
                "output_root": str(output_root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
