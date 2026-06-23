"""Benchmark production stack on Golden Set v2 subsets."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_GOLD_JSONL = ROOT / "data/golden_set/v2/step6_gold/golden_set.jsonl"
DEFAULT_EVAL_DIR = ROOT / "data/golden_set/v2/step6_gold/eval_by_company"
DEFAULT_REPORT_PATH = ROOT / "reports/golden_v2_benchmark_jina.md"

COMPANY_PACKAGES = [
    ("한샘", "한샘_dataset_package_20260608T042739", "hanssem"),
    ("레이시온", "레이시온_dataset_package_20260608T055801", "raysolution"),
    ("무신사", "무신사_dataset_package_20260608T092823", "musinsa"),
]


def _load_dotenv() -> None:
    for name in (".env.local", ".env"):
        p = ROOT / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k, v)


def _load_gold_rows(gold_jsonl: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in gold_jsonl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_eval_md(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Golden Set v2 - company subset",
        "",
        "| ID | Question | Expected Evidence Source | Expected Answer Notes | Record ID | Difficulty | Category | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['question_id']} | {row['question']} | {row.get('expected_source', '')} | "
            f"{row.get('ground_truth_answer', '')} | {row.get('ground_truth_record_id', '')} | "
            f"{row.get('difficulty', '')} | {row.get('question_type', '')} | approved |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_case(
    *,
    run_id: str,
    config_id: str,
    company_filter: str,
    eval_path: Path,
    eval_max: int,
    timeout_sec: int,
) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "src/run_benchmark_case.py"),
        "--run-id",
        run_id,
        "--config-id",
        config_id,
        "--dataset-lane",
        "company_export_json_full",
        "--benchmark-lane",
        "company_export_json_full",
        "--benchmark-mode",
        "full_pipeline",
        "--chunking-profile",
        "section_based",
        "--chunk-size",
        "800",
        "--chunk-overlap",
        "120",
        "--embedding-model",
        "openai:text-embedding-3-small",
        "--retrieval-mode",
        "hybrid_dense_bm25_rerank",
        "--reranker",
        "jina_api",
        "--reranker-backend",
        "jina_api",
        "--reranker-model",
        "jina-reranker-v3",
        "--top-k",
        "4",
        "--pool",
        "64",
        "--index-key",
        config_id,
        "--parser-version",
        "jsonl_v1",
        "--corpus-version",
        "golden_v2_per_record_chunks",
        "--corpus-ratio",
        "1.0",
        "--eval-max-questions",
        str(eval_max),
        "--reuse-index",
        "true",
        "--cache-root",
        "artifacts/benchmark_cache",
        "--eval-set-path",
        str(eval_path),
        "--vector-store",
        "qdrant",
        "--answer-mode",
        "generative",
        "--company-filter",
        company_filter,
        "--collect-failure-audit",
    ]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("RAG_BENCHMARK_LLM_PROVIDER", "openai_api")
    env.setdefault("OPENAI_MODEL", "gpt-4o-mini")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_sec,
        env=env,
    )
    payload: Dict[str, Any] = {"stdout": proc.stdout, "stderr": proc.stderr}
    try:
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                payload = json.loads(line)
                break
    except json.JSONDecodeError:
        payload["status"] = "failed"
        payload["error_reason"] = "no_json_payload"
    if proc.returncode != 0 and payload.get("status") != "success":
        payload.setdefault("status", "failed")
        payload.setdefault("error_reason", proc.stderr[-500:] if proc.stderr else f"exit_{proc.returncode}")
    return payload


def _sf(value: Any) -> float:
    try:
        return float(value) if value not in (None, "") else 0.0
    except Exception:
        return 0.0


def _weighted_avg(cases: List[Dict[str, Any]], key: str) -> float:
    total_n = sum(case["n_questions"] for case in cases if case.get("status") == "success")
    if not total_n:
        return 0.0
    return round(
        sum(_sf(case.get(key)) * case["n_questions"] for case in cases if case.get("status") == "success")
        / total_n,
        4,
    )


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Golden Set v2 subset")
    parser.add_argument("--gold-jsonl", type=Path, default=DEFAULT_GOLD_JSONL)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--title", default="# Golden Set v2 Benchmark - OpenAI + Jina v3")
    args = parser.parse_args(argv)
    args.gold_jsonl = args.gold_jsonl if args.gold_jsonl.is_absolute() else (ROOT / args.gold_jsonl)
    args.eval_dir = args.eval_dir if args.eval_dir.is_absolute() else (ROOT / args.eval_dir)
    args.report_path = args.report_path if args.report_path.is_absolute() else (ROOT / args.report_path)
    if args.json_out is not None and not args.json_out.is_absolute():
        args.json_out = ROOT / args.json_out
    return args


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    _load_dotenv()
    if not args.gold_jsonl.exists():
        print(f"Missing {args.gold_jsonl} - run golden set step 6 first", file=sys.stderr)
        return 1

    from eval_set_io import parse_eval_set_rows

    gold = _load_gold_rows(args.gold_jsonl)
    by_pkg: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in gold:
        by_pkg[row.get("package_name", "")].append(row)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    cases: List[Dict[str, Any]] = []
    for company_name, package_name, slug in COMPANY_PACKAGES:
        subset = by_pkg.get(package_name, [])
        if not subset:
            continue
        eval_path = args.eval_dir / f"eval_golden_v2_{slug}_ko.md"
        _write_eval_md(subset, eval_path)
        n_questions = len(parse_eval_set_rows(eval_path))
        run_id = f"golden_v2_{slug}_{ts}"
        config_id = f"golden_v2_jina_{slug}"
        print(f"Running {slug}: {n_questions} questions ...")
        payload = _run_case(
            run_id=run_id,
            config_id=config_id,
            company_filter=package_name,
            eval_path=eval_path,
            eval_max=n_questions,
            timeout_sec=7200,
        )
        payload["company"] = company_name
        payload["package"] = package_name
        payload["n_questions"] = n_questions
        payload["eval_path"] = str(eval_path.relative_to(ROOT))
        cases.append(payload)
        print(
            json.dumps(
                {
                    key: payload.get(key)
                    for key in (
                        "status",
                        "n_questions",
                        "retrieval_hit_rate",
                        "citation_correctness",
                        "answer_correctness",
                        "latency",
                    )
                },
                ensure_ascii=False,
            )
        )

    aggregate = {
        "total_questions": sum(case["n_questions"] for case in cases if case.get("status") == "success"),
        "retrieval_hit_rate": _weighted_avg(cases, "retrieval_hit_rate"),
        "citation_correctness": _weighted_avg(cases, "citation_correctness"),
        "answer_correctness": _weighted_avg(cases, "answer_correctness"),
        "query_time_avg": _weighted_avg(cases, "query_time_avg"),
        "latency_total_sec": round(sum(_sf(case.get("latency")) for case in cases), 1),
    }

    lines = [
        args.title,
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "Stack: hybrid_dense_bm25_rerank - Qdrant - gpt-4o-mini generative - jina-reranker-v3",
        f"Gold source: `{args.gold_jsonl.relative_to(ROOT)}`",
        "",
        "## Aggregate (weighted by question count)",
        "",
        f"- total_questions: **{aggregate['total_questions']}**",
        f"- retrieval_hit_rate: **{aggregate['retrieval_hit_rate']}**",
        f"- citation_correctness: **{aggregate['citation_correctness']}**",
        f"- answer_correctness: **{aggregate['answer_correctness']}**",
        f"- query_time_avg (sec): **{aggregate['query_time_avg']}**",
        f"- wall_latency_total (sec): **{aggregate['latency_total_sec']}**",
        "",
        "## Per company",
        "",
        "| company | n | status | hit | citation | answer | latency |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for case in cases:
        lines.append(
            f"| {case.get('company', '')} | {case.get('n_questions', 0)} | {case.get('status', '')} | "
            f"{case.get('retrieval_hit_rate', '')} | {case.get('citation_correctness', '')} | "
            f"{case.get('answer_correctness', '')} | {case.get('latency', '')} |"
        )

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = args.json_out or (ROOT / "reports" / f"golden_v2_benchmark_jina_{ts}.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps({"aggregate": aggregate, "cases": cases}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"report": str(args.report_path), "aggregate": aggregate}, ensure_ascii=False, indent=2))
    return 0 if aggregate["total_questions"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
