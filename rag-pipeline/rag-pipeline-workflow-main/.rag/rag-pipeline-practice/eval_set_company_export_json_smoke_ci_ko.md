# Evaluation Set - Smoke CI (KO, 5 cau production gate)

Schema: evidence-based (8 cot). Subset answerable-only tu `eval_set_company_export_json_dev_ko.md`.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-J02 | 회사의 ticker는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | ticker는 137940이다. | ticker | easy | Governance | smoke_ci |
| CE-J03 | 프로필에 있는 DART corp code는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | DART corp code는 00614593이다. | dart_corp_code | easy | Governance | smoke_ci |
| CE-J06 | 이 데이터셋의 export type은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | 주 benchmark lane은 raw_public_first이다. | export_type | easy | Metadata | smoke_ci |
| CE-J07 | export 파일의 버전은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | dataset_version은 1.1.1이다. | export_version | easy | Metadata | smoke_ci |
| CE-J08 | export 파일의 생성 시각은 언제인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | exported_at timestamp는 2026-05-28T09:14:09Z이다. | generated_at | easy | Metadata | smoke_ci |
