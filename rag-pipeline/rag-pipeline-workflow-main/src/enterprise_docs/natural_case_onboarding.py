"""Natural-case onboarding workflow — plug real enterprise docs into capability gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from enterprise_docs.capability_gate_runner import (
    default_gate_definition,
    load_gate_definition,
    report_by_capability_layer,
    run_capability_gate,
)
from enterprise_docs.crossdoc_case_builder import (
    CASES_PATH,
    PROBE_PATHS,
    all_capability_cases,
    natural_cases_from_probes,
    write_capability_cases_jsonl,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "data/enterprise_docs/natural_capability_case_schema.json"

REQUIRED_NATURAL_FIELDS = ("case_id", "case_origin", "company_id", "family_id", "test_type", "probe")
NATURAL_TEST_TYPE = "natural_holdout_probe"


def load_case_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_natural_case(case: dict[str, Any]) -> list[str]:
    """Lightweight validation without external jsonschema dependency."""
    errors: list[str] = []
    if case.get("case_origin") != "natural":
        errors.append("case_origin must be 'natural'")
    for field in REQUIRED_NATURAL_FIELDS:
        if not case.get(field):
            errors.append(f"missing required field: {field}")
    if case.get("test_type") != NATURAL_TEST_TYPE:
        errors.append(f"test_type must be '{NATURAL_TEST_TYPE}'")
    probe = case.get("probe") or {}
    if not probe.get("probe_id"):
        errors.append("probe.probe_id required")
    if not probe.get("kind"):
        errors.append("probe.kind required")
    fid = case.get("family_id")
    if fid and fid not in ("employee_headcount", "environment_ghg", "governance"):
        errors.append(f"family_id '{fid}' not in pilot families")
    return errors


def natural_case_from_probe(
    probe: dict[str, Any],
    *,
    company_id: str | None = None,
    expected_outcome_class: str | None = None,
    logical_docs: list[str] | None = None,
    readiness_expectation: str | None = None,
) -> dict[str, Any]:
    """Build a natural capability case from a holdout-style probe dict."""
    from enterprise_docs.crossdoc_case_builder import CROSS_DOC_PATTERN_FAMILIES, _family_for_probe

    cid = company_id or str(probe.get("company") or "")
    pf = str(probe.get("pattern_family") or "")
    fid = _family_for_probe(probe) or "governance"
    case_id = f"NATURAL-{probe.get('probe_id')}"
    row: dict[str, Any] = {
        "case_id": case_id,
        "case_origin": "natural",
        "capability": "natural_overlap_probe",
        "capability_tags": ["cross_role_extraction", "evidence_fusion", "natural_corpus"],
        "family_id": fid,
        "company_id": cid,
        "pattern_family": pf,
        "cross_doc_eligible": pf in CROSS_DOC_PATTERN_FAMILIES,
        "expected_capability_type": "natural_overlap_probe",
        "kind": probe.get("kind"),
        "test_type": NATURAL_TEST_TYPE,
        "probe": probe,
        "item": probe.get("item"),
        "question": probe.get("question"),
    }
    if logical_docs:
        row["logical_docs"] = logical_docs
    if expected_outcome_class:
        row["expected_outcome_class"] = expected_outcome_class
    if readiness_expectation:
        row["readiness_expectation"] = readiness_expectation
    return row


def load_probes_from_jsonl(path: Path) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            probes.append(json.loads(line))
    return probes


def build_natural_cases_for_company(
    company_id: str,
    probes_path: Path | None = None,
    *,
    quantitative_only: bool = True,
) -> list[dict[str, Any]]:
    """Convert probe JSONL into natural capability cases for one company."""
    path = probes_path or PROBE_PATHS.get(company_id)
    if path is None or not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for probe in load_probes_from_jsonl(path):
        if quantitative_only and probe.get("kind") != "quantitative":
            continue
        case = natural_case_from_probe(probe, company_id=company_id)
        errs = validate_natural_case(case)
        if errs:
            continue
        out.append(case)
    return out


def merge_regression_and_natural_cases(
    *,
    natural_cases: list[dict[str, Any]] | None = None,
    include_constructed: bool = True,
) -> list[dict[str, Any]]:
    """Standard onboarding case set: constructed regression + natural probes."""
    cases: list[dict[str, Any]] = []
    if include_constructed:
        cases.extend(c for c in all_capability_cases(include_natural=False) if c.get("case_origin") == "constructed")
    natural = natural_cases if natural_cases is not None else natural_cases_from_probes()
    cases.extend(natural)
    return cases


def write_onboarding_cases_jsonl(
    path: Path | None = None,
    *,
    natural_cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out_path = path or CASES_PATH
    cases = merge_regression_and_natural_cases(natural_cases=natural_cases)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in cases:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {
        "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "total": len(cases),
        "constructed": sum(1 for c in cases if c.get("case_origin") == "constructed"),
        "natural": sum(1 for c in cases if c.get("case_origin") == "natural"),
    }


ONBOARDING_FLOW_STEPS = (
    {
        "step": 1,
        "name": "ingest_documents",
        "action": "Ingest enterprise PDF/HTML/XML/Excel via existing enterprise_docs ingest path",
        "output": "Corpus units + logical_doc mapping for company_id",
    },
    {
        "step": 2,
        "name": "define_probes",
        "action": "Author holdout probes JSONL (question, item, pattern_family, expected_signal)",
        "output": "data/enterprise_docs/holdout_probes_{company_id}.jsonl",
    },
    {
        "step": 3,
        "name": "build_natural_cases",
        "action": "Run natural_case_from_probe / build_natural_cases_for_company or write_onboarding_cases_jsonl",
        "output": "Natural rows in crossdoc_capability_cases.jsonl with case_origin=natural",
    },
    {
        "step": 4,
        "name": "run_capability_gate",
        "action": "scripts/run_enterprise_docs_natural_onboarding_gate.py",
        "output": "Gate report: constructed regression must pass; natural diagnostics by failure_mode",
    },
    {
        "step": 5,
        "name": "review_by_layer",
        "action": "Inspect report_by_capability_layer — corpus_limited vs system_gap",
        "output": "Decision: expand corpus overlap vs extend registry/equivalence",
    },
)


def run_onboarding_gate(
    *,
    cases_path: Path | None = None,
    gate_path: Path | None = None,
) -> dict[str, Any]:
    """Full onboarding gate: refresh cases, run benchmark, evaluate layers."""
    cases_meta = write_capability_cases_jsonl(include_natural=True)
    gate = load_gate_definition(gate_path)
    result = run_capability_gate(
        cases_path=cases_path or CASES_PATH,
        include_constructed=True,
        include_natural=True,
        gate=gate,
    )
    bench = result["benchmark"]
    layer_matrix = report_by_capability_layer(bench.get("case_results") or [])
    return {
        **result,
        "cases_meta": cases_meta,
        "layer_matrix": layer_matrix,
        "onboarding_flow": ONBOARDING_FLOW_STEPS,
        "schema_path": str(SCHEMA_PATH.relative_to(ROOT)).replace("\\", "/"),
        "gate_definition_default": default_gate_definition(),
    }


def mandatory_onboarding_answers(gate_run: dict[str, Any]) -> dict[str, Any]:
    """Six mandatory strategic questions for report.md."""
    gate_eval = gate_run.get("gate_evaluation") or {}
    layer = gate_eval.get("layer_report") or {}
    cm = (gate_run.get("benchmark") or {}).get("capability_metrics") or {}
    nm = (gate_run.get("benchmark") or {}).get("natural_metrics") or {}

    return {
        "1_core_gate_reusable_for_natural_cases": {
            "answer": (
                "Có — cùng harness `run_capability_benchmark()` và `evaluate_case()`; "
                "natural cases chỉ cần `test_type=natural_holdout_probe` + embedded probe. "
                "Không sửa pipeline lõi khi thêm case mới."
            ),
            "regression_gate_passed": gate_eval.get("regression_gate_passed"),
            "reusable_harness": True,
        },
        "2_natural_case_schema_fields": {
            "answer": (
                "case_id, case_origin=natural, company_id, family_id, pattern_family, "
                "logical_docs (optional), expected_capability_type, expected_outcome_class, "
                "expected_canonical_value / conflict / readiness (optional), probe embed."
            ),
            "schema_path": gate_run.get("schema_path"),
        },
        "3_acceptance_gate_draft_for_real_docs": {
            "constructed_regression": layer.get("constructed_regression"),
            "natural_draft_thresholds": default_gate_definition().get("natural_onboarding_draft"),
            "natural_diagnostics": layer.get("natural_diagnostics"),
        },
        "4_demo_constructed_dependencies_remaining": {
            "answer": (
                "Constructed `source_units` synthetic corpus; holdout corpus paths hanssem/musinsa; "
                "PROBE_PATHS hardcoded; pilot PILOT_FAMILIES filter; metric_equivalence_registry "
                "mở rộng khi gặp pattern mới — không block plug-in case mới."
            ),
            "depends_on_demo_corpus": ["hanssem", "musinsa holdout ingest"],
            "depends_on_constructed_regression": True,
            "independent_of_langgraph_synthesis": True,
        },
        "5_shortest_onboarding_flow_for_real_docs": {
            "steps": ONBOARDING_FLOW_STEPS,
            "minimal_command": "python scripts/run_enterprise_docs_natural_onboarding_gate.py",
        },
        "6_next_step_after_onboarding_gate": {
            "answer": (
                "Onboard công ty thật đầu tiên: ingest → probes → natural cases → gate; "
                "phân tích corpus_limited vs system_gap; mở registry/equivalence chỉ khi system_gap; "
                "giữ constructed regression làm CI gate."
            ),
            "do_not": ["LangGraph runtime", "synthesis", "parser/retrieval rebuild", "case tuning for demo score"],
        },
    }
