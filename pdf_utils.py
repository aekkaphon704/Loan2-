# pdf_utils.py
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
        self.set_font('Sarabun', 'B', 16)
        self.cell(0, 10, 'ใบเสร็จรับเงิน', border=0, ln=1, align='C')
        self.ln(10) # ลดระยะห่างเล็กน้อยสำหรับ A5

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
    pdf = PDF(format='A5')          # <-- ตั้งค่าขนาดเป็น A5
    pdf.set_text_shaping(True)     # <-- เปิดโหมดภาษาไทย
    pdf.member_info = receipt_data['member_info']

    pdf.add_font('Sarabun', '', 'fonts/Sarabun-Regular.ttf', uni=True)
    pdf.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
    
    pdf.add_page()
    pdf.set_font('Sarabun', '', 12) # ขนาดปกติสำหรับข้อมูลส่วนตัว

    # --- ส่วนข้อมูลส่วนตัว ---
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
    pdf.ln(2) # เว้นบรรทัดเล็กน้อย

    # --- *** นี่คือส่วนที่แก้ไข (ข้อ 2) *** ---
    # เพิ่ม LoanID ถ้ามี
    loan_id = receipt_data.get('loan_id')
    if loan_id:
        pdf.set_font('Sarabun', 'B', 11) # ตั้งค่าฟอนต์สำหรับ LoanID
        pdf.cell(0, 8, f"  สำหรับสัญญาเลขที่: {loan_id}", ln=1, border=0)
    pdf.ln(3) # เว้นบรรทัดก่อนตาราง
    # --- *** สิ้นสุดการแก้ไข *** ---

    # --- ส่วนตารางรายการ (แบบไดนามิก) ---
    
    # --- *** นี่คือส่วนที่แก้ไข (ข้อ 3) *** ---
    # ลดขนาดฟอนต์หัวตาราง และลดความสูงแถว
    pdf.set_font('Sarabun', 'B', 10) # <-- ลดขนาดฟอนต์หัวตาราง
    pdf.cell(100, 8, 'รายการ', border=1) # <-- ลดความสูงแถว
    pdf.cell(30, 8, 'จำนวนเงิน (บาท)', border=1, ln=1, align='C') # <-- ลดความสูงแถว
    
    pdf.set_font('Sarabun', '', 10) # <-- ลดขนาดฟอนต์เนื้อหาตาราง
    total_paid = 0
    for item in receipt_data.get('line_items', []):
        label = item.get('label', 'N/A')
        amount = item.get('amount', 0)
        pdf.cell(100, 8, f"  {label}", border='L,R') # <-- ลดความสูงแถว
        pdf.cell(30, 8, f"{amount:,.2f}", border='L,R', ln=1, align='R') # <-- ลดความสูงแถว
        total_paid += amount
    
    pdf.set_font('Sarabun', 'B', 10) # <-- ลดขนาดฟอนต์ยอดรวม
    pdf.cell(100, 8, f"  รวมทั้งสิ้น", border=1) # <-- ลดความสูงแถว
    pdf.cell(30, 8, f"{total_paid:,.2f}", border=1, ln=1, align='R') # <-- ลดความสูงแถว
    pdf.ln(10)
    # --- *** สิ้นสุดการแก้ไข *** ---

    # --- ส่วนยอดคงเหลือ (แบบไดนามิก) ---
    pdf.set_font('Sarabun', 'B', 12) # (กลับมาใช้ขนาด 12)
    pdf.cell(0, 8, f"ยอดคงเหลือ", ln=1)
    pdf.set_font('Sarabun', '', 12)
    
    if not receipt_data.get('balance_summary'):
        pdf.cell(0, 8, "  - ไม่มีหนี้คงเหลือ -", ln=1)
    else:
        for balance in receipt_data.get('balance_summary', []):
            label = balance.get('label', 'N/A')
            amount = balance.get('amount', 0)
            unit = balance.get('unit', 'บาท')
            pdf.cell(0, 8, f"  {label}: {amount:,.2f} {unit}", ln=1)
    
    # ส่งออกไฟล์ PDF เป็น bytes
    return pdf.output(dest='S')
