# Ticket P1-J06 — Generative manifest lane_policy

**Trang thai:** open  
**Uu tien:** P1 follow-up (khong block freeze)  
**Tao:** 2026-05-29

## Van de

CE-J06 (`Export type cua bo du lieu nay la gi?`) — retrieval + extractive **pass**, generative tra `Khong du du lieu trong context.` du top source la `manifest.json` chua `lane_policy.primary_benchmark_lane: raw_public_first`.

## Pham vi

- Chi answer layer generative (GPT-4o-mini)
- Khong doi retrieval stack da freeze
- Khong mo lai full benchmark matrix

## Huong xu ly de xuat

1. Prompt template rieng cho cau manifest/JSON structured (`lane_policy`, `dataset_version`, `exported_at`)
2. Hoac pre-parse manifest chunk truoc khi dua vao LLM (structured field hint)
3. Rerun targeted 3-5 cau: J06, J07, J08 (optional)

## Lenh verify sau fix

```powershell
cd E:\Documents\rag-pipeline-workflow
$env:RAG_BENCHMARK_LLM_PROVIDER='openai_api'
python scripts/p0_1_verify_ce_j03_j07.py
python scripts/run_production_smoke_ci.py
```

## Tieu chi dong ticket

- CE-J06 generative tra `raw_public_first` (hoac alias trong `EXTRACTED_FIELD_ALIASES`)
- Smoke CI van pass (J06 da waive answer; ticket dong khi generative pass de nang answer_correctness)
