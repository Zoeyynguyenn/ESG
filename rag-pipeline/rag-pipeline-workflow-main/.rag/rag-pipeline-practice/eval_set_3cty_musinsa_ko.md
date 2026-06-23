# Evaluation Set — 무신사 (Musinsa) KO, answerable-only

Schema: evidence-based (8 cot). Package: `무신사_dataset_package_20260608T092823`.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-MS01 | JSON export에서 회사명은 무엇인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | 회사명은 무신사여야 한다. | company_name | easy | Metadata | draft |
| CE-MS02 | DART corp_code는 무엇인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/records/company_evidence.jsonl | corp_code는 01137727이다. | dart_corp_code | medium | Governance | draft |
| CE-MS03 | export 파일의 dataset_version은 무엇인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | dataset_version은 1.1.1이다. | dataset_version | easy | Metadata | draft |
| CE-MS04 | manifest의 record_count는 얼마인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | record_count는 2160이다. | record_count | medium | Metadata | draft |
| CE-MS05 | manifest의 document_count는 얼마인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | document_count는 679이다. | document_count | medium | Metadata | draft |
| CE-MS06 | export 파일의 생성 시각(exported_at)은 언제인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | exported_at은 2026-06-08T09:28:23Z이다. | exported_at | easy | Metadata | draft |
| CE-MS07 | manifest의 schema_version은 무엇인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | schema_version은 1.1이다. | schema_version | easy | Metadata | draft |
| CE-MS08 | manifest의 source_count는 얼마인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | source_count는 113이다. | source_count | medium | Metadata | draft |
| CE-MS09 | primary benchmark lane 정책은 무엇인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | primary_benchmark_lane은 raw_public_first이다. | primary_benchmark_lane | easy | Metadata | draft |
| CE-MS10 | validation split 레코드 수는 얼마인가? | data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/manifest.json | validation split은 804건이다. | validation_split_count | medium | Metadata | draft |
