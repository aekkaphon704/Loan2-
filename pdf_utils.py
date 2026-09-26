# pdf_utils.py
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm

# --- ตั้งค่าฟอนต์ภาษาไทย ---
def setup_pdf_styles():
    # 1. ลองหาฟอนต์ THSarabunNew (ดีที่สุด)
    thai_font = 'THSarabunNew'
    thai_font_bold = 'THSarabunNew-Bold'
    
    try:
        # อ้างอิง Path ไปที่โฟลเดอร์ fonts/
        pdfmetrics.registerFont(TTFont(thai_font, 'fonts/THSarabunNew.ttf'))
        try:
            pdfmetrics.registerFont(TTFont(thai_font_bold, 'fonts/THSarabunNew Bold.ttf'))
        except:
            thai_font_bold = thai_font
    except:
        # 2. ถ้าระบบไม่เจอ THSarabunNew ให้ดึง Sarabun ตัวปกติมาใช้แทน
        try:
            thai_font = 'Sarabun'
            thai_font_bold = 'Sarabun-Bold'
            pdfmetrics.registerFont(TTFont(thai_font, 'fonts/Sarabun-Regular.ttf'))
            pdfmetrics.registerFont(TTFont(thai_font_bold, 'fonts/Sarabun-Bold.ttf'))
        except:
            thai_font = 'Helvetica'
            thai_font_bold = 'Helvetica-Bold'

    # สร้างสไตล์สำหรับใช้งานใน Paragraph
    styles = getSampleStyleSheet()
    
    style_definitions = [
        ('TitleStyle', thai_font_bold, 28, TA_CENTER, 20), 
        ('NormalLeft', thai_font, 16, TA_LEFT, 0),
        ('NormalRight', thai_font, 16, TA_RIGHT, 0),
        ('BoldLeft', thai_font_bold, 16, TA_LEFT, 0),
        ('BoldRight', thai_font_bold, 16, TA_RIGHT, 0),
        ('SignatureCenter', thai_font, 15, TA_CENTER, 0), 
    ]
    
    for name, font, size, alignment, space_after in style_definitions:
        if name not in styles.byName:
            styles.add(ParagraphStyle(
                name=name, 
                fontName=font, 
                fontSize=size, 
                alignment=alignment, 
                leading=size + 2, 
                spaceAfter=space_after
            ))

    return styles, thai_font, thai_font_bold

def generate_receipt_pdf(receipt_data):
    # โหลด Stylesheet
    pdf_styles, font_normal, font_bold = setup_pdf_styles()
    
    buffer = io.BytesIO()
    # ตั้งค่าหน้ากระดาษ A4 เว้นขอบ 2.5 ซม.
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=2.5*cm, rightMargin=2.5*cm, 
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    elements = []

    # ดึงข้อมูลจาก Data
    member_name = receipt_data['member_info'].get('Name', 'ไม่ระบุ')
    pay_date = receipt_data.get('payment_date', '')
    line_items = receipt_data.get('line_items', [])
    balance_summary = receipt_data.get('balance_summary', [])

    # --- 1. หัวกระดาษ ---
    elements.append(Paragraph("ใบเสร็จรับเงิน", pdf_styles['TitleStyle']))
    elements.append(Spacer(1, 0.8*cm)) 

    # --- 2. ข้อมูลลูกหนี้และวันที่ ---
    data_info = [
        [Paragraph(f"ชื่อลูกหนี้: <font face='{font_bold}'>{member_name}</font>", pdf_styles['NormalLeft']), ""],
        [Paragraph(f"วันที่ชำระ: {pay_date}", pdf_styles['NormalLeft']), ""]
    ]
    table_info = Table(data_info, colWidths=[12*cm, 4*cm]) 
    table_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),  
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5), 
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 0.5*cm))
    
    # --- 3. รายการที่ชำระ (Dynamic) ---
    elements.append(Paragraph("รายการที่ชำระ:", pdf_styles['BoldLeft']))
    elements.append(Spacer(1, 0.2*cm))

    items_data = []
    for item in line_items:
        clean_label = item['label'].replace("บัญชี บัญชี", "บัญชี")
        items_data.append([
            Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{clean_label}", pdf_styles['NormalLeft']),
            Paragraph(f"{item['amount']:,.2f} บาท", pdf_styles['NormalRight'])
        ])

    if items_data:
        table_items = Table(items_data, colWidths=[10*cm, 6*cm])
        table_items.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(table_items)

    # เส้นคั่น
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("-" * 85, pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 0.2*cm))

    # --- 4. สรุปยอดคงเหลือ (Dynamic) ---
    summary_data = []
    for bal in balance_summary:
        unit = bal.get('unit', 'บาท')
        summary_data.append([
            Paragraph(bal['label'] + ":", pdf_styles['NormalLeft']),
            Paragraph(f"<font face='{font_bold}'>{bal['amount']:,.2f} {unit}</font>", pdf_styles['BoldRight'])
        ])

    if summary_data:
        table_summary = Table(summary_data, colWidths=[10*cm, 6*cm])
        table_summary.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(table_summary)

    # เส้นคั่น
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("-" * 85, pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 1.5*cm))

    # --- 5. ลายเซ็น ---
    signature_table_data = [
        [Paragraph("________________________", pdf_styles['SignatureCenter']), Paragraph("________________________", pdf_styles['SignatureCenter'])],
        [Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้ชำระเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureCenter']), Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้รับเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureCenter'])]
    ]
    signature_table = Table(signature_table_data, colWidths=[8*cm, 8*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(signature_table)

    # สั่งให้ Platypus จัดเรียงและสร้างไฟล์ PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
