"""Build Local MiniLM vs OpenAI comparison table (MD + CSV)."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pick(rows: list[dict], config_id: str) -> dict[str, str]:
    for r in rows:
        if r.get("config_id") == config_id:
            return r
    return {}


def _f(row: dict, key: str, default: str = "") -> str:
    v = row.get(key, default)
    return str(v) if v not in (None, "") else default


def _flt(row: dict, key: str) -> float:
    try:
        return float(row.get(key) or 0)
    except ValueError:
        return 0.0


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    local = _read(base / "reports" / "benchmark_exportjson_phase1_results.csv")
    openai_val = _read(base / "reports" / "benchmark_exportjson_openai_validation_results.csv")
    openai_p3 = _read(base / "reports" / "benchmark_exportjson_openai_phase3_results.csv")
    openai_smoke = _read(base / "reports" / "benchmark_exportjson_openai_smoke_results.csv")

    pairs = [
        ("recursive_800_120", "semantic_dense", "p1_rec800_minilm_dense_chroma", "val_openai_rec800_dense_chroma"),
        ("recursive_800_120", "hybrid_dense_bm25", "p1_rec800_minilm_hybrid_chroma", "val_openai_rec800_hybrid_chroma"),
        ("section_based", "semantic_dense", "p1_section_minilm_dense_chroma", "val_openai_section_dense_chroma"),
        ("section_based", "hybrid_dense_bm25", "p1_section_minilm_hybrid_chroma", "val_openai_section_hybrid_chroma"),
    ]

    out_rows: list[dict[str, str]] = []
    for chunk, retr, lid, oid in pairs:
        loc = _pick(local, lid)
        oai = _pick(openai_val, oid)
        lq, oq = _flt(loc, "query_time_avg"), _flt(oai, "query_time_avg")
        ratio = f"{oq / lq:.1f}x" if lq > 0 else "—"
        out_rows.append(
            {
                "chunking": chunk,
                "retrieval": retr,
                "local_config": lid,
                "openai_config": oid,
                "local_lane": _f(loc, "dataset_lane", "company_export_json_dev"),
                "openai_lane": _f(oai, "dataset_lane", "company_export_json_validation"),
                "local_pool": _f(loc, "candidate_pool"),
                "openai_pool": _f(oai, "candidate_pool"),
                "local_hit": _f(loc, "retrieval_hit_rate"),
                "openai_hit": _f(oai, "retrieval_hit_rate"),
                "local_citation": _f(loc, "citation_correctness"),
                "openai_citation": _f(oai, "citation_correctness"),
                "local_composite": _f(loc, "composite_score"),
                "openai_composite": _f(oai, "composite_score"),
                "local_query_s": _f(loc, "query_time_avg"),
                "openai_query_s": _f(oai, "query_time_avg"),
                "query_ratio_openai_vs_local": ratio,
                "local_index_build_s": _f(loc, "index_build_time"),
                "openai_index_build_s": _f(oai, "index_build_time"),
                "local_latency_s": _f(loc, "latency"),
                "openai_latency_s": _f(oai, "latency"),
            }
        )

    # Production OpenAI row (Phase 3 winner)
    p3_winner = _pick(openai_p3, "p3_openai_section_hybrid_qdrant")
    loc_ref = _pick(local, "p1_section_minilm_hybrid_chroma")
    if p3_winner:
        out_rows.append(
            {
                "chunking": "section_based",
                "retrieval": "hybrid_dense_bm25",
                "local_config": "p1_section_minilm_hybrid_chroma",
                "openai_config": "p3_openai_section_hybrid_qdrant (production)",
                "local_lane": _f(loc_ref, "dataset_lane"),
                "openai_lane": _f(p3_winner, "dataset_lane"),
                "local_pool": _f(loc_ref, "candidate_pool"),
                "openai_pool": _f(p3_winner, "candidate_pool"),
                "local_hit": _f(loc_ref, "retrieval_hit_rate"),
                "openai_hit": _f(p3_winner, "retrieval_hit_rate"),
                "local_citation": _f(loc_ref, "citation_correctness"),
                "openai_citation": _f(p3_winner, "citation_correctness"),
                "local_composite": _f(loc_ref, "composite_score"),
                "openai_composite": _f(p3_winner, "composite_score"),
                "local_query_s": _f(loc_ref, "query_time_avg"),
                "openai_query_s": _f(p3_winner, "query_time_avg"),
                "query_ratio_openai_vs_local": (
                    f"{_flt(p3_winner, 'query_time_avg') / _flt(loc_ref, 'query_time_avg'):.1f}x"
                    if _flt(loc_ref, "query_time_avg") > 0
                    else "—"
                ),
                "local_index_build_s": _f(loc_ref, "index_build_time"),
                "openai_index_build_s": _f(p3_winner, "index_build_time"),
                "local_latency_s": _f(loc_ref, "latency"),
                "openai_latency_s": _f(p3_winner, "latency"),
            }
        )

    csv_path = base / "reports" / "benchmark_local_vs_openai_comparison.csv"
    md_path = base / "reports" / "benchmark_local_vs_openai_comparison.md"
    fields = list(out_rows[0].keys()) if out_rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    md_lines = [
        "# So sánh Local (MiniLM) vs OpenAI",
        "",
        f"Tạo lúc: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Lưu ý khi đọc",
        "",
        "| Khía cạnh | Local | OpenAI |",
        "|---|---|---|",
        "| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (local CPU) | `openai:text-embedding-3-small` (API) |",
        "| Lane corpus | `company_export_json_dev` → `splits/dev.jsonl` | `company_export_json_validation` → `splits/validation.jsonl` |",
        "| Eval | Cùng file `.rag/.../eval_set_company_export_json_dev_ko.md` (20 câu trên validation; dev thường ít hơn tùy `eval_questions`) |",
        "| Pool | 24 (Pha 1) | 64 (validation / Phase 3) |",
        "| Vector store | Chroma | Chroma (validation) / Qdrant (Phase 3 winner) |",
        "",
        "**Tốc độ:** `query_s` = giây trung bình mỗi câu; `index_build_s` = thời gian build index; `latency_s` = tổng thời gian chạy eval case.",
        "",
        "## Bảng chính (cùng chunking + retrieval)",
        "",
        "| Chunking | Retrieval | Hit L | Hit O | Cit L | Cit O | Composite L | Composite O | Query L (s) | Query O (s) | O/L query | Index L (s) | Index O (s) | Latency L (s) | Latency O (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in out_rows:
        md_lines.append(
            f"| {r['chunking']} | {r['retrieval']} "
            f"| {r['local_hit']} | {r['openai_hit']} "
            f"| {r['local_citation']} | {r['openai_citation']} "
            f"| {r['local_composite']} | {r['openai_composite']} "
            f"| {r['local_query_s']} | {r['openai_query_s']} | {r['query_ratio_openai_vs_local']} "
            f"| {r['local_index_build_s']} | {r['openai_index_build_s']} "
            f"| {r['local_latency_s']} | {r['openai_latency_s']} |"
        )

    # Smoke dev: same lane as local
    md_lines.extend(
        [
            "",
            "## OpenAI smoke trên dev lane (cùng lane với Local)",
            "",
            "| Config | Hit | Cit | Composite | Query (s) | Index (s) | Latency (s) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for sid in ("smoke_openai_rec800_dense_chroma", "smoke_openai_rec800_hybrid_chroma"):
        s = _pick(openai_smoke, sid)
        if s:
            md_lines.append(
                f"| `{sid}` | {_f(s, 'retrieval_hit_rate')} | {_f(s, 'citation_correctness')} "
                f"| {_f(s, 'composite_score')} | {_f(s, 'query_time_avg')} | {_f(s, 'index_build_time')} "
                f"| {_f(s, 'latency')} |"
            )

    md_lines.extend(
        [
            "",
            "## Nguồn",
            "",
            "- `reports/benchmark_exportjson_phase1_results.csv`",
            "- `reports/benchmark_exportjson_openai_validation_results.csv`",
            "- `reports/benchmark_exportjson_openai_phase3_results.csv`",
            f"- CSV bảng này: `{csv_path.name}`",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


if __name__ == "__main__":
    main()
