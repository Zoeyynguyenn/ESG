# Handoff — LangGraph Evidence API (staging, 3 công ty)

**Ngày:** 2026-06-05 · **Trạng thái:** **ACTIVE** — sẵn sàng tích hợp Phase 1.

**Registry:** 3 công ty chính (`musinsa`, `rayshion`, `hanssem`) · `nexteye` giữ legacy cache (dataset đã gỡ — **không dùng**).

**Smoke test:** `python scripts/smoke_langgraph_evidence_api.py` — PASS (musinsa / rayshion / hanssem trả evidence; nexteye `items: []`).

Spec kỹ thuật đầy đủ: `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md`.

---

## 1. Thông tin kết nối (staging)

| Mục | Giá trị |
|-----|---------|
| **Base URL (máy dev hiện tại)** | `http://192.168.1.5:8787` (LAN — đổi nếu deploy máy khác) |
| **Swagger** | `http://192.168.1.5:8787/docs` |
| **Auth** | Header `X-API-Key` — staging dev: `langgraph-staging-dev` (đổi khi deploy chính thức) |
| **`company_id` dùng trong MVP** | `musinsa` · `rayshion` · `hanssem` |
| **List companies** | `GET /companies` (không cần API key) |
| **Rerank** | Tắt · **GPU** | Không · **LLM** | Không (LangGraph tự generate, vd. Ollama) |

### Map `company_id` ↔ dataset

| `company_id` | Công ty (KO) | Package Dataset | Records (full split) | Index (~chunks) |
|--------------|--------------|-----------------|----------------------|-----------------|
| `musinsa` | 무신사 | `무신사_dataset_package_20260608T092823` | 2160 | ~739 |
| `rayshion` | 레이시온 | `레이시온_dataset_package_20260608T055801` | 1087 | ~739 |
| `hanssem` | 한샘 | `한샘_dataset_package_20260608T042739` | 1161 | ~759 |

> Corpus chủ yếu **tiếng Hàn**. Query tiếng Việt/Anh vẫn chấp nhận staging; ghi giới hạn trong integration log.

> **`nexteye`:** vẫn có trong registry với `legacy_cache_only: true` nhưng package gốc đã xóa khỏi disk → `/retrieve` trả `items: []`. **Không dùng** cho tích hợp mới.

### Không mở được URL?

| Nguyên nhân | Cách xử lý |
|-------------|------------|
| Không cùng WiFi/LAN/VPN | Tunnel: `scripts/run_langgraph_tunnel.ps1` → URL `https://....trycloudflare.com` |
| Windows Firewall chặn | PowerShell **Admin**: `scripts/open_langgraph_api_firewall.ps1` |
| Server chưa chạy | Xem §2 |
| IP đổi (DHCP) | Chạy lại script firewall để xem IP mới |

---

## 2. Chạy server (phía RAG)

```powershell
cd E:\Documents\rag-pipeline-workflow
pip install fastapi "uvicorn[standard]"

# .env cần OPENAI_API_KEY (embed). Tuỳ chọn: LANGGRAPH_API_KEY — xem .env.langgraph.example
python scripts/prebuild_langgraph_staging_index.py
python scripts/run_langgraph_evidence_api.py --host 0.0.0.0 --port 8787
```

Rebuild một công ty sau khi Dataset đổi package:

```powershell
python scripts/prebuild_langgraph_staging_index.py --company musinsa --force
python scripts/prebuild_langgraph_staging_index.py --company rayshion --force
python scripts/prebuild_langgraph_staging_index.py --company hanssem --force
```

Smoke test:

```powershell
python scripts/smoke_langgraph_evidence_api.py
python scripts/smoke_langgraph_evidence_api.py --base-url http://127.0.0.1:8787 --api-key langgraph-staging-dev
```

---

## 3. Ví dụ gọi API (LangGraph)

### Health & danh sách công ty

```http
GET /health
GET /companies
```

### Retrieve — 무신사 (`musinsa`)

```http
POST /retrieve
Content-Type: application/json
X-API-Key: <key>

{
  "query": "ESG 지속가능경영 탄소 배출",
  "company_id": "musinsa",
  "top_k": 8
}
```

### Retrieve — 한샘 (`hanssem`) + filter evidence_type

```http
POST /retrieve
Content-Type: application/json
X-API-Key: <key>

{
  "query": "거버넌스 정책",
  "company_id": "hanssem",
  "top_k": 8,
  "filters": { "evidence_type": "policy" }
}
```

### Retrieve — 레이시온 (`rayshion`)

```json
{
  "query": "sustainability report ESG",
  "company_id": "rayshion",
  "top_k": 8
}
```

Enum `filters.evidence_type`: `metric`, `policy`, `strategy`, `risk`, `text`.

### Filter năm (cứng)

```json
{
  "query": "carbon emissions",
  "company_id": "musinsa",
  "year": 2024,
  "top_k": 8
}
```

Không có evidence đúng năm → `"items": []` (HTTP 200). Metadata `year` trên record có thể null — test filter năm trước khi dùng production.

### Company chưa index

```json
{ "query": "test", "company_id": "unknown_co" }
```

→ HTTP **404** `{ "error": "company_not_indexed", "company_id": "unknown_co" }`

---

## 4. Response mẫu

```json
{
  "company_id": "musinsa",
  "query": "ESG 지속가능경영",
  "items": [
    {
      "text": "...",
      "source": "data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/splits/full.jsonl",
      "score": 1.0,
      "confidence": "high",
      "page": null,
      "section_path": null,
      "metric_name": null,
      "value": null,
      "unit": null,
      "record_id": "rec_8fa64125c8cc553a",
      "evidence_type": "text"
    }
  ]
}
```

`confidence`: rule-based (`low` / `medium` / `high`) — không ML/rerank.

---

## 5. Luồng tích hợp LangGraph

```text
GET /companies  →  chọn company_id (musinsa | rayshion | hanssem)
       ↓
POST /retrieve  →  items[]
       ↓
ghép context từ items[].text (+ cite source / page / record_id)
       ↓
Ollama local (hoặc LLM khác)  →  câu trả lời cuối
```

Ghi trong integration log:

- Model generate thực tế (Ollama / …)
- Giới hạn corpus KO + query vi/en
- `company_id` và ví dụ query đã test

---

## 6. Checklist test tích hợp (team LangGraph)

- [ ] `GET /health` → `status: ok`, `rerank_enabled: false`
- [ ] `GET /companies` → 3 công ty chính `indexed: true`
- [ ] `POST /retrieve` + `musinsa` — có `items` không rỗng
- [ ] `POST /retrieve` + `hanssem` + `filters.evidence_type: policy`
- [ ] `POST /retrieve` + `company_id` không tồn tại → 404
- [ ] Query vi/en trên corpus KO — ghi nhận chất lượng retrieval
- [ ] End-to-end: retrieve → Ollama → citation khớp `items[].source`

---

## 7. Tài liệu & file liên quan

| File | Nội dung |
|------|----------|
| `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` | Spec thống nhất §8 |
| `configs/langgraph_staging.yaml` | Registry + stack staging (tách C2/H200) |
| `.env.langgraph.example` | Biến môi trường tối thiểu |
| `data_contract_dataset_team_v1_1.md` | Schema record Dataset |

---

## 8. Lưu ý vận hành

1. **Tách H200/C2:** API dùng config/index cache riêng (`langgraph_staging`) — không ảnh hưởng benchmark C2.
2. **Env embed:** `OPENAI_API_KEY` trong `.env` / `.env.local` (không dùng key hallmdr từ `.env.c2`).
3. **Chi phí:** OpenAI embed theo token khi build index và mỗi query dense.
4. **Không dùng `nexteye`:** chuyển sang `musinsa` / `rayshion` / `hanssem`.

---

*Gửi kèm `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` + file handoff này cho team LangGraph.*
