# -*- coding: utf-8 -*-
"""Tao file PDF mau ve ESG de test RAG."""
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Bao Cao ESG 2024 - Cong Ty Xanh Viet Nam", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Trang {self.page_no()}", align="C")

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Helvetica", size=11)

sections = [
    ("1. GIOI THIEU",
     "Cong Ty Xanh Viet Nam duoc thanh lap nam 2010, hoat dong trong linh vuc nang luong tai tao "
     "va quan ly moi truong. Cong ty hien co hon 2.000 nhan vien tai 12 tinh thanh tren ca nuoc. "
     "Chien luoc phat trien ben vung la nen tang cot loi trong moi hoat dong kinh doanh cua chung toi."),

    ("2. MOI TRUONG (Environmental)",
     "Phat thai khi nha kinh: Nam 2024, tong luong phat thai CO2 cua cong ty dat 12.500 tan, "
     "giam 18% so voi nam 2023 nho viec chuyen doi sang su dung nang luong mat troi tai 3 nha may. "
     "Tieu thu nuoc: Giam 22% nho he thong tai che nuoc khep kin tai khu cong nghiep Binh Duong. "
     "Chat thai ran: 95% chat thai duoc tai che hoac tai su dung, chi 5% dua ra bai rac. "
     "Nang luong tai tao: 65% dien nang su dung den tu cac to may dien gio va dien mat troi. "
     "Muc tieu 2025: Dat phat thai rong bang khong (Net Zero) tai toan bo co so san xuat phia Nam."),

    ("3. XA HOI (Social)",
     "Nhan su: Cong ty co 2.134 nhan vien chinh thuc, trong do 42% la phu nu. Muc luong trung "
     "binh cao hon 35% so voi muc luong toi thieu vung. Dao tao: Moi nhan vien duoc dao tao trung binh "
     "48 gio/nam ve ky nang chuyen mon va an toan lao dong. "
     "An toan lao dong: Ti le tai nan lao dong giam 60% trong 3 nam lien tiep. "
     "Cong dong: Dau tu 5 ty dong cho cac du an nuoc sach tai 20 xa vung sau vung xa. "
     "Khach hang: Chi so hai long khach hang (CSAT) dat 94 diem, tang 6 diem so voi 2023."),

    ("4. QUAN TRI (Governance)",
     "Hoi dong quan tri: Gom 9 thanh vien, trong do 4 thanh vien doc lap va 3 phu nu. "
     "Chinh sach chong tham nhung: 100% nhan vien cap quan ly ky cam ket dao duc kinh doanh. "
     "Bao mat du lieu: He thong ISO 27001 duoc cap chung chi nam 2024. "
     "Kiem toan: Bao cao tai chinh duoc kiem toan boi PwC, khong co kien nghi trong yeu. "
     "Minh bach thong tin: Cong ty cong bo bao cao ESG hang nam theo chuan GRI Standards."),

    ("5. CAM KET VA MUC TIEU 2025-2030",
     "Muc tieu den 2030: Giam 50% luong phat thai CO2 so voi moc 2020. "
     "Dat 100% nang luong tai tao trong san xuat. "
     "Dau tu 50 ty dong vao cac du an phat trien cong dong. "
     "Mo rong sang 5 nuoc ASEAN voi tieu chuan ESG dong nhat. "
     "Ra mat quy ESG tri gia 20 ty dong ho tro startup xanh Viet Nam."),
]

for title, body in sections:
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, body)
    pdf.ln(4)

out = "D:/ESG/AI/sample_esg_report.pdf"
pdf.output(out)
print(f"Da tao: {out}")
