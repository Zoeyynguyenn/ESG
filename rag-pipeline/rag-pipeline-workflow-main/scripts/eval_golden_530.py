#!/usr/bin/env python3
"""Real golden-set eval — RAG vs Gold (goldns + emni).

Reads goldns_emni_rag_vs_gold_comparison.xlsx and computes the real answer/abstain
metrics on ~530 actual ESG questions. This measures the full RAG pipeline (not the
lightweight answerability heuristic), and is the real-data evidence for the
answer/abstain axis.

Run: python scripts/eval_golden_530.py [path/to/workbook.xlsx]
Writes: reports/enterprise_docs_golden_eval_530_<date>/summary.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = [
    ROOT / "goldns_emni_rag_vs_gold_comparison.xlsx",
    ROOT.parent / "goldns_emni_rag_vs_gold_comparison.xlsx",
    ROOT / "data" / "goldns_emni_rag_vs_gold_comparison.xlsx",
]


def _norm(v):
    return str(v).strip() if v is not None else None


def _load(wb, sheet):
    rows = list(wb[sheet].iter_rows(values_only=True))
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if any(c is not None for c in r)]


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = next((p for p in DEFAULT_CANDIDATES if p.exists()), None)
    if not path or not path.exists():
        print("Workbook not found. Pass the path as an argument.")
        return 2

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = {"goldns": "goldns_compare", "emni": "emni_compare"}
    allrows = []
    by_company = {}
    for cid, sh in sheets.items():
        rs = _load(wb, sh)
        allrows += rs
        part = Counter(_norm(r.get("partition")) for r in rs)
        green = sum(1 for r in rs if _norm(r.get("comparison_status")) in ("ABSTAIN_OK", "MATCH"))
        by_company[cid] = {
            "total": len(rs),
            "answerable_gold": part.get("answerable_gold", 0),
            "abstain_gold": part.get("abstain_gold", 0),
            "green": green,
            "answer_correct": sum(1 for r in rs if _norm(r.get("answer_correct")) == "True"),
        }

    conf: dict = {}
    for r in allrows:
        g = _norm(r.get("partition")); p = _norm(r.get("rag_predicted_abstain"))
        conf.setdefault(g, Counter())[p] += 1

    non_green = [
        {
            "question_id": _norm(r.get("question_id")),
            "status": _norm(r.get("comparison_status")),
            "fail_type": _norm(r.get("fail_type")),
            "note": (_norm(r.get("comparison_note")) or "")[:80],
        }
        for r in allrows
        if _norm(r.get("comparison_status")) not in ("ABSTAIN_OK", "MATCH")
    ]

    n = len(allrows)
    res = {
        "source_workbook": path.name,
        "total_questions": n,
        "gold_partition": dict(Counter(_norm(r.get("partition")) for r in allrows)),
        "answer_correct_total": sum(1 for r in allrows if _norm(r.get("answer_correct")) == "True"),
        "green_total": sum(1 for r in allrows if _norm(r.get("comparison_status")) in ("ABSTAIN_OK", "MATCH")),
        "abstain_confusion_gold_x_predicted_abstain": {k: dict(v) for k, v in conf.items()},
        "by_company": by_company,
        "non_green_rows": non_green,
    }
    ts = datetime.now().strftime("%Y%m%d")
    out = ROOT / f"reports/enterprise_docs_golden_eval_530_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
