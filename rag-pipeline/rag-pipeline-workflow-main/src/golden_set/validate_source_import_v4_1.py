"""Validate imported ESG PDF sources for Hansem and Raysolution (v4.1 intake)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]

IMPORTS = [
    {
        "company": "한샘",
        "file_name": "한샘_esg_export_20260608_043142.pdf",
        "source_path": Path(
            r"C:\Users\nguye\Downloads\data-company\3cty\레이시온-한샘\한샘\한샘_esg_export_20260608_043142.pdf"
        ),
        "import_destination": (
            "data/rag_dataset/05_company_export_json/"
            "한샘_dataset_package_20260608T042739/_sources/한샘_esg_export_20260608_043142.pdf"
        ),
    },
    {
        "company": "레이시온",
        "file_name": "레이시온_esg_export_20260608_055704.pdf",
        "source_path": Path(
            r"C:\Users\nguye\Downloads\data-company\3cty\레이시온-한샘\레이시온\레이시온_esg_export_20260608_055704.pdf"
        ),
        "import_destination": (
            "data/rag_dataset/05_company_export_json/"
            "레이시온_dataset_package_20260608T055801/_sources/레이시온_esg_export_20260608_055704.pdf"
        ),
    },
]

REPORT_BODY_MARKERS = (
    "about this report",
    "보고서 개요",
    "ceo 인사말",
    "ceo message",
    "중대성",
    "materiality",
    "gri standard",
    "gri ",
    "목차",
    "table of contents",
    "지속가능",
    "sustainability report",
    "esg report",
    "esg경영",
    "esg 경영",
)

ESG_KEYWORDS = (
    "esg",
    "지속가능",
    "환경",
    "사회",
    "지배구조",
    "governance",
    "온실가스",
    "탄소",
    "중대성",
    "이해관계자",
)

COVERAGE_EXPORT_MARKERS = (
    "esg requirement coverage",
    "compact report shows how many rows",
    "matched by public evidence",
    "coverage ratio",
    "total guide rows",
)

WRONG_DOC_MARKERS = (
    "중소기업 연차보고서",
    "www.mss.go.kr",
    "mss.go.kr",
)

COMPANY_ALIASES = {
    "한샘": ("한샘", "hanssem", "hansem"),
    "레이시온": ("레이시온", "raysolution", "ray solution"),
}


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def score_signals(text: str, company: str) -> Tuple[int, int, int]:
    lower = text.lower()
    company_score = sum(text.count(a) for a in COMPANY_ALIASES.get(company, (company,)))
    esg_score = sum(1 for k in ESG_KEYWORDS if k in lower)
    report_score = sum(1 for m in REPORT_BODY_MARKERS if m in lower)
    esg_signal = esg_score + report_score * 2
    wrong_score = sum(1 for m in WRONG_DOC_MARKERS if m in text)
    return esg_signal, company_score, wrong_score


def validate_pdf(dest: Path, company: str, max_pages: int = 20) -> Dict[str, Any]:
    size_bytes = dest.stat().st_size if dest.exists() else 0
    if not dest.exists():
        return {
            "readability_status": "missing",
            "pages": 0,
            "text_length": 0,
            "esg_signal_score": 0,
            "company_signal_score": 0,
            "preview": "",
            "validation_decision": "reject",
            "validation_reason": "file_not_found_after_import",
            "recommended_next_action": "re-copy source file into package _sources/",
            "size_bytes": size_bytes,
        }

    try:
        reader = PdfReader(str(dest))
        pages = len(reader.pages)
        chunks: List[str] = []
        for page in reader.pages[:max_pages]:
            chunks.append(page.extract_text() or "")
        blob = "\n".join(chunks)
    except Exception as exc:  # noqa: BLE001
        return {
            "readability_status": "unreadable",
            "pages": 0,
            "text_length": 0,
            "esg_signal_score": 0,
            "company_signal_score": 0,
            "preview": "",
            "validation_decision": "reject",
            "validation_reason": f"pdf_read_error:{exc}",
            "recommended_next_action": "inspect source export; re-export PDF or provide alternate SR file",
            "size_bytes": size_bytes,
        }

    text_len = len(blob.strip())
    esg_signal, company_signal, wrong_signal = score_signals(blob, company)
    preview = _norm_ws(blob)[:500]
    lower = blob.lower()
    is_coverage_export = sum(1 for m in COVERAGE_EXPORT_MARKERS if m in lower) >= 2

    if wrong_signal > 0:
        decision = "reject"
        reason = "wrong_document_type_detected"
        action = "replace with actual company ESG/sustainability report PDF"
    elif text_len < 500:
        decision = "reject"
        reason = f"insufficient_extracted_text:{text_len}_chars"
        action = "obtain full SR PDF (current file may be cover/stub only)"
    elif esg_signal < 3:
        decision = "reject"
        reason = f"low_esg_signal:{esg_signal}"
        action = "verify export content; may not be ESG report body"
    elif is_coverage_export:
        decision = "accept_with_warnings"
        reason = "readable_esg_coverage_export_not_full_sustainability_report_body"
        action = (
            "intake pass for pipeline readability; v4.2 re-ingest should treat as "
            "coverage/evidence export — still need actual SR PDF for report-body seeds"
        )
    elif company_signal < 1:
        decision = "accept_with_warnings"
        reason = f"readable_but_low_company_signal:{company_signal}"
        action = "proceed to v4.2 re-ingest with manual company-name check"
    elif esg_signal >= 5 and company_signal >= 2 and text_len >= 2000:
        decision = "accept"
        reason = "readable_esg_report_body_signals_present"
        action = "ready for v4.2 re-ingest via ingest_actual_esg_sources_v3.py or v4.2 wrapper"
    else:
        decision = "accept_with_warnings"
        reason = f"readable_partial_report_body:esg={esg_signal},company={company_signal},len={text_len}"
        action = "proceed to v4.2 re-ingest; review extracted passages during seed build"

    return {
        "readability_status": "readable" if text_len > 0 else "empty_text",
        "pages": pages,
        "text_length": text_len,
        "esg_signal_score": esg_signal,
        "company_signal_score": company_signal,
        "wrong_document_signal": wrong_signal,
        "is_coverage_export": is_coverage_export,
        "preview": preview,
        "validation_decision": decision,
        "validation_reason": reason,
        "recommended_next_action": action,
        "size_bytes": size_bytes,
    }


def build_report(records: List[Dict[str, Any]]) -> str:
    lines = [
        "# Golden Set — Source Import Validation V4.1",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu",
        "",
        "Import 2 PDF ESG từ Downloads vào package workspace và validate khả năng đọc / độ phù hợp.",
        "",
        "## File nào được import",
        "",
    ]
    for r in records:
        lines.append(f"- `{r['file_name']}` ({r['company']}) — {r['size_bytes']} bytes")
    lines.extend(["", "## Import vào đâu", ""])
    for r in records:
        lines.append(f"- **{r['company']}:** `{r['import_destination']}`")

    lines.extend(["", "## Kết quả validation từng file", ""])
    for r in records:
        lines.extend(
            [
                f"### {r['company']} — `{r['file_name']}`",
                "",
                f"- **exists_after_import:** {r['exists_after_import']}",
                f"- **readability:** {r['readability_status']} ({r.get('pages', 0)} pages, {r.get('text_length', 0)} chars extracted)",
                f"- **ESG signal score:** {r['esg_signal_score']}",
                f"- **Company signal score:** {r['company_signal_score']}",
        f"- **verdict:** `{r['validation_decision']}`",
        f"- **document type note:** {'ESG coverage export (not full SR body)' if r.get('is_coverage_export') else 'standard ESG/sustainability signals'}",
        f"- **reason:** {r['validation_reason']}",
                f"- **preview:** {r.get('preview', '')[:300]}…" if r.get("preview") else "- **preview:** (none)",
                "",
            ]
        )

    hs = next(r for r in records if r["company"] == "한샘")
    rx = next(r for r in records if r["company"] == "레이시온")
    lines.extend(
        [
            "## Đánh giá",
            "",
            f"- **한샘 PDF usable cho ingest?** {'Có (coverage export — cần SR body riêng cho seed report-body)' if hs['validation_decision'] in ('accept', 'accept_with_warnings') else 'Không'} — `{hs['validation_decision']}`",
            f"- **레이시온 PDF usable cho ingest?** {'Có (coverage export — cần SR body riêng cho seed report-body)' if rx['validation_decision'] in ('accept', 'accept_with_warnings') else 'Không'} — `{rx['validation_decision']}`",
            "",
            "## Kết luận",
            "",
        ]
    )
    ready = [r for r in records if r["validation_decision"] in ("accept", "accept_with_warnings")]
    blocked = [r for r in records if r["validation_decision"] == "reject"]
    if ready:
        lines.append("**Sẵn sàng re-ingest:**")
        for r in ready:
            lines.append(f"- {r['company']}: `{r['file_name']}` ({r['validation_decision']})")
    if blocked:
        lines.append("")
        lines.append("**Cần xử lý thêm:**")
        for r in blocked:
            lines.append(f"- {r['company']}: {r['validation_reason']} → {r['recommended_next_action']}")

    all_pass = all(r["validation_decision"] in ("accept", "accept_with_warnings") for r in records)
    if all_pass:
        lines.extend(
            [
                "",
                "**Bước kế tiếp (chưa chạy trong task này):** rerun `ingest_actual_esg_sources_v3.py` hoặc wrapper v4.2 re-ingest sau khi cập nhật discovery cho package `_sources/` mới.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    records: List[Dict[str, Any]] = []
    for item in IMPORTS:
        dest = ROOT / item["import_destination"]
        result = validate_pdf(dest, item["company"])
        records.append(
            {
                "file_name": item["file_name"],
                "company": item["company"],
                "import_destination": item["import_destination"],
                "exists_after_import": dest.exists(),
                **result,
            }
        )

    out_json = ROOT / "data/golden_set/v2/source_acquisition/intake_validation_v4_1.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "validation_version": "v4_1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "files": records,
        "summary": {
            "total": len(records),
            "accept": sum(1 for r in records if r["validation_decision"] == "accept"),
            "accept_with_warnings": sum(
                1 for r in records if r["validation_decision"] == "accept_with_warnings"
            ),
            "reject": sum(1 for r in records if r["validation_decision"] == "reject"),
            "ready_for_reingest": all(
                r["validation_decision"] in ("accept", "accept_with_warnings") for r in records
            ),
        },
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = ROOT / "reports/golden_set_source_import_validation_v4_1.md"
    report_path.write_text(build_report(records), encoding="utf-8")

    print(json.dumps(payload["summary"], ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
