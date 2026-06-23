# Bao cao 21 - Cong viec ngay 2026-06-18

## 1. Ket qua flow chinh cua team RAG

- Team tiep tuc van hanh flow chinh theo huong `Dataset -> Source -> RAG -> metrics/score -> Excel review`.
- Voi 2 cong ty `goldns` va `emni`, flow nay da chay xong end-to-end va dang o trang thai on dinh.
- Ket qua benchmark hien tai:
  - `answer_accuracy = 1.0`
  - `abstain_accuracy = 1.0`
  - `overall_score = 0.9702`
- Team da xuat file Excel doi chieu truc quan giua ket qua RAG va file gold goc:
  - `reports/goldns_emni_rag_vs_gold_comparison.xlsx`
- File review da bo sung cac sheet loc rieng cho dong khop hoan toan, dong can SME review, dong thieu coverage/source, va dong retrieval can xem lai.

## 2. Y nghia cua flow chinh hien tai

- Team da co duoc mot quy trinh on dinh de do chat luong RAG bang `metrics` va `score`.
- Team da co co che review ket qua nhanh bang Excel thay vi chi doc report ky thuat.
- Team da bat dau tich luy `rule` va `pattern` dung chung de tai su dung cho cac cong ty tiep theo.

## 3. Bo sung lane moi: enterprise internal-doc

- Ben canh flow chinh, hom nay team tiep tuc mo rong lane `enterprise internal-doc`.
- Lane nay phuc vu bai toan xu ly tai lieu doanh nghiep va tai lieu noi bo o nhieu dinh dang nhu `PDF`, `Excel`, `HTML`, `JSON`, `Word`, `PPT`, va tai lieu hon hop.
- Muc tieu cua lane nay la chuyen tai lieu thanh `evidence` co cau truc, danh gia muc do san sang cua du lieu, va sau nay handoff cho team LangGraph khi du dieu kien.

## 4. Trang thai hien tai cua lane enterprise internal-doc

- Lane moi da duoc dua tu muc pilot sang muc framework co contract ro hon.
- Cac thanh phan chinh da co:
  - registry quan ly pattern va tai lieu
  - readiness model
  - holdout harness
  - LangGraph handoff contract
- Ket qua hien tai cho thay huong di la dung, nhung lane nay chua mo synthesis/generative.
- Trong giai doan nay, team uu tien abstraction, holdout robustness, va synthesis gate, thay vi toi uu tung loi le.

## 5. Ket luan va buoc tiep theo

- Flow chinh `Dataset -> RAG -> metrics/score -> Excel review` da cho ket qua ro rang va co the dung de danh gia chat luong he thong.
- Lane `enterprise internal-doc` da duoc mo nhu mot huong bo sung can thiet de chuan bi cho bai toan xu ly tai lieu doanh nghiep thuc te.
- Trong thoi gian tiep theo, team se tiep tuc cung co kha nang tai su dung cua he thong, mo rong holdout co kiem soat, va chua mo synthesis cho lane moi khi gate chat luong chua dat.
