# Preflight — Raw Nexteye smoke benchmark

Ngày: 2026-05-29  
Mục tiêu: so sánh data gốc “lộn xộn” vs lane `05_company_export_json` đã chuẩn hóa.

---

## 1) Data gốc đã xác định

**Nguồn:** `C:\Users\nguye\Downloads\data-company`

**Công ty Nexteye (넥스트아이):**

| Mục | Giá trị |
|---|---|
| Thư mục chọn | `(주)넥스트아이_일반자료_20260424` |
| Lý do chọn | Chỉ có **một** bản Nexteye; cấu trúc thư mục ESG/DART/HTML/XML **chưa** có `dataset_package_*` / `splits/*.jsonl` — đây là bản **raw nhất** trong Downloads |
| So với lane chuẩn | `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/` (9 jsonl + manifest, ~5.7 MB) |

**Cây thư mục rút gọn:**

```
(주)넥스트아이_일반자료_20260424/
├── MANIFEST.md
├── 01_기업기본정보/
├── 02_재무_신용/          ← DART_corp_code.json, DART 공시 PDF/HTML, XBRL…
├── 03_고용_인사/
├── 04_환경_안전_공표/
├── 05_정부지원_투자이력/
├── 06_지식재산_기술/      ← KIPRIS XML
├── 07_뉴스_평판/          ← Naver/Google news JSON + HTML
├── 08_외부검색/
├── 08_웹사이트_캡처/
└── 09_기타/
```

**Thống kê file:**

| | Raw Nexteye | Package chuẩn hóa |
|---|---:|---:|
| Số file | 141 | 13 |
| Dung lượng | ~44.6 MB | ~5.7 MB |
| Định dạng chính | .html 58, .xml 37, .pdf 15 | .jsonl 9 |

**File quan trọng cho eval smoke (gợi ý):**

- `02_재무_신용/DART_corp_code.json` — ticker / corp code
- `MANIFEST.md` — metadata tổng hợp (không có `export_type` 1.1.1 như jsonl package)

**Không ingest được với pipeline hiện tại:** `.docx` (10), `.xlsx` (5) — `rag_common.iter_corpus_files()` không liệt kê suffix này.

---

## 2) Ước lượng thời gian & chi phí (smoke 2 config × 5 câu)

### Thời gian

| Hạng mục | Ước lượng | Ghi chú |
|---|---|---|
| Setup lane (junction + config + eval raw) | 30–45 phút dev **một lần** | Chưa có lane `company_export_json_raw_nexteye_smoke` trong repo |
| Index lần 1 (Chroma + OpenAI embed) | **5–15 phút** | Nếu **bỏ PDF** hoặc chỉ `pypdf` (không OCR) |
| Index lần 1 | **45–90+ phút** | Nếu parser mặc định chạy **Docling/RapidOCR** trên 15 PDF (~20 MB) — đã thấy ~2.5 phút/PDF trong thử nhanh |
| Index lần 2 (config retrieval thứ 2) | **0 phút** | Có thể `--reuse-index true` (cùng embedding/chunking) |
| Query 5 câu × 2 mode | **1–3 phút** | Extractive; generative ~2× (~4 s/câu như smoke CI) |
| **Tổng smoke (tối ưu)** | **~15–25 phút** | PDF tắt hoặc pypdf + reuse index |
| **Tổng smoke (xấu)** | **~1.5–2 giờ** | OCR full PDF × 2 index |

### Chi phí API (OpenAI `text-embedding-3-small` + tùy generative)

| Hạng mục | Ước lượng |
|---|---|
| Embedding ingest (html+xml+json+md, không PDF) | ~0.2–1M token → **$0.004–0.02** / lần index |
| Embedding + PDF text (pypdf) | có thể **$0.02–0.06** / lần index |
| 2 config (reuse index) | **×1** embed, không ×2 |
| Generative 5 câu × 2 retrieval mode | **~$0.01–0.03** (gpt-4o-mini) |
| **Tổng smoke hợp lý** | **~$0.02–0.10** |
| RAGAS | Không bắt buộc — bỏ qua |

**Kết luận chi phí:** **Thấp** nếu kiểm soát PDF/OCR; **không** đáng kể so với full lane 20 câu + generative + RAGAS.

---

## 3) Rủi ro kỹ thuật (quan trọng hơn tiền)

### A. Lane chưa tồn tại

Repo chỉ hỗ trợ `company_export_json_{dev,validation,full}` trên bucket `05_company_export_json`. Cần thêm bucket/lane riêng (vd. `06_company_raw_nexteye`) + sửa nhẹ `rag_common`, `retrieval_v3`, `run_benchmark_case` — **không** viết framework mới.

### B. Eval / scoring lệch path (rủi ro cao)

Smoke CI hiện tại trỏ `expected_source` → `.../splits/dev.jsonl` / `manifest.json`.  
Raw **không có** các path đó → nếu copy nguyên eval set, **hit_rate / citation có thể ≈ 0** dù retrieval tốt.

**Cần:** eval set riêng 5 câu, `expected_source` trỏ file raw (vd. `.../DART_corp_code.json`, `MANIFEST.md`).  
**Không** sửa retrieval — chỉ mapping eval (đúng yêu cầu bước 6).

### C. So sánh baseline “không công bằng tuyệt đối”

| | Lane chuẩn | Raw |
|---|---|---|
| Corpus | 1 jsonl full (~620 chunks đã đo) | ~141 file đa định dạng, nhiễu news/HTML |
| Eval path | package_split_match | path/file match (cần matcher mở rộng hoặc alias) |
| Metadata | manifest.json có export_type/version | MANIFEST.md kiểu thu thập, không cùng schema |

→ Smoke trả lời: **“raw có đủ signal để đáng test full?”** — không phải “số composite có bằng 0.79 OpenAI E2E không”.

### D. PDF / parser

15 PDF (~20 MB) là **nút thắt thời gian**, không phải tiền. Khuyến nghị smoke: `RAG_PDF_PARSER=pypdf` hoặc loại PDF khỏi manifest smoke.

---

## 4) Baseline để so (tham chiếu)

| Run | hit | cit | composite | query_avg |
|---|---:|---:|---:|---:|
| Production smoke CI (5 câu, generative, package) | 1.0 | 1.0 | ~0.73 | ~4.2 s |
| OpenAI E2E generative (20 câu, package) | 1.0 | 1.0 | 0.79 | ~2.05 s |
| OpenAI E2E extractive (20 câu) | 1.0 | 1.0 | 0.65 | ~0.94 s |

Raw smoke **mục tiêu tối thiểu:** hit ≥ 0.6, cit ≥ 0.6 trên 5 câu có eval path đúng — nếu không, **no-go full**.

---

## 5) Go / no-go — **chạy smoke preflight?**

| | Đánh giá |
|---|---|
| **Chi phí** | ✅ Thấp (~$0.02–0.10) |
| **Thời gian** | ⚠️ 15–25 phút nếu setup + tắt OCR; ❌ 1–2h nếu không |
| **Effort setup** | ⚠️ ~30–45 phút code/lane/eval (lần đầu) |
| **Giá trị** | ✅ Biết raw có đáng đưa vào pipeline export hay không |
| **Khuyến nghị** | **Có thể làm smoke** với điều kiện: junction (không copy 45 MB), eval raw 5 câu, `pypdf`/skip PDF, extractive hoặc 1 mode generative, **không** RAGAS |

### Kết luận 1 dòng (trước khi chạy)

**Chưa chạy benchmark** — preflight: **đáng làm smoke có kiểm soát (go có điều kiện)**; **chưa go full** cho đến khi smoke hit/cit đủ sau khi sửa eval path; **không nên** chạy nếu để OCR toàn bộ PDF.

---

## 6) Việc cần làm nếu user đồng ý chạy

1. Junction: `data/rag_dataset/06_company_raw_nexteye/(주)넥스트아이_일반자료_20260424` → Downloads (không copy).
2. Lane + config `configs/benchmark_raw_nexteye_smoke.yaml` (2 retrieval, Chroma, pool 64, OpenAI embed).
3. Eval: `.rag/.../eval_set_raw_nexteye_smoke.md` (5 câu, path raw).
4. Script: `scripts/run_raw_nexteye_smoke_benchmark.py` → `reports/benchmark_raw_nexteye_smoke_*.{csv,md}`.
5. Env: `RAG_PDF_PARSER=pypdf`, `corpus_ratio=1.0`, không RAGAS.

**Lệnh dự kiến (sau khi implement):**

```powershell
cd E:\Documents\rag-pipeline-workflow
$env:RAG_PDF_PARSER='pypdf'
$env:RAG_BENCHMARK_LLM_PROVIDER='openai_api'
python scripts/run_raw_nexteye_smoke_benchmark.py
```
