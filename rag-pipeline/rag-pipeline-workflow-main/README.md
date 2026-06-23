# RAG Pipeline Workflow

Repo nay duoc giu lai de van hanh workflow `Dataset -> RAG Pipeline -> LangGraph` cho bai toan ESG company QA/eval.

## Muc tieu hien tai

1. Nhan bo cau hoi/gold answer tu team Dataset.
2. Crawl va index toan bo tai lieu trong `Source URL`.
3. Chay retrieval/generation va doi chieu voi dap an da duoc chuyen gia xac nhan.
4. Ban giao ket qua co evidence + reliability flags cho team LangGraph.

## Doc truoc khi lam viec

1. `.rag/current_plan`
2. `.rag/rag-pipeline-practice/plan.md`
3. `.rag/rag-pipeline-practice/progress.md`
4. `.rag/rag-pipeline-practice/findings.md`
5. `.rag/rag-pipeline-practice/decisions.md`
6. `.rag/rag-pipeline-practice/experiment_log.md`
7. `.rag/rag-pipeline-practice/eval_set.md`

## Tai lieu chinh

| File | Vai tro |
|---|---|
| `docs/RAG_PIPELINE_OPERATING_MODEL_20260617.md` | Mo hinh van hanh de repo bam dung workflow Dataset -> RAG -> LangGraph |
| `data_contract_dataset_team_v1.md` | Contract du lieu nen tang giua team Dataset va team RAG |
| `data_contract_dataset_team_v1_1.md` | Ban contract mo rong, co split va acceptance gate |
| `docs/LANGGRAPH_SWAGGER_RETRIEVE_HANDBOOK_20260612.md` | Handoff cho team LangGraph khi doc `/retrieve` |
| `data/README.md`, `reports/README.md` | Cau truc du lieu va bao cao |

## Lenh workflow

1. `/rag status`: xem muc tieu hien tai, blocker, next step.
2. `/rag research`: ghi research/findings.
3. `/rag experiment`: ghi va chay thu nghiem.
4. `/rag eval`: cap nhat bo eval va tong hop metric.
5. `/rag report`: tao hoac cap nhat bao cao.
6. `/rag compact`: flush state ra file truoc khi chat dai.

## Pham vi active

Repo hien uu tien:

1. `company_export_json` / input tu team Dataset.
2. `golden_set` va eval workbook de cham dung/sai theo tung cau.
3. `evidence_api` cho handoff retrieval sang LangGraph.

Huong benchmark GPU `RunPod/C2/H200` da duoc loai khoi entry flow va khong con la duong van hanh chinh.

## Luu y ve generated corpus lon

Mot so artifact trong lane `enterprise internal-doc` la file sinh ra tu pipeline va khong can commit vao git:

- `data/enterprise_docs/*/corpus_units_reingested.jsonl`
- `data/enterprise_docs/*/corpus_units_filtered.jsonl`
- `data/enterprise_docs/*/corpus_units_family_scoped.jsonl`
- `data/enterprise_docs/*/corpus_units_overlap_ready.jsonl`

Neu pull repo ve ma chua co cac file nay, repo van chay binh thuong. Chi cac lenh holdout/reingest moi can rebuild artifact truoc khi danh gia:

```bash
python scripts/build_holdout_reingested_corpus.py
python scripts/build_holdout_filtered_corpus.py
```
