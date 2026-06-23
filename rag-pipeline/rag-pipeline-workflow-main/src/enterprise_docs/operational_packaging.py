"""Operational packaging for real-company onboarding — bootstrap kit manifest + SOP metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PRIOR_ONBOARDING_ARTIFACT = ROOT / "reports/enterprise_docs_natural_onboarding_gate_20260619-103432"

BOOTSTRAP_KIT_PATHS = {
    "runbook": "docs/ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md",
    "bootstrap_guide": "docs/ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md",
    "onboarding_doc": "docs/ENTERPRISE_INTERNAL_DOC_NATURAL_CASE_ONBOARDING.md",
    "schema": "data/enterprise_docs/natural_capability_case_schema.json",
    "probe_template": "data/enterprise_docs/templates/holdout_probes_template.jsonl",
    "natural_case_template": "data/enterprise_docs/templates/natural_capability_cases_template.jsonl",
    "review_template": "data/enterprise_docs/templates/onboarding_review_template.md",
    "bootstrap_script": "scripts/bootstrap_enterprise_company.py",
    "onboarding_gate_script": "scripts/run_enterprise_docs_natural_onboarding_gate.py",
    "company_registry": "data/enterprise_docs/company_doc_registry.json",
    "capability_cases": "data/enterprise_docs/crossdoc_capability_cases.jsonl",
}

CHECKLIST_SECTIONS = (
    {
        "id": "data_intake",
        "title": "Checklist tiếp nhận dữ liệu doanh nghiệp",
        "items": [
            "Xác nhận company_id (slug ASCII, ví dụ `acme_corp`)",
            "Thu thập SR/ESG report, DART/XML, bảng Excel/CSV hỗ trợ",
            "Liệt kê logical documents (SR narrative, evidence table, governance, HR, …)",
            "Ghi nhận format file (.pdf/.html/.xml/.json/.csv) và năm báo cáo",
            "Không bắt đầu tune pipeline trước khi ingest xong",
        ],
    },
    {
        "id": "ingest",
        "title": "Checklist ingest",
        "items": [
            "Tạo thư mục `data/enterprise_docs/{company_id}/`",
            "Chạy ingest theo profile trong `company_doc_registry.json`",
            "Sinh `corpus_units.jsonl` (hoặc reingested/filtered artifact theo policy)",
            "Kiểm tra parser: mỗi unit có `evidence_text` hoặc `text` không rỗng",
            "Ghi `reingest_summary.json` nếu dùng structured ESG re-ingest path",
        ],
    },
    {
        "id": "logical_doc_mapping",
        "title": "Checklist logical-doc mapping",
        "items": [
            "Thêm company block vào `company_doc_registry.json`",
            "Khai báo `logical_documents` với path_hint, domains, role_labels",
            "Gán `corpus_artifact` trỏ tới corpus JSONL đã ingest",
            "Xác nhận ít nhất 2 logical docs có metric overlap cho cross-doc (nếu cần fusion)",
            "Review routing: holdout_routing / primary_document_ids cho quant probes",
        ],
    },
    {
        "id": "probes",
        "title": "Checklist tạo probes",
        "items": [
            "Copy template → `holdout_probes_{company_id}.jsonl`",
            "Ưu tiên `kind=quantitative` trong 3 pilot families",
            "Mỗi probe: probe_id, pattern_family, item, question, expected_signal",
            "Đăng ký path trong `PROBE_PATHS` (`crossdoc_case_builder.py`) hoặc dùng bootstrap manifest",
            "Không dùng constructed cases để đo corpus thật",
        ],
    },
    {
        "id": "gate",
        "title": "Checklist chạy gate",
        "items": [
            "Refresh natural cases: `write_capability_cases_jsonl` hoặc bootstrap merge",
            "Chạy `python scripts/run_enterprise_docs_natural_onboarding_gate.py`",
            "Constructed regression **phải PASS** (5 layers, ghost_pass=0)",
            "Natural metrics là diagnostic — không fail CI vì corpus_limited cao",
            "Lưu artifact timestamp vào onboarding review",
        ],
    },
    {
        "id": "review",
        "title": "Checklist review corpus_limited vs system_gap",
        "items": [
            "Đọc `natural_metrics.by_failure_mode` trong summary.json",
            "corpus_limited_* → thiếu overlap tài liệu → bổ sung source, không harden lõi",
            "system_gap → registry/extraction/equivalence theo family_id",
            "parser empty text → parser lane, không nhầm với system_gap",
            "Điền `onboarding_review_{company_id}.md` từ template",
        ],
    },
)

DECISION_RULES = (
    {
        "signal": "corpus_limited",
        "meaning": "Corpus thiếu metric ở >=2 logical docs hoặc không tìm thấy candidate",
        "action": "Bổ sung tài liệu / logical-doc map; **không** mở workstream hardening pipeline lõi",
        "do_not": ["rebuild parser", "rebuild retrieval", "tune constructed cases"],
    },
    {
        "signal": "system_gap",
        "meaning": "Corpus đủ nhưng extraction/equivalence/fusion fail trên natural case",
        "action": "Mở rộng `metric_equivalence_registry` / cross_role patterns đúng family_id",
        "do_not": ["chase demo score", "inflate multi_source metric"],
    },
    {
        "signal": "parser_fail",
        "meaning": "Unit rỗng, format không parse được, evidence_text trống",
        "action": "Quay lại parser lane (html/xml/pdf) cho format cụ thể",
        "do_not": ["đổi fusion contract", "mở LangGraph"],
    },
    {
        "signal": "natural_pass",
        "meaning": "Natural probes pass capability layers; fusion/promotion integrity OK",
        "action": "Chuyển structured ESG output sang bước báo cáo / handoff prep (không mở synthesis trial)",
        "do_not": ["rebuild core pipeline"],
    },
)

OPERATIONAL_RUNBOOK_STEPS = (
    {"step": 1, "name": "ingest", "command_hint": "ingest + corpus_units.jsonl"},
    {"step": 2, "name": "map_logical_docs", "command_hint": "company_doc_registry.json"},
    {"step": 3, "name": "create_probes", "command_hint": "holdout_probes_{company_id}.jsonl"},
    {"step": 4, "name": "build_natural_cases", "command_hint": "natural_case_from_probe / crossdoc_capability_cases.jsonl"},
    {"step": 5, "name": "run_onboarding_gate", "command_hint": "python scripts/run_enterprise_docs_natural_onboarding_gate.py"},
    {"step": 6, "name": "classify_failure", "command_hint": "corpus_limited vs system_gap in summary.json"},
    {"step": 7, "name": "decide_next_action", "command_hint": "onboarding_review template + DECISION_RULES"},
)


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def bootstrap_kit_manifest() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for key, rel in BOOTSTRAP_KIT_PATHS.items():
        p = ROOT / rel
        files.append(
            {
                "key": key,
                "path": rel,
                "exists": p.exists(),
                "size_bytes": p.stat().st_size if p.exists() else None,
            }
        )
    prior_summary = {}
    if PRIOR_ONBOARDING_ARTIFACT.joinpath("summary.json").exists():
        prior_summary = json.loads(PRIOR_ONBOARDING_ARTIFACT.joinpath("summary.json").read_text(encoding="utf-8"))

    return {
        "kit_version": "operational_bootstrap_v1",
        "lane_status": "done_until_real_data",
        "prior_onboarding_artifact": _rel(PRIOR_ONBOARDING_ARTIFACT),
        "prior_gate_status": (prior_summary.get("gate_evaluation") or {}).get("overall_status"),
        "constructed_regression_baseline": "PASS 100% — CI gate",
        "natural_onboarding_path": "ready_for_natural_plug_in",
        "files": files,
        "all_required_present": all(f["exists"] for f in files),
        "checklist_sections": CHECKLIST_SECTIONS,
        "decision_rules": DECISION_RULES,
        "runbook_steps": OPERATIONAL_RUNBOOK_STEPS,
        "constraints": {
            "no_langgraph_runtime": True,
            "no_synthesis": True,
            "no_core_pipeline_rebuild": True,
            "no_demo_score_tuning": True,
        },
    }


def mandatory_packaging_answers(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "1_bootstrap_kit_contents": {
            "answer": (
                "Runbook SOP, bootstrap guide, 3 templates (probes/natural cases/review), "
                "bootstrap script, onboarding gate script, schema, company registry reference, "
                "6 checklist sections, 4 decision rules."
            ),
            "files": [f["path"] for f in manifest.get("files") or [] if f.get("exists")],
            "checklist_section_ids": [s["id"] for s in CHECKLIST_SECTIONS],
        },
        "2_shortest_onboarding_flow": {
            "answer": "ingest → map logical docs → create probes → build natural cases → run gate → classify → decide",
            "steps": OPERATIONAL_RUNBOOK_STEPS,
        },
        "3_files_before_gate": {
            "answer": (
                "corpus_units.jsonl + company_doc_registry entry; holdout_probes_{company_id}.jsonl; "
                "PROBE_PATHS registration; refreshed crossdoc_capability_cases.jsonl with natural rows."
            ),
            "required_artifacts": [
                "data/enterprise_docs/{company_id}/corpus_units*.jsonl",
                "data/enterprise_docs/company_doc_registry.json (company block)",
                "data/enterprise_docs/holdout_probes_{company_id}.jsonl",
                "data/enterprise_docs/crossdoc_capability_cases.jsonl",
            ],
        },
        "4_corpus_limited_vs_system_gap": {
            "corpus_limited": DECISION_RULES[0],
            "system_gap": DECISION_RULES[1],
            "how_to_read": (
                "Xem natural_metrics.by_failure_mode trong gate summary: "
                "corpus_limited_* = thiếu corpus/overlap; system_gap = capability fail dù có candidate."
            ),
        },
        "5_done_until_real_data": {
            "answer": "Có — constructed gate là regression chuẩn; natural onboarding path sẵn sàng; bootstrap kit đủ để team onboard mà không suy nghĩ lại flow.",
            "lane_status": manifest.get("lane_status"),
            "all_kit_files_present": manifest.get("all_required_present"),
        },
        "6_next_step_if_no_real_data_yet": {
            "answer": (
                "Giữ constructed regression làm CI; không mở LangGraph/synthesis; "
                "chờ dữ liệu doanh nghiệp thật rồi chạy bootstrap_enterprise_company.py + gate; "
                "hoặc dry-run trên hanssem/musinsa để team làm quen SOP."
            ),
            "do_not": ["harden core pipeline", "chase natural demo score", "source acquisition as main workstream"],
        },
    }


def render_runbook_checklist_md(manifest: dict[str, Any]) -> str:
    lines = [
        "# Runbook checklist — Enterprise internal-doc onboarding",
        "",
        "Lane status: **`done_until_real_data`**",
        "",
        "## Flow vận hành (7 bước)",
        "",
    ]
    for s in OPERATIONAL_RUNBOOK_STEPS:
        lines.append(f"{s['step']}. **{s['name']}** — `{s['command_hint']}`")
    lines.extend(["", "## Checklists", ""])
    for section in CHECKLIST_SECTIONS:
        lines.append(f"### {section['title']}")
        lines.append("")
        for item in section["items"]:
            lines.append(f"- [ ] {item}")
        lines.append("")
    lines.extend(["## Quy tắc quyết định", ""])
    for rule in DECISION_RULES:
        lines.append(f"### `{rule['signal']}`")
        lines.append(f"- **Nghĩa:** {rule['meaning']}")
        lines.append(f"- **Hành động:** {rule['action']}")
        lines.append(f"- **Không làm:** {', '.join(rule['do_not'])}")
        lines.append("")
    lines.append("## Lệnh bootstrap công ty mới")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/bootstrap_enterprise_company.py --company-id acme_corp --company-label \"ACME Corp\"")
    lines.append("python scripts/run_enterprise_docs_natural_onboarding_gate.py")
    lines.append("```")
    return "\n".join(lines)
