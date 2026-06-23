"""Map logical document IDs to corpus document_id strings via company registry."""

from __future__ import annotations

from enterprise_docs.registries import corpus_path_patterns, logical_documents


def _score_corpus_match(doc_id: str, hint: str, *, doc_type: str | None = None) -> float:
    """Rank corpus document_id matches for logical-doc routing (family-level, not case-specific)."""
    if not hint:
        return 0.0
    doc_l = doc_id.lower()
    hint_l = hint.lower()
    if hint_l not in doc_l:
        return 0.0
    score = float(len(hint_l))
    if doc_type == "sustainability_report":
        if any(tok in doc_l for tok in ("sustain", "지속가능", "impact", "임팩트")):
            score += 40.0
        if doc_l.endswith("_pdf"):
            score += 8.0
    if doc_type == "governance_report" or doc_type == "dart_filing":
        if any(tok in doc_l for tok in ("지배구조", "governance", "dart", "공시")):
            score += 35.0
        if doc_l.endswith("_xml"):
            score += 6.0
    if doc_l.endswith("_json"):
        score -= 5.0
    return score


def matching_corpus_documents_for_logical(
    logical_id: str,
    corpus_document_ids: list[str],
    *,
    company_id: str = "demo_company",
    min_score: float = 1.0,
) -> list[str]:
    """All corpus document_ids that match a logical doc (not just top-1)."""
    spec = logical_documents(company_id).get(logical_id) or {}
    hints: list[str] = []
    for token in spec.get("corpus_match_tokens") or []:
        hints.append(str(token))
    path_hint = str(spec.get("path_hint") or "")
    if path_hint:
        hints.append(path_hint)
    patterns = corpus_path_patterns(company_id)
    if logical_id in patterns and patterns[logical_id] not in hints:
        hints.append(patterns[logical_id])

    doc_type = str(spec.get("document_type") or "")
    scored: list[tuple[float, str]] = []
    for doc_id in corpus_document_ids:
        best = 0.0
        for hint in hints:
            if hint:
                best = max(best, _score_corpus_match(doc_id, hint, doc_type=doc_type or None))
        if best >= min_score:
            scored.append((best, doc_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [doc_id for _, doc_id in scored]


def corpus_document_id(
    logical_id: str,
    corpus_document_ids: list[str],
    *,
    company_id: str = "demo_company",
) -> str | None:
    spec = logical_documents(company_id).get(logical_id) or {}
    hints: list[str] = []
    for token in spec.get("corpus_match_tokens") or []:
        hints.append(str(token))
    path_hint = str(spec.get("path_hint") or "")
    if path_hint:
        hints.append(path_hint)
    patterns = corpus_path_patterns(company_id)
    if logical_id in patterns and patterns[logical_id] not in hints:
        hints.append(patterns[logical_id])

    doc_type = str(spec.get("document_type") or "")
    best_doc: str | None = None
    best_score = 0.0
    for hint in hints:
        if not hint:
            continue
        for doc_id in corpus_document_ids:
            score = _score_corpus_match(doc_id, hint, doc_type=doc_type or None)
            if score > best_score:
                best_score = score
                best_doc = doc_id
    return best_doc


def build_logical_to_corpus_map(
    corpus_document_ids: list[str],
    *,
    company_id: str = "demo_company",
) -> dict[str, str]:
    patterns = corpus_path_patterns(company_id)
    mapping: dict[str, str] = {}
    for logical_id in patterns:
        resolved = corpus_document_id(logical_id, corpus_document_ids, company_id=company_id)
        if resolved:
            mapping[logical_id] = resolved
    return mapping


def logical_ids_to_corpus(
    logical_ids: list[str],
    logical_to_corpus: dict[str, str],
) -> list[str]:
    out: list[str] = []
    for lid in logical_ids:
        cid = logical_to_corpus.get(lid)
        if cid and cid not in out:
            out.append(cid)
    return out


# Backward-compatible demo export (registry is source of truth)
CORPUS_DOC_PATTERNS: dict[str, str] = corpus_path_patterns("demo_company")
