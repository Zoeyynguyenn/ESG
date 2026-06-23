# Evaluation Set - Company Export JSON Dev Lane

Schema: evidence-based (8 cot). Chi dung du lieu trong `05_company_export_json`.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-J01 | Company name trong JSON export la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Neu parse dung se tra ten cong ty Nexteye/Nexteye Korean | company_name | easy | Metadata | draft |
| CE-J02 | Ticker cua cong ty la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Ticker 137940 | ticker | easy | Governance | draft |
| CE-J03 | Dart corp code trong ho so la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Dart corp code 00614593 | dart_corp_code | easy | Governance | draft |
| CE-J04 | Cong ty niem yet tren san nao? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | KOSDAQ | krx_market | easy | Governance | draft |
| CE-J05 | Trang web chinh thuc cua cong ty la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Homepage chinh thuc (source_system=homepage); nexteye.com hoac information@nexteye | homepage | easy | Metadata | draft |
| CE-J06 | Export type cua bo du lieu nay la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | raw_public_first (primary benchmark lane trong manifest) | export_type | easy | Metadata | draft |
| CE-J07 | Version cua file export la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | dataset_version 1.1.1 | export_version | easy | Metadata | draft |
| CE-J08 | Generated_at cua file export la thoi diem nao? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | Co timestamp ISO 2026-05-28T09:14:09Z (exported_at trong manifest) | generated_at | easy | Metadata | draft |
| CE-J09 | Company profile co listing_status la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | listed | listing_status | medium | Governance | draft |
| CE-J10 | Industry group duoc gan trong profile la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | KRX industry group hien dang la loai khac (other) | industry_group | medium | Governance | draft |
| CE-J11 | Muc confidence trong profile la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Co truong confidence dang chuoi so | profile_confidence | medium | Metadata | draft |
| CE-J12 | Muc completeness_score cua profile la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | completeness_score 100.00 | completeness_score | medium | Metadata | draft |
| CE-J13 | Country trong profile duoc ghi nhu the nao? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | South Korea | country | medium | Metadata | draft |
| CE-J14 | Bo du lieu co phan profile_evidence hay khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Co key profile_evidence | profile_evidence_presence | medium | Governance | draft |
| CE-J15 | Bo du lieu co phan public_evidence hay khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Co key public_evidence | public_evidence_presence | medium | Governance | draft |
| CE-J16 | Bo du lieu co ghi metric Scope 3 reduction target den 2030 khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong du thong tin dinh luong Scope 3 trong file nay | insufficient_scope3 | hard | insufficient | draft |
| CE-J17 | Bo du lieu co LTIFR target cu the nam 2026 khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong du thong tin LTIFR target | insufficient_ltifr | hard | insufficient | draft |
| CE-J18 | Bo du lieu co board committee count ro rang khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong thay thong tin board committee count cu the | insufficient_board_committee | hard | insufficient | draft |
| CE-J19 | Co the tim duoc wastewater reuse target (%) tu file export nay khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong du thong tin target wastewater reuse | insufficient_water_reuse | hard | insufficient | draft |
| CE-J20 | Co the tim duoc third-party ESG audit frequency ro rang khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong du thong tin tan suat audit ESG | insufficient_audit_frequency | hard | insufficient | draft |
