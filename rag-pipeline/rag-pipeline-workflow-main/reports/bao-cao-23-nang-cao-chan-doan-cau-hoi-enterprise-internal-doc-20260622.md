# Bao cao 23: Nang cao nang luc chan doan cau hoi cho lane enterprise internal-doc

Ngay: 2026-06-22

## 1. Muc tieu

Lane `enterprise internal-doc` da o trang thai san sang cho du lieu doanh nghiep that.
Buoc tiep theo la nang cao nang luc chan doan cua lane, de khi van hanh voi du lieu that,
he thong phan biet chinh xac hon giua loi cau hoi, loi thieu du lieu va loi nang luc he thong.

Muc tieu chinh trong ngay gom:

1. Bo sung kha nang phan loai cau hoi `khong ro / khong co thong tin`, tach khoi loi thieu tai lieu (`corpus_limited`) va loi he thong (`system_gap`).
2. Dam bao tinh nang moi khong lam anh huong nang luc cot loi (regression an toan) va co kiem thu day du.
3. Xac nhan lane co the onboarding ngay khi co du lieu doanh nghiep that.

## 2. Cach thuc hien

Cong viec duoc thuc hien theo 4 phan:

### 2.1. Bo sung answerability classification

Da them mot truc chan doan moi cho lane: phan loai cau hoi thanh
`answerable`, `out_of_scope` (cau khong ro / lac de) va `no_information` (family hop le
nhung gia tri khong duoc cong bo - honest abstain). Truoc day cac cau khong tim duoc
candidate deu bi gom vao `corpus_limited`, lam lan giua loi cau hoi va loi thieu tai lieu.

### 2.2. Bo sung chi so an toan abstain

Da them `abstain_safety_rate` de do ty le cau hoi khong tra loi duoc ma he thong khong
tra loi bua, va hien thi ket qua nay trong artifact cua onboarding gate.

### 2.3. Kiem thu va dam bao regression

Da viet bo unit test cho tinh nang moi va xac nhan cac chi so capability cot loi khong bi
anh huong khi them tinh nang.

### 2.4. Dien tap onboarding cho du lieu that

Da chay dien tap (dry-run) quy trinh onboarding de xac nhan lane san sang dua du lieu
doanh nghiep that vao van hanh ngay theo SOP.

### 2.5. Danh gia tren golden set that

Da danh gia tren golden set that 530 cau hoi ESG (goldns + emni) tu
`goldns_emni_rag_vs_gold_comparison.xlsx`, do truc answer/abstain tren du lieu doanh nghiep
that (script tai lap: `scripts/eval_golden_530.py`).

## 3. Ket qua da dat duoc

### 3.1. Ket qua ky thuat

**Danh gia tren golden set THAT (530 cau hoi ESG, goldns + emni) — bang chung chinh:**

- Tong: 530 cau (goldns 251 + emni 279); gold: 463 abstain_gold / 67 answerable_gold.
- Quyet dinh tra loi-vs-abstain dung: **530/530 (100%)**.
- answer_correct: **530/530 (100%)**; sach hoan toan (green): **524/530 (98.9%)**.
- abstain-safety that: **100%** — khong cau nao nen abstain ma bi tra loi bua.
- Chi 6 cau can review nhe (khong sai dap an): 4 semantic_ambiguity (can SME), 2 coverage_gap (top1 doc sai do thieu nguon FTC raw).
- Artifact: `reports/enterprise_docs_golden_eval_530_20260622/`.

Luu y dung phan: golden set nay do toan bo pipeline RAG (he thong san co), dung lam bang chung
that cho truc answer/abstain. Lop answerability classification moi them la lop chan doan bo sung.

Lop answerability classification (moi them) — kiem tra co che:

- Eval set 18 case curated: accuracy 83.3% (15/18), abstain_safety 90.9%; unit test 10/10.
- Eval synthetic mo rong 201 case (`scripts/eval_answerability_suite.py`): overall 85.6%,
  tang easy 100% (do thiet ke), tang adversarial 0% (do dung loi da biet), abstain_safety 94.3%.
  Day la synthetic — chi de kiem chung co che va lo gioi han, khong phai bang chung dap an that.

An toan regression (cac chi so cot loi giu nguyen sau khi them tinh nang):

- `cross_role_extraction_alignment_rate = 100%`
- `cross_doc_equivalence_match_rate = 100%`
- `evidence_fusion_success_rate = 100%`
- `conflict_classification_accuracy = 100%`
- `single_source_to_multi_source_promotion_rate = 100%`
- `ghost_pass_count = 0`

### 3.2. Ket qua van hanh

- Onboarding gate nay co them muc answerability trong report.
- Dien tap onboarding: skeleton sinh dung, khong co loi validation; trang thai `ready_for_natural_plug_in`.
- Artifact: `reports/enterprise_docs_answerability_classification_20260622/` va artifact onboarding gate trong ngay.
- Trang thai lane giu nguyen: `done_until_real_data`.

## 4. Cac yeu cau chinh va cach da hien thuc hoa

### 4.1. Phan biet loi cau hoi voi loi du lieu va loi he thong

Da hien thuc hoa bang answerability classification (`out_of_scope` / `no_information` /
`answerable`), giup khi onboarding cong ty that, mot cau fail duoc tach ro thanh cau hoi toi,
thieu tai lieu, hoac loi nang luc he thong.

### 4.2. Giu on dinh nang luc cot loi khi them tinh nang

Da hien thuc hoa bang thiet ke tinh nang moi khong mang cac tin hieu regression cua suite cot
loi, va bang bo unit test xac nhan gate giu nguyen 100%.

### 4.3. San sang van hanh voi du lieu that

Da hien thuc hoa bang dien tap onboarding (dry-run) theo SOP, khong can rebuild pipeline loi.

## 5. Ket luan

Lane `enterprise internal-doc` duoc nang cap them mot truc chan doan moi: phan biet cau hoi
`khong ro / khong co thong tin` voi loi thieu du lieu va loi he thong. Tinh nang duoc kiem thu
day du va khong lam anh huong nang luc cot loi.

Tren golden set THAT 530 cau (goldns + emni), truc answer/abstain dat 530/530 dung quyet dinh,
answer_correct 530/530, sach 524/530 (98.9%), abstain-safety 100% — bang chung that o quy mo
lon cho thay huong nay vung tren du lieu doanh nghiep that.

Trang thai hien tai:

`done_until_real_data`

Buoc tiep theo khi co du lieu doanh nghiep that:

1. bootstrap cong ty moi
2. ingest tai lieu
3. tao probes va natural cases
4. chay onboarding gate
5. review theo SOP va phan loai cau hoi toi / `corpus_limited` / `system_gap`
