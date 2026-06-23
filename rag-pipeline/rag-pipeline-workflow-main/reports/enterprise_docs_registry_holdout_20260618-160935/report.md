# Enterprise Internal-Doc — Registry + Holdout Extraction Round

Generated: 20260618-160935

## Registry migration

- Already registry-driven: **9** (was 8)
- Partially registry-driven: **3** (was 5)
- Still code-driven: **0** (was 1)

## Holdout vs prior round

- Extraction avg: **0.3541** (delta 0.0416)
- Hanssem retrieval: **0.9167** (delta 0.0)
- Governance extraction: **0.3333**
- Governance still weakest: **True**

## Family summary

- **employee**: retrieval=1.0, extraction=0.3333, tier=retrieval_only
- **employee_headcount**: retrieval=1.0, extraction=1.0, tier=reusable_holdout
- **environment_ghg**: retrieval=1.0, extraction=0.5, tier=reusable_holdout
- **financial**: retrieval=1.0, extraction=1.0, tier=pilot_only
- **governance**: retrieval=0.8333, extraction=0.3333, tier=retrieval_only
- **other**: retrieval=1.0, extraction=0.0, tier=retrieval_only

## System gates

- `ready_for_holdout_expansion`: **True**
- `ready_for_limited_langgraph_handoff`: **False**
- `not_ready_for_synthesis`: **True**
- Handoff candidates: none
- Synthesis gap (holdout extraction): **0.1459**
- Priority next: **holdout_extraction_by_family**

Registry-driven components 9; holdout extraction avg 0.3541; governance extraction 0.3333; synthesis blocked.
