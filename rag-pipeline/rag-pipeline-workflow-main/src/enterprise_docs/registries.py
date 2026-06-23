"""Registry loaders for enterprise internal-doc abstraction layer."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / "data" / "enterprise_docs"


@lru_cache(maxsize=1)
def load_company_doc_registry() -> dict[str, Any]:
    path = REGISTRY_DIR / "company_doc_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_metric_family_registry() -> dict[str, Any]:
    path = REGISTRY_DIR / "metric_family_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_source_role_registry() -> dict[str, Any]:
    path = REGISTRY_DIR / "source_role_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def company_config(company_id: str) -> dict[str, Any]:
    reg = load_company_doc_registry()
    companies = reg.get("companies") or {}
    if company_id not in companies:
        return {}
    return companies[company_id]


def is_holdout_company(company_id: str) -> bool:
    role = str(company_config(company_id).get("role") or "")
    return role in ("holdout", "holdout_probe")


def holdout_routing_profile(company_id: str) -> dict[str, Any]:
    """Per-company holdout routing overrides (narrative SR corpus)."""
    routing = routing_defaults(company_id)
    defaults = dict(load_company_doc_registry().get("defaults") or {}).get("holdout_routing") or {}
    company = dict(company_config(company_id).get("holdout_routing") or {})
    merged = {**defaults, **company}
    if is_holdout_company(company_id):
        merged.setdefault("force_single_doc_quant", True)
        merged.setdefault("max_primary_docs", 1)
    return merged


def logical_documents(company_id: str) -> dict[str, dict[str, Any]]:
    return dict(company_config(company_id).get("logical_documents") or {})


def corpus_path_patterns(company_id: str) -> dict[str, str]:
    docs = logical_documents(company_id)
    return {
        lid: str(spec.get("path_hint") or "")
        for lid, spec in docs.items()
        if spec.get("path_hint")
    }


def _family_applies(family: dict[str, Any], company_id: str | None) -> bool:
    companies = family.get("companies") or []
    if not company_id:
        return True
    if not companies:
        return True
    return company_id in companies


def row_aliases(company_id: str | None = None) -> dict[str, list[str]]:
    reg = load_metric_family_registry()
    out: dict[str, list[str]] = {}
    for family in reg.get("families") or []:
        if not _family_applies(family, company_id):
            continue
        scope = str(family.get("scope") or "generic")
        if scope == "pilot_only" and company_id and company_id not in (family.get("companies") or []):
            continue
        for item_key, aliases in (family.get("row_aliases") or {}).items():
            existing = out.setdefault(item_key, [])
            for a in aliases:
                if a not in existing:
                    existing.append(a)
    return out


@lru_cache(maxsize=1)
def load_metric_overlap_registry() -> dict[str, Any]:
    path = REGISTRY_DIR / "metric_overlap_registry.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_bridge(company_id: str | None = None) -> dict[str, list[str]]:
    reg = load_metric_family_registry()
    out: dict[str, list[str]] = {}
    for family in reg.get("families") or []:
        bridge = family.get("semantic_bridge") or {}
        if not bridge:
            continue
        if company_id and not _family_applies(family, company_id):
            continue
        scope = str(family.get("scope") or "generic")
        if scope == "pilot_only" and company_id and company_id not in (family.get("companies") or []):
            continue
        for k, v in bridge.items():
            existing = out.setdefault(k, [])
            for a in v:
                if a not in existing:
                    existing.append(a)

    overlap = load_metric_overlap_registry()
    for _fid, fam_map in (overlap.get("pair_bridge_aliases") or {}).items():
        for _lid, item_map in (fam_map or {}).items():
            for item_key, aliases in (item_map or {}).items():
                existing = out.setdefault(item_key, [])
                for a in aliases or []:
                    if a not in existing:
                        existing.append(a)
    return out


def governance_anchor_metrics(company_id: str = "demo_company") -> frozenset[str]:
    reg = load_metric_family_registry()
    for family in reg.get("families") or []:
        if family.get("family_id") == "governance_financial_anchor":
            if company_id in (family.get("companies") or []):
                return frozenset(family.get("anchor_metrics") or [])
    return frozenset()


def governance_anchor_doc(company_id: str = "demo_company") -> str | None:
    reg = load_metric_family_registry()
    for family in reg.get("families") or []:
        if family.get("family_id") == "governance_financial_anchor":
            if company_id in (family.get("companies") or []):
                by_company = family.get("anchor_logical_doc_by_company") or {}
                if company_id in by_company:
                    return str(by_company[company_id])
                return family.get("anchor_logical_doc")
    return None


def resolve_narrative_probe_logical_doc(company_id: str, resolver: str | None = None) -> str | None:
    """Resolve probe logical doc from company registry (document_type or priority)."""
    docs = logical_documents(company_id)
    if not docs:
        return None
    resolver = resolver or "sustainability_report"
    if resolver == "sustainability_report":
        ranked = sorted(
            docs.items(),
            key=lambda x: int(x[1].get("narrative_probe_priority") or 99),
        )
        for lid, spec in ranked:
            if spec.get("document_type") == "sustainability_report":
                return lid
        for lid, spec in ranked:
            if spec.get("scope") == "generic":
                return lid
    routing = routing_defaults(company_id)
    fallback = routing.get("fallback_logical_doc")
    if fallback and fallback in docs:
        return str(fallback)
    return next(iter(docs), None)


def routing_defaults(company_id: str) -> dict[str, Any]:
    reg = load_company_doc_registry()
    defaults = dict(reg.get("defaults") or {}).get("routing_defaults") or {}
    company = dict(company_config(company_id).get("routing_defaults") or {})
    return {**defaults, **company}


def role_label_for_doc(company_id: str, logical_id: str, *, kind: str) -> str:
    doc = logical_documents(company_id).get(logical_id) or {}
    labels = doc.get("role_labels") or {}
    key = "qualitative" if kind == "qualitative" else "quantitative"
    return str(labels.get(key) or labels.get("default") or "")


def routing_profile() -> dict[str, Any]:
    reg = load_source_role_registry()
    return dict(reg.get("routing") or {})


def retrieval_policy() -> dict[str, Any]:
    reg = load_source_role_registry()
    return dict(reg.get("retrieval_policy") or {})


def csv_supporting_logical_doc(company_id: str) -> str | None:
    routing = routing_defaults(company_id)
    lid = routing.get("csv_supporting_logical_doc")
    if lid and lid in logical_documents(company_id):
        return str(lid)
    return None


def fallback_logical_doc(company_id: str) -> str | None:
    routing = routing_defaults(company_id)
    lid = routing.get("fallback_logical_doc")
    docs = logical_documents(company_id)
    if lid and lid in docs:
        return str(lid)
    return next(iter(docs), None) if docs else None


def cross_document_signals() -> list[dict[str, Any]]:
    return list(routing_profile().get("cross_document_signals") or [])


def narrative_probe_config(company_id: str = "demo_company") -> dict[str, Any]:
    """Merge probe config from families that declare probe_metrics."""
    reg = load_metric_family_registry()
    metrics: set[str] = set()
    logical_doc: str | None = None
    patterns: list[dict[str, Any]] = []
    for family in reg.get("families") or []:
        if not _family_applies(family, company_id):
            continue
        probe_m = family.get("probe_metrics") or []
        if not probe_m:
            continue
        metrics.update(str(m) for m in probe_m)
        if not logical_doc:
            if family.get("probe_logical_doc"):
                logical_doc = str(family.get("probe_logical_doc"))
            elif family.get("probe_logical_doc_resolver"):
                logical_doc = resolve_narrative_probe_logical_doc(
                    company_id, str(family.get("probe_logical_doc_resolver"))
                )
        patterns.extend(family.get("narrative_patterns") or [])
    if not logical_doc:
        logical_doc = resolve_narrative_probe_logical_doc(company_id)
    return {
        "metrics": frozenset(metrics),
        "logical_doc": logical_doc,
        "patterns": patterns,
    }


def compile_narrative_patterns(company_id: str = "demo_company") -> list[tuple[str, re.Pattern[str]]]:
    """Compile narrative patterns from all applicable metric families."""
    reg = load_metric_family_registry()
    compiled: list[tuple[str, re.Pattern[str]]] = []
    seen: set[tuple[str, str]] = set()
    for family in reg.get("families") or []:
        if not _family_applies(family, company_id):
            continue
        for entry in family.get("narrative_patterns") or []:
            label = str(entry.get("label") or "")
            pattern = str(entry.get("pattern") or "")
            key = (label, pattern)
            if not label or not pattern or key in seen:
                continue
            seen.add(key)
            flags = re.IGNORECASE if entry.get("ignore_case", True) else 0
            compiled.append((label, re.compile(pattern, flags)))
    return compiled


def ingest_profile(company_id: str = "demo_company") -> dict[str, Any]:
    reg = load_company_doc_registry()
    defaults = dict(reg.get("defaults") or {}).get("ingest_profile") or {}
    company = company_config(company_id).get("ingest_profile") or {}
    merged = {**defaults, **company}
    return {
        "chunk_size": int(merged.get("chunk_size") or 900),
        "chunk_overlap": int(merged.get("chunk_overlap") or 150),
        "supported_extensions": list(
            merged.get("supported_extensions")
            or [".md", ".markdown", ".html", ".htm", ".json", ".jsonl", ".xml", ".csv", ".txt", ".pdf"]
        ),
    }


def retrieval_boost(logical_doc_id: str, company_id: str = "demo_company") -> float:
    reg = load_source_role_registry()
    boosts = reg.get("retrieval_boosts") or {}
    doc_cfg = logical_documents(company_id).get(logical_doc_id) or {}
    if doc_cfg.get("scope") == "pilot_only" and logical_doc_id in boosts:
        return float(boosts.get(logical_doc_id) or 1.0)
    return float(boosts.get(logical_doc_id) or 1.0)


def role_classification(role_desc: str) -> str:
    reg = load_source_role_registry()
    desc = (role_desc or "").lower()
    for rule in reg.get("classification_rules") or []:
        if any(tok in desc for tok in rule.get("match_tokens") or []):
            return str(rule.get("role_class") or "required")
    return str(reg.get("default_role_class") or "required")


def export_registry_snapshot() -> dict[str, Any]:
    return {
        "company_doc_registry": load_company_doc_registry(),
        "metric_family_registry": load_metric_family_registry(),
        "source_role_registry": load_source_role_registry(),
    }
