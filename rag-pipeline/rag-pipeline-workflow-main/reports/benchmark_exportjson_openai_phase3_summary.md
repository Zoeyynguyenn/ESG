# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `p3_openai_section_hybrid_qdrant` (composite=0.7575)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 1.0000-1.0000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `p3_openai_section_hybrid_qdrant` | success | 1.0 | 1.0 | 0.7575 | 33.785 | 13.212 |
| 2 | `p3_openai_section_dense_chroma` | success | 1.0 | 1.0 | 0.7551 | 33.973 | 13.692 |
| 3 | `p3_openai_rec800_hybrid_qdrant` | success | 1.0 | 1.0 | 0.7011 | 34.853 | 14.175 |
| 4 | `p3_openai_section_hybrid_chroma` | success | 1.0 | 1.0 | 0.6983 | 34.905 | 14.629 |
| 5 | `p3_openai_section_dense_qdrant` | success | 1.0 | 1.0 | 0.665 | 35.678 | 15.812 |
| 6 | `p3_openai_rec800_hybrid_chroma` | success | 1.0 | 1.0 | 0.6646 | 35.401 | 15.316 |
