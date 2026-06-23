# Tom tat gui sep: enterprise internal-doc

- Lane `enterprise internal-doc` da hoan tat phan chuan bi cho bai toan xu ly tai lieu doanh nghiep thanh du lieu ESG co cau truc.
- He thong da bo sung day du parser cho cac dinh dang chinh, schema ESG co cau truc, retrieval theo logical document / family, va co che xu ly cross-document.
- Cac capability cot loi da duoc harden xong va khoa lai bang regression gate, voi cac chi so constructed suite dang o muc 100% va `ghost_pass_count = 0`.
- He thong da phan biet ro `corpus_limited` va `system_gap`, giup khi co du lieu that co the biet ngay can bo sung tai lieu hay can mo hardening theo family.
- Lane da co onboarding gate, SOP van hanh, bootstrap kit, templates va script khoi tao cong ty moi.
- Trang thai hien tai cua lane la `done_until_real_data`, nghia la khong can rebuild pipeline loi truoc khi co du lieu doanh nghiep that.
- Khi du lieu that duoc cap, quy trinh se la: bootstrap cong ty moi -> ingest tai lieu -> tao probes va natural cases -> chay onboarding gate -> review theo SOP.
- O giai doan hien tai, team khong mo rong theo huong LangGraph, synthesis, hoac toi uu diem tren bo demo, ma giu lane o trang thai san sang van hanh.
