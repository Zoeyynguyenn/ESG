# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **False**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `p3_top1_top3_section_minilm_dense_chroma_none_chroma` (composite=0.2575)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 0.0000-0.0000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `p3_top1_top3_section_minilm_dense_chroma_none_chroma` | success | 0.0 | 0.0 | 0.2575 | 39.734 | 30.278 |
| 2 | `p3_top3_top1_rec800_minilm_dense_chroma_none_chroma` | success | 0.0 | 0.0 | 0.2256 | 43.4 | 32.847 |
| 3 | `p3_top3_top1_rec800_minilm_dense_chroma_none_qdrant` | success | 0.0 | 0.0 | 0.2254 | 43.422 | 33.242 |
| 4 | `p3_top2_top3_top2_rec512_minilm_dense_chroma_none_qdrant` | success | 0.0 | 0.0 | 0.2213 | 43.892 | 33.841 |
| 5 | `p3_top2_top3_top2_rec512_minilm_dense_chroma_none_chroma` | success | 0.0 | 0.0 | 0.2035 | 45.938 | 35.639 |
| 6 | `p3_top1_top3_section_minilm_dense_chroma_none_qdrant` | success | 0.0 | 0.0 | 0.1575 | 51.222 | 40.04 |
