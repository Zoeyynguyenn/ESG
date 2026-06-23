"""Raw source audit v4.2 for Musinsa and Raysolution general data folders."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]

AUDIT_DIRS = {
    "무신사": Path(r"C:\Users\nguye\Downloads\data-company\무신사_일반자료_20260430"),
    "레이시온": Path(r"C:\Users\nguye\Downloads\data-company\레이시온_일반자료_20260502"),
}

PRIORITY_PARTS = (
    "09_기타/에이전트다운로더/IR자료",
    "09_기타/에이전트다운로더/기타",
    "02_재무_신용/DART_원본문서",
)

ESG_MARKERS = (
    "impact report",
    "임팩트 리포트",
    "sustainability report",
    "지속가능경영보고서",
    "esg report",
    "gri standard",
    "중대성",
    "materiality",
    "ceo message",
    "ceo 인사말",
)

FINANCIAL_MARKERS = (
    "사업보고서",
    "분기보고서",
    "반기보고서",
    "감사보고서",
    "annual report",
    "form 10-k",
    "10-k",
    "재무제표",
    "consolidated statements",
)

ANALYST_MARKERS = (
    "기업분석",
    "증권",
    "research",
    "investment opinion",
    "목표주가",
    "the game changer",
)

WRONG_COMPANY_MARKERS = {
    "레이시온": (
        "rtx corporation",
        "raytheon technologies",
        "patriot",
        "tomahawk",
        "department of war",
        "form 10-k",
    ),
}

COMPANY_ALIASES = {
    "무신사": ("무신사", "musinsa"),
    "레이시온": ("레이시온", "raysolution", "레이 솔루션"),
}


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _read_text_preview(path: Path, limit: int = 4000) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(path))
            chunks = []
            for page in reader.pages[:8]:
                chunks.append(page.extract_text() or "")
            return _norm("\n".join(chunks))[:limit]
        except Exception as exc:  # noqa: BLE001
            return f"[pdf_read_error:{exc}]"
    if suffix in {".html", ".htm"}:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            raw = path.read_text(encoding="cp949", errors="ignore")
        return _strip_html(raw)[:limit]
    if suffix == ".xml":
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            raw = path.read_text(encoding="cp949", errors="ignore")
        # strip tags lightly for preview
        plain = re.sub(r"<[^>]+>", " ", raw)
        return _norm(plain)[:limit]
    if suffix in {".md", ".json"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        except OSError:
            return ""
    return ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _title_from_path(path: Path) -> str:
    return path.name


def _title_from_preview(path: Path, preview: str) -> str:
    if path.suffix.lower() == ".xml" and "_" in path.parent.name:
        return path.parent.name
    m = re.search(r"(?i)(impact report|임팩트|sustainability|지속가능|10-k|사업보고서|감사보고서|기업분석)", preview)
    if m:
        return m.group(0)
    return path.stem


def score_signals(preview: str, company: str) -> Tuple[int, int, int]:
    lower = preview.lower()
    company_score = sum(preview.count(a) for a in COMPANY_ALIASES.get(company, (company,)))
    esg_score = sum(1 for m in ESG_MARKERS if m.lower() in lower)
    fin_score = sum(1 for m in FINANCIAL_MARKERS if m.lower() in lower)
    wrong = sum(1 for m in WRONG_COMPANY_MARKERS.get(company, ()) if m in lower)
    return esg_score, company_score, fin_score + wrong * 3


def _candidate_row(
    path: Path,
    company: str,
    preview: str,
    rel: str,
    download_meta: Optional[Dict[str, Any]],
    title: str,
    esg_score: int,
    company_score: int,
    fin_or_wrong: int,
    candidate_class: str,
    why: str,
    recommended: str,
) -> Dict[str, Any]:
    return {
        "company": company,
        "path": str(path),
        "relative_path": rel,
        "file_name": path.name,
        "title_headline": title,
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "company_signal_score": company_score,
        "esg_report_body_signal_score": esg_score,
        "financial_only_signal": fin_or_wrong,
        "preview": preview[:400],
        "candidate_class": candidate_class,
        "why_candidate": why,
        "recommended_action": recommended,
        "download_meta": download_meta,
        "priority_tier": (
            1
            if any(p.replace("/", "\\") in rel.replace("/", "\\") for p in PRIORITY_PARTS)
            else 2
        ),
    }


def classify_candidate(
    path: Path,
    company: str,
    preview: str,
    rel: str,
    download_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    lower = preview.lower()
    rel_lower = rel.lower()
    esg_score, company_score, fin_or_wrong = score_signals(preview, company)

    title = _title_from_preview(path, preview)
    why = []
    recommended = "exclude_from_esg_golden_set"

    if download_meta:
        desc = (download_meta.get("description") or "").lower()
        if company == "레이시온" and ("rtx corporation" in desc or "10-k" in desc):
            candidate_class = "financial_report_or_dart_only"
            why.append("SEC RTX Corporation 10-K (US Raytheon) — wrong company vs Korean 레이시온")
            recommended = "exclude; do not import for Korean Raysolution Golden Set"
            return _candidate_row(
                path, company, preview, rel, download_meta, title,
                esg_score, company_score, fin_or_wrong,
                candidate_class, "; ".join(why), recommended,
            )

    if any(m in lower for m in WRONG_COMPANY_MARKERS.get(company, ())) or (
        company == "레이시온" and "rtx-" in path.name.lower()
    ):
        candidate_class = "unknown_needs_manual_check"
        why.append("cross-company contamination: US RTX/Raytheon not Korean target")
        recommended = "exclude; re-acquire Korean Raysolution sources separately"
    elif "07_뉴스" in rel or "news_" in path.name.lower():
        candidate_class = "news_or_press"
        why.append("captured news article HTML")
    elif "08_웹사이트" in rel or "홈페이지" in path.name:
        candidate_class = "website_capture"
        why.append("e-commerce / corporate site capture")
        if "newsroom.musinsa" in lower or "/impact" in lower:
            why.append("contains newsroom/impact nav but not report PDF body")
    elif "02_재무_신용/DART" in rel or path.suffix.lower() == ".xml":
        candidate_class = "financial_report_or_dart_only"
        why.append(f"DART filing: {path.parent.name if path.parent else path.name}")
        if esg_score > 0 and "지속가능경영보고서" not in rel_lower:
            why.append("incidental ESG keyword only (not standalone SR)")
    elif path.suffix.lower() == ".pdf":
        if any(m in lower for m in ANALYST_MARKERS) or (
            download_meta and "증권" in (download_meta.get("description") or "")
        ):
            candidate_class = "financial_report_or_dart_only"
            why.append("sell-side equity research PDF, not company ESG report")
        elif "입찰" in rel or "downloadfile.do" in path.name.lower():
            candidate_class = "portal_or_navigation_noise"
            why.append("public procurement bid document")
        elif esg_score >= 3 and company_score >= 2:
            candidate_class = "likely_actual_esg_report"
            why.append("strong ESG report-body markers in PDF preview")
            recommended = "import_to_package_sources_next"
        elif "impact" in lower or "임팩트" in preview:
            candidate_class = "likely_company_impact_report"
            why.append("impact report signals in preview")
            recommended = "import_to_package_sources_next"
        else:
            candidate_class = "unknown_needs_manual_check"
            why.append("PDF without clear ESG report-body markers")
    elif esg_score >= 4 and company_score >= 2 and fin_or_wrong == 0:
        candidate_class = "likely_actual_esg_report"
        why.append("ESG/report-body text signals")
        recommended = "import_to_package_sources_next"
    elif "portal" in lower or "민원" in preview or "navigation" in lower:
        candidate_class = "portal_or_navigation_noise"
        why.append("portal/listing chrome")
    else:
        candidate_class = "unknown_needs_manual_check"
        why.append("insufficient ESG report-body evidence in preview")

    return _candidate_row(
        path, company, preview, rel, download_meta, title,
        esg_score, company_score, fin_or_wrong,
        candidate_class, "; ".join(why), recommended,
    )


def load_download_meta(folder: Path) -> Dict[str, Dict[str, Any]]:
    meta_path = folder / "09_기타/에이전트다운로더/다운로드목록.json"
    out: Dict[str, Dict[str, Any]] = {}
    if not meta_path.exists():
        return out
    for row in json.loads(meta_path.read_text(encoding="utf-8")):
        out[row.get("filename", "")] = row
    return out


def audit_company(company: str, folder: Path) -> Dict[str, Any]:
    download_meta_by_name = load_download_meta(folder)
    candidates: List[Dict[str, Any]] = []
    all_files: List[Path] = []

    if not folder.exists():
        return {
            "folder": str(folder),
            "exists": False,
            "candidates": [],
            "summary": {},
        }

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        all_files.append(path)
        suffix = path.suffix.lower()
        if suffix not in {".pdf", ".html", ".htm", ".xml", ".md", ".json"}:
            continue
        rel = str(path.relative_to(folder)).replace("\\", "/")
        # skip large json logs except download list handled separately
        if suffix == ".json" and "다운로드목록" not in path.name:
            if "DART" not in rel and "MANIFEST" not in rel:
                continue
        preview = _read_text_preview(path)
        meta = download_meta_by_name.get(path.name)
        row = classify_candidate(path, company, preview, rel, meta)
        candidates.append(row)

    classes = [c["candidate_class"] for c in candidates]
    likely_actual = [c for c in candidates if c["candidate_class"] == "likely_actual_esg_report"]
    likely_impact = [c for c in candidates if c["candidate_class"] == "likely_company_impact_report"]
    financial = [c for c in candidates if c["candidate_class"] == "financial_report_or_dart_only"]
    manual = [c for c in candidates if c["candidate_class"] == "unknown_needs_manual_check"]

    best = sorted(
        [c for c in candidates if c["candidate_class"] in (
            "likely_actual_esg_report",
            "likely_company_impact_report",
        )],
        key=lambda x: (-x["esg_report_body_signal_score"], -x["company_signal_score"]),
    )

    # secondary: newsroom capture for musinsa
    secondary = [
        c
        for c in candidates
        if c["candidate_class"] == "website_capture"
        and ("newsroom" in c["preview"].lower() or "impact" in c["relative_path"].lower())
    ]

    return {
        "folder": str(folder),
        "exists": True,
        "total_files": len(all_files),
        "audited_documents": len(candidates),
        "candidates": candidates,
        "best_candidates": (best or secondary)[:5],
        "likely_actual_report_count": len(likely_actual) + len(likely_impact),
        "likely_financial_only_count": len(financial),
        "needs_manual_check": [c["relative_path"] for c in manual[:15]],
        "class_counts": {k: classes.count(k) for k in sorted(set(classes))},
    }


def build_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# Golden Set — Raw Source Audit V4.2",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Mục tiêu",
        "",
        "Audit raw folders ngoài package để tìm **actual ESG / Impact / Sustainability report** source gốc.",
        "",
        "## Thư mục đã audit",
        "",
    ]
    for co, data in payload["companies"].items():
        lines.append(f"- **{co}:** `{data['folder']}` ({data.get('total_files', 0)} files total)")

    for co in ("무신사", "레이시온"):
        data = payload["companies"][co]
        eng = "Musinsa" if co == "무신사" else "Raysolution"
        lines.extend(["", f"## Kết quả cho {eng}", ""])
        best = data.get("best_candidates") or []
        if best:
            lines.append("### Candidate tốt nhất")
            for b in best[:3]:
                lines.append(
                    f"- `{b['relative_path']}` — **{b['candidate_class']}** — {b['why_candidate']}"
                )
        else:
            lines.append("### Candidate tốt nhất")
            lines.append("- **Không có** file `likely_actual_esg_report` / `likely_company_impact_report`.")

        lines.append("")
        lines.append("### Financial / news / web capture (không phải SR body)")
        fin_samples = [
            c
            for c in data.get("candidates", [])
            if c["candidate_class"]
            in ("financial_report_or_dart_only", "news_or_press", "website_capture", "portal_or_navigation_noise")
        ][:6]
        for c in fin_samples:
            lines.append(f"- `{c['relative_path']}` — {c['candidate_class']}")

        has_real = data.get("likely_actual_report_count", 0) > 0
        lines.append("")
        if co == "무신사":
            lines.append(
                f"**Có Impact Report / ESG Report thật?** {'Có candidate yếu (newsroom capture)' if not has_real and best else 'Không' if not has_real else 'Có PDF candidate'}"
            )
        else:
            lines.append(
                f"**Có Sustainability / ESG Report thật?** {'Không' if not has_real else 'Có candidate'}"
            )
            if data.get("class_counts", {}).get("unknown_needs_manual_check"):
                lines.append(
                    "- **Cảnh báo:** folder bị **cross-company contamination** (US RTX/Raytheon), không phải Korean 레이시온 target."
                )

    lines.extend(["", "## Audit ưu tiên — PDF / agent downloader", ""])
    for co in ("무신사", "레이시온"):
        data = payload["companies"][co]
        pdfs = [
            c for c in data.get("candidates", [])
            if "09_기타/에이전트다운로더" in c["relative_path"]
            and c["relative_path"].endswith((".pdf", ".html"))
        ]
        lines.append(f"### {co}")
        for c in pdfs:
            desc = (c.get("download_meta") or {}).get("description", "")
            lines.append(
                f"- `{c['relative_path']}` → `{c['candidate_class']}`"
                + (f" ({desc})" if desc else "")
            )
            lines.append(f"  - preview: {c['preview'][:160]}…")
        lines.append("")

    lines.extend(["", "## Bảng shortlist", ""])
    lines.append("| company | path | candidate_class | why_candidate | recommended_action |")
    lines.append("|---|---|---|---|---|")
    shortlist = []
    for co in ("무신사", "레이시온"):
        data = payload["companies"][co]
        ranked = sorted(
            data.get("candidates", []),
            key=lambda x: (
                0
                if x["candidate_class"]
                in ("likely_actual_esg_report", "likely_company_impact_report")
                else 1,
                x["priority_tier"],
                -x["esg_report_body_signal_score"],
            ),
        )
        for c in ranked[:12]:
            shortlist.append(c)
            rel = c["relative_path"].replace("|", "\\|")
            why = c["why_candidate"].replace("|", "\\|")[:120]
            lines.append(
                f"| {co} | `{rel}` | `{c['candidate_class']}` | {why} | {c['recommended_action']} |"
            )

    lines.extend(["", "## Kết luận cuối", ""])
    ms = payload["companies"]["무신사"]
    rx = payload["companies"]["레이시온"]
    lines.append(
        f"- **무신사:** {'có raw source ESG report PDF' if ms['likely_actual_report_count'] else '**chưa có** Impact/ESG report PDF trong raw folder; chỉ analyst PDF + DART financial + newsroom web capture'}"
    )
    lines.append(
        f"- **레이시온:** {'có raw source' if rx['likely_actual_report_count'] else '**chưa có** SR/ESG report; folder chủ yếu RTX 10-K + DART audit + defense news (sai công ty)'}"
    )
    lines.extend(["", "### Bước import tiếp theo (chưa thực hiện)", ""])
    for note in payload.get("import_recommendations", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    companies: Dict[str, Any] = {}
    import_recs: List[str] = []

    for company, folder in AUDIT_DIRS.items():
        companies[company] = audit_company(company, folder)

    ms = companies["무신사"]
    rx = companies["레이시온"]

    if ms["likely_actual_report_count"] == 0:
        import_recs.append(
            "무신사: **không import** PDF analyst/입찰 từ raw folder cho Golden Set ESG; cần acquire "
            "`2024/2025 Musinsa Impact Report` PDF trực tiếp từ newsroom.musinsa.com hoặc corp site."
        )
        newsroom = next(
            (
                c
                for c in ms.get("candidates", [])
                if "page_04_web" in c["relative_path"]
                and (
                    "newsroom" in c["preview"].lower()
                    or "무신사 뉴스룸" in (c.get("title_headline") or "")
                )
            ),
            None,
        )
        if not newsroom:
            newsroom = next(
                (
                    c
                    for c in ms.get("candidates", [])
                    if "page_04_web" in c["relative_path"]
                ),
                None,
            )
        if newsroom:
            import_recs.append(
                f"무신사 (secondary): `{newsroom['relative_path']}` — newsroom listing capture only; "
                "dùng để trace URL, không thay report PDF."
            )

    import_recs.append(
        "레이시온: **không import** rtx-20251231.htm.html / rtx-20241231.htm.html — đây là RTX Corporation "
        "(Mỹ), không phải Korean 레이시온; cần source acquisition riêng (SR PDF / company site)."
    )

    summary = {
        "audit_version": "v4_2",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "musinsa": {
            "folder": ms["folder"],
            "best_candidates": [
                {
                    "path": c["path"],
                    "relative_path": c["relative_path"],
                    "candidate_class": c["candidate_class"],
                    "why_candidate": c["why_candidate"],
                    "recommended_action": c["recommended_action"],
                    "preview": c["preview"][:200],
                }
                for c in (ms.get("best_candidates") or [])[:5]
            ],
            "likely_actual_report_count": ms.get("likely_actual_report_count", 0),
            "likely_financial_only_count": ms.get("likely_financial_only_count", 0),
            "needs_manual_check": ms.get("needs_manual_check", []),
            "has_actual_esg_report_pdf": ms.get("likely_actual_report_count", 0) > 0,
        },
        "raysolution": {
            "folder": rx["folder"],
            "best_candidates": [
                {
                    "path": c["path"],
                    "relative_path": c["relative_path"],
                    "candidate_class": c["candidate_class"],
                    "why_candidate": c["why_candidate"],
                    "recommended_action": c["recommended_action"],
                    "preview": c["preview"][:200],
                }
                for c in (rx.get("best_candidates") or [])[:5]
            ],
            "likely_actual_report_count": rx.get("likely_actual_report_count", 0),
            "likely_financial_only_count": rx.get("likely_financial_only_count", 0),
            "needs_manual_check": rx.get("needs_manual_check", []),
            "cross_company_contamination": "US RTX/Raytheon conflated with Korean 레이시온",
            "has_actual_esg_report_pdf": rx.get("likely_actual_report_count", 0) > 0,
        },
        "import_recommendations": import_recs,
    }

    payload = {
        "generated_at": summary["generated_at"],
        "companies": companies,
        "import_recommendations": import_recs,
    }

    out_json = ROOT / "reports/_raw_source_audit_v4_2_summary.json"
    out_md = ROOT / "reports/golden_set_raw_source_audit_v4_2.md"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(build_markdown(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "ms_actual": ms.get("likely_actual_report_count"),
                "rx_actual": rx.get("likely_actual_report_count"),
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
