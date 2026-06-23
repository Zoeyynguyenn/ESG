"""Evidence-based query V1."""

from __future__ import annotations

import argparse
import json

from config import FINAL_TOP_K, RETRIEVAL_MODE, RETRIEVAL_MODES_V3, TOP_K
from evidence_rag import get_chunks, run_query
from rag_stack import query_chroma, stack_available


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--force-lexical", action="store_true")
    parser.add_argument(
        "--retrieval-mode",
        default=None,
        choices=RETRIEVAL_MODES_V3 + [None],
        help="V3 retrieval mode; mac dinh semantic_dense (query_chroma)",
    )
    args = parser.parse_args()
    retrieval_mode = args.retrieval_mode or RETRIEVAL_MODE

    if (
        not args.force_lexical
        and retrieval_mode in RETRIEVAL_MODES_V3
        and retrieval_mode != "semantic_dense"
    ):
        from retrieval_v3 import query_v3

        result = query_v3(args.question, retrieval_mode=retrieval_mode, top_k=args.top_k or FINAL_TOP_K)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.force_lexical and stack_available() and retrieval_mode == "semantic_dense":
        try:
            result = query_chroma(args.question, top_k=args.top_k)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        except Exception as exc:
            fallback_reason = str(exc)
    else:
        fallback_reason = "chroma_unavailable_or_forced_lexical"

    chunks = get_chunks()
    result = run_query(args.question, chunks, top_k=args.top_k)
    result["stack_fallback_reason"] = fallback_reason
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
