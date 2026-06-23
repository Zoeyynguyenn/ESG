"""Pilot selector R2.3 — dedupe fact clusters, block TOC/intro, rank for Distillation yield."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl
from golden_set.prefilter_corpus_units_r2_2 import (
    PREFILTER_VERSION,
    _duplicate_cluster_id,
    _is_toc_heavy,
    _text_fingerprint,
    detect_signals_r22,
)

SELECTOR_VERSION = "2.3.0"

# Hard block — TOC / ambiguous / insufficient (Distillation R2.2)
DISTILL_R22_HARD_BLOCK_IDS = {
    "rec_fcab1197e3c245b6",  # ambiguous TOC/about
    "rec_b1e5d2fd63103966",  # insufficient_substance
    "rec_adf521a49feec751",  # nav_or_menu intro
    "rec_102f3d47a149ed3d",  # ambiguous_grounding
    "rec_65c50bede5bb66da",  # nav TOC
    "rec_89c6e8dd36c4db22",  # ambiguous news
    "rec_ea632bae09735059",  # insufficient about-report
}

# Soft block — duplicate in batch; selector dedupe handles
DISTILL_R22_SOFT_DUP_IDS = {
    "rec_0f7c7247e048a21e",
    "rec_39fe9a810a0d6923",
}

DISTILL_R22_FAILED_IDS = DISTILL_R22_HARD_BLOCK_IDS  # backward compat alias

# Proven usable in Distillation R2.2 — priority boost
DISTILL_R22_USABLE_IDS = {
    "rec_3adad134db5cb9c2",
    "rec_6d11be8f9ba7006c",
    "rec_41a160ead0ae1be6",
    "rec_66100907c00656ec",
    "rec_acac077bde904698",
    "rec_5edea297fe4ab1d8",
}

# Near-duplicate of proven unit (same press body) — exclude
NEAR_DUP_OF_PROVEN = {
    "rec_6d11be8f9ba7006c",  # chrome duplicate of rec_3adad134 body
}

# KGCS / 2022 news body duplicate of rec_66100907
KGCS_SIBLING_DUP_IDS = {
    "rec_acac077bde904698",
}

FACT_TAG_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("fact_8_material_issues", re.compile(r"8개\s*중대", re.I)),
    ("fact_12_material_issues", re.compile(r"12개.*중대|총\s*12개", re.I)),
    ("fact_net_zero_2050", re.compile(r"탄소중립|Net\s*Zero|넷제로", re.I)),
    ("fact_kgcs_rating", re.compile(r"KGCS|ESG경영\s*평가.*등급", re.I)),
    ("fact_scope3_cdp", re.compile(r"Scope\s*3|CDP", re.I)),
    ("fact_double_materiality", re.compile(r"이중\s*중대성", re.I)),
    ("fact_esrs_issb", re.compile(r"ESRS|ISSB", re.I)),
    ("fact_iso45001", re.compile(r"ISO\s*45001", re.I)),
    ("fact_housing_social", re.compile(r"948호|1,000호", re.I)),
    ("fact_gov_compliance_pct", re.compile(r"7%p|준수율", re.I)),
    ("fact_board_esg_2021", re.compile(r"2021.*이사회|ESG\s*위원회", re.I)),
    ("fact_consecutive_publish", re.compile(r"\d+년\s*연속.*발간", re.I)),
    ("fact_sustinvest_aa", re.compile(r"SUSTINVEST|서스틴베스트", re.I)),
    ("fact_un_global_compact", re.compile(r"UNGC|글로벌컴팩트", re.I)),
]

TOC_INTRO_MARKERS = [
    "About this Report",
    "About this report",
    "보고서 개요",
    "TABLE OF CONTENTS",
    "Table of Contents",
    "목차",
    "CEO Message",
    "CEO message",
]


@dataclass
class SelectorScore:
    unit: Dict[str, Any]
    selector_rank: float
    pilot_blocked: bool
    selector_exclude_reason: str = ""
    grounding_risk: str = "low"  # low | medium | high
    fact_cluster_strength: int = 0
    fact_tags: List[str] = field(default_factory=list)
    pilot_source: str = ""


def _fact_tags(text: str) -> List[str]:
    tags = []
    for name, pat in FACT_TAG_PATTERNS:
        if pat.search(text):
            tags.append(name)
    return tags


def _is_about_report_intro(text: str, substance: int) -> bool:
    head = text[:2200]
    intro_hits = sum(1 for m in TOC_INTRO_MARKERS if m in head)
    if _is_toc_heavy(text):
        return True
    if intro_hits >= 2:
        return True
    if "보고서 개요" in head[:900] and intro_hits >= 1:
        return True
    if head.count("지속가능경영보고서") >= 4 and substance < 14:
        return True
    if re.search(r"여섯\s*번째|다섯\s*번째|세\s*번째.*보고서", head) and "목차" in head:
        return True
    return False


def _is_news_grounding_risk(text: str, noise: int, substance: int) -> bool:
    head = text[:500]
    if noise >= 15:
        return True
    if noise >= 7 and ("기자" in head or "발행일" in head):
        return True
    if "secondary_news_rewrite" in str(text) and noise >= 4 and substance < 18:
        return False  # taxonomy checked separately
    return False


def _grounding_risk_level(
    unit: Dict[str, Any],
    sig,
    *,
    is_toc: bool,
    is_news_risk: bool,
) -> str:
    rid = unit.get("record_id", "")
    if rid in DISTILL_R22_HARD_BLOCK_IDS:
        return "high"
    if rid in DISTILL_R22_SOFT_DUP_IDS:
        return "medium"
    if is_toc:
        return "high"
    if is_news_risk:
        return "medium"
    if unit.get("prefilter_decision") == "conditional":
        return "medium"
    if sig.noise_score >= 14:
        return "medium"
    if sig.noise_score >= 5:
        return "medium"
    return "low"


def score_unit_for_pilot(
    unit: Dict[str, Any],
    *,
    distill_failed: Optional[Set[str]] = None,
    distill_usable: Optional[Set[str]] = None,
) -> SelectorScore:
    text = unit.get("text") or ""
    sig = detect_signals_r22(unit)
    rid = unit.get("record_id", "")
    failed = distill_failed or DISTILL_R22_FAILED_IDS
    usable = distill_usable or DISTILL_R22_USABLE_IDS

    tags = _fact_tags(text)
    is_toc = _is_about_report_intro(text, sig.substance_score)
    is_news = _is_news_grounding_risk(text, sig.noise_score, sig.substance_score)
    tax = set(unit.get("unit_taxonomy") or [])
    if "nav_or_menu_noise" in tax and is_toc:
        is_toc = True

    blocked = False
    exclude = ""

    if rid in DISTILL_R22_HARD_BLOCK_IDS or rid in (failed or set()):
        blocked = True
        exclude = "distill_r22_hard_block"
    elif rid in DISTILL_R22_SOFT_DUP_IDS:
        blocked = True
        exclude = "distill_r22_soft_dup"
    elif rid in NEAR_DUP_OF_PROVEN or rid in KGCS_SIBLING_DUP_IDS:
        blocked = True
        exclude = "near_dup_proven_body"
    elif is_toc:
        blocked = True
        exclude = "toc_intro_about_report"
    elif sig.substance_score < 10:
        blocked = True
        exclude = "insufficient_substance_score"
    elif sig.noise_score >= 9:
        blocked = True
        exclude = "noise_too_high"

    risk = _grounding_risk_level(unit, sig, is_toc=is_toc, is_news_risk=is_news)

    rank = sig.substance_score * 10.0 - sig.noise_score * 6.0
    if unit.get("prefilter_decision") == "keep":
        rank += 25
    elif unit.get("prefilter_decision") == "conditional":
        rank += 8
    if rid in usable:
        rank += 120
    if risk == "high":
        rank -= 80
    elif risk == "medium":
        rank -= 25
    if is_news and rid not in usable:
        rank -= 30

    cluster_strength = len(tags) + min(sig.substance_score // 4, 4)

    return SelectorScore(
        unit=unit,
        selector_rank=round(rank, 2),
        pilot_blocked=blocked,
        selector_exclude_reason=exclude,
        grounding_risk=risk,
        fact_cluster_strength=cluster_strength,
        fact_tags=tags,
    )


def _enrich_pilot_row(scored: SelectorScore, *, pilot_source: str, notes: str) -> Dict[str, Any]:
    u = scored.unit
    row = dict(u)
    row["selector_version"] = SELECTOR_VERSION
    row["selector_rank"] = scored.selector_rank
    row["pilot_blocked"] = scored.pilot_blocked
    row["selector_exclude_reason"] = scored.selector_exclude_reason
    row["grounding_risk"] = scored.grounding_risk
    row["fact_cluster_strength"] = scored.fact_cluster_strength
    row["fact_tags"] = scored.fact_tags
    row["pilot_source"] = pilot_source
    row["pilot_candidate_notes"] = notes
    row["pilot_candidate"] = True
    return row


def _eligible_for_pilot_pool(scored: SelectorScore) -> bool:
    rid = scored.unit.get("record_id", "")
    if rid in DISTILL_R22_HARD_BLOCK_IDS or rid in NEAR_DUP_OF_PROVEN or rid in KGCS_SIBLING_DUP_IDS:
        return False
    if rid in DISTILL_R22_SOFT_DUP_IDS:
        return False
    if scored.selector_exclude_reason == "toc_intro_about_report":
        return False
    sig = detect_signals_r22(scored.unit)
    if sig.substance_score < 8 or sig.noise_score > 18:
        return False
    return True


def _best_per_fingerprint(scored_all: List[SelectorScore]) -> List[SelectorScore]:
    by_fp: Dict[str, List[SelectorScore]] = defaultdict(list)
    for s in scored_all:
        if not _eligible_for_pilot_pool(s):
            continue
        fp = _text_fingerprint(s.unit)
        by_fp[fp].append(s)
    winners: List[SelectorScore] = []
    for group in by_fp.values():
        winners.append(max(group, key=lambda x: x.selector_rank))
    winners.sort(key=lambda x: -x.selector_rank)
    return winners


def select_pilot_hanssem_r23(
    pool: List[Dict[str, Any]],
    *,
    n: int = 15,
    distill_failed: Optional[Set[str]] = None,
    distill_usable: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[SelectorScore]]:
    hanssem = [u for u in pool if u.get("company") == "한샘"]
    scored_all = [
        score_unit_for_pilot(u, distill_failed=distill_failed, distill_usable=distill_usable)
        for u in hanssem
    ]

    fp_winners = _best_per_fingerprint(scored_all)
    proven_ids = (distill_usable or DISTILL_R22_USABLE_IDS) - NEAR_DUP_OF_PROVEN - KGCS_SIBLING_DUP_IDS

    chosen: List[Dict[str, Any]] = []
    claimed_tags: Set[str] = set()
    selection_log: List[SelectorScore] = []

    def append_scored(scored: SelectorScore, *, pilot_source: str = "") -> None:
        u = scored.unit
        src = pilot_source or (
            "proven_usable_r2_2"
            if u.get("record_id") in proven_ids
            else "eligible_keep_r2_2"
            if u.get("prefilter_decision") == "keep"
            else "conditional_r2_2"
            if u.get("prefilter_decision") == "conditional"
            else "corpus_fill_r2_3"
        )
        notes = f"rank={scored.selector_rank}, tags={scored.fact_tags}, risk={scored.grounding_risk}"
        chosen.append(_enrich_pilot_row(scored, pilot_source=src, notes=notes))
        selection_log.append(scored)

    def try_add(scored: SelectorScore, *, allow_shared_tags: bool = False) -> bool:
        if scored in selection_log:
            return False
        novel = [t for t in scored.fact_tags if t not in claimed_tags]
        if scored.fact_tags and not novel and not allow_shared_tags:
            return False
        for t in novel:
            claimed_tags.add(t)
        append_scored(scored)
        return True

    # Phase 1: proven usable with novel fact tags
    for s in fp_winners:
        if len(chosen) >= n:
            break
        if s.unit.get("record_id") not in proven_ids:
            continue
        try_add(s)

    # Phase 2: diversify fact tags (unique fingerprint already)
    for s in fp_winners:
        if len(chosen) >= n:
            break
        try_add(s)

    # Phase 3: fill remaining slots (allow shared tags)
    for s in fp_winners:
        if len(chosen) >= n:
            break
        try_add(s, allow_shared_tags=True)

    return chosen[:n], selection_log


def _enrich_from_corpus(unit: Dict[str, Any]) -> Dict[str, Any]:
    """Attach substance/noise when unit comes from raw corpus pool."""
    if unit.get("substance_score") is not None:
        return unit
    sig = detect_signals_r22(unit)
    row = dict(unit)
    row["substance_score"] = sig.substance_score
    row["noise_score"] = sig.noise_score
    row["duplicate_cluster_id"] = _duplicate_cluster_id(unit)
    return row


def build_pool(
    *,
    eligible_path: Path,
    conditional_path: Path,
    corpus_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for path in (eligible_path, conditional_path):
        if not path.exists():
            continue
        for u in read_jsonl(path):
            rid = u.get("record_id", "")
            if rid and rid not in seen:
                seen.add(rid)
                pool.append(u)
    if corpus_path and corpus_path.exists():
        for u in read_jsonl(corpus_path):
            if u.get("company") != "한샘":
                continue
            rid = u.get("record_id", "")
            if rid and rid not in seen:
                seen.add(rid)
                pool.append(_enrich_from_corpus(u))
    return pool


def run_selector_r23(
    *,
    eligible_path: Path,
    conditional_path: Path,
    corpus_path: Path,
    output_path: Path,
    old_pilot_path: Path,
    distill_summary_path: Optional[Path] = None,
    n: int = 15,
) -> Dict[str, Any]:
    pool = build_pool(
        eligible_path=eligible_path,
        conditional_path=conditional_path,
        corpus_path=corpus_path,
    )

    failed = set(DISTILL_R22_HARD_BLOCK_IDS)
    usable = set(DISTILL_R22_USABLE_IDS)
    if distill_summary_path and distill_summary_path.exists():
        ds = json.loads(distill_summary_path.read_text(encoding="utf-8"))
        for c in ds.get("silver_qc_candidates", []):
            usable.add(c.get("record_id", ""))

    pilot_rows, _ = select_pilot_hanssem_r23(
        pool, n=n, distill_failed=failed, distill_usable=usable
    )
    write_jsonl(output_path, pilot_rows)

    old_ids: List[str] = []
    if old_pilot_path.exists():
        old_ids = [u.get("record_id", "") for u in read_jsonl(old_pilot_path)]

    new_ids = [u.get("record_id", "") for u in pilot_rows]
    removed = sorted(set(old_ids) - set(new_ids))
    added = sorted(set(new_ids) - set(old_ids))
    overlap = sorted(set(old_ids) & set(new_ids))

    scored_pool = [score_unit_for_pilot(u) for u in pool if u.get("company") == "한샘"]
    blocked_counts = Counter(s.selector_exclude_reason for s in scored_pool if s.pilot_blocked)

    low_risk = sum(1 for u in pilot_rows if u.get("grounding_risk") == "low")
    med_risk = sum(1 for u in pilot_rows if u.get("grounding_risk") == "medium")
    high_risk = sum(1 for u in pilot_rows if u.get("grounding_risk") == "high")
    proven_in_pilot = sum(1 for u in pilot_rows if u.get("record_id") in usable)
    failed_in_pilot = sum(
        1 for u in pilot_rows if u.get("record_id") in (failed or DISTILL_R22_FAILED_IDS)
    )

    # Heuristic: proven anchors ~1 each; low ~0.8; medium ~0.45; high-noise tail ~0.25
    est_usable = int(
        proven_in_pilot * 0.95
        + low_risk * 0.8
        + med_risk * 0.45
    )

    summary = {
        "selector_version": SELECTOR_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pool_hanssem_count": len([u for u in pool if u.get("company") == "한샘"]),
        "pilot_selected": len(pilot_rows),
        "old_pilot_record_ids": old_ids,
        "new_pilot_record_ids": new_ids,
        "overlap_count": len(overlap),
        "overlap_ids": overlap,
        "removed_from_r22": removed,
        "added_in_r23": added,
        "replacement_count": len(removed),
        "blocked_reason_counts": dict(blocked_counts),
        "pilot_risk_breakdown": {"low": low_risk, "medium": med_risk, "high": high_risk},
        "distill_failed_in_pilot": failed_in_pilot,
        "proven_usable_in_pilot": proven_in_pilot,
        "forecast_usable_min": max(proven_in_pilot, est_usable - 2),
        "forecast_usable_max": min(n, est_usable + 2),
        "forecast_pass_8_usable": est_usable >= 8,
        "output_path": str(output_path),
        "pilot_selection": [
            {
                "record_id": u.get("record_id"),
                "prefilter_decision": u.get("prefilter_decision"),
                "pilot_source": u.get("pilot_source"),
                "selector_rank": u.get("selector_rank"),
                "grounding_risk": u.get("grounding_risk"),
                "fact_tags": u.get("fact_tags"),
                "fact_cluster_strength": u.get("fact_cluster_strength"),
                "substance_score": u.get("substance_score"),
                "noise_score": u.get("noise_score"),
            }
            for u in pilot_rows
        ],
    }
    return summary


def write_report_r23(summary: Dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Golden Set — Pilot Selector Round 2.3",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu selector R2.3",
        "",
        "Tái chọn pilot Hansem 15 unit sau Distillation R2.2 (6/15 usable): loại duplicate fact, TOC/intro, unit grounding yếu; tăng xác suất đạt **≥8 keep usable**.",
        "",
        "## Vì sao R2.2 chưa đạt gate",
        "",
        "- Distillation R2.2: **keep 6 / usable 6** — thiếu 2 so với ngưỡng 8.",
        "- **2** drop `duplicate_same_fact` — pilot chứa unit trùng cluster 8 issues / KGCS.",
        "- **5** drop TOC/intro/ambiguous — `rec_fcab1197`, `rec_adf521a49`, `rec_65c50bed`, `rec_102f3d47`, `rec_89c6e8dd`.",
        "- Prompt Distillation + validation **không** phải bottleneck.",
        "",
        "## Pattern bị loại ở level selector",
        "",
        "| Pattern | Hành vi R2.3 |",
        "|---------|--------------|",
        "| `distill_r22_hard_block` | Hard block 7 unit TOC/ambiguous/insufficient |",
        "| `distill_r22_soft_dup` | Block duplicate-span unit; thay bằng anchor proven |",
        "| `toc_intro_about_report` | Block TOC, About this Report, 보고서 개요 |",
        "| `near_dup_proven_body` | Block `rec_6d11be8f` (dup `rec_3adad134`) |",
        "| Fact tag dedupe | Chỉ 1 unit / fact tag trước khi fill |",
        "| `grounding_risk=high` | Không chọn trừ last-resort |",
        "",
        "### Block counts (pool Hanssem)",
        "",
    ]
    for k, v in sorted(summary.get("blocked_reason_counts", {}).items()):
        lines.append(f"- `{k}`: {v}")

    lines.extend(
        [
            "",
            "## Logic ranking / dedupe / replacement",
            "",
            "- `selector_rank = substance*10 - noise*6 + keep_bonus + proven_boost(+120) - risk_penalty`",
            "- `fact_tags`: 8 issues, 12 issues, Net Zero, KGCS, Scope3/CDP, ESRS, …",
            "- Dedupe: text fingerprint + claimed fact tags",
            "- Ưu tiên 5 proven usable (trừ near-dup), sau đó diversity tag, cuối cùng fill low-risk",
            "",
            "## So sánh pilot R2.2 vs R2.3",
            "",
            f"| Metric | R2.2 | R2.3 |",
            f"|--------|-----:|-----:|",
            f"| Pilot size | 15 | {summary.get('pilot_selected', 0)} |",
            f"| Overlap | — | {summary.get('overlap_count', 0)} |",
            f"| Replacements | — | {summary.get('replacement_count', 0)} |",
            f"| Proven usable retained | — | {summary.get('proven_usable_in_pilot', 0)} |",
            f"| grounding_risk low | — | {summary.get('pilot_risk_breakdown', {}).get('low', 0)} |",
            f"| grounding_risk medium | — | {summary.get('pilot_risk_breakdown', {}).get('medium', 0)} |",
            "",
            "### Unit bị thay ra",
            "",
        ]
    )
    for rid in summary.get("removed_from_r22", []):
        lines.append(f"- `{rid}`")

    lines.extend(["", "### Unit mới đưa vào", ""])
    for rid in summary.get("added_in_r23", []):
        lines.append(f"- `{rid}`")

    lines.extend(["", "### Pilot R2.3 (ranked)", ""])
    for item in summary.get("pilot_selection", []):
        lines.append(
            f"- `{item['record_id']}` rank={item['selector_rank']} risk={item['grounding_risk']} "
            f"tags={item.get('fact_tags', [])} sub={item.get('substance_score')} noise={item.get('noise_score')}"
        )

    fc_min = summary.get("forecast_usable_min", 0)
    fc_max = summary.get("forecast_usable_max", 0)
    lines.extend(
        [
            "",
            "## Dự báo xác suất đạt ≥8 usable",
            "",
            f"- Proven usable trong pilot: **{summary.get('proven_usable_in_pilot', 0)}**",
            f"- Heuristic forecast: **{fc_min}–{fc_max}** usable (không chạy Distillation trong task này)",
            f"- Pass threshold ≥8: **{'có khả năng' if summary.get('forecast_pass_8_usable') else 'cần validate bằng Distillation pilot R2.3'}**",
            "",
            "## Kết luận và bước kế tiếp",
            "",
            "1. Chạy Distillation pilot trên `pilot_hanssem_15_eligible_r2_3.jsonl` (prompt R2.1 unchanged).",
            "2. Nếu ≥8 usable → mở Silver QC pilot.",
            "3. Nếu vẫn thiếu: mở rộng corpus Hansem hoặc prefilter promote thêm unit report-body.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot selector R2.3 for Hansem")
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
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible_r2_3.jsonl",
    )
    parser.add_argument(
        "--old-pilot",
        default="data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible_r2_2.jsonl",
    )
    parser.add_argument(
        "--distill-summary",
        default="reports/_distill_pilot_hanssem_round2_2_summary.json",
    )
    parser.add_argument("--report", default="reports/golden_set_selector_round2_3.md")
    parser.add_argument("--summary-json", default="reports/_selector_r2_3_summary.json")
    args = parser.parse_args(argv)

    summary = run_selector_r23(
        eligible_path=root / args.eligible,
        conditional_path=root / args.conditional,
        corpus_path=root / args.corpus,
        output_path=root / args.output,
        old_pilot_path=root / args.old_pilot,
        distill_summary_path=root / args.distill_summary,
    )
    write_report_r23(summary, root / args.report)
    (root / args.summary_json).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(
        {
            "pilot_selected": summary["pilot_selected"],
            "replacements": summary["replacement_count"],
            "overlap": summary["overlap_count"],
            "proven_in_pilot": summary["proven_usable_in_pilot"],
            "forecast_pass_8": summary["forecast_pass_8_usable"],
        },
        ensure_ascii=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
