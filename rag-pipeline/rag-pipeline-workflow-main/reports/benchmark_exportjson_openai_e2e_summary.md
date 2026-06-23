# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `e2e_openai_hybrid_qdrant_generative` (composite=0.7533)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 0.8667-0.8667)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `e2e_openai_hybrid_qdrant_generative` | success | 0.8667 | 0.8667 | 0.7533 | 183.648 | 0.0 |
| 2 | `e2e_openai_hybrid_qdrant_extractive` | success | 0.8667 | 0.8667 | 0.74 | 490.663 | 0.0 |
