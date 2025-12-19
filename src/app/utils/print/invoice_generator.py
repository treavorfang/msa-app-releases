import os
import shutil
import tempfile
import subprocess
import platform
import io
import base64
import qrcode
from datetime import datetime
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# === MACOS WEASYPRINT FIX ===
# Ensure WeasyPrint can find the libraries installed by Homebrew
if platform.system() == 'Darwin':
    # Add common Homebrew paths to fallback library path
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

from weasyprint import HTML, CSS
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class InvoiceGenerator:
    def __init__(self, parent=None, business_settings_service=None):
        self.parent = parent
        self.business_settings_service = business_settings_service
        self.settings = self._get_business_settings()
        self.lm = language_manager

    def _get_business_settings(self):
        if self.business_settings_service:
            return self.business_settings_service.get_settings()
        return None

    def _safe_get(self, data, key, default='-'):
        """Safely get value from dictionary"""
        val = data.get(key)
        if val is None:
            return default
        s_val = str(val).strip()
        if s_val.lower() == 'none' or not s_val:
            return default
        return s_val

    def _generate_qr_code_base64(self, data):
        """Generate QR code base64 string"""
        try:
            # Consistent QR content format with previous implementation
            qr_content = f"INVOICE:{data}"
            qr = qrcode.QRCode(box_size=10, border=0)
            qr.add_data(qr_content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            print(f"QR Generation Error: {e}")
            return ""

    def _get_font_family(self):
        """Return CSS font stack for Myanmar support"""
        return "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"

    def generate_html(self, data):
        """Generate HTML content based on print format"""
        print_format = data.get('print_format', 'Standard A5')
        
        if 'Thermal' in print_format or 'Slip' in print_format:
            return self._generate_thermal_html(data, print_format)
        else:
            return self._generate_a5_html(data)

    def _generate_thermal_html(self, data, print_format):
        """Generate HTML for thermal printers (58mm/80mm)"""
        width_mm = 58 if "58mm" in print_format else 80
        font_family = self._get_font_family()
        
        # WeasyPrint Page CSS
        page_css = f"""
            @page {{
                size: {width_mm}mm 200mm;
                margin: 5mm;
            }}
        """
        
        # Styles
        style = f"""
        <style>
            {page_css}
            body {{ font-family: {font_family}; font-size: 9pt; margin: 0; padding: 2mm; width: 100%; box-sizing: border-box; }}
            .header {{ text-align: center; font-weight: bold; font-size: 11pt; margin-bottom: 2px; }}
            .info {{ text-align: center; font-size: 8pt; color: #333; }}
            .divider {{ border-top: 1px dashed black; margin: 5px 0; }}
            .section-title {{ font-weight: bold; margin-top: 5px; font-size: 9pt; }}
            .item {{ font-size: 8pt; margin-bottom: 2px; }}
            .bold {{ font-weight: bold; }}
            .terms {{ font-size: 6pt; color: #444; margin-top: 5px; }}
            .footer {{ text-align: center; margin-top: 10px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td {{ vertical-align: top; }}
            .fin-row td {{ padding: 2px 0; }}
            .fin-label {{ text-align: right; padding-right: 5px; }}
            .fin-val {{ text-align: right; font-weight: bold; }}
            .fin-total {{ font-size: 10pt; font-weight: bold; color: #000000; text-align: right; }}
            .items-table {{ width: 100%; margin-top: 5px; }}
            .items-table td {{ padding: 2px 0; }}
        </style>
        """

        # Data
        biz_name = (self.settings.business_name if self.settings and self.settings.business_name else "Repair Shop")
        biz_addr = (self.settings.address if self.settings and self.settings.address else "123 Tech Street")
        biz_phone = (self.settings.business_phone if self.settings and self.settings.business_phone else "(555) 012-3456")
        
        inv_date = self._safe_get(data, 'date', datetime.now().strftime("%Y-%m-%d"))
        inv_num = self._safe_get(data, 'invoice_number')
        cust_name = self._safe_get(data, 'customer_name')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>{style}</head>
        <body>
            <div class="header">{biz_name}</div>
            <div class="info">{biz_addr}</div>
            <div class="info">{self.lm.get('Common.tel', 'Tel')}: {biz_phone}</div>
            <div class="divider"></div>
            
            <div class="header" style="font-size: 11pt;">{self.lm.get('Invoices.invoice_title_caps', 'INVOICE')}</div>
            <br>
            
            <div class="item"><span class="bold">{self.lm.get('Invoices.invoice_number', 'Inv #')}:</span> {inv_num}</div>
            <div class="item">{self.lm.get('Common.date', 'Date')}: {inv_date}</div>
            <div class="item">{self.lm.get('Invoices.customer', 'Cust')}: {cust_name}</div>
            
            <div class="divider"></div>
            
            <!-- Items -->
            <table class="items-table">
        """
        
        hide_prices = data.get('hide_item_prices', False)
        
        for item in data.get('items', []):
            desc = item.get('description', 'Item')
            qty = item.get('quantity', 0)
            
            html += f"<tr><td colspan='2' class='bold'>{desc}</td></tr>"
            
            if hide_prices:
                 html += f"<tr><td colspan='2'>x {qty}</td></tr>"
            else:
                 price = item.get('unit_price', 0)
                 total = item.get('total', 0)
                 html += f"""
                 <tr>
                    <td>{qty} x {currency_formatter.format(price)}</td>
                    <td style='text-align: right;'>{currency_formatter.format(total)}</td>
                 </tr>
                 """
            html += "<tr><td colspan='2' style='height: 5px;'></td></tr>" # Spacer
            
        html += "</table><div class='divider'></div><table class='fin-table'>"
        
        if not hide_prices:
            subtotal = data.get('subtotal', 0.0)
            tax = data.get('tax', 0.0)
            discount = data.get('discount', 0.0)
            total = data.get('total', 0.0)
            
            if tax > 0 or discount > 0:
                 html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('Invoices.subtotal', 'Sub')}:</td><td class='fin-val'>{currency_formatter.format(subtotal)}</td></tr>"
            if tax > 0:
                 html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('Invoices.tax', 'Tax')}:</td><td class='fin-val'>{currency_formatter.format(tax)}</td></tr>"
            if discount > 0:
                 html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('Invoices.discount', 'Disc')}:</td><td class='fin-val'>-{currency_formatter.format(discount)}</td></tr>"
            
            html += f"<tr class='fin-row'><td class='fin-label' style='font-size: 11pt; font-weight: bold;'>{self.lm.get('Invoices.total_caps', 'TOTAL')}:</td><td class='fin-val' style='font-size: 11pt;'>{currency_formatter.format(total)}</td></tr>"
            
            paid = data.get('amount_paid', 0.0)
            deposit = data.get('deposit_paid', 0.0)
            
            if deposit > 0:
                html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('Invoices.deposit', 'Deposit')}:</td><td class='fin-val'>({currency_formatter.format(deposit)})</td></tr>"
            if paid > 0:
                html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('Invoices.paid', 'Paid')}:</td><td class='fin-val'>({currency_formatter.format(paid)})</td></tr>"
                
            bal = total - deposit - paid
            label = "CHANGE" if bal <= 0 else "BALANCE"
            html += f"<tr class='fin-row'><td colspan='2'><hr></td></tr>"
            html += f"<tr><td class='fin-label' style='font-weight: bold;'>{label}:</td><td class='fin-total'>{currency_formatter.format(abs(bal))}</td></tr>"

        html += """
            </table>
            <div class="divider"></div>
            <div class="section-title">""" + self.lm.get('TicketReceipt.terms_conditions', 'Terms & Conditions') + """:</div>
            <div class="terms">
                """ + "".join([f"<div>- {line.strip()}</div>" for line in (self.settings.invoice_terms or "").split('\n') if line.strip()]) + (f"<div>- {self.lm.get('Invoices.footer_note', 'Please keep this invoice for warranty purposes.')}</div>" if not self.settings or not self.settings.invoice_terms else "") + """
            </div>
        """
        
        qr_data = inv_num
        qr_b64 = self._generate_qr_code_base64(qr_data)
        
        if qr_b64:
             html += f"""
             <br>
             <div style="text-align: center;">
                 <img src="data:image/png;base64,{qr_b64}" width="60" height="60">
             </div>
             """
             
        html += f"""
            <div class="footer">{self.lm.get('Common.thank_you_excl', 'Thank You!')}</div>
        </body>
        </html>
        """
        return html

    def _generate_a5_html(self, data):
        """Generate HTML for A5 Corporate"""
        font_family = self._get_font_family()
        
        # Colors (Optimized for B&W / High Contrast)
        c_header = "#000000"
        c_sub = "#333333"
        c_blue = "#000000" 
        c_red = "#000000"
        c_bg_head = "#eeeeee" 
        c_bg_fin = "#eeeeee"
        c_line = "#000000"
        
        # WeasyPrint A5 CSS
        page_css = """
            @page {
                size: A5;
                margin: 0;
            }
        """
        
        # Reduced Layout for A5 Fit
        style = f"""
        <style>
            {page_css}
            body {{ font-family: {font_family}; font-size: 8pt; margin: 0; padding: 0.5cm; }}
            table {{ border-collapse: collapse; width: 100%; }}
            td {{ vertical-align: top; padding: 1px; }}
            .header-bg {{ background-color: {c_bg_head}; padding: 10px; }}
            .biz-name {{ font-size: 11pt; font-weight: bold; color: {c_header}; }}
            .biz-sub {{ font-size: 7pt; color: {c_sub}; }}
            .doc-title {{ font-size: 9pt; font-weight: bold; color: {c_blue}; text-align: right; }}
            .doc-id {{ font-size: 8pt; font-weight: bold; color: {c_red}; text-align: right; }}
            .meta {{ font-size: 7pt; color: {c_header}; text-align: right; }}
            .sect-head {{ font-size: 8pt; font-weight: bold; color: {c_header}; margin-bottom: 2px; }}
            .val {{ font-size: 8pt; color: black; }}
            .sep-line {{ border-bottom: 1px solid {c_line}; height: 1px; margin-bottom: 3px; }}
            .footer-bg {{ background-color: {c_bg_fin}; padding: 10px; }}
            .fin-label {{ font-size: 7pt; color: {c_sub}; }}
            .fin-val {{ font-size: 8pt; font-weight: bold; text-align: right; }}
            .fin-total {{ font-size: 10pt; font-weight: bold; color: #000000; text-align: right; }}
            .terms {{ font-size: 6pt; color: {c_sub}; margin-top: 1px; }}
            .items-header {{ background-color: {c_header}; color: white; font-weight: bold; font-size: 7pt; text-align: center; padding: 3px; }}
            .items-cell {{ border: 1px solid {c_line}; font-size: 7pt; padding: 3px; vertical-align: middle; }}
            .items-num {{ border: 1px solid {c_line}; font-size: 7pt; padding: 3px; vertical-align: middle; text-align: right; }}
        </style>
        """
        
        biz_name = (self.settings.business_name if self.settings else "WORLD LOCK MOBILE").upper()
        biz_addr = (self.settings.address if self.settings else "")
        biz_phone = (self.settings.business_phone if self.settings else "")
        
        inv_date = self._safe_get(data, 'date', datetime.now().strftime("%Y-%m-%d"))
        inv_num = self._safe_get(data, 'invoice_number')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>{style}</head>
        <body>
            <!-- Header -->
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="60%" class="header-bg">
                        <div class="biz-name">{biz_name}</div>
                        <div class="biz-sub">{biz_addr}</div>
                        <div class="biz-sub">{biz_phone}</div>
                    </td>
                    <td width="40%" class="header-bg" style="text-align: right;">
                        <div class="doc-title">{self.lm.get('Invoices.invoice_title_caps', 'INVOICE')}</div>
                        <div class="doc-id">{inv_num}</div>
                        <div class="meta">{self.lm.get('Common.date', 'Date')}: {inv_date}</div>
                        <div class="meta">{self.lm.get('Invoices.ticket_number', 'Ticket #')}: {self._safe_get(data, 'ticket_number')}</div>
                    </td>
                </tr>
            </table>
            
            <br>
            
            <!-- Customer & Device -->
            <table width="100%" cellpadding="0" cellspacing="5">
                <tr>
                    <td width="50%">
                        <div class="sect-head">{self.lm.get('TicketReceipt.customer_details_caps', 'CUSTOMER DETAILS')}</div>
                        <div class="sep-line"></div>
                        <div class="val">{self.lm.get('TicketReceipt.name', 'Name')}: <b>{self._safe_get(data, 'customer_name')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.phone', 'Phone')}: <b>{self._safe_get(data, 'customer_phone')}</b></div>
                    </td>
                    <td width="50%">
                        <div class="sect-head">{self.lm.get('TicketReceipt.device_details_caps', 'DEVICE DETAILS')}</div>
                        <div class="sep-line"></div>
                        <div class="val">{self.lm.get('TicketReceipt.model', 'Model')}: <b>{self._safe_get(data, 'device')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.issue', 'Issue')}: <b>{self._safe_get(data, 'issue')}</b></div>
                    </td>
                </tr>
            </table>
            
            <br>
            
            <!-- Items -->
            <div class="sect-head">{self.lm.get('Invoices.items', 'LINE ITEMS')}</div>
            <div class="sep-line"></div>
            
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 3px;">
        """
        
        hide_prices = data.get('hide_item_prices', False)
        
        # Headers
        html += "<tr>"
        html += f"<td class='items-header' width='5%'>#</td>"
        html += f"<td class='items-header' width='50%' style='text-align: left;'>{self.lm.get('Invoices.description', 'Description')}</td>"
        html += f"<td class='items-header' width='10%'>{self.lm.get('Invoices.qty', 'Qty')}</td>"
        if not hide_prices:
             html += f"<td class='items-header' width='15%'>{self.lm.get('Invoices.price', 'Price')}</td>"
             html += f"<td class='items-header' width='20%'>{self.lm.get('Invoices.total', 'Total')}</td>"
        html += "</tr>"
        
        # Rows
        for i, item in enumerate(data.get('items', []), 1):
            desc = item.get('description', '')
            qty = item.get('quantity', 0)
            
            html += f"<tr><td class='items-cell' style='text-align: center;'>{i}</td>"
            html += f"<td class='items-cell'>{desc}</td>"
            html += f"<td class='items-cell' style='text-align: center;'>{qty}</td>"
            
            if not hide_prices:
                price = currency_formatter.format(item.get('unit_price', 0))
                total = currency_formatter.format(item.get('total', 0))
                html += f"<td class='items-num'>{price}</td>"
                html += f"<td class='items-num'>{total}</td>"
            html += "</tr>"
            
        html += """
            </table>
            <br><br>
            
            <!-- Footer -->
            <table width="100%">
                <tr>
                    <td width="50%" style="padding-left: 20px;">
                        """ + self._get_qr_img(inv_num) + """
                    </td>
                    <td width="50%">
                        <div class="footer-bg">
                            <table width="100%">
                                """ + self._get_financial_row(data, hide_prices) + """
                            </table>
                        </div>
                    </td>
                </tr>
            </table>
            
            <br>
             <div class="sect-head">{self.lm.get('TicketReceipt.terms_conditions_caps', 'TERMS & CONDITIONS')}:</div>
        """
        
        if self.settings and self.settings.invoice_terms:
            for t in self.settings.invoice_terms.split('\n'):
                if t.strip():
                    html += f"<div class='terms'>- {t.strip()}</div>"
        else:
            terms = [
                 "- " + self.lm.get('Invoices.term_1', 'All repairs are guaranteed for 30 days from completion date'),
                 "- " + self.lm.get('Invoices.term_2', 'Devices not collected within 30 days may incur storage fees'),
                 "- " + self.lm.get('Invoices.term_3', 'Payment is due upon receipt of this invoice')
            ]
            for t in terms:
                html += f"<div class='terms'>{t}</div>"
            
        html += f"""
            <br>
            <div class="sect-head" style="text-align: center;">{self.lm.get('Invoices.thank_you', 'Thank you for your business!')}</div>
        </body></html>
        """
        
        return html

    def _get_qr_img(self, data):
        b64 = self._generate_qr_code_base64(data)
        if b64:
            return f'<img src="data:image/png;base64,{b64}" width="60" height="60">'
        return ""

    def _get_financial_row(self, data, hide_prices):
        if hide_prices:
            return ""
            
        subtotal = data.get('subtotal', 0.0)
        tax = data.get('tax', 0.0)
        discount = data.get('discount', 0.0)
        total = data.get('total', 0.0)
        paid = data.get('amount_paid', 0.0)
        deposit = data.get('deposit_paid', 0.0)
        
        html = ""
        if tax > 0 or discount > 0:
             html += f"<tr><td class='fin-label'>{self.lm.get('Invoices.subtotal', 'Subtotal')}:</td><td class='fin-val'>{currency_formatter.format(subtotal)}</td></tr>"
        if tax > 0:
             html += f"<tr><td class='fin-label'>{self.lm.get('Invoices.tax', 'Tax')}:</td><td class='fin-val'>{currency_formatter.format(tax)}</td></tr>"
        if discount > 0:
             html += f"<tr><td class='fin-label'>{self.lm.get('Invoices.discount', 'Discount')}:</td><td class='fin-val'>-{currency_formatter.format(discount)}</td></tr>"
             
        html += f"<tr><td class='fin-label' style='font-size: 10pt; font-weight: bold;'>{self.lm.get('Invoices.total_caps', 'TOTAL')}:</td><td class='fin-total'>{currency_formatter.format(total)}</td></tr>"
        
        if deposit > 0:
            html += f"<tr><td class='fin-label'>{self.lm.get('Invoices.deposit', 'Deposit')}:</td><td class='fin-val'>({currency_formatter.format(deposit)})</td></tr>"
        if paid > 0:
            html += f"<tr><td class='fin-label'>{self.lm.get('Invoices.paid', 'Paid')}:</td><td class='fin-val'>({currency_formatter.format(paid)})</td></tr>"
            
        bal = total - deposit - paid
        label = "CHANGE" if bal <= 0 else "BALANCE"
        html += f"<tr><td colspan='2'><hr></td></tr>"
        html += f"<tr><td class='fin-label' style='font-weight: bold;'>{label}:</td><td class='fin-total'>{currency_formatter.format(abs(bal))}</td></tr>"
        return html

    def preview_invoice(self, data):
        """Generate PDF and open system viewer"""
        try:
            # Use meaningful name
            num = data.get('invoice_number', 'Invoice').replace('/', '-').replace('\\', '-')
            safe_filename = f"Invoice-{num}.pdf"
            filename = os.path.join(tempfile.gettempdir(), safe_filename)
            # temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            # filename = temp_file.name
            # temp_file.close()
            
            self._print_to_pdf(data, filename)
            
            if platform.system() == 'Darwin':
                subprocess.call(('open', filename))
            elif platform.system() == 'Windows':
                os.startfile(filename)
            else:
                subprocess.call(('xdg-open', filename))
        except Exception as e:
            print(f"Error generating preview: {e}")

    def print_invoice(self, data):
        """Print invoice with QPrinter"""
        try:
            # Use meaningful name
            num = data.get('invoice_number', 'Invoice').replace('/', '-').replace('\\', '-')
            safe_filename = f"Invoice-{num}.pdf"
            filename = os.path.join(tempfile.gettempdir(), safe_filename)
            # temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            # filename = temp_file.name
            # temp_file.close()
            
            self._print_to_pdf(data, filename)
            
            printer = QPrinter(QPrinter.HighResolution)
            num = data.get('invoice_number', 'Invoice')
            
            # Suggest filename to dialog
            safe_basename = f"Invoice-{num.replace('/', '-').replace('\\', '-')}.pdf"
            printer.setDocName(safe_basename)
            printer.setDocName(safe_basename)
            # printer.setOutputFileName(safe_basename) # Do NOT set this, or it acts like "Print to File" is checked
            
            dialog = QPrintDialog(printer, self.parent)
            if dialog.exec():
                printer_name = printer.printerName()
                output_file = printer.outputFileName()
                print(f"DEBUG: Selected Printer: '{printer_name}'")
                print(f"DEBUG: Output File: '{output_file}'")

                # CASE 1: Save as PDF (Native Dialog yielded a path)
                if output_file:
                    print(f"DEBUG: Save to PDF detected. Copying to {output_file}")
                    try:
                        shutil.copy(filename, output_file)
                        print("DEBUG: File saved successfully.")
                    except Exception as e:
                        print(f"Error copying PDF: {e}")
                        # Fallback to preview if copy fails
                        if platform.system() == 'Darwin':
                             subprocess.call(('open', filename))
                    return

                # CASE 2: PDF intent but no path
                if not printer_name or "pdf" in printer_name.lower():
                     print("DEBUG: PDF/Empty printer selected. Opening in Preview for saving.")
                     if platform.system() == 'Darwin':
                         subprocess.call(('open', filename))
                     elif platform.system() == 'Windows':
                         os.startfile(filename)
                     else:
                         subprocess.call(('xdg-open', filename))
                     return

                if platform.system() == 'Darwin' or platform.system() == 'Linux':
                     cmd = ['lp', '-d', printer_name, filename]
                     print(f"DEBUG: Running command: {cmd}")
                     res = subprocess.run(cmd, capture_output=True, text=True)
                     if res.returncode != 0:
                         print(f"Error printing: {res.stderr}")
                     else:
                         print(f"Print job submitted: {res.stdout}")

                elif platform.system() == 'Windows':
                     # Try to print using SumatraPDF (Silent & Accurate)
                     try:
                        from config.config import get_sumatra_path, log_print_debug
                        
                        log_print_debug(f"Attempting to print invoice {num} to printer '{printer_name}'")
                        
                        sumatra_path = get_sumatra_path()
                        if not sumatra_path:
                             raise FileNotFoundError("SumatraPDF path not found via config")
                             
                        log_print_debug(f"Found SumatraPDF at: {sumatra_path}")
                        
                        printer_name_arg = f'{printer_name}'
                        
                        # SumatraPDF command: SumatraPDF.exe -print-to "Printer Name" "file.pdf"
                        cmd = [
                            sumatra_path,
                            "-print-to", printer_name_arg,
                            "-silent",
                            filename
                        ]
                        
                        log_print_debug(f"Executing command: {cmd}")
                        print(f"DEBUG: Attempting SumatraPDF: {cmd}")
                        
                        # We use subprocess.run. If SumatraPDF is missing, this will raise FileNotFoundError
                        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                        log_print_debug(f"Command successful. Stdout: {result.stdout}")
                        print("DEBUG: SumatraPDF print command successful")
                        
                     except Exception as sumatra_e:
                        from config.config import log_print_debug
                        log_print_debug(f"SumatraPDF failed: {sumatra_e}")
                        print(f"SumatraPDF failed or not found ({sumatra_e}). Falling back to default handler...")
                        
                        # Fallback: Try PowerShell PrintTo (Standard method)
                        try:
                            printer_name_arg = f'"{printer_name}"'
                            cmd = [
                                "powershell", 
                                "-Command", 
                                f"Start-Process -FilePath '{filename}' -Verb PrintTo -ArgumentList {printer_name_arg} -PassThru | Wait-Process"
                            ]
                            log_print_debug(f"Fallback to PowerShell: {cmd}")
                            print(f"DEBUG: Attempting Windows PrintTo: {cmd}")
                            subprocess.run(cmd, check=True)
                        except Exception as win_e:
                            log_print_debug(f"PowerShell failed: {win_e}")
                            print(f"Windows PrintTo failed ({win_e}), falling back to simple print...")
                            os.startfile(filename, "print")
                
        except Exception as e:
            print(f"Printing error: {e}")
            import traceback
            traceback.print_exc()

    def _print_to_pdf(self, data, filename):
        """Render HTML to PDF file"""
        html = self.generate_html(data)
        HTML(string=html).write_pdf(filename, presentational_hints=True)