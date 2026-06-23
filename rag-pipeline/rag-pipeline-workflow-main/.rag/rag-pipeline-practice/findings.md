# Findings

## Unified ESG answer resolution (2026-06-19) — executed

1. **Artifact**: `reports/unified_esg_answer_resolution_20260619-144820/`
2. **Code**: `unified_esg_resolution_policy.py`, `unified_esg_answer_resolution.py`; schema `data/unified_esg/unified_answer_schema.json`
3. **Merge**: join `question_id` ưu tiên; fallback `company_id::family_id::metric_name::year`
4. **Pilot** (goldns/emni RAG + holdout/demo structured): **566** rows — BACKFILL_DATASET **67**, BACKFILL_INTERNAL **19**, NO_ANSWER **480**; chưa MATCH/CONFLICT vì company_id chưa overlap
5. **Review**: `unified_esg_review.xlsx` + `unified_answers.jsonl` — không ghi đè Excel gốc
6. **Chiến lược**: dataset + internal-doc = 2 nguồn đầu vào cùng bài toán ESG answer resolution

## Team playbook 2 lane (2026-06-19)

1. Da tao tai lieu tong hop 2 lane theo goc nhin dung chung cho team:
   - lane `Dataset Excel -> RAG eval -> metrics/score`
   - lane `Enterprise internal-doc -> structured ESG data`
2. Tai lieu khong di sau vao lich su benchmark, ma tap trung vao:
   - muc tieu tung lane
   - dau vao / dau ra
   - khi nao dung lane nao
   - cach doc loi
   - flow ngan nhat khi co cong ty moi
3. Tai lieu phu hop de onboarding thanh vien moi va de thong nhat cach van hanh trong team
4. Ban moi da duoc nang cap theo tu duy hop nhat nghiep vu:
   - 2 nguon dau vao
   - 2 lane xu ly
   - 1 lop `unified ESG answer resolution`
5. Day la cach hieu dung nhat de team ap dung sau khi da co layer hop nhat ket qua ESG

## Bao cao 22 - enterprise internal-doc (2026-06-19)

1. Bao cao 22 tach rieng khoi bao cao 21 va chi tap trung vao lane `enterprise internal-doc`
2. Cau truc bao cao duoc chot theo 4 nhom:
   - muc tieu cua lane
   - cach thuc hien
   - ket qua dat duoc
   - cac yeu cau chinh va cach da hien thuc hoa
3. Noi dung bao cao khong lap lai lane `Dataset Excel -> RAG eval -> metrics/score`, ma chi nhan manh:
   - capability cot loi da harden
   - onboarding path da plug-in-ready
   - SOP / bootstrap kit / templates da co
   - trang thai hien tai = `done_until_real_data`

## Operational packaging (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_operational_packaging_20260619-104141/`
2. **Deliverables**: `ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md`, `ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md`, 3 templates, `bootstrap_enterprise_company.py`, `operational_packaging.py`
3. **Bootstrap kit**: 6 checklist sections (intake → review), 7-step runbook, 4 decision rules (corpus_limited / system_gap / parser / natural_pass)
4. **Lane status**: **`done_until_real_data`** — chuẩn bị hoàn tất; constructed regression = CI chuẩn; natural path plug-in-ready
5. **Manual steps còn lại khi có công ty mới**: registry + PROBE_PATHS + ingest (vận hành, không code lõi)
6. **Nếu chưa có data thật**: giữ CI constructed; dry-run SOP trên hanssem/musinsa; không harden lõi thêm

## Natural-case onboarding gate (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_natural_onboarding_gate_20260619-103432/`
2. **Code**: `capability_gate_runner.py`, `natural_case_onboarding.py`; schema `natural_capability_case_schema.json`; doc `docs/ENTERPRISE_INTERNAL_DOC_NATURAL_CASE_ONBOARDING.md`
3. **Gate kết quả**:
   - Constructed regression: **5/5 layers pass**, metrics **100%**, `ghost_pass_count=0`
   - Natural diagnostics (13 holdout probes): `candidate_found_rate=30.8%`, `corpus_limited_rate=100%`, `system_gap_rate=0%`
   - `overall_status`: **ready_for_natural_plug_in**
4. **Harness reuse**: cùng `run_capability_benchmark()` — natural case chỉ cần `test_type=natural_holdout_probe` + embedded probe; không sửa pipeline lõi
5. **Phụ thuộc demo còn lại**: holdout corpus hanssem/musinsa, `PROBE_PATHS` hardcoded, constructed `source_units` synthetic cho regression
6. **Natural draft thresholds**: informational only — headline fail `parser_coverage_minimum` (0.31 vs 0.5) do corpus chưa overlap, không phải system gap
7. **Bước tiếp**: onboard công ty thật đầu tiên — ingest → probes → natural cases → gate → phân tích failure_mode

## Fusion equivalence hardening (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_fusion_equivalence_hardening_20260619-102350/`
2. **Code**: `fusion_equivalence.py`, `narrative_table_fusion.py`; refine `value_equivalence.py`, `evidence_aggregator.py`, `conflict_classifier.py`
3. **Constructed cases bổ sung**: `CONSTRUCT-EQUIV-NUMERIC-COMMA`, `CONSTRUCT-FUSION-NARRATIVE-TABLE-SCALED` (labeled `constructed`)
4. **Delta vs cross-role hardening prior** (`20260619-101153`):
   - `cross_doc_equivalence_match_rate`: **66.7% → 100%**
   - `evidence_fusion_success_rate`: **83.3% → 100%**
   - `conflict_classification_accuracy`: **83.3% → 100%**
   - `single_source_to_multi_source_promotion_rate`: **83.3% → 100%** (ghost_pass **0**)
5. **Root fixes (family-level, không tune case lẻ)**:
   - Narrative GHG regex: tránh capture `Scope 1+2` → `0`/`1`; anchor `were/was ... tCO2e`
   - Numeric canonical: không collapse mọi numeric về cùng `family:item` key
   - Grade equivalence: `A+` tách khỏi `A` trước registry lookup
   - Thousand scale: `12.5 thousand` → `12500` tại extraction
   - Fusion contract: tách `equivalence_collapse_ok`, `fusion_ok`, `promotion_integrity_ok`
   - Conflict: `numeric vs missing/undisclosed role` → `conflict_numeric`
6. **Narrative↔table**: `CONSTRUCT-NARRATIVE-VS-TABLE` và scaled variant đều **multi_source_confirmed**
7. **Natural probes**: không đổi — vẫn **100% corpus_limited**
8. **Bước tiếp**: plug-in tài liệu doanh nghiệp thật qua natural cases; giữ constructed gate

## Cross-role extraction hardening (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_cross_role_hardening_20260619-101153/`
2. **Registry**: `data/enterprise_docs/metric_equivalence_registry.json` — family buckets, metric aliases, cross-role narrative patterns, value/semantic equivalence
3. **Code**: `src/enterprise_docs/cross_role_extraction.py`, `value_equivalence.py`; wire vào `structured_extractor._collect_row_candidates_from_text` + capability benchmark
4. **Delta vs capability benchmark prior** (`20260619-100639`):
   - `cross_role_extraction_alignment_rate`: **0% → 100%** (6/6 constructed multi-source cases)
   - `alias_normalization_success_rate`: **50% → 100%**
   - `evidence_fusion_success_rate`: **50% → 83.3%** (5/6)
   - `conflict_classification_accuracy`: **33% → 83.3%**
   - `conflict_resolution_readiness_rate`: **16.7% → 100%** (proxy)
   - `single_source_to_multi_source_promotion_rate`: **100% → 83.3%** — promotion giờ bám `fusion_ok`, không còn ghost pass
5. **Root cause đã fix**: extraction trước đây phụ thuộc `company_id` trong family registry → `capability_synthetic` không load patterns; cross-role path bypass theo `family_id`
6. **Case còn yếu trên constructed suite**: `CONSTRUCT-NARRATIVE-VS-TABLE` — extraction OK nhưng fusion chưa confirm multi-source (numeric equivalence narrative↔table)
7. **Hardest mismatch đã giải quyết**: EN/KR scope label, grade normalization, governance numeric form — qua family-level patterns trong equivalence registry
8. **Natural probes**: không đổi — vẫn **100% corpus_limited** (đúng kỳ vọng, không chase demo score)
9. **Bước tiếp**: harden fusion narrative↔table + canonical equivalence; giữ constructed suite làm regression gate trước plug-in tài liệu thật

## Cross-doc core capability benchmark (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_crossdoc_core_capability_20260619-100639/`
2. **Harness**: `data/enterprise_docs/crossdoc_capability_cases.jsonl` — **9 constructed** + **13 natural** holdout probes
3. **Code**: `src/enterprise_docs/crossdoc_case_builder.py`, `crossdoc_capability_benchmark.py`, `scripts/run_enterprise_docs_crossdoc_core_capability.py`
4. **Constructed capability metrics** (proxy/heuristic, không trộn production benchmark):
   - `alias_normalization_success_rate`: **50%** (1/2) — Scope3 alias OK; net-zero year 2050≠2030 đúng nhưng case alias fail do pair logic
   - `cross_doc_equivalence_match_rate`: **33.3%** (1/3) — A vs A+ không collapse (đúng); một số canonical case chưa pass
   - `cross_role_extraction_alignment_rate`: **0%** (0/6) — **gap hệ thống rõ**: `probe_candidates_in_units` không bắt được synthetic cross-role text (Scope3 EN/KR, grade A, board count, narrative vs table)
   - `evidence_fusion_success_rate`: **50%** (3/6) — conflict/single-source cases pass expectation; multi-source positive cases fail do extraction
   - `conflict_classification_accuracy`: **33.3%** (2/6)
   - `conflict_resolution_readiness_rate`: **16.7%** (1/6) — proxy `resolution_status resolved*`
   - `single_source_to_multi_source_promotion_rate`: **100%** (6/6) — promotion heuristic pass; **không** đồng nghĩa fusion thật
5. **Natural overlap cases** (13 quant holdout probes):
   - `candidate_found_rate`: **30.8%** (4/13)
   - `corpus_limited_rate`: **100%** — mọi natural fail đều gán `corpus_limited_*`, **không** `system_extraction_or_equivalence_gap`
   - `by_failure_mode`: `corpus_limited_no_candidate` **9**, `corpus_limited_single_logical_doc` **4**
6. **Tách bạch corpus vs capability**:
   - Natural metrics thấp → **giới hạn demo corpus** (thiếu overlap metric thật), không phải parser/routing cơ bản
   - Constructed extraction **0%** → **gap capability thật** cần harden trước khi plug-in tài liệu doanh nghiệp
7. **Family tốt nhất trên constructed pipeline**: `environment_ghg` (fusion success cao nhất trong matrix)
8. **Conflict handling**: classification mạnh hơn resolution; promotion path pass nhưng không bù extraction gap
9. **Bước tiếp**: harden cross-role extraction patterns + equivalence registry trên constructed suite; giữ benchmark làm regression gate; khi có tài liệu thật chỉ thêm natural cases — **không** rebuild pipeline; **không** ưu tiên source acquisition làm workstream chính

## Overlap strengthening (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_overlap_strengthening_20260619-095735/`
2. **Registry**: `data/enterprise_docs/metric_overlap_registry.json` — logical-doc pairs, canonical keys, pair bridge aliases, source_limitations
3. **Code**: `overlap_strengthening.py`; merge bridges vào `semantic_bridge()`; multi-doc `matching_corpus_documents_for_logical()`; full-text narrative search; `values_equivalent()` trong aggregator
4. **Overlap system metrics** (12 quant probes, sau bridge):
   - `logical_doc_overlap_rate`: **0%** (không tăng vs family-scoped round)
   - `candidate_overlap_rate`: **0%**
   - `single_source_only_rate`: **33.3%** (tăng — nhiều probe có candidate ở 1 logical doc)
   - `zero_overlap_rate`: **66.7%**
5. **`multi_source_confirmed`**: **0%** — đã reject presence-style inflate cho quant probes (`present` ≠ numeric confirm)
6. **Coverage holdout**: **22.2%** — flat vs family_scoped; cải thiện extraction chưa đủ tạo cross-doc numeric confirm
7. **musinsa**: `source_limited` — không thể tạo overlap thật từ package hiện có (chỉ annual report xml)
8. **hanssem**: tiềm năng overlap **partial** — SR PDF mạnh; DART ESG xml chủ yếu TOC/metadata, không body metric
9. **Bước tiếp**: **Done** — superseded bởi crossdoc capability benchmark; không lấy source acquisition làm workstream chính

## Family-scoped retrieval pool (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_family_scoped_retrieval_20260619-094309/`
2. **Policy**: `data/enterprise_docs/family_retrieval_pool_policy.json` — pools `sr_pdf`, `dart_governance_xml`, `dart_esg_sustainability_xml`, `annual_report_workforce_xml`, `impact_html`; family→pool mapping + `company_pool_overrides.musinsa`
3. **Implementation**: `src/enterprise_docs/family_retrieval_pool.py`; per-record filter trong `structured_esg_mapper` khi `holdout_corpus=family_scoped`; union artifact `corpus_units_family_scoped.jsonl`
4. **Pool matrix thực tế** (trên filtered base):
   - hanssem: `governance` pool **864** units (SR PDF 598 + DART xml 266); `environment_ghg` **624**; `employee_headcount` **598**
   - musinsa: mọi family **308** units (chỉ `annual_report_workforce_xml`); `sr_pdf`/`dart_esg`/ `impact_html` = **0**
5. **Holdout 3-lane compare** (18 cases):
   - reingested full: **22.2%**
   - filtered scoped: **22.2%**
   - family_scoped pool: **22.2%** — **không tăng aggregate** so với filtered
   - hanssem family_scoped: **36.4%** (4/11); musinsa: **0%** (0/7)
6. **`logical_doc_overlap_rate` theo family** (quant probes, family pool scan):
   - `employee_headcount`: **0%** multi-doc; **100%** zero overlap
   - `environment_ghg`: **0%** multi-doc; **25%** single-doc-only (HOLDOUT-007 chỉ `doc_sr_narrative`)
   - `governance`: **0%** multi-doc; **100%** zero overlap
   - aggregate: **0%** — không có probe nào có candidate ở ≥2 logical docs
7. **`multi_source_confirmed` vẫn 0%** — blocker chính: **`corpus_lacks_real_multi_logical_doc_metric_overlap`** (không phải aggregation policy chặn giả)
8. **musinsa**: pool có 308 units nhưng coverage 0% → vấn đề **thiếu source slice mạnh** (SR PDF, DART ESG xml, impact html) hơn là family policy sai hoàn toàn
9. **Bước hệ thống tiếp theo**: overlap strengthening — alias/bridge giữa SR PDF pool và DART ESG xml pool trên cùng metric; chưa LangGraph/synthesis

## Retrieval scope narrowing (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_retrieval_scope_narrowing_20260619-092751/`
2. **Scope policy**: `data/enterprise_docs/retrieval_scope_policy.json` — slices `sr_pdf_only`, `governance_dart_xml`, `no_web_crawl`, `structured_esg_retrieval_ready`; company override cho `musinsa` (사업보고서 xml)
3. **Filtered corpus**: hanssem **864** units (9 docs: SR PDF + DART ESG xml); musinsa **348** units (6 docs: 사업보고서 xml)
4. **Holdout comparison** (18 pilot cases, cross-doc probe path mở trên 11 quant probes):
   - baseline narrative: coverage **38.9%** (giảm vs vòng re-ingest do cross-doc routing)
   - reingested full: **22.2%**
   - filtered scoped: **22.2%** aggregate; **hanssem +9.1pp** vs full reingest; **musinsa −14.3pp**
5. **Scope slice hữu ích nhất (hanssem)**: SR PDF **772** units; combined slice **864**; governance DART xml **326**
6. **`multi_source_confirmed` vẫn 0%** — 11 cross-doc probes kích hoạt nhưng **insufficient_cross_doc_support 44%** → blocker **logical-doc overlap / extraction cross-role**, không phải aggregation taxonomy
7. **Family hưởng lợi nhiều nhất**: `governance` (+11pp filtered vs full reingest trên holdout)
8. **Bước tiếp**: family-scoped retrieval pool theo logical doc; tăng overlap SR PDF ↔ DART ESG xml trên cùng metric

## Structured ESG re-ingest + cross-doc surface (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_structured_esg_reingest_20260619-091843/`
2. **Re-ingest thật**: `holdout_reingest.py` + `corpus_units_reingested.jsonl` — 한샘 **45,266** units / **170** docs; 무신사 tương tự từ package inventory
3. **Parser v1.1 tạo giá trị thật** trên format đúng: reingested `by_format.pdf` coverage **100%** (3/3 case khi retrieval trúng SR PDF) — không chỉ audit readiness
4. **Net holdout coverage giảm** so với golden narrative baseline:
   - hanssem: **45.5% → 27.3%** (−18.2pp)
   - musinsa: **28.6% → 14.3%** (−14.3pp)
   - Nguyên nhân chính: **retrieval dilution** — full package gồm DART xml lớn + web crawl html làm BM25 top units không còn narrative sạch như golden
5. **Holdout cases không có `source_format`** (bucket `narrative_holdout`) → **100% metric_absent** trên 20 case — extraction không chạy vì retrieval miss SR/governance slice
6. **`multi_source_confirmed` vẫn 0%** — holdout probes `force_single_doc_quant`; demo cross-doc vẫn thiếu cùng metric ở ≥2 logical docs sau alias expansion
7. **Family cross-doc surface** (registry-level): mở rộng `environment_ghg`, `governance_narrative`, `financial_en_bridge` → hanssem/musinsa; `semantic_bridge` merge đa family; governance anchor theo company
8. **Bước hệ thống tiếp theo**: retrieval scope narrowing (ưu tiên SR PDF + DART governance xml, loại web noise) trước khi đo lại cross-doc

## Structured ESG hardening (2026-06-19) — executed

1. **Artifact**: `reports/enterprise_docs_structured_esg_hardening_20260619-090700/`
2. **Parser v1.1**: html +0.23, xml +0.20, pdf +0.13 readiness (weak → adequate)
3. **`esg_field_normalizer.py`**: plan domain/category vào record; esg_field_mapping **100%**
4. **Cross-doc infra**: `_confirming_logical_docs`, role-corpus scan, conflict taxonomy v1.1
5. **`multi_source_confirmed` vẫn 0%** — debug QUANT-0208: chỉ 1 logical doc có candidate; blocker **extraction**, không phải aggregation
6. **Coverage chưa tăng** vì holdout corpus chưa re-ingest bằng parser mới

## Structured ESG hardening planning (2026-06-19)

1. Artifact `reports/enterprise_docs_structured_esg_20260618-174141/` da danh dau dung pha uu tien: tu retrieval/evidence sang `structured ESG records`
2. Markdown/demo path da chung minh pipeline co the di den output co cau truc; holdout mixed-format van la diem nghen chinh
3. `format_parse_coverage=71.4%` cho thay parser co do phu co ban, nhung html/xml/pdf van con qua yeu de coi la lane san sang cho tai lieu doanh nghiep that
4. `structured_record_coverage` chenh lech giua `demo_company`, `hanssem`, `musinsa` cho thay bai toan ke tiep khong phai downstream handoff, ma la do on dinh cua `document -> field/value/evidence`
5. `multi_source_confirmed=0%` nghia la cross-document conflict taxonomy da co, nhung chua co du aggregator/evidence packing de xac nhan metric tren nhieu nguon mot cach that su
6. Vi vay pha tiep theo hop ly nhat la `structured_esg_hardening`: parser strengthening + ESG field mapping robustness + cross-doc aggregation confirmation; khong mo LangGraph/runtime

## Structured ESG output evaluation (2026-06-18)

1. **Artifact**: `reports/enterprise_docs_structured_esg_20260618-174141/`
2. **Trọng tâm**: quay lại `document → structured ESG data` — LangGraph handoff **không** ưu tiên
3. **Format audit**: markdown **strong** (0.85); csv/json **adequate**; html/xml/pdf **weak** — ưu tiên strengthen html/xml/pdf
4. **ESG schema**: `esg_target_schema.json` — 20+ fields, family→domain mapping 100% trên pilot
5. **Structured output** (36 records, 3 pilot families):
   - demo: structured_record_coverage **66.7%**
   - hanssem: **54.5%**; musinsa: **28.6%**
   - environment_ghg mạnh nhất (71.4%); governance yếu hơn (44.4%)
6. **Conflict**: taxonomy rõ (`metric_absent`, `single_source_sufficient`, …); cross-doc cases **7**; conflict_rate **0** (chưa có numeric clash trên subset)
7. **Gap chính**: holdout narrative corpus → metric_absent cao; multi_source_confirmed **0%** — cần cross-doc aggregation sâu hơn

## LangGraph handoff preparation (2026-06-18)

1. **Artifact**: `reports/enterprise_docs_langgraph_handoff_prep_20260618-172234/`
2. **Contract**: `data/enterprise_docs/langgraph_handoff_contract.json` — 3 pilot families với prep gate 3 trạng thái (`handoff_allowed_for_preparation`, `handoff_blocked`, `needs_manual_review_before_handoff`)
3. **Payload schema**: `handoff_payload_schema.json` — 5 nhóm field (identity, readiness, answer, evidence, review_control)
4. **Review owner policy** v1.1.0 (`review_owner_policy.py`): RAG / SME / Dataset / None — priority-ordered rules
5. **Kết quả prep round** (không runtime trial):
   - total `handoff_allowed_for_preparation`: **16** (demo 6, hanssem 6, musinsa 4)
   - blocked: **29**; review-required: **0**
   - holdout prep allowed: **10** trên 3 pilot families
6. **Dominant blocker**: `package_blocker` (missing value/bundle/confidence trên case chưa promote)
7. **Trial**: `recommend_trial=false` — contract đủ cho design review, chưa đủ sign-off runtime

## Holdout handoff enablement (2026-06-18)

1. **Artifact**: `reports/enterprise_docs_holdout_handoff_enablement_20260618-171016/`
2. **Root cause holdout 100% coverage_gap** (đã fix):
   - `path_hint` không khớp `Company_Evidence_*` corpus IDs → `corpus_match_tokens` v1.3.0
   - Multi-primary routing → cross_doc trên narrative corpus → `holdout_routing.force_single_doc_quant`
   - `build_index_from_units` không truyền `company_id` → logical_map rỗng (bug chính)
   - Narrative confidence=0 → `confidence_policy.resolve_extraction_confidence`
3. **Kết quả sau enablement**:
   - holdout promote **10/27** (37.04%); demo giữ **6/18**
   - hanssem: 6 promoted; musinsa: 4 promoted
   - Cả 3 pilot family có promote trên holdout: env 3, gov 4, emp 1
4. **Gate**: `ready_for_limited_langgraph_handoff_preparation=true`; trial vẫn **false**
5. **Blocker còn lại**: qualitative probes, retrieval_ready quant chưa extract, confidence calibration, review_owner

## Handoff readiness preparation — enterprise internal-doc (2026-06-18)

1. **Artifact**: `reports/enterprise_docs_handoff_readiness_20260618-165702/`
2. **Family handoff schema** (`family_handoff_registry.json` v1.0.0): 3 pilot families với `required_readiness_state=single_source_sufficient`, `required_evidence_count=1`, `confidence_rule` (table 0.85 / narrative 0.25), `handoff_blockers`, `review_owner_rule`.
3. **Promotion logic** (`handoff_readiness.promote_readiness`): chỉ promote từ `extraction_ready`/`retrieval_ready`/`aggregation_ready` khi package đủ; **không** promote từ `coverage_gap`/`needs_sme_review`/`honest_abstain`/qualitative.
4. **demo_company (dev)**: 18 case pilot → promote **6**, `single_source_sufficient` after **12**, `handoff_candidate` **12** (promotion rate 0.33).
   - `employee_headcount`: promote 1 (QUANT-0001)
   - `environment_ghg`: promote 4; 6 handoff_candidate
   - `governance`: promote 1; 5 handoff_candidate (3 từ aggregator path sẵn có)
5. **Holdout gate (hanssem 16 + musinsa 11)**: full pipeline → **100% `coverage_gap`**; promote **0**; handoff_candidate **0**.
   - Root cause: `assess_readiness` diagnostics vs narrative SR corpus — khác feasibility harness (extraction avg 0.6 ở vòng trước).
   - Một số case có `predicted_value` nhưng `confidence=0.0` và readiness vẫn `coverage_gap`.
6. **System decision**: `ready_for_limited_langgraph_handoff=false`; `ready_for_limited_langgraph_handoff_preparation=false`; `not_ready_for_synthesis=true`.
7. **Gap trước trial**: holdout evidence packaging, confidence policy trên narrative extract, formal `single_source_sufficient` trên holdout, review_owner enforcement.

## Enterprise internal-doc generalization (2026-06-18)

1. **Rule inventory** (`data/enterprise_docs/rule_inventory.json`): 27 rules — 13 reusable generic, 7 pilot-only, 3 pattern-specific, 2 coverage/abstain, 2 synthesis-blocker.
2. **`reusable_system_coverage=0.48`** — thấp hơn dataset_excel lane (0.89) vì nhiều rule gắn RTX 7-step / demo mapping.
3. **Readiness model** (`readiness_model.py`): 9 trạng thái chuẩn; áp dụng demo_company 35 cases:
   - quant: `single_source_sufficient` 6, `extraction_ready` 8, `retrieval_ready` 14, `honest_abstain` 1
   - qual: `not_ready_for_synthesis` 5 (100%)
   - `synthesis_gate_allowed_rate_quant=0.23` — chưa đủ mở generative
4. **Holdout sanity 한샘** (8 probes, narrative corpus 15 units):
   - parser **1.0**, retrieval feasible **0.875**, extraction feasible **0.375**
   - BM25 generic reuse OK; `ED-MAP-001` và narrative patterns cần abstraction
5. **Reusable thật**: parser, ingest, BM25 retrieval, row scoring, conflict resolve, sufficiency taxonomy, fail taxonomy, honest abstain.
6. **Pilot-only / corpus-specific**: `DEMO_DOCUMENTS`, `CORPUS_DOC_PATTERNS`, `ROW_ALIASES`, `SEMANTIC_BRIDGE`, `GOVERNANCE_ANCHOR`, CSV boost, narrative probe.
7. **Architecture**: có thể mở rộng holdout 한샘/무신사 có kiểm soát; **chưa** mở synthesis; ưu tiên `abstraction_rule_registry`.

## Aggregation sufficiency taxonomy — demo_company (2026-06-18)

1. **Sufficiency taxonomy** (`evidence_aggregator.py`, `pilot_only`):
   - `missing_numeric_role`: role required nhưng corpus có metric nhưng chưa extract được
   - `metric_absent_in_role`: role optional/supporting không chứa metric trong corpus (probe)
   - `single_source_sufficient`: metric chỉ có ở 1 nguồn authoritative (`doc_06_governance` financial EN table)
2. Output mới: `sufficiency_status`, `sufficiency_reason`, `required_roles`, `optional_roles`, `roles_with_metric`, `roles_absent_by_design`, `missing_numeric_roles`.
3. Benchmark (`reports/demo_company_aggregation_sufficiency_20260618-150423/`):
   - Cross quant: `quant_aggregation_success_rate=0.7` (Δ +0.5 vs 144715)
   - `resolved_single_source_sufficient_rate=0.6`
   - `aggregation_partial_rate=0.0` (Δ -0.27)
   - `missing_numeric_role_rate=0.0`, `wrong_row_risk_count=0`
   - `narrative_metric_parse_success_count=1` (QUANT-0133 환경투자액 → 20.8)
4. Focus cases:
   - **0208/0209/0210/0213**: partial → `resolved_single_source_sufficient` (doc_06 anchor; doc_01/CSV absent by design)
   - **0133**: narrative probe `doc_01_business` → success 20.8 (không cần multi-role GHG/renewable)
   - **0044**: `metric_absent` — 복리후생 không có trong planned corpus
   - **0046**: `not_disclosed_honest_fail` — giữ nguyên
5. Metric `metric_absent_in_role_rate=1.0` là **heuristic proxy** (mọi quant case đều có ít nhất 1 role absent by design sau reclassify) — không đồng nghĩa fail.
6. Bottleneck chuyển từ aggregation semantics sang **extraction gap trên metric không có trong corpus** (0044) và **honest not_disclosed** (0046).
7. `open_synthesis=false`; chưa chuyển 한샘/무신사.

## Bridge + table-first + narrative parse — demo_company (2026-06-18)

1. **EN↔KR semantic bridge** (`SEMANTIC_BRIDGE`, pilot_only): map KR item → EN row label exact/near-exact; output `semantic_bridge_used`, `bridge_reason`.
2. **Table-unit-first retrieval**: inject table units (`|`) trước narrative bullets cho financial/metric questions; log `table_unit_preferred`, `table_candidates_seen`.
3. **Narrative metric parse**: pattern `투자액: USD X million`; output `narrative_metric_parse_used`, `normalized_numeric_value`, `normalized_unit`.
4. Benchmark (`reports/demo_company_bridge_table_parse_20260618-144715/`):
   - Single: `success_on_ready=0.8`, `wrong_row_risk=0` (giữ trung thực)
   - Cross quant: `quant_aggregation_success=0.2` (không đổi — partial không tính success)
   - `aggregation_partial_rate=0.27` (↑ từ 0.07) — financial cases có resolved value nhưng thiếu numeric từ mọi role
   - `table_unit_hit_rate=0.7`, `semantic_bridge_usage_count=4`, `missing_role_rate=0`
5. Focus cases:
   - **0208/0209/0210/0213**: extraction **SUCCESS** qua bridge (`Capital expenditures`, `Interest expense`, `Defined contribution`, `Income tax expense`); aggregation **partial** (chỉ `doc_06_governance` có row)
   - **0046**: honest fail `source_not_disclosed_for_metric` (đúng nguồn)
   - **0044**: vẫn fail — không có row 복리후생 trong planned docs
6. Bottleneck chuyển từ "không parse được EN row" sang **multi-role numeric coverage trong aggregator**.
7. `open_synthesis=false`; khóa tiếp `demo_company`.

## Row disambiguation + conflict resolution + role-aware retrieval — demo_company (2026-06-18)

1. **Row disambiguation** (`structured_extractor.py`): `score_row_match()` strong→weak (item/subcategory/alias/token); `GENERIC_TOKENS` penalty; output `row_match_score`, `row_match_reason`, `top_row_candidates`, `wrong_row_risk`.
2. **Conflict resolution** (`evidence_aggregator.py`): primary doc preference; filter `Not disclosed` khi co numeric; `resolved_value`, `resolution_status`, `resolution_reason`, `primary_doc_used`.
3. **Role-aware retrieval** (`cross_doc_retriever.py`): sub-query theo role; CSV boost `pilot_only`; `role_coverage`, `role_hits`, `missing_roles_after_retrieval`, `csv_role_hit`; table-unit boost.
4. Benchmark (`reports/demo_company_resolution_retrieval_20260618-143749/`):
   - **Single:** `single_extraction_success_rate_on_ready=0.8` (giam tu 1.0 — **trung thuc hon**, khong con wrong-row parse); `wrong_row_risk_count=0`
   - **Cross quant:** `quant_aggregation_success_rate=0.2` (giam tu 0.5 — nhieu case cu la false positive do loose row match)
   - **Cross:** `aggregation_conflict_rate=0.0` (giam tu 0.2); `quant_resolution_rate=0.3`
   - **Retrieval-aware:** `role_coverage_rate=1.0`, `csv_role_hit_rate=1.0`, `missing_role_rate=0.0` (retrieval layer)
5. Case cai thien ro:
   - `QUANT-0001`: `구성원 총 교육 시간` → `총 임직원` (alias `총 구성원 수`)
   - `QUANT-0006`: `총 임직원` → `정규직 직원 비율` 98.4%
   - `QUANT-0042`: conflict → success (`primary_doc_best_row_match`)
6. Case van fail: cross quant financial (`0208/0209/0210/0213`), `0044` 복리후생, `0133` 환경투자, `0046` 육아휴직 (Not disclosed trong source).
7. **Chua** mo synthesis (`open_synthesis=false`); bottleneck lon nhat: **extraction** (cross-doc EN table row + narrative).

## Extractor + aggregator pilot — demo_company (2026-06-18)

1. `structured_extractor.py`: table/CSV-ish numeric parse; pilot-only row aliases.
2. `evidence_aggregator.py`: collect candidates per doc/role; conflict `not_disclosed_vs_numeric`; status success/partial/conflict/failed.
3. Metric (`reports/demo_company_extractor_aggregator_20260618-142543/`):
   - **Single (20):** `single_extraction_success_rate_on_ready=1.0` (10/10 ready) — **proxy only** (parseable, khong co gold)
   - **Single all:** `0.5` — 10 fail do `retrieval_gap` (chua ready)
   - **Cross quant (10):** `quant_aggregation_success_rate=0.5` (5/10 success)
   - **Cross all (15):** aggregation success **0.33**, conflict **0.2**, partial **0.13**, missing_role **0.47**
4. Fail taxonomy sau pilot:
   - Single: 10 `retrieval_gap` (chua ready), 0 `extraction_gap` tren ready group
   - Cross quant: 5 success, 3 conflict (0042/0044/0046), 2 partial (0134/0213)
5. Honest limit: `QUANT-0001` extract duoc so nhung **sai row** (`구성원 총 교육 시간` vs `총 임직원`) — can them row disambiguation / gold check truoc khi tin success rate.
6. Aggregator bien cross-doc tu retrieval-only sang mergeable evidence **mot phan** — conflict detection that hon heuristic cu.
7. **Chua** mo synthesis/generative (`open_synthesis=false`).

## Enterprise cross-doc diagnostic v1 — demo_company (2026-06-18)

1. Eval subset chot tay: **20 single** + **15 cross** (`eval_subset_*.jsonl`) — heuristic plan chi la bootstrap.
2. `cross_doc_retriever`: BM25 + lexical + planned-doc boost (single) / diversify (cross).
3. Diagnostic run (`20260618-141731`):
   - **Single:** `doc_hit_at_1=0.85`, `doc_hit_at_k=0.9`, `unit_hit_at_k=0.55`, `single_doc_ready_rate=0.5`, `parser_fail_rate=0`
   - **Cross:** `multi_doc_recall=0.86`, `evidence_plan_coverage=0.86`, `aggregation_readiness=1.0`, `cross_doc_ready_rate=0.87`
4. Fail taxonomy: `parser_gap`, `retrieval_gap`, `aggregation_gap`, `synthesis_gap`, `coverage_gap` — qualitative thuong `synthesis_gap` khi chua full doc coverage.
5. Bottleneck thuc te tren subset:
   - Single: doc routing da tot hon sau primary boost; **unit signal** (`unit_hit_at_k`) va answer extraction la blocker tiep theo
   - Cross: retrieval/doc recall kha tot tren demo nho; **aggregation/synthesis** chua implement — `conflict_detected_rate=1.0` la heuristic noisy (Not disclosed + numeric)
6. **Chua** sang synthesis/generative — cross qualitative can aggregator truoc.
7. 10 single ready (pilot answer): QUANT-0001, 0006, 0028, 0146, 0151, 0200, 0083, 0126, 0017, 0031.

## Enterprise internal-doc lane v1 — demo_company (2026-06-18)

1. Lane moi `src/enterprise_docs/` tach rieng khoi `src/dataset_excel/`; khong sua goldns/emni benchmark v5.
2. Ingest prototype:
   - `demo_company` RTX 7-step: **7** MD + **1** CSV evidence → **47** `EvidenceUnit` (`corpus_units.jsonl`)
   - Parser ho tro: md/html/json/csv/pdf (prototype); stub cho Word/PPT/OCR chua implement
3. Phan loai cau hoi heuristic (`classify_demo_company_questions.py`):
   - Tong **278** (quant **251**, qual **27**)
   - `single_document_answer`: **151** (quant 151)
   - `cross_document_answer`: **127** (quant 100 + qual 27)
   - Qualitative: **100%** cross-doc (narrative span nhieu file)
4. Inventory file thuc te (`file_inventory.json`):
   - `demo_company`: 23 file (md 16, pdf 4, json 2, csv 1) — co ban trung lap TalkFile zip
   - `한샘_일반자료_20260430`: **170** file — chu yeu html/json/md/pdf
   - `무신사_일반자료_20260430`: **122** file — tuong tu, phu hop stress-test parser vong 2
5. Evidence plan artifact: `question_evidence_plans.jsonl` — moi cau co `primary_document_ids`, `roles`, `needs_merge`, `needs_conflict_resolution`
6. Bottleneck du doan (uu tien): cross-doc retrieval > aggregation > synthesis > parser (tren demo MD)
7. Reuse tu lane Dataset-Excel: chunking pattern, fail taxonomy, review owner model, rule **families** (employee/financial/governance) — khong reuse hardcode DART/goldns

## Role alignment + internal-document preparation (2026-06-18)

1. Nhan dinh moi cua sep phu hop voi huong repo hien tai:
   - Team Dataset: thu thap/sap xep du lieu cong khai
   - Team RAG: xu ly tai lieu doanh nghiep/noi bo thanh du lieu co cau truc, sau do handoff cho LangGraph
2. Workstream Dataset-Excel hien tai moi cover tot nhat bai toan:
   - `dataset-provided gold + source`
   - answerable/abstain eval
   - reusable rule accumulation
   Chua cover day du lane `document-to-structured-data` cho file doanh nghiep da nhan truc tiep.
3. Trong `C:\Users\nguye\Downloads\data-company` da co mau du lieu phu hop de nghien cuu truoc khi nhan data noi bo that:
   - `demo_company`: bo `7step_dataset` Markdown + PDF reference RTX, hop cho test multi-document synthesis co kiem soat
   - `한샘_일반자료_20260430`: co tap lon `PDF/XML/HTML/JSON/MD`, gan voi bai toan doanh nghiep thuc te
   - `무신사_일반자료_20260430`: co `PDF/XML/HTML/JSON/MD`, phu hop lam holdout thu hai
4. Rui ro lon nhat sep neu la dung:
   - Retrieval/extraction 1 tai lieu don co the on
   - nhung cau hoi can tong hop tu nhieu tai lieu (`cross-document retrieval`) de roi vao 3 loi:
     - top-k lay dung tung manh nhung khong gom thanh cung fact plan
     - evidence conflict/duplicate giua cac tai lieu
     - answer dung tung phan nhung khong dat duoc cau tra loi tong hop cuoi
5. Nghia la buoc tiep theo hop ly khong phai tang diem tren 2 workbook hien tai, ma la mo lane thu nghiem:
   - ingest mixed-format documents
   - build evidence graph/doc-plan nhe
   - danh gia cau hoi multi-source

## RAG vs gold comparison workbook UX (2026-06-18)

1. Cai thien export script — khong doi RAG results/metrics
2. Sheet moi: `review_guide`, `review_all_non_green` (6), `review_semantic_ambiguity` (4), `review_coverage_gap` (2), `review_retrieval_miss_answer_ok` (4)
3. Cot review moi: `retrieval_review_status`, `review_priority`, `review_bucket`, `needs_*`, `review_owner_hint`, `top1_vs_gold_doc_match`, `source_gap_reason`, `business_meaning_note`
4. `comparison_status` giu nguyen; retrieval miss tach rieng qua `retrieval_review_status` + sheet rieng
5. Summary: safe ignore **524** vs needs review **6**; breakdown theo bucket/owner/priority

## RAG vs gold comparison workbook (2026-06-18)

1. Script: `scripts/export_goldns_emni_rag_comparison_workbook.py`
2. Output: `reports/goldns_emni_rag_vs_gold_comparison.xlsx`
   - Sheet `goldns_compare`, `emni_compare`, `summary`
3. Mapping: **100%** qua `source_row_index` (cung logic ingest `ingest_esg_excel_workbook.py`)
   - goldns: 251/251 rows
   - emni: 279/279 rows
4. `comparison_status` theo company:
   - **goldns**: MATCH 21, ABSTAIN_OK 227, SEMANTIC_AMBIGUITY 1, COVERAGE_GAP 2
   - **emni**: MATCH 40, ABSTAIN_OK 236, SEMANTIC_AMBIGUITY 3
5. Cac case retrieval_top1_miss nhung answer dung duoc gom vao SEMANTIC_AMBIGUITY hoac COVERAGE_GAP (uu tien diagnostic tag hon RETRIEVAL_MISS_BUT_ANSWER_OK)

## Generalization hardening — freeze v5 (2026-06-18)

1. Refactor rule system ra `src/dataset_excel/`:
   - `rule_registry.py` — **28 rules** phan loai 4 nhom
   - `family_router.py`, `extractors.py`, `retrieval.py`, `diagnostics.py`
   - `reusability_audit.py` — diagnostic view moi (khong doi metric v5)
2. Rule inventory (`data/dataset_excel/rule_inventory.json`):
   - `reusable_generic_rule`: 7
   - `pattern_specific_rule`: 14
   - `company_specific_rule`: 3
   - `semantic_or_coverage_exception`: 4
3. Diagnostic view tren 67 answerable:
   - `reusable_system_coverage`: **0.8955** (~60/67 cau dung reusable family, khong co exception tag)
   - `company_specific_dependency`: **0.1045** (FTC blocked, tax ambiguity, fair_trade tuning)
   - `reusable_family_answer_accuracy`: **1.0**
4. Pattern he thong da hoc (reuse cho cong ty DART + sanction portals tuong tu):
   - employee / executive / board_director / financial_* / sanction lanes / minimum_wage
5. Khong worth productizing: hardcode `question_id`, case boost chi de +score tren goldns/emni
6. Artifact:
   - `docs/NEW_COMPANY_ONBOARDING_RAG_20260618.md`
   - `reports/dataset_excel_reusability_audit.json`
   - Eval refactor verify: `reports/goldns_emni_rag_eval_20260618-100003/`

## Goldns/emni RAG benchmark v5 (2026-06-18)

1. Rule moi:
   - **safetykorea**: `_safetykorea_recall_list_empty()` — phat hien bang recall trong (pagination `< 1 >`, row `&nbsp;`), tra `0` thay vi bat so noise tu HTML
   - **financial_capex**: family `유형자산`+`취득` -> account `유형자산의 취득` trong `현금흐름표` (khong lay balance sheet `유형자산`)
   - **financial_tax distribution**: `abs(법인세비용)` khi quy doi sang 백만 원
2. Diagnostic tags bo sung: `coverage_gap`, `rule_extractor_gap` tach khoi fail_type co ban
3. Metrics tong (530 cau):
   - `retrieval_hit_top1`: **0.9403** (giong v4)
   - `answer_accuracy`: **1.0** (v4: 0.9254, **+0.0746**)
   - `overall_score`: **0.9702** (v4: 0.9515, **+0.0187**)
4. Theo company:
   - `emni`: retrieval **0.9535**, answer **1.0**
   - `goldns`: retrieval **0.9167**, answer **1.0**
5. Fail con lai (khong con `answer_fail`):
   - `semantic_ambiguity`: 4 (`emni-0236/0237/0238`, `goldns-0214`)
   - `coverage_gap`: 2 (`goldns-0237/0238` — FTC blocked)
   - `retrieval_top1_miss`: 4 (tat ca answer dung)
6. Blocker khong giai bang rule: FTC `case.ftc.go.kr` blocked

## Goldns/emni RAG benchmark v4 (2026-06-18)

1. Coverage goldns da bo sung tu Downloads (collector `output_restart_goldns_20260616`):
   - `2025_exctvSttus.json`, `2025_재무_OFS.json`, `2025_outcmpnyDrctrNdChangeSttus.json`
   - manifest `resolve_local_file_first.jsonl` goldns tang tu 2 len 5 local source
   - collect **17/17 ok** (emni 12 + goldns 5); corpus **660 units** (local 642 + web 18)
2. Lane `제재이력` da tach provenance:
   - `제재이력_safetykorea.json`, `제재이력_pipc.json` (FTC blocked giu backlog)
   - metadata `sanction_lane` + `canonical_doc_title`
   - retrieval match theo `source_url` domain khi gold van dung `doc_title=제재이력.json`
3. Report fail types (answerable):
   - `answer_fail`: 5
   - `retrieval_top1_miss` (tong): 4
   - `answer_correct_but_wrong_top1`: 2
   - `semantic_ambiguity`: 4
4. Metrics tong (530 cau):
   - `retrieval_hit_top1`: **0.9403** (v3: 0.8507, **+0.0896**)
   - `answer_accuracy`: **0.9254** (v3: 0.8955, **+0.0299**)
   - `overall_score`: **0.9515** (v3: 0.8992, **+0.0523**)
5. Theo company:
   - `emni`: retrieval_hit_top1 **0.9535**, answer_accuracy **1.0**
   - `goldns`: retrieval_hit_top1 **0.9167**, answer_accuracy **0.7917** (v3: 0.667 / 0.708)
6. Phan loai nguyen nhan fail goldns con lai:
   - **Logic**: `sanction_safetykorea` (3) — page HTML co so `1` noise, gold=0
   - **Logic**: `financial_generic`/`financial_tax` (2) — extractor account/sign
   - **Coverage**: FTC lane blocked — `goldns-0237/0238` answer dung nhung top1 la `pipc` lane
7. Semantic audit giu nguyen: `emni-0236/0237/0238`, `goldns-0214`

## Goldns/emni RAG benchmark v3 (2026-06-18)

1. Rule/extractor moi:
   - `board_director`: doc `outcmpnyDrctrNdChangeSttus`; `사외이사` -> `otcmp_drctr_co`; `사내이사` -> `drctr_co - otcmp_drctr_co`
   - `financial_tax`: `유보된 경제가치` -> `당기순이익` (포괄손익계산서); `경제적 가치 배분` -> `법인세비용`
   - `fair_trade_sanction`: tach khoi `board_director`; uu tien `제재이력.json`
2. Retrieval v3:
   - post-rerank theo family (outcmpny len truoc exctvSttus; financial year-match truoc)
   - penalize `제재이력`/`최저임금` cho family khong lien quan
   - expand evidence tu toan bo line trong cung `doc_title`+`year` khi extract financial/board
3. Metrics tong (530 cau):
   - `retrieval_hit_top1`: **0.8507** (v2: 0.7612, **+0.0895**)
   - `retrieval_hit_topk`: **0.8507** (v2: 0.8507)
   - `answer_accuracy`: **0.8955** (v2: 0.8657, **+0.0298**)
   - `overall_score`: **0.8992** (v2: 0.8470, **+0.0522**)
4. Theo company:
   - `emni`: retrieval_hit_top1 **0.9535**, answer_accuracy **1.0**
   - `goldns`: retrieval_hit_top1 **0.6667**, answer_accuracy **0.7083**
5. Fail con lai (7 answerable fail hoac retrieval_top1 miss):
   - `financial_tax` (4): chu yeu `goldns` thieu `재무_OFS` trong corpus
   - `board_director` (2): `goldns` thieu `outcmpnyDrctrNdChangeSttus` trong corpus
   - `generic`, `executive_diversity`, `minimum_wage`, `financial_revenue`, `financial_generic` (moi 1)
6. Semantic audit:
   - `emni-0236/0237/0238`: label tax nhung gold map `당기순이익` — extractor dung rule proxy, van log ambiguity
   - `emni-0237`: van giu SME note rieng

## Goldns/emni RAG benchmark v2 (2026-06-18)

1. Corpus representation da tach:
   - `search_text`: chi noi dung retrieval (khong prepend metadata header)
   - `evidence_text`: text hien thi/trich xuat
   - `metadata`: `company_id`, `doc_title`, `year`, `schema`, `source_url`, `file_url`, ...
2. Retrieval heuristic v2:
   - rule family theo keyword (`empSttus`, `exctvSttus`, `outcmpnyDrctrNdChangeSttus`, `재무_`, `최저임금`)
   - boost/penalty theo `year`, `doc_title`, `schema`
   - penalize manh `최저임금` cho cau khong lien quan
3. Answer extractor v2:
   - employee: tong, % gioi tinh, % regular, avg salary, salary ratio
   - executive: % nu giam doc
   - financial: map account + chon cot ky `제 NN 기` theo offset nam
   - minimum wage: lay cot monthly wage theo nam
   - khong fallback tra nguyen header chunk
4. Metric definitions v2 (hon thuc te hon v1):
   - `retrieval_hit_top1` / `retrieval_hit_topk`
   - `source_match_top1` / `source_match_topk` (alias, khong match bang `source_url` chung DART khi da co `doc_title`)
5. Metrics tong (530 cau):
   - `retrieval_hit_top1`: **0.7612** (v1: 0.2388)
   - `retrieval_hit_topk`: **0.8507** (v1 source_match 0.9851 bi phong)
   - `answer_accuracy`: **0.8657** (v1: 0.4627)
   - `abstain_accuracy`: **1.0**
   - `overall_score`: **0.8470** (v1: 0.6716)
6. Theo company:
   - `emni`: retrieval_hit_top1 **0.814**, answer_accuracy **0.907**
   - `goldns`: retrieval_hit_top1 **0.6667**, answer_accuracy **0.7917**
7. Fail clusters con lai:
   - `board_director` (7): chua co extractor chuyen biet; top-1 hay roi vao `exctvSttus`
   - `financial_tax` (5): account mapping chua khop label workbook (`세금 및 공과 + 법인세`)
   - wrong top-1 docs: `제재이력.json` (7), `2025 최저임금 고시` (3)
8. Semantic audit:
   - `emni-0237` van giu SME note; khong sua semantic o v2

## Goldns/emni RAG benchmark v1 (2026-06-17)

1. Da tao corpus build + eval runner:
   - `scripts/build_goldns_emni_chunked_corpus.py`
   - `scripts/run_goldns_emni_rag_eval.py`
2. Corpus output:
   - `data/corpus/20260617_goldns_emni/corpus_units.jsonl`
   - tong **532** units (`520` local records/chunks + `12` web chunks)
   - web lane skip/block: **6** (gom `case.ftc.go.kr` redirect loop)
3. Eval input:
   - `data/dataset_excel_eval_ready/20260617_goldns_emni/`
   - `answerable_gold` + `abstain_gold`, bo qua `needs_review`
4. Benchmark run dau tien:
   - artifact: `reports/goldns_emni_rag_eval_20260617-163805/`
   - snapshot: `reports/goldns_emni_rag_eval_latest.json`
5. Metrics tong:
   - `retrieval_hit_rate`: **0.2388**
   - `source_match_rate`: **0.9851**
   - `answer_accuracy`: **0.4627**
   - `abstain_accuracy`: **1.0**
   - `overall_score`: **0.6716**
6. Theo company:
   - `emni`: retrieval_hit **0.093**, answer_accuracy **0.3721**
   - `goldns`: retrieval_hit **0.5**, answer_accuracy **0.625**
7. Ghi chu metric:
   - `source_match_rate` cao vi top-k thuong chua dung `doc_title/file_url` khi corpus da du local JSON
   - `retrieval_hit_rate` thap hon nhieu, dac biet `emni`, cho thay top-1 chua on dinh
   - `abstain_accuracy=1.0` dat duoc vi tat ca row `abstain_gold` khong co `source_url/file_url`; baseline policy abstain khi gold khong co provenance — day la dung theo eval design nhung chua phai gate "phat hien insufficient tu noise retrieval"
8. Semantic audit:
   - `emni-0237` van can SME follow-up; khong tu chot dung nghiep vu

## Reprocess workbook `emni` sau khi user thay file Excel (2026-06-17)

1. User da thay file:
   - `C:\Users\nguye\Downloads\data-company\dataset-excel\이엠앤아이_Final_ESG_Data.xlsx`
2. Sau khi chay lai toan bo chuoi `ingest -> reconcile -> validate -> source prep -> local collect`, ket qua eval-ready khong doi so voi state da lam sach truoc do:
   - `emni`: answerable **43**, abstain **236**, needs_review **0**
3. Source intake prep chot o trang thai:
   - total unique source: **18**
   - `crawl_web`: **4**
   - `resolve_local_file_first`: **14**
4. Local JSON collect sau khi chay lai tren manifest moi nhat:
   - total **14**
   - ok **14**
   - fail **0**
5. Luc dau co mot do lech tam thoi `15/15` o local collect, nhung nguyen nhan la:
   - da tung chay `source prep` va `local collect` song song
   - collector doc manifest cu truoc khi source prep ghi xong
6. Sau khi chay lai rieng local collect tren manifest moi nhat, so lieu chot la:
   - **14/14 ok**

## Local source collector/parser cho lane `resolve_local_file_first` (2026-06-17)

1. Da tao script:
   - `scripts/collect_local_sources_from_manifest.py`
2. Input:
   - `data/source_intake_prep/20260617_goldns_emni/*/resolve_local_file_first.jsonl`
   - local JSON root:
     - `C:\Users\nguye\Downloads\data-company\dataset-excel`
3. Output:
   - `data/source_raw/20260617_goldns_emni_local/`
4. Moi source local sau khi collect co:
   - `source_manifest.json`
   - `extracted.txt` (text san sang cho chunking)
   - `records.jsonl` (record-level text)
   - `raw.json` (ban sao file goc)
5. Ket qua smoke test:
   - tong **14/14 ok**
   - `emni`: 12 source
   - `goldns`: 2 source
6. Schema parser hien tai:
   - `dart_financial_statement`
   - `dart_employee_status`
   - `dart_executive_status`
   - `dart_board_director_change`
7. Luu y slug artifact:
   - ten thu muc artifact dang strip ky tu Han trong `doc_title`, vi du `2024_재무_OFS.json` -> `2024_OFS.json`
   - metadata van giu `doc_title` goc day du
8. Audit semantic lien quan `emni-0237`:
   - trong `2024_재무_OFS.json`, gia tri `1487148638` xuat hien o account `당기순이익(손실)` / `ifrs-full_ProfitLoss`
   - chua thay bang chung trong file nay cho metric label workbook `세금 및 공과 + 법인세`
   - van giu note SME follow-up, khong tu dong chot dung nghiep vu

## Reconcile local financial JSON cho `emni` (2026-06-17)

1. User da bo sung them bo local JSON trong:
   - `C:\Users\nguye\Downloads\data-company\dataset-excel\output_restart_emni_20260617\output_restart_emni_20260617\이엠앤아이_일반자료_20260617\02_재무_신용`
2. O lane `DART_주요정보` co day du file nam `2024`.
3. O lane `DART_재무` khong co `2024_재무_CFS.json`, nhung co:
   - `2024_재무_OFS.json`
4. Ba row `needs_review` cua `emni` deu dang tro toi:
   - `2024_재무_CFS.json`
5. Sau khi doi chieu `2024_재무_OFS.json`:
   - `29699` map sach voi `ifrs-full_Revenue` / `수익(매출액)`
   - `749` map voi `dart_InterestExpenseFinanceExpense` / `이자비용`
   - `1487` xuat hien voi `ifrs-full_ProfitLoss` / `당기순이익(손실)`
6. Da them script:
   - `scripts/reconcile_dataset_excel_local_sources.py`
   de noi lai provenance cho cac row thieu local file.
7. Sau khi reconcile va chay lai validator:
   - `emni`: answerable **43**, abstain **236**, needs_review **0**
8. Ba `question_id` da duoc go khoi `needs_review`:
   - `emni-0226`
   - `emni-0230`
   - `emni-0237`
9. Luu y nghiep vu:
   - `emni-0237` da du provenance file va khong con bi validator chan
   - nhung metric label `세금 및 공과 + 법인세` dang co do lech nhe voi account match duoc trong OFS (`당기순이익(손실)`)
   - nen giu ghi chu SME follow-up neu sau nay can audit semantic chuyen sau

## Source intake prep sau khi co local JSON thuc (2026-06-17)

1. Rule cu cua `scripts/prepare_source_intake_from_registry.py` dedupe theo `source_url` truoc, nen:
   - neu mot filing page DART co nhieu file local khac nhau
   - mot local file co the bi nuot mat khoi manifest
2. Da sua 2 diem:
   - neu co `file_url` JSON thi xep `source_kind=collector_file_reference`, `recommended_action=resolve_local_file_first`
   - dedupe key uu tien `file_url` truoc `source_url`
3. Sau khi chay lai source prep:
   - `2024_재무_OFS.json` xuat hien dung trong `resolve_local_file_first`
   - source intake prep khong con che mat local JSON chi vi trung filing page URL
4. Source intake prep moi hien nghieng manh sang lane local JSON:
   - tong unique source: **18**
   - `crawl_web`: **4**
   - `resolve_local_file_first`: **14**
5. Nghia la tu diem nay:
   - web crawler chi dung cho URL public that su
   - DART JSON local phai di qua local collector/parser lane rieng

## Source raw download tu source manifest (2026-06-17)

1. Da tao script:
   - `scripts/download_sources_from_manifest.py`
2. Input:
   - `data/source_intake_prep/20260617_goldns_emni/all_sources_manifest.jsonl`
3. Output raw source:
   - `data/source_raw/20260617_goldns_emni/`
4. Ket qua download:
   - tong `crawl_web`: **9**
   - download `ok`: **8**
   - download `fail`: **1**
5. `safetykorea` fail o lan dau do:
   - `SSL: CERTIFICATE_VERIFY_FAILED`
   Sau khi patch fallback `requests_noverify` thi tai duoc.
6. `case.ftc.go.kr` van fail sau patch:
   - site tra `307` va redirect lai chinh no
   - da danh dau ro: `self_redirect_loop_blocked_by_site`
7. Raw HTML da co cho:
   - `5` DART pages
   - `1` minimum wage page
   - `1` PIPC page
   - `1` SafetyKorea page
8. Nguon chua co raw content:
   - `case.ftc.go.kr` (blocked by site)
9. Nguon chua nam trong web download lane:
   - `2` source `collector_file_reference` cua `emni`
   - can resolve local file hoac map lai URL goc truoc khi chunk chung

## Source intake / crawl prep tu source_registry (2026-06-17)

1. Da tao script:
   - `scripts/prepare_source_intake_from_registry.py`
2. Input cho script la:
   - `data/dataset_excel_intake/20260617_goldns_emni/*/source_registry.jsonl`
3. Tong so source unique sau dedupe:
   - **11**
4. Phan loai theo action:
   - `crawl_web`: **9**
   - `resolve_local_file_first`: **2**
   - `needs_review`: **0**
5. Phan loai theo source kind:
   - `web_dart`: **5**
   - `web_public`: **4**
   - `collector_file_reference`: **2**
6. `goldns` co **5** source, deu crawl web duoc.
7. `emni` co **6** source:
   - **4** crawl web duoc
   - **2** chi con `file_url` dang `colletor-ai/.../DART_재무/...json`, khong con `Source URL`
8. Hai source `collector_file_reference` cua `emni` hien khong nen dua vao crawler web; can:
   - map lai ve URL DART goc
   - hoac attach file raw noi bo neu da ton tai
9. Output da duoc tao tai:
   - `data/source_intake_prep/20260617_goldns_emni/`
10. Manifest moi da tach san theo company va theo action:
   - `crawl_web`
   - `resolve_local_file_first`
   - `needs_review`

## Validator + partitioner cho intake ESG Excel (2026-06-17)

1. Da tao script:
   - `scripts/validate_partition_esg_intake.py`
2. Script validate theo `question_id` va kiem tra:
   - duplicate trong `questions`
   - duplicate trong `gold_answers`
   - missing source row
   - `matched` nhung khong co source that su
   - `Not disclosed` co dung `abstain_expected` / `NOT_DISCLOSED` / `requires_abstain_when_missing`
3. Script xuat 3 tap:
   - `answerable_gold`
   - `abstain_gold`
   - `needs_review`
4. Ket qua cho `goldns`:
   - answerable **24**
   - abstain **227**
   - needs_review **0**
5. Ket qua cho `emni`:
   - answerable **40**
   - abstain **236**
   - needs_review **3**
6. Ca 3 row `needs_review` cua `emni` deu la:
   - `matched_missing_real_source`
   - co answer so, nhung thieu `Source URL/File URL` that su
   - doc title con lai: `2024_재무_CFS.json`
7. Output eval-ready da duoc tao tai:
   - `data/dataset_excel_eval_ready/20260617_goldns_emni/`
8. Cho benchmark chinh, nen chi dung:
   - `answerable_gold`
   - `abstain_gold`
   Va loai `needs_review` ra khoi main run.

## Intake 2 workbook ESG tu team Dataset (2026-06-17)

1. Hai workbook user dua co cung schema `ESG Results` 24 cot + `Coverage Summary`.
2. `골드앤에스_Final_ESG_Data.xlsx` co **251** row du lieu:
   - `matched`: **24**
   - `Not disclosed`: **227**
   - unique source registry thuc te: **6**
3. `이엠앤아이_Final_ESG_Data.xlsx` co **279** row du lieu:
   - `matched`: **43**
   - `Not disclosed`: **236**
   - unique source registry thuc te: **6**
4. Workbook `이엠앤아이` co **28** continuation rows theo nam, trong do 12 cot context dau dong bi de trong va phai fill-forward tu row truoc.
5. Co the xem `Disclosure status=Not disclosed` la mot dang gold answer hop le cho bai toan `abstain_expected`, khong nen bo row nay khoi bo eval.
6. Da tao script intake:
   - `scripts/ingest_esg_excel_workbook.py`
7. Da sinh artifact canonical vao:
   - `data/dataset_excel_intake/20260617_goldns_emni/goldns/`
   - `data/dataset_excel_intake/20260617_goldns_emni/emni/`
8. Moi company hien co:
   - `questions.jsonl/.csv`
   - `gold_answers.jsonl/.csv`
   - `sources.jsonl/.csv`
   - `source_registry.jsonl/.csv`
   - `manifest.json`
9. `source_registry` chi nen dedupe tren `Source URL` hoac `File URL` that su; khong nen tao pseudo-source cho dong `Not disclosed`.

## Repo refocus theo workflow Dataset -> RAG -> LangGraph (2026-06-17)

1. Mo ta 3 team cua user la **dung huong**, nhung repo hien tai bi lech entry flow vi con mang nhieu dau vet benchmark `RunPod/C2/H200`.
2. Bai toan nghiep vu dung cho team RAG la:
   - nhan bo cau hoi/gold tu team Dataset
   - crawl `Source URL`
   - chunk/index/retrieve/generate
   - cham voi `gold answer`
   - handoff ket qua co evidence/reliability flags cho team LangGraph
3. Team Dataset khong nen chi ban giao 1 workbook tong hop; can co 3 lop contract ro hon:
   - `questions`
   - `gold_answers`
   - `sources`
4. Neu khong tach `gold_answer` khoi `source_url`, team RAG se phai tiep tuc hardcode logic cham diem va provenance trong code.
5. Cac cot can bo sung cho bo 252 cau hoi:
   - `question_type`
   - `normalization_rule`
   - `expected_answer_language`
   - `requires_abstain_when_missing`
6. Phan phu hop voi scope hien tai cua repo:
   - `company_export_json`
   - `golden_set`
   - `evidence_api`
7. Phan lech scope va co the bo khoi entry flow:
   - docs/configs/scripts cho `RunPod/C2/H200`
   - co che nap `.env.c2`
8. Da tao tai lieu chot huong moi:
   - `docs/RAG_PIPELINE_OPERATING_MODEL_20260617.md`
9. README moi can tro thanh cua vao cho workflow nghiep vu hien tai, khong con dan user vao benchmark GPU archive.

## Repo cleanup truoc khi push (2026-06-12)

1. Co the xoa an toan nhom file thua ro rang:
   - `artifacts/tmp`
   - file zip trung noi dung voi lane raw (`06_rtx_references_raw.zip`)
   - HTML report sinh lai duoc
   - dump scan/debug `_diag_*`, `_v3_*`, `_st_*`
2. Mot so artifact RTX da superseded va da bi xoa:
   - `golden_set_candidate_generation_rtx_v1.md`
   - `golden_set_candidate_generation_rtx_v2_fact_specific.md`
   - `golden_set_manual_review_rtx_round2_prep.md`
   - va summary JSON tuong ung
3. Nen giu lai:
   - report Markdown/PDF chot cuoi
   - artifact RTX `v2.1`
   - lane RTX raw va chunk/current workbook
4. Van con 4 file dang o trang thai `D` trong `data/rag_dataset/05_company_export_json/...091409`:
   - `README.md`
   - `known_issues.md`
   - `manifest.json`
   - `schema.json`
   Neu khong chu dong xoa package cu thi khong nen commit xoa cac file nay theo.

## Bao cao cong viec ngay 2026-06-12 - sua theo luong Rayxion that (2026-06-12)

1. Bao cao ngay cho `Rayxion` khong nen mo ta nhu mot "bao cao cong ty" chung chung, ma phai ghi ro luong cong viec giua `team Dataset` va `team RAG`.
2. Dinh dang dau ra dung de stakeholder hieu la bo file bao cao co cau truc tuong tu package:
   - `C:\Users\nguye\Downloads\data-company\demo_company\rtx_7step_dataset\rtx_7step_dataset`
3. Package mau cho thay muc tieu la tao cac file theo nhom:
   - business extract
   - GHG / energy
   - renewable contracts
   - HR / safety
   - social contribution / human rights
   - governance / compliance
   - certifications
   - va them workbook cau hoi dinh luong
4. Bao cao ngay can noi ro: `team Dataset` tim nguon tai lieu, ban giao cho `team RAG`, sau do `team RAG` bien thanh bo file bao cao co cau truc; day la yeu cau rieng cua workstream Rayxion.
5. Phan `LangGraph API` can bam vao reliability flags (`retrieval_confidence`, `abstain_recommended`, `no_relevant_evidence`, `answerable_candidate`), khong chi noi chung chung la "sua API".
6. Phan `Golden Set` tren du lieu moi nen co so lieu thuc de tranh mo ta mo ho:
   - lane RTX moi: `10` file nguon
   - `2761` source corpus units
   - `2724` normalized units
   - `42` usable candidates o moc `v2.1`

## Bao cao 18 Korean/PDF (2026-06-12)

1. Phan `Y nghia cua dau viec Rayxion` da bi cat bo de bao cao gon hon va tranh lap y voi phan mo ta luong cong viec.
2. Da tao ban Korean rieng cho bao cao 18:
   - `reports/bao-cao-18-cong-viec-ngay-20260612-rayxion-langgraph-golden-set-ko.md`
3. Da export thanh cong:
   - `.html`
   - `.pdf`
4. Ban Korean van giu dung 3 trong tam:
   - Rayxion = luong `dataset -> report package`
   - LangGraph = reliability flags / generation guard
   - Golden Set = he thong dang duoc test lai tren du lieu moi

## RTX v2.1 review round 1 (2026-06-12)

1. Review restart trên v2.1 only — **không** dùng v1/manual legacy.
2. Input **42** → keep **22**, rewrite **7**, collapse **13**, reject **0**; reviewable **29**.
3. 0 reject — quality gates v2.1 giữ được; collapse chủ yếu duplicate fact/year cluster.
4. `manual_review_ready_flag=true` — đủ mở manual review prep.

## RTX v2.1 fact-quality rebuild (2026-06-12)

1. v2 sửa duplicate (0 exact) nhưng **317/327** rows fail quality audit (wording/mismatch/residue/overlong).
2. Ví dụ lỗi: Q04 ergonomic high vs disclosure medium; Q02 phrase extraction thô; Q06 residue `s Workforce`.
3. v2.1: canonical fact catalog + quality gates → **42** candidates, **42** unique questions, 0 post-audit errors.
4. Ưu tiên usability > count; `review_ready_flag=true` trên v2.1.

## RTX question layer reset + v2 fact-specific (2026-06-12) — superseded

1. **Root cause**: v1 có **11** unique `question_draft` cho **3170** rows (100% affected) — duplicate/over-generic question failure.
2. Manual round 2 polish **không sửa** backbone template; vẫn còn fallback `ESG metric or policy`.
3. v2 rebuild từ `corpus_units_rtx_normalized.jsonl`: **327** candidates, **327** unique questions, **0** exact duplicate.
4. Mỗi row có `fact_target` + `fact_target_type`; question bám fact cụ thể.
5. **Tạm dừng**: manual R2 execution, canonical, gold, benchmark — mở lại review R1 trên v2.

## RTX manual review round 2 prep (2026-06-12) — PAUSED

1. Không review phẳng **221** row — lane split: A **5**, B **202**, C **13**, reject recommended **1**.
2. Rewrite polish: **169** draft pipe-token (`foo|bar|baz`) → **0** sau polish; reviewer không cần sửa cơ học.
3. Lane C giữ table-heavy/10-K salvage (**13** row); Lane B là bulk review với `polished_question_draft` đã human-friendly hơn.
4. Ước lượng survivors tới canonical: **~162** (A 90% + B 75% + C 45%).

## RTX workbook review round 1 (2026-06-12)

1. Không nên manual review thẳng **3170** row — chỉ **11** unique `question_draft`, candidate inflation từ generic templates.
2. Auto-triage R1: keep **5**, rewrite **216**, reject **736**, collapse **2213** → **221** reviewable (~93% reduction).
3. Reject chủ yếu: `insufficient_esg_substance` (351), `generic_question_weak_grounding` (309) — contamination nặng đã ít (`high_noise` ~5 ở gen).
4. Collapse chủ yếu: generic template caps + table/governance duplicate clusters.
5. Coverage reviewable: `10k` 141, `proxy` 19, `appendix` 43, `data_table` 13, `questionnaire` 4 — đủ mở manual review R2.

## RTX Golden Set candidate gen v1 (2026-06-12)

1. Lane RTX moi **du tot** de test lai workflow Golden Set — khong can quay lai salvage bo cu.
2. Ground truth so luong tren disk: **2761** corpus units / **2762** chunks (khong lay tom tat mieng 2641).
3. Normalization nhe (`html.unescape`, mojibake repair, strip HTML residue) giam encoding noise; **17** unit co `&amp;`, **38** co HTML residue; drop **37** unit qua ngan sau clean.
4. Workbook-first RTX v1: **4116** raw → **3170** filtered candidates tu **1131** passages; yield **>>** lane v4 3-company (175 filtered) nhung corpus lon hon nhieu — can reviewer triage, khong hard-gate som.
5. Noise con lai: table markdown pipes trong excerpt CDP/appendix; SEC boilerplate mot phan van qua passage filter (`no_esg_substance` 1548 reject).
6. Ket luan: workbook RTX v1 **du mo review round 1**; uu tien Golden Set workflow truoc RAG ingest/index.

## RAG retrieve analysis - Musinsa metric question (2026-06-11)

1. Nhan dinh "giu noise, sua retrieve" la **dung huong** hon so voi viec coi `mss.go.kr` la blocker data layer. Neu dap an `1891명` da co trong package thi bai toan chinh la ranking duoi noise.
2. `src/rag_common.py`: `tokenize()` hien chi giu `[a-zA-Z0-9_]+` -> BM25 gan nhu **mu** voi query/corpus tieng Han. Voi cau `해당 기업의 총 구성원 수는 몇 명인가요?`, lop lexical hien tai khong dong vai tro that su.
3. `src/evidence_api/service.py`: LangGraph staging service dang goi **truc tiep** `retrieve_hybrid_dense_bm25(req.query, pool, pool)` thay vi doc `retrieval_mode` tu config/runtime. Nghia la **chi doi config sang rerank ON la chua du**; service hien tai se van khong di qua path rerank.
4. `src/retrieval_v3.py`: backend rerank da ton tai (`retrieve_hybrid_dense_bm25_rerank`, `jina_api`, `flashrank`, `cross_encoder`), nen van de la **service wiring**, khong phai thieu ham rerank.
5. `company_id` hien chi duoc dung de scope package/index qua `apply_company_env()` + `RAG_COMPANY_FILTER`; query text gui vao retriever **khong duoc prepend** ten cong ty. Vi vay nhan dinh "해당 기업 khong neo ve Musinsa" la dung, nhung la van de **bo tro sau BM25/rerank**, khong phai loi duy nhat.
6. `src/export_json_retrieval_hints.py` da co `expand_query()` nhung chi phuc vu metadata/export questions; chua co logic rewrite generic Korean metric question theo registry/company facts.
7. Ket luan ky thuat: neu giu nguyen corpus noise, 3 muc uu tien dung la:
   - `Korean BM25` de lexical thuc su hoat dong.
   - `Service wiring -> rerank that su` tren LangGraph staging.
   - `Company-aware query rewrite` cho nhom query generic nhu `해당 기업`.
8. `Boost` hau retrieval co the dung lam ablation staging, nhung khong nen thay the rerank. Neu top pool chua co chunk `1891명` thi boost hau ky khong giai quyet duoc goc van de.

## RAG KO metric regression - Musinsa paraphrases (2026-06-11)

1. Regression 16 cau paraphrase KO cho headcount Musinsa xac nhan fix hien tai **khong phai one-off**, nhung **chua tong quat**: top-1 dung chi **5/16 (31.2%)**, top-3 co chunk dung **11/16 (68.8%)**.
2. `Jina rerank` da chay that su **16/16** (`jina_api`), nen nhom fail hien tai khong phai do fallback overlap.
3. Nhom **PASS** tap trung vao wording `구성원` hoac `임직원`, cho thay query rewrite + BM25 KO da bat dung mot cum tu vung hep.
4. Nhom fail `answerable_chunk_not_in_top_pool` (4 case) chu yeu roi vao synonym `인원 / 전체 인원`; nghia la BM25 recall van yeu khi query khong dung dung tu cua chunk.
5. Nhom fail `rerank_failed_to_promote` (6 case) cho thay chunk dung `1891명` da vao pool nhung top-1 bi chunk `1604명` hoac noise cung chu de headcount danh bai. Day la van de ranking tren nhieu so canh tranh, khong phai no-hit.
6. `Dense` gan nhu khong cuu duoc bai toan nay (`dense_rank=0` hau het case); retrieval metric KO hien tai phu thuoc chu yeu vao **BM25 KO + rewrite**.
7. Co 1 case `rewrite_miss`: pattern `이 기업` chua nam trong regex generic company, va rewrite hien tai con nguy co prepend xau kieu `무신사 이 기업의 ...`.
8. Ket luan ky thuat:
   - Van de chinh hien tai = **lexical synonym coverage** + **metric-aware ranking under competing numbers**.
   - Chua nen ket luan retrieval KO "xong" chi tu case `1891명`.
9. Huong sua dung tiep theo:
   - Query rewrite: them `이 기업`, va chuan hoa rewrite output gon hon.
   - BM25 query expansion: map `인원 <-> 직원 <-> 구성원 <-> 임직원 <-> 근로자`.
   - Metric-aware ranking/boost: uu tien chunk co pattern `\d+명` gan cum metric headcount.
   - Giữ regression gate: `>=80%` top-1, `100%` top-3 truoc khi freeze.

## RAG KO metric regression v2 - Musinsa 16/16 (2026-06-11)

1. Theo bao cao Cursor, sau khi them `safe possessive rewrite + BM25 synonym expansion + headcount-aware ranking`, regression Musinsa da dat **16/16 top-1** va **16/16 top-3**; `Jina` van chay that su **16/16**.
2. Neu khong co hardcode theo `1891` / `record_id` / package Musinsa, day la bang chung manh rang he thong da generalize tot hon trong **lop headcount KO paraphrase**.
3. Gia tri ky thuat cua ket qua nay la da xoa duoc ca 3 nhom loi truoc do:
   - `rewrite_miss`
   - `answerable_chunk_not_in_top_pool`
   - `rerank_failed_to_promote`
4. Tuy nhien, bang chung hien tai van bi gioi han boi pham vi eval:
   - **1 cong ty** (`musinsa`)
   - **1 metric family** (headcount)
   - **1 ground-truth numeric anchor** (`1891명`)
5. Nguy co con lai khong phai la "van fail query nay", ma la **over-specialization theo metric family**:
   - synonym expansion dang target headcount
   - ranking boost dang target pattern `숫자 + 명`
   - blend alpha dieu chinh rieng cho headcount
6. Vi vay, ket luan dung nhat luc nay la:
   - **Da generalize tot trong headcount class**
   - **Chua du bang chung de freeze retrieval chung cho metric KO**
7. Buoc danh gia tiep theo nen la:
   - ablation tung lop (`rewrite`, `bm25 expansion`, `headcount boost`)
   - holdout paraphrase moi khong nam trong bo 16 cau
   - mo rong sang metric dinh luong khac khi co GT sach
   - mo rong sang `hanssem` / `rayshion` khi annotate duoc GT

## RAG gender-ratio baseline audit (2026-06-11)

1. Hai query `해당 기업의 남성 비율은 몇 %인가요?` va `해당 기업의 여성 비율은 몇 %인가요?` hien **chua the danh gia la dung/sai theo answer GT**, vi khong co ground truth workforce male/female `%` sach trong lane indexed `company_evidence`.
2. Rewrite layer hoat dong dung huong (`해당 기업 -> 무신사의`), va `rerank_status=jina_api` xac nhan wiring rerank khong phai blocker.
3. Top-1 hien tai la noise UI / policy false positive (`여성 남성` form text, `여성기업`, `mss.go.kr`, v.v.). Nghia la retrieval hien van tra ve **best-of-wrong-candidates**, khong tu biet abstain.
4. Blocker goc la **GT/data absence**, khong phai retrieval tuning:
   - `splits/full.jsonl`: khong co chunk workforce male/female ratio sach
   - `ai_extracted_response.jsonl`: co taxonomy/field nhung khong phai evidence GT da verify
   - Golden set ratio row dang `dataset_issue`
5. Co mot rui ro ky thuat da lo ro: query ratio co them `임직원/구성원` co the kich hoat nham headcount path. Day la risk can xu ly **sau khi co GT**, khong nen patch mu.
6. Ket luan dung:
   - **Khong patch gender-ratio retrieval luc nay**
   - **Can them abstain/no-relevant-evidence gate** cho API retrieve, vi neu khong co evidence dung thi API van tra top-1 sai nhung "co ve hop ly"
7. Lớp gate can backlog:
   - detect `no_relevant_evidence`
   - co the dua tren score/rerank/pattern mismatch/domain mismatch
   - tra `items=[]` hoac flag `abstain_recommended=true` / `retrieval_confidence=low`
   - khong dong nhat `top_1` voi "dap an dung nhat"

## RTX lane chunking (2026-06-12)

1. **Input:** 4 PDF + 5 HTML + 1 MD fallback (10 files).
2. **Output:** `rtx_chunked_corpus.jsonl` **2641** chunks; `corpus_units_rtx.jsonl` **2641** units.
3. **Strategy:** pypdf (không docling); SEC HTML section-aware; chunk 900/150.
4. **Breakdown kind:** 10k 1684, proxy 544, questionnaire 236, appendix 87, data_table 64, policy 24, press 2.
5. **DOJ:** fallback `.md` → 2 chunks.
6. **Ready:** RAG + Golden Set workbook-first step 1.

## RTX web sources raw HTML download (2026-06-12)

1. **Lane:** `data/rag_dataset/06_rtx_references_raw/` — 4 PDF + web references.
2. **Download:** 5/6 raw HTML thanh cong (SEC x3, RTX x2); DOJ **HTTP 403** blocked.
3. **Snapshot cleanup:** 5 file `.md` da xoa sau khi co HTML tuong ung; DOJ snapshot giu lai.
4. **Chunking readiness:** gan du (9/10 file) — thieu DOJ HTML that.

## Refine hold round 5 (2026-06-12)

1. **Input:** 17 hold rows (HS 15, MS 2); **không** đụng gold_core_v1 / RX.
2. **Lanes:** `lane_1_known_cluster_cleanup` (5), `lane_2_fc_unknown_resolution` (12).
3. **Decisions:** promote_candidate **3**, keep_hold **9**, drop_after_refine **5**.
4. **FC_UNKNOWN:** input 12 → resolved **9**, unresolved **3**.
5. **Promote examples:** MS-V4-Q09 (governance trim), HS-V4-Q39 (human rights), HS-V4-T03 (report framework).
6. **gold_core_v1_1:** có **3** row đủ promote_candidate — chưa freeze trong task.
7. Artifact: `golden_set_core_round5_refine.xlsx`, `golden_set_refine_hold_round5.md`.

## Freeze gold core v1 (2026-06-12)

1. **Input:** 26 `gold_approve` từ round 4 — **không** hold/reject/RX.
2. **Output:** `golden_set_core_v1.jsonl` — **26** row frozen (`gold_version=gold_core_v1`, `gold_status=frozen_approved`).
3. **By company:** 한샘 **21**, 무신사 **5**.
4. **By question_type:** quantitative **18**, qualitative **7**, trend **1**.
5. **By cluster:** FC_ESG_GOVERNANCE **13**, FC_MATERIAL_8 **5**, FC_HUMAN_RIGHTS **3**, FC_TCFD **2**, FC_KGCS_A **2**, FC_OFFLINE_RETAIL **1**.
6. **Hold backlog:** **17** row — expansion lane, không trộn vào v1.
7. **RX:** `source-acquisition dependent` — ngoài gold core.
8. Artifact: `golden_set_core_v1.xlsx`, `eval_gold_core_v1_ko.md`, `golden_set_freeze_gold_core_v1.md`.

## Gold decision core round 4 (2026-06-12)

1. **Input:** 45 core canonical (HS+MS).
2. **Gold decision:** approve **26**, revise_hold **17**, reject **2**.
3. **FC_UNKNOWN (15):** approve 1, hold 12, reject 2 — **14 chưa chốt** (không auto-approve).
4. **Core gold ready:** **26** (한샘 **21**, 무신사 **5**).
5. **RX:** backlog `source-acquisition dependent` — không trong gold core.
6. Artifact: `golden_set_core_round4_decision.xlsx`, `golden_set_gold_decision_core_round4.md`.

## Core canonical round 3 (2026-06-11)

1. **Scope:** chỉ `한샘` + `무신사` (`canonical_candidate_flag=true`); **không** RX trong core.
2. **Input:** 60 candidates → **45** core canonical (keep **30**, keep_after_merge **15**).
3. **Drops:** duplicate **8**, weak **7**.
4. **By company:** 한샘 **36**, 무신사 **9**.
5. **RX:** backlog **40** row (1 survivor + lane C + reject) — source-acquisition dependent.
6. **Gold decision:** `core_ready_for_gold_decision_flag=true` — chưa promote trong task.
7. Artifact: `reference_seed_workbook_core_canonical_round3.xlsx`, `golden_set_core_canonical_round3.md`.

## Manual review round 2 execution (2026-06-11)

1. **Lane A+B processed:** 80 row → confirm **31**, revise **30**, drop **19**.
2. **Canonical candidates:** **61** (confirm+revise, sau cluster dedupe).
3. **한샘:** confirm 24, revise 25, drop 1 — core anchor đủ mạnh (49 canonical candidates).
4. **무신사:** confirm 6, revise 5, drop 6 (11 canonical candidates).
5. **레이시온:** confirm 1, revise 0, drop 12 — portal/cross-company contamination; **1** row sống thực sự.
6. **Lane C backlog:** 22 row chưa xử lý.
7. **Ready canonical round:** Có (core HS/MS); RX cần source acquisition sau.
8. Artifact: `reference_seed_workbook_v4_manual_round2_reviewed.xlsx`, `golden_set_manual_review_round2_execution.md`.

## Manual review round 2 prep (2026-06-11)

1. **Lane split** trên 107 reviewable: A **14**, B **66**, C **22**, reject recommended **5**.
2. **Lane A:** round1 keep + disclosure sạch — confirm/drop nhanh.
3. **Lane B:** rewrite_light (chủ yếu `generic_question` + disclosure sạch) — chỉnh wording/specificity.
4. **Lane C:** passage bẩn (news chrome, truncated, meta) — salvage nếu còn thời gian.
5. **Reject recommended:** TCFD definition truncated (`HS-V4-Q04`), heavy news chrome KGCS (`HS-V4-Q01/Q08`), v.v.
6. **Survivors estimate:** ~**72** row có khả năng tới canonical round (A×90% + B×75% + C×45%).
7. Artifact: `reference_seed_workbook_v4_manual_round2.xlsx`, `golden_set_manual_review_round2_prep.md`.

## Workbook review round 1 v4 (2026-06-11)

1. **Input:** 175 v4 JSONL candidates → triage 4 trạng thái (keep/rewrite/reject/collapse).
2. **Kết quả:** keep **35**, rewrite **72**, reject **35**, collapse **33** → **107** reviewable (keep+rewrite).
3. **Noise đã loại:** cross-company **15** (현대트랜시스 gán 레이시온), listing/index **4**, framework-only **2**, insufficient **13**.
4. **Coverage reviewable:** 한샘 **71**, 무신사 **22**, 레이시온 **14** — RX mỏng do contamination gốc.
5. **Không bóp yield:** 107 rows >> nhánh cũ (~17); đủ đa dạng 3 công ty cho manual review R2.
6. Artifact: `reference_seed_candidates_v4_reviewed_round1.jsonl`, `reference_seed_workbook_v4_review_round1.xlsx`, `golden_set_workbook_review_round1.md`.

## Candidate generation v4 JSONL (2026-06-11)

1. **Reset đúng hướng:** Builder v4 đọc trực tiếp `corpus_units.jsonl` (118 units) — không cần PDF; không hardcode salvage record id.
2. **Yield:** 98 passage accepted (20 rejected: cross-company 14, no ESG 3, nav 2, financial 1) → 899 raw → 383 after dedupe → **175** workbook rows.
3. **Coverage 3 công ty:** 한샘 **97**, 무신사 **47**, 레이시온 **31** — đa dạng hơn v1 (~17), v2 (10), v3 (9).
4. **Question types:** quantitative 88, qualitative 75, trend 12; candidate_kind: report/framework 64, governance 34, quantitative_fact 30, qualitative 30.
5. **Provenance:** `jsonl_primary_candidate` 121, `jsonl_mixed_candidate` 54; ~0 `jsonl_noisy_but_salvageable` flagged at high-noise reject.
6. **So với workflow cũ:** vấn đề không phải AI không tìm ESG fact mà `1 unit → 1 QA` + hard-drop sớm; v4 khôi phục yield mà vẫn có guardrail 3 tầng.
7. Artifact: `reference_seed_candidates_v4_jsonl.jsonl`, `reference_seed_workbook_v4_jsonl.xlsx`, `golden_set_candidate_generation_v4_jsonl.md`, `_candidate_generation_v4_jsonl_summary.json`.

## Raw source audit v4.2 (2026-06-11)

1. **무신사 raw folder:** 7 PDF trong `09_기타/에이전트다운로더` — toàn **sell-side research** (KB/삼성/LS증권) + **입찰조달**; **không** Impact Report PDF.
2. **DART 무신사:** chỉ `사업보고서`/`분기보고서`/`반기보고서` — **không** `지속가능경영보고서` filing.
3. **Secondary trace:** `page_04_web` capture có link newsroom `/impact` nhưng **không** phải report body.
4. **레이시온 raw folder:** agent research + downloader nhầm **RTX Corporation (US Raytheon)**; `rtx-20251231.htm.html` = SEC 10-K, **sai công ty**.
5. **DART 레이시온:** chỉ `감사보고서` — **không** SR/ESG report.
6. Artifact: `golden_set_raw_source_audit_v4_2.md`, `_raw_source_audit_v4_2_summary.json`.

## Source import validation v4.1 (2026-06-11)

1. **Import:** 2 PDF từ `Downloads/data-company/3cty/` đã copy vào package `_sources/` (한샘, 레이시온).
2. **Readable:** Cả hai đọc được (5 trang, ~9.5k chars extracted mỗi file).
3. **Document type:** Không phải sustainability report body — là **ESG Requirement Coverage export** (matched evidence stats, coverage ratio).
4. **Verdict:** `accept_with_warnings` cho cả hai — intake pass về readability, nhưng **chưa** thay SR PDF thật cho report-body seeds.
5. Artifact: `intake_validation_v4_1.json`, `golden_set_source_import_validation_v4_1.md`.

## Reference workbook v3 actual sources (2026-06-11)

1. **Audit PDF:** 무신사 `_sources/` có 3 PDF — không có Impact Report usable (1 file = 중소기업 연차보고서 1120 trang; 2 file corrupt/HTML). 레이시온 không có `_sources/`.
2. **Company-primary narrative:** 무신사 có `newsroom.musinsa.com` (`2024-0719`, `2025-0724`) — tốt hơn Yonhap/headline v2 nhưng **không** phải full report PDF body.
3. **레이시온 gap:** corpus = YGPA portal + cross-company noise; chỉ salvage 1 câu stakeholder disclosure (`portal_salvage_seed`).
4. **V3 output:** 4 Hansem frozen + **4** MS `company_primary_narrative_seed` + **1** RX `portal_salvage_seed` = **9** seed / **6** cluster.
5. **actual_report_body_seed:** **0** cho cả hai công ty — cần source acquisition trước review.
6. Artifact: `source_pool_*_v3.jsonl`, `reference_seed_candidates_v3.jsonl`, `reference_seed_workbook_v3.xlsx`, `golden_set_actual_source_audit_v3.md`.

## Reference workbook rebuild v2 (2026-06-11)

1. **Vì sao 무신사/레이시온 biến mất khỏi R2:** corpus 38+40 unit chủ yếu portal/nav, listing, financial/analyst, cross-company (YGPA portal gán nhầm 레이시온).
2. **Contamination chính:** `contact_navigation_site_text`, `press_release_mixed`, `financial_or_irrelevant_non_esg`, `cross_company_contamination`.
3. **Salvageable:** 무신사 — Yonhap Impact Report (`rec_753`), headline listing (`rec_0f148d`); 레이시온 — 1 câu stakeholder disclosure (`rec_40b94d`) trong portal chrome.
4. **Rebuild output:** 4 Hansem frozen + **5** MS seed (`FC_IMPACT_REPORT`, `FC_CLIMATE_GHG`, `FC_ESG_GOVERNANCE`, `FC_COMMUNITY_DONATION`, `FC_EXTERNAL_DIRECTOR`) + **1** RX seed (`FC_STAKEHOLDER_DISCLOSURE`).
5. **Tổng:** 10 seed / 9 cluster — có mặt 3 công ty nhưng **chưa** review-ready (RX mỏng, MS phụ thuộc press).
6. Artifact: `reference_seed_candidates_v2.jsonl`, `reference_seed_workbook_v2.xlsx`, `source_pool_*_r2.jsonl`.

## Reference workbook canonical R2 (2026-06-11)

1. Input curated R1: **14** row (Hansem-only) → canonical **4** row, **4** fact cluster độc lập.
2. Cluster collapse: `FC_NET_ZERO_2050` 3→1, `FC_ESG_GOVERNANCE` 3→1, `FC_MATERIAL_8` 3→1, `FC_KGCS_A` 2→1; `FC_TCFD` 3→0 (no company fact).
3. R1 semantic drift **đã sửa** trên HS-G-Q01 (2050 goal, không còn drift sang governance); HS-G-T03 drop `truncated_unsalvageable`.
4. Canonical seeds: `HS-G-T04`, `HS-G-Q01`, `HS-G-Q06`, `HS-G-T01`.
5. **Chưa** đủ review nội dung đầy đủ — đây là **Hansem canonical skeleton**, không phải workbook 3 công ty.
6. Bước tiếp: **rebuild seed workbook v2** cho 무신사/레이시온 trước khi review nội dung multi-company.

## Reference workbook curation R1 (2026-06-11) — đã supersede bởi R2

1. Input `reference_seed_candidates_v1.jsonl`: **17** seed (한샘 16, 무신사 1).
2. Curation R1: **keep_strong 3** (`HS-G-T04`, `HS-G-Q06`, `HS-G-L06`), **keep_but_needs_rewrite 11**, **reject 3** (`drop_contact_or_navigation` 1, `drop_listing_archive` 2).
3. **Usable thực sự (strong):** 3 — đủ làm anchor review nhưng chưa đủ đại diện 3 công ty.
4. **Salvageable (rewrite):** 11 — chủ yếu news press-release chrome + TCFD definition noise + truncated passage; fact ESG vẫn cứu được bằng rewrite round 2.
5. **무신사** duy nhất 1 seed → reject (portal/nav); cần corpus narrative sạch trước khi có seed workbook đa công ty.
6. ~~Workbook curated R1 đủ review~~ — **đánh giá lại**: chỉ là partial Hansem workbook; R2 collapse xuống 4 canonical.
7. Artifact R1: `reference_seed_candidates_curated_r1.jsonl`; artifact R2: `reference_seed_candidates_canonical_r2.jsonl`, `reference_seed_workbook_canonical_r2.xlsx`.

## Revise before promote R2.4 (2026-06-11)

1. 4 row revise → **cứu được 2** (`0001` dup winner, `0002` Net Zero rewrite); **không cứu** `0004` (dup loser), `0005` (news chrome noise=16).
2. Promote-ready sau revise: **3** (`SV2-P24-0001`, `0002`, `0003`) — đủ gold pilot mini-set thử nghiệm.
3. Chiến lược dup: giữ `0001` (unit sạch rec_3adad134) thay `0004` (백세경제 chrome).
4. Artifact: `pilot_hanssem_5_qc_revised_r2_4.jsonl`, `reports/golden_set_revise_before_promote_r2_4.md`.

## Silver QC pilot Hansem R2.4 (2026-06-11)

1. QC pilot hạn chế 5 row compact: **pass 1 / revise 4 / reject 0**; `promotion_candidate=yes` chỉ **1** row (`SV2-P24-0003` TCFD).
2. Rubric rule-based (faithfulness / answer relevancy / groundedness) + duplicate batch: `0001`+`0004` trùng fact cluster **8개 중대 이슈**.
3. `0002` Net Zero, `0005` KGCS rating: groundedness **partial** (conditional/news mixed) — revise, không reject.
4. Schema QC đủ cho reviewer (`pilot_hanssem_5_qc_review.csv`); **chưa đủ** gold mini-set ngay — cần **revise trước promote** (chọn 1 trong dup pair; SME review news-chrome rows).
5. Artifact: `pilot_hanssem_5_usable_for_qc_r2_4.jsonl`, `pilot_hanssem_5_qc_result_r2_4.jsonl`, `reports/golden_set_silver_qc_pilot_r2_4.md`.

## Pilot Compact Hansem R2.4 (2026-06-11)

1. Pilot compact 6 unit (6 anchor R2.3 proven, 0 expansion, 0 tail filler) — **không đạt** target 8–10 vì pool Hansem bão hòa.
2. Distillation compact: **keep 5 / drop 1 / usable 5**; `usable/input=83%`, `usable/keep=100%` vs R2.3 `40%`/`100%`.
3. Drop duy nhất: `rec_147089a328626757` (news chrome → `ambiguous_grounding`) — LLM variance (usable ở R2.3).
4. **Hướng A:** mở Silver QC pilot hạn chế trên 5 row (`SV2-P24-0001`..`0005`); ratio đủ cao dù chưa đạt gate tuyệt đối ≥8.
5. Vẫn cần mở rộng corpus Hansem để full step 2 / gate chính ≥8.
6. Artifact: `pilot_hanssem_10_compact_r2_4.jsonl`, `pilot_hanssem_10_compact_distilled_r2_4.jsonl`, `reports/golden_set_pilot_compact_r2_4.md`.

## Distillation pilot Hansem R2.3 (2026-06-11)

1. Input 15 unit (4 proven anchors + 11 corpus fill) → output **keep 6 / drop 9 / usable 6** — **bang R2.2** (Δ0).
2. Prompt Distillation R2.1 + validation: 6/6 keep usable, 0 weak/generic — **distillation khong phai bottleneck**.
3. **Chua dat** nguong `>=8 keep usable` — **chua du** mo Silver QC lam gate chinh.
4. So voi R2.2: `ambiguous_grounding` giam 3→1; `duplicate_same_fact` tang 2→3; `insufficient_substance` tang 2→4; `nav_or_menu_noise` giam 2→1.
5. Proven anchor `rec_66100907` (usable R2.2) bi drop `ambiguous_grounding`; corpus fill bo sung 3 usable moi (`rec_2d0cf95b`, `rec_ba9d092`, `rec_147089a328626757`).
6. Root cause: **selector** — Hansem pool ~15 unique body; tail corpus-fill van noisy/duplicate fact; forecast 8-12 khong dat.
7. Artifact: `pilot_hanssem_15_distilled_r2_3.jsonl`, `reports/golden_set_distillation_pilot_hanssem_round2_3.md`.

## Pilot selector Hansem R2.3 (2026-06-11)

1. Sau Distillation R2.2 (6/15 usable), selector R2.3 loại 10 unit R2.2: TOC/intro, soft-dup span, near-dup body (`rec_6d11be8f`, `rec_acac077`).
2. Logic: best-per-fingerprint, fact-tag diversity, hard-block 7 distill failures, proven boost (+120).
3. Pilot moi 15 unit: 4 proven anchors + 11 corpus fill (unique body, noise<=18); **0** unit hard-block trong pilot.
4. Hansem pool chi co ~15 unique body chat — tail slots la news noise 14-17 (medium risk).
5. Artifact: `pilot_hanssem_15_eligible_r2_3.jsonl`, `reports/golden_set_selector_round2_3.md`.

## Distillation pilot Hansem R2.2 (2026-06-10)

1. Input 15 unit (10 keep + 5 conditional R2.2) → output **keep 6 / drop 9 / usable 6** (R2.1: 3/3/3).
2. Prompt Distillation R2.1 + validation: 6/6 keep usable, 0 weak/generic — prompt **khong** phai bottleneck.
3. **Chua dat** nguong `>=8 keep usable` — **chua du** mo Silver QC lam gate chinh.
4. Drop chinh: `duplicate_same_fact` (2), `ambiguous_grounding` (3), `nav_or_menu_noise` LLM (2) — pilot van chua unit trung fact cluster va TOC/intro.
5. Silver QC candidates san sang: `SV2-P22-0001`, `0002`, `0003`, `0005`, `0006`, `0010`.
6. Artifact: `pilot_hanssem_15_distilled_r2_2.jsonl`, `reports/golden_set_distillation_pilot_hanssem_round2_2.md`.

## Prefilter R2.2 + pilot selection (2026-06-10)

1. Sau pilot Distillation R2.1 (`3/15` keep), siết prefilter R2.2: `substance_score` / `noise_score`, R8 chỉ keep khi có fact ESG thật, R6 drop portal/archive/news nặng, R10 conditional news mixed (`substance>=16`, `noise<=8`).
2. Kết quả toàn corpus: `keep=23`, `drop=89`, `conditional=6` (artifact riêng `corpus_units_eligible_r2_2.jsonl`, không ghi đè R2.1).
3. `한샘`: keep `10`, conditional `6`; pilot mới `15` unit (`10` keep + `5` conditional), loại `10/15` unit noisy của pilot R2.1 (portal/nav/archive/URL chrome).
4. Overlap pilot cũ/mới: `5` record_id; bổ sung unit sạch (`rec_3adad134`, `rec_fcab1197`, `rec_66100907`, …).
5. CLI: `python scripts/golden_set_pipeline.py --step 0 --prefilter-r2-2` hoặc `python -m golden_set.prefilter_corpus_units_r2_2` từ `src/`.

## Distillation pilot Hansem R2.1 (2026-06-10)

1. Pilot 15 unit: output `15` row, `keep=3`, `drop=12`, `usable=3` (`SV2-P21-0001`, `0008`, `0012`).
2. Prompt R2.1 + post-validation hoat dong: moi keep co `evidence_span`/`why_grounded`; dedupe bat trung Net Zero; reject generic paraphrase.
3. Root cause yield thap: **pilot input** van chua news UI/portal nav/listing du prefilter R8 keep — LLM drop dung 8 case `insufficient_substance`.
4. Chua du sach de mo Silver QC (can ~8-10 keep); uu tien **siết prefilter + tai chon pilot** truoc khi full step 2.
5. Artifact: `data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled.jsonl`, `reports/golden_set_distillation_pilot_hanssem_round2_1.md`.

## Prefilter R2.1 run (2026-06-10)

1. Da implement va chay pre-filter deterministic tren `118` corpus units:
   - `keep=40`, `drop=74`, `conditional=4`
   - Rule drop nhieu nhat: `R1_cross_company_mismatch` (`29`), `R6_secondary_news_rewrite_ui_noise` (`18+`)
   - Rule keep: `R8_primary_esg_narrative_keep` (`30`), `R9_metric_or_policy_keep` (`17`)
2. Theo company: `한샘` keep `23` (du pilot 15), `레이시온` keep `1`, `무신사` keep `16`.
3. `corpus_units_conditional_r2_1.jsonl` gom intro/report mixed (vd. `rec_ea632bae`, `rec_fcab1197`) — khong merge vao eligible mac dinh.
4. Pilot file `pilot_hanssem_15_eligible.jsonl` da chon 15 unit (primary + metric + governance, dedupe fingerprint).
5. CLI: `python scripts/golden_set_pipeline.py --step 0` hoac `python -m golden_set.prefilter_corpus_units_r2_1` tu `src/`.

## Distillation Round 2.1 design (2026-06-10)

1. Prompt v2 (`step2_distill.py`) luon sinh Q&A cho 118/118 unit — khong co `decision=drop`; day la root cause truc tiep cua silver/gold ban truoc denylist.
2. Audit heuristic tren 118 corpus unit:
   - `cross_company_mismatch`: 29 unit (레이시온 26/40)
   - `nav_or_menu_noise`: 35 unit
   - `primary_esg_narrative`: 50 unit — nguon silver sach chinh (한샘 ~29 unit)
3. Pre-filter R2.1 de xuat 9 rule deterministic truoc LLM; uoc luong ~47 unit khong nen goi LLM neu khong co primary ESG body.
4. Prompt R2.1 bat buoc: `decision`, `drop_reason`, `evidence_span`, `why_grounded`; post-validation AC-1..AC-10 + dedupe `(company, evidence_span)`.
5. Artifact: `reports/golden_set_distillation_round2_1.md`, prompt copy-paste `reports/golden_set_distillation_prompt_round2_1.md`.

## Golden Set method Round 2 (2026-06-10)

1. 6 nguon chuan user chot khac framing Grounding Contract R1: 4 tai lieu phuong phap (khai niem, runbook, so sanh Distillation/Evol/Judge, cong cu metric) + 2 CSV taxonomy ESG; company evidence la **lane dataset**, khong nam trong 6 nguon phuong phap.
2. `ESG-정량` (251 dong) uu tien seed cau **fact/metric** (so lieu, don vi, GRI/SASB/K-ESG); `ESG-정성` (27 dong, 4 Pillars) uu tien **narrative/governance/risk/strategy**.
3. Root cause gold ban v2: Distillation tu corpus chua loc du — denylist 6 rule (`nav/menu`, `listing/index`, `date-only`, `company mismatch`, `secondary/vendor generic`, `duplicate same fact`) phai gan vao prompt Distillation + Silver QC + Judge, khong chi buoc clean sau promote.
4. Prompt uu tien tiep theo: **Distillation** — Evol va LLM-as-a-judge chi co gia tri khi silver dau vao da sach hon; artifact: `reports/golden_set_method_round2.md`.

## Golden worksheet sample learning (2026-06-09)

1. File mau `TalkFile_golden_worksheet_v1.xlsx.xlsx` cho thay golden set nen duoc to chuc thanh workbook review duoc, thay vi chi la CSV ky thuat.
2. 3 sheet cua file mau co y nghia ro:
   - `안내`: huong dan cach viet golden
   - `작성`: bang lam viec chinh cho tung seed
   - `참조`: mapping area / code / taxonomy
3. Cot `acceptable_disclosure`, `prohibited_claims`, `gold_area`, `gold_ebx`, `status`, `notes` rat hop voi workflow review cua team Dataset/SME.
4. Dung Korean-only cho question/answer/evidence/prohibited claims la hop ly hon doi voi lane Nexteye vi tranh sai lech nghia do dich.

## Golden Set v2 clean subset audit (2026-06-10)

1. Co the loc noisy gold theo denylist ro ly do ma khong can sua tay `golden_set.jsonl`:
   - artifact moi: `data/golden_set/v2/step6_gold/golden_set_clean.jsonl`
   - script tai lap: `scripts/filter_golden_v2_clean.py`
2. Sau khi loc:
   - giu `41/87` cau
   - `한샘`: giu nguyen `29`
   - `무신사`: giu `12`
   - `레이시온`: loai toan bo `30`
3. Nhom noisy chinh da bi loai:
   - `date-only` / `listing-only`
   - `nav/menu` / `lookup page`
   - `company mismatch` (record noi dung cong ty/to chuc khac)
   - `generic vendor content`
   - `duplicate same fact`
   - `question-answer mismatch` (cau hoi hoi "ly do/y nghia" nhung gold chi tra fact ngan)
4. `reports/golden_v2_cleaning_report.md` da ghi ro tung `question_id -> reason`, nen co the review hoac dieu chinh denylist sau nay ma van audit duoc.
5. Rerun benchmark tren tap clean trong runtime hien tai khong the dung de ket luan:
   - ngay ca `eval_golden_v2_hanssem_ko.md` goc cung rerun ra `retrieval_hit=0`
   - `top_sources=[]` hang loat
   - dau hieu la runtime/harness drift, khong phai do denylist clean subset

## 3-company dataset audit for preliminary answer fill (2026-06-09)

1. Package `레이시온_dataset_package_20260608T055801` co dau hieu mismatch noi dung:
   - nhieu record `official_sustainability_report` tro toi noi dung cong khai cua to chuc/website khac
   - khong du tin cay de dung lam `gold answer` cho company `레이시온`
2. Package `무신사_dataset_package_20260608T092823` co nhieu record `official_sustainability_report` chi la trang dang bai / listing / file index, khong phai than noi dung report.
3. Package `한샘_dataset_package_20260608T042739` la package duy nhat trong 3 package hien tai co mot so snippet ESG doc duoc va co the dung de dien `gold_answer` dinh tinh o muc so bo.
4. Shortlist 20 cau hien tai lech voi taxonomy/noise profile cua 3 package:
   - phan lon cau dinh luong khong tim duoc value grounded ro rang trong `company_evidence`
   - mot so cau dinh tinh co the dien cho `한샘`, nhung `레이시온` va `무신사` chu yeu nen de `dataset_issue`

## Golden set / teacher-answer framing (2026-06-09)

1. User framing bai toan hien tai theo kieu "co giao ra de + dap an mau + bai lam cua he thong + bang diem", phu hop hon voi workflow eval hon la benchmark ha tang.
2. Golden set can co it nhat 4 lop du lieu:
   - `question`: cau hoi dau vao
   - `ground_truth_answer`: dap an dung/canonical answer
   - `evidence_anchor`: vi tri bang chung dung de audit
   - `scoring_rule`: cach cham dung/sai/mot phan/cam tra loi
3. Neu chi cham answer text ma khong co `evidence position`, `forbidden rule`, va `notes` thi khong du de danh gia pipeline ESG/document QA theo yeu cau business.
4. Artifact xuat ket qua phai uu tien dang bang (`xlsx/csv`) theo tung dong cau hoi de team Dataset/SME review va ghi chu thu cong.
5. "Vi tri cau tra loi" can duoc dinh nghia ro ngay tu dau: toi thieu nen co `doc_id`, `page`, `chunk_id`, va snippet/span neu co.

## RAG Concepts

RAG Pipeline gom hai pha chinh: indexing va querying. Indexing thuong gom load, chunk, embed, store. Querying thuong gom embed query, retrieve, rerank va generate.

## Tool Notes

Trong giai doan thuc hanh, uu tien tool mien phi, local va de debug: Python, LangChain hoac LlamaIndex, Chroma hoac FAISS, sentence-transformers, rank-bm25, FlashRank, RAGAS, Phoenix, Ollama.

Trong giai doan product, can nhac ingestion tot hon, vector database production, hybrid retrieval, reranking, observability va evaluation.

## Ingestion Findings

Nen bat dau bang MarkdownLoader cho bo tai lieu markdown noi bo de giam loi parser trong V1.

## Chunking Findings

De xuat baseline V1: RecursiveCharacterTextSplitter voi `chunk_size=800`, `chunk_overlap=120`; uu tien de citation ro rang truoc khi toi uu chat luong retrieval.

## Embedding / Vector Store Findings

Cap sentence-transformers/all-MiniLM-L6-v2 + Chroma phu hop cho bo du lieu nho, toc do on va de chay local.

## Retrieval / Reranking Findings

Hybrid retrieval la huong quan trong o V3: BM25 bat keyword chinh xac, vector search bat ngu nghia, fusion/rerank giup chon context tot hon.

## Evaluation Findings

Can giu mot eval set co dinh xuyen suot cac version de so sanh cong bang.

## Product Notes

Chua thuc nghiem.

## Implementation Notes

Da tao scaffold V1 trong repo:
- `src/ingest.py` cho load/chunk/embed/persist Chroma.
- `src/ask.py` cho retrieve + generate qua Ollama.
- `data/sample_docs/*.md` la bo du lieu mau ban dau.
- `BASELINE_V1.md` la quick guide de chay baseline.

## Dataset Findings

Da tao bo `Core Dataset` moi tai `data/rag_dataset` de dung xuyen suot Version 1-6:

- `01_synthetic_controlled`: 6 tai lieu noi bo gia lap, co heading/section/bullet/bang de tao cau hoi eval on dinh.
- `02_public_reports`: dung de chua report cong khai ESG/sustainability/annual/governance tu nguon chinh thuc.
- `03_noisy_or_complex`: du phong cho tai lieu OCR/noisy de test robustness o version sau.

Ly do chon:

1. Synthetic controlled giup benchmark baseline va debug retrieval de dang.
2. Public reports giup danh gia tinh tong quat tren tai lieu thuc te.
3. Cung mot dataset co dinh giup so sanh cong bang giua cac version.

Ghi chu han che hien tai:

- Moi truong shell dang bi chan network, khong tai duoc PDF public.
- Da luu URL chinh thuc va trang thai tai trong `data/rag_dataset/sources.md`.

## ESG Dataset Findings

Da nang cap dataset theo huong ESG public chuan hon:

- Doi bucket thanh `02_esg_public_core` va `03_esg_public_complex`.
- Chon bo ESG core theo nguon framework + corporate reports chinh thuc:
  - GRI, IFRS/ISSB, TCFD, UNGC, OECD
  - Apple, Google, Vinamilk
- Chon bo ESG complex cho benchmark hard:
  - Microsoft Sustainability
  - Unilever Annual Report
  - Toyota Sustainability Data Book
  - FPT Investor Reports

Ly do chon:

1. Co day du tru cot E/S/G.
2. Co tai lieu ngan va dai, thuan cho V1->V6.
3. Co tinh dinh luong va governance language de test retrieval + citation.
4. Nguon chinh thuc, on dinh, de truy vet.

Han che:

- Moi truong hien tai khong download duoc tai lieu public qua shell.
- Da danh dau `manual_download_required` trong `data/rag_dataset/sources.md`.

Cap nhat 2026-05-22:

- Da tai thanh cong 11 tai lieu ESG public vao local (core + complex) bang `Invoke-WebRequest` voi quyen escalated.
- 1 tai lieu con lai `ESG-X02` (Unilever Annual Report 2025) bi 403 Forbidden khi tai tu dong.
- Voi bo local hien tai, da du du lieu de bat dau baseline evidence-based; tai lieu ESG-X02 se bo sung thu cong de hoan tat 12/12.

Cap nhat bo sung:

- User da tai thu cong ESG-X02 thanh cong.
- Trang thai dataset hien tai: 12/12 tai lieu ESG da co local.

## Evidence-based Roadmap Insights

Insight moi sau khi ra soat bai toan thuc te:

1. Lo trinh RAG can huong toi evidence-based pipeline, khong chi chatbot Q&A.
2. Product thuc te thuong can output du lieu co cau truc + bang chung + bao cao.
3. RAG la loi truy xuat/kiem chung bang chung, khong phai toan bo he thong.
4. Danh gia can cham ca answer quality va evidence quality (source/citation/groundedness/insufficient handling).

## Work Block V1 Findings (2026-05-22)

1. Da khoi dong thanh cong work block Version 1 tren ESG local dataset (12/12 tai lieu).
2. Da tao artifact chay that tai `reports/workblock-v1-baseline-esg.md`.
3. Fallback lexical retrieval co the tao output `answer + evidence + citation + confidence` de bat dau benchmark.
4. Chat luong generation hien con tho; insufficient-information handling can cai thien trong Version 2.
5. Stack LangChain+Chroma chua run duoc tren Python 3.13 vi `chroma-hnswlib` can C++ build tools.

## V1 Baseline Implementation (2026-05-22)

1. Da chuan hoa `src/config.py`, `src/ingest.py`, `src/ask.py`, `src/rag_common.py`, `src/evidence_rag.py`, `src/run_v1_eval.py`.
2. Ingest lexical: 21 file scanned, 20 co text, 188 chunks; file PDF `ESG-X02_unilever_annual_report_2025.pdf` chua doc duoc (chua co trong workspace hoac thieu `pypdf`).
3. Eval 10 cau: artifact chinh `reports/v1-baseline-eval-20260522-093928.md`, quick_check 10/10.
4. Cau synthetic (E01,E05,E10,G01,S01) tra dung nguon `01_synthetic_controlled` sau khi boost source + extract fact.
5. Cau catalog (E07,E08,E14) tra dung tu `sources.md` bang keyword routing.
6. Cau insufficient (I01,I02) tra `Khong du du lieu trong context` voi `insufficient=true`.
7. `pip install -r requirements.txt` that bai o `chroma-hnswlib`; Ollama khong co trong PATH — can fallback lexical cho den khi moi truong san sang.

## V1 Stack Target (2026-05-22 — hoan tat phien)

1. **Chroma tren Python 3.13.7**: dung `chromadb>=1.5.9` (binary wheel), khong can MSVC Build Tools (khac voi pin `0.6.3` + `chroma-hnswlib`).
2. **Ingest full corpus**: 658 chunks, 21 files; PDF `ESG-X02_unilever_annual_report_2025.pdf` **loaded, 450 chunks** — artifact `reports/v1-ingest-report-20260522-095522.md`.
3. **Retrieval mode**: `semantic` qua LangChain Chroma + `all-MiniLM-L6-v2`.
4. **LLM mode thuc te**: `extractive` (Ollama khong co; `OPENAI_API_KEY` khong set). Co the bat bang `RAG_LLM_MODE=openai_api` hoac cai Ollama.
5. **Eval**: smoke `reports/v1-baseline-smoke-20260522-095605.md` (10 cau); full `reports/v1-baseline-full-eval-20260522-095816.md` (50 cau).
6. **Full eval metrics**: retrieval_hit_rate 0.72, citation_correctness 0.46, groundedness 1.0, answer_correctness 0.6, insufficient_information_handling 1.0; pass/partial/fail = 20/27/3.
7. Lexical fallback van giu trong `evidence_rag.py` khi Chroma DB khong ton tai.

## Version 2 Eval Pipeline (2026-05-22)

1. Parser/validator: `src/eval_set_io.py` — 8 cot, 50 rows valid.
2. Scoring V2: `src/eval_scoring_v2.py` — alias source, citation top1+topk, groundedness claim+overlap, answer numeric/boolean/insufficient.
3. Runner: `src/run_v2_eval.py` — mode extractive (+ generative khi co Ollama/API).
4. Extractive full eval: retrieval_hit 0.72, citation 0.46, citation_topk 0.72, groundedness 1.0, answer 0.58, insufficient 1.0, pass/partial/fail 18/27/5.
5. Top errors: citation_top1_miss, answer_mismatch, retrieval_miss (xem report).
6. Generative mode chua chay — blocker giong V1 (Ollama/API).
7. So voi V1 scoring cu: pass_rate giam nhe (36% vs 40%) do tieu chi chat hon; insufficient van 100%.

## Version 2.1 Cleanup + Re-eval Gate (2026-05-22)

1. Fix data: ESG-E14 expected `downloaded` (khop `sources.md` ESG-C07).
2. Scoring: reason codes chuan + `format_per_question_score` (id, overall, metrics, reason_codes, top_evidence_sources).
3. Re-eval extractive: retrieval 0.72, citation 0.46, groundedness 1.0, answer 0.52, insufficient 1.0; pass/partial/fail 17/27/6.
4. Regression vs V2: hau het khong_doi; answer_correctness xau_hon nhe (0.52 vs 0.58) do rule answer_numeric_mismatch chat hon, khong phai retrieval regression.
5. ESG-E14: pass sau fix (truoc: partial).
6. Gate 1-4 PASS trong `v2_1-re-eval-gate-20260522-110201.md`.
7. Generative van blocker (Ollama/API).

## Version 3 Improved Retrieval (2026-05-22)

1. Modules: `retrieval_v3.py`, `run_v3_eval.py`; config HYBRID_ALPHA, CANDIDATE_POOL_SIZE, FINAL_TOP_K, RERANK_*.
2. Benchmark 50 cau (extractive answer, scoring V2):
   - semantic_dense: ret 0.72, cit 0.46 (baseline V2.1)
   - bm25_lexical: ret 0.76, cit 0.60
   - hybrid_dense_bm25: ret 0.80, cit 0.44 (retrieval tot, citation giam)
   - hybrid_dense_bm25_rerank: ret 0.80, cit 0.60, answer 0.56 — **best**
3. Gates V3: retrieval tang, citation tang, grounded>=0.95, insufficient>=0.95 — PASS.
4. Rerank: CrossEncoder `ms-marco-MiniLM-L-6-v2` chay duoc; fallback overlap neu loi.
5. Artifact: `reports/v3-compare-retrieval-modes-20260522-113046.md`.

## V3.1 Generative Baseline (2026-05-22)

1. Code: `llm_runtime.py`, `query_v3(..., answer_mode=generative)`, `run_v3_1_eval.py`.
2. Extractive rerun (cung script): ret 0.80, cit 0.60, answer 0.56, insuf 1.0, pass 52%.
3. Generative: **blocked** — Ollama khong trong PATH, OPENAI_API_KEY chua set.
4. Artifacts (lan 1): `v3_1-eval-generative-20260522-113845.md`, `v3_1-compare-extractive-vs-generative-20260522-113845.md`.
5. Khuyen nghi tam thoi: **giu extractive**; generative can Ollama pull hoac API key.

## Post-roadmap Hardening (2026-05-22)

1. Modules: `normalize_v6.py`, `hardening_config.py`, `hardening_orchestrator.py`, `run_hardening_benchmark.py`.
2. Fix `water_reuse_target`: `parse_water_reuse_target` — khong con nham 100% wastewater; `water_reuse_wrong_100_count=0` tren moi config mixed.
3. Matrix 4 configs: current, no_policy_boost, public_only, mixed_strict — reports `hardening-test-matrix-*.md`.
4. **Public-only rerun (corpus filter day du):** coverage 0.11, priority 0.0, insufficient 0.89 — phan anh overfit synthetic khi dung mixed corpus.
5. Mixed + no_boost van coverage cao (~1.0) vi retrieval van hit synthetic/PDF trong index; public-heavy can parser PDF/table rieng.
6. Observability: `trace_hardened.json`, `verification_hardened.json` co per-field latency, candidates, resolve_reason.

## Version 6 Advanced RAG (2026-05-22)

1. Modules: `router_v6`, `verification_v6`, `conflict_resolver_v6`, `orchestrator_v6`, `run_v6_workflow.py`.
2. Flow: per-field route (numeric/boolean/table/conflict_prone) -> extract -> verification loop (rewrite + fallback mode) -> source-rank conflict resolve -> policy_file_boost.
3. Run `demo_v6_001`: verify trigger 3, success 1.0, priority_completion 1.0 (vs V5 0.0); insufficient 0, conflict 0.
4. Delta vs V5: coverage +0.11, verified +0.32, insufficient -0.18, conflict -0.14, priority +1.0.
5. Artifacts: `artifacts/v6_runs/demo_v6_001/*`, `reports/v6-workflow-report-*.md`, `reports/v6-vs-v5-comparison-*.md`.

## Version 5 Workflow / Product-Oriented (2026-05-22)

1. Modules: `workflow_v5.py`, `gap_analysis_v5.py`, `report_v5.py`, `run_v5_workflow.py`.
2. Flow: intake_input -> load_or_select_corpus -> retrieve_evidence -> extract_structured_data (V4) -> gap_analysis -> generate_report.
3. Intake: `data/rag_dataset/v5_intake_template.json`; output `artifacts/v5_runs/<run_id>/`.
4. Run `demo_v5_001`: E2E ~106s, execution_success true, coverage 0.89, priority_risk_high 7.
5. Artifacts: intake_resolved, extracted_profile, gap_analysis, workflow_log + `reports/v5-workflow-report-*.md`.

## Version 4 Structured Extraction (2026-05-22)

1. Schema: `data/rag_dataset/esg_extraction_schema_v1.json` — 28 field (E:8, S:8, G:7, Metadata:5).
2. Pipeline: `extraction_v4.py` + `run_v4_extraction.py`; retrieval `hybrid_dense_bm25_rerank`; extractive/heuristic only.
3. Output record: field, value, evidence_text, source, citation, confidence, status.
4. Metrics (run `20260522-142211`): coverage 0.89, verified 0.68, insufficient 0.18, conflict 0.14, evidence_presence 1.0.
5. Artifacts: `artifacts/v4_extracted_profile_20260522-142211.json`, `reports/v4-extraction-report-20260522-142211.md`, `reports/v4-extraction-eval-20260522-142211.md`.
6. Han che: boolean/table field (wastewater, water_reuse); women_mid_management lay cot 2025 thay vi target 2027; conflict nhe o whistleblowing/LTIFR.

## V3.1 Unblock attempt (2026-05-22, lan 2)

1. Runtime check: `ollama` khong trong PATH; `OPENAI_API_KEY` khong set; khong tim thay `ollama.exe` tai `C:\Program Files\Ollama` hoac `%LOCALAPPDATA%\Programs\Ollama`.
2. Khong the chay `ollama pull qwen2.5:7b-instruct` hoac OpenAI path — chuyen buoc 4 (blocker report).
3. `python src/run_v3_1_eval.py` chay lai: extractive on dinh; generative van blocked.
4. Artifacts moi nhat: `reports/v3_1-eval-generative-20260522-114712.md`, `reports/v3_1-compare-extractive-vs-generative-20260522-114712.md`.
5. Delta extractive vs generative: **n/a** (generative chua chay).

## Re-plan after dataset contract v1.1 (2026-05-28)

1. Khi dataset da chuan hoa theo contract v1.1, benchmark phai chay theo 3 lane ro rang (dev/validation/final) de tranh overfit va tranh ket luan tu mot lane.
2. So sanh model phai tach 2 lop: retrieval-only gate truoc, full-pipeline confirm sau; neu tron ngay se kho phan biet loi do retrieval hay do extraction/report.
3. Dung fail reason taxonomy (timeout, invalid_case_output, model_not_cached_local, ragas_disabled) la bat buoc de ket luan cong bang.
4. Winner nen chot theo composite co trong so retrieval_hit_rate + citation_correctness + answer_correctness + insufficient_handling, khong chot theo 1 metric don le.

## Dataset intake check: Nexteye package (2026-05-28)

1. Package da duoc copy vao `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T082146`.
2. Manifest/split/checksum hop le: `record_count=273`, split `117/106/50` khop thuc te va checksum match.
3. Kiem tra schema-required pass: khong thieu field bat buoc, khong co record `text` ngan hon 50 ky tu.
4. Diem can xac nhan voi team Dataset: `source_url` dang null 273/273 trong records, trong khi `manifest.source_count=193`; chua co quy tac doi chieu ro rang tu package hien tai.

## Resources

1. Bao cao tong hop RAG Pipeline.
2. Bao cao phan tich cong cu RAG Pipeline.

## Benchmark Config Research (AutoRAG / ragflow / haystack)

1. **AutoRAG**: pattern manh nhat la `config YAML + evaluator runner + summary.csv` va so sanh pipeline theo node combinations co dinh. Bai hoc ap dung: matrix phai khai bao ro dimensions, khong random, va report top config theo metric.
2. **ragflow**: nhan manh trade-off chunking (small chunk vs context integrity), retrieval hybrid keyword+vector, citation grounded, va parser/chunking theo loai tai lieu (PDF/HTML/table). Bai hoc ap dung: giu retrieval + extraction flow co dinh, chi thay 4 bien matrix de fair comparison.
3. **haystack**: uu diem o component modular + pipeline minh bach, de thay/swap retriever/reranker/evaluator ma khong doi kien truc tong the. Bai hoc ap dung: benchmark runner nen la lop orchestration ben ngoai, khong refactor lon backbone V6.
4. Ket luan cho repo hien tai: benchmark dung matrix 36 cases co kiem soat, output csv/md/html, metric ESG/evidence la metric chinh; RAGAS de bo sung va co fallback khi khong co API key.

## Benchmark Optimization Findings (Stage-wise + Multi-lane)

1. Chay full-factorial 36 cases tren full corpus ngay lap tuc gay ton thoi gian lon, khong phu hop de iteration nhanh.
2. Stage-wise cho phep loai config yeu som:
   - Round A (chunking/embedding/retrieval/reranker) de shortlist.
   - Round B (focused combos) de so sanh chat hon.
   - Round C (final confirm) cho top 2-3.
3. Dataset lanes (dev/validation/full) giup can bang toc do va do tin cay:
   - dev de scan nhanh,
   - validation de xac nhan,
   - full de chot.
4. Cache key can co `parser_version + chunking_config + embedding_model + corpus_version`; neu chi doi retrieval/reranker thi co the reuse index.
5. Tach `retrieval_only_benchmark` khoi `full_pipeline_benchmark` giup tiet kiem thoi gian: retrieval gate truoc, full pipeline sau.

## Execution Planning Findings

1. Nhu cau hien tai la clarity ve thu tu hanh dong hon la mo rong code them.
2. Prompt theo pha (A/B/C) giup giam sai lech khi handoff sang Cursor.
3. Checkpoint theo lane + mode + output file giup quy trinh de audit va de tiep tuc giua cac phien.
4. NotebookLM nen duoc dung cho tong hop trinh bay, khong tham gia thay benchmark engine.

## Benchmark Pha A Findings (2026-05-27, stagewise dev retrieval_only)

1. Run ID `bench_20260527-103808_*`: 10 case stage-wise, lane `dev`, eval subset 40 cau, corpus ratio 0.2.
2. Metric noi bo (8 case success): `retrieval_hit_rate` 0.2 (baseline dense/semantic); `hybrid_bm25_dense` dat 0.45 (+125% so dense); `citation_correctness` 0.2 dong deu; `composite_score` TB ~0.309, max 0.375 (`stageA_retrieval__hybrid_bm25_dense`).
3. Chunking (3 case): `recursive_800_120`, `recursive_512_80`, `section_based` bang nhau tren metric dev (hit 0.2, composite 0.3) — chua tach duoc uu the o lane dev.
4. Embedding: chi `all-MiniLM-L6-v2` chay thanh cong; `bge-m3` va `multilingual-e5-base` fail `model_not_cached_local` (khong ket noi HuggingFace, khong co cache).
5. Reranker: `none` vs `bge_reranker_or_flashrank` bang nhau khi retrieval_mode van `semantic_dense` (reranker case khong bat hybrid override trong stage A).
6. RAGAS: tat ca case success co `ragas_status=disabled`, `ragas_reason=OPENAI_API_KEY_missing` — metric noi bo van du de shortlist Pha A.
7. Shortlist de xuat Pha B: uu tien `hybrid_bm25_dense`; chunking giu `recursive_800_120` (baseline V6); embedding `all-MiniLM-L6-v2`; reranker can test lai o focused khi ket hop hybrid.

## Benchmark Replan Findings (2026-05-27)

1. Batch `111821` la baseline day du (13 case); khong can chay lai 10 case stagewise dev neu resume bật.
2. `dev_chunking_ids` (3 dai dien) giam tu 6 xuong 3 chunking stage — ly do metric dev khong phan hoa.
3. Runner moi: `matrix_hash`, resume skip success, timeout 1200s, `error_code`, dry-run khong ghi de CSV.
4. RAGAS: stagewise → skipped; focused/final → `--enable-ragas` + OPENAI_API_KEY; tich hop RAGAS day du chua co.
5. ai-gemma4: chi adopt logging/error taxonomy/retrieval audit — khong Qdrant/FlagEmbedding/MLX.

## Benchmark Fairness + company_public_dev (2026-05-27)

1. **Bug da fix:** `_embeddings()` doc `RAG_EMBEDDING_MODEL` runtime; `stageA_reranker` chay tren `hybrid_bm25_dense` (+ pool 64, rerank path).
2. **Khong dung batch `144412`:** reranker van `semantic_dense` → ket luan reranker vo nghia.
3. **Batch `155224` (sau fix):** lane `company_public_dev` metric spread lon hon `dev` (hit ~0.03–0.57 vs ~0.2–0.45).
4. **Chunking/embedding (semantic_dense):** van dong metric tren lane moi (0.5667 hit) — can so sanh khi embedding case chay xong.
5. **bge-m3 / e5:** timeout 1200s khi ingest 200 PDF — can timeout rieng hoac corpus nho hon cho stage embedding.
6. **Reranker sau fix:** `none` hybrid hit 0.33 > `bge_reranker` hybrid_rerank hit 0.03 tren lane nay (can xem lai reranker model/cache).

## External Project Scan: ai-gemma4 (E:\Documents\RAG-clone\ai-gemma4)

1. Kien truc du an theo huong enterprise RAG kha day du: parser/chunker/embedder/retriever/reranker/generator + ACL + audit + evaluation + UI + infra scripts.
2. Stack retrieval trung tam: Qdrant + BGE-M3 (dense+sparse) + hybrid retrieval (RRF) + optional HyDE/CRAG/query rewrite/decomposition/agentic flags.
3. `src/rag/pipeline.py` cho thay pipeline co nhieu guardrail (ACL recheck truoc LLM, low-confidence prefix, citation checks, audit events), phu hop bai toan kiem soat rui ro.
4. `src/rag/retriever.py` co filter ACL, hybrid query API cua Qdrant, va fallback dense-only; diem manh la retrieval modular theo config env.
5. `src/rag/indexer.py` co batch upsert + retry + payload metadata day du (classification/acl_tags/parent-child), phu hop van hanh corpus lon.
6. Dependency footprint nang hon repo hien tai (Qdrant, FlagEmbedding/BGE-M3, ragas, streamlit, mlx-lm, nhieu infra script), can effort MLOps cao hon neu adopt toan bo.
7. Du an co test surface lon (100+ test files) va nhieu tai lieu ADR/architecture, tot cho tham chieu quy trinh engineering, nhung khong nen copy nguyen khoi vao workflow practice gon nhe.

## Model candidate overnight — audit thoi gian (2026-05-28)

1. **9/9 case da ghi CSV** truoc mat dien; "chua xong" = 5 case khong co metric (3 BGE timeout + 2 fail), RAGAS chua chay.
2. **~6h la 3 x timeout 7200s** cho BGE — moi lan ingest chua xong bi kill, lan sau ingest lai (khong co index hoan chinh).
3. Script PS1 cu ep `--timeout-sec 7200` du yaml ghi 10800 cho embedding nang.
4. e5 hybrid_rerank: **index_build ~40 phut** — 1 lan ingest thanh cong; du bao BGE tuong tu neu prebuild 1 lan.
5. Recovery nhanh: `scripts/run_fast_model_recovery.ps1` (~2-3h), khong rerun full 9 case. Chi tiet: `reports/model_candidate_time_audit.md`.

## Benchmark quick patch (2026-05-28)

1. Da them parser PDF theo co che `docling` optional-fallback trong `rag_common.py` (`RAG_PDF_PARSER=auto|docling|pypdf`).
2. Da them metadata ingest cho moi chunk/doc (`company`, `doc_group`, `source_tier`) trong `rag_stack.py`.
3. Da bo sung metadata-aware retrieval filter trong `retrieval_v3.py` (dense + bm25) khi bat `RAG_METADATA_AWARE_RETRIEVAL=true`.
4. Da bo sung co `--metadata-aware` cho `run_benchmark_case.py` de bat/tat theo lane benchmark.
5. Da sua bug `effective_embedding` chua khoi tao trong nhanh fail cua benchmark case.
6. Da mo duong chay Qdrant local trong `run_benchmark_case.py` + `rag_stack.py` (bo hard-block, dung `RAG_VECTOR_STORE=qdrant`, index path rieng).
7. Da nang cap `prebuild_benchmark_index.py` de build truoc index cho **nhieu embedding** va cho ca `--vector-store chroma|qdrant`; muc tieu la khong ingest lap lai trong benchmark.
8. Da cai `docling` thanh cong, nhung smoke test tren sample PDF `nexteye/general/*.pdf` van tra rong; parser fallback `pypdf` van can de giu ingestion on dinh.
9. Metadata-aware retrieval da co fallback auto khi no-hit: `no-hit-after-metadata-filter;fallback_no_filter` trong `retrieve_note` (khong bi ket qua rong khi filter qua chat).
10. Da giam nguy co case bi kill/treo benchmark bang 3 thay doi:
   - Embedding runtime bat `local_files_only` trong benchmark (`RAG_EMBED_LOCAL_ONLY=true`) de tranh retry HuggingFace.
   - Benchmark parser mac dinh ve `pypdf` thay vi docling (toc do/on dinh cao hon cho lane hien tai).
   - Resume benchmark khong con skip case qdrant bi block cu, cho phep rerun case Qdrant that.

## Dataset Team Contract Insight (2026-05-28)

1. JSON export co the giup giam thoi gian thu thap/curation, nhung neu thieu schema traceability thi benchmark evidence se lech.
2. Team RAG can mot data contract ro rang (schema + manifest + checksum + known issues) de tranh run thu nghiem mo ho.
3. Khong nen trộn `public_raw_lane` va `dataset_export_lane` khi benchmark chinh, vi muc do kho retrieval khac nhau.
4. Ban send-off v1.1 can co them benchmark split (`dev/validation/full`) va acceptance gate so luong de hai team dong bo nhanh.

## Dataset Package Review: Nexteye Export (2026-05-28)

1. Package `05_company_export_json/넥스트아이_dataset_package_20260528T082146` dat layout contract co ban: `README.md`, `manifest.json`, `schema.json`, `splits/*`, `records/full.jsonl`, `known_issues.md`.
2. `manifest.json` khai bao 273 records, 272 documents, 1 company, split dev=117/validation=106/full=50; schema version 1.1 va checksums co mat.
3. Diem tot: JSONL co `record_id`, `doc_id`, metadata source_path, `is_raw_text`, `is_derived_summary`, `derived_from_doc_ids`, `esg_tags`; co the ingest/validate co ban.
4. Rui ro lon: `README.md` ghi `splits/full.jsonl` la derived summary lane, mau full co `is_raw_text=false`, `is_derived_summary=true`; khong nen dung lam full benchmark chinh raw evidence.
5. Rui ro traceability: `source_url` null toan bo theo known issue; voi news/web/public source nen map URL ra field rieng thay vi chi de trong text/metadata.
6. Rui ro metric: nhieu record co `metric.metric_name=esg_metric` va `value_raw` lay ma cong ty, market cap, relevance/completeness `100%` thay vi metric ESG doanh nghiep; khong nen dung metric object cho scoring extraction khi chua lam sach.
7. Rui ro typing: mot so DART/news/taxonomy requirement rows duoc map vao `source_type` nhu `annual_report`/`policy` chua chinh xac voi y nghia contract.
8. Khuyen nghi: chi dung dev/validation raw lane cho smoke retrieval truoc; yeu cau Dataset team tach `requirements/taxonomy` khoi company evidence va sua metric/source_url truoc full benchmark.

## Dataset Package Review: Nexteye v1.1.1 (2026-05-28)

1. Package moi `넥스트아이_dataset_package_20260528T085019` da duoc copy vao `data/rag_dataset/05_company_export_json`.
2. Manifest: `dataset_version=1.1.1`, `record_count=270`, `document_count=262`, `source_count=92`, split dev=77/validation=93/full=170.
3. Cau truc da dung huong bai toan ESG response readiness: co lane rieng `company_evidence` (170), `requirement_taxonomy` (50), `ai_extracted_response` (50).
4. README xac nhan `splits/full.jsonl` la full raw company evidence lane, khac voi ban truoc full la derived summary.
5. Schema da them `record_role`, `source_system`, va `metric.metric_kind` voi enum `company_reported_metric`, `requirement_metric`, `internal_score`.
6. Known issue con lai: internal/local artifacts khong co public URL; chap nhan tam thoi neu `metadata.source_path`, `metadata.source_system`, `doc_id` du trace.

## Export JSON 3-phase Benchmark Findings (2026-05-28)

1. Overnight-safe runner da thong luong: checkpoint sau moi case, phase-specific CSV, log rieng `exportjson_overnight_3phase_20260528-170617.log`.
2. Smoke 2 case MiniLM tren `splits/dev.jsonl` chay thanh cong, xac nhan loader chi doc dung package `091409`.
3. Pha 1: trong cac case co model local, `recursive_800_120 + MiniLM + hybrid_dense_bm25 + Chroma` dat composite cao nhat (0.345, hit 0.25).
4. BGE-M3 va multilingual-e5-base chua the so sanh thuc vi khong co local cache; 12 case fail nhanh `model_not_cached_local`, khong bi treo/kill.
5. Pha 2: reranker `cross-encoder/ms-marco-MiniLM-L-6-v2` khong cai thien metric tren lane nay, va lam query avg tang tu ~0.2s len ~5.6s/cau.
6. Pha 3: Qdrant da chay duoc, metric chat luong ngang Chroma tren top configs; query avg Qdrant nhe hon nhung chua du bang chung chot production winner.
7. Candidate tam thoi: `recursive_800_120 + sentence-transformers/all-MiniLM-L6-v2 + hybrid_dense_bm25 + reranker=none`; Chroma la safe default, Qdrant la ung vien scale.
8. Can align lai eval/source aliases va answer scoring theo package ESG moi, vi metric retrieval/citation/answer con thap so voi muc tieu.
9. Windows path warning xuat hien khi cache key nhung nguyen ten package tieng Han; da patch cache/manifest key sang hash ngan de giam rui ro path too long cho cac lan chay sau.
10. Script overnight co `-Fresh` de archive artifact cu truoc khi chay lai tu dau; mac dinh van resume de khong mat ket qua khi bi kill.

## Overnight Preparation Findings (2026-05-28, buoi toi)

1. Bug retrieval lane da xac nhan: `_source_allowed_for_lane` truoc do chi filter `company_public_dev`; vi vay lane `company_export_json_*` bi leak source tu `04_company_public_curated`, lam reranker bi danh gia sai.
2. Sau khi patch lane filter, smoke benchmark tren package `091409` cho thay top sources chi con trong `05_company_export_json`; khong con evidence leakage tu lane khac.
3. Eval set `eval_set_company_export_json_dev.md` dang tro expected source cu (`...esg_export_20260528T071604.json`), can align sang package moi de retrieval/citation metric phan anh dung.
4. Local cache hien tai: `sentence-transformers/all-MiniLM-L6-v2` va reranker `cross-encoder/ms-marco-MiniLM-L-6-v2` co san; `BAAI/bge-m3` va `intfloat/multilingual-e5-base` chua co.
5. Thu tai model truc tiep bi chan mang he thong (`WinError 10013` toi `huggingface.co`), khong phai timeout benchmark logic.

## Fairness + Dimension Findings (2026-05-28, rerun sau fix)

1. Lỗi dimension `expected 384, got 1024/768` không phải do model hỏng, mà do Chroma collection bị dùng chéo giữa các embedding profile.
2. Sau khi tách `collection_name` theo hash cache key và rerun Pha 1, toàn bộ 18 case (MiniLM/BGE/e5) đều chạy success.
3. Pha 2 apples-to-apples (cùng `candidate_pool=64`, cùng retrieval family) cho thấy reranker vẫn kém hơn none trên dataset hiện tại, nên kết luận nghiêng về không phù hợp domain/ngôn ngữ hơn là bug runtime.
4. `source_alias_issue` vẫn xuất hiện nhiều do eval đang chấm theo `splits/*.jsonl` file-level, chưa chấm tới record/chunk evidence-level; đây là nhiễu metric còn lại cần xử lý để “test tốt” thật sự.

## Hyundai-only Benchmark Setup (2026-05-28)

1. Giam `04_company_public_curated` tu 5 cong ty xuong 1 cong ty co the giam parse/chunk/embed/index gan tuyen tinh theo so file/chunk.
2. Hyundai Motor la lane 1-cong-ty phu hop nhat hien tai vi eval company public dang tap trung nhieu cau Hyundai va co du E/S/G, policy, sustainability report, EN/KO.
3. Can eval subset rieng: neu giu cau positive cua Hansem/Musinsa/Dunamu/Nexteye khi corpus chi con Hyundai thi metric se fail gia.
4. Runner can tach cache key theo company (`__company=hyundai_motor`); neu khong, `reuse-index` co the dung lai index 5 cong ty va lam sai ket qua.
5. Thu tu test da chot:
   - Phase 1: MiniLM dense vs hybrid vs hybrid_rerank tren Chroma.
   - Phase 2: BGE-M3 vs multilingual-e5-base tren retrieval winner, Chroma.
   - Phase 3: rerank cho embedding tot nhat/gan tot nhat.
   - Phase 4: Qdrant comparison cho winner, khong nhan full matrix.
6. Trong phien nay shell agent khong thuc thi lenh runtime (`py_compile` khong xuat hien trong terminal transcript), nen benchmark chua chay that duoc tu agent.

## Eval matcher export JSON (2026-05-29)

1. Validation OpenAI hit=0 truoc day la do matcher file-level: eval `splits/dev.jsonl` + folder mojibake, corpus `splits/validation.jsonl` + UTF-8 dung — retrieval tra dung file nhung scorer fail.
2. Matcher moi (`eval_source_matcher.py`) uu tien `dataset_package_<timestamp>` cho split alias; sau fix: hit=1.0, citation=1.0 tren 4 config validation.
3. Nen sua eval set UTF-8 cho expected_source; matcher da bypass nhung audit van hien mojibake o normalized_expected.

## P0.1 CE-J03-J07 export JSON (2026-05-29)

1. Hit=1 + answer fail do top chunk sai record (news/garbled), khong phai miss file — matcher `package_split_match` qua rong.
2. J06-J08 expected sai so voi `manifest.json` (`company_esg_dataset`, version `1.0`, timestamp cu).
3. J05 URL `http://www.nexteye.com` nam trong probe profile chunk, khong trong homepage records rieng.
4. Fix retrieval: `export_json_retrieval_hints.py` (field boost, BM25 query expansion, runtime manifest inject).
5. Fix eval: cap nhat expected J05-J08; `EXTRACTED_FIELD_ALIASES` trong scoring.
6. Corpus manifest them `manifest.json` + `README.md` cho lane export JSON (can re-index de on dinh).

## External reference review: Gemma 4 MVP report (2026-06-02)

1. Bao cao `보고서 11_ Gemma 4 MVP 테스트 결과 분석 (2026-06-01).docx` co gia tri tham khao ve test discipline hon la retrieval winner:
   - 122 unit/security/integration tests PASS
   - co bug log ro rang (`BUG-001`)
   - co phan "allowed vs not allowed conclusions"
   - co bang tach Local CPU / GPU Production / Cloud API
2. Phan benchmark trong bao cao do la `retrieval_only`, RAGAS bi skip, va answer quality/generation quality chua duoc do day du; vi vay khong the dung de so sanh truc tiep voi OpenAI E2E lane da chay trong repo nay.
3. Cac so "minilm hybrid tot nhat", "bge-m3 dense duoc de xuat", "latency 0.018s" phu thuoc dataset, scoring va harness cua du an kia; khong nen import vao bao-cao-10/11 nhu mot bang chung benchmark cho Nexteye ESG.
4. Phan co the tai su dung cho repo hien tai:
   - ro hoa gate "duoc ket luan / chua duoc ket luan"
   - tach benchmark retrieval-only voi full generation quality
   - bo sung load/SLO test rieng thay vi tron vao benchmark retrieval
   - ghi bug/runtime issue thanh artifact chinh thuc truoc khi chot stack
5. Phan khong nen mang ve nguyen xi:
   - ket luan embedding winner tu bo benchmark khac
   - gemma4/Ollama-specific stack recommendation
   - so sanh dense/hybrid neu khong cung eval matcher va lane ESG hien tai

## Benchmark language alignment (2026-06-02)

1. Nguyen nhan lam RAGAS va answer scoring lech them la benchmark lane Nexteye dang hoi/expected bang tieng Viet trong khi corpus va answer tot nhat tu nhien la tieng Han.
2. Tu cac run tiep theo, benchmark input cho lane `company_export_json` duoc thong nhat sang tieng Han:
   - question
   - expected answer
   - insufficient canonical phrase
3. Bao cao ket qua cho user van viet bang tieng Viet; chi benchmark/runtime/eval moi chuyen sang tieng Han.
4. Da tao bo eval moi:
   - `.rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md`
   - `.rag/rag-pipeline-practice/eval_set_company_export_json_smoke_ci_ko.md`
5. Da doi prompt generative va `insufficient` runtime/scoring sang default `RAG_BENCHMARK_LANGUAGE=ko`.

## Eval answerable-only rerun (2026-06-03)

1. Bo eval dev KO rut con 15 cau co ground truth trong package `091409`; bo 5 cau insufficient va 3 cau field khong ton tai (completeness_score, profile_evidence, public_evidence).
2. Run E2E OpenAI (embed small, hybrid, reranker none, gpt-4o-mini): hit/cit 0.8667; answer 0.73-0.80; composite winner generative 0.7533.
3. Hai miss retrieval co dinh: CE-J04 (KOSDAQ market) va CE-J05 (homepage) — evidence rong trong audit; can dieu tra query/alias cho krx_meta va profile record.
4. GPU/Qwen/bge-reranker chua benchmark — doi pipeline on dinh hon theo bao cao 12.

## C2 RunPod benchmark (2026-06-03)

1. RunPod proxy port 8000 tra HTTP 403 neu dung User-Agent mac dinh cua Python `urllib`; LangChain/OpenAI SDK va curl mac dinh OK. Preflight da them UA.
2. URL `.env.c2` co `//v1` thua gay loi 403/404 — dung dang `https://<pod>-8000.proxy.runpod.net/v1`.
3. Benchmark C2 tu PC (rerank CrossEncoder CPU): hit/cit/answer bang OpenAI baseline; composite **0.7667** > 0.7533; latency 105s vs 183s; groundedness 0.7333 vs 0.60.
4. Gate C2 PASS; production YAML chua doi — can xac nhan trien khai.
## Golden set 3-company audit (2026-06-09)

1. Dataset dung cho giai doan golden set hien tai la 3 package trong `data/rag_dataset/05_company_export_json`:
   - `ë ˆì´ì‹œì˜¨_dataset_package_20260608T055801`
   - `ë¬´ì‹ ì‚¬_dataset_package_20260608T092823`
   - `í•œìƒ˜_dataset_package_20260608T042739`
2. Lane co gia tri de tim `gold_answer` la `company_evidence`; `ai_extracted_response` chi la output suy dien san, khong nen dung lam dap an dung.
3. Audit so bo cho thay:
   - `ë ˆì´ì‹œì˜¨`: nhieu snippet `official_sustainability_report` bi lech nguon/khong khop clean voi cong ty, nen phai gan `dataset_issue`.
   - `ë¬´ì‹ ì‚¬`: nhieu record nghieng ve trang listing/download bao cao, khong du noi dung ESG de tra loi theo cau hoi.
   - `í•œìƒ˜`: co the rut duoc mot so dap an dinh tinh co bang chung ro tu `company_evidence`.
4. Ban dien so bo `golden_answer_fill_preliminary_ko_20260609.csv` co 60 dong:
   - `filled_from_dataset`: 6
   - `partial_from_dataset`: 2
   - `not_found_in_current_dataset`: 12
   - `dataset_issue`: 40
5. Neu ap tieu chi chat cho `golden set v1` la chi nhan `filled_from_dataset`, tap dung duoc ngay hien tai chi con 6 cau, deu la `qualitative` va deu thuoc package `í•œìƒ˜`.

## Pipeline eval workbook v1 (2026-06-09)

1. De giam ma sat cho phase cham pipeline, nen co workbook rieng thay vi bat reviewer copy tay giua CSV va ket qua run.
2. Cau truc workbook toi thieu hop ly:
   - `Info`: huong dan nhanh
   - `GoldSet`: ban sao gold de doi chieu
   - `PipelineInput`: cho dan output pipeline
   - `Score`: auto check `EXACT` text va `evidence_record_id`, kem cot cham tay
   - `Summary`: tong hop so cau da tra loi va diem trung binh
3. Auto check chi co gia tri muc co ban; cac cau paraphrase dung nhung khac wording van can reviewer dien `manual_answer_score` / `manual_evidence_score`.

## Working set >=20 cho phase cham thuc dung (2026-06-09)

1. De workbook cham dung duoc thuc te hon trong khi dataset chua du sach, can tach khai niem:
   - `golden set`: chi gom cau co `gold_answer` va grounding chac chan
   - `working set`: gom them cau `partial` va `needs_review` de team van co tap lam viec du rong
2. Cach chon thuc dung nhat hien tai la lay toan bo `20` cau shortlist cua `í•œìƒ˜`, vi:
   - `레이시온` va `무신사` dang o trang thai `dataset_issue`
   - `í•œìƒ˜` la package duy nhat co mot phan grounding that su dung duoc
3. Mapping trang thai trong `working_set_v1`:
   - `filled_from_dataset` -> `grounded`
   - `partial_from_dataset` -> `partial`
   - `not_found_in_current_dataset` -> `needs_review`
4. Phan bo hien tai cua `working_set_v1`:
   - `grounded`: 6
   - `partial`: 2
   - `needs_review`: 12
5. `working_set_v1` phu hop cho vong danh gia/noi bo va de paste output pipeline vao workbook, nhung khong duoc bao cao nhu mot `golden set` da hoan tat.

## FlashRank runtime hardening (2026-06-10)

1. Runtime rerank truoc do chi ho tro `sentence_transformers.CrossEncoder`; chua co backend `FlashRank` that su.
2. Da tich hop backend `FlashRank` vao `src/retrieval_v3.py` voi co che:
   - `RAG_RERANK_BACKEND=flashrank|cross_encoder|auto`
   - auto detect `flashrank` khi model name dang `ms-marco-*` khong co namespace `/`
3. Default moi cho nhanh RAG hien tai:
   - `RAG_RETRIEVAL_MODE=hybrid_dense_bm25_rerank`
   - `RAG_RERANK_MODEL=ms-marco-MultiBERT-L-12`
4. `production_config` da duoc noi voi stack `OpenAI + Qdrant + FlashRank`, va benchmark runner da nhan `reranker_backend`.
5. Smoke import/runtime cho thay:
   - code path `FlashRank` da di dung
   - blocker con lai la lan tai model dau tien den HuggingFace bi chan (`WinError 10013`)
   - neu chua pre-seed cache, runtime se fallback overlap thay vi dung ONNX reranker that
6. Nghia la luong RAG da du thong day code/config, nhung de freeze rerank can mot trong hai dieu kien:
   - mo outbound HuggingFace
   - hoac copy san cache model `ms-marco-MultiBERT-L-12` vao may

## Jina rerank gate (2026-06-10)

1. Repo da co backend `jina_api` trong `src/retrieval_v3.py` va helper `src/jina_rerank.py`.
2. Production frozen moi la `configs/production_openai_hybrid_qdrant_jina.yaml`, khong phai FlashRank.
3. Gate `reports/benchmark_exportjson_openai_rerank_gate_summary.md` cho thay:
   - baseline `openai_hybrid_qdrant_none_gate`: composite `0.805`
   - `openai_hybrid_qdrant_jina_gate`: composite `0.755`
   - ca hai deu hit/citation `1.0`
4. Dung theo artifact hien tai, `Jina Reranker v3` da test thanh cong va da duoc freeze vao production, du composite van thap hon `none`; nghia la quyet dinh production uu tien stack da chot/on dinh thay vi metric composite don le.
5. De chuyen sang Golden set, can xem FlashRank la lane thu nghiem da dong, va Jina la production reference hien tai.

## Tong hop 4 tai lieu Golden Set va tooling (2026-06-10)

1. Ca 4 tai lieu dong quy rang `golden set` cua RAG phai la tap `question + context + ground_truth`, trong do `ground_truth` duoc con nguoi xac nhan; no duoc dung de danh gia retrieval, generation, va regression test.
2. Quy trinh cot loi lap lai nhieu nhat la mo hinh `Silver -> Gold`:
   - dung LLM sinh bo `silver` quy mo lon
   - loc tu dong theo answerability/do kho/grounding
   - human/SME review de sua, xac nhan dap an, them edge case
   - version hoa thanh `golden set`
3. Tai lieu so sanh phuong phap tu dong hoa ket luan cach phoi hop hop ly nhat la:
   - `Distillation` de mo rong nhanh
   - `Evol-Instruct` de tang do kho/da dang tren mot phan bo mau
   - `LLM-as-a-judge` de cham loc/phan hang truoc vong human review
4. Ve cong cu:
   - `Ragas` manh o generation da dang va metric danh gia RAG, nhung ton token/chi phi hon
   - `DeepEval` manh o API/workflow don gian va CI/CD-friendly, nhung do da dang generation thuong phu thuoc prompt nhieu hon
   - `Giskard` hop cho edge case/adversarial testing hon la sinh bo gold chinh
   - `Phoenix` manh ve observability/debugging
   - `TruLens` manh o giam sat bo metric `Groundedness / Context Relevance / Answer Relevance`
5. Bo 3 metric phai bam khi xay va loc mau:
   - `Faithfulness`: cau tra loi co trung thuc voi context hay khong
   - `Answer Relevancy`: cau tra loi co dung tam cau hoi hay khong
   - `Groundedness`: cau tra loi co bam sat evidence/chung cu hay khong
6. Doi voi 2 mau CSV ESG:
   - file `dinh luong` phu hop sinh cau hoi factoid/metric/comparison dua tren cac cot chi tieu, don vi, GRI/SASB
   - file `dinh tinh` phu hop sinh cau hoi theo 4 tru cot `Strategy / Governance / Risk Management / Metrics`, va chi nen nang cap thanh cau hoi suy luan khi van giu duoc grounding ro
7. Rang buoc lon nhat rut ra tu tai lieu la: cau hoi kho hon khong duoc danh doi bang viec giam `answerability` hoac lam mo `ground_truth`; vi vay bo loc grounding va human review la bat buoc.

## Reset theo workbook tham chieu (2026-06-11)

1. Workbook tham chieu `golden_set_3companies_v4.xlsx` va bao cao `golden_eval_report_en_ko.docx` cho thay bai toan dung la `workbook-first`, khong phai `single-unit QA hard gate`.
2. Mot `passage_text` ESG tot co the sinh nhieu seed hop le (`quantitative`, `trend`, `qualitative`, `unanswerable`), trong khi nhanh R2.1-R2.4 dang ep `1 unit -> 1 QA`.
3. Bao cao tham chieu dat `23/24 pass` nhho toi uu `query/eval strategy`, khong phai cat manh yield o buoc distillation.
4. Da them builder moi:
   - `src/golden_set/build_reference_seed_workbook.py`
   - `scripts/build_reference_seed_workbook.py`
5. Chay that builder tren `118` corpus units cho ket qua vong dau:
   - `raw_candidates=180`
   - `deduped_candidates=162`
   - `selected_rows=24`
6. Dieu nay xac nhan he thong van co kha nang sinh duoc pool ESG seed co quy mo workbook.
7. Khi siet contamination, so seed giam manh; nghia la van de data layer hien tai la `corpus_units.jsonl` dang tron:
   - `news chrome`
   - `listing/archive`
   - `contact/satisfaction page`
   - `analyst/financial text`
   - `cross-company contamination`
8. Ket luan: van de goc la `objective/gating + contaminated corpus`, khong phai AI khong tim duoc ESG fact.

## Workflow report framing (2026-06-11)

1. O thoi diem hien tai, workstream `Golden Set` nen duoc bao cao theo **quy trinh 6 buoc** thay vi chot metric/accuracy cuoi, vi bo workbook van dang trong cac vong review, rewrite va canonicalization.
2. Cach dien giai dung de stakeholder de hieu la:
   - `jsonl passage`
   - `candidate workbook`
   - `triage round`
   - `lane-based manual review`
   - `canonicalization`
   - `review-ready set`
   thay vi mo ta nhu pipeline co ngay `gold row` o dau ra.
3. O workstream `LangGraph staging retrieval`, van de can bao cao khong phai la doi 1 tham so trong YAML, ma la sua duong di service/runtime de retrieval mode trong config thuc su co tac dung.
4. Vi vay bao cao ngay nen uu tien:
   - giai thich ro quy trinh dang lam
   - phan biet phuong phap voi ket qua cuoi
   - va mo ta de hieu cac sua doi retrieval trong staging.
5. Doi voi bao cao stakeholder/noi bo nhanh, dang trinh bay phu hop hon la:
   - `Golden Set`: mo ta bang workflow 6 buoc + so do truc quan
   - `LangGraph staging retrieval`: chi noi `nguyen nhan -> huong sua`
   - tranh ke lai lich su "da lam sai cai gi" neu muc tieu la bao cao cong viec trong ngay.

## RTX raw dataset intake (2026-06-12)

1. Thu muc `C:\\Users\\nguye\\Downloads\\data-company\\demo_company\\RTX_References\\References` hien tai co `4` PDF local:
   - `2023-ESG-ESGAppendix.pdf`
   - `2025 CDP RTX Corporation Questionnaire.pdf`
   - `RTX Corp 2023 EEO-1.pdf`
   - `RTX_Performance Data Tables and Indexes_8125.pdf`
2. Trong cay `RTX_References` khong thay file HTML local; phan HTML/web user cung cap hien dang ton tai duoi dang URL tham chieu.
3. Da tao lane moi `data/rag_dataset/06_rtx_references_raw` va copy 4 PDF vao `_sources/`.
4. Da them `source_urls.json` de giu 6 URL web tham chieu lam provenance cho buoc ingest/chunk sau.
5. Do PowerShell trong moi truong hien tai khong ket noi duoc ra ngoai, raw HTML khong tai truc tiep ve workspace; thay vao do da luu `6` file `web_sources/*.md` o dang text snapshot local.
6. Lane RTX moi hien co ca:
   - `4` PDF local
   - `6` web text snapshot local
7. Lane RTX moi hien o trang thai:
   - raw
   - chua chunk
   - chua ingest
   - chua benchmark
8. Lane nay phu hop lam dau vao moi de chay lai ca:
   - chunking cho RAG
   - corpus-unit / candidate generation cho Golden Set

## RTX workbook-first reset and v2.1 stop-point (2026-06-12)

1. Lane RTX moi xac nhan mot dieu ro rang: khi corpus tot hon, workflow `workbook-first` sinh candidate rat manh; van de cua lane cu chu yeu la data quality + gating sai.
2. RTX v1 candidate generation bi hong nang o tang question:
   - `3170` rows
   - chi `11` unique questions
   - `100%` rows bi exact duplicate templates
3. RTX manual round 2 cu khong giai quyet duoc root cause, vi rewrite polish van de fallback generic templates.
4. RTX v2 fact-specific sua duoc duplicate (`0` exact dup), nhung van con loi tang `fact_target quality`:
   - `fact_mismatch`
   - `unnatural_question_wording`
   - `residue_led_question`
   - `overlong_fact_phrase`
5. RTX v2.1 la moc dung hien tai:
   - `42` usable rows
   - `42` unique questions
   - `0` exact duplicate
   - post-audit errors = `0`
6. Sample `v2.1` cho thay question layer da du de mo lai `review round 1`, du van con mot so disclosure semi-structured tu `questionnaire` va `data_table`.
7. Trang thai dung hien tai:
   - khong benchmark
   - khong canonical
   - khong gold decision
   - chi chuan bi mo lai `RTX review round 1` tren workbook `v2.1`

## Enterprise internal-doc framework contract (2026-06-18)

1. Lane `enterprise internal-doc` da chuyen tu generalization-hardening sang **framework co contract ro**:
   - `src/enterprise_docs/registries.py` + 3 JSON registry
   - `src/enterprise_docs/holdout_harness.py` — harness chuan hoa demo_company (dev) / hanssem / musinsa
   - `src/enterprise_docs/langgraph_handoff.py` — schema v1.0.0 + synthesis gate
2. Artifact: `reports/enterprise_docs_framework_20260618-152811/`
3. Holdout matrix:
   - `hanssem`: retrieval **0.875**, extraction **0.375**, aggregation **0.375**
   - `musinsa`: retrieval **1.0**, extraction **0.4**, aggregation **0.4** (5 probes)
4. Demo readiness giu nguyen: quant synthesis-gate **0.23**; `reusable_system_coverage` **0.48**
5. Pilot-only con lai co ly do ghi trong registry:
   - `doc_evidence_csv`, `financial_en_bridge`, `governance_financial_anchor`, `narrative_investment`
   - code fallback `ROW_ALIASES`/`SEMANTIC_BRIDGE` trong `structured_extractor.py` (merge registry khi co `company_id`)
6. Quyet dinh he thong:
   - Giu `demo_company` lam dev set chinh
   - Mo rong holdout 한샘/무신사: **co** (retrieval du tot)
   - LangGraph handoff integration: **chua** (quant gate 0.23 < 0.4)
   - Mo synthesis: **chua** (nguong 0.6)

## Abstraction + holdout robustness round (2026-06-18)

1. Registry migration audit: **8** already registry-driven, **5** partial, **1** still code-driven (`parsers/ingest`)
2. Refactor: `doc_router.route_documents(company_id)` tu registry; `retrieval_boost` tu `source_role_registry`
3. Holdout mo rong: hanssem **12** probes, musinsa **8** probes
4. Artifact: `reports/enterprise_docs_abstraction_holdout_20260618-155302/`
5. Holdout metrics:
   - hanssem: retrieval **0.917**, extraction **0.333**
   - musinsa: retrieval **1.0**, extraction **0.375**
6. Family view:
   - strongest: `employee_headcount` (reusable_holdout)
   - weakest: `governance` (retrieval_only, extraction 0.17)
   - `environment_ghg`: reusable_holdout (retrieval 1.0, extraction 0.67)
7. System gates:
   - `ready_for_holdout_expansion`: **true**
   - `ready_for_limited_langgraph_handoff`: **false**
   - `not_ready_for_synthesis`: **true**
   - `requires_more_registry_abstraction`: **true** (3 partial còn lại)

## Registry abstraction + holdout extraction round (2026-06-18)

1. Hotspot giảm: partial **5→3**, code-driven **1→0**, already registry-driven **8→9**
2. `structured_extractor`, `doc_mapping`, `ingest` → registry-first
3. Family mới: `governance_narrative`, `demo_company_table_aliases` trong metric_family_registry
4. Artifact: `reports/enterprise_docs_registry_holdout_20260618-160935/`
5. Holdout delta vs prior:
   - hanssem extraction **0.333** (+0.083 vs 0.25)
   - extraction avg **0.354** (+0.042)
   - retrieval giữ **0.917 / 1.0**
6. Governance extraction **0.167 → 0.333** — vẫn weakest nhưng tăng gấp đôi; HOLDOUT-003/004 cải thiện nhờ `governance_narrative`
7. Chưa handoff trial; synthesis blocked

## Family holdout + partial hotspot completion (2026-06-18)

1. **3 partial hotspot → 0**: `doc_router`, `evidence_aggregator`, `cross_doc_retriever` đều `already_registry_driven`
2. `company_doc_registry` v1.2.0: `role_labels`, `routing_defaults` per company
3. `source_role_registry` v1.1.0: `routing` profiles + `retrieval_policy`
4. Holdout mở rộng: hanssem 14 probes (+2), musinsa 10 probes (+2)
5. Artifact: `reports/enterprise_docs_family_holdout_20260618-163238/`
6. Metrics vs registry round:
   - extraction avg **0.414** (+0.060)
   - governance **0.5** — không còn weakest; tier `reusable_holdout`
   - employee_headcount **1.0** (2 probes)
   - environment_ghg **0.4** — weakest sau probe mix
7. `requires_more_registry_abstraction=false`; synthesis/handoff vẫn blocked

## Family-focused holdout strengthening (2026-06-18)

1. `metric_family_registry` v1.3.0: patterns `environment_ghg` (net-zero reverse, env grade, impact report year)
2. `family_readiness_gate.py`: `handoff_candidate_likelihood` heuristic (quant-only)
3. Artifact: `reports/enterprise_docs_family_strengthening_20260618-164132/`
4. Family metrics vs prior family-holdout round:
   - extraction avg **0.600** (+0.186)
   - `environment_ghg` **0.667** (quant extraction **1.0**, +0.267)
   - `governance` **0.667** (+0.167)
   - `employee_headcount` **1.0** (stable)
5. `handoff_prep_candidate_families`: employee_headcount, environment_ghg, governance — chưa `single_source_sufficient`
6. `ready_for_limited_langgraph_handoff=false`; synthesis blocked

## Bao cao cong viec ngay 2026-06-12

1. Khi tong hop cong viec trong ngay, ba dau viec chinh lien ket voi nhau la:
   - phoi hop voi team `LangGraph` de phuc vu luong bao cao cong ty `Rayxion`
   - sua API va bo sung co/canh bao `do tin cay thap`
   - dua quy trinh `Silver -> Golden Set` sang tap du lieu moi de test lai he thong
2. Cach trinh bay phu hop cho stakeholder la:
   - nhan manh luong du lieu va luong kiem soat chat luong
   - khong di qua sau vao chi tiet noi bo cua cac vong rebuild
   - nhan manh su chuyen doi tu "cuu du lieu cu" sang "test he thong tren du lieu tot hon"
