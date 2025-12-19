"""
License Invoice PDF Generator using WeasyPrint
"""
import os
import io
import base64
import platform
import qrcode
from datetime import datetime

# Fix for macOS WeasyPrint - MUST run before importing weasyprint
if platform.system() == 'Darwin':
    # Add Homebrew lib paths to DYLD_FALLBACK_LIBRARY_PATH
    lib_paths = ['/opt/homebrew/lib', '/usr/local/lib', '/usr/lib']
    existing_path = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = ':'.join(lib_paths) + ':' + existing_path
    
    # Explicitly preload critical libraries that ctypes often misses
    try:
        from ctypes import CDLL
        # List of libraries to try preloading (order matters sometimes)
        libs = [
            '/opt/homebrew/lib/libgobject-2.0.0.dylib',
            '/opt/homebrew/lib/libpango-1.0.0.dylib',
            '/opt/homebrew/lib/libharfbuzz.0.dylib',
            '/opt/homebrew/lib/libfontconfig.1.dylib'
        ]
        for lib in libs:
            if os.path.exists(lib):
                CDLL(lib)
    except Exception as e:
        print(f"Warning: Failed to preload WeasyPrint dependencies: {e}")

from weasyprint import HTML, CSS

from core.config import (COMPANY_NAME, COMPANY_SUBTITLE, 
                         COMPANY_CONTACT_PHONE, COMPANY_CONTACT_SOCIAL)

class LicenseInvoiceGenerator:
    """Generate professional license invoices using WeasyPrint"""
    
    def __init__(self):
        self.font_family = "'Helvetica', 'Arial', sans-serif"
    
    def _generate_qr_b64(self, data):
        """Generate QR code base64 with Invoice Details"""
        try:
            # Construct QR content with requested details
            inv = data.get('invoice_number', 'N/A')
            email = data.get('email', 'N/A')
            renewal = data.get('renewal_reminder', 'N/A')
            
            qr_content = (f"Invoice: {inv}\n"
                          f"Email: {email}\n"
                          f"Renew: {renewal}")
            
            qr = qrcode.QRCode(box_size=4, border=1)
            qr.add_data(qr_content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
        except:
            return ""

    def generate_pdf(self, data, filename):
        """Generate PDF license invoice"""
        
        # A5 Page
        page_css = """
            @page {
                size: A5;
                margin: 0;
            }
        """
        
        # CSS Styling
        style = f"""
        <style>
            {page_css}
            body {{
                font-family: {self.font_family};
                font-size: 9pt;
                margin: 0;
                padding: 15mm;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .company-name {{
                font-size: 14pt;
                font-weight: bold;
                color: #000;
            }}
            .company-info {{
                font-size: 8pt;
                color: #555;
                margin-top: 2px;
            }}
            .invoice-title {{
                font-size: 16pt;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
                letter-spacing: 2px;
                color: #000;
            }}
            .columns {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .col {{
                width: 48%;
            }}
            .section-title {{
                font-size: 10pt;
                font-weight: bold;
                border-bottom: 2px solid #eee;
                padding-bottom: 5px;
                margin-bottom: 10px;
                color: #000;
            }}
            .row {{
                display: flex;
                margin-bottom: 4px;
            }}
            .label {{
                font-weight: bold;
                width: 80px;
                font-size: 9pt;
            }}
            .value {{
                flex: 1;
                font-size: 9pt;
            }}
            .full-width-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .full-width-table th, .full-width-table td {{
                padding: 8px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            .full-width-table th {{
                background-color: #f9f9f9;
                font-weight: bold;
            }}
            .amount-row {{
                display: flex;
                justify-content: flex-end;
                margin-top: 10px;
                font-size: 10pt;
            }}
            .license-key-box {{
                background-color: #f5f5f5;
                padding: 10px;
                font-family: monospace;
                font-size: 8pt;
                word-break: break-all;
                border-radius: 4px;
                border: 1px solid #ddd;
                margin: 10px 0;
            }}
            .footer {{
                text-align: center;
                font-size: 8pt;
                color: #777;
                margin-top: 30px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
            .qr-container {{
                text-align: center;
                margin-top: 20px;
            }}
            .terms {{
                font-size: 7pt;
                color: #666;
                margin-top: 5px;
            }}
        </style>
        """
        
        # Prepare Data
        inv_num = data.get('invoice_number', 'N/A')
        date_str = data.get('generated_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>{style}</head>
        <body>
            
            <div class="header">
                <div class="company-name">{COMPANY_NAME}</div>
                <div class="company-info">{COMPANY_SUBTITLE}</div>
                <div class="company-info">{COMPANY_CONTACT_PHONE}</div>
                <div class="company-info">{COMPANY_CONTACT_SOCIAL}</div>
            </div>
            
            <div class="invoice-title">LICENSE INVOICE</div>
            
            <!-- Details Columns -->
            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td style="width: 50%; vertical-align: top; padding-right: 10px;">
                        <div class="section-title">Invoice Details</div>
                        <div class="row"><div class="label">Invoice #:</div><div class="value">{inv_num}</div></div>
                        <div class="row"><div class="label">Date:</div><div class="value">{date_str}</div></div>
                        <div class="row"><div class="label">Type:</div><div class="value">{data.get('license_type', 'N/A')}</div></div>
                    </td>
                    <td style="width: 50%; vertical-align: top; padding-left: 10px;">
                        <div class="section-title">Customer Details</div>
                        <div class="row"><div class="label">Name:</div><div class="value">{data.get('customer_name', data.get('name', 'N/A'))}</div></div>
                        <div class="row"><div class="label">Email:</div><div class="value">{data.get('email') or 'N/A'}</div></div>
                        <div class="row"><div class="label">Phone:</div><div class="value">{data.get('phone') or 'N/A'}</div></div>
                    </td>
                </tr>
            </table>
            
            <div class="section-title">License Information</div>
            <table class="full-width-table">
                <tr>
                    <th>Hardware ID</th>
                    <td>{data.get('hwid', 'N/A')}</td>
                </tr>
                <tr>
                    <th>Expiry Date</th>
                    <td>{data.get('expiry_date', data.get('expiration_date', 'N/A'))}</td>
                </tr>
                <tr>
                    <th>Renewal Reminder</th>
                    <td>{data.get('renewal_reminder', 'N/A')}</td>
                </tr>
            </table>
            
            <div class="amount-row">
                <table style="width: 200px;">
                    <tr>
                        <td style="text-align: right; font-weight: bold;">License Fee:</td>
                        <td style="text-align: right;">{data.get('amount') or '0.00'}</td>
                    </tr>
                    <tr>
                        <td style="text-align: right; font-weight: bold;">Payment Method:</td>
                        <td style="text-align: right;">{data.get('payment_method', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            
 
            
            <div class="qr-container">
                <img src="data:image/png;base64,{self._generate_qr_b64(data)}" width="60" height="60">
            </div>
            
            <div class="footer">
                <div style="font-weight: bold; font-size: 9pt;">THANK YOU FOR YOUR PURCHASE!</div>
                <div class="terms">This license is hardware-locked and non-transferable.</div>
                <div class="terms">Please keep this invoice for your records.</div>
            </div>
            
        </body>
        </html>
        """
        
        # Write PDF
        HTML(string=html).write_pdf(filename)
        return filename
