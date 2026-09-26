import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm

# ========== PDF GENERATION SETUP (โครงสร้างเป๊ะตามต้นฉบับ) ==========
def setup_pdf_styles():
    thai_font_name_local = 'THSarabunNew'
    thai_font_name_bold_local = 'THSarabunNewBold'
    try:
        # ชี้โฟลเดอร์ fonts/ เผื่อกรณีใช้ THSarabunNew
        if 'THSarabunNew' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('THSarabunNew', 'fonts/THSarabunNew.ttf'))
        if 'THSarabunNewBold' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('THSarabunNewBold', 'fonts/THSarabunNew Bold.ttf'))
    except:
        # ระบบสำรอง: ถ้าไม่มี THSarabunNew ให้ดึง Sarabun ตัวเดิมที่พี่มีในโฟลเดอร์มาใช้
        try:
            thai_font_name_local = 'Sarabun'
            thai_font_name_bold_local = 'Sarabun-Bold'
            pdfmetrics.registerFont(TTFont('Sarabun', 'fonts/Sarabun-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Sarabun-Bold', 'fonts/Sarabun-Bold.ttf'))
        except:
            thai_font_name_local = 'Helvetica'
            thai_font_name_bold_local = 'Helvetica-Bold'
        
    styles = getSampleStyleSheet()
    style_definitions = [
        ('TitleStyle', thai_font_name_bold_local, 28, TA_CENTER, 20), 
        ('Heading1', thai_font_name_bold_local, 20, TA_LEFT, 6),     
        ('Normal', thai_font_name_local, 14, TA_LEFT, 0),            
        ('SignatureCenter', thai_font_name_local, 14, TA_CENTER, 0), 
        ('SignatureLeft', thai_font_name_local, 14, TA_LEFT, 0),    
        ('SignatureRight', thai_font_name_local, 14, TA_RIGHT, 0),   
        ('RightAlign', thai_font_name_local, 14, TA_RIGHT, 0),      
        ('BoldNormal', thai_font_name_bold_local, 14, TA_LEFT, 0),  
        ('RightAlignAmount', thai_font_name_bold_local, 14, TA_RIGHT, 0),
        ('NormalLeft', thai_font_name_local, 14, TA_LEFT, 0) 
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
        else: 
            styles[name].fontName = font
            styles[name].fontSize = size
            styles[name].alignment = alignment
            styles[name].leading = size + 2
            styles[name].spaceAfter = space_after
            
    return styles, thai_font_name_local, thai_font_name_bold_local

# ========== สร้าง PDF ==========
def generate_receipt_pdf(receipt_data):
    pdf_styles, thai_font_name, thai_font_name_bold = setup_pdf_styles()

    buffer = io.BytesIO()
    # ตั้งค่ากระดาษ margins เป๊ะตามโค้ดต้นฉบับ 2.5*cm
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=2.5*cm, rightMargin=2.5*cm, 
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    elements = []

    # ดึงตัวแปรข้อมูล
    member_name = receipt_data['member_info'].get('Name', 'ไม่ระบุ')
    pay_date = receipt_data.get('payment_date', '')
    line_items = receipt_data.get('line_items', [])
    balance_summary = receipt_data.get('balance_summary', [])

    # หัวใบเสร็จ
    elements.append(Paragraph("ใบเสร็จรับเงิน", pdf_styles['TitleStyle']))
    elements.append(Spacer(1, 0.8*cm)) 

    # --- ข้อมูลลูกหนี้และการชำระเงิน ---
    data_info = [
        [Paragraph(f"ชื่อลูกหนี้: <font face='{thai_font_name_bold}'>{member_name}</font>", pdf_styles['NormalLeft']), ""],
        [Paragraph(f"วันที่ชำระ: {pay_date}", pdf_styles['NormalLeft']), ""]
    ]
    
    # วนลูปเอารายการจ่ายเงินมาต่อท้ายให้เหมือนโค้ดต้นฉบับเป๊ะๆ
    for item in line_items:
        clean_label = item['label'].replace("บัญชี บัญชี", "บัญชี")
        data_info.append([
            Paragraph(f"{clean_label}:", pdf_styles['Normal']), 
            Paragraph(f"<font face='{thai_font_name_bold}'>{item['amount']:,.2f} บาท</font>", pdf_styles['RightAlignAmount'])
        ])

    table_info = Table(data_info, colWidths=[12*cm, 4*cm]) 
    table_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),  
        ('ALIGN', (1,2), (1,-1), 'RIGHT'),  # ปรับให้ตัวเลขชิดขวา
        ('SPAN', (0,0), (1,0)), 
        ('SPAN', (0,1), (1,1)), 
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5), 
    ]))
    elements.append(table_info)
    
    # เส้นคั่นกลาง 1
    elements.append(Spacer(1, 1.5*cm)) 
    elements.append(Paragraph("---", pdf_styles['Normal']))
    elements.append(Spacer(1, 1.5*cm)) 

    # --- สรุปยอดหนี้โดยรวม (ใช้ Table เพื่อจัดชิดขวา) ---
    data_summary = []
    for i, bal in enumerate(balance_summary):
        unit = bal.get('unit', 'บาท')
        label_text = bal['label'] + ":"
        
        # ทำให้บรรทัดสุดท้ายหนาเหมือน 'ยอดหนี้คงเหลือทั้งหมด (รวมค่าปรับ)' ในโค้ดต้นฉบับ
        if i == len(balance_summary) - 1:
            data_summary.append([
                Paragraph(label_text, pdf_styles['BoldNormal']), 
                Paragraph(f"<font face='{thai_font_name_bold}'>{bal['amount']:,.2f} {unit}</font>", pdf_styles['RightAlignAmount'])
            ])
        else:
            data_summary.append([
                Paragraph(label_text, pdf_styles['Normal']), 
                Paragraph(f"{bal['amount']:,.2f} {unit}", pdf_styles['RightAlignAmount'])
            ])

    if data_summary:
        table_summary = Table(data_summary, colWidths=[10*cm, 6*cm]) 
        table_summary.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'), 
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5), 
        ]))
        elements.append(table_summary)
    
    # เส้นคั่นกลาง 2
    elements.append(Spacer(1, 1.5*cm)) 
    elements.append(Paragraph("---", pdf_styles['Normal']))
    elements.append(Spacer(1, 1.0*cm)) 

    # --- ลายเซ็น: บรรทัดเดียวกัน ชิดซ้ายและขวา ---
    signature_table_data = [
        [Paragraph("___________________", pdf_styles['SignatureLeft']), Paragraph("___________________", pdf_styles['SignatureRight'])],
        [Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้ชำระเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureLeft']), Paragraph("(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ผู้รับเงิน&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", pdf_styles['SignatureRight'])]
    ]
    signature_table = Table(signature_table_data, colWidths=[8*cm, 8*cm]) # แบ่งครึ่งหน้ากระดาษ
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(signature_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
