"""Pilot selector R2.4 Compact — small high-precision Hansem pilot (8–10 target, no tail fill)."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl
from golden_set.prefilter_corpus_units_r2_2 import (
    _duplicate_cluster_id,
    _text_fingerprint,
    detect_signals_r22,
)
from golden_set.pilot_selector_r2_3 import (
    DISTILL_R22_HARD_BLOCK_IDS,
    DISTILL_R22_SOFT_DUP_IDS,
    KGCS_SIBLING_DUP_IDS,
    NEAR_DUP_OF_PROVEN,
    _fact_tags,
    _is_about_report_intro,
    build_pool,
)

SELECTOR_VERSION = "2.4.0-compact"

# Proven usable from Distillation pilot R2.3 (validated keep + audit pass)
DISTILL_R23_USABLE_IDS = {
    "rec_3adad134db5cb9c2",
    "rec_41a160ead0ae1be6",
    "rec_5edea297fe4ab1d8",
    "rec_2d0cf95b00a0fefc",
    "rec_ba9d092227fde816",
    "rec_147089a328626757",
}

# Fact diversity labels for reporting (not used to block)
FACT_CATEGORY_MAP = {
    "fact_esrs_issb": "strategy",
    "fact_net_zero_2050": "strategy",
    "fact_double_materiality": "materiality",
    "fact_12_material_issues": "materiality",
    "fact_8_material_issues": "materiality",
    "fact_kgcs_rating": "rating_recognition",
    "fact_sustinvest_aa": "rating_recognition",
    "fact_board_esg_2021": "governance",
    "fact_consecutive_publish": "report_publication",
    "fact_scope3_cdp": "metric",
    "fact_gov_compliance_pct": "governance",
    "fact_housing_social": "governance",
    "fact_iso45001": "governance",
    "fact_un_global_compact": "governance",
}


def _fact_categories(tags: List[str]) -> List[str]:
    cats = []
    for t in tags:
        c = FACT_CATEGORY_MAP.get(t)
        if c and c not in cats:
            cats.append(c)
    return cats


def _is_tail_filler(unit: Dict[str, Any], *, from_corpus_only: bool) -> bool:
    """Tail = low substance corpus-fill units not in eligible/conditional."""
    if not from_corpus_only:
        return False
    sig = detect_signals_r22(unit)
    return sig.substance_score < 14 or sig.noise_score > 6


def _compact_eligible(
    unit: Dict[str, Any],
    *,
    claimed_fps: Set[str],
    claimed_clusters: Set[str],
    claimed_categories: Set[str],
) -> Tuple[bool, str]:
    rid = unit.get("record_id", "")
    if rid in DISTILL_R22_HARD_BLOCK_IDS:
        return False, "hard_block_distill_fail"
    if rid in DISTILL_R22_SOFT_DUP_IDS or rid in NEAR_DUP_OF_PROVEN or rid in KGCS_SIBLING_DUP_IDS:
        return False, "near_dup_or_soft_block"
    if rid in DISTILL_R23_USABLE_IDS:
        return True, "proven_usable_r2_3"

    text = unit.get("text") or ""
    sig = detect_signals_r22(unit)
    if _is_about_report_intro(text, sig.substance_score):
        return False, "toc_intro"
    if sig.substance_score < 14:
        return False, "substance_too_low"
    if sig.noise_score > 6:
        return False, "noise_too_high"

    fp = _text_fingerprint(unit)
    cl = unit.get("duplicate_cluster_id") or _duplicate_cluster_id(unit)
    if fp in claimed_fps:
        return False, "duplicate_fingerprint"
    if cl in claimed_clusters:
        return False, "duplicate_cluster_id"

    cats = _fact_categories(_fact_tags(text))
    if cats and all(c in claimed_categories for c in cats):
        return False, "fact_category_saturated"

    pf = unit.get("prefilter_decision")
    if pf not in ("keep", "conditional"):
        return False, "not_eligible_prefilter"

    return True, "unique_body_eligible"


def select_pilot_hanssem_compact(
    pool: List[Dict[str, Any]],
    *,
    target_min: int = 8,
    target_max: int = 10,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    hanssem = [u for u in pool if u.get("company") == "한샘"]
    by_id = {u.get("record_id"): u for u in hanssem}

    chosen: List[Dict[str, Any]] = []
    selection_log: List[Dict[str, Any]] = []
    claimed_fps: Set[str] = set()
    claimed_clusters: Set[str] = set()
    claimed_categories: Set[str] = set()

    def claim_unit(unit: Dict[str, Any], *, pilot_source: str, select_reason: str) -> None:
        fp = _text_fingerprint(unit)
        cl = unit.get("duplicate_cluster_id") or _duplicate_cluster_id(unit)
        tags = _fact_tags(unit.get("text") or "")
        cats = _fact_categories(tags)
        claimed_fps.add(fp)
        claimed_clusters.add(cl)
        for c in cats:
            claimed_categories.add(c)

        sig = detect_signals_r22(unit)
        row = dict(unit)
        row.update(
            {
                "selector_version": SELECTOR_VERSION,
                "pilot_source": pilot_source,
                "select_reason": select_reason,
                "fact_tags": tags,
                "fact_categories": cats,
                "compact_rank": len(chosen) + 1,
                "grounding_risk": "low" if sig.noise_score <= 4 else "medium",
                "substance_score": sig.substance_score,
                "noise_score": sig.noise_score,
                "duplicate_cluster_id": cl,
                "pilot_candidate": True,
                "pilot_blocked": False,
            }
        )
        chosen.append(row)
        selection_log.append(
            {
                "record_id": unit.get("record_id"),
                "pilot_source": pilot_source,
                "select_reason": select_reason,
                "fact_tags": tags,
                "fact_categories": cats,
                "substance_score": sig.substance_score,
                "noise_score": sig.noise_score,
            }
        )

    # Phase 1 — proven R2.3 usable anchors (fixed order by fact diversity)
    anchor_order = [
        "rec_3adad134db5cb9c2",  # strategy ESRS
        "rec_41a160ead0ae1be6",  # strategy Net Zero
        "rec_5edea297fe4ab1d8",  # report TCFD
        "rec_2d0cf95b00a0fefc",  # materiality 12 issues
        "rec_ba9d092227fde816",  # rating KGCS
        "rec_147089a328626757",  # narrative 2022
    ]
    for rid in anchor_order:
        u = by_id.get(rid)
        if u:
            claim_unit(u, pilot_source="proven_usable_r2_3", select_reason="distill_r23_validated_keep")

    # Phase 2 — expand from eligible pool only (no corpus tail fill)
    eligible_units = [
        u
        for u in hanssem
        if u.get("prefilter_decision") in ("keep", "conditional")
        and u.get("record_id") not in DISTILL_R23_USABLE_IDS
    ]
    scored: List[Tuple[float, Dict[str, Any], str]] = []
    for u in eligible_units:
        ok, reason = _compact_eligible(
            u,
            claimed_fps=claimed_fps,
            claimed_clusters=claimed_clusters,
            claimed_categories=claimed_categories,
        )
        if not ok:
            continue
        sig = detect_signals_r22(u)
        score = sig.substance_score * 10.0 - sig.noise_score * 6.0
        if u.get("prefilter_decision") == "keep":
            score += 20
        scored.append((score, u, reason))

    scored.sort(key=lambda x: -x[0])
    for _, u, reason in scored:
        if len(chosen) >= target_max:
            break
        claim_unit(
            u,
            pilot_source="unique_body_eligible",
            select_reason=reason,
        )

    meta = {
        "target_min": target_min,
        "target_max": target_max,
        "achieved_size": len(chosen),
        "anchor_count": sum(1 for x in selection_log if x["pilot_source"] == "proven_usable_r2_3"),
        "expansion_count": sum(1 for x in selection_log if x["pilot_source"] == "unique_body_eligible"),
        "tail_filler_count": 0,
        "unique_fingerprint_count": len(claimed_fps),
        "unique_cluster_count": len(claimed_clusters),
        "fact_categories_covered": sorted(claimed_categories),
        "selection_log": selection_log,
        "pool_analysis": _analyze_pool(hanssem),
    }
    return chosen, meta


def _analyze_pool(hanssem: List[Dict[str, Any]]) -> Dict[str, Any]:
    fps: Set[str] = set()
    clusters: Counter = Counter()
    anchors = 0
    tail = 0
    for u in hanssem:
        fps.add(_text_fingerprint(u))
        clusters[_duplicate_cluster_id(u)] += 1
        if u.get("record_id") in DISTILL_R23_USABLE_IDS:
            anchors += 1
        elif u.get("prefilter_decision") not in ("keep", "conditional"):
            tail += 1
    saturated = [k for k, v in clusters.items() if v > 1]
    return {
        "hanssem_pool_size": len(hanssem),
        "unique_body_fingerprints": len(fps),
        "proven_anchor_count": anchors,
        "tail_corpus_only_estimate": tail,
        "duplicate_clusters": len(saturated),
        "saturated_cluster_ids": saturated[:12],
    }


def run_selector_r24_compact(
    *,
    eligible_path: Path,
    conditional_path: Path,
    corpus_path: Path,
    output_path: Path,
    distill_r23_summary_path: Path,
    target_min: int = 8,
    target_max: int = 10,
) -> Dict[str, Any]:
    pool = build_pool(
        eligible_path=eligible_path,
        conditional_path=conditional_path,
        corpus_path=corpus_path,
    )

    # Refresh proven set from R2.3 summary if available
    global DISTILL_R23_USABLE_IDS
    if distill_r23_summary_path.exists():
        ds = json.loads(distill_r23_summary_path.read_text(encoding="utf-8"))
        ids = {c.get("record_id") for c in ds.get("silver_qc_candidates", []) if c.get("record_id")}
        if ids:
            DISTILL_R23_USABLE_IDS = ids

    pilot_rows, meta = select_pilot_hanssem_compact(pool, target_min=target_min, target_max=target_max)
    write_jsonl(output_path, pilot_rows)

    r23_path = output_path.parent / "pilot_hanssem_15_eligible_r2_3.jsonl"
    r23_ids: List[str] = []
    if r23_path.exists():
        r23_ids = [u.get("record_id", "") for u in read_jsonl(r23_path)]

    new_ids = [u.get("record_id", "") for u in pilot_rows]
    summary = {
        "selector_version": SELECTOR_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "strategy": "compact_no_tail_fill",
        "target_size_min": target_min,
        "target_size_max": target_max,
        "pilot_selected": len(pilot_rows),
        "pilot_record_ids": new_ids,
        "vs_r23_15": {
            "r23_size": len(r23_ids),
            "overlap_ids": sorted(set(r23_ids) & set(new_ids)),
            "overlap_count": len(set(r23_ids) & set(new_ids)),
            "removed_from_r23": sorted(set(r23_ids) - set(new_ids)),
            "removed_count": len(set(r23_ids) - set(new_ids)),
        },
        "output_path": str(output_path),
        **meta,
    }
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot selector R2.4 Compact for Hansem")
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--eligible",
        default="data/golden_set/v2/step1_corpus_units/corpus_units_eligible_r2_2.jsonl",
    )
    parser.add_argument(
        "--conditional",
        default="data/golden_set/v2/step1_corpus_units/corpus_units_conditional_r2_2.jsonl",
    )
    parser.add_argument(
        "--corpus",
        default="data/golden_set/v2/step1_corpus_units/corpus_units.jsonl",
    )
    parser.add_argument(
        "--output",
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_10_compact_r2_4.jsonl",
    )
    parser.add_argument(
        "--distill-r23-summary",
        default="reports/_distill_pilot_hanssem_round2_3_summary.json",
    )
    parser.add_argument("--target-min", type=int, default=8)
    parser.add_argument("--target-max", type=int, default=10)
    parser.add_argument("--summary-json", default="reports/_pilot_compact_r2_4_summary.json")
    args = parser.parse_args(argv)

    summary = run_selector_r24_compact(
        eligible_path=root / args.eligible,
        conditional_path=root / args.conditional,
        corpus_path=root / args.corpus,
        output_path=root / args.output,
        distill_r23_summary_path=root / args.distill_r23_summary,
        target_min=args.target_min,
        target_max=args.target_max,
    )
    (root / args.summary_json).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(
        {
            "pilot_selected": summary["pilot_selected"],
            "anchors": summary["anchor_count"],
            "expansion": summary["expansion_count"],
            "target_met": summary["pilot_selected"] >= args.target_min,
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
