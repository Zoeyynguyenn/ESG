#!/usr/bin/env python3
"""Natural-case onboarding gate — package constructed regression + natural plug-in path."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.capability_gate_runner import default_gate_definition  # noqa: E402
from enterprise_docs.natural_case_onboarding import (  # noqa: E402
    ONBOARDING_FLOW_STEPS,
    load_case_schema,
    mandatory_onboarding_answers,
    run_onboarding_gate,
)

PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_fusion_equivalence_hardening_20260619-102350"


def _onboarding_flow_md(*, artifact_rel: str, answers: dict[str, Any]) -> str:
    steps_md = "\n".join(
        f"{s['step']}. **{s['name']}** — {s['action']}\n   - Output: `{s['output']}`"
        for s in ONBOARDING_FLOW_STEPS
    )
    return "\n".join(
        [
            "# Natural-case onboarding flow",
            "",
            f"Artifact: `{artifact_rel}`",
            "",
            "## Mục tiêu",
            "",
            "Biến capability benchmark thành onboarding gate plug-in-ready: "
            "constructed suite giữ regression CI; natural cases đo dữ liệu thật qua cùng harness.",
            "",
            "## Flow ngắn nhất (5 bước)",
            "",
            steps_md,
            "",
            "## Lệnh chạy gate",
            "",
            "```bash",
            "python scripts/run_enterprise_docs_natural_onboarding_gate.py",
            "```",
            "",
            "## Phân biệt case_origin",
            "",
            "| Loại | Mục đích | Sửa pipeline lõi? |",
            "|---|---|---|",
            "| `constructed` | Regression capability (extraction→promotion) | Không — thêm case trong JSONL |",
            "| `natural` | Diagnostic trên corpus thật | Không — thêm probe + natural row |",
            "",
            "## Sau gate",
            "",
            answers.get("6_next_step_after_onboarding_gate", {}).get("answer", ""),
            "",
        ]
    )


def _report_md(
    *,
    artifact_rel: str,
    summary: dict[str, Any],
    answers: dict[str, Any],
) -> str:
    ge = summary.get("gate_evaluation") or {}
    lr = ge.get("layer_report") or {}
    return "\n".join(
        [
            "# Enterprise internal-doc — Natural-case onboarding gate",
            "",
            f"Artifact: `{artifact_rel}`",
            "",
            f"**Overall status:** `{ge.get('overall_status')}`",
            f"**Regression gate passed:** `{ge.get('regression_gate_passed')}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Constructed regression (capability layers)",
            "",
            json.dumps(lr.get("by_capability_layer"), ensure_ascii=False, indent=2),
            "",
            "## Natural diagnostics",
            "",
            json.dumps(lr.get("natural_diagnostics"), ensure_ascii=False, indent=2),
            "",
            "## Answerability classification (unclear / no-information)",
            "",
            "Tách câu hỏi `out_of_scope` (không rõ/lạc đề) và `no_information` "
            "(honest abstain) khỏi `corpus_limited` / `system_gap`.",
            "",
            json.dumps(summary.get("answerability_metrics"), ensure_ascii=False, indent=2),
            "",
            "## Capability metrics (full suite)",
            "",
            json.dumps(summary.get("capability_metrics"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run natural-case onboarding gate")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = args.out_dir or (ROOT / f"reports/enterprise_docs_natural_onboarding_gate_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    gate_run = run_onboarding_gate()
    bench = gate_run["benchmark"]
    gate_eval = gate_run["gate_evaluation"]
    answers = mandatory_onboarding_answers(gate_run)
    gate_def = default_gate_definition()
    schema = load_case_schema()

    artifact_rel = str(out_dir.relative_to(ROOT)).replace("\\", "/")
    summary: dict[str, Any] = {
        "artifact": "enterprise_docs_natural_onboarding_gate",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "natural_case_onboarding_gate",
        "prior_artifact": str(PRIOR_ARTIFACT.relative_to(ROOT)).replace("\\", "/"),
        "cases_meta": gate_run.get("cases_meta"),
        "capability_metrics": bench.get("capability_metrics"),
        "natural_metrics": bench.get("natural_metrics"),
        "answerability_metrics": bench.get("answerability_metrics"),
        "gate_evaluation": gate_eval,
        "mandatory_answers": answers,
        "schema_path": gate_run.get("schema_path"),
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
            "no_core_pipeline_rebuild": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "gate_definition.json").write_text(json.dumps(gate_def, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "case_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "layer_matrix.json").write_text(
        json.dumps(gate_run.get("layer_matrix"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "natural_vs_constructed_split.json").write_text(
        json.dumps(bench.get("natural_vs_constructed_split"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "onboarding_flow.md").write_text(
        _onboarding_flow_md(artifact_rel=artifact_rel, answers=answers), encoding="utf-8"
    )
    (out_dir / "report.md").write_text(
        _report_md(artifact_rel=artifact_rel, summary=summary, answers=answers), encoding="utf-8"
    )

    print(json.dumps({"artifact": artifact_rel, "regression_gate_passed": gate_eval.get("regression_gate_passed")}, indent=2))
    return 0 if gate_eval.get("regression_gate_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
