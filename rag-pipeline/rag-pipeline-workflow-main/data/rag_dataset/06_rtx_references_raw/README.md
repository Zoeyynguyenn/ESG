## RTX References Raw

Muc nay duoc tao de nap bo du lieu tham chieu moi cho `RTX` truoc khi chay lai:

1. `chunking` cho RAG
2. `candidate generation / Silver -> Gold` cho Golden Set

### Cau truc

- `_sources/`: 4 file PDF da copy tu `C:\Users\nguye\Downloads\data-company\demo_company\RTX_References\References`
- `web_sources/`: **5 raw HTML local** + **1 text snapshot** (DOJ fallback)
- `chunks/`: `rtx_chunked_corpus.jsonl` — chunked corpus cho RAG
- `source_urls.json`: danh sach 6 URL web tham chieu + trang thai download
- `web_sources_download_status.json`: ket qua kiem tra tung file HTML
- Golden Set step 1: `data/golden_set/v2/rtx_step1_corpus_units/corpus_units_rtx.jsonl`

### Trang thai hien tai (2026-06-12)

| Loai | So luong | Ghi chu |
|---|---|---|
| PDF local | 4 | San sang chunking |
| Raw HTML local | 5 | SEC x3 + RTX corporate x2 |
| Snapshot `.md` con lai | 1 | DOJ press release (403 blocked) |
| Chunked corpus | 2641+ | `chunks/rtx_chunked_corpus.jsonl` |
| Corpus units (GS step 1) | 2641+ | `data/golden_set/v2/rtx_step1_corpus_units/` |

### Ghi chu

- Raw HTML tai bang `scripts/download_rtx_web_sources.py` (Python + User-Agent).
- Chunking: `scripts/build_rtx_chunked_corpus.py` (pypdf cho PDF, section-aware cho SEC HTML).
- Trang DOJ (`justice.gov`) tra **HTTP 403** — chunk tu snapshot `.md` fallback.
- Lane da chunk; **chua ingest index, chua benchmark**.
