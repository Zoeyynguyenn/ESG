# Báo cáo 09: Tổng hợp benchmark và dataset ESG ngày 2026-05-28

## 1. Mục tiêu trong ngày

Ngày 2026-05-28 tập trung vào việc đưa benchmark RAG từ trạng thái chạy thử rộng, dễ timeout, sang một quy trình có kiểm soát hơn trên dataset ESG đã được chuẩn hóa.

Các mục tiêu chính:

1. Rà soát kết quả benchmark qua đêm và xác định vì sao chưa thể chốt model.
2. Bổ sung một số option kỹ thuật cho ingestion/retrieval.
3. Thu hẹp benchmark về một công ty để giảm thời gian chạy.
4. Làm việc với team Dataset để chuẩn hóa lại package theo bài toán ESG response readiness.
5. Nhận package mới và vẽ lại lộ trình test theo 3 pha.

## 2. Benchmark qua đêm

Benchmark model candidate qua đêm đã chạy nhưng chưa đủ tin cậy để dùng làm kết luận cuối.

Các vấn đề gặp phải:

| Vấn đề | Tác động |
|---|---|
| Case bị timeout hoặc bị kill | Không có metric đầy đủ cho toàn bộ matrix |
| Một số case trả `invalid_case_output` | Runner không ghi được kết quả hợp lệ |
| BGE/e5 ingest/index lâu | Dễ vượt timeout nếu chạy lại full matrix |
| Qdrant ban đầu còn bị chặn runtime | Chưa thể so sánh vectorDB công bằng |

Kết luận:

- Không dùng kết quả overnight để chốt model winner.
- Chỉ dùng kết quả overnight để nhận diện bottleneck: timeout, cache, prebuild index, failure taxonomy.
- Cần chạy lại theo batch nhỏ hơn và có checkpoint rõ ràng.

## 3. Bổ sung kỹ thuật trong pipeline

Đã thêm một số option để chuẩn bị cho benchmark ổn định hơn:

| Nhóm | Thay đổi | Trạng thái |
|---|---|---|
| Parser | Thêm `docling` optional để đọc tài liệu phức tạp | Option, chưa làm mặc định |
| Parser mặc định | Giữ `pypdf` cho benchmark ổn định | Dùng cho benchmark nhanh |
| Metadata | Thêm metadata vào chunk/document | Đã tích hợp |
| Retrieval | Thêm metadata-aware retrieval | Option, bật theo lane khi cần |
| Fallback | Nếu metadata filter không có hit thì fallback không filter | Đã thêm để tránh kết quả rỗng |
| VectorDB | Mở đường chạy `qdrant` local | Dùng ở Pha 3, không chạy đại trà |
| Cache | Thêm prebuild index theo embedding/vector store | Dùng để giảm ingest lặp |

Kết luận:

- `docling` và metadata-aware retrieval là option hỗ trợ, không phải kết luận chất lượng.
- Benchmark chính vẫn cần đo bằng matrix có kiểm soát, không kết luận chỉ vì đã thêm option.

## 4. Thu hẹp benchmark về một công ty

Do benchmark trên nhiều công ty/PDF chạy lâu, hướng trong ngày là thu hẹp scope về một công ty trước.

Đã làm:

1. Thêm eval/config cho lane một công ty.
2. Thêm `company_filter` vào runner/prebuild.
3. Tách cache key theo công ty để tránh reuse sai index.
4. Thiết kế phase nhỏ: dense vs hybrid, embedding comparison, rerank, rồi Qdrant.

Kết luận:

- Cách chạy một công ty là phù hợp để debug tốc độ và pipeline.
- Sau khi team Dataset bàn giao package ESG mới, trọng tâm chuyển sang package `05_company_export_json` thay vì tiếp tục mở rộng lane Hyundai-only.

## 5. Dataset: vấn đề đã được xử lý bằng package mới

Ban đầu, package `넥스트아이_dataset_package_20260528T082146` đã đúng format contract v1.1 nhưng còn các điểm cần sửa trong `dataset_team_fix_request_nexteye_20260528.md`.

Các yêu cầu chính trong fix request:

| Yêu cầu | Trạng thái trong package mới |
|---|---|
| Tách `company_evidence`, `requirement_taxonomy`, `ai_extracted_response` | Đã có trong `lanes/` |
| Không trộn summary/AI response với evidence gốc | Đã tách lane |
| Làm rõ vai trò taxonomy/requirement | Đã có lane `requirement_taxonomy` |
| Làm rõ AI extracted response | Đã có lane `ai_extracted_response` |
| Full split nên là raw company evidence | Package mới dùng `full=170`, khớp `company_evidence=170` |
| Có manifest/checksum cho split/lane | Đã có `checksums` và `lane_checksums` |

Package mới đang được ưu tiên:

`data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409`

Thông tin từ manifest:

| Thuộc tính | Giá trị |
|---|---:|
| `dataset_version` | `1.1.1` |
| `schema_version` | `1.1` |
| `record_count` | `270` |
| `document_count` | `262` |
| `company_count` | `1` |
| `source_count` | `92` |
| `dev` | `77` |
| `validation` | `93` |
| `full` | `170` |
| `company_evidence` | `170` |
| `requirement_taxonomy` | `50` |
| `ai_extracted_response` | `50` |

Kết luận:

- Các điểm chính trong fix request đã được phản ánh ở dataset mới.
- Dataset mới đủ điều kiện để chạy smoke benchmark kỹ thuật.
- `source_url=null` được tạm bỏ qua theo quyết định hiện tại; traceability vẫn có thể dựa vào `metadata.source_path`, `source_system`, và lane role trong giai đoạn smoke.

## 6. Lộ trình test với dataset mới

Lộ trình benchmark được thiết kế lại thành 3 pha:

| Pha | Mục tiêu | Cố định | Biến so sánh |
|---|---|---|---|
| Pha 1 | Lọc retrieval config nhanh | `vectorDB=chroma`, `reranker=none` | `chunking`, `embedding`, `retrieval_mode` |
| Pha 2 | Đo tác động reranker | Top retrieval configs từ Pha 1 | `reranker` |
| Pha 3 | Chốt production candidate | Top 2-3 configs | `vectorDB=chroma` vs `qdrant` |

Để tránh lặp lại lỗi chạy quá rộng, bước kế tiếp nên là smoke rút gọn:

| Smoke | Cấu hình |
|---|---|
| Dataset | `넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| VectorDB | `chroma` |
| Reranker | `none` |
| Retrieval mode | `semantic_dense`, `hybrid_dense_bm25` |
| Mục tiêu | Đo thời gian ingest/index/query trước khi mở matrix |

## 7. Trạng thái chạy thực tế

Đã bắt đầu chuẩn bị chạy smoke:

1. Thêm đọc `.jsonl` records trong `src/rag_common.py`.
2. Thêm lọc package `넥스트아이_dataset_package_20260528T091409` trong `src/run_benchmark_case.py`.
3. Tạo config `configs/benchmark_model_candidates_exportjson_smoke.yaml`.
4. Chạy smoke 2 case MiniLM nhưng bị dừng giữa chừng theo yêu cầu chuyển sang làm báo cáo.

Vì vậy:

- Chưa có số liệu runtime cuối cùng cho smoke.
- Chưa chốt được Pha 1.
- Chưa chốt được model/method winner.

## 8. Việc còn mở

| Việc | Lý do |
|---|---|
| Chạy lại smoke rút gọn | Để biết dataset mới chạy nhanh hay chậm |
| Xác nhận loader chỉ đọc đúng split/lane mới | Tránh đọc lẫn package cũ hoặc file export cũ |
| Chạy Pha 1 theo batch nhỏ | Tránh timeout khi thêm BGE/e5 |
| Sau Pha 1 mới bật reranker | Để biết reranker có cải thiện citation thật không |
| Chỉ test Qdrant với top configs | Tránh tốn thời gian cho toàn matrix |

## 9. Khuyến nghị

1. Không chạy lại 18 case một lượt.
2. Chạy smoke MiniLM trước để đo thời gian thật.
3. Nếu smoke ổn, mở Pha 1 theo từng nhóm: chunking trước, retrieval mode sau, embedding nặng sau cùng.
4. BGE/e5 nên chạy với prebuild index hoặc từng case riêng.
5. Qdrant chỉ chạy ở Pha 3 với top 2-3 config.

## 10. Kết luận

Trong ngày 2026-05-28, phần quan trọng nhất đã được xử lý là dataset. Các yêu cầu trong `dataset_team_fix_request_nexteye_20260528.md` đã được phản ánh bằng package mới `넥스트아이_dataset_package_20260528T091409`, với lane evidence/taxonomy/AI response tách rõ.

Benchmark vẫn chưa có kết luận model cuối cùng vì quá trình chạy thực tế còn bị timeout/kill và smoke mới chưa hoàn tất. Bước tiếp theo hợp lý là chạy lại smoke rút gọn trên package mới, sau đó mới mở Pha 1 theo batch nhỏ.
