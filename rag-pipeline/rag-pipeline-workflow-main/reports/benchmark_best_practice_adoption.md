# Benchmark Best Practice Adoption (tu ai-gemma4)

Ngay: 2026-05-27  
Tham chieu: `E:\Documents\RAG-clone\ai-gemma4` (chi pattern, khong copy stack).

## Da ap dung vao rag-pipeline-workflow

| Pattern ai-gemma4 | Ap dung | File |
|---|---|---|
| Metadata per case (timing, config, failure) | `started_at`, `ended_at`, `ingest_status`, `resume_action`, `latency` | `run_benchmark_case.py`, CSV schema |
| Error taxonomy ro | `error_code` chuan + `error_reason` chi tiet | `benchmark_utils.py`, CSV |
| Retrieval audit | `retrieval_mode`, `retrieval_hit_rate`, `citation_correctness` trong CSV/dashboard | `run_benchmark_matrix.py` |
| Resume / khong ghi de mu quang | Archive CSV + skip `success` theo key | `benchmark_utils.py`, `run_benchmark_matrix.py` |
| Timeout per case | `subprocess` timeout `--case-timeout-sec` (mac dinh 1200) | `run_benchmark_matrix.py` |
| RAGAS co chinh sach lane | stagewise skipped; focused/final `--enable-ragas` | `run_benchmark_case.py` |

## Khong ap dung (co ly do)

| Thanh phan ai-gemma4 | Ly do |
|---|---|
| Qdrant + hybrid RRF | Doi vector DB — refactor lon; giu Chroma |
| FlagEmbedding BGEM3FlagModel | Trung `sentence-transformers` cho bge-m3; dependency nang |
| Streamlit QA UI | Ngoai scope benchmark runner |
| MLX / Gemma fused | Stack Apple/Gemma khac; Windows + V6 ESG |
| ACL / audit append-only enterprise | Vuot scope practice benchmark |

## Ghi chu RAGAS (tu eval_ragas.py)

- ai-gemma4: RAGAS judge can `OPENAI_API_KEY`; script `eval` / `ab` / `latency` tach biet.
- Repo hien tai: RAGAS **chua tich hop day du** — co key van `ragas_not_integrated_in_this_run` cho den khi implement o focused/final.

## Buoc sau (tuy chon)

1. Subset RAGAS tren 10–20 cau validation (khong full 80) khi bat `--enable-ragas`.
2. Them cot `retrieval_top_sources` (JSON ngan) neu can debug hybrid — hoc tu retriever audit emit.
