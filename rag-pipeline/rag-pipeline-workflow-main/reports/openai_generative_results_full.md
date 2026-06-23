# Kết quả Generative vs Extractive — chi tiết 20 câu

LLM generative: `gpt-4o-mini` | Lane: full

## CE-J01 — Company name trong JSON export la gi?

**Expected:** Neu parse dung se tra ten cong ty Nexteye/Nexteye Korean

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
는 2016년 6월 27일 이사회 결의에 의거 NEXTEYE technology (China) Co.,Ltd.사를
USD 5,000,000에 신규 설립 및 출자하기로 결정하였으며, 2016년 7월 18일자로 자본금의 납입이 이루어졌으며, 2019년 04월 02일 지분 USD 7,500,000을 추가
취득하였습니다.주2) 당사는 2016년 10월19일 이사회 결의에 의거 Shanghai Bel-Cosmetic Co.,Ltd 를 479,974,980원에 출자하기로 결정 하였으며,
2017년03월23일 자본금의 납입이 이루어 졌습니다.</P> <P> <SPAN USERMARK="F-GL">주3) 당사는 2017년 04월28일 이사회 결의에 의거 Tianjin Village
11 Cross-border e-commerce Co.,Ltd 를 2,424,744,000원에 출자하기로 결정 하였으며, 2017년05월02일 자본금의 납입이 이루어 졌습니다.주4) 당사는
2018년 1월 5일 이사회의 결의에 의거 마인즈아이 주식회사에 대한 제3자배정 유상증자(204,000주, 유상증자액 : 306,000천원)에 참여하였으며, 2018년 1월 8

--- record ---

record_id: rec_dd1ecc979338be8f
doc_id: doc_d2951e4f1ad2b77b
company: 넥스트아이
title: local_file
section_path: Company Evidence/General / Other
record_role: company_evidence
source_system: local_file
sou
```

### Generative (GPT-4o-mini)

```
Company name trong JSON export là "넥스트아이".
```

---

## CE-J02 — Ticker cua cong ty la bao nhieu?

**Expected:** Ticker 137940

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
# (주)넥스트아이 회사 프로필 - 입력 회사명: (주)넥스트아이 - 해석 회사명: (주)넥스트아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지:
http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군: 기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker:
`companies.csv` - dart_corp_code: `local_dart` - homepage: `companies.csv` - applicant_name: `companies.csv` -
listing_status: `derived` - industry: `krx_meta` ## 보강 필요 항목 - 없음 ## 권장 후속 프로브 - 없음 ## 로컬/KRX 요약 - 로컬 DART 공시:
29건 - 로컬 뉴스: {'naver': 30, 'google': 20} - 로컬 KIPRIS: {'KIPRIS_design_넥스트아이. 아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지: http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군:
기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker: `companies.csv` - dart_corp_code: `local_dart` - homepage:
`companies.csv` - applicant_name: `companies.csv` - listing_status: `derived` - in
```

### Generative (GPT-4o-mini)

```
Ticker của công ty là 137940.
```

---

## CE-J03 — Dart corp code trong ho so la gi?

**Expected:** Dart corp code 00614593

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
# (주)넥스트아이 회사 프로필 - 입력 회사명: (주)넥스트아이 - 해석 회사명: (주)넥스트아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지:
http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군: 기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker:
`companies.csv` - dart_corp_code: `local_dart` - homepage: `companies.csv` - applicant_name: `companies.csv` -
listing_status: `derived` - industry: `krx_meta` ## 보강 필요 항목 - 없음 ## 권장 후속 프로브 - 없음 ## 로컬/KRX 요약 - 로컬 DART 공시:
29건 - 로컬 뉴스: {'naver': 30, 'google': 20} - 로컬 KIPRIS: {'KIPRIS_design_넥스트아이. 아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지: http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군:
기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker: `companies.csv` - dart_corp_code: `local_dart` - homepage:
`companies.csv` - applicant_name: `companies.csv` - listing_status: `derived` - in
```

### Generative (GPT-4o-mini)

```
DART corp code trong hồ sơ là 00614593.
```

---

## CE-J04 — Cong ty niem yet tren san nao?

**Expected:** KOSDAQ

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
G.board, G.compliance

DART disclosure snapshot
corp_code: 00614593
corp_name: 넥스트아이
stock_code: 137940
corp_cls: K
report_nm: 주권매매거래정지 (주식의 병합, 분할 등 전자등록 변경, 말소)
rcept_no: 20260428900546
flr_nm: 코스닥시장본부
rcept_dt: 20260428
rm: 코

--- record ---

record_id: rec_497992415b48e244
doc_id: doc_da4ce800c6e07a5d
company: 넥스트아이
title: krx_meta
section_path: Company Evidence/Business & Strategy
record_role: company_evidence
source_system: krx_esg
source_url: None
esg_tags: G.strategy

KRX company metadata
name: 넥스트아이
market: KOSDAQ
market_cap: 22452044896
sector: 중견기업부
industry_raw: 측정, 시험, 항해, 제어 및 기타 정밀기기 제조업; 광학기기 제외
industry_group: 기타
size_tier: 초소형

--- record ---

record_id: rec_35b526d91f403aab
doc_id: doc_df5c3db65e3681e2
company: 넥스트아이
title: local_downloader
section_path: Company Evidenc
```

### Generative (GPT-4o-mini)

```
Công ty niêm yết trên sàn KOSDAQ.
```

---

## CE-J05 — Trang web chinh thuc cua cong ty la gi?

**Expected:** Homepage chinh thuc (source_system=homepage); nexteye.com hoac information@nexteye

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
# (주)넥스트아이 회사 프로필 - 입력 회사명: (주)넥스트아이 - 해석 회사명: (주)넥스트아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지:
http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군: 기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker:
`companies.csv` - dart_corp_code: `local_dart` - homepage: `companies.csv` - applicant_name: `companies.csv` -
listing_status: `derived` - industry: `krx_meta` ## 보강 필요 항목 - 없음 ## 권장 후속 프로브 - 없음 ## 로컬/KRX 요약 - 로컬 DART 공시:
29건 - 로컬 뉴스: {'naver': 30, 'google': 20} - 로컬 KIPRIS: {'KIPRIS_design_넥스트아이. 아이 - 종목코드: 137940 - DART corp_code: 00614593 - 홈페이지: http://www.nexteye.com - 상장구분: listed - 업종: 기타 - KRX 산업군:
기타 - KRX 시가총액 구분: 초소형 ## 출처별 판정 - ticker: `companies.csv` - dart_corp_code: `local_dart` - homepage:
`companies.csv` - applicant_name: `companies.csv` - listing_status: `derived` - in
```

### Generative (GPT-4o-mini)

```
Trang web chính thức của công ty (주)넥스트아이 là http://www.nexteye.com.
```

---

## CE-J06 — Export type cua bo du lieu nay la gi?

**Expected:** raw_public_first (primary benchmark lane trong manifest)

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | False |
| insufficient_ok | True | True |

### Extractive

```
{
  "dataset_name": "넥스트아이",
  "dataset_version": "1.1.1",
  "schema_version": "1.1",
  "exported_at": "2026-05-28T09:14:09Z",
  "record_count": 270,
  "document_count": 262,
  "company_count": 1,
  "source_count": 92,
  "benchmark_split": {
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "lane_policy": {
    "primary_benchmark_lane": "raw_public_first",
    "summary_lane": "derived_summary_only",
    "separate_lanes": [
      "company_evidence",
      "requirement_taxonomy",
      "ai_extracted_response"
    ]
  },
  "lane_counts": {
    "company_evidence": 170,
    "requirement_taxonomy": 50,
    "ai_extracted_response": 50,
    "raw_count": 170,
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "checksums": [
    {
      "path": "splits/dev.jsonl",
      "sha256": "e01dcf2148ab1fc0f2ecaaadea6efec41880b5eaef16633702ed18407ffdec30"
    },
    {
      "path": "sp...
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J07 — Version cua file export la bao nhieu?

**Expected:** dataset_version 1.1.1

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
{
  "dataset_name": "넥스트아이",
  "dataset_version": "1.1.1",
  "schema_version": "1.1",
  "exported_at": "2026-05-28T09:14:09Z",
  "record_count": 270,
  "document_count": 262,
  "company_count": 1,
  "source_count": 92,
  "benchmark_split": {
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "lane_policy": {
    "primary_benchmark_lane": "raw_public_first",
    "summary_lane": "derived_summary_only",
    "separate_lanes": [
      "company_evidence",
      "requirement_taxonomy",
      "ai_extracted_response"
    ]
  },
  "lane_counts": {
    "company_evidence": 170,
    "requirement_taxonomy": 50,
    "ai_extracted_response": 50,
    "raw_count": 170,
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "checksums": [
    {
      "path": "splits/dev.jsonl",
      "sha256": "e01dcf2148ab1fc0f2ecaaadea6efec41880b5eaef16633702ed18407ffdec30"
    },
    {
      "path": "sp...
```

### Generative (GPT-4o-mini)

```
Version của file export là 1.1.1.
```

---

## CE-J08 — Generated_at cua file export la thoi diem nao?

**Expected:** Co timestamp ISO 2026-05-28T09:14:09Z (exported_at trong manifest)

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/manifest.json`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | True | True |
| insufficient_ok | True | True |

### Extractive

```
{
  "dataset_name": "넥스트아이",
  "dataset_version": "1.1.1",
  "schema_version": "1.1",
  "exported_at": "2026-05-28T09:14:09Z",
  "record_count": 270,
  "document_count": 262,
  "company_count": 1,
  "source_count": 92,
  "benchmark_split": {
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "lane_policy": {
    "primary_benchmark_lane": "raw_public_first",
    "summary_lane": "derived_summary_only",
    "separate_lanes": [
      "company_evidence",
      "requirement_taxonomy",
      "ai_extracted_response"
    ]
  },
  "lane_counts": {
    "company_evidence": 170,
    "requirement_taxonomy": 50,
    "ai_extracted_response": 50,
    "raw_count": 170,
    "dev": 77,
    "validation": 93,
    "full": 170
  },
  "checksums": [
    {
      "path": "splits/dev.jsonl",
      "sha256": "e01dcf2148ab1fc0f2ecaaadea6efec41880b5eaef16633702ed18407ffdec30"
    },
    {
      "path": "sp...
```

### Generative (GPT-4o-mini)

```
Generated_at của file export là 2026-04-30T05:04:18.034736.
```

---

## CE-J09 — Company profile co listing_status la gi?

**Expected:** listed

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | True |
| insufficient_ok | True | True |

### Extractive

```
tes": 228652 }, { "ts":
"2026-04-23T00:06:51.407151", "url": "http://www.nexteye.com/upload_img/file/202203/1647500074562765.pdf",
"category": "재무보고서", "description": "넥스트아이 2021년 감사보고서 (2022.03)", "filename": "1647500074562765.pdf",
"size_bytes": 2208206 }, { "ts": "2026-04-23T00:07:21.288376", "url":
"http://www.nexteye.com/upload_img/file/202503/1742540185242448.pdf", "category": "재무보고서", "description":
"넥스트아이 2024년 연결재무제표에 대한 감사보고서 (2025.03)", "filename": "1742540185242448.pdf", "siz

--- record ---

record_id: rec_8ac15c79e1a0096e
doc_id: doc_7217e6ef23aed689
company: 넥스트아이
title: local_file
section_path: Company Evidence/General / Other
record_role: company_evidence
source_system: local_file
source_url: None
esg_tags: G.other

D 주5)2017.11.24100.00% 화장품 판매 홍콩 비상장 - 마인즈 아이(주) 주6)2018.
```

### Generative (GPT-4o-mini)

```
Listing_status trong hồ sơ công ty có nghĩa là trạng thái niêm yết của công ty trên sàn giao dịch chứng khoán. Trong trường hợp của công ty 넥스트아이, listing_status được ghi là "listed", có nghĩa là công ty đã được niêm yết trên sàn giao dịch.
```

---

## CE-J10 — Industry group duoc gan trong profile la gi?

**Expected:** KRX industry group hien dang la loai khac (other)

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
1 ~ 42) 도매 및 소매업 (45~47) 운수 및 창고업 (49~52) 숙박 및 음식점업 (55 ~ 56) 정보통신업 (58 ~ 63) 금융 및 보험업 (64 ~ 66)
부동산업 (68) 교육 서비스업 (85) 업종 15개씩 보기 30개씩 보기 15개씩 보기 30개씩 보기 첫페이지로 이동 이전 5페이지로 이동 1 페이지로 이동 2 페이지로 이동 3 페이지로 이동 4
페이지로 이동 5 페이지로 이동 다음 5페이지로 이동 마지막 페이지로 이동 첫페이지로 이동 이전 5페이지로 이동 페이지로 이동 페이지로 이동 페이지로 이동 페이지로 이동 페이지로 이동 다음
5페이지로 이동 마지막 페이지로 이동 이용약관 개인정보처리방침 신고센터 벤처기업확인기관 사업자등록번호 : 398-82-00505 | 벤처기업확인기관장 : 송 병 준 (06151) 서울 강남구
테헤란로 309 삼성제일빌딩 10층 COPYRIGHT(C) VENTURE ALL RIGHTS RESERVED. 상담센터 1566-6487 운영시간 09:00 ~ 18:00 (주말/공휴일 휴무)
점심시간 12:00 ~ 13:00 카카오 상담채널 바로가기 이용약관 개인정보처리방침 신고센터 벤처기업확인기관 사업자등록번호 : 398-82-00505 | 벤처기업확인기관장 : 송 병 준
(06151) 서울 강남구 테헤란로 309 삼성제일빌딩 10층 COPYRIGHT(C) VENTURE ALL RIGHTS RESERVED.
```

### Generative (GPT-4o-mini)

```
Ngành công nghiệp được gán trong hồ sơ là "ứng dụng phần mềm phát triển và cung cấp".
```

---

## CE-J11 — Muc confidence trong profile la bao nhieu?

**Expected:** Co truong confidence dang chuoi so

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
맥북 프로 대신 '맥북 울트라' 등판…애플, 차세대 맥 브랜드 개편 시동 6 구글 딥마인드 "AGI 프론티어로 새 르네상스 열 것“ 7 윤창수
본부장, 아주IB투자 주식 3075주 매도 8 비트코인 4만달러 추락설? 전문가가 답했다…"통계적으로 불가능" 9 [핀테크핫이슈] 4대 금융그룹 실적 '희비'...AI·디지털 금융 확산 10
인크레더블버즈, 주권 매매거래정지 기간 변경…감사의견 관련 개선기간 반영 1 2026년 5월 사상 최고가 기록할 알트코인 3종 2 샘슨 모우 "비트코인 100만달러 코앞…12만달러 아래는 저평가"
3 비트코인, 핵심 지지선서 반등…트레이더들 8만달러 재도전 주시 4 일론 머스크, 오픈AI 재판서 “AI가 인류를 끝낼 수 있다” 증언 5 폴리마켓서 10만개 계정 1000달러 이상 손실…수익은
소수 고빈도 계정에 집중 6 SNS서 비트코인 9만달러 전망 급증…되레 약세 신호인 이유 7 번스타인, 로빈후드 목표가 130달러 유지…예측시장 확대에 무게 8 10년 휴면 이더리움 ICO 지갑
재가동…1만ETH 전량 이체 9 캐나다, 암호화폐 ATM 금지 추진…사기범·자금세탁 통로로 규정 10 아담 백 “비트코인 ETF 호재지만 기관 자금 예상보다 느려” 2026년 5월 사상 최고가
기록할 알트코인 3종 샘슨 모우 "비트코인 100만달러 코앞…12만달러 아래는 저평가" 비트코인, 핵심 지지선서 반등…트레이더들 8만달러 재도전 주시 일론 머스크, 오픈AI 재판서 “AI가 인류를
끝낼 수 있다” 증언 폴리마켓서 10만개 계정 1000달러 이상 손실…수익은 소수 고빈도 계정에 집중 위로 전체메뉴닫기
```

### Generative (GPT-4o-mini)

```
Mức confidence trong profile là "high".
```

---

## CE-J12 — Muc completeness_score cua profile la bao nhieu?

**Expected:** completeness_score 100.00

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
랜드 (주)티몬 2,953 리뷰 (주)위메프 2,780 리뷰 (주)엘지유플러스 2,605 리뷰 서비스업 (주)장스푸드 (주)에스씨케이컴퍼니 7,579 리뷰
(주)트랜스코스모스코리아 3,970 리뷰 (주)비케이알 3,739 리뷰 제조/화학 한국쯔바키모토오토모티브(주) 삼성전자(주) 11,103 리뷰 LG전자(주) 7,534 리뷰 엘지이노텍(주)
5,053 리뷰 의료/제약/복지 오스템임플란트(주) 1,799 리뷰 한미약

기업 랭킹 홈 바로가기 실시간 급상승 검색 기업 2026.04.30 04:30 기준 더블유피피미디어코리아(주) 카테노이드(주) 1 대구문화방송(주) 2 2 (주)코리아이앤피 12 3
(주)다이나믹디자인 -1 4 충북대학교산학협력단 3 5 (주)에이피알 - 6 디케이산업(주) New 7 파티붕붕(주) 1 8 (주)정석케미칼 1 9 현대건설(주) -5 10 (주)웹스 2
IT/웹/통신 (주)올포랜드 (주)티몬 2,953 리뷰 (주)위메프 2,780 리뷰 (주)엘지유플러스 2,605 리뷰 서비스업 (주)장스푸드 (주)에스씨케이컴퍼니 7,579 리뷰
(주)트랜스코스모스코리아 3,970 리뷰 (주)비케이알 3,739 리뷰 제조/화학 한국쯔바키모토오토모티브(주) 삼성전자(주) 11,103 리뷰 LG전자(주) 7,534 리뷰 엘지이노텍(주)
5,053 리뷰 의료/제약/복지 오스템임플란트(주) 1,799 리뷰 한미약품(주) 1

육(주) 1,597 리뷰 건설업 한국토지주택공사 2,390 리뷰 한전KPS(주) 1,510 리뷰 현대엔지니어링(주) 1,475 리뷰 미디어/디자인 (주)대학내일 씨제이씨지브이(주) 2
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J13 — Country trong profile duoc ghi nhu the nao?

**Expected:** South Korea

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
점 소재지 : (도로명주소)경기도 안양시 동안구 동편로 13번길 65 넥스트아이빌딩 (전
화) 031-389-2204 - 7 - 재 무 상 태 표 제 27 기 2024년 12월 31일 현재 제 26 기 2023년 12월 31일 현재 주식회사 넥스트아이 (단위 : 원) 과 목 주석 제
27(당) 기 제 26(전) 기 자 산 Ⅰ. 유동자산 19,085,142,47324,945,321,113 1.
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J14 — Bo du lieu co phan profile_evidence hay khong?

**Expected:** Co key profile_evidence

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
99862347053.docx", "category": "기타", "description":
"첨부파일2", "filename": "1647999862347053_4.docx", "size_bytes": 17222 }, { "ts": "2026-04-29T03:18:06.132173",
"url": "http://www.nexteye.com/upload_img/file/202204/1649152869352583.docx", "category": "입찰조달",
"description": "입찰서 다운로드", "filename

[ { "ts": "2026-04-29T03:18:02.134542", "url":
"http://www.nexteye.com/upload_img/file/202203/1647999843911857.xlsx", "category": "기타", "description":
"첨부파일1", "filename": "1647999843911857_4.xlsx", "size_bytes": 139569 }, { "ts": "2026-04-29T03:18:04.127614",
"url": "http://www.nexteye.com/upload_img/file/202203/1647999862347053.docx", "category": "기타", "description":
"첨부파일2", "filename": "1647999862347053_4.docx", "size_bytes": 17222 }, { "ts": "2026-04-29T03:18:06.132173",
"url": "http://www.nex
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J15 — Bo du lieu co phan public_evidence hay khong?

**Expected:** Co key public_evidence

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | True | True |

### Extractive

```
inline-
block;*/ padding-left:3px; padding-right: 1px; line-height:22px; padding-top:0p

--- record ---

record_id: rec_2b7f153a4b114a4f
doc_id: doc_a897d4649797e8a2
company: 넥스트아이
title: probe_agent_research_file
section_path: Company Evidence/General / Other
record_role: company_evidence
source_system: probe
source_url: None
esg_tags: G.other

/html; charset=euc-kr"/> </HEAD> <body> <STYLE> .PGBRK {page-break-after:always} .COVER-TITLE {TEXT-
ALIGN:CENTER; color: #ff8625; FONT-FAMILY: HY헤드라인M; FONT-WEIGHT: bold; FONT-SIZE: 28px; LETTER-SPACING: -1px;
line-height:28px; height:45px; WIDTH:600px;} .P {TEXT-ALIGN:JUSTIFY; FONT-FAMILY:돋움; COLOR:#666666; LINE-
HEIGHT:18px; WIDTH:600px;} .P-LARGE {TEXT-ALIGN:LEFT; FONT-FAMILY:돋움; FONT-SIZE:14px; COLOR:#000000;
WIDTH:600px; LETTER-SPACING:0.01cm
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J16 — Bo du lieu co ghi metric Scope 3 reduction target den 2030 khong?

**Expected:** Khong du thong tin dinh luong Scope 3 trong file nay

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | True |
| insufficient_ok | False | True |

### Extractive

```
렌즈고정방법 특허 2014-03-13 미 포커싱 CCM의 자동선 별장치 및 자동선별방법 특허 2014-05-16 3차원 자동 측정장치 및
3차원 자동 측정방법 특허 2015-04-08 카메라 모듈의 포커싱 장치 특허 2015-06-15 카메라 모듈의 제조 및 검사 장치 특허 2016-02-24 카메라모듈 검사

검사 장비에 대한 설계, 제작, 제어등자체기술보유 사업 영역 주요 제품 TFT AOI CF AOI MAC/MIC Mindseye 기술 특허 권리 구분 세부 출원번호/등록번호 출원/등록 일자 명칭
특허 기계장치 생산기술 10-2014-0028803 2014-03-12 자유곡면 또는 3차원 형상을 가지는 검사대상물에 대한 검사시스템 및 상기 검사시스템 운영방법 특허 기계장치 생산기술
10-2014-0028802 2014-03-13 CCM 렌즈고정방법 특허 기계장치 생산기술 10-2014-0028801 2014-03-13 미 포커싱 CCM의 자동선 별장치 및 자동선별방법 특허
기계장치 생산기술 10-2014-0058684 2014-05-16 3차원 자동 측정장치 및 3차원 자동 측정방법 특허 기계장치 생산기술 10-2015-0049636 2015-04-08 카메라 모듈의
포커싱 장치 특허 기계장치 생산기술 10-2015-0084108 2015-06-15 카메라 모듈의 제조 및 검사 장치 특허 기계장치 생산기술 10-2016-0021626 2016-02-24
카메라모듈 검사장치 및 검사방법 권리 출원/등록 일자 명칭 특허 2014-03-12 자유곡면 또는 3차원 형상을 가지는 검사대상물에 대한 검사시스템 및
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J17 — Bo du lieu co LTIFR target cu the nam 2026 khong?

**Expected:** Khong du thong tin LTIFR target

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | False |
| insufficient_ok | False | False |

### Extractive

```
9.13% 상승 확정…서울
18.6% ‘급등’ 성남 상대원2구역 시공사 교체 내홍 격화…‘운명의 1주일’ 분수령 [현장] 한화에어로, 공중·지상 넘나드는 방위 기술 국산화 ‘총력’...중심에는

비용 효율화로 수익성 개선 여지가 커지고 있다는 평가다. 증권가에서는 당분간 화장품 업종 내에서도 종목별 차별화 장세가 이어질 것으로 보고 있다.
```

### Generative (GPT-4o-mini)

```
Không đủ dữ liệu trong context.
```

---

## CE-J18 — Bo du lieu co board committee count ro rang khong?

**Expected:** Khong thay thong tin board committee count cu the

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | True |
| insufficient_ok | False | True |

### Extractive

```
과제 (33건) 더보기 도움말 과제명 (과제고유번호)/ 기준연도 / 사업명 / 연구책임자명 / 과제수행기관 / 부처명 / 정부투자연구비(총연구비) 연구내용 보안과제(국방
비밀과제 포함) 서비스는 검색에서 제한됩니다. 산업용 영상처리보다 전용 IC 개발 (1420019073) 2002 중소기업기술이전지원 변종은 ( 주 ) 넥스트아이 중소기업청 51,000,000 (

이상 시작날짜 달력 열기 - 종료날짜 달력 열기 공동과제 유무 5 해당없음 공동연구 위탁과제 위탁/공동 집행부처명 5 집행부처명검색어 입력 검색 집행부처명검색 검색어 입력 검색 과학기술정보통신부
(2) 교육부 (2,301) 교육과학기술부 (39) 중소벤처기업부 (2) 산업통상자원부 (301) 국토교통부 (39) 더보기 더보기 연구 수행 주체 82 연구 책임자 82 고급 필터 열기 검색 필터
과제 (33건) 더보기 도움말 과제명 (과제고유번호)/ 기준연도 / 사업명 / 연구책임자명 / 과제수행기관 / 부처명 / 정부투자연구비(총연구비) 연구내용 보안과제(국방 비밀과제 포함) 서비스는
검색에서 제한됩니다.
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J19 — Co the tim duoc wastewater reuse target (%) tu file export nay khong?

**Expected:** Khong du thong tin target wastewater reuse

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | True |
| insufficient_ok | False | True |

### Extractive

```
6%대
상승…KT 늘고 vs SK텔레콤 줄 때, 네이버·카카오 중 누가 웃었을까 [데이터 뉴스룸] 기계 업체 50곳 영업益 성적 희비 교차…한화엔진 웃고 vs 두산밥캣 울고 [데이터 뉴스룸] 기계 업체
50곳 영업益 성적 희비 교차…한화엔진 웃고 vs 두산밥캣 울고 [데이터 뉴스룸] 에너지 업체 이익 곳간 늘었지만 침울, 왜?…한국전력 vs 삼성SDI, 영업이익 성적에 누가 울고 웃었을까 [데이터
뉴스룸] 에너지 업체 이익 곳간 늘었지만 침울, 왜?…한국전력 vs 삼성SDI, 영업이익 성적에 누가 울고 웃었을까 [데이터 뉴스룸] 유통상사業, 1년 새 영업益 1000억 넘게 오른 회사
2곳은?…이부진 사장이 이끄는 호텔신라 영업익 증가율만 3000%↑ [데이터 뉴스룸] 유통상사業, 1년 새 영업益 1000억 넘게 오른 회사 2곳은?…이부진 사장이 이끄는 호텔신라 영업익 증가율만
3000%↑ [신재생에너지 혁신] 독일, 라이江 물살 이용한 친환경 수력발전 도입 [신재생에너지 혁신] 독일, 라이江 물살 이용한 친환경 수력발전 도입 [녹색경제신문 = 박진아 유럽 주재기자]
태양광 및 풍력 등 신재생에너지로 발전되는 전력 공급은 하루 해가 저문 밤 시간과 바람이 없는 잔잔한 날이 되면 전기 발전량이 급감하지만 ... [테크+디자인] 태양광 집전판 표면을 다채롭게 디자인
할 때 [EU 에너지정책] EU 委, 회원국들에 ‚탈원전 폐쇄 천천히 하라‘ 권고 [디자인+웨어러블] 매출 침체로 고전 중인 명품가 구찌, AI

vs SK텔레콤 줄 때, 네이버·카카오 중 누가 웃었을까 [데이터 뉴스룸] 정보통신 업체 50곳 영업益
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---

## CE-J20 — Co the tim duoc third-party ESG audit frequency ro rang khong?

**Expected:** Khong du thong tin tan suat audit ESG

**Top source:** `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl`

| Metric | Extractive | Generative |
|---|---|---|
| retrieval_hit | True | True |
| citation | True | True |
| answer_correct | False | True |
| insufficient_ok | False | True |

### Extractive

```
company: 넥스트아이
title: probe_agent_research_file
section_path: Company Evidence/General / Other
record_role: company_evidence
source_system: probe
source_url: None
esg_tags: G.other

; line-height:22px; padding-top:0px; padding-bottom:0px; text-align:left; vertical-align:middle; border: 0px
solid #DBDBDB; } .xforms.img{ border : 0px; } .xforms a:link { color: #194866; text-decoration: none; }
.xforms a:active { color: #194866; text-decoration: none; } .xforms a:visited { color: #194866; text-
decoration: none; } .xforms A:hover { color:008BE3; text-decoration: none; } .xforms_input{ border: 0px solid
#DBDBDB; padding-left:3px; padding-right: 1px; height:22px; padding-top:0px; padding-bottom:0px; text-
align:left; } </STYLE> <title>넥스트아이/주주명부폐쇄기간 또는 기준일 설정/(2024.12.13)주주명부폐쇄기간 또는 기준일 설정</ti
```

### Generative (GPT-4o-mini)

```
Khong du du lieu trong context.
```

---
