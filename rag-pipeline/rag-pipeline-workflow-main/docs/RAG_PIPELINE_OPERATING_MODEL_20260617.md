# RAG Pipeline Operating Model

Ngay cap nhat: 2026-06-17

## 1. Nhan dinh ve mo ta 3 team

Mo ta hien tai la **dung huong**, nhung can siet lai contract giua 3 team de tranh tron vai tro.

### Team Dataset

Team Dataset nen chiu trach nhiem 3 artifact rieng:

1. `question_set`: 252 cau hoi/chieu danh gia.
2. `gold_answer_set`: dap an da duoc chuyen gia xac nhan.
3. `source_registry`: danh sach `Source URL` va metadata tai lieu da dung de tra loi.

### Team RAG Pipeline

Team RAG khong nen nhan dau vao o dang "chi co mot file Excel tong hop" roi tu suy luan phan nao la gold, phan nao la source, phan nao la metadata.

Team RAG nen co workflow ro:

1. Nap `question_set`.
2. Deduplicate `Source URL`.
3. Crawl/download tai lieu.
4. Chunk/index.
5. Retrieve/generate.
6. So ket qua voi `gold_answer_set`.
7. Xuat workbook eval va JSON handoff.

### Team LangGraph

Team LangGraph khong nen tham gia cham do dung/sai cua retrieval.

Team LangGraph nen nhan:

1. `answer`
2. `evidence`
3. `citation`
4. `retrieval_confidence`
5. `abstain_recommended`

Va chi lo trinh bay theo template.

## 2. Diem can cai thien trong mo ta hien tai

### 2.1. Tach "ground truth" khoi "source to crawl"

Mot dong Excel hien dang vua chua cau hoi, vua chua dap an, vua chua `Source URL`.
Dieu nay dung cho con nguoi doc, nhung chua du tot cho pipeline.

Can tach logic:

1. `gold_answer` la chuan cham.
2. `source_url` la input crawl.
3. `source_span` la bang chung mong doi neu da co.

### 2.2. Khong dung moi "answer text exact match" lam metric chinh

Voi ESG, can cham it nhat 4 lop:

1. `retrieval_hit`
2. `citation_correct`
3. `answer_correct`
4. `abstain_correct`

Neu chi cham exact answer string, pipeline se bi phat oan o cac cau paraphrase.

### 2.3. Can co cot phan loai question

252 cau hoi nen co them:

1. `question_type`: `quantitative | qualitative | yes_no | list | date`
2. `normalization_rule`
3. `expected_answer_language`
4. `requires_abstain_when_missing`

Neu khong co 4 cot nay, team RAG se phai hardcode logic cham diem trong code.

### 2.4. Can co provenance tot hon cho team RAG

Neu Excel chi co `Source URL` ma khong co:

1. `doc_title`
2. `page_or_section`
3. `source_type`
4. `published_at`

thi chi phi crawl/audit se cao hon nhieu.

## 3. De xuat contract du lieu tot hon

Excel van co the la artifact nghiep vu chinh, nhung nen convert sang 3 bang canonical.

### Bang 1: `questions`

Cot toi thieu:

1. `question_id`
2. `company_name`
3. `question_text`
4. `question_type`
5. `metric_name`
6. `expected_answer_language`
7. `requires_abstain_when_missing`

### Bang 2: `gold_answers`

Cot toi thieu:

1. `question_id`
2. `gold_answer_raw`
3. `gold_answer_normalized`
4. `expert_verified`
5. `normalization_rule`
6. `scoring_rule`

### Bang 3: `sources`

Cot toi thieu:

1. `question_id`
2. `source_url`
3. `doc_title`
4. `source_type`
5. `page_or_section`
6. `source_priority`
7. `crawl_allowed`

## 4. Luong repo nen bam theo

### Input boundary

1. Team Dataset ban giao Excel + file convert canonical.
2. Team RAG chi nhan `source_url` da duoc whitelist hoac duoc xac nhan hop le.

### RAG boundary

1. Crawl/download
2. Parsing/chunking
3. Index/retrieve/rerank
4. Generation hoac extractive answer
5. Eval voi gold

### Output boundary

1. Workbook cham diem theo tung cau
2. JSON ket qua co evidence
3. Reliability flags cho LangGraph

## 5. Danh gia repo hien tai

Repo hien tai co 3 cum chinh:

1. `golden_set`
2. `company_export_json` benchmark/eval
3. `evidence_api` handoff cho LangGraph

Phan **phu hop** voi bai toan hien tai:

1. `data_contract_dataset_team_v1*.md`
2. `src/retrieval_v3.py`, `src/rag_stack.py`, `src/rag_common.py`
3. `src/evidence_api/*`
4. `scripts` lien quan `exportjson`, `golden_set`, `langgraph`

Phan **thua hoac lech scope** so voi workflow hien tai:

1. benchmark GPU `RunPod/C2/H200`
2. script dong goi pod
3. config production/archive cho GPU runtime cu
4. README entrypoint cu huong ve C2

## 6. Cleanup da chot cho repo

### Giu lai

1. Luong `Dataset -> RAG -> LangGraph`
2. `golden_set`
3. `evidence_api`
4. `production_openai_*`

### Loai khoi entry flow

1. `RunPod/C2/H200`
2. `.env.c2` loading path
3. config/script pod benchmark da archive

## 7. Khuyen nghi tiep theo

1. Them mot script intake tu Excel sang `questions/gold_answers/sources`.
2. Them validator cho workbook 252 cau truoc khi crawl.
3. Them runner eval theo `question_id` thay vi theo package summary.
4. Giu LangGraph o vai tro presentation, khong de team nay danh gia retrieval quality.
