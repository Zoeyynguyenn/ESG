#!/usr/bin/env python3
"""Parse seah dart_full section text to build pseudo empSttus/exctvSttus/재무 JSON.

Steps:
  1. Open seah zip, locate employee/exec/financial sections by rcp.
  2. Parse tables → list[dict] per schema.
  3. Save JSON arrays as raw data.
  4. Create artifact directories with records.jsonl (text field = human-readable row).
  5. Write collect_status.jsonl so the corpus builder can pick them up.

Usage:
  python scripts/build_seah_structured_json_from_sections.py
"""
from __future__ import annotations
import json, re, zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "../SeAH Steel/세아제강.zip"
OUT_ROOT = ROOT / "data/source_raw/seah_structured_local"

COMPANY_ID = "seah"
COMPANY_NAME = "세아제강"

# ---------------------------------------------------------------------------
# RCP → report year mapping (FY end date = Dec 31 of that year)
# ---------------------------------------------------------------------------
RCP_YEAR: dict[str, int | None] = {
    "20240306000569": 2023,  # FY2023 annual (filed 2024-03-06)
    "20260312000989": 2025,  # FY2025 annual (filed 2026-03-12, English version)
    "20260515001247": None,  # Q1 report — skip
    "20260529001922": None,  # ESG disclosure — skip
}

# Section folder names that contain employee+exec tables
EMP_EXEC_SECTIONS = {
    "1. 임원 및 직원 등의 현황_42",
    "1. Status of executives and employees, etc._124",
}

# Section folder names that contain financial summary
FIN_SECTIONS_2023 = {
    "1. 요약재무정보_18",
    "III. 재무에 관한 사항_17",
    "4. 재무제표_21",
}
FIN_SECTIONS_2025 = {
    "1. Summary of financial information_18",     # compact key figures
    "4-1. Statement Of FinancialPosition_63",     # separate balance sheet
    "4-2. Statement Of ComprehensiveIncome_64",   # separate income statement
    "III. Financial Matters_17",
}


# ---------------------------------------------------------------------------
# Employee table parser
# ---------------------------------------------------------------------------

# Exclude 합계/Total row: the extractor sums male+female internally to get totals.
# Including 합계 as a third row causes it to triple-count employees in ratio calculations.
_EMP_ROW_LABELS = {
    "남": "남", "여": "여",
    "Male": "남", "Female": "여",
}


def _parse_emp_table(txt: str, stlm_dt: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    # Isolate the employee subsection (after 나. or b.)
    block = ""
    for marker in ("나.직원 등 현황", "나. 직원 등 현황", "b. Employee Status",
                   "b.Employee Status", "b. Status of employees", "나. 직원 현황", "나."):
        idx = txt.find(marker)
        if idx != -1:
            block = txt[idx: idx + 2000]
            break
    if not block:
        return records

    # Strip NBSP and normalise
    block = block.replace("\xa0", " ").replace("－", "-")

    # Each cell is on its own line. Collect sequential non-empty lines.
    lines = [ln.strip() for ln in block.splitlines()]

    # Find label lines and collect the numbers that follow them
    row_data: dict[str, list[str]] = {}
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln in _EMP_ROW_LABELS:
            sex = _EMP_ROW_LABELS[ln]
            nums: list[str] = []
            j = i + 1
            # Consume up to 15 following lines, stop at next label or section end
            while j < len(lines) and j < i + 20:
                cell = lines[j].strip().rstrip(".")
                if cell in _EMP_ROW_LABELS:
                    break
                cell_clean = cell.replace(",", "")
                if re.match(r"^[\d]+$", cell_clean):
                    nums.append(cell_clean)
                elif cell == "-":
                    nums.append("")  # placeholder
                j += 1

            # nums layout (skipping - placeholders):
            # [regular, -, contract, -, total, tenure, ann_sal, mon_avg, ...]
            real_nums = [n for n in nums if n]  # drop placeholders
            if len(real_nums) >= 5:
                regular = real_nums[0]
                contract = real_nums[1]
                total = real_nums[2]
                tenure = real_nums[3]
                ann_sal = real_nums[4] if len(real_nums) > 4 else ""
                mon_sal = real_nums[5] if len(real_nums) > 5 else ""
                row_data[sex] = [regular, contract, total, tenure, ann_sal, mon_sal]
            i = j
            continue
        i += 1

    for sex, vals in row_data.items():
        regular, contract, total, tenure, ann_sal, mon_sal = vals
        records.append({
            "corp_name": COMPANY_NAME,
            "fo_bbm": "-",
            "sexdstn": sex,
            "rgllbr_co": regular,
            "cnttk_co": contract,
            "sm": total,
            "avrg_cnwk_sdytrn": tenure,
            "fyer_salary_totamt": ann_sal,
            "jan_salary_am": mon_sal,
            "stlm_dt": stlm_dt,
        })
    return records


def _emp_text(row: dict[str, Any]) -> str:
    return (
        f"corp={row.get('corp_name')} | division={row.get('fo_bbm')} | "
        f"sex={row.get('sexdstn')} | regular={row.get('rgllbr_co')} | "
        f"contract={row.get('cnttk_co')} | total={row.get('sm')} | "
        f"avg_tenure={row.get('avrg_cnwk_sdytrn')} | "
        f"annual_salary={row.get('fyer_salary_totamt')} | "
        f"monthly_salary={row.get('jan_salary_am')} | "
        f"stlm_dt={row.get('stlm_dt')}"
    )


# ---------------------------------------------------------------------------
# Executive table parser
# ---------------------------------------------------------------------------

def _parse_exec_table(txt: str, stlm_dt: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    # Take only the executive subsection (before 나.)
    block_end = txt.find("나.")
    if block_end == -1:
        block_end = txt.find("b.")
    block = txt[:block_end].strip() if block_end > 0 else txt[:4000]

    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    i = 0
    while i < len(lines) - 1:
        line = lines[i]
        next_ln = lines[i + 1]
        if next_ln in ("남", "여", "Male", "Female"):
            sex = "남" if next_ln in ("남", "Male") else "여"
            position = lines[i + 3] if i + 3 < len(lines) else ""
            registered_raw = lines[i + 4] if i + 4 < len(lines) else ""
            full_time_raw = lines[i + 5] if i + 5 < len(lines) else ""
            role = lines[i + 6] if i + 6 < len(lines) else ""

            reg_yn = "Y" if registered_raw in (
                "사내이사", "사외이사", "Executive Directors", "Outside Director",
                "Audit Committee Member", "Audit Committee", "감사위원회위원", "기타비상무이사"
            ) else "N"
            fte_yn = "Y" if full_time_raw in ("상근", "Full-time") else "N"

            tenure = ""
            for j in range(i + 1, min(i + 15, len(lines))):
                if re.search(r'\d+\.\d+년', lines[j]):
                    tenure = lines[j]
                    break

            records.append({
                "corp_name": COMPANY_NAME,
                "nm": line,
                "sexdstn": sex,
                "ofcps": position,
                "rgist_exctv_at": reg_yn,
                "fte_at": fte_yn,
                "chrg_job": role,
                "hffc_pd": tenure,
                "stlm_dt": stlm_dt,
            })
            i += 7
            continue
        i += 1
    return records


def _exec_text(row: dict[str, Any]) -> str:
    return (
        f"corp={row.get('corp_name')} | name={row.get('nm')} | sex={row.get('sexdstn')} | "
        f"position={row.get('ofcps')} | registered_exec={row.get('rgist_exctv_at')} | "
        f"full_time={row.get('fte_at')} | role={str(row.get('chrg_job') or '').replace(chr(10), ' / ')} | "
        f"tenure={row.get('hffc_pd')} | stlm_dt={row.get('stlm_dt')}"
    )


# ---------------------------------------------------------------------------
# Financial statement parser
# ---------------------------------------------------------------------------

FIN_ITEMS = [
    ("매출액", "Revenue", "dart_Revenue", "손익계산서"),
    ("영업이익", "Operating profit", "dart_OperatingIncomeLoss", "손익계산서"),
    ("당기순이익", "Net income", "dart_ProfitLoss", "손익계산서"),
    ("자산총계", "Total assets", "dart_Assets", "재무상태표"),
    ("부채총계", "Total liabilities", "dart_Liabilities", "재무상태표"),
    ("자본총계", "Total equity", "dart_Equity", "재무상태표"),
    ("자본금", "Capital stock", "dart_IssuedCapital", "재무상태표"),
    ("이익잉여금", "Retained earnings", "dart_RetainedEarnings", "재무상태표"),
]


def _find_amount(txt: str, korean: str, english: str) -> str:
    for kw in (korean, english):
        idx = txt.find(kw)
        if idx == -1:
            continue
        snippet = txt[idx: idx + 300]
        # First large number (7+ digits) after keyword
        m = re.search(r'([\d,]{7,})', snippet)
        if m:
            return m.group(1).replace(",", "")
    return ""


def _parse_financial(txt: str, stlm_dt: str, bsns_year: str) -> list[dict[str, Any]]:
    records = []
    term_no = int(bsns_year) - 2016 + 1  # 세아제강 7기 = 2023
    for korean, english, dart_id, sj_nm in FIN_ITEMS:
        amt = _find_amount(txt, korean, english)
        if not amt:
            continue
        records.append({
            "rcept_no": "",
            "bsns_year": bsns_year,
            "corp_code": "",
            "sj_nm": sj_nm,
            "account_nm": korean,
            "account_id": dart_id,
            "thstrm_nm": f"제{term_no}기",
            "thstrm_amount": amt,
            "frmtrm_nm": "",
            "frmtrm_amount": "",
            "bfefrmtrm_nm": "",
            "bfefrmtrm_amount": "",
            "ord": "1",
            "currency": "KRW",
        })
    return records


def _fin_text(row: dict[str, Any]) -> str:
    return (
        f"corp={COMPANY_NAME} | year={row.get('bsns_year')} | "
        f"statement={row.get('sj_nm')} | account={row.get('account_nm')} | "
        f"account_id={row.get('account_id')} | amount={row.get('thstrm_amount')} | "
        f"currency={row.get('currency')}"
    )


# ---------------------------------------------------------------------------
# Artifact staging helpers
# ---------------------------------------------------------------------------

def _write_artifact(
    art_dir: Path,
    raw_records: list[dict[str, Any]],
    text_fn,
    source_url: str,
    doc_title: str,
    schema: str,
    year: str,
) -> dict[str, Any] | None:
    if not raw_records:
        return None

    art_dir.mkdir(parents=True, exist_ok=True)

    # records.jsonl — text field is what the corpus builder indexes
    records_rows = []
    for idx, rec in enumerate(raw_records):
        records_rows.append({
            "record_id": f"{COMPANY_ID}::{doc_title}::{idx}",
            "text": text_fn(rec),
            **rec,
        })

    (art_dir / "records.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records_rows),
        encoding="utf-8",
    )

    # Save raw JSON with canonical filename — this is what local_path points to.
    # The corpus builder's enrich_base_meta derives canonical_doc_id from basename(local_path),
    # so it must be the JSON filename (e.g. "2023_empSttus.json") for structured identity to work.
    json_path = art_dir / doc_title
    json_path.write_text(json.dumps(raw_records, ensure_ascii=False, indent=2), encoding="utf-8")

    # extracted.txt as fallback (corpus builder reads records.jsonl first)
    header = (
        f"company_id: {COMPANY_ID}\n"
        f"company_name: {COMPANY_NAME}\n"
        f"doc_title: {doc_title}\n"
        f"source_url: {source_url}\n"
        f"schema: {schema}\n"
        f"year: {year}\n\n"
    )
    body = "\n".join(rec["text"] for rec in records_rows)
    (art_dir / "extracted.txt").write_text(header + body, encoding="utf-8")

    return {
        "collect_status": "ok",
        "company_id": COMPANY_ID,
        "company_name": COMPANY_NAME,
        "doc_title": doc_title,
        "source_url": source_url,
        "file_url": None,
        "source_kind": "dart_local_artifact",
        "schema": schema,
        "local_path": str(json_path),   # basename = "2023_empSttus.json" → drives canonical_doc_id
        "artifact_dir": str(art_dir),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    z = zipfile.ZipFile(str(ZIP_PATH))
    all_names = z.namelist()

    # Group by rcp
    by_rcp: dict[str, list[str]] = {}
    for name in all_names:
        m = re.search(r'dart_full/(\d{14})/', name)
        if m:
            by_rcp.setdefault(m.group(1), []).append(name)

    collect_rows: list[dict[str, Any]] = []

    for rcp, entries in sorted(by_rcp.items()):
        report_year = RCP_YEAR.get(rcp)
        if report_year is None:
            continue

        stlm_dt = f"{report_year}1231"
        bsns_year = str(report_year)
        dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp}"
        fin_sections = FIN_SECTIONS_2023 if report_year == 2023 else FIN_SECTIONS_2025

        print(f"\n[rcp={rcp}, year={report_year}]")

        # Find employee+exec section and financial section(s)
        emp_txt = exec_txt = ""
        fin_txts: list[str] = []
        for entry in entries:
            parts = entry.replace("\\", "/").split("/")
            try:
                di = parts.index("dart_full")
            except ValueError:
                continue
            if len(parts) < di + 4:
                continue
            section_dir = parts[di + 2]
            if section_dir in EMP_EXEC_SECTIONS and entry.endswith("section.txt"):
                raw = z.read(entry).decode("utf-8", errors="replace")
                emp_txt = exec_txt = raw
            if section_dir in fin_sections and entry.endswith("section.txt"):
                fin_txts.append(z.read(entry).decode("utf-8", errors="replace"))
        # Combine all financial section texts for parsing
        fin_txt = "\n".join(fin_txts)

        # Employee
        emp_recs = _parse_emp_table(emp_txt, stlm_dt) if emp_txt else []
        art_dir = OUT_ROOT / COMPANY_ID / rcp / "empSttus"
        row = _write_artifact(art_dir, emp_recs, _emp_text, dart_url,
                              f"{bsns_year}_empSttus.json", "dart_employee_status", bsns_year)
        if row:
            collect_rows.append(row)
            print(f"  empSttus: {len(emp_recs)} records → {art_dir}")
        else:
            print(f"  empSttus: no data parsed")

        # Executive
        exec_recs = _parse_exec_table(exec_txt, stlm_dt) if exec_txt else []
        art_dir = OUT_ROOT / COMPANY_ID / rcp / "exctvSttus"
        row = _write_artifact(art_dir, exec_recs, _exec_text, dart_url,
                              f"{bsns_year}_exctvSttus.json", "dart_executive_status", bsns_year)
        if row:
            collect_rows.append(row)
            print(f"  exctvSttus: {len(exec_recs)} records → {art_dir}")
        else:
            print(f"  exctvSttus: no data parsed")

        # Financial
        fin_recs = _parse_financial(fin_txt, stlm_dt, bsns_year) if fin_txt else []
        art_dir = OUT_ROOT / COMPANY_ID / rcp / "financial_OFS"
        row = _write_artifact(art_dir, fin_recs, _fin_text, dart_url,
                              f"{bsns_year}_재무_OFS.json", "dart_financial_statement", bsns_year)
        if row:
            collect_rows.append(row)
            print(f"  재무_OFS: {len(fin_recs)} records → {art_dir}")
        else:
            print(f"  재무_OFS: no data parsed")

    z.close()

    # Write collect_status.jsonl
    status_path = OUT_ROOT / "collect_status.jsonl"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in collect_rows),
        encoding="utf-8",
    )
    print(f"\nTotal: {len(collect_rows)} structured entries → {status_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
