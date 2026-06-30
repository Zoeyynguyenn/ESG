import json
from pathlib import Path

folder = sorted(Path("data/eval_results/20260630_v3c").glob("goldns_emni_rag_eval_*/"))[0]
rows = [json.loads(l) for l in (folder / "results.jsonl").read_text("utf-8").splitlines() if l.strip()]

seah_ans = [r for r in rows if r.get("company_id") == "seah" and r.get("partition") == "answerable_gold"]
seah_fails = [r for r in seah_ans if not r.get("answer_correct")]

emp_fails = [r for r in seah_fails if r.get("question_family") == "employee_status"]
print(f"employee_status fails v3c: {len(emp_fails)}")
for r in emp_fails:
    pred = str(r.get("predicted_answer", ""))[:25]
    top1 = str((r.get("top_doc_titles") or [""])[0])[:35]
    print(f"  {r['question_id']}: gold={r['gold_answer_raw']} pred={pred} top1={top1}")
