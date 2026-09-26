import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ตั้งค่าฟอนต์ภาษาไทย ---
try:
    # 💡 ชี้ไปที่ฟอนต์ราชการ THSarabunNew เพื่อแก้ปัญหาสระลอย/ทับกัน
    pdfmetrics.registerFont(TTFont('THSarabunNew', 'fonts/THSarabunNew.ttf'))
    try:
        pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', 'fonts/THSarabunNew Bold.ttf'))
        FONT_BOLD = 'THSarabunNew-Bold'
    except:
        FONT_BOLD = 'THSarabunNew'
    FONT_NAME = 'THSarabunNew'
except Exception as e:
    print(f"Font Load Error: {e}")
    # ระบบสำรอง: ถ้าลืมใส่ THSarabunNew จะดึง Sarabun ตัวเดิมมาแก้ขัด (แต่สระอาจจะลอย)
    try:
        pdfmetrics.registerFont(TTFont('Sarabun', 'fonts/Sarabun-Regular.ttf'))
        FONT_NAME = 'Sarabun'
        FONT_BOLD = 'Sarabun'
    except:
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
    y_pos = 730  
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
    c.setFont(FONT_NAME, 17) 
    for item in line_items:
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
        label_text = bal['label']
        
        # 💡 แก้ปัญหาข้อความชนตัวเลข: ถ้ารหัสสัญญามีคำว่า L-M- (แปลว่ายาวแน่ๆ) ให้ปัดบรรทัด
        if len(label_text) > 25 and "L-M-" in label_text:
            parts = label_text.split(" L-M-")
            c.drawString(70, y_pos, parts[0] + ":")
            y_pos -= 25 # ปัดตัวเลขรหัสลงมาอีก 1 บรรทัด
            c.drawString(100, y_pos, "รหัส: L-M-" + parts[1])
            c.drawRightString(520, y_pos, f"{bal['amount']:,.2f} {unit}")
        else:
            c.drawString(70, y_pos, label_text + ":")
            c.drawRightString(520, y_pos, f"{bal['amount']:,.2f} {unit}")
        
        y_pos -= 30

    # เส้นประคั่นรายการด้านล่าง
    y_pos -= 10
    c.drawString(70, y_pos, "-------------------------------------------------------------------------------------------------------------")

    # --- 5. ลายเซ็นต์ ---
    sig_y = y_pos - 120 
    if sig_y < 100: sig_y = 100

    c.setFont(FONT_NAME, 17)
    c.drawString(90, sig_y + 25, "_________________________")
    c.drawString(120, sig_y, "(       ผู้ชำระเงิน       )")

    c.drawString(330, sig_y + 25, "_________________________")
    c.drawString(360, sig_y, "(        ผู้รับเงิน        )")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
