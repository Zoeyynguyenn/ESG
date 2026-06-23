# Data Contract Dataset Team v1.1 (Send-off)

## 1) Mục tiêu
Chuẩn hóa dữ liệu bàn giao từ team Dataset để team RAG Pipeline có thể:
1. Chạy ingest ổn định.
2. Benchmark model công bằng.
3. Truy vết bằng chứng rõ ràng.

Phạm vi sử dụng: từ thời điểm ban hành tài liệu này, ưu tiên dữ liệu từ team Dataset; các bộ tự curate trước đó chỉ dùng tham chiếu.

## 2) Nguyên tắc bắt buộc
1. Một nguồn sự thật: dữ liệu benchmark chính chỉ lấy từ package theo contract này.
2. Không trộn raw và summary trong cùng lane benchmark.
3. Mọi claim phải truy vết được về nguồn gốc.
4. Mọi bản phát hành phải có version + checksum + changelog.

## 3) Cấu trúc package bàn giao
```text
dataset_package/
  README.md
  manifest.json
  schema.json
  splits/
    dev.jsonl
    validation.jsonl
    full.jsonl
  records/
    <optional_sharded_jsonl_files>
  known_issues.md
```

## 4) Schema record bắt buộc (JSON/JSONL)
Mỗi record phải có các trường sau:
1. `record_id` (string, unique toàn package)
2. `doc_id` (string, unique theo tài liệu)
3. `company` (string)
4. `year` (integer hoặc null)
5. `source_type` (enum: `annual_report`, `sustainability_report`, `policy`, `governance_report`, `news`, `other`)
6. `language` (ISO code, ví dụ `en`, `ko`, `vi`)
7. `source_url` (string URL hoặc null nếu internal source)
8. `published_at` (ISO datetime hoặc null)
9. `ingested_at` (ISO datetime)
10. `title` (string)
11. `section_path` (string hoặc null)
12. `page` (integer hoặc null)
13. `text` (string, raw evidence text, không rỗng)
14. `is_raw_text` (boolean)
15. `is_derived_summary` (boolean)
16. `derived_from_doc_ids` (array[string], bắt buộc nếu `is_derived_summary=true`)
17. `esg_tags` (array[string], ví dụ `E.climate`, `S.labor`, `G.board`)
18. `metadata` (object, optional)

Ràng buộc:
1. `is_raw_text=true` và `is_derived_summary=false` cho lane benchmark chính.
2. Nếu `is_derived_summary=true` thì `derived_from_doc_ids` phải có ít nhất 1 phần tử.
3. `text` tối thiểu 50 ký tự sau khi trim (trừ record loại metadata-only).

## 5) Chuẩn dữ liệu định lượng ESG
Nếu record có số liệu ESG, thêm object `metric`:
```json
{
  "metric_name": "scope_1_2_emissions_intensity",
  "value_raw": "25%",
  "value_normalized": 25.0,
  "unit": "%",
  "baseline_year": 2023,
  "target_year": 2028
}
```

Quy tắc:
1. Không gộp hai metric khác nghĩa vào một field.
2. Bắt buộc tách rõ cặp dễ nhầm:
   - `water_reuse_rate`
   - `wastewater_treatment_rate`

## 6) Manifest bắt buộc (`manifest.json`)
```json
{
  "dataset_name": "company_esg_public_first",
  "dataset_version": "1.1.0",
  "schema_version": "1.1",
  "exported_at": "2026-05-28T00:00:00Z",
  "record_count": 0,
  "document_count": 0,
  "company_count": 0,
  "source_count": 0,
  "benchmark_split": {
    "dev": 0,
    "validation": 0,
    "full": 0
  },
  "lane_policy": {
    "primary_benchmark_lane": "raw_public_first",
    "summary_lane": "derived_summary_only"
  },
  "checksums": [
    {"path": "splits/dev.jsonl", "sha256": "..."}
  ],
  "changelog": [
    "Initial release"
  ]
}
```

## 7) Chia split benchmark (bắt buộc)
1. `dev`: dùng cho vòng lọc nhanh (stagewise/focused sớm).
2. `validation`: dùng chọn top config.
3. `full`: dùng xác nhận cuối.

Quy tắc:
1. Một `record_id` chỉ xuất hiện ở một split.
2. Phân bổ công ty/ngôn ngữ/source_type tương đối cân bằng giữa split.

## 8) Chất lượng dữ liệu tối thiểu (Acceptance Gate)
Package bị từ chối nếu không đạt:
1. Duplicate `record_id`: 0%
2. Duplicate `doc_id` ngoài chủ đích: 0%
3. `text` rỗng: <= 1%
4. Thiếu trường bắt buộc: <= 1%
5. `source_url` hợp lệ hoặc null có lý do: >= 95%
6. Record có `section_path` hoặc `page`: >= 85%
7. Record summary thiếu `derived_from_doc_ids`: 0%

## 9) File `known_issues.md` bắt buộc
Mỗi issue phải có:
1. `issue_id`
2. `severity` (`low`, `medium`, `high`, `blocker`)
3. `scope` (company/doc/split)
4. `description`
5. `mitigation`
6. `eta_fix` (nếu có)

## 10) Quy trình bàn giao / nghiệm thu
1. Team Dataset gửi package + checksum + changelog.
2. Team RAG chạy validator contract.
3. Nếu fail gate: trả checklist lỗi theo field.
4. Nếu pass gate: đưa vào lane benchmark chính.

## 11) SemVer bắt buộc cho dữ liệu
1. `MAJOR` tăng khi đổi schema phá tương thích.
2. `MINOR` tăng khi thêm dữ liệu/field tương thích.
3. `PATCH` tăng khi sửa lỗi dữ liệu không đổi schema.

## 12) Mẫu record tối thiểu
```json
{
  "record_id": "rec_nexteye_000001",
  "doc_id": "doc_nexteye_2025_sr_en",
  "company": "Nexteye",
  "year": 2025,
  "source_type": "sustainability_report",
  "language": "en",
  "source_url": "https://example.com/report.pdf",
  "published_at": "2025-04-30T00:00:00Z",
  "ingested_at": "2026-05-28T09:00:00Z",
  "title": "Sustainability Report 2025",
  "section_path": "E/Climate/Targets",
  "page": 42,
  "text": "We target a 25% reduction in Scope 1+2 emissions intensity by 2028 from 2023 baseline.",
  "is_raw_text": true,
  "is_derived_summary": false,
  "derived_from_doc_ids": [],
  "esg_tags": ["E.climate", "E.emissions"],
  "metadata": {
    "country": "KR"
  }
}
```

---

## Kết luận gửi team Dataset
Đây là chuẩn bàn giao chính thức cho benchmark RAG từ thời điểm hiện tại. Dữ liệu không đạt Acceptance Gate sẽ không đưa vào lane benchmark chính.
