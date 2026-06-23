# Golden Set — Reference Workbook Canonical R2

Generated: 2026-06-11T10:29:55

## Mục tiêu

Canonical hóa curated R1 theo **fact target**: giữ đúng fact mà seed đại diện, loại semantic drift, dedupe cluster — tạo workbook chặt hơn trước review nội dung.

## Vấn đề còn lại của R1

1. Curated set **Hansem-only** (14/14) — không còn 무신사/레이시온.
2. 11 row `keep_but_needs_rewrite` trùng fact cluster (Net Zero, board 14/44, KGCS, material 8).
3. R1 rewrite **semantic drift**: ví dụ HS-G-Q01 hỏi 2050 goal nhưng rewrite sang governance.
4. **Answer target mismatch**: HS-G-T03 disclosure rewrite rơi vào TCFD/BIS thay vì Net Zero.
5. `keep_strong` Q06/L06 trùng KGCS — cần dedupe.

## Quy tắc canonicalization R2

| Decision | Điều kiện |
|----------|-----------|
| `canonical_keep` | Fact target rõ, passage sạch, không drift |
| `canonical_keep_after_rewrite` | Fact salvageable, rewrite giữ nguyên target |
| `drop_semantic_drift` | Rewrite R1 đổi fact target |
| `drop_answer_target_mismatch` | Disclosure không trả lời fact câu hỏi |
| `drop_duplicate_fact_cluster` | Trùng cluster+intent, giữ 1 bản tốt nhất |
| `drop_truncated_unsalvageable` | Fact line cắt cụt |
| `drop_still_too_noisy` | Không có company fact cho target |

## Tổng số row đầu vào

**14** row từ `reference_seed_candidates_curated_r1.jsonl`.

## Kết quả canonical

| Chỉ số | Giá trị |
|--------|--------:|
| canonical_keep | 0 |
| canonical_keep_after_rewrite | 4 |
| canonical usable total | 4 |
| independent fact clusters | 4 |

### Drop theo nhóm

- `drop_duplicate_fact_cluster`: **6**
- `drop_still_too_noisy`: **3**
- `drop_truncated_unsalvageable`: **1**

## Fact cluster collapse

- **FC_ESG_GOVERNANCE**: input 3 → canonical 1
- **FC_KGCS_A**: input 2 → canonical 1
- **FC_MATERIAL_8**: input 3 → canonical 1
- **FC_NET_ZERO_2050**: input 3 → canonical 1
- **FC_TCFD**: input 3 → canonical 0

## Ví dụ cụ thể

### `drop_duplicate_fact_cluster`
- **HS-G-L01**: Trùng fact cluster/intent với HS-G-Q01; giữ bản sạch hơn.
- **HS-G-Q02**: Trùng fact cluster/intent với HS-G-T01; giữ bản sạch hơn.

### `canonical_keep_after_rewrite`
- **HS-G-T04**: Fact target giữ nguyên; disclosure thu gọn theo fact line.
- **HS-G-Q01**: Fact target giữ nguyên; disclosure thu gọn theo fact line. (R1 drift đã sửa: rewrite_target_FC_ESG_G

## Đánh giá cuối

- **Seed canonical usable:** 4
- **Fact cluster độc lập:** 4
- **Coverage:** **Hansem-only canonical workbook** — chưa có multi-company coverage.
- **Đủ review nội dung?** Chưa — Hansem-only skeleton (4 cluster); đủ pilot format, chưa đủ review nội dung 3 công ty

## Kết luận (3 câu)

1. **Sau R2 còn bao nhiêu seed canonical usable?** **4** seed.
2. **Có bao nhiêu fact cluster độc lập?** **4** cluster.
3. **Bước tiếp theo?** **Chưa** đủ cho review nội dung đầy đủ 3 công ty. Ưu tiên: (a) review nội dung round 3 trên Hansem canonical nếu cần validate format; (b) **rebuild seed workbook v2** cho 무신사/레이시온 từ corpus sạch.
