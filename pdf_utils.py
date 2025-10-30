# pdf_utils.py
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
        self.set_font('Sarabun', 'B', 16)
        self.cell(0, 10, 'ใบเสร็จรับเงิน', border=0, ln=1, align='C') # <-- เปลี่ยนชื่อเป็นกลางๆ
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.add_font('Sarabun', '', 'fonts/Sarabun-Regular.ttf', uni=True)
        self.set_font('Sarabun', '', 10)
        col_width = (self.w - self.l_margin - self.r_margin) / 2
        self.cell(col_width, 10, 'ผู้ชำระเงิน ........................................', align='L') 
        self.cell(col_width, 10, 'ผู้รับเงิน ........................................', align='R', ln=1)
        member_name = self.member_info.get("Name", "")
        self.cell(col_width, 10, f'({member_name})', align='C')
        self.cell(col_width, 10, '(........................................)', align='R', ln=1)

def generate_receipt_pdf(receipt_data: dict):
    """
    สร้างไฟล์ PDF อเนกประสงค์สำหรับธุรกรรมทุกประเภท (ขนาด A5)
    """
    pdf = PDF(format='A5')          # <-- 1. ตั้งค่าขนาดเป็น A5
    pdf.set_text_shaping(True)     # <-- 2. เปิดโหมดภาษาไทย
    pdf.member_info = receipt_data['member_info']

    pdf.add_font('Sarabun', '', 'fonts/Sarabun-Regular.ttf', uni=True)
    pdf.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
    
    pdf.add_page()
    pdf.set_font('Sarabun', '', 12)

    # --- ส่วนข้อมูลส่วนตัว (เหมือนเดิม) ---
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(0, 8, f"ข้อมูลผู้ทำรายการ", ln=1)
    pdf.set_font('Sarabun', '', 12)
    pdf.cell(0, 8, f"  ชื่อ: {receipt_data['member_info'].get('Name', '')}", ln=1)
    address = (
        f"  ที่อยู่: {receipt_data['member_info'].get('AddressNo', '')} "
        f"หมู่บ้าน {receipt_data['member_info'].get('Village', '')} "
        f"ต.{receipt_data['member_info'].get('SubDistrict', '')} "
        f"อ.{receipt_data['member_info'].get('District', '')} "
        f"จ.{receipt_data['member_info'].get('Province', '')}"
    )
    pdf.cell(0, 8, address, ln=1)
    pdf.cell(0, 8, f"  วันที่ทำรายการ: {receipt_data['payment_date']}", ln=1)
    pdf.ln(5)

    # --- 3. ส่วนตารางรายการ (แบบไดนามิก) ---
    # (A5 กว้าง 148mm, เราใช้ 100 + 30 = 130mm)
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(100, 10, 'รายการ', border=1)
    pdf.cell(30, 10, 'จำนวนเงิน (บาท)', border=1, ln=1, align='C')
    
    pdf.set_font('Sarabun', '', 12)
    total_paid = 0
    # วนลูปตาม "รายการ" ที่หน้าแอปส่งมาให้
    for item in receipt_data.get('line_items', []):
        label = item.get('label', 'N/A')
        amount = item.get('amount', 0)
        pdf.cell(100, 10, f"  {label}", border='L,R')
        pdf.cell(30, 10, f"{amount:,.2f}", border='L,R', ln=1, align='R')
        total_paid += amount
    
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(100, 10, f"  รวมทั้งสิ้น", border=1)
    pdf.cell(30, 10, f"{total_paid:,.2f}", border=1, ln=1, align='R')
    pdf.ln(10)

    # --- 4. ส่วนยอดคงเหลือ (แบบไดนามิก) ---
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(0, 8, f"ยอดคงเหลือ", ln=1)
    pdf.set_font('Sarabun', '', 12)
    # วนลูปตาม "ยอดคงเหลือ" ที่หน้าแอปส่งมาให้
    for balance in receipt_data.get('balance_summary', []):
        label = balance.get('label', 'N/A')
        amount = balance.get('amount', 0)
        unit = balance.get('unit', 'บาท') # เพิ่มหน่วย (สำหรับ "หุ้น")
        pdf.cell(0, 8, f"  {label}: {amount:,.2f} {unit}", ln=1)
    
    # ส่งออกไฟล์ PDF เป็น bytes
    return pdf.output(dest='S')
