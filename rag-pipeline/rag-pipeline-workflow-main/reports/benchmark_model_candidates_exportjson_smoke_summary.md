# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `smoke_nexteye_minilm_hybrid_chroma` (composite=0.43)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 0.2000-0.2000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `smoke_nexteye_minilm_hybrid_chroma` | success | 0.2 | 0.2 | 0.43 | 27.379 | 19.67 |
| 2 | `smoke_nexteye_minilm_dense_chroma` | success | 0.2 | 0.2 | 0.22 | 29.939 | 21.874 |
