import json
from pathlib import Path

r = json.loads(Path("data/eval_results/20260630_v3_final/goldns_emni_rag_eval_latest.json").read_text("utf-8"))
print("=== FULL EVAL v3 (goldns + seah) ===")
print("answer_accuracy:", r["answer_accuracy"])
print("retrieval_hit_top1:", r["retrieval_hit_top1"])
print("abstain_accuracy:", r["abstain_accuracy"])
print("overall_score:", r["overall_score"])
print()
print("=== By company ===")
for co, m in r.get("by_company", {}).items():
    ans = m.get("answer_accuracy")
    ret = m.get("retrieval_hit_top1")
    abs_ = m.get("abstain_accuracy")
    tot = m.get("total")
    print(f"  {co}: ans={ans}  ret={ret}  abs={abs_}  total={tot}")
print()
print("=== Fail by family (all companies) ===")
for fam, cnt in r.get("fail_by_family", {}).items():
    print(f"  {fam}: {cnt}")
