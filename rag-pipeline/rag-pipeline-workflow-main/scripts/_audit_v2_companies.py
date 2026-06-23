"""One-off audit helper for rebuild v2."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = [
    json.loads(l)
    for l in (ROOT / "data/golden_set/v2/step1_corpus_units/corpus_units.jsonl").read_text(encoding="utf-8").splitlines()
    if l.strip()
]
lines = []
for co in ["무신사", "레이시온"]:
    sub = [r for r in rows if r.get("company") == co]
    lines.append(f"=== {co} units {len(sub)} ===")
    st = Counter(r.get("source_type") for r in sub)
    lines.append(f"source_types {dict(st)}")
    for r in sorted(sub, key=lambda x: -(x.get("substance_score") or 0))[:12]:
        t = (r.get("text") or "")[:160].replace("\n", " ")
        lines.append(f"{r.get('record_id')} {r.get('source_type')} sub={r.get('substance_score')} {t}")
(ROOT / "reports/_audit_v2_companies.txt").write_text("\n".join(lines), encoding="utf-8")
