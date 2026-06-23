"""Audit enterprise internal-doc code for registry vs pilot-only dependencies."""

from __future__ import annotations

from typing import Any

AUDIT_ENTRIES: list[dict[str, Any]] = [
    {
        "component": "registries.py",
        "driver": "already_registry_driven",
        "registry_source": ["company_doc_registry", "metric_family_registry", "source_role_registry"],
        "pilot_dependency": "none",
        "migration_path": "source of truth — extend JSON only",
    },
    {
        "component": "doc_mapping.py",
        "driver": "already_registry_driven",
        "registry_source": ["company_doc_registry"],
        "pilot_dependency": "CORPUS_DOC_PATTERNS re-export for backward compat only",
        "migration_path": "remove CORPUS_DOC_PATTERNS export when downstream migrated",
    },
    {
        "component": "doc_router.py",
        "driver": "already_registry_driven",
        "registry_source": ["company_doc_registry", "source_role_registry"],
        "pilot_dependency": "pilot_only csv_supporting_logical_doc on demo_company only",
        "migration_path": "extend role_labels per company in registry when new corps added",
    },
    {
        "component": "structured_extractor.py",
        "driver": "already_registry_driven",
        "registry_source": ["metric_family_registry"],
        "pilot_dependency": "none — aliases/patterns loaded from registry",
        "migration_path": "extend metric_family_registry families only",
    },
    {
        "component": "evidence_aggregator.py",
        "driver": "already_registry_driven",
        "registry_source": ["metric_family_registry", "company_doc_registry"],
        "pilot_dependency": "governance_financial_anchor pilot_only on demo_company",
        "migration_path": "add anchor families per company when structured tables exist",
    },
    {
        "component": "cross_doc_retriever.py",
        "driver": "already_registry_driven",
        "registry_source": ["source_role_registry", "company_doc_registry"],
        "pilot_dependency": "csv floor applies only when csv_supporting_logical_doc configured",
        "migration_path": "per-company retrieval_policy overrides if needed",
    },
    {
        "component": "holdout_harness.py",
        "driver": "already_registry_driven",
        "registry_source": ["company_doc_registry"],
        "pilot_dependency": "musinsa filter fallback in loader",
        "migration_path": "corpus_filter fully in company_doc_registry",
    },
    {
        "component": "readiness_model.py",
        "driver": "already_registry_driven",
        "registry_source": ["source_role_registry"],
        "pilot_dependency": "minimal",
        "migration_path": "wire synthesis_gate config explicitly",
    },
    {
        "component": "langgraph_handoff.py",
        "driver": "already_registry_driven",
        "registry_source": ["source_role_registry"],
        "pilot_dependency": "ALLOWED_HANDOFF_STATES duplicate in code",
        "migration_path": "single source: synthesis_gate in registry",
    },
    {
        "component": "ingest.py",
        "driver": "already_registry_driven",
        "registry_source": ["company_doc_registry.defaults.ingest_profile"],
        "pilot_dependency": "none",
        "migration_path": "per-company ingest overrides in registry",
    },
    {
        "component": "parsers.py",
        "driver": "already_registry_driven",
        "registry_source": [],
        "pilot_dependency": "generic format detection — no company coupling",
        "migration_path": "no change",
    },
    {
        "component": "rule_inventory.py",
        "driver": "already_registry_driven",
        "registry_source": ["rule_inventory.json"],
        "pilot_dependency": "audit artifact only",
        "migration_path": "sync with registry changes",
    },
]


def classify_summary() -> dict[str, Any]:
    by_driver: dict[str, list[str]] = {
        "already_registry_driven": [],
        "partially_registry_driven": [],
        "still_code_driven": [],
        "pilot_only": [],
    }
    for entry in AUDIT_ENTRIES:
        driver = entry["driver"]
        by_driver.setdefault(driver, []).append(entry["component"])
        dep = str(entry.get("pilot_dependency") or "")
        if "pilot_only" in dep.lower() and driver == "already_registry_driven":
            by_driver["pilot_only"].append(entry["component"])

    pilot_hotspots = [
        e["component"]
        for e in AUDIT_ENTRIES
        if e["driver"] != "already_registry_driven"
    ]
    pilot_only_labeled = list(dict.fromkeys(by_driver.get("pilot_only") or []))

    return {
        "entries": AUDIT_ENTRIES,
        "counts": {
            "already_registry_driven": len(by_driver.get("already_registry_driven") or []),
            "partially_registry_driven": len(by_driver.get("partially_registry_driven") or []),
            "still_code_driven": len(by_driver.get("still_code_driven") or []),
            "pilot_only_labeled": len(pilot_only_labeled),
        },
        "by_driver": {k: v for k, v in by_driver.items() if k != "pilot_only"},
        "pilot_only_components": pilot_only_labeled,
        "pilot_hotspots": pilot_hotspots,
    }


def export_migration_audit() -> dict[str, Any]:
    summary = classify_summary()
    return {
        "version": "1.2.0",
        "description": "Registry migration audit for enterprise internal-doc lane",
        **summary,
        "migration_priority": [
            "metric_family_registry → holdout governance/employee/environment families",
            "company_doc_registry → new holdout companies with role_labels",
            "source_role_registry → synthesis_gate wiring in readiness_model",
        ],
    }
