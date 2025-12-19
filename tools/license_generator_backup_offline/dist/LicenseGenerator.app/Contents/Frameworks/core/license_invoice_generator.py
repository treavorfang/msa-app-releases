"""
License Invoice PDF Generator using ReportLab
Similar to MSA app's invoice generator
"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget


class LicenseInvoiceGenerator:
    """Generate professional license invoices using ReportLab"""
    
    def __init__(self):
        self.font_name = 'Helvetica'
        self.font_name_bold = 'Helvetica-Bold'
    
    def _generate_qr_code(self, data, size=25*mm):
        """Generate QR code with license key"""
        try:
            license_key = data.get('license_key', 'N/A')[:50]  # Truncate for QR
            qr_content = f"LICENSE:{license_key}"
            
            qrw = QrCodeWidget(qr_content)
            bounds = qrw.getBounds()
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            drawing = Drawing(size, size, transform=[size/width,0,0,size/height,0,0])
            drawing.add(qrw)
            return drawing
        except:
            return Drawing(size, size)
    
    def generate_pdf(self, data, filename):
        """Generate PDF license invoice"""
        # A5 Layout with same margins as MSA invoices
        doc = SimpleDocTemplate(
            filename,
            pagesize=A5,
            rightMargin=16*mm,
            leftMargin=16*mm,
            topMargin=8*mm,
            bottomMargin=8*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Calculate available width
        available_width = A5[0] - (16*mm + 16*mm)
        
        # Custom Styles
        styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=2,
            fontName=self.font_name_bold
        ))
        
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Heading2'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=0,
            fontName=self.font_name_bold
        ))
        
        styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            fontName=self.font_name,
            leading=8
        ))
        
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading3'],
            fontSize=8,
            textColor=colors.black,
            spaceAfter=1,
            fontName=self.font_name_bold
        ))
        
        styles.add(ParagraphStyle(
            name='Normal9',
            parent=styles['Normal'],
            fontSize=9,
            fontName=self.font_name,
            leading=10
        ))
        
        styles.add(ParagraphStyle(
            name='Bold9',
            parent=styles['Normal'],
            fontSize=9,
            fontName=self.font_name_bold,
            leading=10
        ))
        
        styles.add(ParagraphStyle(
            name='FooterText',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            textColor=colors.gray,
            leading=7
        ))
        
        # --- Header ---
        story.append(Paragraph("World Lock / Studio Tai", styles['CompanyName']))
        story.append(Paragraph("Mobile Service & Photography", styles['CompanyInfo']))
        story.append(Paragraph("📱 +959259282400 | +95968098642", styles['CompanyInfo']))
        story.append(Paragraph("💬 WhatsApp/Telegram: +959259282400", styles['CompanyInfo']))
        story.append(Spacer(1, 2*mm))
        
        # --- Invoice Title ---
        story.append(Paragraph("LICENSE INVOICE", styles['InvoiceTitle']))
        story.append(Spacer(1, 2*mm))
        
        # --- Invoice Info & Customer Info (Side by Side) ---
        invoice_number = data.get('invoice_number', 'N/A')
        date = data.get('generated_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        customer_name = data.get('customer_name', 'N/A')
        customer_email = data.get('email', 'N/A') if data.get('email') else 'N/A'
        customer_phone = data.get('phone', 'N/A') if data.get('phone') else 'N/A'
        customer_city = data.get('city', 'N/A') if data.get('city') else 'N/A'
        
        # Invoice Details
        invoice_info_data = [
            [Paragraph("<b>Invoice #:</b>", styles['Bold9']), invoice_number],
            [Paragraph("<b>Date:</b>", styles['Bold9']), date],
            [Paragraph("<b>License Type:</b>", styles['Bold9']), data.get('license_type', 'N/A')]
        ]
        
        # Customer Details
        customer_info_data = [
            [Paragraph("<b>Customer:</b>", styles['Bold9']), customer_name],
            [Paragraph("<b>Email:</b>", styles['Bold9']), customer_email],
            [Paragraph("<b>Phone:</b>", styles['Bold9']), customer_phone],
            [Paragraph("<b>City:</b>", styles['Bold9']), customer_city]
        ]
        
        invoice_info_table = Table(invoice_info_data, colWidths=[25*mm, available_width/2-25*mm])
        invoice_info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        customer_info_table = Table(customer_info_data, colWidths=[25*mm, available_width/2-25*mm])
        customer_info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Combine into side-by-side layout
        info_table_data = [
            [
                Paragraph("<b>Invoice Details</b>", styles['SectionTitle']),
                Paragraph("<b>Customer Details</b>", styles['SectionTitle'])
            ],
            [invoice_info_table, customer_info_table]
        ]
        
        info_table = Table(info_table_data, colWidths=[available_width/2, available_width/2])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 2*mm))
        
        # --- License Details ---
        license_data = [
            [Paragraph("<b>License Information</b>", styles['SectionTitle'])],
            [Paragraph(f"<b>Hardware ID:</b> {data.get('hwid', 'N/A')}", styles['Normal9'])],
            [Paragraph(f"<b>Expiry Date:</b> {data.get('expiry_date', 'N/A')}", styles['Normal9'])],
            [Paragraph(f"<b>Renewal Reminder:</b> {data.get('renewal_reminder', 'N/A')}", styles['Normal9'])]
        ]
        
        license_table = Table(license_data, colWidths=[available_width])
        license_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(license_table)
        story.append(Spacer(1, 2*mm))
        
        # --- Payment Information ---
        amount = data.get('amount', '0.00')
        if not amount or amount == '':
            amount = '0.00'
        payment_method = data.get('payment_method', 'N/A')
        payment_status = data.get('payment_status', 'N/A')
        
        payment_data = [
            ["License Fee:", amount if amount != '0.00' else 'N/A'],
            ["Payment Method:", payment_method],
            ["Payment Status:", payment_status]
        ]
        
        payment_table = Table(payment_data, colWidths=[35*mm, 25*mm])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (0,-1), self.font_name_bold),
            ('FONTNAME', (-1,0), (-1,-1), self.font_name),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            # Bold last row
            ('FONTNAME', (0, -1), (-1, -1), self.font_name_bold),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
        ]))
        
        payment_table.hAlign = 'RIGHT'
        story.append(payment_table)
        story.append(Spacer(1, 3*mm))
        
        # --- License Key ---
        story.append(Paragraph("<b>License Key</b>", styles['SectionTitle']))
        story.append(Spacer(1, 1*mm))
        
        license_key = data.get('license_key', 'N/A')
        # Split long license key into multiple lines
        key_style = ParagraphStyle(
            'LicenseKey',
            parent=styles['Normal'],
            fontSize=7,
            fontName='Courier',
            leading=9,
            wordWrap='CJK'
        )
        story.append(Paragraph(license_key, key_style))
        story.append(Spacer(1, 2*mm))
        
        # --- Notes ---
        notes = data.get('notes', '')
        if notes:
            story.append(Paragraph(f"<b>Notes:</b> {notes}", styles['Normal9']))
            story.append(Spacer(1, 2*mm))
        
        # --- Footer ---
        story.append(Paragraph("THANK YOU FOR YOUR PURCHASE!", 
            ParagraphStyle('FooterTitle', parent=styles['Normal'], alignment=TA_CENTER, 
                          fontName=self.font_name_bold, fontSize=8, spaceAfter=0)))
        
        story.append(Paragraph("This license is hardware-locked and non-transferable.",
            styles['FooterText']))
        story.append(Paragraph("Please keep this invoice for your records.",
            styles['FooterText']))
        
        story.append(Spacer(1, 2*mm))
        
        # --- QR Code ---
        qr_table_data = [[self._generate_qr_code(data, size=25*mm)]]
        qr_table = Table(qr_table_data, colWidths=[available_width])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(qr_table)
        
        # Build PDF
        doc.build(story)
        return filename
