import json
from pathlib import Path

rows = [json.loads(l) for l in Path("data/source_raw/20260630_v3_local/collect_status.jsonl").read_text("utf-8").splitlines() if l.strip()]

print("=== GOLDNS structured ===")
for r in rows:
    if r["company_id"] == "goldns" and r.get("schema") not in ("dart_section_text", None):
        lp = Path(r.get("local_path") or "")
        print(f"  doc_title={r['doc_title']} | local_path_basename={lp.name} | schema={r['schema']}")

print()
print("=== SEAH structured ===")
for r in rows:
    if r["company_id"] == "seah" and r.get("schema") not in ("dart_section_text", None):
        lp = Path(r.get("local_path") or "")
        print(f"  doc_title={r['doc_title']} | local_path_basename={lp.name} | schema={r['schema']}")
