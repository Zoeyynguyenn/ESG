# Model Candidate Benchmark Summary

## Tra loi nhanh

1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`
2. BGE-M3 chay thanh cong: **True**
3. multilingual-e5 chay thanh cong: **False**
4. Config tot nhat: `p1_rec800_minilm_dense_chroma` (composite=0.765)
5. Hybrid vs dense: xem bang duoi (retrieval_hit 1.0000-1.0000)
6. Reranker: so `*_rerank` vs `*_none`
7. Qdrant: blocked (khong implement trong backbone V6)
8. RAGAS: chi top configs, max questions tu env

## Bang ket qua

| rank | config_id | status | hit | cit | composite | latency | index_build |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `p1_rec800_minilm_dense_chroma` | success | 1.0 | 1.0 | 0.765 | 26.859 | 16.815 |
| 2 | `p1_rec512_minilm_dense_chroma` | success | 1.0 | 1.0 | 0.7644 | 29.092 | 18.586 |
| 3 | `p1_section_minilm_dense_chroma` | success | 1.0 | 1.0 | 0.7644 | 29.109 | 18.663 |
| 4 | `p1_rec512_minilm_hybrid_chroma` | success | 1.0 | 1.0 | 0.7641 | 30.19 | 19.865 |
| 5 | `p1_section_minilm_hybrid_chroma` | success | 1.0 | 1.0 | 0.764 | 30.807 | 19.074 |
| 6 | `p1_rec800_minilm_hybrid_chroma` | success | 1.0 | 1.0 | 0.7638 | 31.558 | 20.144 |
| 7 | `p1_rec512_e5_dense_chroma` | success | 1.0 | 1.0 | 0.7432 | 109.701 | 80.207 |
| 8 | `p1_rec800_e5_dense_chroma` | success | 1.0 | 1.0 | 0.7421 | 113.873 | 82.599 |
| 9 | `p1_section_e5_dense_chroma` | success | 1.0 | 1.0 | 0.7409 | 118.4 | 88.785 |
| 10 | `p1_rec800_e5_hybrid_chroma` | success | 1.0 | 1.0 | 0.7361 | 108.172 | 78.563 |
| 11 | `p1_section_e5_hybrid_chroma` | success | 1.0 | 1.0 | 0.7358 | 109.357 | 79.011 |
| 12 | `p1_rec512_e5_hybrid_chroma` | success | 1.0 | 1.0 | 0.7342 | 115.534 | 85.604 |
| 13 | `p1_section_bge_hybrid_chroma` | success | 1.0 | 1.0 | 0.6916 | 334.9 | 287.157 |
| 14 | `p1_rec512_bge_hybrid_chroma` | success | 1.0 | 1.0 | 0.6862 | 355.32 | 306.854 |
| 15 | `p1_rec800_bge_dense_chroma` | success | 1.0 | 1.0 | 0.6852 | 359.246 | 311.71 |
| 16 | `p1_section_bge_dense_chroma` | success | 1.0 | 1.0 | 0.68 | 378.889 | 330.517 |
| 17 | `p1_rec512_bge_dense_chroma` | success | 1.0 | 1.0 | 0.6728 | 406.196 | 354.398 |
| 18 | `p1_rec800_bge_hybrid_chroma` | success | 1.0 | 1.0 | 0.6725 | 407.464 | 356.197 |
