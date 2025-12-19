# src/app/utils/print/barcode_generator.py
"""
Barcode Generator - Generate and print device barcodes using WeasyPrint and python-barcode
"""

import os
import tempfile
import platform
import base64
import io
import shutil
import subprocess

# Fix for macOS WeasyPrint
if platform.system() == 'Darwin':
     os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

from weasyprint import HTML, CSS
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtCore import QSizeF, QMarginsF, QUrl
from PySide6.QtGui import QDesktopServices

try:
    import barcode
    from barcode.writer import ImageWriter
    HAS_BARCODE_LIB = True
except ImportError:
    HAS_BARCODE_LIB = False
    print("Warning: python-barcode not installed. Barcode generation will fail.")

class BarcodeGenerator:
    """Generate barcode labels for devices (optimized for thermal printers)"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def _generate_barcode_b64(self, code_text):
        """Generate Code128 barcode as base64 png"""
        if not HAS_BARCODE_LIB or not code_text:
            return ""
        
        try:
            # Code128 is standard
            code128 = barcode.get_barcode_class('code128')
            # Use ImageWriter to get PNG (easier to size in HTML than SVG sometimes, or consistent)
            # Actually ImageWriter requires Pillow
            writer = ImageWriter()
            
            # Configure writer
            # module_height is in mm by default for some writers or relative
            # For ImageWriter, it is in pixels approx.
            
            bc = code128(code_text, writer=writer)
            
            buffer = io.BytesIO()
            options = {
                'module_width': 0.3, # thinnest bar width in mm (default 0.2)
                'module_height': 5.0, # height in mm (default 15)
                'quiet_zone': 1.0, 
                'font_size': 0, # No text, we add our own
                'text_distance': 0,
                'write_text': False
            }
            bc.write(buffer, options=options)
            
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            print(f"Error generating barcode image: {e}")
            return ""

    def generate_barcodes(self, devices, file_path):
        """
        Generate barcode PDF for devices (thermal printer format - single column)
        Args:
            devices: List of device DTOs
            file_path: Path to save PDF
        """
        # Thermal label size: 2.5" x 1.5"
        # Converted to mm: 63.5mm x 38.1mm
        width_mm = 63.5
        height_mm = 38.1
        
        # HTML Content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page {{
                    size: {width_mm}mm {height_mm}mm;
                    margin: 0;
                }}
                body {{
                    font-family: Helvetica, sans-serif; /* Standard fallback */
                    margin: 0;
                    padding: 2mm;
                    text-align: center;
                    width: {width_mm}mm;
                    height: {height_mm}mm;
                    box-sizing: border-box;
                    overflow: hidden;
                }}
                .label-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                }}
                .barcode-img {{
                    max-width: 90%;
                    height: auto;
                    margin-bottom: 2px;
                }}
                .barcode-text {{
                    font-size: 8pt;
                    font-family: monospace;
                    margin-bottom: 2px;
                }}
                .device-name {{
                    font-size: 9pt;
                    font-weight: bold;
                    margin-bottom: 2px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 100%;
                }}
                .meta {{
                    font-size: 7pt;
                    color: #333;
                }}
                /* Page break for multi-page PDF */
                .page-break {{
                    page-break-after: always;
                }}
            </style>
        </head>
        <body>
        """
        
        for idx, device in enumerate(devices):
            if idx > 0:
                html_content += '<div class="page-break"></div>'
            
            b64_img = self._generate_barcode_b64(device.barcode)
            
            brand_model = f"{device.brand or ''} {device.model or ''}".strip()
            
            # Lock info
            lock_info = "Lock: N/A"
            if device.lock_type:
                 lock_info = f"Lock: {device.lock_type}"
                 if device.passcode:
                     lock_info += f" ({device.passcode})"
            
            # Ticket
            ticket_info = ""
            if hasattr(device, 'ticket_number') and device.ticket_number:
                ticket_info = f"Ticket: {device.ticket_number}"

            html_content += f"""
            <div class="label-container">
                <img src="data:image/png;base64,{b64_img}" class="barcode-img">
                <div class="barcode-text">{device.barcode or ''}</div>
                <div class="device-name">{brand_model}</div>
                <div class="meta">{lock_info}</div>
                {f'<div class="meta">{ticket_info}</div>' if ticket_info else ''}
            </div>
            """
            
        html_content += "</body></html>"
        
        # Render PDF
        HTML(string=html_content).write_pdf(file_path)

    def preview_barcodes(self, devices):
        """Preview barcodes in default PDF viewer"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix='.pdf',
                prefix='barcode_preview_',
                delete=False
            )
            temp_path = temp_file.name
            temp_file.close()
            
            self.generate_barcodes(devices, temp_path)
            
            if platform.system() == 'Darwin':
                subprocess.call(('open', temp_path))
            elif platform.system() == 'Windows':
                os.startfile(temp_path)
            else:
                subprocess.call(('xdg-open', temp_path))
            
            return True
        except Exception as e:
            print(f"Error previewing barcodes: {e}")
            return False

    def print_barcodes(self, devices):
        """Print barcodes using Qt"""
        temp_pdf = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix='.pdf',
                prefix='barcode_print_',
                delete=False
            )
            temp_pdf = temp_file.name
            temp_file.close()
            
            self.generate_barcodes(devices, temp_pdf)
            
            printer = QPrinter(QPrinter.HighResolution)
            
            # Common thermal size
            label_size = QSizeF(2.5, 1.5) # Inches
            page_size = QPageSize(label_size, QPageSize.Unit.Inch, "Thermal Label")
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            printer.setPageMargins(QMarginsF(0, 0, 0, 0))
            
            dialog = QPrintDialog(printer, self.parent)
            if dialog.exec():
                output_file = printer.outputFileName()
                if output_file:
                    shutil.copy2(temp_pdf, output_file)
                else:
                    # Windows Printing Logic
                    if platform.system() == 'Windows':
                        try:
                           from config.config import get_sumatra_path, log_print_debug
                           printer_name = printer.printerName()
                           
                           log_print_debug(f"Attempting to print Barcodes to printer '{printer_name}'")
                           
                           sumatra_path = get_sumatra_path()
                           if not sumatra_path:
                                raise FileNotFoundError("SumatraPDF path not found via config")
                                
                           log_print_debug(f"Found SumatraPDF at: {sumatra_path}")
                           
                           printer_name_arg = f'{printer_name}'
                           
                           cmd = [
                               sumatra_path,
                               "-print-to", printer_name_arg,
                               "-silent",
                               temp_pdf
                           ]
                           
                           log_print_debug(f"Executing command: {cmd}")
                           print(f"DEBUG: Attempting SumatraPDF for Barcode: {cmd}")
                           
                           result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                           log_print_debug(f"Command successful. Stdout: {result.stdout}")
                           
                        except Exception as e:
                            from config.config import log_print_debug
                            log_print_debug(f"SumatraPDF failed: {e}")
                            print(f"SumatraPDF failed ({e}), falling back to Qt native print...")
                            log_print_debug("Fallback to Qt Native")
                            self._print_pdf_with_qt(temp_pdf, printer)
                    else:
                        # Non-Windows fallback to Qt Native
                        self._print_pdf_with_qt(temp_pdf, printer)
                        
                return True
            return False
            
        except Exception as e:
            print(f"Error printing barcodes: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if temp_pdf and os.path.exists(temp_pdf):
                try:
                    os.unlink(temp_pdf)
                except:
                    pass

    def _print_pdf_with_qt(self, pdf_path, printer):
        """Print PDF using QtPdf"""
        try:
            from PySide6.QtPdf import QPdfDocument
            from PySide6.QtGui import QPainter
            
            pdf_doc = QPdfDocument()
            pdf_doc.load(pdf_path)
            
            if pdf_doc.error() != QPdfDocument.Error.NoError:
                raise Exception(f"Failed to load PDF: {pdf_doc.error()}")
            
            painter = QPainter()
            if not painter.begin(printer):
                 raise Exception("Failed to start painting")
            
            try:
                for page_num in range(pdf_doc.pageCount()):
                    if page_num > 0:
                        printer.newPage()
                    
                    page_size = pdf_doc.pagePointSize(page_num)
                    # Use a higher resolution render if possible
                    image = pdf_doc.render(page_num, QSizeF(page_size.width() * 4, page_size.height() * 4))
                    
                    target_rect = painter.viewport()
                    painter.drawImage(target_rect, image)
            finally:
                painter.end()
                
        except Exception as e:
            print(f"Error in _print_pdf_with_qt: {e}")
            raise
