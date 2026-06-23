# Evaluation Set - Company Export JSON Dev Lane (KO, answerable-only)

Schema: evidence-based (8 cot). Moi cau co ground truth trong package `넥스트아이_dataset_package_20260528T091409`. Khong gom cau insufficient (CE-J16–J20 cu).

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| CE-J01 | JSON export에서 회사명은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | 회사명은 넥스트아이 또는 Nexteye여야 한다. | company_name | easy | Metadata | draft |
| CE-J02 | 회사의 ticker는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | ticker는 137940이다. | ticker | easy | Governance | draft |
| CE-J03 | 프로필에 있는 DART corp code는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | DART corp code는 00614593이다. | dart_corp_code | easy | Governance | draft |
| CE-J04 | 이 회사는 어느 시장에 상장되어 있는가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | 시장은 KOSDAQ이다. | krx_market | easy | Governance | draft |
| CE-J05 | 회사의 공식 홈페이지는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | 공식 홈페이지는 nexteye.com 또는 http://www.nexteye.com 이다. | homepage | easy | Metadata | draft |
| CE-J06 | 이 데이터셋의 export type은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | 주 benchmark lane은 raw_public_first이다. | export_type | easy | Metadata | draft |
| CE-J07 | export 파일의 버전은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | dataset_version은 1.1.1이다. | export_version | easy | Metadata | draft |
| CE-J08 | export 파일의 생성 시각은 언제인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | exported_at timestamp는 2026-05-28T09:14:09Z이다. | generated_at | easy | Metadata | draft |
| CE-J09 | company profile의 listing_status는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | listing_status는 listed이다. | listing_status | medium | Governance | draft |
| CE-J10 | profile에 지정된 industry group은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | KRX industry group은 other 또는 기타이다. | industry_group | medium | Governance | draft |
| CE-J11 | KRX metadata의 internal_score confidence는 얼마인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | confidence는 70.85이다. | krx_confidence | medium | Metadata | draft |
| CE-J12 | manifest의 schema_version은 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | schema_version은 1.1이다. | schema_version | medium | Metadata | draft |
| CE-J13 | KRX metadata의 size_tier는 무엇인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl | size_tier는 초소형이다. | size_tier | medium | Governance | draft |
| CE-J14 | manifest의 record_count는 얼마인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | record_count는 270이다. | record_count | medium | Metadata | draft |
| CE-J15 | manifest의 document_count는 얼마인가? | data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json | document_count는 262이다. | document_count | medium | Metadata | draft |
