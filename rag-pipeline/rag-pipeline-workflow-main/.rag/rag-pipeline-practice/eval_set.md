# Evaluation Set

Schema cap nhat: evidence-based eval set voi cot evidence source va extracted field.

| ID | Question | Expected Evidence Source | Expected Answer Notes | Expected Extracted Field neu co | Difficulty | Category | Status |
|---|---|---|---|---|---|---|---|
| ESG-E01 | Chinh sach moi truong dat muc giam tieu thu dien moi nam la bao nhieu? | 01_synthetic_controlled/environment_policy.md | Giam 3% moi nam | energy_reduction_target | easy | Environmental | draft |
| ESG-E02 | Muc tieu ty le tai che chat thai nam 2026 la bao nhieu? | 01_synthetic_controlled/environment_policy.md | >= 72% | waste_recycling_target | easy | Environmental | draft |
| ESG-E03 | Chinh sach moi truong yeu cau gi doi voi nuoc thai? | 01_synthetic_controlled/environment_policy.md | 100% xu ly truoc khi xa thai | wastewater_treatment_policy | easy | Environmental | draft |
| ESG-E04 | Co bao nhieu nhom phan loai chat thai tai nguon? | 01_synthetic_controlled/environment_policy.md | 4 nhom | waste_classification_groups | easy | Environmental | draft |
| ESG-E05 | Muc tieu giam cuong do phat thai Scope 1+2 den 2028 la gi? | 01_synthetic_controlled/company_overview.md | Giam 25% so voi 2023 | scope12_reduction_target | medium | Environmental | draft |
| ESG-E06 | Ty le tai che chat thai nam 2025 cua cong ty la bao nhieu? | 01_synthetic_controlled/company_overview.md | 68% | waste_recycling_rate_2025 | easy | Environmental | draft |
| ESG-E07 | Trong bo ESG core, tai lieu nao la chuan climate governance pho bien? | data/rag_dataset/sources.md | TCFD Recommendations | evidence_doc_id | medium | Environmental | draft |
| ESG-E08 | Tai lieu nao duoc de xuat de lay metric emissions/energy/water ro rang? | data/rag_dataset/sources.md | Google 2025 Environmental Report | evidence_doc_id | medium | Environmental | draft |
| ESG-E09 | Tai lieu nao trong ESG core phu hop cho benchmark environmental theo ngu canh VN? | data/rag_dataset/sources.md | Vinamilk sustainability reports | evidence_doc_id | medium | Environmental | draft |
| ESG-E10 | Chinh sach moi truong co yeu cau danh gia ben thu ba theo tan suat nao? | 01_synthetic_controlled/environment_policy.md | Moi nam 1 lan | third_party_audit_frequency | easy | Environmental | draft |
| ESG-E11 | Co cam ket nao ve tai su dung nuoc sau xu ly? | 01_synthetic_controlled/environment_policy.md | Toi thieu 15% | water_reuse_target | easy | Environmental | draft |
| ESG-E12 | Chi so cuong do dien nang duoc dat theo don vi nao? | 01_synthetic_controlled/environment_policy.md | kWh/san pham | energy_intensity_unit | easy | Environmental | draft |
| ESG-E13 | Neu can tai lieu environmental dai va phuc tap de test rerank, nen dung tai lieu nao? | data/rag_dataset/dataset_readme.md | Microsoft/Unilever/Toyota complex set | recommended_complex_docs | hard | Environmental | draft |
| ESG-E14 | Trong sources, trang thai download cua Google Environmental Report la gi? | data/rag_dataset/sources.md | downloaded | source_status | easy | Environmental | draft |
| ESG-E15 | Muc tieu vi pham xa thai nam 2026 la bao nhieu vu? | 01_synthetic_controlled/environment_policy.md | 0 vu | wastewater_violation_target | easy | Environmental | draft |
| ESG-S01 | Ty le nu toan cong ty nam 2025 la bao nhieu? | 01_synthetic_controlled/social_policy.md | 47% | female_ratio_2025 | easy | Social | draft |
| ESG-S02 | Ty le nu cap quan ly trung muc tieu 2027 la bao nhieu? | 01_synthetic_controlled/social_policy.md | 40% | women_mid_management_target | easy | Social | draft |
| ESG-S03 | Cong ty co su dung lao dong duoi 18 tuoi cho vi tri san xuat khong? | 01_synthetic_controlled/social_policy.md | Khong | child_labor_policy_flag | easy | Social | draft |
| ESG-S04 | Muc luong toi thieu noi bo cao hon muc luong toi thieu vung bao nhieu? | 01_synthetic_controlled/social_policy.md | 12% | wage_premium_ratio | easy | Social | draft |
| ESG-S05 | LTIFR muc tieu nam 2026 la bao nhieu? | 01_synthetic_controlled/social_policy.md | <= 0.35 | ltifr_target_2026 | easy | Social | draft |
| ESG-S06 | Tan suat dien tap PCCC toi thieu la bao nhieu? | 01_synthetic_controlled/social_policy.md | 2 lan/nam moi co so | fire_drill_frequency | easy | Social | draft |
| ESG-S07 | Co bao nhieu ngay lam viec de phan hoi ban dau cho khieu nai/to cao? | 01_synthetic_controlled/social_policy.md; 01_synthetic_controlled/compliance_faq.md | 5 ngay lam viec | whistleblowing_response_sla | medium | Social | draft |
| ESG-S08 | Co nhung kenh nao de bao cao vi pham dao duc? | 01_synthetic_controlled/compliance_faq.md | Email, hotline, form an danh | reporting_channels | easy | Social | draft |
| ESG-S09 | Chinh sach co bao ve nguoi to cao khong? | 01_synthetic_controlled/social_policy.md; 01_synthetic_controlled/compliance_faq.md | Co, cam tra dua | anti_retaliation_policy | medium | Social | draft |
| ESG-S10 | Muc tieu ty le nhan vien khuyet tat nam 2027 la bao nhieu? | 01_synthetic_controlled/social_policy.md | 2.0% | disability_ratio_target | easy | Social | draft |
| ESG-S11 | Dieu kien doi tra 30 ngay cua san pham GR-Home gom gi? | 01_synthetic_controlled/product_internal_faq.md | Loi NSX, du phu kien, hoa don hop le | return_policy_conditions | medium | Social | draft |
| ESG-S12 | SLA xu ly ticket lien quan an toan la bao lau? | 01_synthetic_controlled/product_internal_faq.md | <= 24 gio | safety_ticket_sla | easy | Social | draft |
| ESG-S13 | Tai lieu nao trong ESG core de danh gia human rights/labour theo questionnaire? | data/rag_dataset/sources.md | UNGC CoP Questionnaire | evidence_doc_id | medium | Social | draft |
| ESG-S14 | Tai lieu OECD trong sources thuoc nhom nao va vi sao? | data/rag_dataset/sources.md | S,G vi due diligence va responsible business conduct | esg_dimension_mapping | hard | Social | draft |
| ESG-S15 | Chinh sach gio lam them toi da moi thang la bao nhieu gio? | 01_synthetic_controlled/social_policy.md | 30 gio/thang | overtime_limit | easy | Social | draft |
| ESG-G01 | Tong so thanh vien HDQT la bao nhieu? | 01_synthetic_controlled/governance_policy.md | 5 | board_size | easy | Governance | draft |
| ESG-G02 | Co bao nhieu thanh vien doc lap trong HDQT? | 01_synthetic_controlled/governance_policy.md | 2 | independent_board_members | easy | Governance | draft |
| ESG-G03 | Qua tang tren nguong nao phai khai bao? | 01_synthetic_controlled/governance_policy.md; 01_synthetic_controlled/compliance_faq.md | Tren 100 USD | gift_threshold | easy | Governance | draft |
| ESG-G04 | Chu ky cap nhat risk register la gi? | 01_synthetic_controlled/governance_policy.md | Hang quy | risk_register_frequency | easy | Governance | draft |
| ESG-G05 | Incident report governance phai gui trong bao lau? | 01_synthetic_controlled/governance_policy.md | 48 gio | governance_incident_sla | easy | Governance | draft |
| ESG-G06 | Internal audit summary duoc gui tan suat nao? | 01_synthetic_controlled/governance_policy.md | 2 lan/nam | internal_audit_frequency | easy | Governance | draft |
| ESG-G07 | Du lieu Confidential co yeu cau bao mat gi? | 01_synthetic_controlled/governance_policy.md | Ma hoa khi luu tru va truyen | confidential_data_control | medium | Governance | draft |
| ESG-G08 | Tai lieu nao trong ESG core phu hop lam chuan disclosure governance theo IFRS sustainability? | data/rag_dataset/sources.md | IFRS Sustainability Standards Navigator | evidence_doc_id | medium | Governance | draft |
| ESG-G09 | TCFD recommendations lien quan den nhung tru cot nao? | data/rag_dataset/sources.md | Governance, strategy, risk management, metrics & targets | tcfd_pillars | hard | Governance | draft |
| ESG-G10 | Co bao nhieu uy ban truc thuoc HDQT trong du lieu synthetic? | 01_synthetic_controlled/governance_policy.md | 3 uy ban | board_committee_count | easy | Governance | draft |
| ESG-M01 | Tong hop cac nguong thoi gian bao cao khan cap lien quan E va G trong bo synthetic. | 01_synthetic_controlled/environment_policy.md; 01_synthetic_controlled/governance_policy.md | E: 24h; G: 24h security incident, 48h incident report | multi_source_synthesis_field | hard | Multi-hop | draft |
| ESG-M02 | Neu mot su co an toan san pham xay ra, bo phan nao va SLA nao duoc uu tien? | 01_synthetic_controlled/product_internal_faq.md; 01_synthetic_controlled/governance_policy.md | Quality+Compliance, <=24h, bao cao incident | multi_source_synthesis_field | hard | Multi-hop | draft |
| ESG-M03 | Tong hop 3 KPI dai dien cho E, S, G tu bo synthetic. | company_overview.md; environment_policy.md; social_policy.md; governance_policy.md | KPI dinh luong dai dien cho E,S,G | multi_source_synthesis_field | hard | Multi-hop | draft |
| ESG-M04 | Tai lieu nao nen dung cho V3 de test hybrid retrieval tren ESG thuc te va vi sao? | data/rag_dataset/dataset_readme.md; data/rag_dataset/sources.md | Core + complex docs co do dai va metric | multi_source_synthesis_field | hard | Multi-hop | draft |
| ESG-M05 | Neu can danh gia policy-level va metric-level cung luc, nen ket hop nhung bucket nao? | data/rag_dataset/dataset_readme.md | 01 + 02 (+03 cho hard cases) | multi_source_synthesis_field | hard | Multi-hop | draft |
| ESG-I01 | Microsoft report 2025 co tong Scope 3 emissions la bao nhieu MtCO2e? | ESG-X01 (chua tai local) | Khong du thong tin trong local context hien tai | insufficient_information_flag | insufficient | Insufficient | draft |
| ESG-I02 | Apple Environmental Progress Report 2025 co tong water withdrawal la bao nhieu? | ESG-C06 (chua tai local) | Khong du thong tin trong local context hien tai | insufficient_information_flag | insufficient | Insufficient | draft |
| ESG-I03 | Ten Chu tich HDQT cua Vinamilk trong bao cao sustainability moi nhat la ai? | ESG-C08 (chua tai local) | Khong du thong tin trong local context hien tai | insufficient_information_flag | insufficient | Insufficient | draft |
| ESG-I04 | FPT report moi nhat cong bo ty le women in leadership chinh xac la bao nhieu? | ESG-X04 (chua tai local) | Khong du thong tin trong local context hien tai | insufficient_information_flag | insufficient | Insufficient | draft |
| ESG-I05 | Toyota Sustainability Data Book moi nhat co chi tieu methane reduction cu the nao? | ESG-X03 (chua tai local) | Khong du thong tin trong local context hien tai | insufficient_information_flag | insufficient | Insufficient | draft |
