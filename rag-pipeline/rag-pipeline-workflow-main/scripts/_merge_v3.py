import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

merged_path = ROOT / "data/source_raw/20260630_merged_local/collect_status.jsonl"
existing = [json.loads(l) for l in merged_path.read_text("utf-8").splitlines() if l.strip()]

new_struct_path = ROOT / "data/source_raw/seah_structured_local/collect_status.jsonl"
new_struct = [json.loads(l) for l in new_struct_path.read_text("utf-8").splitlines() if l.strip()]

combined: dict = {}
for row in existing:
    if row.get("collect_status") != "ok":
        continue
    key = (row.get("company_id"), row.get("doc_title"))
    combined[key] = row

for row in new_struct:
    if row.get("collect_status") != "ok":
        continue
    art = row.get("artifact_dir")
    if not art or not Path(art).is_dir():
        print("SKIP missing dir:", row.get("doc_title"))
        continue
    key = (row.get("company_id"), row.get("doc_title"))
    combined[key] = row

rows = list(combined.values())
out_dir = ROOT / "data/source_raw/20260630_v3_local"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "collect_status.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

by_co = Counter(r["company_id"] for r in rows)
by_schema = Counter(r.get("schema", "?") for r in rows)
print("Total:", len(rows), "->", out_path)
print("By company:", dict(sorted(by_co.items())))
print("By schema:", dict(sorted(by_schema.items())))
