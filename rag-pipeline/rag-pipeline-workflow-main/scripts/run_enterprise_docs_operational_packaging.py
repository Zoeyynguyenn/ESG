#!/usr/bin/env python3
"""Operational packaging — bootstrap kit + runbook for real-company onboarding."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.operational_packaging import (  # noqa: E402
    bootstrap_kit_manifest,
    mandatory_packaging_answers,
    render_runbook_checklist_md,
)

PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_natural_onboarding_gate_20260619-103432"


def _report_md(*, artifact_rel: str, summary: dict, answers: dict) -> str:
    manifest = summary.get("bootstrap_kit_manifest") or {}
    return "\n".join(
        [
            "# Enterprise internal-doc — Operational packaging",
            "",
            f"Artifact: `{artifact_rel}`",
            "",
            f"**Lane status:** `{summary.get('lane_status')}`",
            f"**Kit complete:** `{manifest.get('all_required_present')}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Bootstrap kit files",
            "",
            json.dumps(manifest.get("files"), ensure_ascii=False, indent=2),
            "",
            "## Constraints",
            "",
            json.dumps(summary.get("constraints"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = args.out_dir or (ROOT / f"reports/enterprise_docs_operational_packaging_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = bootstrap_kit_manifest()
    answers = mandatory_packaging_answers(manifest)
    artifact_rel = str(out_dir.relative_to(ROOT)).replace("\\", "/")

    summary = {
        "artifact": "enterprise_docs_operational_packaging",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "operational_packaging_for_real_company_onboarding",
        "prior_artifact": str(PRIOR_ARTIFACT.relative_to(ROOT)).replace("\\", "/"),
        "lane_status": "done_until_real_data",
        "bootstrap_kit_manifest": manifest,
        "mandatory_answers": answers,
        "constraints": manifest.get("constraints"),
        "next_action_when_real_data_arrives": (
            "python scripts/bootstrap_enterprise_company.py --company-id <id> --company-label \"<label>\""
        ),
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "bootstrap_kit_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "runbook_checklist.md").write_text(render_runbook_checklist_md(manifest), encoding="utf-8")
    (out_dir / "report.md").write_text(
        _report_md(artifact_rel=artifact_rel, summary=summary, answers=answers), encoding="utf-8"
    )

    print(json.dumps({"artifact": artifact_rel, "lane_status": summary["lane_status"]}, indent=2))
    return 0 if manifest.get("all_required_present") else 1


if __name__ == "__main__":
    raise SystemExit(main())
