# Evaluation Set — 한샘 (Hanssem) KO, answerable-only

Schema: evidence-based (8 cot). Package: `한샘_dataset_package_20260608T042739`.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-HS01 | JSON export에서 회사명은 무엇인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | 회사명은 한샘이어야 한다. | company_name | easy | Metadata | draft |
| CE-HS02 | 회사의 ticker는 무엇인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/records/company_evidence.jsonl | ticker는 009240이다. | ticker | easy | Governance | draft |
| CE-HS03 | 이 회사는 어느 시장에 상장되어 있는가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/records/company_evidence.jsonl | 시장은 KOSPI이다. | krx_market | easy | Governance | draft |
| CE-HS04 | export 파일의 dataset_version은 무엇인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | dataset_version은 1.1.1이다. | dataset_version | easy | Metadata | draft |
| CE-HS05 | manifest의 record_count는 얼마인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | record_count는 1161이다. | record_count | medium | Metadata | draft |
| CE-HS06 | manifest의 document_count는 얼마인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | document_count는 687이다. | document_count | medium | Metadata | draft |
| CE-HS07 | export 파일의 생성 시각(exported_at)은 언제인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | exported_at은 2026-06-08T04:27:39Z이다. | exported_at | easy | Metadata | draft |
| CE-HS08 | manifest의 schema_version은 무엇인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | schema_version은 1.1이다. | schema_version | easy | Metadata | draft |
| CE-HS09 | KRX metadata의 size_tier는 무엇인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/records/company_evidence.jsonl | size_tier는 중형이다. | size_tier | medium | Governance | draft |
| CE-HS10 | manifest의 source_count는 얼마인가? | data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json | source_count는 117이다. | source_count | medium | Metadata | draft |
