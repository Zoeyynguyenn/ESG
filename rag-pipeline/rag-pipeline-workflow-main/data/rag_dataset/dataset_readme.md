# ESG Core Dataset Readme

## 1. Muc tieu

Bo ESG Core Dataset duoc chot de dung xuyen suot 6 version RAG, giup so sanh cong bang ket qua retrieval/generation.

## 2. Cau truc dataset

```text
data/rag_dataset/
  01_synthetic_controlled/
  02_esg_public_core/
  03_esg_public_complex/
  sources.md
  dataset_readme.md
  esg_eval_guidelines.md
```

## 3. Mapping tai lieu ESG core

| ID | Ten tai lieu | To chuc | Nam | ESG chinh | Do kho | Dung tot cho version | Cau truc tai lieu |
|---|---|---|---|---|---|---|---|
| ESG-C01 | GRI Standards Download Hub | GRI | 2025/2026 | E,S,G | medium | V2,V3,V5 | Theo module/chu de, heading ro, thuan cho policy QA |
| ESG-C02 | IFRS Sustainability Standards Navigator (S1/S2) | IFRS/ISSB | 2025/2026 | E,S,G | hard | V2,V3,V6 | Chuan disclosure, van ban ky thuat, can retrieval chinh xac |
| ESG-C03 | TCFD Recommendations | TCFD/FSB | latest | E,G | medium | V2,V3,V5 | Co governance/strategy/risk/metrics ro rang |
| ESG-C04 | UNGC CoP Questionnaire | UN Global Compact | 2026 | E,S,G | medium | V2,V4,V5 | Dang questionnaire, de tao eval theo checklist |
| ESG-C05 | OECD Responsible Business Conduct | OECD | latest | S,G | medium | V2,V3,V6 | Guidance due diligence, human rights, governance |
| ESG-C06 | Apple Environmental Report page | Apple | latest | E,G | easy | V1,V2,V3 | Corporate report structure ro, metric E de truy van |
| ESG-C07 | Google 2025 Environmental Report | Google | 2025 | E,G | medium | V2,V3,V5 | Co metric emissions/energy/water, phu hop eval dinh luong |
| ESG-C08 | Vinamilk Sustainability Reports page | Vinamilk | multi-year | E,S,G | medium | V1,V2,V4 | Nguon VN, thuan ngu canh noi dia, co report theo nam |

## 4. Mapping tai lieu ESG complex

| ID | Ten tai lieu | To chuc | Nam | ESG chinh | Do kho | Dung tot cho version | Cau truc tai lieu |
|---|---|---|---|---|---|---|---|
| ESG-X01 | Microsoft Environmental Sustainability Report | Microsoft | 2025 | E,S,G | hard | V3,V5,V6 | Dai, nhieu metric, phu hop test rerank/multi-hop |
| ESG-X02 | Unilever Annual Report and Accounts | Unilever | 2025 | E,S,G | hard | V3,V5,V6 | Tich hop tai chinh + ESG + risk, context dai |
| ESG-X03 | Toyota Sustainability Data Book | Toyota | latest | E,S,G | hard | V3,V5,V6 | Data-heavy, nhieu bang so lieu, test chunking phuc tap |
| ESG-X04 | FPT Investor Reports | FPT | multi-year | E,S,G | medium-hard | V2,V4,V5 | Report doanh nghiep VN, co annual/sustainability |

## 5. Quy tac su dung

1. Khong sua noi dung file trong `01_synthetic_controlled` neu da dung de baseline.
2. Tai lieu public tai ve local se duoc doi ten file theo ID (`ESG-Cxx`, `ESG-Xxx`) de de track.
3. Moi thay doi dataset phai cap nhat `sources.md` va `eval_set.md`.
4. Khi chua tai duoc file do network/sandbox, van giu URL + metadata va danh dau `manual_download_required`.

## 6. Trang thai hien tai

- Da co du bucket va metadata ESG core/complex.
- Da tai local du 12/12 tai lieu ESG public theo danh sach `sources.md`.
- Bo ESG Core Dataset da san sang cho baseline/eval evidence-based.
