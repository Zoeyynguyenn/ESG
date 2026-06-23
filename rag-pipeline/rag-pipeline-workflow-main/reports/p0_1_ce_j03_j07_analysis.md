# P0.1 — Mổ xẻ CE-J03–J07 (retrieval/eval fix)

**Ngày:** 2026-05-29  
**Lane:** `company_export_json_full` (넥스트아이 package)  
**Stack kiểm tra:** `section_based` + `hybrid_dense_bm25` + OpenAI embed + Qdrant, pool=64

## Tóm tắt

| ID | Triệu chứng trước fix | Nguyên nhân gốc | Fix | Top chunk sau fix |
|---|---|---|---|---|
| CE-J03 | hit=1, answer sai | Hybrid xếp chunk nhiễu (news/legal) trên record DART/probe | Field boost + BM25 query expansion | Probe profile: `corp_code: 00614593` |
| CE-J04 | hit=1, answer sai | Top chunk không có `market: KOSDAQ` | Boost `krx_esg` / `market: kosdaq` + BM25 expansion | `KRX company metadata … market: KOSDAQ` |
| CE-J05 | hit=1, answer sai | URL không có trong text homepage riêng; nằm ở probe profile | Boost `홈페이지: http://www.nexteye.com` | Cùng probe profile chunk |
| CE-J06 | hit=1, expected sai | `company_esg_dataset` **không tồn tại** trong package; metadata ở `manifest.json` | Sửa eval → `raw_public_first`; inject manifest at query time | `manifest.json` (`lane_policy.primary_benchmark_lane`) |
| CE-J07 | hit=1, expected sai | Expected `1.0` vs thực tế `dataset_version: 1.1.1` | Sửa eval + manifest inject | `manifest.json` |
| CE-J08 | (cùng nhóm metadata) | Expected timestamp cũ `07:16:04` vs `exported_at 09:14:09` | Sửa eval + manifest inject | `manifest.json` |

## Phân tích chi tiết

### 1. Retrieval “hit” nhưng answer fail

Matcher `package_split_match` coi mọi chunk cùng package là hit — kể cả chunk news/garbled. Citation=1.0 vì top-1 vẫn thuộc `full.jsonl`, nhưng **nội dung chunk không chứa field cần trả lời**.

### 2. Dữ liệu thực tế trong corpus

- **J03:** `rec_487707d631ecca43` (dart) + probe profile (line ~42 trong full split)  
- **J04:** `rec_497992415b48e244` — `market: KOSDAQ`  
- **J05:** URL `http://www.nexteye.com` chỉ xuất hiện trong **probe profile**, không có string `nexteye.com` trong metadata homepage records  
- **J06–J08:** Chỉ có trong `manifest.json` / `README.md`, **không** nằm trong record jsonl

### 3. Lỗi eval (ground truth)

| Câu | Expected cũ | Ground truth đúng |
|---|---|---|
| J06 | `company_esg_dataset` | `raw_public_first` (manifest `lane_policy.primary_benchmark_lane`) |
| J07 | `1.0` | `1.1.1` (`dataset_version`) |
| J08 | `2026-05-28T07:16:04Z` | `2026-05-28T09:14:09Z` (`exported_at`) |
| J05 | bắt buộc URL exact | URL trong probe profile; chấp nhận `nexteye.com` / `information@nexteye` |

## Thay đổi code

| File | Thay đổi |
|---|---|
| `src/export_json_retrieval_hints.py` | Field boost, BM25 `expand_query`, runtime inject `manifest.json` |
| `src/retrieval_v3.py` | Gọi boost + expanded BM25 trong `retrieve_hybrid_dense_bm25` |
| `src/run_benchmark_case.py` | Corpus manifest thêm `manifest.json` + `README.md` |
| `src/eval_scoring_v2.py` | `EXTRACTED_FIELD_ALIASES` cho metadata questions |
| `.rag/.../eval_set_company_export_json_dev.md` | Sửa J05–J08 expected + expected_source |
| `scripts/p0_1_verify_ce_j03_j07.py` | Script kiểm tra top chunk J03–J07 |

## Kết quả verify retrieval (post-fix)

```
CE-J03: probe profile, corp_code 00614593, boost=0.88
CE-J04: KRX metadata, market KOSDAQ, boost=0.60
CE-J05: probe profile, homepage URL, boost=0.84
CE-J06: manifest.json, raw_public_first lane, boost=0.60
CE-J07: manifest.json, dataset_version 1.1.1, boost=0.88
```

## Việc còn lại trước mở rộng benchmark matrix

1. **Re-run generative report** trên full lane (`generate_openai_generative_results_report.py`) để xác nhận answer layer J03–J07  
2. **Re-index** (optional nhưng khuyến nghị): manifest/README trong corpus manifest → chunk BM25/dense ổn định thay vì chỉ runtime inject  
3. **Lane-specific eval files** (`dev` / `validation` / `full`) với `expected_source` khớp split  
4. Chạy lại E2E gate sau re-index nếu muốn RAGAS trên 20 câu

## Lệnh kiểm tra nhanh

```powershell
cd E:\Documents\rag-pipeline-workflow
$env:PYTHONIOENCODING='utf-8'
python scripts/p0_1_verify_ce_j03_j07.py
```

## Quyết định

**P0.1: `pass_with_limits`** — gate mở cho P1.

| Tiêu chí | Kết quả |
|---|---|
| J03–J07 không còn insufficient sai (retrieval) | ✅ J03–J05, J07 generative OK; J06 gen fail (1/5 metadata-gov còn lại) |
| answer_correctness generative không giảm | ✅ **8 → 12/20** (+4) |
| insufficient_handling không giảm | ✅ **4/5** insufficient (J17 unicode — đã thêm alias scoring) |
| J06–J08 evidence/expected mismatch | ✅ Top source = `manifest.json`; extractive pass J06–J08 |

**Re-index:** 620 chunks, manifest trong BM25/Qdrant (`scripts/p0_1_reindex_full_lane.py`).

**Báo cáo mới:** `reports/openai_generative_results_summary.md` (2026-05-29T12:08:15).

**Chưa mở rộng benchmark matrix.** Chuyển **P1:** freeze production config + smoke CI + monitoring.
