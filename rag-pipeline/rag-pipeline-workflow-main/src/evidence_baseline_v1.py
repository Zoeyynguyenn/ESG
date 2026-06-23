"""CLI mong muon cho baseline lexical (giu tuong thich)."""

import argparse
import json

from evidence_rag import get_chunks, run_query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--reindex", action="store_true")
    args = parser.parse_args()
    chunks = get_chunks(force_rebuild=args.reindex)
    out = run_query(args.question, chunks, top_k=args.top_k)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
