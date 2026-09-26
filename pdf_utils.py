import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm

# ========== ตั้งค่าฟอนต์และสไตล์ ==========
def setup_pdf_styles():
    thai_font = 'THSarabunNew'
    thai_font_bold = 'THSarabunNew-Bold'
    
    try:
        # โหลดตัวธรรมดา
        pdfmetrics.registerFont(TTFont('THSarabunNew', 'fonts/THSarabunNew.ttf'))
        # โหลดตัวหนา (ถ้าไม่มีใช้ตัวธรรมดาแทน)
        try:
            pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', 'fonts/THSarabunNew Bold.ttf'))
        except:
            thai_font_bold = 'THSarabunNew'
    except Exception as e:
        print(f"Font Load Error: {e}")
        try:
            pdfmetrics.registerFont(TTFont('Sarabun', 'fonts/Sarabun-Regular.ttf'))
            try:
                pdfmetrics.registerFont(TTFont('Sarabun-Bold', 'fonts/Sarabun-Bold.ttf'))
                thai_font_bold = 'Sarabun-Bold'
            except:
                thai_font_bold = 'Sarabun'
            thai_font = 'Sarabun'
        except:
            thai_font = 'Helvetica'
            thai_font_bold = 'Helvetica-Bold'
        
    styles = getSampleStyleSheet()
    style_definitions = [
        ('TitleStyle', thai_font_bold, 24, TA_CENTER, 20), 
        ('NormalLeft', thai_font, 16, TA_LEFT, 0),
        ('NormalRight', thai_font, 16, TA_RIGHT, 0),
        ('BoldLeft', thai_font_bold, 16, TA_LEFT, 0),
        ('SignatureCenter', thai_font, 16, TA_CENTER, 0), 
    ]
    
    for name, font, size, alignment, space_after in style_definitions:
        if name not in styles.byName: 
            styles.add(ParagraphStyle(
                name=name, fontName=font, fontSize=size, 
                alignment=alignment, leading=size + 4, spaceAfter=space_after
            ))
        else: 
            styles[name].fontName = font
            styles[name].fontSize = size
            styles[name].alignment = alignment
            styles[name].leading = size + 4
            styles[name].spaceAfter = space_after
            
    return styles, thai_font, thai_font_bold

# ========== ฟังก์ชันกรองคำ ==========
def format_clean_label(label):
    match = re.search(r'L-M-\d+-(\d+)-\d+', label)
    if match:
        acc_num = match.group(1)
        return f"ยอดหนี้คงเหลือ บัญชี {acc_num}"
    return label.replace("บัญชี บัญชี", "บัญชี")

# ========== สร้าง PDF ==========
def generate_receipt_pdf(receipt_data):
    pdf_styles, font_normal, font_bold = setup_pdf_styles()

    buffer = io.BytesIO()
    # ตั้งค่าหน้ากระดาษ A4 เว้นขอบกว้างๆ ตามรูป
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=2.5*cm, rightMargin=2.5*cm, 
                            topMargin=3.0*cm, bottomMargin=2.5*cm)
    elements = []

    # ดึงข้อมูลจากตะกร้า
    member_name = receipt_data['member_info'].get('Name', 'ไม่ระบุ')
    pay_date = receipt_data.get('payment_date', '')
    line_items = receipt_data.get('line_items', [])
    balance_summary = receipt_data.get('balance_summary', [])

    # 1. หัวใบเสร็จ
    elements.append(Paragraph("ใบเสร็จรับเงิน", pdf_styles['TitleStyle']))
    elements.append(Spacer(1, 1.2*cm)) 

    # 2. ข้อมูลลูกหนี้
    elements.append(Paragraph(f"ชื่อลูกหนี้: {member_name}", pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(f"วันที่ชำระ: {pay_date}", pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 0.8*cm))

    # 3. รายการที่ชำระ (ตั้งตารางให้ชิดขวา)
    data_items = []
    for item in line_items:
        clean_label = format_clean_label(item['label'])
        data_items.append([
            Paragraph(f"{clean_label}:", pdf_styles['NormalLeft']), 
            Paragraph(f"{item['amount']:,.2f} บาท", pdf_styles['NormalRight'])
        ])

    if data_items:
        table_items = Table(data_items, colWidths=[8*cm, 8*cm]) 
        table_items.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),  
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),  
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), 
        ]))
        elements.append(table_items)
    
    # เส้นคั่นที่ 1 
    elements.append(Spacer(1, 1.2*cm)) 
    elements.append(Paragraph("-", pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 1.2*cm)) 

    # 4. สรุปยอดคงเหลือ (ห้ามมีค่าปรับ)
    data_summary = []
    for bal in balance_summary:
        # 💡 ดักกรอง: ถ้ามีคำว่าค่าปรับ ให้ข้ามไปเลย ไม่ต้องพิมพ์
        if "ค่าปรับ" in bal['label']:
            continue
            
        unit = bal.get('unit', 'บาท')
        clean_label = format_clean_label(bal['label']) + ":"
        
        # ลบคำว่า (รวมค่าปรับ) ออกถ้ามีหลงมา
        clean_label = clean_label.replace(" (รวมค่าปรับ)", "")
        
        data_summary.append([
            Paragraph(clean_label, pdf_styles['NormalLeft']), 
            Paragraph(f"{bal['amount']:,.2f} {unit}", pdf_styles['NormalRight'])
        ])

    if data_summary:
        table_summary = Table(data_summary, colWidths=[8*cm, 8*cm]) 
        table_summary.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'), 
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), 
        ]))
        elements.append(table_summary)
    
    # เส้นคั่นที่ 2
    elements.append(Spacer(1, 1.2*cm)) 
    elements.append(Paragraph("-", pdf_styles['NormalLeft']))
    elements.append(Spacer(1, 2.5*cm)) 

    # 5. ลายเซ็น
    signature_table_data = [
        [Paragraph("___________________", pdf_styles['SignatureCenter']), Paragraph("___________________", pdf_styles['SignatureCenter'])],
        [Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้ชำระเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureCenter']), Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้รับเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureCenter'])]
    ]
    signature_table = Table(signature_table_data, colWidths=[8*cm, 8*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(signature_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
