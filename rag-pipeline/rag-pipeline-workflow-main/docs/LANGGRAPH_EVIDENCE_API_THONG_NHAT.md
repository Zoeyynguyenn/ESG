# Thống nhất kỹ thuật — RAG Evidence Retrieval API (team LangGraph)

**Phiên bản:** 2026-06-05 (rev.5) · **Phía RAG pipeline:** `rag-pipeline-workflow`  
**Đối tác:** Team LangGraph (ESG)  
**Mục đích:** Căn chỉnh spec API trước khi implement Phase 1 staging.  
**Trạng thái:** Phase 1 staging **ACTIVE** — registry MVP: `musinsa`, `rayshion`, `hanssem`. Handoff: `docs/LANGGRAPH_API_HANDOFF.md`.

---

## 1. Tóm tắt thống nhất

| Hạng mục | Thống nhất |
|----------|------------|
| **Phạm vi API** | **Retrieval-only** — trả evidence/chunk + citation; **không** sinh câu trả lời cuối. |
| **Generate downstream** | Team LangGraph tự sinh câu trả lời (hiện test bằng **Ollama local**). API RAG **không** cung cấp LLM endpoint. |
| **Phù hợp kiến trúc** | **Có** — tách retrieve / generate đúng hướng evidence RAG. |
| **Stack API staging (Phase 1)** | OpenAI `text-embedding-3-small` + hybrid dense/BM25 + **Qdrant** — **rerank tắt**, **không dùng GPU**. |
| **Công cụ API** | **FastAPI + Uvicorn** (open source, Swagger tại `/docs`). |
| **`company_id`** | Slug lowercase theo registry RAG (MVP: `musinsa`, `rayshion`, `hanssem`). |
| **Ingest Phase 1** | RAG **pre-index** package Dataset; LangGraph chỉ gọi `/retrieve`. |
| **Staging URL** | Mạng nội bộ / VPN — chưa cần public internet. |

---

## 2. Stack API staging (Phase 1)

| Layer | Công nghệ | Ghi chú |
|-------|-----------|---------|
| Corpus | `05_company_export_json` — package jsonl (Dataset team) | Contract v1.1 |
| Chunking | `section_based` 800/120 | |
| Embed | `openai:text-embedding-3-small` | OpenAI API — **không GPU** |
| Vector + lexical | Qdrant + BM25 hybrid | Chạy **CPU** |
| Rerank | **Tắt** (`reranker: none`) | Có thể bật ở phase sau nếu hai bên cần |
| Generative | **Không** — LangGraph dùng **Ollama** | Ngoài scope API |

---

## 3. Map spec LangGraph ↔ API staging

### 3.1 `POST /retrieve` — khớp

- `query`, `top_k` → hybrid search, sort giảm dần theo `score` (dense + BM25, **không** rerank).
- `text`, `source`, `score` từ chunk đã ingest — endpoint **không** gọi LLM → **không hallucinate** trên `/retrieve`.
- `company_id` — slug lowercase (vd. `musinsa`); RAG tra registry trước khi search.
- `year` — **filter cứng** khi client truyền: không có evidence đúng năm → `items: []`, **không** fallback sang năm khác.
- Query vi/en/mixed **chấp nhận** cho staging; corpus chủ yếu **tiếng Hàn** — ghi giới hạn trong integration log.

### 3.2 `POST /retrieve` — Phase 1

| Field / behavior | Thống nhất |
|------------------|------------|
| `company_id` | Slug lowercase; registry `company_id` → package/index đã load |
| `year` | Filter cứng trên metadata record; không fallback |
| `filters.evidence_type` | Enum LangGraph → map Dataset theo §5 |
| `filters.taxonomy_item_id` | Phase 2 |
| `filters.language` | Sau khi enrich metadata ingest |
| `page` | Trả từ payload index lúc ingest |
| `metric_name`, `value`, `unit` | Chỉ khi record có `metric` — **không** LLM điền |
| `confidence` | Rule-based Phase 1 (xem §5.1) |

### 3.3 HTTP — empty / missing company

| Tình huống | HTTP | Response |
|------------|------|----------|
| `company_id` có trong registry, không có evidence (hoặc không khớp `year`/filter) | **200** | `items: []` |
| `company_id` **chưa** có trong registry/index | **404** | `{"error": "company_not_indexed", "company_id": "<id>"}` |

### 3.4 `POST /ingest`

| Mục | Phase 1 |
|-----|---------|
| Luồng chính | RAG **pre-index** package Dataset — LangGraph **không** gọi trong MVP |
| `/ingest` | Giữ cho async/admin; align `data_contract_dataset_team_v1_1.md` |
| Upload PDF | **Không** — package jsonl hoặc chunks JSON |
| Thời gian | **Async** (job id) khi dùng `/ingest` |

### 3.5 `GET /companies`

Không cần API key — danh sách `company_id` trong registry + `indexed: true/false`.

```json
{
  "items": [
    { "company_id": "musinsa", "indexed": true, "record_split": "full", "legacy_cache_only": false }
  ],
  "count": 4,
  "indexed_count": 4
}
```

Registry staging (2026-06-08): **`musinsa`, `rayshion`, `hanssem`** (MVP) · `nexteye` (legacy cache — không dùng tích hợp mới).

### 3.6 `GET /health`

```json
{
  "status": "ok",
  "mode": "langgraph_staging",
  "rerank_enabled": false,
  "gpu": false,
  "index_version": "optional"
}
```

---

## 4. LangGraph + Ollama (phía các bạn)

Luồng tích hợp:

```text
1. LangGraph gọi POST /retrieve  →  items[] (evidence)
2. LangGraph ghép context từ items[].text
3. LangGraph gọi Ollama local    →  câu trả lời + cite source/page từ items
```

- RAG **không** phụ thuộc model Ollama — model có thể thay đổi; ghi model thực tế trong integration log.
- RAG chỉ cam kết **items** đúng schema và đúng `company_id`/index — **không** chịu trách nhiệm chất lượng câu trả lời phía Ollama.
- Đánh giá integration: tách **retrieval OK** vs **generation OK**.

---

## 5. Map `evidence_type` (đã thống nhất)

LangGraph giữ enum: `metric`, `policy`, `strategy`, `risk`, `text`. RAG map sang metadata Dataset:

| `evidence_type` (LangGraph) | Nguồn dữ liệu RAG |
|-----------------------------|-------------------|
| `metric` | Record có `metric` hoặc tags emissions/climate |
| `policy` | `source_type` = policy / governance_report |
| `strategy` | `section_path` / tags chiến lược |
| `risk` | governance / risk tags |
| `text` | Mặc định — raw evidence |

### 5.1 `confidence` — rule-based Phase 1

Chấp nhận rule-based, **không** ML/reranker. Gợi ý tín hiệu kết hợp:

| Tín hiệu | Ảnh hưởng |
|----------|-----------|
| `score` (hybrid retrieval) | Cơ sở chính |
| Có `page` / `section_path` | Tăng confidence |
| Có `metric` structured (`name`, `value`, `unit`) | Tăng confidence |
| `is_raw_text=true` | Tăng nhẹ (evidence gốc) |
| `source_type` đáng tin cậy (policy, report, …) | Tăng confidence |

---

## 6. Phase giao hàng API

### Phase 1 — MVP staging

- [x] `GET /health` (`rerank_enabled: false`)
- [x] `POST /retrieve` — schema LangGraph + registry `company_id` + filter `year` cứng
- [x] Pre-index package Dataset (`musinsa`, `rayshion`, `hanssem`); LangGraph chỉ `/retrieve`
- [x] `/ingest` async (admin — không bắt buộc LangGraph MVP)
- [x] OpenAPI `/docs` + example request/response — xem `docs/LANGGRAPH_API_HANDOFF.md`
- [ ] API key + base URL staging (mạng nội bộ / VPN) — cung cấp khi server chạy 24/7
- [ ] Test cases integration phía LangGraph (checklist trong handoff)
- [ ] Integration log: ghi giới hạn corpus KO + model Ollama thực tế
- [ ] Timeout: **30s** `/retrieve`; ingest async **300s+**
- [ ] `max top_k`: **32** (spec LangGraph `8` OK)

### Phase 2 (sau khi tích hợp ổn)

- [ ] Rerank (tuỳ chọn)
- [ ] Multi-company mở rộng registry
- [ ] `taxonomy_item_id`, PDF ingest, rate limit

---

## 7. Vận hành & SLA (staging)

| Mục | Thống nhất |
|-----|------------|
| **Auth** | `X-API-Key` (header) |
| **Base URL** | Mạng nội bộ / VPN — cung cấp sau deploy |
| **Hạ tầng** | CPU + OpenAI embed; **không GPU** phase 1 |
| **Timeout client** | 30s `/retrieve` |
| **Rate limit** | Thỏa thuận (vd. 60 req/phút staging) |
| **Empty evidence** | HTTP 200 + `items: []` |
| **Company chưa index** | HTTP 404 + `company_not_indexed` |
| **Chi phí OSS** | FastAPI/Uvicorn/Qdrant client — miễn phí |
| **Chi phí vận hành** | OpenAI embed (theo token) |

---

## 8. Thống nhất từ phản hồi LangGraph

| # | Chủ đề | Thống nhất |
|---|--------|------------|
| 1 | **`company_id`** | Slug lowercase theo registry RAG. MVP: `musinsa`, `rayshion`, `hanssem`. |
| 2 | **`year`** | Filter **cứng** khi client truyền; không evidence đúng năm → empty, **không** fallback năm khác. |
| 3 | **`evidence_type`** | Enum LangGraph: `metric`, `policy`, `strategy`, `risk`, `text` — RAG map theo §5. |
| 4 | **`confidence`** | Rule-based Phase 1; tín hiệu: score, page/section_path, metric structured, `is_raw_text`, source type (§5.1). |
| 5 | **Query vi/en + corpus KO** | Chấp nhận staging; LangGraph test vi/en; ghi giới hạn corpus KO + embedding multilingual trong integration log. |
| 6 | **Ingest** | Phase 1: RAG pre-index; LangGraph chỉ `/retrieve`. `/ingest` async/admin — chưa bắt buộc MVP. |
| 7 | **Staging URL** | Nội bộ / VPN; chưa cần public internet. |
| 8 | **Empty / missing company** | Có index, không evidence → **200** + `items: []`; chưa index → **404** + `company_not_indexed`. |
| 9 | **Ollama** | Local Ollama phía LangGraph; model tùy chọn — ghi trong integration log, RAG không phụ thuộc. |

---

## 9. Cam kết phía RAG

1. Triển khai **FastAPI staging**: hybrid + Qdrant, **rerank tắt**, **không GPU**.  
2. Pre-index package Dataset; expose `/retrieve` theo contract §3.  
3. **Không** host LLM — LangGraph tự generate (Ollama).  
4. Cung cấp OpenAPI, examples, checklist test integration + template integration log.

### 9.1 Scaffold API (repo)

| Thành phần | Path |
|------------|------|
| Config staging (tách C2/H200) | `configs/langgraph_staging.yaml` |
| FastAPI app | `src/evidence_api/app.py` |
| Pre-index | `python scripts/prebuild_langgraph_staging_index.py` |
| Chạy server | `python scripts/run_langgraph_evidence_api.py --port 8787` |
| Swagger | `http://127.0.0.1:8787/docs` |

Env tuỳ chọn: `LANGGRAPH_API_KEY`, `LANGGRAPH_STAGING_CONFIG`, `OPENAI_API_KEY`.

---

## 10. Tài liệu tham chiếu

| File | Nội dung |
|------|----------|
| `data_contract_dataset_team_v1_1.md` | Schema record / metric / page |

---

*Rev.5 — Handoff 3 công ty MVP; xem `docs/LANGGRAPH_API_HANDOFF.md`.*
