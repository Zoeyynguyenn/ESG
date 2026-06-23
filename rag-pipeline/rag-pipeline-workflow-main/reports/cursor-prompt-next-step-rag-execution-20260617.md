Bạn đang tiếp tục workstream trong repo:

- Workspace: `E:\Documents\rag-pipeline-workflow`
- Ngôn ngữ note/workflow: tiếng Việt

Trước khi làm gì, hãy đọc state file-backed:

1. `.rag/current_plan`
2. `.rag/rag-pipeline-practice/plan.md`
3. `.rag/rag-pipeline-practice/progress.md`
4. `.rag/rag-pipeline-practice/findings.md`
5. `.rag/rag-pipeline-practice/decisions.md`
6. `.rag/rag-pipeline-practice/experiment_log.md`
7. `.rag/rag-pipeline-practice/eval_set.md`

## Bối cảnh hiện tại

Team Dataset đã bàn giao:

- `C:\Users\nguye\Downloads\data-company\dataset-excel\골드앤에스_Final_ESG_Data.xlsx`
- `C:\Users\nguye\Downloads\data-company\dataset-excel\이엠앤아이_Final_ESG_Data.xlsx`

và thêm local JSON/DART package trong `dataset-excel/output_restart_*`.

Team RAG đã hoàn tất các bước chuẩn bị dữ liệu:

### Eval-ready

- `goldns`: `24 answerable`, `227 abstain`, `0 needs_review`
- `emni`: `43 answerable`, `236 abstain`, `0 needs_review`

### Source intake

- `data/source_intake_prep/20260617_goldns_emni/`
- tổng unique source: `18`
- `crawl_web`: `4`
- `resolve_local_file_first`: `14`

### Web raw source

- `data/source_raw/20260617_goldns_emni/`
- web download trước đó: `8/9 ok`
- FTC redirect-loop vẫn backlog

### Local raw source

- `data/source_raw/20260617_goldns_emni_local/`
- local collect mới nhất: `14/14 ok`

Script đã có:

- `scripts/ingest_esg_excel_workbook.py`
- `scripts/reconcile_dataset_excel_local_sources.py`
- `scripts/validate_partition_esg_intake.py`
- `scripts/prepare_source_intake_from_registry.py`
- `scripts/download_sources_from_manifest.py`
- `scripts/collect_local_sources_from_manifest.py`

## Nhận định

Hướng hiện tại là đúng. Có thể tiến hành quy trình RAG luôn.

Mục tiêu tiếp theo là đi hết chuỗi:

`raw source -> chunk/index -> retrieve -> answer/abstain -> compare với gold -> report metrics/score`

## Việc cần Cursor thực hiện

### 1. Khảo sát code hiện có để tái sử dụng tối đa

Đọc kỹ các file liên quan đến ingest/chunk/index/retrieval/eval trong repo trước khi sửa:

- `src/rag_common.py`
- `src/rag_stack.py`
- `src/retrieval_v3.py`
- `src/run_benchmark_case.py`
- mọi script/reports có liên quan đến `source_raw`, `corpus`, `benchmark`, `eval runner`

### 2. Xây bước corpus build cho workstream này

Mục tiêu:

- hợp nhất source từ:
  - `data/source_raw/20260617_goldns_emni/`
  - `data/source_raw/20260617_goldns_emni_local/`
- tạo corpus/chunks có metadata rõ:
  - `company_id`
  - `doc_title`
  - `source_url`
  - `file_url`
  - `source_kind`
  - `year` nếu suy ra được

Ưu tiên tạo script mới riêng cho workstream này, ví dụ:

- `scripts/build_goldns_emni_chunked_corpus.py`

hoặc tên khác hợp lý hơn nếu bạn thấy tốt hơn.

### 3. Nối eval runner theo `question_id`

Dùng:

- `data/dataset_excel_eval_ready/20260617_goldns_emni/`

Lấy:

- `answerable_gold`
- `abstain_gold`

Không dùng `needs_review` vì hiện đã về `0`.

### 4. Chạy RAG benchmark đầu tiên

Ít nhất cần có 1 run đầu tiên để tạo số đo thật:

- retrieval
- answer generation hoặc abstain
- compare với gold

### 5. Báo cáo metrics/score

Bắt buộc trả ra tối thiểu:

- `retrieval_hit_rate`
- `answer_accuracy`
- `abstain_accuracy`
- `source_match_rate`
- `overall_score`

Nếu có metric nào chưa tính được thì nói rõ vì sao, không đoán.

## Lưu ý quan trọng

1. `emni-0237` vẫn giữ note semantic audit:
   - provenance đã có
   - nhưng semantic mapping vẫn nên để SME theo dõi
   - không tự khẳng định đúng nghiệp vụ nếu chưa đủ bằng chứng

2. FTC web source bị block không được làm hỏng cả run:
   - có thể skip source đó
   - nhưng phải log rõ trong artifact/report

3. Ưu tiên additive changes:
   - không phá các lane benchmark cũ
   - không overwrite logic production nếu chưa cần

4. Sau khi làm xong phải cập nhật:
   - `.rag/rag-pipeline-practice/progress.md`
   - `.rag/rag-pipeline-practice/findings.md`
   - `.rag/rag-pipeline-practice/decisions.md`
   - `.rag/rag-pipeline-practice/experiment_log.md`
   - `.rag/rag-pipeline-practice/daily_report.md`

## Cách báo cáo lại

Khi hoàn tất, hãy trả ra:

1. Những file đã tạo/sửa
2. Script mới làm gì
3. Đã chạy lệnh nào
4. Output/corpus/artifact nằm ở đâu
5. Metrics và score là gì
6. Còn blocker/risk nào không
7. Có phát hiện semantic nào cần SME audit không
