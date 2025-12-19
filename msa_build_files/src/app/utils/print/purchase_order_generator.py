import os
import shutil
import tempfile
import subprocess
import platform
from datetime import datetime
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import QApplication

# Fix for macOS WeasyPrint GObject issue
if platform.system() == 'Darwin':
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib'

from weasyprint import HTML, CSS
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class PurchaseOrderGenerator:
    def __init__(self, parent=None, business_settings_service=None):
        self.parent = parent
        self.business_settings_service = business_settings_service
        self.lm = language_manager
        self.cf = currency_formatter
        self.settings = self._get_business_settings()

    def _get_business_settings(self):
        if self.business_settings_service:
            return self.business_settings_service.get_settings()
        return None
    
    def _get_font_family(self):
        return "'Inter', 'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"

    def generate_html(self, data):
        """Generate HTML content for Purchase Order"""
        
        # --- Localization ---
        L = lambda key, default: self.lm.get(key, default)
        
        title = L("PurchaseOrders.invoice_title_caps", "PURCHASE ORDER") # Reusing invoice title or "Purchase Order"
        if title == "PURCHASE ORDER": # Fallback if key missing
             title = L("Inventory.purchase_order_details", "PURCHASE ORDER").upper()
             
        lbl_po_number = L("Inventory.po_number", "PO Number")
        lbl_date = L("Common.date", "Date")
        lbl_expected = L("Inventory.expected_delivery", "Expected Delivery")
        lbl_supplier = L("Inventory.supplier", "Supplier")
        lbl_bill_to = L("Inventory.bill_to", "Bill To") # You might want to add this key
        if lbl_bill_to == "Bill To": lbl_bill_to = "Bill To" 

        lbl_item = L("Inventory.part", "Item")
        lbl_qty = L("Inventory.quantity", "Qty")
        lbl_unit_cost = L("Inventory.unit_cost", "Unit Cost")
        lbl_total = L("Inventory.total", "Total")
        
        lbl_notes = L("Inventory.notes_label", "Notes")
        lbl_total_amount = L("Inventory.total_amount", "Total Amount")
        
        # --- Data ---
        po_number = data.get('po_number', 'N/A')
        date_str = data.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        expected_str = data.get('expected_delivery', 'N/A')
        
        supplier_name = data.get('supplier_name', 'N/A')
        supplier_contact = data.get('supplier_contact', '')
        supplier_phone = data.get('supplier_phone', '')
        supplier_address = data.get('supplier_address', '') # Assuming this might exist
        
        items = data.get('items', [])
        total_amount = data.get('total_amount', 0)
        formatted_total = self.cf.format(total_amount)
        notes = data.get('notes', '')

        # --- Company Info ---
        company_name = "My Company"
        company_address = ""
        company_phone = ""
        company_logo = None
        
        if self.settings:
            company_name = self.settings.business_name or company_name
            company_address = self.settings.address or ""
            company_phone = self.settings.business_phone or ""
            company_logo = self.settings.logo_url

        # Logo HTML
        logo_html = ""
        if company_logo and os.path.exists(company_logo):
            logo_html = f'<img src="file://{company_logo}" class="logo" alt="Logo">'
        
        # Items Rows
        items_html = ""
        for i, item in enumerate(items, 1):
            qty = item.get('quantity', 0)
            cost = float(item.get('unit_price', 0))
            line_total = float(item.get('total', 0))
            
            items_html += f"""
            <tr>
                <td>{i}</td>
                <td>{item.get('part_name', '')}</td>
                <td class="text-center">{qty}</td>
                <td class="text-right">{self.cf.format(cost)}</td>
                <td class="text-right">{self.cf.format(line_total)}</td>
            </tr>
            """
            
        # --- CSS ---
        font_family = self._get_font_family()
        css = f"""
        @page {{
            size: A4;
            margin: 20mm;
        }}
        body {{
            font-family: {font_family};
            font-size: 14px;
            color: #333;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .logo {{
            max-height: 80px;
            margin-bottom: 10px;
        }}
        .company-info h1 {{
            margin: 0;
            font-size: 24px;
            color: #2c3e50;
        }}
        .company-info p {{
            margin: 2px 0;
            font-size: 12px;
            color: #666;
        }}
        .po-title {{
            text-align: right;
        }}
        .po-title h2 {{
            margin: 0;
            font-size: 32px;
            color: #34495e;
            text-transform: uppercase;
        }}
        .po-meta {{
            margin-top: 10px;
            text-align: right;
            font-size: 12px;
        }}
        .po-meta table {{
            margin-left: auto;
        }}
        .po-meta td {{
            padding: 2px 8px;
        }}
        .addresses {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            gap: 20px;
        }}
        .address-box {{
            flex: 1;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }}
        .address-box h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #2c3e50;
            text-transform: uppercase;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
            display: inline-block;
        }}
        .address-box p {{
            margin: 2px 0;
            font-size: 12px;
        }}
        table.items {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        table.items th {{
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
            font-size: 12px;
        }}
        table.items td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 12px;
        }}
        table.items tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        
        .totals {{
            width: 40%;
            margin-left: auto;
        }}
        .totals table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .totals td {{
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .totals .grand-total {{
            font-weight: bold;
            font-size: 16px;
            border-top: 2px solid #2c3e50;
            color: #2c3e50;
        }}
        .notes {{
            margin-top: 30px;
            padding: 15px;
            background: #fff3cd;
            border: 1px solid #ffeeba;
            border-radius: 4px;
            color: #856404;
            font-size: 12px;
        }}
        .footer {{
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 10px;
            color: #aaa;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }}
        """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{css}</style>
        </head>
        <body>
            <div class="header">
                <div class="company-info">
                    {logo_html}
                    <h1>{company_name}</h1>
                    <div class="address-lines">
                        <p>{company_address}</p>
                        <p>{company_phone}</p>
                    </div>
                </div>
                <div class="po-title">
                    <h2>{title}</h2>
                    <div class="po-meta">
                        <table>
                            <tr>
                                <td><strong>{lbl_po_number}:</strong></td>
                                <td>{po_number}</td>
                            </tr>
                            <tr>
                                <td><strong>{lbl_date}:</strong></td>
                                <td>{date_str}</td>
                            </tr>
                            <tr>
                                <td><strong>{lbl_expected}:</strong></td>
                                <td>{expected_str}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>

            <div class="addresses">
                <div class="address-box">
                    <h3>{lbl_supplier}</h3>
                    <p><strong>{supplier_name}</strong></p>
                    <p>{supplier_contact}</p>
                    <p>{supplier_phone}</p>
                    <p>{supplier_address}</p>
                </div>
                <div class="address-box">
                    <h3>{lbl_bill_to}</h3>
                    <p><strong>{company_name}</strong></p>
                    <p>{company_address}</p>
                    <p>{company_phone}</p>
                </div>
            </div>

            <table class="items">
                <thead>
                    <tr>
                        <th width="5%">#</th>
                        <th width="45%">{lbl_item}</th>
                        <th width="15%" class="text-center">{lbl_qty}</th>
                        <th width="17.5%" class="text-right">{lbl_unit_cost}</th>
                        <th width="17.5%" class="text-right">{lbl_total}</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="totals">
                <table>
                    <tr class="grand-total">
                        <td>{lbl_total_amount}</td>
                        <td class="text-right">{formatted_total}</td>
                    </tr>
                </table>
            </div>

            {f'<div class="notes"><strong>{lbl_notes}:</strong><br>{notes}</div>' if notes else ''}

            <div class="footer">
                Generated via MSA System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        return html_content

    def _print_to_pdf(self, data, filename):
        """Generate PDF file from data"""
        html_content = self.generate_html(data)
        
        # Configure font
        font_config = None
        if platform.system() == 'Darwin':
             # Minimal font config for WeasyPrint/Pango
             pass
        
        # Create HTML object
        html = HTML(string=html_content)
        
        # Write PDF
        html.write_pdf(target=filename)
        return filename

    def preview_purchase_order(self, data):
        """Generate and open PDF preview"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            filename = temp_file.name
            temp_file.close()
            
            self._print_to_pdf(data, filename)
            
            # Open the file
            if platform.system() == 'Darwin':
                subprocess.call(('open', filename))
            elif platform.system() == 'Windows':
                os.startfile(filename)
            else:
                subprocess.call(('xdg-open', filename))
                
            return filename
        except Exception as e:
            print(f"Error previewing PO: {e}")
            import traceback
            traceback.print_exc()
            return None

    def print_purchase_order(self, data):
        """Print purchase order using native dialog (or save as PDF)"""
        try:
            # 1. Generate temp PDF
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            filename = temp_file.name
            temp_file.close()
            
            self._print_to_pdf(data, filename)
            
            # 2. Setup Printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.NativeFormat)
            
            # 3. Show Print Dialog
            dialog = QPrintDialog(printer, self.parent)
            if dialog.exec() == QPrintDialog.Accepted:
                # Handle "Print to PDF" on Linux/Windows if selected in dialog,
                # but MacOS native dialog handles PDF saving internally usually.
                # If output filename is set, we copy/write there.
                
                if printer.outputFileName():
                     shutil.copyfile(filename, printer.outputFileName())
                else:
                    printer_name = printer.printerName()
                    
                    if platform.system() == 'Darwin':
                         subprocess.call(['lpr', filename])
                         
                    elif platform.system() == 'Windows':
                        # Try to print using SumatraPDF (Silent & Accurate)
                        try:
                           from config.config import get_sumatra_path, log_print_debug
                           
                           log_print_debug(f"Attempting to print PO to printer '{printer_name}'")
                           
                           sumatra_path = get_sumatra_path()
                           if not sumatra_path:
                                raise FileNotFoundError("SumatraPDF path not found via config")
                                
                           log_print_debug(f"Found SumatraPDF at: {sumatra_path}")
                           
                           printer_name_arg = f'{printer_name}'
                           
                           # SumatraPDF command
                           cmd = [
                               sumatra_path,
                               "-print-to", printer_name_arg,
                               "-silent",
                               filename
                           ]
                           
                           log_print_debug(f"Executing command: {cmd}")
                           print(f"DEBUG: Attempting SumatraPDF for PO: {cmd}")
                           
                           result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                           log_print_debug(f"Command successful. Stdout: {result.stdout}")
                           print("DEBUG: SumatraPDF print command successful")
                           
                        except Exception as sumatra_e:
                           from config.config import log_print_debug
                           log_print_debug(f"SumatraPDF failed: {sumatra_e}")
                           print(f"SumatraPDF failed ({sumatra_e}). Falling back to os.startfile...")
                           log_print_debug("Fallback to os.startfile")
                           os.startfile(filename, 'print')
                           
                    else:
                         subprocess.call(['lpr', filename])
                         
                return filename
            else:
                # Dialog cancelled
                return None
        except Exception as e:
            print(f"Error printing PO: {e}")
            return None

    # --- Backward Compatibility Aliases ---
    def preview_pdf(self, data):
        return self.preview_purchase_order(data)

    def print_pdf(self, data):
        return self.print_purchase_order(data)

    def generate_pdf(self, data, filename=None):
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            filename = temp_file.name
            temp_file.close()
        self._print_to_pdf(data, filename)
        return filename
