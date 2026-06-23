# Tiêu chí chọn eval subset demo_company

**Nguyên tắc:** heuristic plan chỉ là bootstrap — subset này chọn tay để traceable, không phải gold cuối.

## Single-doc (20 câu)
- Mỗi câu có **một** `primary_document_id` rõ (HR/env/gov/business/social/cert).
- Tránh câu semantic mơ hồ hoặc label lệch workbook.
- Cân bằng domain: HR×5, Environment×4, Governance×3, Business×1, Social×3, Certification×1, bổ sung×3.

## Cross-doc (15 câu)
- 5 qualitative: narrative span nhiều file (ESG, governance, safety, human rights, environment).
- 10 quantitative: có `needs_merge` hoặc CSV supporting, đại diện HR+CSV, env cluster, economic distribution.
- Mỗi câu ghi rõ trong plan: primary docs, supporting, `needs_merge`.

## Không dùng làm
- Gold answer scoring
- So sánh với `overall_score` lane Dataset-Excel v5
