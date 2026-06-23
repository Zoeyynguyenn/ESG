# Golden eval thật — RAG vs Gold (goldns + emni, 530 câu)

Ngày: 2026-06-22
Nguồn: `goldns_emni_rag_vs_gold_comparison.xlsx`

## Phạm vi

Đánh giá trên **golden set thật** 530 câu hỏi ESG của 2 công ty (goldns 251 + emni 279),
so RAG predicted vs gold answer. Đây là kết quả **toàn bộ pipeline RAG** (hệ thống sẵn có),
dùng làm bằng chứng thật cho trục answer/abstain mà workstream answerability đang củng cố.

## Kết quả

| Chỉ số | Kết quả |
|---|---|
| Tổng câu hỏi | 530 |
| Gold: abstain_gold / answerable_gold | 463 / 67 |
| Quyết định answer-vs-abstain đúng | 530/530 (100%) |
| answer_correct | 530/530 (100%) |
| Sạch hoàn toàn (green: ABSTAIN_OK + MATCH) | 524/530 (98.9%) |
| abstain-safety thật (không trả lời bừa câu nên abstain) | 100% |

Confusion (gold × predicted abstain):

- abstain_gold (463) → predicted abstain = True: 463 (đúng toàn bộ)
- answerable_gold (67) → predicted abstain = False: 67 (trả lời toàn bộ, answer đúng)

Theo công ty:

- goldns: 251 câu, green 248, answer_correct 251.
- emni: 279 câu, green 276, answer_correct 279.

## 6 câu cần review nhẹ (không phải sai đáp án)

- 4 × `SEMANTIC_AMBIGUITY` (유보된 경제가치): đáp án đúng nhưng cần SME xác nhận nghĩa (label workbook vs account OFS/CFS).
- 2 × `COVERAGE_GAP` (공정거래 소송/위반 건수, goldns): đáp án đúng nhưng top1 doc sai do thiếu nguồn FTC raw HTML.

## Diễn giải

- Trên dữ liệu doanh nghiệp thật, hệ thống quyết định trả lời-hay-abstain đúng 100% và
  không trả lời bừa câu nào → đúng tinh thần answerability/abstain-safety.
- Set lệch mạnh về abstain (87% abstain_gold) vì phần lớn metric công ty không công bố;
  tuy vậy toàn bộ 67 câu có đáp án đều trả lời đúng.
- 6 câu non-green không phải lỗi đáp án: 4 cần SME, 2 do nguồn FTC bị chặn (coverage).

## Bước tiếp theo

- Mở nguồn FTC raw để đóng 2 `COVERAGE_GAP`.
- SME review 4 `SEMANTIC_AMBIGUITY` (유보된 경제가치).
- Bổ sung thêm công ty thật để mở rộng golden set.
