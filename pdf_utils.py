# pdf_utils.py
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # ตั้งค่าฟอนต์สำหรับ Header
        self.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
        self.set_font('Sarabun', 'B', 16)
        # สร้างกล่องข้อความ
        self.cell(0, 10, 'ใบเสร็จชำระเงิน', border=0, ln=1, align='C')
        self.ln(10) # เว้นบรรทัด

    def footer(self):
    # ตั้งค่าฟอนต์สำหรับ Footer
        self.set_y(-30) # ย้ายตำแหน่ง Y ไปใกล้ด้านล่าง
        self.add_font('Sarabun', '', 'fonts/Sarabun-Regular.ttf', uni=True)
        self.set_font('Sarabun', '', 10)

    # คำนวณความกว้างครึ่งหนึ่งของหน้ากระดาษที่ใช้งานได้
    # (ความกว้างทั้งหมด - ขอบซ้าย - ขอบขวา) / 2
        col_width = (self.w - self.l_margin - self.r_margin) / 2

    # --- ส่วนที่แก้ไข ---
    # ช่องผู้ชำระเงิน (ชิดซ้าย)
        self.cell(col_width, 10, 'ผู้ชำระเงิน ........................................', align='C') 
    # ช่องผู้รับเงิน (ชิดขวา)
        self.cell(col_width, 10, 'ผู้รับเงิน ........................................', align='C', ln=1)

    # ดึงชื่อผู้ชำระจากข้อมูลที่ส่งมา
        member_name = self.member_info.get("Name", "")

    # ชื่อผู้ชำระเงิน (ชิดซ้าย)
        self.cell(col_width, 10, f'({member_name})', align='C')
    # ชื่อผู้รับเงิน (ชิดขวา)
        self.cell(col_width, 10, '(....................................................)', align='C', ln=1)

def generate_receipt_pdf(receipt_data: dict):
    pdf = PDF()
    pdf.set_text_shaping(True)
    pdf.member_info = receipt_data['member_info'] # ส่งข้อมูลสมาชิกไปให้ footer ใช้

    # เพิ่มฟอนต์ภาษาไทย
    pdf.add_font('Sarabun', '', 'fonts/Sarabun-Regular.ttf', uni=True)
    pdf.add_font('Sarabun', 'B', 'fonts/Sarabun-Bold.ttf', uni=True)
    
    pdf.add_page()
    pdf.set_font('Sarabun', '', 12)

    # --- ส่วนข้อมูลส่วนตัว ---
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(0, 8, f"ข้อมูลผู้ชำระ", ln=1)
    pdf.set_font('Sarabun', '', 12)
    pdf.cell(0, 8, f"  ชื่อ: {receipt_data['member_info'].get('Name', '')}", ln=1)
    
    address = (
        f"  ที่อยู่: {receipt_data['member_info'].get('AddressNo', '')} "
        f"หมู่บ้าน {receipt_data['member_info'].get('Village', '')} "
        f"ต.{receipt_data['member_info'].get('SubDistrict', '')}"
    )
    pdf.cell(0, 8, address, ln=1)
    
    address2 = (
        f"  อ.{receipt_data['member_info'].get('District', '')} "
        f"จ.{receipt_data['member_info'].get('Province', '')}"
    )
    pdf.cell(0, 8, address2, ln=1)
    pdf.cell(0, 8, f"  วันที่ชำระ: {receipt_data['payment_date']}", ln=1)
    pdf.ln(5)

    # --- ส่วนตารางรายการ ---
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(150, 10, 'รายการ', border=1)
    pdf.cell(40, 10, 'จำนวนเงิน (บาท)', border=1, ln=1, align='C')
    
    pdf.set_font('Sarabun', '', 12)
    pdf.cell(150, 10, f"  ชำระหนี้บัญชีที่ {receipt_data['account_paid']}", border='L,R')
    pdf.cell(40, 10, f"{receipt_data['principal_paid']:.2f}", border='L,R', ln=1, align='R')
    
    pdf.cell(150, 10, f"  ดอกเบี้ย", border='L,R')
    pdf.cell(40, 10, f"{receipt_data['interest_paid']:.2f}", border='L,R', ln=1, align='R')
    
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(150, 10, f"  รวม", border=1)
    pdf.cell(40, 10, f"{receipt_data['total_paid']:.2f}", border=1, ln=1, align='R')
    pdf.ln(10)

    # --- ส่วนยอดคงเหลือ ---
    pdf.set_font('Sarabun', 'B', 12)
    pdf.cell(0, 8, f"ยอดคงเหลือ", ln=1)
    pdf.set_font('Sarabun', '', 12)
    balances = receipt_data['new_balances']
    pdf.cell(0, 8, f"  บัญชีเงินกู้ที่ 1: {balances.get('Loan1_Balance', 0):,.2f} บาท", ln=1)
    pdf.cell(0, 8, f"  บัญชีเงินกู้ที่ 2: {balances.get('Loan2_Balance', 0):,.2f} บาท", ln=1)
    pdf.cell(0, 8, f"  บัญชีเงินกู้ที่ 4: {balances.get('Loan4_Balance', 0):,.2f} บาท", ln=1)
    
    # ส่งออกไฟล์ PDF เป็น bytes
    return pdf.output(dest='S')