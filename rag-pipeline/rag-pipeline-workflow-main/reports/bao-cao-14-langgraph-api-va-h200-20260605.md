# Báo cáo 14: API LangGraph staging và tìm hiểu H200 / AI Nexus

**Ngày:** 2026-06-05 · **Nối tiếp:** [Báo cáo 13](bao-cao-13-chot-c2-production-git-runpod-20260604.md)  
**Phạm vi:** Công việc trong ngày — tích hợp team LangGraph (retrieval API) và chuẩn bị luồng H200

---

## 1. Tóm tắt

| Hạng mục | Kết quả |
|---|---|
| **LangGraph API** | Scaffold FastAPI staging, thống nhất spec §8, pre-index `nexteye`, smoke PASS |
| **Tách luồng** | API staging (CPU, rerank off) **độc lập** benchmark C2 / H200 |
| **H200 / AI Nexus** | Đang tìm hiểu tài liệu vận hành (5 file); công ty triển khai **Qwen 3.5 122B** |
| **Production C2** | Không đổi — vẫn frozen RunPod; H200 là luồng thí nghiệm / migrate tiếp theo |

---

## 2. Công việc đã làm

### 2.1 Tìm hiểu H200 / kt cloud AI Nexus (5 tài liệu)

Đang rà soát bộ tài liệu hướng dẫn và VoC liên quan môi trường GPU công ty (kt cloud AI Nexus, workflow NIPA, chuyển VM, QnA vận hành). Mục tiêu: nắm khái niệm vận hành (session, NAS, quota, port, idle policy) trước khi map luồng benchmark C2 từ RunPod sang H200.

**Đại ý đang tìm hiểu:**

- AI Nexus là nền tảng GPU (Backend.AI), không phải LLM sẵn có — cần tự deploy hoặc dùng endpoint công ty cung cấp.
- Lưu trữ: vFolder NAS cho code/dataset/model; scratch local giới hạn dung lượng.
- Vận hành session: thường một session, tmux; preopen port phục vụ (vd. vLLM 8000).
- Khác biệt so RunPod: không DinD hai tab; cần checklist account, NAS, quota từ admin.

**Artifact:** extract text `reports/_h200_extract/` · ghi chú nội bộ `docs/H200_AI_NEXUS_C2.md` (draft).

**Tin từ công ty:** đang cài **Qwen 3.5 122B** trên H200 — bước sau cần plan vLLM + benchmark gate C2 với model mới (chưa chạy gate trong ngày).

### 2.2 API Evidence Retrieval cho team LangGraph

1. **Thống nhất kỹ thuật** với team LangGraph (phản hồi §8): `company_id` slug (`nexteye`), filter `year` cứng, enum `evidence_type`, confidence rule-based, pre-index RAG, staging nội bộ/VPN, HTTP 404 `company_not_indexed` vs 200 `items: []`.
2. **Implement staging API** — module `src/evidence_api/`, config `configs/langgraph_staging.yaml` (tách `production_c2_*`).
3. **Pre-index** package Dataset `nexteye` (~630 chunks, hybrid + Qdrant, OpenAI embed, **rerank tắt**, không GPU).
4. **Smoke test** — `/health`, `/retrieve`, 404 company unknown; Swagger `/docs` + Authorize API key.
5. **Handoff** — `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` (rev.4), `docs/LANGGRAPH_API_HANDOFF.md`.
6. **Script vận hành** — `prebuild_langgraph_staging_index.py`, `run_langgraph_evidence_api.py`, `stop_langgraph_evidence_api.ps1`, `open_langgraph_api_firewall.ps1`, `run_langgraph_tunnel.ps1` (tunnel dự phòng khi không cùng LAN).

**Luồng tích hợp LangGraph:** `POST /retrieve` → ghép `items[].text` → **Ollama local** (phía LangGraph) generate; RAG không host LLM.

---

## 3. Kết quả API LangGraph (staging)

| Mục | Trạng thái |
|---|---|
| Stack | OpenAI `text-embedding-3-small` + hybrid BM25/Qdrant, rerank **off**, CPU |
| Company index | `nexteye` |
| Endpoints | `GET /health`, `POST /retrieve`, `POST /ingest` (admin/async) |
| Auth | `X-API-Key` (staging) |
| Test nội bộ | Smoke PASS; server chạy `0.0.0.0:8787` |

**Lưu ý gửi team:** corpus chủ yếu tiếng Hàn; filter `year` chưa có hiệu lực thực tế vì package chưa có metadata `year`. Team remote cần cùng LAN/VPN hoặc Cloudflare tunnel.

---

## 4. Tài liệu / file chính

| File | Mục đích |
|---|---|
| `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` | Spec đã thống nhất với LangGraph |
| `docs/LANGGRAPH_API_HANDOFF.md` | URL, API key, ví dụ test |
| `configs/langgraph_staging.yaml` | Stack staging (không dùng C2) |
| `src/evidence_api/` | FastAPI app + service |
| `docs/H200_AI_NEXUS_C2.md` | Ghi chú luồng H200 (nội bộ) |

---

## 5. Việc tiếp theo

| Luồng | Việc |
|---|---|
| **LangGraph** | Team test integration qua LAN/tunnel; ghi integration log (Ollama model, giới hạn corpus KO) |
| **H200** | Nhận account AI Nexus + NAS; plan vLLM **Qwen 3.5 122B**; map checklist C2 → session H200 |
| **Dataset** | Phối hợp bổ sung `year` trên record nếu cần filter staging |

---

*Báo cáo 14 — công việc ngày 2026-06-05: API LangGraph staging và giai đoạn tìm hiểu H200.*
