"""Build natural + constructed cross-document capability benchmark cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "data/enterprise_docs/crossdoc_capability_cases.jsonl"
PROBE_PATHS = {
    "hanssem": ROOT / "data/enterprise_docs/holdout_probes_hanssem.jsonl",
    "musinsa": ROOT / "data/enterprise_docs/holdout_probes_musinsa.jsonl",
}
CROSS_DOC_PATTERN_FAMILIES = frozenset({
    "climate_narrative",
    "scope_expansion",
    "governance_numeric_narrative",
    "environment_esg_grade",
    "governance_materiality",
    "esg_rating_narrative",
    "employee_headcount",
})

PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


def _constructed_cases() -> list[dict[str, Any]]:
    """System-level capability cases — explicitly labeled constructed."""
    return [
        {
            "case_id": "CONSTRUCT-ALIAS-SCOPE3",
            "case_origin": "constructed",
            "capability": "alias_normalization",
            "capability_tags": ["alias_normalization", "cross_doc_equivalence"],
            "family_id": "environment_ghg",
            "item": "스코프 3",
            "kind": "capability_unit",
            "test_type": "value_pair_equivalence",
            "value_pairs": [["Scope 3", "scope3"], ["스코프 3", "Scope 3"], ["Scope3", "scope 3"]],
            "expected_all_equivalent": True,
        },
        {
            "case_id": "CONSTRUCT-ALIAS-NETZERO-YEAR",
            "case_origin": "constructed",
            "capability": "alias_normalization",
            "capability_tags": ["alias_normalization"],
            "family_id": "environment_ghg",
            "item": "탄소중립",
            "kind": "capability_unit",
            "test_type": "value_pair_equivalence",
            "value_pairs": [["2050", "2030"]],
            "expected_all_equivalent": False,
        },
        {
            "case_id": "CONSTRUCT-EQUIV-GRADE",
            "case_origin": "constructed",
            "capability": "cross_doc_equivalence",
            "capability_tags": ["cross_doc_equivalence", "alias_normalization"],
            "family_id": "governance",
            "item": "ESG 평가 등급",
            "kind": "capability_unit",
            "test_type": "canonical_key_match",
            "values": ["A", "A+", "a등급"],
            "expected_same_canonical": False,
            "notes": "A vs A+ should not collapse to same canonical grade",
        },
        {
            "case_id": "CONSTRUCT-EQUIV-NUMERIC-COMMA",
            "case_origin": "constructed",
            "capability": "cross_doc_equivalence",
            "capability_tags": ["cross_doc_equivalence", "numeric_equivalence"],
            "family_id": "environment_ghg",
            "item": "총 온실가스",
            "kind": "capability_unit",
            "test_type": "canonical_key_match",
            "values": ["12,500", "12500", "12500.0"],
            "expected_same_canonical": True,
        },
        {
            "case_id": "CONSTRUCT-FUSION-NARRATIVE-TABLE-SCALED",
            "case_origin": "constructed",
            "capability": "evidence_fusion",
            "capability_tags": ["evidence_fusion", "narrative_table_fusion", "numeric_equivalence"],
            "family_id": "environment_ghg",
            "item": "총 온실가스",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_evidence_csv"],
            "roles": {
                "doc_sr_narrative": "narrative",
                "doc_evidence_csv": "numeric table evidence",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_narrative_ghg_scaled",
                    "text": "Total GHG emissions were reported as 12.5 thousand tCO2e for fiscal 2023.",
                },
                {
                    "logical_doc": "doc_evidence_csv",
                    "document_id": "synthetic_table_ghg_scaled",
                    "text": "| Metric | 2023 | Unit |\n| --- | --- | --- |\n| 총 온실가스 | 12500 | tCO2e |",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_evidence_csv": True},
            "expected_multi_source_confirmed": True,
        },
        {
            "case_id": "CONSTRUCT-EXTRACT-SCOPE3-CROSSROLE",
            "case_origin": "constructed",
            "capability": "cross_role_extraction",
            "capability_tags": ["cross_role_extraction", "semantic_bridge"],
            "family_id": "environment_ghg",
            "item": "스코프 3",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_governance_disclosure"],
            "roles": {
                "doc_sr_narrative": "sustainability narrative",
                "doc_governance_disclosure": "governance disclosure",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_sr_scope3_en",
                    "text": "GHG management expanded from Scope 2 to Scope 3 including affiliates.",
                },
                {
                    "logical_doc": "doc_governance_disclosure",
                    "document_id": "synthetic_dart_scope3_kr",
                    "text": "온실가스 관리 범위를 스코프(Scope) 3까지 확대하였습니다.",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_governance_disclosure": True},
            "expected_multi_source_confirmed": True,
        },
        {
            "case_id": "CONSTRUCT-FUSION-GRADE-A",
            "case_origin": "constructed",
            "capability": "evidence_fusion",
            "capability_tags": ["evidence_fusion", "cross_doc_equivalence", "readiness_promotion"],
            "family_id": "governance",
            "item": "ESG 평가 등급",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_governance_disclosure"],
            "roles": {
                "doc_sr_narrative": "sustainability narrative",
                "doc_governance_disclosure": "governance disclosure",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_sr_grade",
                    "text": "KCGS ESG evaluation result 'A' grade obtained in 2022.",
                },
                {
                    "logical_doc": "doc_governance_disclosure",
                    "document_id": "synthetic_dart_grade",
                    "text": "ESG 평가 등급 A등급을 유지하였습니다.",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_governance_disclosure": True},
            "expected_multi_source_confirmed": True,
            "expected_conflict_status": "multi_source_confirmed",
        },
        {
            "case_id": "CONSTRUCT-CONFLICT-NUMERIC",
            "case_origin": "constructed",
            "capability": "conflict_classification",
            "capability_tags": ["conflict_classification", "conflict_resolution", "evidence_fusion"],
            "family_id": "governance",
            "item": "이사회 개최",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_governance_disclosure"],
            "roles": {
                "doc_sr_narrative": "sustainability narrative",
                "doc_governance_disclosure": "governance disclosure",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_sr_board",
                    "text": "The board of directors met 14 times in 2022.",
                },
                {
                    "logical_doc": "doc_governance_disclosure",
                    "document_id": "synthetic_dart_board",
                    "text": "2022년 이사회를 10회 개최하였습니다.",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_governance_disclosure": True},
            "expected_multi_source_confirmed": False,
            "expected_conflict_status": "conflict_numeric",
        },
        {
            "case_id": "CONSTRUCT-NOTDISC-VS-NUMERIC",
            "case_origin": "constructed",
            "capability": "conflict_classification",
            "capability_tags": ["conflict_classification"],
            "family_id": "employee_headcount",
            "item": "육아휴직",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_governance_disclosure"],
            "roles": {
                "doc_sr_narrative": "workforce narrative",
                "doc_governance_disclosure": "workforce disclosure",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_sr_parental",
                    "text": "육아휴직 대상자 수: Not disclosed",
                },
                {
                    "logical_doc": "doc_governance_disclosure",
                    "document_id": "synthetic_dart_parental",
                    "text": "육아휴직 사용 인원 120명",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": False, "doc_governance_disclosure": True},
            "expected_multi_source_confirmed": False,
            "expected_conflict_status": "conflict_numeric",
        },
        {
            "case_id": "CONSTRUCT-SINGLE-SOURCE",
            "case_origin": "constructed",
            "capability": "readiness_promotion",
            "capability_tags": ["readiness_promotion", "evidence_fusion"],
            "family_id": "environment_ghg",
            "item": "탄소중립",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_governance_disclosure"],
            "roles": {
                "doc_sr_narrative": "sustainability narrative",
                "doc_governance_disclosure": "governance disclosure",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_sr_netzero",
                    "text": "We target 2050 carbon neutral by 2050 탄소중립.",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_governance_disclosure": False},
            "expected_multi_source_confirmed": False,
            "expected_conflict_status": "single_source_sufficient",
        },
        {
            "case_id": "CONSTRUCT-NARRATIVE-VS-TABLE",
            "case_origin": "constructed",
            "capability": "cross_role_extraction",
            "capability_tags": ["cross_role_extraction"],
            "family_id": "environment_ghg",
            "item": "총 온실가스",
            "kind": "quantitative",
            "test_type": "multi_source_extraction",
            "company_id": "capability_synthetic",
            "answer_mode": "cross_document_answer",
            "primary_document_ids": ["doc_sr_narrative", "doc_evidence_csv"],
            "roles": {
                "doc_sr_narrative": "narrative",
                "doc_evidence_csv": "numeric table evidence",
            },
            "source_units": [
                {
                    "logical_doc": "doc_sr_narrative",
                    "document_id": "synthetic_narrative_ghg",
                    "text": "Total GHG emissions Scope 1+2 were 12,500 tCO2e in 2023.",
                },
                {
                    "logical_doc": "doc_evidence_csv",
                    "document_id": "synthetic_table_ghg",
                    "text": "| Metric | 2023 | Unit |\n| --- | --- | --- |\n| 총 온실가스 | 12,500 | tCO2e |",
                },
            ],
            "expected_extract_per_doc": {"doc_sr_narrative": True, "doc_evidence_csv": True},
            "expected_multi_source_confirmed": True,
        },
    ]


def _family_for_probe(probe: dict[str, Any]) -> str | None:
    pf = str(probe.get("pattern_family") or "")
    if "employee" in pf or "headcount" in pf or probe.get("item") in ("구성원", "MAU"):
        return "employee_headcount"
    if "climate" in pf or "scope" in pf or "environment" in pf or probe.get("item") in (
        "탄소중립",
        "스코프 3",
        "환경 ESG 등급",
    ):
        return "environment_ghg"
    if "governance" in pf or "esg_rating" in pf or "materiality" in pf or probe.get("domain") == "지배구조":
        return "governance"
    return None


def natural_cases_from_probes() -> list[dict[str, Any]]:
    """Wrap holdout quant probes as natural cross-doc capability cases."""
    out: list[dict[str, Any]] = []
    for company_id, path in PROBE_PATHS.items():
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            probe = json.loads(line)
            if probe.get("kind") != "quantitative":
                continue
            pf = str(probe.get("pattern_family") or "")
            fid = _family_for_probe(probe)
            if fid not in PILOT_FAMILIES:
                continue
            out.append(
                {
                    "case_id": f"NATURAL-{probe.get('probe_id')}",
                    "case_origin": "natural",
                    "capability": "natural_overlap_probe",
                    "capability_tags": ["cross_role_extraction", "evidence_fusion", "natural_corpus"],
                    "family_id": fid,
                    "company_id": company_id,
                    "pattern_family": pf,
                    "cross_doc_eligible": pf in CROSS_DOC_PATTERN_FAMILIES,
                    "kind": "quantitative",
                    "test_type": "natural_holdout_probe",
                    "probe": probe,
                    "item": probe.get("item"),
                    "question": probe.get("question"),
                }
            )
    return out


# Answerability classification cases — distinguish a *question problem* (unclear /
# out-of-scope) and an *honest abstain* (metric simply not disclosed) from a real
# corpus_limited / system_gap. Self-contained: each case carries an inline corpus so
# no external probe file is required. capability_tags intentionally EXCLUDE the five
# constructed regression signals so these cases never affect the regression gate.
ANSWERABILITY_CASES: list[dict[str, Any]] = [
    {
        "case_id": "ANSWERABILITY-CONTROL-GHG",
        "case_origin": "constructed",
        "capability": "answerability_classification",
        "capability_tags": ["answerability", "abstain_safety"],
        "test_type": "answerability_probe",
        "family_id": "environment_ghg",
        "company_id": "capability_synthetic",
        "kind": "quantitative",
        "expected_answerability": "answerable",
        "probe": {
            "question": "2023년 Scope 1 온실가스 배출량은?",
            "item": "스코프 3",
            "pattern_family": "environment_narrative",
            "kind": "quantitative",
        },
        "inline_corpus": [
            {"logical_doc_id": "sr_2023", "text": "2023 온실가스 배출량 Scope 1: 1,200 tCO2e"},
        ],
    },
    {
        "case_id": "ANSWERABILITY-OUT-OF-SCOPE-PERSONAL",
        "case_origin": "constructed",
        "capability": "answerability_classification",
        "capability_tags": ["answerability", "abstain_safety"],
        "test_type": "answerability_probe",
        "family_id": None,
        "company_id": "capability_synthetic",
        "kind": "quantitative",
        "expected_answerability": "out_of_scope",
        "probe": {
            "question": "CEO의 개인 휴대폰 번호는 무엇입니까?",
            "item": "개인 연락처",
            "pattern_family": "unrelated_personal_info",
            "kind": "quantitative",
        },
        "inline_corpus": [
            {"logical_doc_id": "sr_2023", "text": "2023 온실가스 배출량 Scope 1: 1,200 tCO2e"},
        ],
    },
    {
        "case_id": "ANSWERABILITY-OUT-OF-SCOPE-VAGUE",
        "case_origin": "constructed",
        "capability": "answerability_classification",
        "capability_tags": ["answerability", "abstain_safety"],
        "test_type": "answerability_probe",
        "family_id": None,
        "company_id": "capability_synthetic",
        "kind": "quantitative",
        "expected_answerability": "out_of_scope",
        "probe": {
            "question": "이 회사 어때요?",
            "item": "",
            "pattern_family": "",
            "kind": "quantitative",
        },
        "inline_corpus": [
            {"logical_doc_id": "sr_2023", "text": "2023 온실가스 배출량 Scope 1: 1,200 tCO2e"},
        ],
    },
    {
        "case_id": "ANSWERABILITY-NO-INFORMATION-GHG",
        "case_origin": "constructed",
        "capability": "answerability_classification",
        "capability_tags": ["answerability", "abstain_safety"],
        "test_type": "answerability_probe",
        "family_id": "environment_ghg",
        "company_id": "capability_synthetic",
        "kind": "quantitative",
        "expected_answerability": "no_information",
        "probe": {
            "question": "2023년 Scope 3 온실가스 배출량은?",
            "item": "스코프 3",
            "pattern_family": "scope_expansion",
            "kind": "quantitative",
        },
        # Corpus has Scope 1 only — the metric family is recognized but the specific
        # value is genuinely not disclosed → honest abstain, NOT corpus_limited.
        "inline_corpus": [
            {"logical_doc_id": "sr_2023", "text": "2023 온실가스 배출량 Scope 1: 1,200 tCO2e"},
        ],
    },
]


def _ac(case_id, expected, question, item, pattern_family, corpus_texts):
    return {
        "case_id": case_id,
        "case_origin": "constructed",
        "capability": "answerability_classification",
        "capability_tags": ["answerability", "abstain_safety"],
        "test_type": "answerability_probe",
        "company_id": "capability_synthetic",
        "kind": "quantitative",
        "expected_answerability": expected,
        "probe": {"question": question, "item": item, "pattern_family": pattern_family, "kind": "quantitative"},
        "inline_corpus": [{"logical_doc_id": "d", "text": t} for t in corpus_texts],
    }


# Expanded answerability suite (diverse + adversarial). The ADV-* cases are EXPECTED to
# expose heuristic limits — keyword dependence, token match without value check, and
# phrasing-sensitive item matching — so reported accuracy stays honest, not inflated.
_GHG_S1 = ["2023 온실가스 배출량 Scope 1: 1,200 tCO2e"]
ANSWERABILITY_EXTRA_CASES: list[dict[str, Any]] = [
    _ac("ANS-EMP-HEADCOUNT", "answerable", "총 구성원 수는?", "총 구성원 수", "employee_headcount", ["총 구성원 수: 1,234명"]),
    _ac("ANS-GOV-BOARD", "answerable", "이사회 규모는?", "이사회 규모", "governance_board", ["이사회 규모: 9명"]),
    _ac("ANS-ENV-NETZERO", "answerable", "탄소중립 목표 연도는?", "탄소중립", "climate_narrative", ["2050 탄소중립 목표"]),
    _ac("ANS-ENV-GRADE", "answerable", "환경 ESG 등급은?", "환경 ESG 등급", "environment_esg_grade", ["환경 ESG 등급: A"]),
    _ac("ANS-EMP-MAU", "answerable", "MAU는?", "MAU", "employee_hr", ["MAU: 500만"]),
    _ac("OOS-WEATHER", "out_of_scope", "오늘 서울 날씨 어때요?", "날씨", "weather_smalltalk", _GHG_S1),
    _ac("OOS-LUNCH", "out_of_scope", "점심 메뉴 추천해줘", "메뉴", "chitchat", _GHG_S1),
    _ac("OOS-PARKING", "out_of_scope", "본사 주차장 위치는?", "주차장", "facility_misc", _GHG_S1),
    _ac("NOINFO-EMP", "no_information", "총 구성원 수는?", "총 구성원 수", "employee_headcount", _GHG_S1),
    _ac("NOINFO-GOV-MAT", "no_information", "중대성 평가 결과는?", "중대성", "governance_materiality", ["이사회 규모: 9명"]),
    _ac("NOINFO-CERT-YEAR", "no_information", "ISO14001 인증 연도는?", "인증 연도", "environment_certification", ["환경경영을 강화하고 있다"]),
    # adversarial — documented known limitations (expected to fail under current heuristic)
    _ac("ADV-NO-KEYWORD", "no_information", "작년에 탄소 얼마나 줄였나요?", "", "", _GHG_S1),
    _ac("ADV-TOKEN-FALSEPOS", "no_information", "2023 Scope 3 배출량은?", "스코프 3", "scope_expansion", ["스코프 3 측정 방법론은 별도 보고서를 참조하십시오"]),
    _ac("ADV-PHRASING", "answerable", "여성 임원 비율은?", "여성 임원 비율", "governance_board", ["이사회 내 여성 비중: 22%"]),
]


def answerability_cases() -> list[dict[str, Any]]:
    """Self-contained answerability classification cases (diverse + adversarial)."""
    return [dict(c) for c in (ANSWERABILITY_CASES + ANSWERABILITY_EXTRA_CASES)]


def all_capability_cases(*, include_natural: bool = True) -> list[dict[str, Any]]:
    cases = _constructed_cases()
    cases.extend(answerability_cases())
    if include_natural:
        cases.extend(natural_cases_from_probes())
    return cases


def case_to_plan(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("test_type") == "natural_holdout_probe":
        probe = dict(case.get("probe") or {})
        probe["company_id"] = case.get("company_id")
        probe["item_id"] = probe.get("probe_id")
        probe["answer_mode"] = "cross_document_answer"
        probe["_capability_case_id"] = case.get("case_id")
        probe["_case_origin"] = "natural"
        return probe
    plan = {
        "item_id": case.get("case_id"),
        "question": case.get("question") or f"Capability case {case.get('case_id')}",
        "item": case.get("item"),
        "family_id": case.get("family_id"),
        "kind": case.get("kind") if case.get("kind") != "capability_unit" else "quantitative",
        "company_id": case.get("company_id") or "capability_synthetic",
        "answer_mode": case.get("answer_mode") or "single_document_answer",
        "primary_document_ids": list(case.get("primary_document_ids") or []),
        "roles": dict(case.get("roles") or {}),
        "pattern_family": case.get("pattern_family") or case.get("family_id"),
        "_capability_case_id": case.get("case_id"),
        "_case_origin": case.get("case_origin"),
    }
    return plan


def synthetic_corpus_from_case(case: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Build in-memory corpus + logical_map for constructed pipeline cases."""
    company_id = str(case.get("company_id") or "capability_synthetic")
    units: list[dict[str, Any]] = []
    logical_map: dict[str, str] = {}
    for i, src in enumerate(case.get("source_units") or []):
        doc_id = str(src.get("document_id") or f"synthetic_{i}")
        lid = str(src.get("logical_doc") or f"doc_{i}")
        logical_map[lid] = doc_id
        text = str(src.get("text") or "")
        units.append(
            {
                "unit_id": f"{company_id}::{doc_id}::{i:04d}",
                "company_id": company_id,
                "document_id": doc_id,
                "source_type": "synthetic",
                "text": text,
                "search_text": text,
                "evidence_text": text,
                "metadata": {"logical_doc": lid, "capability_case": case.get("case_id")},
            }
        )
    return units, logical_map


def load_cases_jsonl(path: Path | None = None) -> list[dict[str, Any]]:
    """Load capability cases from JSONL."""
    in_path = path or CASES_PATH
    if not in_path.exists():
        return all_capability_cases(include_natural=True)
    cases: list[dict[str, Any]] = []
    for line in in_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def write_capability_cases_jsonl(
    path: Path | None = None,
    *,
    include_natural: bool = True,
) -> dict[str, Any]:
    out_path = path or CASES_PATH
    cases = all_capability_cases(include_natural=include_natural)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in cases:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    constructed = sum(1 for c in cases if c.get("case_origin") == "constructed")
    natural = sum(1 for c in cases if c.get("case_origin") == "natural")
    return {
        "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "total": len(cases),
        "constructed": constructed,
        "natural": natural,
    }
