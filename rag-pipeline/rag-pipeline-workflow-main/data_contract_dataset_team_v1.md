# Data Contract Dataset Team v1

## 1) Mục tiêu
Chuẩn hóa đầu ra dữ liệu từ team Dataset để team RAG Pipeline có thể:
1. Ingest ổn định.
2. Benchmark công bằng giữa các cấu hình.
3. Truy vết bằng chứng (evidence) rõ ràng.

## 2) Phạm vi áp dụng
Áp dụng cho mọi gói dữ liệu ESG bàn giao cho `rag-pipeline-workflow`, gồm:
1. Dữ liệu công khai (public reports, policy, annual/sustainability report).
2. Dữ liệu tổng hợp nội bộ (export JSON/JSONL).

## 3) Định dạng bàn giao bắt buộc
1. Encoding: `UTF-8`.
2. Định dạng chính: ưu tiên `JSONL` (1 record/line) hoặc `JSON` schema cố định.
3. Tên file: không chứa ký tự control, không dùng file tạm (`._*`, `*.tmp`).
4. Có `manifest` đi kèm mô tả đầy đủ lô dữ liệu.

## 4) Schema tối thiểu cho mỗi record
Các trường bắt buộc:
1. `doc_id`: định danh duy nhất toàn cục.
2. `company`: tên công ty chuẩn hóa.
3. `year`: năm tài liệu/sự kiện.
4. `source_type`: ví dụ `annual_report`, `sustainability_report`, `policy`, `news`.
5. `language`: `vi`, `en`, `ko`, ...
6. `source_url`: URL nguồn gốc.
7. `published_at`: thời điểm phát hành (nếu có).
8. `ingested_at`: thời điểm thu thập.
9. `title`: tiêu đề tài liệu.
10. `section_path`: đường dẫn section (ví dụ `E/Climate/Targets`).
11. `text`: nội dung thô để retrieval.

Khuyến nghị thêm:
1. `page`: số trang (nếu từ PDF).
2. `evidence_span_start`, `evidence_span_end`: vị trí đoạn bằng chứng trong `text`.
3. `unit`, `value_raw`, `value_normalized`: cho dữ liệu định lượng.
4. `tags`: danh mục ESG, chủ đề, mức ưu tiên.

## 5) Yêu cầu Evidence Traceability
1. Không chỉ gửi summary; bắt buộc có `text` thô truy vết được.
2. Mỗi thông tin tổng hợp phải có link ngược về nguồn:
   - `source_url`
   - `page` hoặc `section_path`
   - `doc_id`
3. Nếu record là derived/synthesized, thêm:
   - `derived_from_doc_ids`: danh sách tài liệu nguồn.

## 6) Chuẩn hóa dữ liệu ESG định lượng
1. Mỗi metric cần tách `value` và `unit`.
2. Không trộn nhiều nghĩa vào 1 field:
   - Ví dụ tách rõ `water_reuse_rate` và `wastewater_treatment_rate`.
3. Nếu có baseline year, thêm:
   - `baseline_year`
   - `target_year`
4. Nếu là tỷ lệ %, lưu cả giá trị số (`15`) và unit (`%`), tránh lưu chuỗi mơ hồ.

## 7) Tách lane dữ liệu để benchmark
Bắt buộc bàn giao theo lane:
1. `public_raw_lane`: tài liệu thô (pdf/html/md/json raw).
2. `dataset_export_lane`: dữ liệu tổng hợp (json/jsonl đã curate).

Không trộn lane khi chấm benchmark chính.

## 8) Manifest bắt buộc cho mỗi đợt bàn giao
File `manifest.json` hoặc `manifest.csv` phải có:
1. `dataset_version`
2. `exported_at`
3. `record_count`
4. `document_count`
5. `company_count`
6. `source_count`
7. `schema_version`
8. `checksum` (ít nhất SHA256 theo file)
9. `changelog` (thêm/sửa/xóa gì so với bản trước)

## 9) Tiêu chí chất lượng dữ liệu đầu vào
1. Trùng lặp `doc_id`: 0%.
2. Missing field bắt buộc: < 1%.
3. `source_url` hợp lệ: >= 95% record.
4. `text` không rỗng: >= 98% record.
5. Record có `page` hoặc `section_path`: >= 90% (nếu có thể).

## 10) Gói bàn giao tối thiểu mỗi lần
1. `dataset/` (dữ liệu chính theo lane).
2. `manifest` (version + thống kê + checksum).
3. `schema` (mô tả field, type, enum, ví dụ).
4. `known_issues.md` (lỗi OCR, thiếu trang, nguồn chết, field khó map).
5. `sample_20_records.jsonl` đã validate thủ công.

## 11) Quy trình phối hợp Team Dataset -> Team RAG
1. Team Dataset bàn giao bản `vX`.
2. Team RAG chạy smoke ingest + retrieval benchmark lane mới.
3. Team RAG phản hồi lỗi mapping/traceability.
4. Team Dataset sửa và phát hành `vX+1` với changelog rõ.

## 12) Definition of Ready (DoR) trước khi Team RAG nhận benchmark chính
Lô dữ liệu được coi là “ready” khi:
1. Đủ schema bắt buộc.
2. Có manifest + checksum.
3. Pass smoke ingest không crash.
4. Có evidence traceability ở mức `doc_id + source_url + section/page`.
5. Không còn lỗi blocker trong `known_issues`.

