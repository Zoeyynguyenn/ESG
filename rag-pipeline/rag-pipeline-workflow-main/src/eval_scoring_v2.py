"""V2 rule-based scoring - on dinh, reason codes ro rang."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from benchmark_language import insufficient_phrases
from eval_set_io import parse_eval_set_rows
from rag_common import tokenize

INSUFFICIENT_PHRASES = insufficient_phrases()

# Reason codes chuan (per-question)
RC_RETRIEVAL_ALIAS_MISS = "retrieval_alias_miss"
RC_RETRIEVAL_NO_EVIDENCE = "retrieval_no_evidence"
RC_RETRIEVAL_TRUE_MISS = "retrieval_true_miss"
RC_CITATION_TOP1_MISS = "citation_top1_miss"
RC_CITATION_TOPK_MISS = "citation_topk_miss"
RC_GROUNDEDNESS_OVERLAP_LOW = "groundedness_overlap_low"
RC_GROUNDEDNESS_NO_EVIDENCE = "groundedness_no_evidence"
RC_ANSWER_NUMERIC_MISMATCH = "answer_numeric_mismatch"
RC_ANSWER_PHRASE_MISMATCH = "answer_phrase_mismatch"
RC_ANSWER_BOOLEAN_MISMATCH = "answer_boolean_mismatch"
RC_ANSWER_TOKEN_MISMATCH = "answer_token_mismatch"
RC_INSUFFICIENT_HANDLING_FAIL = "insufficient_handling_fail"
RC_INSUFFICIENT_UNEXPECTED = "insufficient_unexpected_flag"

EXTRACTED_FIELD_ALIASES: Dict[str, List[str]] = {
    "company_name": ["넥스트아이", "nexteye", "next eye"],
    "dart_corp_code": ["00614593", "corp_code"],
    "krx_market": ["kosdaq", "코스닥"],
    "homepage": [
        "nexteye.com",
        "information@nexteye",
        "source_system: homepage",
        'source_system": "homepage',
        "official homepage",
        "홈페이지",
    ],
    "export_type": ["raw_public_first", "company_evidence", "company evidence", "primary_benchmark_lane"],
    "export_version": ["1.1.1", "dataset_version"],
    "generated_at": ["2026-05-28t09:14:09", "exported_at"],
    "listing_status": ["listed", "listing_status", "상장"],
    "ticker": ["137940"],
    "country": ["south korea", "대한민국", "한국"],
    "industry_group": ["other", "기타"],
    "schema_version": ["1.1", "schema_version"],
    "record_count": ["270", "record_count"],
    "document_count": ["262", "document_count"],
    "size_tier": ["초소형", "size_tier"],
    "krx_confidence": ["70.85", "confidence"],
}


def parse_eval_set(path=None) -> List[Dict[str, str]]:
    from config import EVAL_SET_PATH

    p = path or EVAL_SET_PATH
    return [r.to_dict() for r in parse_eval_set_rows(p)]


def _norm_path(s: str) -> str:
    s = s.replace("\\", "/").lower().strip()
    s = re.sub(r"^data/rag_dataset/", "", s)
    return s


def source_aliases(expected: str) -> List[str]:
    aliases: List[str] = []
    for part in re.split(r"[;,]", expected):
        p = part.strip()
        if not p:
            continue
        aliases.append(_norm_path(p))
        aliases.append(p.split("/")[-1].lower())
        m = re.search(r"esg-[cx]\d+", p, re.I)
        if m:
            aliases.append(m.group(0).lower())
    kw_map = {
        "sources.md": ["sources.md", "sources"],
        "dataset_readme.md": ["dataset_readme", "readme"],
        "tcfd": ["tcfd", "esg-c03"],
        "google": ["google", "esg-c07", "environmental report"],
        "vinamilk": ["vinamilk", "esg-c08"],
        "ungc": ["ungc", "esg-c04", "questionnaire"],
        "ifrs": ["ifrs", "esg-c02", "navigator"],
        "oecd": ["oecd", "esg-c05"],
        "company_overview": ["company_overview"],
        "environment_policy": ["environment_policy"],
        "social_policy": ["social_policy"],
        "governance_policy": ["governance_policy"],
        "compliance_faq": ["compliance_faq"],
        "product_internal_faq": ["product_internal_faq"],
    }
    blob = expected.lower()
    for key, extras in kw_map.items():
        if key in blob:
            aliases.extend(extras)
    seen = set()
    out = []
    for a in aliases:
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def expects_insufficient(row: Dict[str, str]) -> bool:
    cat = (row.get("category") or "").lower()
    ans = (row.get("expected_answer") or "").lower()
    return (
        cat == "insufficient"
        or "khong du" in ans
        or "không đủ" in ans
        or "정보가 부족" in ans
        or row["id"].startswith("ESG-I")
        or row["id"].startswith("CP-I")
        or row["id"].startswith("CE-I")
    )


def _source_match(src: str, aliases: List[str]) -> bool:
    src_n = _norm_path(src)
    for a in aliases:
        if len(a) < 3:
            continue
        if a in src_n or src_n.endswith(a) or a in src_n.split("/")[-1]:
            return True
    return False


def score_retrieval(row: Dict[str, str], evidence: List[dict]) -> Tuple[bool, dict, List[str]]:
    from eval_source_matcher import match_evidence_to_expected, retrieval_reason_codes

    hit, match_reason, detail = match_evidence_to_expected(row, evidence, top1_only=False)
    codes = retrieval_reason_codes(hit, detail)
    hits = detail.get("hit_positions") or []
    return hit, {
        "aliases": source_aliases(row["expected_source"])[:6],
        "hit_positions": hits,
        "top1_hit": 0 in hits if hits else False,
        "match_reason": match_reason,
        "normalized_expected_source": detail.get("normalized_expected_source", ""),
        "normalized_top_sources": detail.get("normalized_top_sources", []),
        "expected_record_id": detail.get("expected_record_id", ""),
        "expected_doc_id": detail.get("expected_doc_id", ""),
        "fail_kind": detail.get("fail_kind", ""),
        "logic": detail.get("logic", "matcher_v2"),
    }, codes


def score_citation(row: Dict[str, str], evidence: List[dict]) -> Tuple[bool, dict, List[str]]:
    from eval_source_matcher import match_evidence_to_expected

    codes: List[str] = []
    if not evidence:
        codes.extend([RC_CITATION_TOP1_MISS, RC_CITATION_TOPK_MISS])
        return False, {"top1": False, "topk_any": False, "topk_count": 0, "logic": "top1_must_match_expected_source"}, codes
    top1_hit, match_reason, detail = match_evidence_to_expected(row, evidence, top1_only=True)
    topk_count = sum(
        1 for e in evidence if match_evidence_to_expected(row, [e], top1_only=True)[0]
    )
    if not top1_hit:
        codes.append(RC_CITATION_TOP1_MISS)
    if topk_count == 0:
        codes.append(RC_CITATION_TOPK_MISS)
    return top1_hit, {
        "top1": top1_hit,
        "topk_any": topk_count > 0,
        "topk_count": topk_count,
        "topk_size": len(evidence),
        "match_reason": match_reason,
        "normalized_expected_source": detail.get("normalized_expected_source", ""),
        "normalized_top_sources": detail.get("normalized_top_sources", []),
        "logic": "top1_matcher_v2",
    }, codes


_KO_ORDINALS = {
    "첫": "1",
    "하나": "1",
    "두": "2",
    "세": "3",
    "세번째": "3",
    "네": "4",
    "네번째": "4",
    "다섯": "5",
    "다섯번째": "5",
    "여섯": "6",
    "여섯번째": "6",
    "일곱": "7",
    "여덟": "8",
    "아홉": "9",
    "열": "10",
}


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip())


def _cjk_chunks(text: str, n: int = 2) -> set:
    compact = _compact_text(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def _cjk_overlap(a: str, b: str) -> float:
    ca, cb = _cjk_chunks(a), _cjk_chunks(b)
    if not ca or not cb:
        return 0.0
    return len(ca & cb) / max(1, len(ca))


def _ko_ordinals_in(text: str) -> List[str]:
    found: List[str] = []
    for word, digit in _KO_ORDINALS.items():
        if word in text:
            found.append(digit)
    return found


def _extract_claims(expected: str) -> List[str]:
    claims = []
    exp = expected.lower()
    for m in re.finditer(r"\d+(?:\.\d+)?%?", exp):
        claims.append(m.group())
    for m in re.finditer(r"\b\d+\b", exp):
        if m.group() not in claims:
            claims.append(m.group())
    for word in ("khong", "co", "tcfd", "google", "vinamilk", "downloaded", "manual", "없", "있"):
        if word in exp:
            claims.append(word)
    for part in re.split(r"[,;]", exp):
        p = part.strip()
        if len(p) >= 4 and not p.isdigit():
            claims.append(p[:40])
    return list(dict.fromkeys(claims))[:8]


def score_groundedness(row: Dict[str, str], result: Dict[str, Any]) -> Tuple[bool, dict, List[str]]:
    codes: List[str] = []
    if expects_insufficient(row):
        ok = not result.get("evidence") or result.get("insufficient")
        if not ok:
            codes.append(RC_GROUNDEDNESS_OVERLAP_LOW)
        return ok, {"rule": "insufficient_no_hallucination", "logic": "insufficient_should_not_cite_wrong_doc"}, codes

    answer = (result.get("answer") or "").lower()
    ev_text = " ".join((e.get("text") or "") for e in (result.get("evidence") or [])).lower()
    if not ev_text:
        codes.append(RC_GROUNDEDNESS_NO_EVIDENCE)
        return False, {"token_overlap": 0.0, "claim_hits": 0, "logic": "answer_claims_must_appear_in_evidence"}, codes

    ans_t = set(tokenize(answer))
    ev_t = set(tokenize(ev_text))
    overlap = len(ans_t & ev_t) / max(1, len(ans_t)) if ans_t else 0.0
    if overlap < 0.18:
        overlap = max(overlap, _cjk_overlap(answer, ev_text))
    claims = _extract_claims(row.get("expected_answer", ""))
    claim_hits = sum(1 for c in claims if c in ev_text or c in answer)
    claim_ok = claim_hits >= max(1, len(claims) // 2) if claims else overlap >= 0.12
    ok = overlap >= 0.18 or claim_ok
    if not ok:
        codes.append(RC_GROUNDEDNESS_OVERLAP_LOW)
    return ok, {
        "token_overlap": round(overlap, 3),
        "claim_hits": claim_hits,
        "logic": "token_overlap>=0.18_or_key_claim_in_evidence",
    }, codes


def score_answer(row: Dict[str, str], result: Dict[str, Any]) -> Tuple[bool, dict, List[str]]:
    codes: List[str] = []
    expected = (row.get("expected_answer") or "").lower()
    answer = (result.get("answer") or "").lower()

    if not expects_insufficient(row):
        if result.get("insufficient") or any(p in answer for p in INSUFFICIENT_PHRASES):
            codes.append(RC_INSUFFICIENT_UNEXPECTED)
            return False, {"rule": "unexpected_insufficient_answer"}, codes

    if expects_insufficient(row):
        ok = bool(result.get("insufficient")) and any(p in answer for p in INSUFFICIENT_PHRASES)
        if not ok:
            codes.append(RC_INSUFFICIENT_HANDLING_FAIL)
        return ok, {"rule": "insufficient_flag_and_phrase"}, codes

    field = (row.get("extracted_field") or "").strip().lower()
    if field and field in EXTRACTED_FIELD_ALIASES:
        aliases = EXTRACTED_FIELD_ALIASES[field]
        hit_aliases = [a for a in aliases if a in answer]
        if hit_aliases:
            return True, {"rule": "extracted_field_alias", "field": field, "hits": hit_aliases[:3]}, codes

    if expected in ("khong", "co", "없음", "있음"):
        ok = expected in answer or (expected == "co" and "co " in f"{answer} ")
        if not ok:
            codes.append(RC_ANSWER_BOOLEAN_MISMATCH)
        return ok, {"rule": "boolean"}, codes

    pcts = re.findall(r"\d+(?:\.\d+)?%", expected)
    nums = re.findall(r"\d+(?:\.\d+)?", expected)
    if pcts or nums:
        pct_ok = any(p.replace("%", "") in answer for p in pcts) if pcts else True
        num_ok = any(n in answer for n in nums) if nums else True
        if pcts and not pct_ok:
            codes.append(RC_ANSWER_NUMERIC_MISMATCH)
        elif nums and not num_ok:
            codes.append(RC_ANSWER_NUMERIC_MISMATCH)
        elif pct_ok or num_ok:
            return True, {"rule": "numeric_or_percent"}, codes
        if pcts or nums:
            codes.append(RC_ANSWER_NUMERIC_MISMATCH)
            return False, {"rule": "numeric_or_percent"}, codes

    exp_compact = _compact_text(expected)
    ans_compact = _compact_text(answer)
    if len(exp_compact) >= 4 and (exp_compact in ans_compact or ans_compact in exp_compact):
        return True, {"rule": "ko_substring"}, codes

    cjk = _cjk_overlap(expected, answer)
    if cjk >= 0.28:
        return True, {"rule": "cjk_bigram", "overlap": round(cjk, 3)}, codes

    ko_exp = _ko_ordinals_in(expected)
    ko_ans = _ko_ordinals_in(answer)
    if ko_exp and any(d in answer or d in ko_ans for d in ko_exp):
        return True, {"rule": "ko_ordinal", "digits": ko_exp[:3]}, codes

    phrases = [p.strip() for p in re.split(r"[,;]", expected) if len(p.strip()) >= 3]
    hits = sum(1 for p in phrases if p in answer)
    if phrases:
        if hits >= max(1, len(phrases) // 2):
            return True, {"rule": "phrase_match", "hits": hits}, codes
        codes.append(RC_ANSWER_PHRASE_MISMATCH)
        return False, {"rule": "phrase_match"}, codes

    tokens = [t for t in re.split(r"[%\s]+", expected) if len(t) >= 3]
    tok_hit = sum(1 for t in tokens if t in answer)
    ok = tok_hit >= max(1, len(tokens) // 2) if tokens else True
    if not ok and cjk >= 0.18:
        ok = True
    if not ok:
        codes.append(RC_ANSWER_TOKEN_MISMATCH)
    return ok, {"rule": "token_heuristic", "token_hits": tok_hit, "cjk": round(cjk, 3)}, codes


def score_insufficient(row: Dict[str, str], result: Dict[str, Any]) -> Tuple[bool, dict, List[str]]:
    codes: List[str] = []
    answer = (result.get("answer") or "").lower()
    if not expects_insufficient(row):
        if result.get("insufficient"):
            ok = any(p in answer for p in INSUFFICIENT_PHRASES)
            if not ok:
                codes.append(RC_INSUFFICIENT_UNEXPECTED)
            return ok, {"rule": "unexpected_insufficient"}, codes
        return True, {"rule": "not_required"}, codes
    ok = bool(result.get("insufficient")) and any(p in answer for p in INSUFFICIENT_PHRASES)
    if not ok:
        codes.append(RC_INSUFFICIENT_HANDLING_FAIL)
    return ok, {"rule": "required_insufficient"}, codes


def _dedupe_codes(codes: List[str]) -> List[str]:
    seen = set()
    out = []
    for c in codes:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _overall_label(
    row: Dict[str, str],
    retrieval_hit: bool,
    citation_top1: bool,
    grounded: bool,
    answer_ok: bool,
    insuf_ok: bool,
) -> str:
    if expects_insufficient(row):
        return "pass" if insuf_ok else "fail"
    parts = [retrieval_hit, citation_top1, grounded, answer_ok]
    if all(parts):
        return "pass"
    if retrieval_hit and (answer_ok or grounded):
        return "partial"
    if retrieval_hit or answer_ok:
        return "partial"
    return "fail"


def format_per_question_score(
    row: Dict[str, str],
    result: Dict[str, Any],
    metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Output chuan per-question."""
    m = metrics or score_result_v2(row, result)
    evidence = result.get("evidence") or []
    top_sources = [e.get("source", "") for e in evidence[:3]]
    return {
        "id": row["id"],
        "overall": m["overall"],
        "metrics": {
            "retrieval_hit": m["retrieval_hit"],
            "citation_correct": m["citation_correct"],
            "citation_topk_any": m.get("citation_topk_any", False),
            "groundedness": m["groundedness"],
            "answer_correct": m["answer_correct"],
            "insufficient_ok": m["insufficient_ok"],
        },
        "reason_codes": m.get("reason_codes", m.get("reasons", [])),
        "top_evidence_sources": top_sources,
    }


def score_result_v2(row: Dict[str, str], result: Dict[str, Any]) -> Dict[str, Any]:
    evidence = result.get("evidence") or []

    retrieval_hit, ret_detail, c1 = score_retrieval(row, evidence)
    citation_top1, cit_detail, c2 = score_citation(row, evidence)
    grounded, grd_detail, c3 = score_groundedness(row, result)
    answer_ok, ans_detail, c4 = score_answer(row, result)
    insuf_ok, ins_detail, c5 = score_insufficient(row, result)
    all_codes = _dedupe_codes(c1 + c2 + c3 + c4 + c5)

    overall = _overall_label(row, retrieval_hit, citation_top1, grounded, answer_ok, insuf_ok)

    return {
        "retrieval_hit": retrieval_hit,
        "citation_correct": citation_top1,
        "citation_topk_any": cit_detail.get("topk_any", False),
        "groundedness": grounded,
        "answer_correct": answer_ok,
        "insufficient_ok": insuf_ok,
        "overall": overall,
        "reason_codes": all_codes,
        "reasons": all_codes,  # backward compatible
        "details": {
            "retrieval": ret_detail,
            "citation": cit_detail,
            "groundedness": grd_detail,
            "answer": ans_detail,
            "insufficient": ins_detail,
        },
    }


def aggregate_metrics_v2(scored: List[Dict[str, Any]]) -> Dict[str, float]:
    n = max(1, len(scored))
    return {
        "retrieval_hit_rate": round(sum(1 for s in scored if s["retrieval_hit"]) / n, 4),
        "citation_correctness": round(sum(1 for s in scored if s["citation_correct"]) / n, 4),
        "citation_topk_rate": round(sum(1 for s in scored if s.get("citation_topk_any")) / n, 4),
        "groundedness": round(sum(1 for s in scored if s["groundedness"]) / n, 4),
        "answer_correctness": round(sum(1 for s in scored if s["answer_correct"]) / n, 4),
        "insufficient_information_handling": round(
            sum(1 for s in scored if s["insufficient_ok"]) / n, 4
        ),
        "pass_rate": round(sum(1 for s in scored if s["overall"] == "pass") / n, 4),
        "partial_rate": round(sum(1 for s in scored if s["overall"] == "partial") / n, 4),
        "fail_rate": round(sum(1 for s in scored if s["overall"] == "fail") / n, 4),
    }


def top_error_patterns(scored_items: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in scored_items:
        m = item.get("metrics") or item
        for r in m.get("reason_codes") or m.get("reasons") or []:
            counts[r] = counts.get(r, 0) + 1
    sorted_items = sorted(counts.items(), key=lambda x: -x[1])[:top_n]
    return dict(sorted_items)


def confusion_summary(evaluated: List[Dict[str, Any]]) -> Dict[str, int]:
    c = {"pass": 0, "partial": 0, "fail": 0}
    for e in evaluated:
        c[e["metrics"]["overall"]] = c.get(e["metrics"]["overall"], 0) + 1
    return c
