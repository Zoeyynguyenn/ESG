# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `val_openai_section_hybrid_chroma` (composite=0.7725)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 1.0000-1.0000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `val_openai_section_hybrid_chroma` | success | 1.0 | 1.0 | 0.7725 | 34.642 | 13.514 |
| 2 | `val_openai_section_dense_chroma` | success | 1.0 | 1.0 | 0.7635 | 34.767 | 14.103 |
| 3 | `val_openai_rec800_hybrid_chroma` | success | 1.0 | 1.0 | 0.7401 | 36.101 | 15.332 |
| 4 | `val_openai_rec800_dense_chroma` | success | 1.0 | 1.0 | 0.665 | 43.02 | 21.471 |
