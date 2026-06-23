"""Retrieval scope narrowing for holdout reingested corpus (registry-driven)."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "data/enterprise_docs/retrieval_scope_policy.json"


@lru_cache(maxsize=1)
def load_retrieval_scope_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def list_scope_names() -> list[str]:
    reg = load_retrieval_scope_policy()
    return sorted((reg.get("scopes") or {}).keys())


def _doc_id(unit: dict[str, Any]) -> str:
    return str(unit.get("document_id") or "").lower()


def _source_type(unit: dict[str, Any]) -> str:
    return str(unit.get("source_type") or "").lower()


def _tokens_in_doc(doc_l: str, tokens: list[str]) -> bool:
    return any(str(t).lower() in doc_l for t in tokens if t)


def _matches_include_rule(unit: dict[str, Any], rule: dict[str, Any]) -> bool:
    doc_l = _doc_id(unit)
    st = _source_type(unit)
    types = [str(x).lower() for x in (rule.get("source_types") or [])]
    if types and st not in types:
        return False
    id_any = rule.get("document_id_any") or []
    return bool(id_any) and _tokens_in_doc(doc_l, id_any)


def _passes_scope_spec(unit: dict[str, Any], spec: dict[str, Any], reg: dict[str, Any]) -> bool:
    doc_l = _doc_id(unit)
    st = _source_type(unit)

    exclude = list(spec.get("exclude_document_id_any") or reg.get("noise_exclude_tokens") or [])
    if _tokens_in_doc(doc_l, exclude):
        return False

    include_types = [str(x).lower() for x in (spec.get("include_source_types") or [])]
    if include_types and st not in include_types:
        return False

    include_id = spec.get("include_document_id_any") or []
    if include_id and not _tokens_in_doc(doc_l, include_id):
        return False

    include_rules = spec.get("include_rules_any") or []
    if include_rules and not any(_matches_include_rule(unit, r) for r in include_rules):
        return False

    if spec.get("exclude_broad_financial_xml_unless_esg"):
        broad = reg.get("broad_financial_xml_tokens") or []
        esg = reg.get("esg_dart_xml_tokens") or []
        if st == "xml" and _tokens_in_doc(doc_l, broad) and not _tokens_in_doc(doc_l, esg):
            if "사업보고서" in doc_l and not _tokens_in_doc(doc_l, esg + (reg.get("sr_document_tokens") or [])):
                return False

    return True


def _scope_spec(scope_name: str, company_id: str | None = None) -> dict[str, Any]:
    reg = load_retrieval_scope_policy()
    spec = dict((reg.get("scopes") or {}).get(scope_name) or {})
    if company_id:
        over = ((reg.get("company_overrides") or {}).get(company_id) or {}).get(scope_name)
        if over:
            spec = {**spec, **over}
    return spec


def filter_units_by_scope(
    units: list[dict[str, Any]],
    scope_name: str,
    *,
    company_id: str | None = None,
    max_units_per_document: int | None = None,
) -> list[dict[str, Any]]:
    reg = load_retrieval_scope_policy()
    spec = _scope_spec(scope_name, company_id)
    if not spec:
        return list(units)

    cap = max_units_per_document
    if cap is None:
        cap = int(spec.get("max_units_per_document") or 0) or None

    kept: list[dict[str, Any]] = []
    per_doc: Counter[str] = Counter()
    for unit in units:
        if not _passes_scope_spec(unit, spec, reg):
            continue
        doc_id = str(unit.get("document_id") or "")
        if cap and per_doc[doc_id] >= cap:
            continue
        kept.append(unit)
        per_doc[doc_id] += 1
    return kept


def summarize_scope(units: list[dict[str, Any]], scope_name: str, *, company_id: str | None = None) -> dict[str, Any]:
    filtered = filter_units_by_scope(units, scope_name, company_id=company_id)
    by_type = Counter(str(u.get("source_type") or "unknown") for u in filtered)
    by_doc = Counter(str(u.get("document_id") or "") for u in filtered)
    return {
        "scope_name": scope_name,
        "input_units": len(units),
        "output_units": len(filtered),
        "document_count": len(by_doc),
        "by_source_type": dict(by_type),
        "top_documents": dict(by_doc.most_common(8)),
    }


def build_scope_policy_matrix(units_by_company: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for scope in list_scope_names():
        matrix[scope] = {}
        for company_id, units in units_by_company.items():
            matrix[scope][company_id] = summarize_scope(units, scope, company_id=company_id)
    default = load_retrieval_scope_policy().get("default_scope") or "structured_esg_retrieval_ready"
    return {
        "default_scope": default,
        "scopes": matrix,
        "policy_path": str(POLICY_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


def write_filtered_corpus(
    company_id: str,
    units: list[dict[str, Any]],
    *,
    scope_name: str | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    reg = load_retrieval_scope_policy()
    scope = scope_name or str(reg.get("default_scope") or "structured_esg_retrieval_ready")
    filtered = filter_units_by_scope(units, scope, company_id=company_id)
    out = output or (ROOT / f"data/enterprise_docs/{company_id}/corpus_units_filtered.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in filtered:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = summarize_scope(units, scope, company_id=company_id)
    summary.update(
        {
            "company_id": company_id,
            "scope_name": scope,
            "status": "ok" if filtered else "empty",
            "output": str(out.relative_to(ROOT)).replace("\\", "/"),
        }
    )
    (out.parent / "filtered_scope_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary
