"""Fail classification, source/answer matching, and eval row assembly."""

from __future__ import annotations

from typing import Any

from dataset_excel.constants import FTC_BLOCKED_URL
from dataset_excel.extractor_utils import close_enough, normalize_path, numbers_in_text
from dataset_excel.extractors import extract_answer
from dataset_excel.family_router import infer_question_profile, rerank_evidence_for_family
from dataset_excel.sanction import sanction_lane_from_evidence, sanction_lane_from_url
from dataset_excel.retrieval import retrieve

SEMANTIC_AUDIT_NOTES: dict[str, str] = {
    "emni-0237": "SME follow-up: workbook label may not match account in OFS",
}


def classify_fail_type(row: dict[str, Any]) -> str | None:
    if row.get("scoring_rule") == "abstain_expected":
        return None
    if row.get("semantic_ambiguity") or row.get("semantic_audit_note"):
        return "semantic_ambiguity"
    answer_ok = bool(row.get("answer_correct"))
    retrieval_ok = bool(row.get("retrieval_hit_top1"))
    if answer_ok and not retrieval_ok:
        return "answer_correct_but_wrong_top1"
    if not answer_ok:
        return "answer_fail"
    return None


def diagnostic_tags(row: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    source_url = str(row.get("source_url") or "")
    fail_type = row.get("fail_type")
    family = str(row.get("question_family") or "")

    if row.get("semantic_ambiguity") or row.get("semantic_audit_note"):
        tags.append("semantic_ambiguity")
    if FTC_BLOCKED_URL in source_url:
        tags.append("coverage_gap")
    if fail_type == "answer_fail" and family in (
        "sanction_safetykorea",
        "sanction_pipc",
        "financial_tax",
        "financial_generic",
        "financial_capex",
        "financial_revenue",
        "financial_interest",
    ):
        tags.append("rule_extractor_gap")
    return sorted(set(tags))


def source_match(row: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    expected_doc = (row.get("doc_title") or "").strip()
    expected_url = (row.get("source_url") or "").strip()
    expected_file = normalize_path(row.get("file_url"))
    expected_lane = sanction_lane_from_url(expected_url) if expected_doc == "제재이력.json" else None

    for item in evidence:
        meta = item.get("metadata") or {}
        doc_title = (meta.get("doc_title") or "").strip()
        file_url = normalize_path(meta.get("file_url"))
        source_url = str(meta.get("source_url") or "")
        lane = sanction_lane_from_evidence(item)

        if expected_lane and lane == expected_lane:
            return True
        if expected_doc == "제재이력.json" and expected_url and expected_url in source_url:
            return True
        if expected_doc and doc_title == expected_doc:
            return True
        if expected_file and expected_file in file_url:
            return True
        if expected_doc:
            continue
        if expected_url and expected_url in source_url:
            return True
    return False


def answer_match(row: dict[str, Any], predicted: dict[str, Any]) -> bool:
    if row.get("scoring_rule") == "abstain_expected":
        return bool(predicted.get("abstain") or predicted.get("insufficient"))
    gold = row.get("gold_answer_normalized")
    answer = str(predicted.get("answer") or "")
    if isinstance(gold, (int, float)):
        nums = numbers_in_text(answer)
        return any(close_enough(n, float(gold), row.get("unit")) for n in nums)
    gold_text = str(row.get("gold_answer_raw") or gold or "").strip().lower()
    return gold_text and gold_text in answer.lower()


def eval_row(
    row: dict[str, Any],
    index: dict[str, Any],
    *,
    top_k: int,
    pool: int,
) -> dict[str, Any]:
    company_id = row["company_id"]
    profile = infer_question_profile(row)
    company_index = index.get(company_id) or {"units": [], "bm25": None, "tokenized": []}
    evidence = retrieve(row["question_text"], company_id, company_index, profile, top_k=top_k, pool=pool)
    evidence = rerank_evidence_for_family(evidence, profile)
    max_score = max((e["score"] for e in evidence), default=0.0)
    predicted = extract_answer(row, evidence, profile, max_score, company_index)
    is_abstain = row.get("scoring_rule") == "abstain_expected"

    retrieval_hit_top1 = source_match(row, evidence[:1]) if not is_abstain else True
    retrieval_hit_topk = source_match(row, evidence) if not is_abstain else True
    answer_ok = answer_match(row, predicted)
    abstain_ok = answer_match(row, predicted) if is_abstain else None

    question_id = row.get("question_id") or ""
    result = {
        "question_id": question_id,
        "company_id": row["company_id"],
        "partition": row.get("partition"),
        "scoring_rule": row.get("scoring_rule"),
        "question_family": profile.family,
        "question_text": row.get("question_text"),
        "gold_answer_raw": row.get("gold_answer_raw"),
        "gold_answer_normalized": row.get("gold_answer_normalized"),
        "doc_title": row.get("doc_title"),
        "source_url": row.get("source_url"),
        "file_url": row.get("file_url"),
        "predicted_answer": predicted.get("answer"),
        "predicted_abstain": predicted.get("abstain"),
        "predict_reason": predicted.get("reason"),
        "unsupported_family": predicted.get("unsupported_family"),
        "semantic_ambiguity": predicted.get("semantic_ambiguity"),
        "retrieval_hit_top1": retrieval_hit_top1,
        "retrieval_hit_topk": retrieval_hit_topk,
        "source_match_top1": retrieval_hit_top1,
        "source_match_topk": retrieval_hit_topk,
        "answer_correct": answer_ok,
        "abstain_correct": abstain_ok,
        "top_score": max_score,
        "top_doc_titles": [(e.get("metadata") or {}).get("doc_title") for e in evidence[:3]],
        "semantic_audit_note": SEMANTIC_AUDIT_NOTES.get(question_id),
    }
    result["fail_type"] = classify_fail_type(result)
    result["diagnostic_tags"] = diagnostic_tags(result)
    if predicted.get("coverage_gap"):
        result["coverage_gap"] = predicted.get("coverage_gap")
    elif FTC_BLOCKED_URL in str(row.get("source_url") or ""):
        result["coverage_gap"] = "coverage_gap_ftc_blocked"
    return result
