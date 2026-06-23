# Enterprise Internal-Doc — Framework Contract

Generated: 20260618-152811

## 1. Abstraction layer

Ba registry da tach:
- `company_doc_registry` — logical documents theo cong ty
- `metric_family_registry` — row aliases, semantic bridge, governance anchor, narrative probe
- `source_role_registry` — role classification + synthesis gate

- So cong ty trong registry: **3**
- Logical doc generic: **4** | pilot-only: **1**
- Rule inventory: **27** (reusable generic **13**, pilot-only **7**)

### Pilot-only con lai (ly do)

- `DEMO_DOCUMENTS` / `doc_evidence_csv` — CSV boost chi cho demo_company
- `ROW_ALIASES` / `SEMANTIC_BRIDGE` trong code — fallback; registry merge khi co company_id
- `financial_en_bridge`, `governance_financial_anchor`, `narrative_investment` — scope pilot_only trong metric_family_registry

## 2. Holdout harness

Harness chuan hoa: `src/enterprise_docs/holdout_harness.py`

| company_id | role | probes | retrieval | extraction | aggregation |
|---|---|---:|---:|---:|---:|
| `hanssem` | holdout | 8 | 0.875 | 0.375 | 0.375 |
| `musinsa` | holdout_probe | 5 | 1.0 | 0.4 | 0.4 |

## 3. LangGraph handoff contract

- Schema version: **1.0.0**
- Handoff allowed states: `aggregation_ready`, `multi_source_sufficient`, `single_source_sufficient`
- Demo handoff samples: **35**
- Demo handoff_allowed rate (quant): **0.2333**

## 4. Reusability

- `reusable_system_coverage`: **0.4815**

## 5. Quyet dinh he thong

- Giu `demo_company` lam dev set chinh: **True**
- Mo rong holdout 한샘 / 무신사: **True**
- Bat dau LangGraph handoff integration: **False**
- Mo synthesis: **False** (nguong quant gate >= 0.6, hien tai 0.2333)
- Layer yeu nhat: **demo_aggregation_sufficiency**
- Buoc tiep theo: **holdout_harness_expansion**

Lane da co abstraction registry + holdout harness + LangGraph handoff schema; reusable coverage 0.4815; quant synthesis-gate 0.2333; chua mo synthesis.
