# Bao cao cong viec ngay 2026-06-12

## 1. Phoi hop voi team LangGraph de tao bo bao cao cho cong ty Rayxion

Cong viec nay khong chi la "lam bao cao cong ty", ma la mot luong ket hop giua `team Dataset` va `team RAG` de tao ra bo file bao cao co cau truc on dinh.

### Cach phoi hop giua 2 team

- `Team Dataset` tim va tap hop nguon tai lieu goc cua cong ty.
- Cac nguon nay duoc ban giao lai cho `team RAG`.
- `Team RAG` dung bo nguon do de chunk, retrieve, rut evidence, roi tao thanh bo file bao cao co dinh dang ro rang.

### Dinh dang dau ra muc tieu

Bo bao cao muc tieu duoc dinh huong theo kieu package nhu:

- `C:\Users\nguye\Downloads\data-company\demo_company\rtx_7step_dataset\rtx_7step_dataset`

Trong package mau nay, dau ra duoc tach thanh cac file rieng theo tung nhom noi dung:

1. `01_사업보고서_발췌.md`
   - thong tin doanh nghiep, business segment, nhan su, doanh thu, quy mo hoat dong
2. `02_온실가스_에너지_명세.md`
   - Scope 1, Scope 2, nang luong, nuoc, chat thai, vi pham moi truong
3. `03_재생에너지_계약.md`
   - hop dong va hinh thuc su dung nang luong tai tao
4. `04_인사_안전_통계.md`
   - nhan su, an toan lao dong, EEO-1, thong ke workforce
5. `05_사회공헌_인권.md`
   - nhan quyen, dong gop xa hoi, hoat dong cong dong
6. `06_지배구조_운영.md`
   - hoi dong quan tri, compliance, ethics, governance process
7. `07_인증_현황.md`
   - chung chi, tieu chuan, he thong xac nhan

Ngoai 7 file Markdown, package mau con co:

- `RTX_quantitative_questions.xlsx`

File Excel nay cho thay dau ra khong chi dung de doc bao cao, ma con dung de doi chieu cac cau hoi dinh luong va phuc vu retrieval/extraction ve sau.

## 2. Sua API cho team LangGraph, bo sung co danh dau khi do tin cay thap

Trong ngay, mot dau viec rieng duoc lam voi `team LangGraph` la sua cach API tra ket qua de downstream khong hieu nham rang moi retrieval result deu "co the dung ngay".

### Van de can sua

Neu API chi tra `items` ma khong co co canh bao, ben `LangGraph` rat de:

- lay nham evidence yeu
- tiep tuc sinh cau tra loi du retrieval chua du chac chan
- tao bao cao co ve hop ly nhung nen bang chung khong vung

### Huong sua API

API duoc dieu chinh theo huong them cac tin hieu danh dau:

- `retrieval_confidence`
- `abstain_recommended`
- `no_relevant_evidence`
- `answerable_candidate`

Muc tieu cua cac co nay la giup phia `LangGraph` biet ro:

- truong hop nao co evidence on
- truong hop nao evidence con yeu
- truong hop nao nen dung lai o muc "chua du co so"

### Tai lieu handoff

Trong ngay da tao tai lieu handoff rieng:

- `docs/LANGGRAPH_SWAGGER_RETRIEVE_HANDBOOK_20260612.md`

Tai lieu nay mo ta:

- cach team LangGraph goi `/retrieve`
- cach doc dung cac co reliability
- khi nao nen bat `generation_guard`
- khi nao khong nen cho phep generation viet tiep nhu mot cau tra loi chac chan

### Y nghia cua dau viec API

Dau viec nay giup luong bao cao cong ty an toan hon.

Thay vi:

- retrieve duoc gi thi dung cai do

luong moi la:

- retrieve
- xem do tin cay
- neu can thi canh bao hoac abstain
- roi moi cho generation viet thanh bao cao

Dieu nay rat quan trong voi cac bo bao cao cong ty kieu `Rayxion`, vi dau ra la cac file tong hop theo tung nhom ESG, khong phai chi mot cau tra loi chat don le.

## 3. Tien hanh tao quy trinh Silver -> Golden Set cho du lieu moi

Dau viec thu ba trong ngay la chuyen quy trinh `Silver -> Golden Set` sang mot bo du lieu moi va tot hon, de test lai he thong tao Golden Set.

### Muc tieu cua workstream nay

Muc tieu khong phai tiep tuc "cuu" bo du lieu cu, ma la kiem tra xem he thong co thuc su hoat dong dung khi duoc cap du lieu tot hon hay khong.

### Dau vao moi da duoc tao

Da tao lane rieng:

- `data/rag_dataset/06_rtx_references_raw`

Thanh phan dau vao hien co:

- `4` file PDF trong `_sources`
- `5` file raw HTML that trong `web_sources`
- `1` file DOJ fallback snapshot `.md`

Tong cong:

- `10` file nguon cho lane RTX moi

### Ket qua xu ly buoc dau

Da chunk lane nay thanh:

- `2762` chunks
- `2761` corpus units

Sau khi normalize:

- `2761` source units
- `2724` normalized units

### Qua trinh workbook-first da chay

Vong candidate generation dau tien cho lane RTX:

- `4116` raw candidates
- `3170` filtered candidates

Sau do phat hien loi lon:

- `3170` row nhung chi co `11` question templates thuc chat
- `100%` row bi exact duplicate question backbone

Vi vay da reset huong va rebuild lai question layer:

1. audit duplicate question
2. rebuild `v2 fact-specific`
3. audit `fact-target quality`
4. rebuild `v2.1 fact-quality`

### Trang thai hien tai cua lane moi

Moc dung hien tai cua workstream:

- `42` usable candidates
- `42` unique questions
- `0` exact duplicate

Artifact chinh hien tai:

- `data/golden_set/v2/reference_style/reference_seed_workbook_rtx_v2_1_fact_quality.xlsx`

Y nghia cua moc nay:

- he thong da di qua duoc bai test quan trong nhat: khong con sinh hang loat cau hoi chung chung
- lane moi da du tot de mo lai vong `review round 1`
- chua benchmark
- chua canonical
- chua gold decision

## 4. Ket luan chung trong ngay

Ba dau viec hom nay thuc chat noi voi nhau thanh mot chuoi:

1. `team Dataset` tim va ban giao nguon tai lieu cho cong ty `Rayxion`
2. `team RAG` dung bo nguon do de tao bo file bao cao co cau truc kieu `7-step dataset`
3. `team LangGraph` nhan ket qua retrieval/API da co co danh dau do tin cay de tao bao cao an toan hon
4. song song, workstream `Silver -> Golden Set` duoc dua sang bo du lieu moi de test lai he thong tao bo cau hoi/chuan danh gia

Diem can nhan manh trong bao cao ngay:

- cong viec `Rayxion` la luong `dataset -> report package`, khong phai mot request tong hop chung chung
- phan `LangGraph API` la de downstream biet luc nao can canh bao va luc nao khong duoc viet tiep nhu mot ket luan chac chan
- phan `Golden Set` da duoc dua sang bo du lieu moi, va he thong da bat dau cho thay giatri tren du lieu tot hon
