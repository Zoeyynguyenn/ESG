# Enterprise Internal-Doc — Family Holdout + Partial Hotspot Completion

Generated: 20260618-163238

## Registry migration

- Already registry-driven: **12**
- Partially registry-driven: **0**
- Still code-driven: **0**
- Pilot-only labeled: **2**

Partial hotspots reduced: **3 → 0**

## Holdout vs prior round

- Extraction avg: **0.4143** (delta 0.0602)
- Hanssem retrieval: **0.9286** (delta 0.0119)
- Governance extraction: **0.5** (still weakest: False)
- Environment GHG extraction: **0.4** (delta -0.1)

## Family summary

- **employee**: retrieval=1.0, extraction=0.3333, tier=retrieval_only
- **employee_headcount**: retrieval=1.0, extraction=1.0, tier=reusable_holdout
- **environment_ghg**: retrieval=0.8, extraction=0.4, tier=retrieval_only
- **financial**: retrieval=1.0, extraction=1.0, tier=pilot_only
- **governance**: retrieval=0.875, extraction=0.5, tier=reusable_holdout
- **other**: retrieval=1.0, extraction=0.0, tier=retrieval_only

## System gates

- `ready_for_holdout_expansion`: **True**
- `ready_for_limited_langgraph_handoff`: **False**
- `not_ready_for_synthesis`: **True**
- Handoff candidates: none
- Synthesis gap (holdout extraction): **0.0857**
- Priority next: **holdout_extraction_by_family**

All core modules registry-driven (12); holdout extraction avg 0.4143; governance 0.5; synthesis blocked.
