# Golden Set — Workbook Review Round 1

Generated: 2026-06-11T12:18:25

## Mục tiêu

Triage `reference_seed_candidates_v4_jsonl.jsonl` thành workbook **reviewable**:
loại noise mạnh (cross-company, listing/index, framework-only), collapse duplicate cluster,
giữ fact thật qua `keep`/`rewrite` — **không** canonical final, **không** gold promotion.

## Tình trạng v4 trước review

- Input: **175** candidate rows (v4 JSONL)
- Vấn đề: cross-company leakage (레이시온/현대트랜시스), listing/index (무신사), report meta/index (한샘)
- Yield đã về nhưng review cost cao — thiếu tầng triage workbook

## Rule triage round 1

| Decision | Điều kiện |
|----------|-----------|
| `keep` | Grounded rõ, company đúng, Q/A usable, không listing/nav/meta |
| `rewrite` | Fact có thật; Q generic hoặc excerpt còn noise nhẹ / truncated |
| `reject` | Cross-company, listing/index/nav, framework-only, grounding yếu |
| `collapse_into_cluster` | Trùng cụm fact với anchor mạnh hơn trong cùng `cluster_id` |

## Kết quả tổng quan

- Total input: **175**
- keep: **35**
- rewrite: **72**
- reject: **35**
- collapse_into_cluster: **33**
- **Reviewable sau round 1 (keep + rewrite):** **107**

### Breakdown theo công ty

- **레이시온**: keep 2, rewrite 12, reject 17, collapse 0
- **무신사**: keep 8, rewrite 14, reject 14, collapse 11
- **한샘**: keep 25, rewrite 46, reject 4, collapse 22

### Breakdown theo question_type

- `trend`: 8
- `quantitative`: 62
- `qualitative`: 37

### Breakdown theo rejection reason

- `cross_company_contamination`: 15
- `insufficient_esg_substance`: 13
- `listing_index_meta`: 4
- `framework_only_no_company_fact`: 2
- `portal_nav_contact`: 1

### Breakdown theo cluster action

- `anchor`: 107
- `rejected`: 35
- `collapsed_variant`: 33

## Ví dụ cụ thể

### Cross-company bị reject
- `RX-V4-T01` (레이시온): 현대트랜시스, 2040년 모든 사업장 재생에너지 100% 사용 현대트랜시스가 지속가능경영을 위한 환경·사회·지배구조(ESG) 추진전략과 성과를 담은 ‘2024 현대트랜시스 지속가능성 보고서’를 발간했다고 14일 밝혔…
- `MS-V4-T02` (무신사): ESG 보고서 정렬하기 날짜(내림차순) 날짜(오름차순) 조회수(내림차순) 조회수(오름차순) 제목+내용 제목 내용 회원명 회원아이디 번호 제목 글쓴이 날짜 조회수 232 2025 삼성전자 지속가능경영보고서 관리자 20…
- `RX-V4-Q01` (레이시온): 현대트랜시스, 2040년 모든 사업장 재생에너지 100% 사용 현대트랜시스가 지속가능경영을 위한 환경·사회·지배구조(ESG) 추진전략과 성과를 담은 ‘2024 현대트랜시스 지속가능성 보고서’를 발간했다고 14일 밝혔…

### Listing/index bị reject
- `MS-V4-T01` (무신사): 노출 글주소 02-11 2025_무신사_임팩트_리포트.pdf(68.1 MB) 02-11 10:45 78 https://share.google/eba4b07yLyYwxJQBS 43 2025 무신사 임팩트 리포트 0 0…
- `MS-V4-Q01` (무신사): 노출 글주소 02-11 2025_무신사_임팩트_리포트.pdf(68.1 MB) 02-11 10:45 78 https://share.google/eba4b07yLyYwxJQBS 43 2025 무신사 임팩트 리포트 0 0…
- `MS-V4-L01` (무신사): 노출 글주소 02-11 2025_무신사_임팩트_리포트.pdf(68.1 MB) 02-11 10:45 78 https://share.google/eba4b07yLyYwxJQBS 43 2025 무신사 임팩트 리포트 0 0…

### Row salvageable được rewrite
- `HS-V4-T01`: `한샘는 2050년까지 어떤 기후 목표를 추진하는가?` → `한샘는 2050년까지 어떤 탄소중립 목표를 공개했는가?`
- `HS-V4-Q01`: `한샘는 ESG 평가에서 어떤 등급을 획득했는가?` → `한샘는 KGCS ESG경영 평가에서 어떤 등급을 획득했는가?`
- `HS-V4-Q03`: `한샘는 2050년까지 어떤 기후 목표를 추진하는가?` → `한샘는 2050년까지 어떤 탄소중립 목표를 공개했는가?`

### Row duplicate bị collapse
- `HS-V4-Q18` cluster `한샘::FC_REPORT_FRAMEWORK` — Trùng cụm với anchor HS-V4-Q16
- `HS-V4-Q20` cluster `한샘::FC_MATERIAL_8` — Trùng cụm với anchor HS-V4-Q02
- `HS-V4-Q23` cluster `한샘::FC_ESG_GOVERNANCE` — Trùng cụm với anchor HS-V4-Q13

## Kết luận

- Reviewable rows (keep + rewrite): **107**
- Manual review round 2 ready? **Có — đủ sạch để mở manual review round 2 (keep+rewrite workbook)**
- Flag: `manual_review_ready_flag` = **True**
