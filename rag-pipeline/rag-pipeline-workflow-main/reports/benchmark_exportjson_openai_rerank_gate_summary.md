# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `openai_hybrid_qdrant_none_gate` (composite=0.805)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 1.0000-1.0000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `openai_hybrid_qdrant_none_gate` | success | 1.0 | 1.0 | 0.805 | 33.426 | 0.0 |
| 2 | `openai_hybrid_qdrant_jina_gate` | success | 1.0 | 1.0 | 0.755 | 42.21 | 0.0 |
