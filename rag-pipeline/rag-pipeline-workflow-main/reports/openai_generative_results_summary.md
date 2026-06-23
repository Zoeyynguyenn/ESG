# Tóm tắt kết quả Generative GPT-4o-mini

Tạo lúc: 2026-05-29T12:08:15

| Mục | Giá trị |
|---|---|
| Lane | `company_export_json_full` |
| Embedding | `openai:text-embedding-3-small` |
| Retrieval | hybrid_dense_bm25, pool 64, Qdrant |
| Generative LLM | `gpt-4o-mini` |
| answer_correct (rule) | Extractive **8/20** → Generative **12/20** |

Chi tiết: [openai_generative_results_full.md](openai_generative_results_full.md)

| ID | Category | Ext OK | Gen OK | Câu trả lời Generative (rút gọn) |
|---|---|---:|---:|---|
| CE-J01 | Metadata | ✓ | ✓ | Company name trong JSON export là "넥스트아이". |
| CE-J02 | Governance | ✓ | ✓ | Ticker của công ty là 137940. |
| CE-J03 | Governance | ✓ | ✓ | DART corp code trong hồ sơ là 00614593. |
| CE-J04 | Governance | ✓ | ✓ | Công ty niêm yết trên sàn KOSDAQ. |
| CE-J05 | Metadata | ✓ | ✓ | Trang web chính thức của công ty (주)넥스트아이 là http://www.nexteye.com. |
| CE-J06 | Metadata | ✓ | ✗ | Khong du du lieu trong context. |
| CE-J07 | Metadata | ✓ | ✓ | Version của file export là 1.1.1. |
| CE-J08 | Metadata | ✓ | ✓ | Generated_at của file export là 2026-04-30T05:04:18.034736. |
| CE-J09 | Governance | ✗ | ✓ | Listing_status trong hồ sơ công ty có nghĩa là trạng thái niêm yết của công ty trên sàn giao dịch chứng khoán. Trong ... |
| CE-J10 | Governance | ✗ | ✗ | Ngành công nghiệp được gán trong hồ sơ là "ứng dụng phần mềm phát triển và cung cấp". |
| CE-J11 | Metadata | ✗ | ✗ | Mức confidence trong profile là "high". |
| CE-J12 | Metadata | ✗ | ✗ | Khong du du lieu trong context. |
| CE-J13 | Metadata | ✗ | ✗ | Khong du du lieu trong context. |
| CE-J14 | Governance | ✗ | ✗ | Khong du du lieu trong context. |
| CE-J15 | Governance | ✗ | ✗ | Khong du du lieu trong context. |
| CE-J16 | insufficient | ✗ | ✓ | Khong du du lieu trong context. |
| CE-J17 | insufficient | ✗ | ✗ | Không đủ dữ liệu trong context. |
| CE-J18 | insufficient | ✗ | ✓ | Khong du du lieu trong context. |
| CE-J19 | insufficient | ✗ | ✓ | Khong du du lieu trong context. |
| CE-J20 | insufficient | ✗ | ✓ | Khong du du lieu trong context. |