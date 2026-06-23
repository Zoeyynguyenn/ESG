# Golden Set — Core Canonical Round 3

Generated: 2026-06-12T14:05:21

## Mục tiêu

Canonicalize core workbook **한샘 + 무신사** từ manual review round 2:
giữ fact target, merge duplicate cluster, chuẩn hóa Q/disclosure.

## Vì sao chỉ canonical core 한샘 + 무신사

- Core đủ mạnh: HS 49 + MS 11 canonical candidates sau manual review.
- **레이시온** chỉ 1 survivor — source/data quality gap, tách backlog.
- Không kéo RX vào core flow; không mở Lane C.

## Input canonical candidates

**60** row (`canonical_candidate_flag=true`, HS+MS).

## Rule merge / dedupe / keep / weak drop

| Decision | Điều kiện |
|----------|-----------|
| `canonical_keep` | Anchor sạch, confirm, không merge |
| `canonical_keep_after_merge` | Anchor sau merge cluster hoặc normalize từ revise |
| `canonical_drop_duplicate` | Trùng fact cluster/intent, giữ anchor mạnh hơn |
| `canonical_drop_weak` | Meta-heavy, truncated, TCFD definition-only, unknown generic |

## Kết quả

- Input: **60**
- canonical_keep: **30**
- keep_after_merge: **15**
- drop_duplicate: **8**
- drop_weak: **7**
- **Core canonical total:** **45**

### Breakdown theo công ty

- **무신사**: 9
- **한샘**: 36

### Breakdown theo question_type

- `quantitative`: 30
- `trend`: 5
- `qualitative`: 10

### Breakdown theo fact cluster

- `FC_ESG_GOVERNANCE`: 15
- `FC_UNKNOWN`: 15
- `FC_MATERIAL_8`: 5
- `FC_HUMAN_RIGHTS`: 5
- `FC_TCFD`: 2
- `FC_KGCS_A`: 3

## Ví dụ

### Duplicate được merge đúng
- `MS-V4-T03`: Anchor MS-V4-T03; merged 1 dup(s): MS-V4-L03
- `MS-V4-T04`: Single row after manual revise — normalized wording
- `MS-V4-T05`: Single row after manual revise — normalized wording

### Row generic thay bằng specific (drop dup)
- `MS-V4-L03` → Defer to anchor MS-V4-T03
- `HS-V4-L01` → Defer to anchor HS-V4-T03
- `HS-V4-Q12` → Defer to anchor HS-V4-T03

### Row weak bị drop
- `MS-V4-Q03`: `unknown_target_generic`
- `HS-V4-Q15`: `unknown_target_generic`
- `HS-V4-Q36`: `truncated_disclosure`

## Kết luận

- Core canonical set: **45** row
- Gold decision round cho core? **Có — core đủ chặt để mở gold decision round (không promote trong task này)**
- RX backlog: **40** row (source-acquisition dependent)
