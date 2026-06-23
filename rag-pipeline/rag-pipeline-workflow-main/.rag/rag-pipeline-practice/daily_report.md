# Daily Report

Ngay: 2026-06-22 (Enterprise internal-doc — readiness re-verify + onboarding dry-run)

## 1. Huong di

- Doi chieu code voi Bao cao 22 (lane enterprise internal-doc = `done_until_real_data`)
- Khong rebuild loi, khong LangGraph/synthesis/demo-score (dung dung ket luan Bao cao 22)
- Chua co du lieu doanh nghiep that -> viec hom nay la **xac minh san sang** + **dien tap SOP**

## 2. Cong viec da lam

- Audit repo: tat ca file Bao cao 22 tham chieu deu co (runbook, bootstrap, gate runner, `esg_field_normalizer`, `structured_esg_mapper`, capability gate runner)
- Sync workspace repo voi ban zip moi nhat (ban cu dung o 06-18, thieu script thoi Bao cao 22)
- Chay lai regression gate hom nay: `scripts/run_enterprise_docs_natural_onboarding_gate.py`
  - Artifact: `reports/enterprise_docs_natural_onboarding_gate_20260622-024256/`
- Dien tap onboarding (dry-run): `scripts/bootstrap_enterprise_company.py --company-id rehearsal_demo_0622 --dry-run`

## 3. Ket qua xac minh (06-22)

| Metric (constructed regression) | Gia tri |
|---|---:|
| cross_role_extraction_alignment_rate | 1.0 |
| cross_doc_equivalence_match_rate | 1.0 |
| evidence_fusion_success_rate | 1.0 |
| conflict_classification_accuracy | 1.0 |
| single_source_to_multi_source_promotion_rate | 1.0 |
| ghost_pass_count | 0 |

- `regression_gate_passed = true`, `overall_status = ready_for_natural_plug_in`
- Bootstrap dry-run: `validation_errors = []`, sinh dung skeleton (probes path + 4 manual steps)
- Ket luan: code khop 100% voi Bao cao 22; khong co code drift can sua

## 4. Cai tien hom nay (answerability classification)

- Van de: bo phan loai natural-case cu gop moi cau "khong co candidate" vao `corpus_limited`,
  ke ca cau hoi khong ro / lac de -> reviewer di thu thap tai lieu nham.
- Them truc thu ba (dung tinh than Bao cao 22 ve corpus_limited vs system_gap):
  - `out_of_scope` (cau hoi khong map vao metric family) — cau khong ro/lac de
  - `no_information` (family hop le nhung gia tri khong duoc cong bo) — honest abstain
  - `answerable`
- Code: them `answerability_probe` + capability `answerability_classification` trong
  `crossdoc_case_builder.py` va `crossdoc_capability_benchmark.py`; them `abstain_safety_rate`.
- Ket qua (eval set 18 case gom ca case kho): answerability_accuracy = 83.3% (15/18), abstain_safety = 90.9% (10/11), unit test 10/10; **regression gate giu nguyen 100%**.
- 3 case adversarial co tinh de lo gioi han heuristic (phu thuoc tu khoa / so token bo qua gia tri / so khop chuoi item) -> huong cai thien khi co data that.
- Artifact: `reports/enterprise_docs_answerability_classification_20260622/`

## 5. Buoc tiep theo

- Khi co du lieu cong ty that: chay 7-step SOP trong runbook (ingest -> map logical docs -> probes -> natural cases -> gate -> classify -> decide)
- Phan loai fail thanh 3 loai: cau hoi toi (sua cau) / `corpus_limited` (thu tai lieu) / `system_gap` (mo hardening)
- Giu constructed regression gate lam CI; chi mo rong registry/equivalence khi xuat hien `system_gap`
- Khong tune pipeline truoc khi co corpus that
