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

from weasyprint import HTML, CSS # Added WeasyPrint
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class TicketReceiptGenerator:
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
            qr = qrcode.QRCode(box_size=10, border=0)
            qr.add_data(data)
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
        # WeasyPrint generally picks up system fonts well if Pango is configured. 
        # Including generic sans-serif is good practice.
        return "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"

    def generate_html(self, ticket_data):
        """Generate HTML content based on print format"""
        print_format = ticket_data.get('print_format', 'Standard A5')
        
        if 'Thermal' in print_format or 'Slip' in print_format:
            return self._generate_thermal_html(ticket_data, print_format)
        else:
            return self._generate_a5_html(ticket_data)

    def _generate_thermal_html(self, ticket_data, print_format):
        """Generate HTML for thermal printers (58mm/80mm)"""
        # WeasyPrint manages page size via CSS @page
        width_mm = 58 if "58mm" in print_format else 80
        font_family = self._get_font_family()
        
        # We define page size in CSS for WeasyPrint
        # margin: 0 to avoid headers
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
        </style>
        """

        # Data
        biz_name = (self.settings.business_name if self.settings and self.settings.business_name else "Repair Shop")
        biz_addr = (self.settings.address if self.settings and self.settings.address else "123 Tech Street")
        biz_phone = (self.settings.business_phone if self.settings and self.settings.business_phone else "(555) 012-3456")
        
        ticket_number = self._safe_get(ticket_data, 'ticket_number', 'N/A')
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>{style}</head>
        <body>
            <div class="header">{biz_name}</div>
            <div class="info">{biz_addr}</div>
            <div class="info">{self.lm.get('Common.tel', 'Tel')}: {biz_phone}</div>
            <div class="divider"></div>
            
            <div class="header" style="font-size: 11pt;">{self.lm.get('TicketReceipt.repair_ticket_caps', 'REPAIR TICKET')}</div>
            <br>
            
            <div class="item"><span class="bold">{self.lm.get('TicketReceipt.ticket_number', 'Ticket #')}:</span> {ticket_number}</div>
            <div class="item">{self.lm.get('Common.date', 'Date')}: {date_str}</div>
            <div class="item">{self.lm.get('TicketReceipt.priority', 'Priority')}: {self._safe_get(ticket_data, 'priority', 'Normal')}</div>
            <div class="item">{self.lm.get('TicketReceipt.deadline', 'Deadline')}: {self._safe_get(ticket_data, 'deadline', 'N/A')}</div>
            
            <br>
            <div class="section-title">{self.lm.get('TicketReceipt.customer_info', 'Customer Info')}:</div>
            <div class="item"><span class="bold">{self.lm.get('TicketReceipt.name', 'Name')}:</span> {self._safe_get(ticket_data, 'customer_name', 'N/A')}</div>
            <div class="item"><span class="bold">{self.lm.get('TicketReceipt.phone', 'Phone')}:</span> {self._safe_get(ticket_data, 'customer_phone', 'N/A')}</div>
            <div class="item"><span class="bold">{self.lm.get('TicketReceipt.location', 'Location')}:</span> {self._safe_get(ticket_data, 'customer_address', '-')}</div>
            
            <br>
            <div class="section-title">{self.lm.get('TicketReceipt.device_details', 'Device Details')}:</div>
            <div class="item">{self._safe_get(ticket_data, 'brand', '')} {self._safe_get(ticket_data, 'model', '')} ({self._safe_get(ticket_data, 'color')})</div>
            <div class="item">IMEI: {self._safe_get(ticket_data, 'imei')}</div>
            <div class="item"><span class="bold">{self.lm.get('TicketReceipt.passcode', 'Passcode')}:</span> {self._safe_get(ticket_data, 'passcode')}</div>
            
            <br>
            <div class="section-title">{self.lm.get('TicketReceipt.issue_details', 'Issue Details')}:</div>
            <div class="item">{self.lm.get('TicketReceipt.type', 'Type')}: {self._safe_get(ticket_data, 'issue_type')}</div>
            <div class="item">{self.lm.get('TicketReceipt.desc', 'Desc')}: {self._safe_get(ticket_data, 'description')}</div>
            
            <div class="divider"></div>
            
            <table class="fin-table">
        """
        
        est_cost = float(ticket_data.get('estimated_cost', 0))
        deposit = float(ticket_data.get('deposit_paid', 0))
        balance = est_cost - deposit
        
        if est_cost > 0:
            html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('TicketReceipt.est_cost_short', 'Est. Cost')}:</td><td class='fin-val'>{currency_formatter.format(est_cost)}</td></tr>"
        if deposit > 0:
            html += f"<tr class='fin-row'><td class='fin-label'>{self.lm.get('TicketReceipt.deposit', 'Deposit')}:</td><td class='fin-val'>{currency_formatter.format(deposit)}</td></tr>"
            
        html += f"<tr class='fin-row'><td class='fin-label' style='font-size: 11pt; font-weight: bold;'>{self.lm.get('TicketReceipt.balance', 'Balance')}:</td><td class='fin-val' style='font-size: 11pt;'>{currency_formatter.format(balance)}</td></tr>"
        
        html += """
            </table>
            <br>
            <div class="section-title">""" + self.lm.get('TicketReceipt.terms_conditions', 'Terms & Conditions') + """:</div>
        """
        
        terms = [
            self.lm.get('TicketReceipt.term1_short', 'All repairs guaranteed for 30 days.'),
            self.lm.get('TicketReceipt.term2_short', 'Storage fees apply after 30 days.'),
            self.lm.get('TicketReceipt.term3_short', 'Not responsible for data loss.')
        ]
        
        for term in terms:
            html += f"<div class='terms'>- {term}</div>"
            
        qr_data = self._safe_get(ticket_data, 'ticket_number', 'PREVIEW')
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

    def _generate_a5_html(self, ticket_data):
        """Generate HTML for A5 Corporate"""
        font_family = self._get_font_family()
        
        # Colors
        # Colors (Optimized for B&W / High Contrast)
        c_header = "#000000"
        c_sub = "#333333"
        c_blue = "#000000" # Was blue, now black for sharp B&W
        c_red = "#000000"  # Was red, now black (rely on bold for emphasis)
        c_bg_head = "#eeeeee" # Light grey background
        c_bg_fin = "#eeeeee"  # Light grey background
        c_line = "#000000"    # Solid black lines
        
        # WeasyPrint A5 Page Size
        page_css = """
            @page {
                size: A5;
                margin: 5mm;
            }
        """

        style = f"""
        <style>
            {page_css}
            body {{ font-family: {font_family}; font-size: 8pt; margin: 0; padding: 0.5cm; }}
            table {{ border-collapse: collapse; width: 100%; }}
            td {{ vertical-align: top; padding: 1px; }}
            .header-bg {{ background-color: {c_bg_head}; padding: 10px; }}
            .biz-name {{ font-size: 11pt; font-weight: bold; color: {c_header}; }}
            .biz-sub {{ font-size: 7pt; color: {c_sub}; }}
            .tkt-title {{ font-size: 9pt; font-weight: bold; color: {c_blue}; text-align: right; }}
            .tkt-id {{ font-size: 8pt; font-weight: bold; color: {c_red}; text-align: right; }}
            .tkt-meta {{ font-size: 7pt; color: {c_header}; text-align: right; }}
            .sect-head {{ font-size: 8pt; font-weight: bold; color: {c_header}; margin-bottom: 2px; }}
            .val {{ font-size: 8pt; color: black; }}
            .sep-line {{ border-bottom: 1px solid {c_line}; height: 1px; margin-bottom: 3px; }}
            .issue-box {{ border: 1px solid {c_line}; padding: 10px; margin-top: 5px; }}
            .footer-bg {{ background-color: {c_bg_fin}; padding: 10px; }}
            .fin-label {{ font-size: 7pt; color: {c_sub}; }}
            .fin-val {{ font-size: 8pt; font-weight: bold; text-align: right; }}
            .fin-total {{ font-size: 10pt; font-weight: bold; color: #000000; text-align: right; }}
            .terms {{ font-size: 6pt; color: {c_sub}; margin-top: 5px; line-height: 1.1; }}
        </style>
        """
        
        biz_name = (self.settings.business_name if self.settings else "WORLD LOCK MOBILE").upper()
        biz_addr = (self.settings.address if self.settings else "")
        biz_phone = (self.settings.business_phone if self.settings else "")
        
        ticket_number = self._safe_get(ticket_data, 'ticket_number', 'PREVIEW')
        
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
                        <div class="tkt-title">{self.lm.get('TicketReceipt.repair_ticket_caps', 'REPAIR TICKET')}</div>
                        <div class="tkt-id">{ticket_number}</div>
                        <div class="tkt-meta">{self.lm.get('Common.date', 'Date')}: {datetime.now().strftime('%Y-%m-%d')}</div>
                        <div class="tkt-meta">{self.lm.get('TicketReceipt.deadline', 'Due')}: {self._safe_get(ticket_data, 'deadline')}</div>
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
                        <div class="val">{self.lm.get('TicketReceipt.name', 'Name')}: <b>{self._safe_get(ticket_data, 'customer_name')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.phone', 'Phone')}: <b>{self._safe_get(ticket_data, 'customer_phone')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.email', 'Email')}: <b>{self._safe_get(ticket_data, 'customer_email')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.location_short', 'Loc')}: <b>{self._safe_get(ticket_data, 'customer_address')}</b></div>
                    </td>
                    <td width="50%">
                        <div class="sect-head">{self.lm.get('TicketReceipt.device_details_caps', 'DEVICE DETAILS')}</div>
                        <div class="sep-line"></div>
                        <div class="val">{self.lm.get('TicketReceipt.model', 'Model')}: <b>{self._safe_get(ticket_data, 'brand')} {self._safe_get(ticket_data, 'model')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.imei', 'IMEI')}: <b>{self._safe_get(ticket_data, 'imei')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.passcode_short', 'Pass')}: <b>{self._safe_get(ticket_data, 'passcode')}</b></div>
                        <div class="val">{self.lm.get('TicketReceipt.condition_short', 'Cond')}: <b>{self._safe_get(ticket_data, 'condition')}</b></div>
                    </td>
                </tr>
            </table>
            
            <!-- Issue -->
            <div class="sect-head" style="margin-top: 5px;">{self.lm.get('TicketReceipt.issue_details_caps', 'ISSUE DETAILS')}</div>
            <div class="issue-box">
                <div class="val"><b>{self.lm.get('TicketReceipt.type', 'Type')}:</b> <span style="color: {c_red}">{self._safe_get(ticket_data, 'issue_type')}</span></div>
                <div class="val"><b>{self.lm.get('TicketReceipt.accessories', 'Accessories')}:</b> {self._safe_get(ticket_data, 'accessories')}</div>
                <div class="val"><b>{self.lm.get('TicketReceipt.notes', 'Notes')}:</b> {self._safe_get(ticket_data, 'description')}</div>
                <br>
            </div>
            
            <br>
            
            <!-- Footer -->
            <table width="100%">
                <tr>
                    <td width="50%" style="padding-left: 20px;">
                        {self._get_qr_img(ticket_number)}
                    </td>
                    <td width="50%">
                        <div class="footer-bg">
                            <table width="100%">
                                {self._get_financial_row(ticket_data)}
                            </table>
                        </div>
                    </td>
                </tr>
            </table>
            
            <br>
             <div class="sect-head">{self.lm.get('TicketReceipt.terms_conditions_caps', 'TERMS & CONDITIONS')}:</div>
        """
        
        terms = [
             "- " + self.lm.get('TicketReceipt.term1', 'All repairs are guaranteed for 30 days. No warranty on water damage.'),
             "- " + self.lm.get('TicketReceipt.term2', 'Devices left over 30 days will be sold to cover costs.'),
             "- " + self.lm.get('TicketReceipt.term3', 'We are not responsible for any data loss.'),
             "- " + self.lm.get('TicketReceipt.term4', 'Physical damage / liquid damage voids warranty.')
        ]
        
        for t in terms:
            html += f"<div class='terms'>{t}</div>"
            
        html += f"""
            <br>
            <div class="sect-head" style="text-align: center;">{self.lm.get('TicketReceipt.thank_you', 'Thank you for choosing us!')}</div>
        </body></html>
        """
        
        return html

    def _get_qr_img(self, data):
        b64 = self._generate_qr_code_base64(data)
        if b64:
            return f'<img src="data:image/png;base64,{b64}" width="60" height="60">'
        return ""

    def _get_financial_row(self, ticket_data):
        est = float(ticket_data.get('estimated_cost', 0))
        dep = float(ticket_data.get('deposit_paid', 0))
        bal = est - dep
        
        return f"""
            <tr><td class='fin-label'>{self.lm.get('TicketReceipt.est_cost_short', 'Est. Cost')}:</td><td class='fin-val'>{currency_formatter.format(est)}</td></tr>
            <tr><td class='fin-label'>{self.lm.get('TicketReceipt.deposit', 'Deposit')}:</td><td class='fin-val'>-{currency_formatter.format(dep)}</td></tr>
            <tr><td colspan="2"><hr></td></tr>
            <tr><td class='fin-label' style="font-weight: bold;">{self.lm.get('TicketReceipt.balance_caps', 'BALANCE')}:</td><td class='fin-total'>{currency_formatter.format(bal)}</td></tr>
        """

    def preview_ticket(self, ticket_data):
        """Generate PDF and open system viewer"""
        try:
            # Use meaningful name for Preview title
            ticket_number = ticket_data.get('ticket_number', 'Ticket').replace('/', '-').replace('\\', '-')
            safe_filename = f"Ticket-{ticket_number}.pdf"
            filename = os.path.join(tempfile.gettempdir(), safe_filename)
            # temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            # filename = temp_file.name
            # temp_file.close()
            
            self._print_to_pdf(ticket_data, filename)
            
            if platform.system() == 'Darwin':
                subprocess.call(('open', filename))
            elif platform.system() == 'Windows':
                os.startfile(filename)
            else:
                subprocess.call(('xdg-open', filename))
        except Exception as e:
            print(f"Error generating preview: {e}")

        except Exception as e:
            print(f"Printing error: {e}")
            import traceback
            traceback.print_exc()

    def print_ticket(self, ticket_data):
        """Print ticket using QPrinter by printing the generated PDF"""
        try:
            # 1. Generate temp PDF with WeasyPrint
            # Use meaningful name for Preview title
            ticket_number = ticket_data.get('ticket_number', 'Ticket').replace('/', '-').replace('\\', '-')
            safe_filename = f"Ticket-{ticket_number}.pdf"
            filename = os.path.join(tempfile.gettempdir(), safe_filename)
            print(f"DEBUG: Generated PDF path: {filename}")
            
            self._print_to_pdf(ticket_data, filename)
            
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                 print("Error: PDF file creation failed or empty")
                 return
            
            # 2. Setup Printer
            printer = QPrinter(QPrinter.HighResolution)
            
            # 3. Configure Ticket Name
            ticket_number = ticket_data.get('ticket_number', 'Ticket')
            # Use safe filename for the suggested save name logic
            safe_basename = f"Ticket-{ticket_number.replace('/', '-').replace('\\', '-')}.pdf"
            printer.setDocName(safe_basename)
            printer.setDocName(safe_basename)
            # printer.setOutputFileName(safe_basename)
            
            # 4. Handle Dialog
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
                        elif platform.system() == 'Windows':
                             os.startfile(filename)
                        else:
                             subprocess.call(('xdg-open', filename))
                    return

                # CASE 2: PDF intent but no path (e.g. Cancelled save or proprietary dialog behavior)
                if not printer_name or "pdf" in printer_name.lower():
                     print("DEBUG: PDF/Empty printer selected but no output path. Opening in Preview.")
                     if platform.system() == 'Darwin':
                         subprocess.call(('open', filename))
                     elif platform.system() == 'Windows':
                         os.startfile(filename)
                     else:
                         subprocess.call(('xdg-open', filename))
                     return

                # CASE 3: Physical Printer
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
                        
                        log_print_debug(f"Attempting to print ticket to printer '{printer_name}'")
                        
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

    def _print_to_pdf(self, ticket_data, filename):
        """Render HTML to PDF file using WeasyPrint"""
        html_content = self.generate_html(ticket_data)
        
        # WeasyPrint generation
        # presentational_hints=True enables support for standard HTML attributes like width/height maps to CSS
        HTML(string=html_content).write_pdf(filename, presentational_hints=True)