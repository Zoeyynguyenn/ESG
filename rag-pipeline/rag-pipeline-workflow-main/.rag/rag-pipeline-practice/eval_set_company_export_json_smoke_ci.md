# Evaluation Set — Smoke CI (5 cau, production gate)

Schema: evidence-based (8 cot). Subset cua eval_set_company_export_json_dev.md.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-J02 | Ticker cua cong ty la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Ticker 137940 | ticker | easy | Governance | smoke_ci |
| CE-J03 | Dart corp code trong ho so la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Dart corp code 00614593 | dart_corp_code | easy | Governance | smoke_ci |
| CE-J06 | Export type cua bo du lieu nay la gi? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | raw_public_first (primary benchmark lane trong manifest) | export_type | easy | Metadata | smoke_ci |
| CE-J07 | Version cua file export la bao nhieu? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | dataset_version 1.1.1 | export_version | easy | Metadata | smoke_ci |
| CE-J16 | Bo du lieu co ghi metric Scope 3 reduction target den 2030 khong? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | Khong du thong tin dinh luong Scope 3 trong file nay | insufficient_scope3 | hard | insufficient | smoke_ci |
