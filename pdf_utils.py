import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ตั้งค่าฟอนต์ภาษาไทย ---
# (หมายเหตุ: ต้องมีไฟล์ THSarabunNew.ttf อยู่ในโฟลเดอร์เดียวกับโปรเจกต์)
try:
    pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))
    try:
        pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', 'THSarabunNew Bold.ttf'))
        FONT_BOLD = 'THSarabunNew-Bold'
    except:
        FONT_BOLD = 'THSarabunNew' # ถ้าไม่มีไฟล์ฟอนต์ตัวหนา ให้ใช้ตัวธรรมดาแทน
    FONT_NAME = 'THSarabunNew'
except:
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

def generate_receipt_pdf(receipt_data):
    buffer = io.BytesIO()
    # ตั้งค่ากระดาษเป็น A4
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ดึงข้อมูลจากตะกร้าใบเสร็จ
    member_name = receipt_data['member_info'].get('Name', 'ไม่ระบุ')
    pay_date = receipt_data.get('payment_date', '')
    line_items = receipt_data.get('line_items', [])
    balance_summary = receipt_data.get('balance_summary', [])

    # --- 1. หัวกระดาษ (ตรงกลาง) ---
    c.setFont(FONT_BOLD, 24)
    c.drawCentredString(width / 2.0, 750, "ใบเสร็จรับเงิน")

    # --- 2. ข้อมูลลูกหนี้ และ วันที่ชำระ (ชิดซ้าย) ---
    c.setFont(FONT_NAME, 16)
    c.drawString(80, 680, f"ชื่อลูกหนี้: {member_name}")
    c.drawString(80, 650, f"วันที่ชำระ: {pay_date}")

    # --- 3. รายการที่ชำระ (ใส่ชื่อรายการตามที่ขอ) ---
    c.drawString(80, 610, "รายการที่ชำระ:")
    
    y_pos = 580
    for item in line_items:
        # ชื่อรายการเยื้องเข้ามานิดหน่อย
        c.drawString(120, y_pos, item['label'])
        # ยอดเงินชิดขวา
        c.drawRightString(515, y_pos, f"{item['amount']:,.2f} บาท")
        y_pos -= 30

    # ขีดเส้นคั่นเล็กๆ เหมือนในรูปต้นฉบับ
    y_pos -= 10
    c.drawString(80, y_pos, "-")
    y_pos -= 40

    # --- 4. สรุปยอดคงเหลือต่างๆ (ดึงจากระบบแบบไดนามิก) ---
    for bal in balance_summary:
        unit = bal.get('unit', 'บาท')
        # ชื่อยอดคงเหลือชิดซ้าย
        c.drawString(80, y_pos, bal['label'] + ":")
        # จำนวนเงินชิดขวา
        c.drawRightString(515, y_pos, f"{bal['amount']:,.2f} {unit}")
        y_pos -= 30

    # ขีดเส้นคั่นเล็กๆ ด้านล่าง เหมือนในรูปต้นฉบับ
    y_pos -= 10
    c.drawString(80, y_pos, "-")

    # --- 5. ลายเซ็นต์ (ด้านล่างสุด) ---
    sig_y = 200 # ขยับขึ้นมาจากขอบล่างพอประมาณ
    
    # ลายเซ็นต์ ผู้ชำระเงิน (ฝั่งซ้าย)
    c.drawString(80, sig_y + 25, "_________________________")
    c.drawString(110, sig_y, "(       ผู้ชำระเงิน       )")

    # ลายเซ็นต์ ผู้รับเงิน (ฝั่งขวา)
    c.drawString(350, sig_y + 25, "_________________________")
    c.drawString(380, sig_y, "(        ผู้รับเงิน        )")

    # บันทึกไฟล์ PDF
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
