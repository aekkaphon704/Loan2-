import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ตั้งค่าฟอนต์ภาษาไทย ---
try:
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
    y_pos = 730  # ขยับลงมาจากขอบบนนิดหน่อย
    c.setFont(FONT_BOLD, 26)
    c.drawCentredString(width / 2.0, y_pos, "ใบเสร็จรับเงิน")

    # --- 2. ข้อมูลลูกหนี้ และ วันที่ชำระ ---
    y_pos -= 60
    c.setFont(FONT_NAME, 18)
    c.drawString(70, y_pos, f"ชื่อลูกหนี้: {member_name}")
    y_pos -= 30
    c.drawString(70, y_pos, f"วันที่ชำระ: {pay_date}")

    # --- 3. รายการที่ชำระ ---
    y_pos -= 45
    c.setFont(FONT_NAME, 18)
    c.drawString(70, y_pos, "รายการที่ชำระ:")
    
    y_pos -= 35
    c.setFont(FONT_NAME, 17) # ปรับขนาดฟอนต์ให้สระไม่เบียดกันเกินไป
    for item in line_items:
        # ตัดคำว่า "บัญชี บัญชี" ที่ซ้ำซ้อนออก
        clean_label = item['label'].replace("บัญชี บัญชี", "บัญชี")
        c.drawString(100, y_pos, clean_label)
        c.drawRightString(520, y_pos, f"{item['amount']:,.2f} บาท")
        y_pos -= 30

    # เส้นประคั่นรายการ
    y_pos -= 10
    c.drawString(70, y_pos, "-------------------------------------------------------------------------------------------------------------")
    y_pos -= 35

    # --- 4. สรุปยอดคงเหลือ ---
    for bal in balance_summary:
        unit = bal.get('unit', 'บาท')
        c.drawString(70, y_pos, bal['label'] + ":")
        c.drawRightString(520, y_pos, f"{bal['amount']:,.2f} {unit}")
        y_pos -= 30

    # เส้นประคั่นรายการด้านล่าง
    y_pos -= 10
    c.drawString(70, y_pos, "-------------------------------------------------------------------------------------------------------------")

    # --- 5. ลายเซ็นต์ (Dynamic: ขยับตามข้อมูล) ---
    # ให้เว้นระยะจากบรรทัดสุดท้ายลงมา 120 พิกเซล (ไม่ตกลงไปก้นกระดาษ)
    sig_y = y_pos - 120 
    
    # ดักไว้ไม่ให้ลายเซ็นตกขอบกระดาษถ้ารายการยาวมาก
    if sig_y < 100: 
        sig_y = 100

    c.setFont(FONT_NAME, 17)
    c.drawString(90, sig_y + 25, "_________________________")
    c.drawString(120, sig_y, "(       ผู้ชำระเงิน       )")

    c.drawString(330, sig_y + 25, "_________________________")
    c.drawString(360, sig_y, "(        ผู้รับเงิน        )")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
