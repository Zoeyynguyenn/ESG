# Golden Set v2 Cleaning Report

Generated: 2026-06-10T17:00:19
Source: `data\golden_set\v2\step6_gold\golden_set.jsonl`
Output: `data\golden_set\v2\step6_gold\golden_set_clean.jsonl`

## Summary

- input_rows: **87**
- kept_rows: **41**
- dropped_rows: **46**

## Kept By Package

| package_name | kept |
|---|---:|
| 무신사_dataset_package_20260608T092823 | 12 |
| 한샘_dataset_package_20260608T042739 | 29 |

## Drop Reasons

| reason | count |
|---|---:|
| drop_company_mismatch | 10 |
| drop_company_mismatch_duplicate | 4 |
| drop_date_only | 2 |
| drop_date_only_listing | 6 |
| drop_duplicate_same_fact | 6 |
| drop_generic_vendor_content | 5 |
| drop_nav_lookup | 1 |
| drop_nav_menu | 5 |
| drop_nav_menu_duplicate | 5 |
| drop_question_answer_mismatch | 2 |

## Dropped Rows

| ID | package_name | reason | question |
|---|---|---|---|
| GV2-033 | 레이시온_dataset_package_20260608T055801 | drop_date_only | 레이시온의 감사보고서는 언제 제출되었나요? |
| GV2-034 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu | 민원서비스에서 어떤 정보를 신청할 수 있나요? |
| GV2-035 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu | 여수항의 일반현황은 무엇인가요? |
| GV2-036 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 공사는 ESG경영 활동에 대한 이해관계자의 관심 사항을 어떻게 파악하고 있습니까? |
| GV2-037 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu | 온라인 민원신청은 어떻게 하나요? |
| GV2-038 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu | 정보공개제도는 무엇인가요? |
| GV2-039 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu_duplicate | 정보공개제도는 무엇인가요? |
| GV2-040 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu_duplicate | 여수광양항만공사에서 제공하는 정보공개제도는 무엇인가요? |
| GV2-041 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu | 최고경영자의 인사말은 무엇인가요? |
| GV2-042 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu_duplicate | 여수광양항만공사의 정보공개제도는 무엇인가요? |
| GV2-043 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu_duplicate | 여수광양항만공사에서 제공하는 정보공개제도는 무엇인가요? |
| GV2-044 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 현대트랜시스는 언제까지 모든 사업장에서 재생에너지를 100% 사용할 계획인가요? |
| GV2-045 | 레이시온_dataset_package_20260608T055801 | drop_nav_menu_duplicate | 여수광양항만공사의 정보공개제도는 무엇인가요? |
| GV2-047 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 현대트랜시스는 언제부터 지속가능경영 보고서를 발간하고 있나요? |
| GV2-048 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch_duplicate | 현대트랜시스는 언제부터 지속가능경영 보고서를 발간하고 있나요? |
| GV2-049 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 에이피알은 어떤 보고서를 처음으로 발표했나요? |
| GV2-050 | 레이시온_dataset_package_20260608T055801 | drop_generic_vendor_content | 지속가능경영보고서는 어떤 형태로 배포되나요? |
| GV2-051 | 레이시온_dataset_package_20260608T055801 | drop_generic_vendor_content | 지속가능경영보고서 제작 과정에서 어떤 절차가 포함되나요? |
| GV2-052 | 레이시온_dataset_package_20260608T055801 | drop_generic_vendor_content | 지속가능경영보고서 제작 시 안정적인 업체는 어떤 특징이 있나요? |
| GV2-053 | 레이시온_dataset_package_20260608T055801 | drop_generic_vendor_content | 귀사의 지속가능경영보고서를 어떻게 활용할 수 있나요? |
| GV2-054 | 레이시온_dataset_package_20260608T055801 | drop_generic_vendor_content | 지속가능경영보고서 품질 향상 및 검증 대응 교육이 ESG 담당자에게 추천되는 이유는 무엇인가요? |
| GV2-055 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 기아는 지속가능경영 보고서를 어떻게 발간하고 있나요? |
| GV2-056 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 삼성전기 지속가능경영에 대한 의견을 어떻게 활용할 예정인가요? |
| GV2-057 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch_duplicate | 삼성전기의 지속가능성보고서를 어디에 활용하실 계획이십니까? |
| GV2-059 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 삼성전기가 개인정보를 수집하는 목적은 무엇인지, 그리고 수집된 개인정보는 어떤 방식으로 이용되며, 수집 목적이 변경될 경우 어떻게 처리되는지 설명해 주세요. |
| GV2-060 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch_duplicate | 삼성전기가 개인정보를 수집하는 목적은 무엇인가요? |
| GV2-061 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 삼성전기의 뉴스레터를 구독하면 어떤 정보와 함께 개인정보가 어떻게 처리되는지에 대한 내용을 받을 수 있나요? |
| GV2-063 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 삼성전기가 아이디어나 제안을 수령하거나 검토하지 않는 이유는 무엇인가요? |
| GV2-064 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch | 삼성전기의 지속가능경영보고서에서 보고된 2023 회계연도의 시작일과 종료일은 언제인가요? |
| GV2-065 | 레이시온_dataset_package_20260608T055801 | drop_company_mismatch_duplicate | 삼성전기의 지속가능경영보고서의 보고기간은 언제인가요? |
| GV2-068 | 무신사_dataset_package_20260608T092823 | drop_date_only | 무신사의 주요사항보고서는 어떤 날짜에 접수되었으며, 접수번호는 무엇인가요? |
| GV2-069 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 2025 무신사 임팩트 리포트는 언제 작성되었나요? |
| GV2-070 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 무신사의 2025 임팩트 리포트가 공시된 날짜는 무엇인가요? 그리고 이 리포트의 파일 크기는 얼마인가요? |
| GV2-071 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 무신사의 임팩트 리포트는 언제 공시되었나요? |
| GV2-072 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 무신사의 임팩트 리포트가 작성된 날짜는 어떤 정보를 바탕으로 알 수 있나요? |
| GV2-073 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 무신사의 임팩트 리포트는 언제 발표되었나요? |
| GV2-074 | 무신사_dataset_package_20260608T092823 | drop_date_only_listing | 무신사의 ESG 임팩트 리포트는 언제 발행되었나요? |
| GV2-075 | 무신사_dataset_package_20260608T092823 | drop_nav_lookup | 무신사의 지속가능경영보고서를 확인할 수 있는 방법은 무엇인가요? 그리고 이 보고서는 어디에서 찾을 수 있나요? |
| GV2-078 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사는 어떤 ESG 리포트를 발간했나요? |
| GV2-080 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사는 어떤 ESG 리포트를 발간했나요? |
| GV2-081 | 무신사_dataset_package_20260608T092823 | drop_question_answer_mismatch | 무신사가 사업보고서를 제출한 날짜는 IPO 준비의 어떤 의미를 갖고 있나요? |
| GV2-085 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사의 지난해 매출은 얼마였나요? |
| GV2-086 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사의 지난해 매출은 얼마였나요? |
| GV2-088 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사의 지난해 매출은 얼마였나요? |
| GV2-090 | 무신사_dataset_package_20260608T092823 | drop_duplicate_same_fact | 무신사의 지난해 영업이익은 얼마였나요? |
| GV2-092 | 무신사_dataset_package_20260608T092823 | drop_question_answer_mismatch | 무신사의 2025년 연간 매출이 1조4679억 원으로 증가한 이유는 무엇인가요? |
