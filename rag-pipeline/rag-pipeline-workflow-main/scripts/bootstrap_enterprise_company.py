#!/usr/bin/env python3
"""Bootstrap skeleton files for a new enterprise company onboarding."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.natural_case_onboarding import (  # noqa: E402
    build_natural_cases_for_company,
    validate_natural_case,
    write_onboarding_cases_jsonl,
)

TEMPLATES = ROOT / "data/enterprise_docs/templates"
DEFAULT_COMPANY_DIR = ROOT / "data/enterprise_docs"


def _substitute(text: str, *, company_id: str, company_label: str) -> str:
    return (
        text.replace("{company_id}", company_id)
        .replace("{company_label}", company_label)
        .replace("{review_date}", date.today().isoformat())
        .replace("{reviewer}", "TBD")
        .replace("{gate_timestamp}", "TBD")
        .replace("{notes}", "")
        .replace("{next_actions}", "Chạy gate sau khi ingest xong.")
    )


def bootstrap_company(
    company_id: str,
    *,
    company_label: str,
    dry_run: bool = False,
    refresh_cases: bool = False,
) -> dict:
    company_dir = DEFAULT_COMPANY_DIR / company_id
    probes_path = DEFAULT_COMPANY_DIR / f"holdout_probes_{company_id}.jsonl"
    review_path = company_dir / f"onboarding_review_{company_id}.md"
    notes_path = company_dir / "onboarding_notes.md"
    manifest_path = company_dir / "bootstrap_manifest.json"

    probe_template = (TEMPLATES / "holdout_probes_template.jsonl").read_text(encoding="utf-8")
    probes_content = _substitute(probe_template, company_id=company_id, company_label=company_label)

    review_template = (TEMPLATES / "onboarding_review_template.md").read_text(encoding="utf-8")
    review_content = _substitute(review_template, company_id=company_id, company_label=company_label)

    notes_content = "\n".join(
        [
            f"# Onboarding notes — {company_id}",
            "",
            f"Company label: {company_label}",
            "",
            "## Trạng thái",
            "",
            "- [ ] Ingest corpus",
            "- [ ] Logical-doc mapping trong company_doc_registry.json",
            "- [ ] Probes finalized",
            "- [ ] PROBE_PATHS registered",
            "- [ ] Gate chạy",
            "",
            "## Manual steps sau bootstrap",
            "",
            f"1. Thêm block `{company_id}` vào `data/enterprise_docs/company_doc_registry.json`",
            f"2. Thêm `{company_id}` vào `PROBE_PATHS` trong `src/enterprise_docs/crossdoc_case_builder.py`:",
            f'   `"{company_id}": ROOT / "data/enterprise_docs/holdout_probes_{company_id}.jsonl"`',
            "3. Ingest tài liệu → `corpus_units.jsonl`",
            "4. Chạy `python scripts/run_enterprise_docs_natural_onboarding_gate.py`",
            "",
        ]
    )

    registry_stub = {
        "company_id": company_id,
        "label": company_label,
        "role": "production_holdout",
        "corpus_artifact": f"data/enterprise_docs/{company_id}/corpus_units.jsonl",
        "logical_documents": {
            "doc_sr_narrative": {
                "path_hint": "SR|지속가능|sustainability",
                "domains": "환경,지배구조,사회",
                "scope": "company_specific",
                "role_labels": {"qualitative": "SR narrative"},
            },
            "doc_evidence_table": {
                "path_hint": "evidence|table|csv|데이터",
                "domains": "환경,사회,지배구조",
                "scope": "company_specific",
                "role_labels": {"quantitative": "numeric table evidence"},
            },
        },
        "_note": "Copy/adapt into company_doc_registry.json after ingest paths confirmed",
    }

    created: list[str] = []
    if not dry_run:
        company_dir.mkdir(parents=True, exist_ok=True)
        probes_path.write_text(probes_content, encoding="utf-8")
        review_path.write_text(review_content, encoding="utf-8")
        notes_path.write_text(notes_content, encoding="utf-8")
        (company_dir / "company_registry_stub.json").write_text(
            json.dumps(registry_stub, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        created.extend(
            [
                str(probes_path.relative_to(ROOT)).replace("\\", "/"),
                str(review_path.relative_to(ROOT)).replace("\\", "/"),
                str(notes_path.relative_to(ROOT)).replace("\\", "/"),
                f"data/enterprise_docs/{company_id}/company_registry_stub.json",
            ]
        )

    natural_cases = build_natural_cases_for_company(company_id, probes_path if probes_path.exists() else None)
    validation_errors = []
    for case in natural_cases:
        validation_errors.extend(validate_natural_case(case))

    cases_meta = None
    if refresh_cases and not dry_run:
        cases_meta = write_onboarding_cases_jsonl()

    manifest = {
        "company_id": company_id,
        "company_label": company_label,
        "created_files": created,
        "probes_path": str(probes_path.relative_to(ROOT)).replace("\\", "/"),
        "natural_case_count_from_probes": len(natural_cases),
        "validation_errors": validation_errors,
        "manual_steps": [
            "Register company in company_doc_registry.json",
            "Register PROBE_PATHS in crossdoc_case_builder.py",
            "Ingest documents to corpus_units.jsonl",
            "Run onboarding gate",
        ],
        "cases_refresh": cases_meta,
    }

    if not dry_run:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append(str(manifest_path.relative_to(ROOT)).replace("\\", "/"))

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap enterprise company onboarding skeleton")
    parser.add_argument("--company-id", required=True, help="ASCII slug, e.g. acme_corp")
    parser.add_argument("--company-label", default=None, help="Display label for probes/questions")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-cases", action="store_true", help="Refresh crossdoc_capability_cases.jsonl")
    args = parser.parse_args()

    label = args.company_label or args.company_id.replace("_", " ")
    manifest = bootstrap_company(
        args.company_id,
        company_label=label,
        dry_run=args.dry_run,
        refresh_cases=args.refresh_cases,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if not manifest.get("validation_errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
