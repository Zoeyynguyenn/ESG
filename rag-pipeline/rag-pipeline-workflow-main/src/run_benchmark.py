"""CLI wrapper de goi benchmark theo mode/lane nhu yeu cau."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["stagewise", "focused", "final"], required=True)
    parser.add_argument(
        "--lane",
        choices=[
            "dev",
            "validation",
            "full",
            "company_public_dev",
            "company_export_json_dev",
            "company_export_json_validation",
            "company_export_json_full",
        ],
        required=True,
    )
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--benchmark-kind", choices=["retrieval_only", "full_pipeline"], default="retrieval_only")
    parser.add_argument("--reuse-index", default="true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", default="true")
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--case-timeout-sec", type=int, default=1200)
    parser.add_argument("--enable-ragas", action="store_true")
    parser.add_argument("--matrix", default="configs/benchmark_matrix_v1.yaml")
    parser.add_argument("--vector-store", choices=["chroma", "qdrant"], default="chroma")
    parser.add_argument("--embed-local-only", default="auto", choices=["auto", "true", "false"])
    parser.add_argument("--pdf-parser", default="auto", choices=["auto", "pypdf", "docling"])
    args = parser.parse_args(argv)

    base_dir = Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        str(base_dir / "src" / "run_benchmark_matrix.py"),
        "--mode",
        args.mode,
        "--lane",
        args.lane,
        "--top-n",
        str(args.top_n),
        "--benchmark-kind",
        args.benchmark_kind,
        "--reuse-index",
        str(args.reuse_index),
        "--matrix",
        args.matrix,
        "--resume",
        str(args.resume),
        "--case-timeout-sec",
        str(args.case_timeout_sec),
        "--vector-store",
        args.vector_store,
        "--embed-local-only",
        args.embed_local_only,
        "--pdf-parser",
        args.pdf_parser,
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.force_rerun:
        cmd.append("--force-rerun")
    if args.enable_ragas:
        cmd.append("--enable-ragas")
    result = subprocess.run(cmd, cwd=str(base_dir))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
