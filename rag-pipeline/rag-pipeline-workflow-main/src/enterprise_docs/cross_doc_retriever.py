"""Cross-document retrieval with document diversification and role-aware sub-queries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from enterprise_docs.doc_mapping import build_logical_to_corpus_map, logical_ids_to_corpus
from enterprise_docs.registries import (
    csv_supporting_logical_doc,
    retrieval_boost,
    retrieval_policy,
)
from enterprise_docs.retrieval_index import build_corpus_index, score_units, unit_search_text


def _company_id(plan_row: dict[str, Any]) -> str:
    return str(plan_row.get("company_id") or "demo_company")


@dataclass
class DocScore:
    logical_document_id: str
    corpus_document_id: str
    score: float
    unit_count: int = 0


@dataclass
class UnitHit:
    unit_id: str
    corpus_document_id: str
    logical_document_id: str
    score: float
    evidence_text: str
    section: str | None = None
    role: str | None = None
    is_table_unit: bool = False


@dataclass
class RetrievalResult:
    item_id: str
    answer_mode: str
    question: str
    top_docs: list[DocScore] = field(default_factory=list)
    top_units: list[UnitHit] = field(default_factory=list)
    evidence_plan_coverage: float = 0.0
    required_doc_hit_rate: float = 0.0
    missing_docs: list[str] = field(default_factory=list)
    missing_roles: list[str] = field(default_factory=list)
    parser_fail: bool = False
    role_coverage: float = 0.0
    role_hits: dict[str, bool] = field(default_factory=dict)
    missing_roles_after_retrieval: list[str] = field(default_factory=list)
    csv_role_hit: bool = False
    table_unit_preferred: bool = False
    table_candidates_seen: int = 0
    narrative_candidates_seen: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["top_docs"] = [asdict(x) for x in self.top_docs]
        d["top_units"] = [asdict(x) for x in self.top_units]
        return d


def _logical_for_corpus(corpus_doc_id: str, logical_to_corpus: dict[str, str]) -> str:
    for logical, corpus in logical_to_corpus.items():
        if corpus == corpus_doc_id:
            return logical
    return corpus_doc_id


def _aggregate_doc_scores(
    ranked: list[tuple[dict[str, Any], float]],
    logical_to_corpus: dict[str, str],
) -> dict[str, DocScore]:
    corpus_to_logical = {v: k for k, v in logical_to_corpus.items()}
    by_doc: dict[str, DocScore] = {}
    for unit, score in ranked:
        corpus_id = str(unit.get("document_id") or "")
        logical_id = corpus_to_logical.get(corpus_id, corpus_id)
        if corpus_id not in by_doc:
            by_doc[corpus_id] = DocScore(
                logical_document_id=logical_id,
                corpus_document_id=corpus_id,
                score=float(score),
                unit_count=1,
            )
        else:
            entry = by_doc[corpus_id]
            entry.score = max(entry.score, float(score))
            entry.unit_count += 1
    return by_doc


def _planned_corpus_ids(plan_row: dict[str, Any], logical_to_corpus: dict[str, str]) -> set[str]:
    logical = list(plan_row.get("primary_document_ids") or []) + list(
        plan_row.get("supporting_document_ids") or []
    )
    return {logical_to_corpus[lid] for lid in logical if lid in logical_to_corpus}


def _is_table_unit(unit: dict[str, Any]) -> bool:
    text = str(unit.get("evidence_text") or unit.get("text") or "")
    return "|" in text and text.count("|") >= 8


def _is_financial_metric_question(plan_row: dict[str, Any]) -> bool:
    blob = " ".join(
        str(plan_row.get(k) or "")
        for k in ("question", "item", "subcategory", "category", "domain")
    )
    markers = retrieval_policy().get("financial_metric_markers") or []
    return any(str(m) in blob for m in markers)


def _corpus_units(index: dict[str, Any], corpus_id: str) -> list[dict[str, Any]]:
    return [u for u in index.get("units", []) if str(u.get("document_id") or "") == corpus_id]


def _inject_table_units_first(
    role_ranked: dict[str, list[tuple[dict[str, Any], float]]],
    index: dict[str, Any],
    planned_corpus: list[str],
    *,
    prefer_tables: bool,
) -> tuple[int, int]:
    """Ensure table units from each planned doc are candidates before narrative bullets."""
    table_seen = 0
    narrative_seen = 0
    if not prefer_tables:
        return table_seen, narrative_seen

    policy = retrieval_policy()
    table_inject_score = float(policy.get("table_inject_score") or 2.5)

    for corpus_id in planned_corpus:
        corpus_units = _corpus_units(index, corpus_id)
        table_units = [u for u in corpus_units if _is_table_unit(u)]
        narrative_units = [u for u in corpus_units if not _is_table_unit(u)]
        table_seen += len(table_units)
        narrative_seen += len(narrative_units)

        existing = {str(u.get("unit_id") or "") for u, _ in role_ranked.get(corpus_id, [])}
        boosted: list[tuple[dict[str, Any], float]] = []
        for tu in table_units:
            uid = str(tu.get("unit_id") or "")
            if uid and uid not in existing:
                boosted.append((tu, table_inject_score))
                existing.add(uid)
        for u, s in role_ranked.get(corpus_id, []):
            boosted.append((u, s))
        boosted.sort(key=lambda x: x[1], reverse=True)
        role_ranked[corpus_id] = boosted

    return table_seen, narrative_seen


def _role_subqueries(plan_row: dict[str, Any]) -> dict[str, str]:
    """Map logical_document_id -> sub-query text for role-aware retrieval."""
    roles: dict[str, str] = plan_row.get("roles") or {}
    base = str(plan_row.get("question") or "")
    item = str(plan_row.get("item") or "")
    sub = str(plan_row.get("subcategory") or "")
    queries: dict[str, str] = {}
    for logical_id, role_desc in roles.items():
        parts = [base, item, sub, role_desc]
        queries[logical_id] = " ".join(p for p in parts if p)
    for lid in plan_row.get("supporting_document_ids") or []:
        if lid not in queries:
            queries[lid] = f"{base} {item} summary aggregate".strip()
    return queries


def _score_units_for_doc(
    query: str,
    index: dict[str, Any],
    corpus_id: str,
    *,
    boost: float = 1.0,
    pool: int = 24,
    prefer_tables: bool = False,
) -> list[tuple[dict[str, Any], float]]:
    ranked = score_units(query, index, pool=pool)
    table_multiplier = float(retrieval_policy().get("table_score_multiplier") or 1.6)
    out: list[tuple[dict[str, Any], float]] = []
    for unit, score in ranked:
        if str(unit.get("document_id") or "") == corpus_id:
            s = float(score) * boost
            text = str(unit.get("evidence_text") or unit.get("text") or "")
            if prefer_tables and "|" in text and text.count("|") >= 4:
                s *= table_multiplier
            out.append((unit, s))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _retrieve_single(
    question: str,
    plan_row: dict[str, Any],
    index: dict[str, Any],
    logical_to_corpus: dict[str, str],
    *,
    top_k_units: int = 5,
    top_k_docs: int = 3,
) -> RetrievalResult:
    ranked = score_units(question, index)
    planned_corpus = _planned_corpus_ids(plan_row, logical_to_corpus)
    planned_boost = float(retrieval_policy().get("planned_corpus_boost") or 1.25)
    if planned_corpus:
        boosted: list[tuple[dict[str, Any], float]] = []
        for unit, score in ranked:
            cid = str(unit.get("document_id") or "")
            boost = planned_boost if cid in planned_corpus else 1.0
            boosted.append((unit, score * boost))
        ranked = sorted(boosted, key=lambda x: x[1], reverse=True)

    by_doc = _aggregate_doc_scores(ranked, logical_to_corpus)
    top_docs = sorted(by_doc.values(), key=lambda d: d.score, reverse=True)[:top_k_docs]

    top_units: list[UnitHit] = []
    for unit, score in ranked[:top_k_units]:
        corpus_id = str(unit.get("document_id") or "")
        top_units.append(
            UnitHit(
                unit_id=str(unit.get("unit_id") or ""),
                corpus_document_id=corpus_id,
                logical_document_id=_logical_for_corpus(corpus_id, logical_to_corpus),
                score=round(float(score), 4),
                evidence_text=(unit.get("evidence_text") or unit.get("text") or "")[:800],
                section=unit.get("section"),
            )
        )

    required_logical = list(plan_row.get("primary_document_ids") or [])
    required_corpus = logical_ids_to_corpus(required_logical, logical_to_corpus)
    hit_corpus = {u.corpus_document_id for u in top_units}
    missing = [lid for lid, cid in zip(required_logical, required_corpus) if cid not in hit_corpus]
    if not required_corpus and required_logical:
        missing = [lid for lid in required_logical if logical_to_corpus.get(lid) is None]

    coverage = 1.0 if not required_logical else (
        sum(1 for cid in required_corpus if cid in hit_corpus) / max(1, len(required_corpus))
    )
    doc_hit_rate = 1.0 if not required_corpus else (
        sum(1 for cid in required_corpus if cid in {d.corpus_document_id for d in top_docs})
        / max(1, len(required_corpus))
    )

    parser_fail = not ranked or all(not unit_search_text(u).strip() for u, _ in ranked[:3])

    return RetrievalResult(
        item_id=str(plan_row.get("item_id") or ""),
        answer_mode=str(plan_row.get("answer_mode") or ""),
        question=question,
        top_docs=top_docs,
        top_units=top_units,
        evidence_plan_coverage=round(coverage, 4),
        required_doc_hit_rate=round(doc_hit_rate, 4),
        missing_docs=missing,
        missing_roles=[r for r in (plan_row.get("roles") or {}) if r in missing],
        parser_fail=parser_fail,
        role_coverage=1.0,
        role_hits={},
        missing_roles_after_retrieval=[],
    )


def _retrieve_cross(
    question: str,
    plan_row: dict[str, Any],
    index: dict[str, Any],
    logical_to_corpus: dict[str, str],
    *,
    top_k_units: int = 10,
    units_per_doc: int = 3,
    max_docs: int = 5,
) -> RetrievalResult:
    roles = plan_row.get("roles") or {}
    role_queries = _role_subqueries(plan_row)
    planned_logical = list(plan_row.get("primary_document_ids") or []) + list(
        plan_row.get("supporting_document_ids") or []
    )
    planned_corpus = logical_ids_to_corpus(planned_logical, logical_to_corpus)

    # Global ranked pool
    ranked_global = score_units(question, index, pool=64)
    by_doc = _aggregate_doc_scores(ranked_global, logical_to_corpus)

    company_id = _company_id(plan_row)
    csv_logical = csv_supporting_logical_doc(company_id)
    csv_floor_score = float(retrieval_policy().get("csv_floor_min_score") or 0.5)

    # Role-aware per-doc retrieval
    role_ranked: dict[str, list[tuple[dict[str, Any], float]]] = {}
    for logical_id in dict.fromkeys(planned_logical):
        corpus_id = logical_to_corpus.get(logical_id)
        if not corpus_id:
            continue
        sub_q = role_queries.get(logical_id, question)
        boost = retrieval_boost(logical_id, company_id)
        role_ranked[corpus_id] = _score_units_for_doc(
            sub_q, index, corpus_id, boost=boost, pool=32, prefer_tables=True
        )
        # Registry CSV floor: only when company declares csv supporting doc
        if csv_logical and logical_id == csv_logical and not role_ranked[corpus_id]:
            for unit, score in ranked_global:
                if str(unit.get("document_id") or "") == corpus_id:
                    role_ranked[corpus_id].append(
                        (unit, max(float(score), csv_floor_score) * boost)
                    )
            role_ranked[corpus_id] = role_ranked[corpus_id][:units_per_doc]

    prefer_tables = _is_financial_metric_question(plan_row)
    table_seen, narrative_seen = _inject_table_units_first(
        role_ranked,
        index,
        list(planned_corpus),
        prefer_tables=prefer_tables,
    )

    selected_docs: list[DocScore] = []
    seen_corpus: set[str] = set()
    for corpus_id in planned_corpus:
        if corpus_id in by_doc and corpus_id not in seen_corpus:
            doc = by_doc[corpus_id]
            if corpus_id in role_ranked and role_ranked[corpus_id]:
                doc.score = max(doc.score, role_ranked[corpus_id][0][1])
            selected_docs.append(doc)
            seen_corpus.add(corpus_id)

    for doc in sorted(by_doc.values(), key=lambda d: d.score, reverse=True):
        if len(selected_docs) >= max_docs:
            break
        if doc.corpus_document_id not in seen_corpus:
            selected_docs.append(doc)
            seen_corpus.add(doc.corpus_document_id)

    selected_docs.sort(key=lambda d: d.score, reverse=True)

    # Merge units: role-specific first, then global diversify
    merged_units: list[tuple[dict[str, Any], float, str]] = []
    seen_unit_ids: set[str] = set()

    for logical_id in dict.fromkeys(planned_logical):
        corpus_id = logical_to_corpus.get(logical_id)
        if not corpus_id:
            continue
        for unit, score in role_ranked.get(corpus_id, [])[:units_per_doc]:
            uid = str(unit.get("unit_id") or "")
            if uid and uid not in seen_unit_ids:
                merged_units.append((unit, score, logical_id))
                seen_unit_ids.add(uid)

    for unit, score in ranked_global:
        if len(merged_units) >= top_k_units:
            break
        uid = str(unit.get("unit_id") or "")
        if uid and uid not in seen_unit_ids:
            cid = str(unit.get("document_id") or "")
            merged_units.append((unit, score, _logical_for_corpus(cid, logical_to_corpus)))
            seen_unit_ids.add(uid)

    merged_units.sort(key=lambda x: x[1], reverse=True)
    merged_units = merged_units[:top_k_units]

    top_units: list[UnitHit] = []
    table_hits = 0
    for unit, score, logical_id in merged_units:
        corpus_id = str(unit.get("document_id") or "")
        is_table = _is_table_unit(unit)
        if is_table:
            table_hits += 1
        top_units.append(
            UnitHit(
                unit_id=str(unit.get("unit_id") or ""),
                corpus_document_id=corpus_id,
                logical_document_id=logical_id,
                score=round(float(score), 4),
                evidence_text=(unit.get("evidence_text") or unit.get("text") or "")[:1200],
                section=unit.get("section"),
                role=(roles.get(logical_id) if isinstance(roles, dict) else None),
                is_table_unit=is_table,
            )
        )

    required_logical = list(dict.fromkeys(planned_logical))
    hit_logical_units = {u.logical_document_id for u in top_units}
    hit_corpus_docs = {d.corpus_document_id for d in selected_docs}

    missing: list[str] = []
    role_hits: dict[str, bool] = {}
    for lid in required_logical:
        cid = logical_to_corpus.get(lid)
        hit = lid in hit_logical_units
        role_hits[lid] = hit
        if cid is None:
            missing.append(lid)
        elif not hit:
            missing.append(lid)

    missing_roles = [lid for lid in roles if not role_hits.get(lid, False)]
    role_coverage = (
        sum(1 for lid in roles if role_hits.get(lid, False)) / max(1, len(roles))
        if roles
        else 1.0
    )
    csv_hit = bool(csv_logical and role_hits.get(csv_logical, False))

    coverage = 1.0 if not required_logical else (
        sum(1 for lid in required_logical if role_hits.get(lid, False)) / max(1, len(required_logical))
    )
    doc_hit_rate = 1.0 if not planned_corpus else (
        sum(1 for cid in planned_corpus if cid in hit_corpus_docs) / max(1, len(planned_corpus))
    )

    parser_fail = not merged_units and (
        not ranked_global or all(not unit_search_text(u).strip() for u, _ in ranked_global[:5])
    )

    return RetrievalResult(
        item_id=str(plan_row.get("item_id") or ""),
        answer_mode=str(plan_row.get("answer_mode") or ""),
        question=question,
        top_docs=selected_docs[:max_docs],
        top_units=top_units,
        evidence_plan_coverage=round(coverage, 4),
        required_doc_hit_rate=round(doc_hit_rate, 4),
        missing_docs=missing,
        missing_roles=missing_roles,
        parser_fail=parser_fail,
        role_coverage=round(role_coverage, 4),
        role_hits=role_hits,
        missing_roles_after_retrieval=missing_roles,
        csv_role_hit=csv_hit,
        table_unit_preferred=prefer_tables and table_hits > 0,
        table_candidates_seen=table_seen,
        narrative_candidates_seen=narrative_seen,
    )


def retrieve_for_plan(
    plan_row: dict[str, Any],
    index: dict[str, Any],
    logical_to_corpus: dict[str, str],
    *,
    top_k_units: int = 5,
) -> RetrievalResult:
    question = str(plan_row.get("question") or "")
    mode = str(plan_row.get("answer_mode") or "")
    if mode == "cross_document_answer":
        return _retrieve_cross(
            question,
            plan_row,
            index,
            logical_to_corpus,
            top_k_units=max(top_k_units, 10),
        )
    return _retrieve_single(
        question,
        plan_row,
        index,
        logical_to_corpus,
        top_k_units=top_k_units,
    )


def build_index_from_units(
    units: list[dict[str, Any]],
    *,
    company_id: str = "demo_company",
) -> tuple[dict[str, Any], dict[str, str]]:
    full = build_corpus_index(units)
    index = full.get(company_id) or {"units": [], "bm25": None, "tokenized": []}
    corpus_ids = sorted({str(u.get("document_id") or "") for u in units})
    logical_map = build_logical_to_corpus_map(corpus_ids, company_id=company_id)
    return index, logical_map
