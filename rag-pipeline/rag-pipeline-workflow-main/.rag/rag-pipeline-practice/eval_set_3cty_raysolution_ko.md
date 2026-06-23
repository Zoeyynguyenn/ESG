# Evaluation Set — 레이시온 (Raysolution) KO, answerable-only

Schema: evidence-based (8 cot). Package: `레이시온_dataset_package_20260608T055801`.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-RC01 | JSON export에서 회사명은 무엇인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | 회사명은 레이시온이어야 한다. | company_name | easy | Metadata | draft |
| CE-RC02 | export 파일의 dataset_version은 무엇인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | dataset_version은 1.1.1이다. | dataset_version | easy | Metadata | draft |
| CE-RC03 | manifest의 schema_version은 무엇인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | schema_version은 1.1이다. | schema_version | easy | Metadata | draft |
| CE-RC04 | export 파일의 생성 시각(exported_at)은 언제인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | exported_at은 2026-06-08T05:58:01Z이다. | exported_at | easy | Metadata | draft |
| CE-RC05 | manifest의 record_count는 얼마인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | record_count는 1087이다. | record_count | medium | Metadata | draft |
| CE-RC06 | manifest의 document_count는 얼마인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | document_count는 630이다. | document_count | medium | Metadata | draft |
| CE-RC07 | manifest의 source_count는 얼마인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | source_count는 74이다. | source_count | medium | Metadata | draft |
| CE-RC08 | primary benchmark lane 정책은 무엇인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | primary_benchmark_lane은 raw_public_first이다. | primary_benchmark_lane | easy | Metadata | draft |
| CE-RC09 | DART corp_code는 무엇인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/records/company_evidence.jsonl | corp_code는 01730366이다. | dart_corp_code | medium | Governance | draft |
| CE-RC10 | dev split 레코드 수는 얼마인가? | data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/manifest.json | dev split은 262건이다. | dev_split_count | medium | Metadata | draft |
