# Production monitoring — ngưỡng cảnh báo regression

Tham chiếu config: `configs/production_openai_hybrid_qdrant_generative.yaml`

## Smoke CI (5 câu)

| Metric | Ngưỡng tối thiểu / tối đa | Ghi chú |
|---|---|---|
| retrieval_hit_rate | ≥ 1.0 (5/5) | Mọi câu smoke |
| citation_correctness | ≥ 1.0 (5/5) | Mọi câu smoke |
| insufficient_smoke | ≥ 1.0 (J16) | Bắt buộc insufficient_ok |
| answer_correctness | ≥ 0.6 (3/4 scored) | CE-J06 waived (ticket P1-J06) |
| query_time_avg_sec | ≤ 8.0 | Generative full lane |

## Full eval baseline (P0.1 gate)

| Metric | Baseline | Alert nếu giảm |
|---|---:|---|
| generative answer_correct (20q) | 12/20 | < 10/20 |
| retrieval_hit_rate | 1.0 | < 0.95 |
| citation_correctness | 1.0 | < 0.95 |
| insufficient (J16–J20) | 4/5 | < 4/5 |

## Lệnh kiểm tra local

```powershell
python scripts/run_production_smoke_ci.py
```

Artifact: `artifacts/smoke_ci/smoke_ci_*.json`

## CI GitHub Actions

Workflow: `.github/workflows/production-smoke.yml`  
Secret bắt buộc: `OPENAI_API_KEY`
