import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ตั้งค่าฟอนต์ภาษาไทย ---
try:
    # ชี้ที่อยู่ไฟล์ไปที่โฟลเดอร์ fonts/ ตามโครงสร้างของโปรเจกต์
    pdfmetrics.registerFont(TTFont('Sarabun', 'fonts/Sarabun-Regular.ttf'))
    try:
        pdfmetrics.registerFont(TTFont('Sarabun-Bold', 'fonts/Sarabun-Bold.ttf'))
        FONT_BOLD = 'Sarabun-Bold'
    except:
        FONT_BOLD = 'Sarabun'
    FONT_NAME = 'Sarabun'
except Exception as e:
    print(f"Font Load Error: {e}")
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

def generate_receipt_pdf(receipt_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    member_name = receipt_data['member_info'].get('Name', 'ไม่ระบุ')
    pay_date = receipt_data.get('payment_date', '')
    line_items = receipt_data.get('line_items', [])
    balance_summary = receipt_data.get('balance_summary', [])

    # --- 1. หัวกระดาษ (ตรงกลาง) ---
    c.setFont(FONT_BOLD, 24)
    c.drawCentredString(width / 2.0, 750, "ใบเสร็จรับเงิน")

    # --- 2. ข้อมูลลูกหนี้ และ วันที่ชำระ (ชิดซ้าย) ---
    c.setFont(FONT_NAME, 16)
    c.drawString(70, 680, f"ชื่อลูกหนี้: {member_name}")
    c.drawString(70, 650, f"วันที่ชำระ: {pay_date}")

    # --- 3. รายการที่ชำระ ---
    c.drawString(70, 610, "รายการที่ชำระ:")
    
    y_pos = 580
    c.setFont(FONT_NAME, 15) 
    for item in line_items:
        c.drawString(100, y_pos, item['label'])
        c.drawRightString(530, y_pos, f"{item['amount']:,.2f} บาท") 
        y_pos -= 25

    y_pos -= 10
    c.drawString(70, y_pos, "-")
    y_pos -= 35

    # --- 4. สรุปยอดคงเหลือ ---
    for bal in balance_summary:
        unit = bal.get('unit', 'บาท')
        c.drawString(70, y_pos, bal['label'] + ":")
        c.drawRightString(530, y_pos, f"{bal['amount']:,.2f} {unit}")
        y_pos -= 25

    y_pos -= 10
    c.drawString(70, y_pos, "-")

    # --- 5. ลายเซ็นต์ (ด้านล่างสุด) ---
    sig_y = 200
    c.setFont(FONT_NAME, 16)
    c.drawString(90, sig_y + 25, "_________________________")
    c.drawString(120, sig_y, "(       ผู้ชำระเงิน       )")

    c.drawString(350, sig_y + 25, "_________________________")
    c.drawString(380, sig_y, "(        ผู้รับเงิน        )")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
