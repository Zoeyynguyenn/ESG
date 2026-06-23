# Báo cáo 16: LangGraph API — 3 công ty mới, verify OpenAI, mở rộng endpoint

**Ngày:** 2026-06-08 · **Nối tiếp:** [Báo cáo 14](bao-cao-14-langgraph-api-va-h200-20260605.md)  
**Phạm vi:** Mở rộng staging API cho LangGraph; pre-index & kiểm tra luồng OpenAI (rerank none)

---

## 1. Tóm tắt

| Hạng mục | Kết quả |
|---|---|
| **Dataset staging** | Thêm **3 công ty mới** thay `nexteye` làm test chính; **giữ cache `nexteye`** (legacy) |
| **Registry** | `musinsa`, `rayshion`, `hanssem` + `nexteye` (`legacy_cache_only`) |
| **API mới** | `GET /companies` — danh sách company + trạng thái index |
| **Pre-index** | 3 công ty mới qua OpenAI embed, hybrid Qdrant, **rerank off** — rebuild `--force` PASS |
| **Verify** | `verify_langgraph_openai_flow.py` + smoke PASS — 4/4 indexed |
| **H200** | **Chờ** backend (LLM + rerank GPU); không block LangGraph staging |

---

## 2. Công việc đã làm

### 2.1 Mở rộng registry & cache

| `company_id` | Package Dataset | Ghi chú |
|---|---|---|
| `musinsa` | `무신사_dataset_package_20260608T092823` | Test chính |
| `rayshion` | `레이시온_dataset_package_20260608T055801` | Test chính |
| `hanssem` | `한샘_dataset_package_20260608T042739` | Test chính |
| `nexteye` | `넥스트아이_dataset_package_20260528T091409` | **Legacy** — chỉ dùng cache cũ, không rebuild |

- Config: `configs/langgraph_staging.yaml` (`api_id: langgraph_staging_v2`).
- `nexteye` giữ `corpus_version` cũ để cache index v1 vẫn khớp.
- 3 công ty mới dùng `corpus_version: langgraph_staging_20260608`.

### 2.2 API LangGraph — endpoint bổ sung

| Endpoint | Mục đích | LangGraph MVP |
|---|---|---|
| `GET /companies` | List `company_id` + `indexed` + `legacy_cache_only` | **Có** — discovery, không cần hardcode list |
| `GET /health` | Server + index tổng quan | Có |
| `POST /retrieve` | Retrieval evidence | **Chính** |
| `POST /ingest` | Rebuild index async (admin) | **Không** — RAG pre-index bằng script |

`POST /ingest` = nạp lại Qdrant/BM25 cho một company (giống `prebuild_langgraph_staging_index.py`), không upload PDF, không generate answer.

### 2.3 Pre-index & verify OpenAI (rerank none)

**Lệnh rebuild:**

```powershell
python scripts/prebuild_langgraph_staging_index.py --company musinsa --force
python scripts/prebuild_langgraph_staging_index.py --company rayshion --force
python scripts/prebuild_langgraph_staging_index.py --company hanssem --force
```

**Kết quả index:**

| Company | Chunks | Retrieve spot-check |
|---|---:|---|
| musinsa | 739 | 5 items, có `record_id` — **tốt** |
| rayshion | 739 | 2 items, hay trúng `manifest.json` |
| hanssem | 759 | 2 items, tương tự rayshion |
| nexteye (legacy) | cache cũ | Index OK; query test có thể `items: []` |

**Script kiểm tra:** `scripts/verify_langgraph_openai_flow.py`  
**Smoke:** `scripts/smoke_langgraph_evidence_api.py` — PASS (4/4 indexed, 404 `unknown_co` đúng spec).

### 2.4 Vận hành API cho team LangGraph

- Server: `python scripts/run_langgraph_evidence_api.py --host 0.0.0.0 --port 8787`
- Swagger: `/docs` · List company: `/companies`
- Handoff cập nhật: `docs/LANGGRAPH_API_HANDOFF.md`, spec `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` (§3.5 `/companies`)
- Mạng: LAN / firewall / tunnel (Cloudflare) nếu team remote

---

## 3. Phân luồng (chốt lại)

```text
LangGraph staging (đã làm):
  OpenAI embed + hybrid Qdrant + rerank OFF + CPU
  → POST /retrieve → LangGraph Ollama generate

H200 (chờ sau):
  Backend công ty → test API LLM (Qwen 3.5 122B) + rerank GPU
  → benchmark gate C2 — tách config/index khỏi langgraph_staging
```

---

## 4. Kết quả kỹ thuật

| Kiểm tra | Kết quả |
|---|---|
| OpenAI API key | OK (`openai_api_key_ok`) |
| `rerank_enabled` | `false` |
| `gpu` | `false` |
| `GET /companies` | 4 company, `indexed_count: 4` |
| `POST /retrieve` musinsa | HTTP 200, evidence có `record_id` |
| Company chưa registry | HTTP 404 `company_not_indexed` |

---

## 5. Vấn đề / hạn chế đã ghi nhận

1. **rayshion / hanssem** — retrieval đôi khi ưu tiên metadata `manifest.json` thay vì body evidence; cần xem lại manifest ingest (lane `company_evidence`) ở bước sau.
2. **nexteye legacy** — data package có thể không còn trên disk; chỉ tin cache. LangGraph nên test **3 công ty mới**.
3. **Filter `year`** — package chưa có metadata `year` → filter trả empty (đúng spec).
4. **H200** — chưa test LLM/rerank API; chờ infra công ty.

---

## 6. Việc tiếp theo

| Luồng | Việc |
|---|---|
| **LangGraph** | Test integration 3 company; `GET /companies` → `/retrieve` → Ollama; ghi integration log |
| **RAG staging** | (Tuỳ chọn) chỉnh ingest rayshion/hanssem để hit evidence tốt hơn |
| **H200** | Account AI Nexus + NAS; deploy vLLM Qwen 3.5 122B; test rerank GPU |
| **Dataset** | Bổ sung `year` metadata nếu cần filter staging |

---

## 7. File tham chiếu

| File | Nội dung |
|---|---|
| `configs/langgraph_staging.yaml` | Registry 4 company |
| `scripts/prebuild_langgraph_staging_index.py` | Pre-index |
| `scripts/verify_langgraph_openai_flow.py` | Verify OpenAI + retrieve |
| `scripts/smoke_langgraph_evidence_api.py` | Smoke test |
| `docs/LANGGRAPH_API_HANDOFF.md` | Hướng dẫn gửi LangGraph |

---

*Báo cáo 16 — 2026-06-08: mở rộng LangGraph staging sang 3 công ty mới và xác nhận luồng OpenAI (rerank none).*
