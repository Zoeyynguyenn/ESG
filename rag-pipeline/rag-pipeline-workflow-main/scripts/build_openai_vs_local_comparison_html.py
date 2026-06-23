"""Build Local (Pha 1 MiniLM dev) vs OpenAI validation comparison HTML."""

from __future__ import annotations

import csv
import html
from datetime import datetime
from pathlib import Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(row: dict, key: str, default: str = "") -> str:
    return str(row.get(key, default) or default)


def _pick(rows: list[dict], config_id: str) -> dict | None:
    for r in rows:
        if r.get("config_id") == config_id:
            return r
    return None


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    local_path = base / "reports" / "benchmark_exportjson_phase1_results.csv"
    openai_path = base / "reports" / "benchmark_exportjson_openai_validation_results.csv"
    smoke_path = base / "reports" / "benchmark_exportjson_openai_smoke_results.csv"
    phase3_path = base / "reports" / "benchmark_exportjson_openai_phase3_results.csv"
    out_path = base / "reports" / "benchmark_exportjson_openai_vs_local_validation.html"

    local_rows = _read_csv(local_path)
    openai_rows = _read_csv(openai_path)
    smoke_rows = _read_csv(smoke_path) if smoke_path.exists() else []

    pairs = [
        (
            "recursive_800_120",
            "semantic_dense",
            "p1_rec800_minilm_dense_chroma",
            "val_openai_rec800_dense_chroma",
            "smoke_openai_rec800_dense_chroma",
        ),
        (
            "recursive_800_120",
            "hybrid_dense_bm25",
            "p1_rec800_minilm_hybrid_chroma",
            "val_openai_rec800_hybrid_chroma",
            "smoke_openai_rec800_hybrid_chroma",
        ),
        (
            "section_based",
            "semantic_dense",
            "p1_section_minilm_dense_chroma",
            "val_openai_section_dense_chroma",
            None,
        ),
        (
            "section_based",
            "hybrid_dense_bm25",
            "p1_section_minilm_hybrid_chroma",
            "val_openai_section_hybrid_chroma",
            None,
        ),
    ]

    table_rows: list[str] = []
    for chunk, retr, lid, oid, sid in pairs:
        loc = _pick(local_rows, lid) or {}
        oai = _pick(openai_rows, oid) or {}
        smk = _pick(smoke_rows, sid) if sid else {}
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(chunk)}</td>"
            f"<td>{html.escape(retr)}</td>"
            f"<td>MiniLM<br><small>dev lane</small></td>"
            f"<td>{_f(loc, 'retrieval_hit_rate')}</td>"
            f"<td>{_f(loc, 'citation_correctness')}</td>"
            f"<td>{_f(loc, 'composite_score')}</td>"
            f"<td>{_f(loc, 'query_time_avg')}</td>"
            f"<td>OpenAI<br><small>validation lane</small></td>"
            f"<td>{_f(oai, 'retrieval_hit_rate')}</td>"
            f"<td>{_f(oai, 'citation_correctness')}</td>"
            f"<td>{_f(oai, 'composite_score')}</td>"
            f"<td>{_f(oai, 'query_time_avg')}</td>"
            f"<td>{_f(smk, 'retrieval_hit_rate') or '—'}</td>"
            f"<td>{_f(smk, 'composite_score') or '—'}</td>"
            f"<td>{_f(oai, 'ragas_status')}</td>"
            "</tr>"
        )

    # Gate logic
    best_oai = max(
        openai_rows,
        key=lambda r: float(r.get("composite_score") or 0),
        default={"config_id": "", "composite_score": "0"},
    )
    gate_blockers = []
    if all(float(r.get("retrieval_hit_rate") or 0) == 0 for r in openai_rows):
        gate_blockers.append("OpenAI validation: retrieval_hit_rate = 0 cho tat ca case")
    if smoke_rows and all(float(r.get("retrieval_hit_rate") or 0) == 1 for r in smoke_rows):
        if all(float(r.get("retrieval_hit_rate") or 0) == 0 for r in openai_rows):
            gate_blockers.append("Lech lon smoke (dev hit=1.0) vs validation (hit=0.0)")
    if any("ragas_unavailable" in (r.get("ragas_reason") or "") for r in openai_rows):
        gate_blockers.append("RAGAS chua chay: thieu package ragas")

    phase3_ok = not gate_blockers

    # Phase 3: Chroma vs Qdrant (same retrieval/chunking, pool=64)
    phase3_rows = _read_csv(phase3_path) if phase3_path.exists() else []
    p3_pairs = [
        ("section_based", "hybrid_dense_bm25", "p3_openai_section_hybrid_chroma", "p3_openai_section_hybrid_qdrant"),
        ("section_based", "semantic_dense", "p3_openai_section_dense_chroma", "p3_openai_section_dense_qdrant"),
        ("recursive_800_120", "hybrid_dense_bm25", "p3_openai_rec800_hybrid_chroma", "p3_openai_rec800_hybrid_qdrant"),
    ]
    p3_table_rows: list[str] = []
    for chunk, retr, cid, qid in p3_pairs:
        chroma = _pick(phase3_rows, cid) or {}
        qdrant = _pick(phase3_rows, qid) or {}
        p3_table_rows.append(
            "<tr>"
            f"<td>{html.escape(chunk)}</td>"
            f"<td>{html.escape(retr)}</td>"
            f"<td>{_f(chroma, 'retrieval_hit_rate') or '—'}</td>"
            f"<td>{_f(chroma, 'citation_correctness') or '—'}</td>"
            f"<td>{_f(chroma, 'composite_score') or '—'}</td>"
            f"<td>{_f(chroma, 'query_time_avg') or '—'}</td>"
            f"<td>{_f(chroma, 'latency') or '—'}</td>"
            f"<td>{_f(qdrant, 'retrieval_hit_rate') or '—'}</td>"
            f"<td>{_f(qdrant, 'citation_correctness') or '—'}</td>"
            f"<td>{_f(qdrant, 'composite_score') or '—'}</td>"
            f"<td>{_f(qdrant, 'query_time_avg') or '—'}</td>"
            f"<td>{_f(qdrant, 'latency') or '—'}</td>"
            f"<td>{_f(qdrant, 'qdrant_status') or '—'}</td>"
            "</tr>"
        )

    p3_winner_note = ""
    if phase3_rows:
        ok_rows = [r for r in phase3_rows if r.get("status") == "success"]
        if ok_rows:
            best = max(ok_rows, key=lambda r: float(r.get("composite_score") or 0))
            comp_chroma = [
                r
                for r in ok_rows
                if r.get("vector_store") == "chroma" and r.get("chunking") == best.get("chunking")
            ]
            comp_qdrant = [
                r
                for r in ok_rows
                if r.get("vector_store") == "qdrant" and r.get("chunking") == best.get("chunking")
            ]
            if comp_chroma and comp_qdrant:
                c = max(comp_chroma, key=lambda r: float(r.get("composite_score") or 0))
                q = max(comp_qdrant, key=lambda r: float(r.get("composite_score") or 0))
                delta = abs(float(c.get("composite_score") or 0) - float(q.get("composite_score") or 0))
                pick = q if delta < 0.02 else best
                store = pick.get("vector_store", "")
                p3_winner_note = (
                    f"<p>Winner Phase 3: <strong>{html.escape(_f(pick, 'config_id'))}</strong> "
                    f"(composite={_f(pick, 'composite_score')}, hit={_f(pick, 'retrieval_hit_rate')}, "
                    f"query_avg={_f(pick, 'query_time_avg')}s). "
                    f"Delta Chroma/Qdrant cung family: {delta:.4f} "
                    f"({'uu tien Qdrant production-scale' if delta < 0.02 and store == 'qdrant' else 'theo composite cao hon'}).</p>"
                )

    gate_html = (
        "<ul>"
        + "".join(f"<li><strong>BLOCKER:</strong> {html.escape(b)}</li>" for b in gate_blockers)
        + "</ul>"
        if gate_blockers
        else "<p><strong>PASS:</strong> Co the mo Phase 3 OpenAI Chroma vs Qdrant.</p>"
    )

    doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8"/>
  <title>So sanh Local vs OpenAI (validation)</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; margin: 24px; color: #1a1a1a; }}
    h1 {{ font-size: 1.4rem; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; margin: 16px 0; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
    th {{ background: #f0f4f8; }}
    .warn {{ background: #fff3cd; padding: 12px; border-left: 4px solid #ffc107; }}
    .meta {{ color: #555; font-size: 0.85rem; }}
    col.local {{ background: #f8fbff; }}
    col.openai {{ background: #f6fff6; }}
  </style>
</head>
<body>
  <h1>So sanh Local (MiniLM, Pha 1 dev) vs OpenAI (validation)</h1>
  <p class="meta">Tao luc: {datetime.now().isoformat(timespec="seconds")}<br/>
  Nguon: <code>{local_path.name}</code>, <code>{openai_path.name}</code>, <code>{smoke_path.name}</code></p>

  <div class="warn">
    <strong>Luu y:</strong> Local = lane <code>company_export_json_dev</code> (5–18 case pool khac);
    OpenAI validation = lane <code>company_export_json_validation</code> (20 cau).
    Cot smoke = OpenAI tren <code>dev</code> (5 cau) de doi chieu gate smoke vs validation.
  </div>

  <table>
    <thead>
      <tr>
        <th rowspan="2">Chunking</th>
        <th rowspan="2">Retrieval</th>
        <th colspan="4">Local MiniLM (dev)</th>
        <th colspan="4">OpenAI embedding (validation)</th>
        <th colspan="2">OpenAI smoke (dev)</th>
        <th rowspan="2">RAGAS</th>
      </tr>
      <tr>
        <th>Stack</th><th>Hit</th><th>Citation</th><th>Composite</th><th>Query s</th>
        <th>Stack</th><th>Hit</th><th>Citation</th><th>Composite</th><th>Query s</th>
        <th>Hit</th><th>Composite</th>
      </tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>

  <h2>Gate quyet dinh (Codex)</h2>
  {gate_html}
  <p>Top OpenAI validation theo composite: <strong>{html.escape(_f(best_oai, 'config_id'))}</strong>
     (composite={_f(best_oai, 'composite_score')}).</p>
  <p>Phase 3 OpenAI Chroma vs Qdrant: <strong>{'CHO PHEP' if phase3_ok else 'TAM HOAN'}</strong>
     — validation hit/citation da tin cay sau eval matcher fix.</p>

  <h2>OpenAI Phase 3: Chroma vs Qdrant</h2>
  <p class="meta">Nguon: <code>{phase3_path.name}</code> — top 3 validation configs, pool=64, reranker=none.</p>
  {"<p><em>Chua co CSV Phase 3 — chay benchmark_exportjson_openai_phase3.yaml</em></p>" if not phase3_rows else ""}
  <table>
    <thead>
      <tr>
        <th rowspan="2">Chunking</th>
        <th rowspan="2">Retrieval</th>
        <th colspan="5">Chroma</th>
        <th colspan="5">Qdrant</th>
        <th rowspan="2">Qdrant status</th>
      </tr>
      <tr>
        <th>Hit</th><th>Citation</th><th>Composite</th><th>Query s</th><th>Latency s</th>
        <th>Hit</th><th>Citation</th><th>Composite</th><th>Query s</th><th>Latency s</th>
      </tr>
    </thead>
    <tbody>
      {''.join(p3_table_rows) if p3_table_rows else '<tr><td colspan="13">—</td></tr>'}
    </tbody>
  </table>
  {p3_winner_note}
</body>
</html>
"""
    out_path.write_text(doc, encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
