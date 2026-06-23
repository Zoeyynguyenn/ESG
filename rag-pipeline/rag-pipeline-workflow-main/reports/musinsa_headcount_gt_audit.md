# Musinsa headcount GT audit (package lane)

**Date:** 2026-06-11  
**Package:** `무신사_dataset_package_20260608T092823`  
**Method:** Direct file scan — no retrieve API  
**Machine JSON:** `reports/musinsa_headcount_gt_audit.json`

---

## Classification

**`gt_present_in_package_and_indexable` (A)**

Ground-truth headcount evidence **exists** in the indexed lane (`splits/full.jsonl`, `record_role=company_evidence`).

---

## Canonical GT anchor

| Field | Value |
|-------|--------|
| **record_id** | `rec_27e2235c5c45f84a` |
| **doc_id** | `doc_507acb85838aa8df` |
| **source_url** | `https://www.etnews.com/20250901000141` |
| **lane** | `splits/full.jsonl` |
| **Numeric anchor** | `총직원 수는1891명` (also `1604명` prior year) |

**Snippet (from package):**

> …전체 임직원수도 287명 증가했다. 지난 6월 기준 **총직원 수는1891명**으로 정규직 1745명, 비정규직 146명을 합한 수다. 지난해 말 기준 직원 수는 **1604명**이다…

Same article appears in `records/company_evidence.jsonl` and `splits/dev.jsonl` (duplicate rows/chunks).

---

## Search counts (package)

| Pattern | `full.jsonl` | All package JSONL | `_sources/` |
|---------|--------------|-------------------|-------------|
| `1891명` | 4 row hits (3 unique record_ids) | 12 | 0 |
| `1891` substring (non-anchor) | 5 | — | — |
| Headcount context regex | 9 | — | — |

**`1891` substring false friends in `full.jsonl` (not workforce GT):**

- National SME statistics tables (`…851891,337…`, phone/ID numbers)
- UI timestamps (`2026-06-08 …`) containing digit run `1891`

These are **not** Musinsa total headcount answers.

---

## Chunk simulation (fresh, no API)

Re-running `rag_common._chunks_from_export_jsonl(full.jsonl)`:

- **3,499** chunks from current `full.jsonl`
- **4** chunks contain `1891명` (ETNews article text)
- **1** chunk contains header `rec_27e2235c5c45f84a`

GT is **indexable in principle** if index is rebuilt from current `full.jsonl`.

---

## `_sources/` lane

No `_sources/` directory with additional headcount GT found in this workspace copy.

---

## Answers (package only)

1. **`1891명` in package?** → **Yes** (`rec_27e2235c5c45f84a`, ETNews 2025-09-01).
2. **Outside indexed lane?** → **No** — present in `full.jsonl`.
3. **Clean GT vs noise?** → One clean workforce anchor; separate `1891` digit runs exist as table/UI noise.
