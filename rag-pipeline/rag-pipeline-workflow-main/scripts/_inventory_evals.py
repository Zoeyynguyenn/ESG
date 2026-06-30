import json
from pathlib import Path

for d in sorted(Path("data/eval_results").iterdir()):
    lf = d / "goldns_emni_rag_eval_latest.json"
    if lf.exists():
        r = json.loads(lf.read_text("utf-8"))
        companies = list(r.get("by_company", {}).keys())
        ans = r.get("answer_accuracy")
        overall = r.get("overall_score")
        ret = r.get("retrieval_hit_top1")
        print(f"{d.name}: companies={companies} ans={ans} ret={ret} overall={overall}")
