# src/app/components/device_info_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QFrame, QLineEdit, QComboBox, QPushButton, 
                              QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import csv
from fpdf import FPDF
from datetime import datetime
from utils.validation.message_handler import MessageHandler

class DeviceInfoWidget(QWidget):
    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self._all_devices = devices  # Store all devices
        self.customer_name = "Customer"  # Default if not set later
        self.current_user = "System"    # Default if not set later

        self._setup_ui()
        self._connect_signals()
        self._filter_devices()  # Initial filter to populate table
        self._update_details()  # Force initial details update

    def _setup_ui(self):
        """Setup the UI components"""
        self.setWindowTitle("Customer Devices")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(
            Qt.Window |
            # Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(True)
        filter_layout.addWidget(self.search_input)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        self.status_filter.addItems(["Received", "Diagnosed", "Repairing", "Repaired", "Completed"])
        filter_layout.addWidget(self.status_filter)

        # Export buttons
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setFixedWidth(100)
        filter_layout.addWidget(self.export_csv_btn)
        
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.setFixedWidth(100)
        filter_layout.addWidget(self.export_pdf_btn)
        
        self.count_label = QLabel("Showing 0 devices")
        filter_layout.addStretch()
        filter_layout.addWidget(self.count_label)
        
        main_layout.addLayout(filter_layout)
        
        # Devices table (now with barcode column)
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)  # Added barcode column
        self.devices_table.setHorizontalHeaderLabels(["#", "Barcode", "Brand - Model", "Status"])
        self.devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.devices_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.devices_table.verticalHeader().setVisible(False)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.devices_table)
        
        # Details panel
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(15, 15, 15, 15)
        
        self.details_title = QLabel("SELECTED DEVICE DETAILS")
        self.details_title.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(self.details_title)
        
        self.details_content = QLabel("Select a device to view details")
        self.details_content.setTextFormat(Qt.RichText)
        self.details_content.setWordWrap(True)
        details_layout.addWidget(self.details_content)
        
        main_layout.addWidget(details_frame)

    def _connect_signals(self):
        """Connect all signals"""
        self.search_input.textChanged.connect(self._filter_devices)
        self.status_filter.currentTextChanged.connect(self._filter_devices)
        self.devices_table.itemSelectionChanged.connect(self._update_details)
        self.export_csv_btn.clicked.connect(self._export_to_csv)
        self.export_pdf_btn.clicked.connect(self._export_to_pdf)

    def _filter_devices(self):
        """Filter devices based on search and status"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        
        filtered = []
        for device in self._all_devices:
            matches_search = (search_text in (device.brand or '').lower() or 
                            search_text in (device.model or '').lower() or
                            search_text in (device.barcode or '').lower())
            matches_status = (status_filter == "All Statuses" or 
                            device.status.lower() == status_filter.lower())
            
            if matches_search and matches_status:
                filtered.append(device)
        
        self._filtered_devices = filtered
        self._populate_table(filtered)
        self.count_label.setText(f"Showing {len(filtered)} devices")

    def _populate_table(self, devices):
        """Populate table with devices"""
        self.devices_table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            # Number column
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            
            # Barcode column
            barcode_item = QTableWidgetItem(device.barcode or "N/A")
            barcode_item.setTextAlignment(Qt.AlignCenter)
            
            # Brand-Model column
            brand_model = f"{device.brand or 'Unknown'} - {device.model or ''}"
            brand_item = QTableWidgetItem(brand_model)
            
            # Status column with color
            status_item = QTableWidgetItem(device.status.capitalize())
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(*self._get_status_color(device.status)))
            
            # Add items to table
            self.devices_table.setItem(row, 0, num_item)
            self.devices_table.setItem(row, 1, barcode_item)
            self.devices_table.setItem(row, 2, brand_item)
            self.devices_table.setItem(row, 3, status_item)
        
        # Select first row if available
        if devices:
            self.devices_table.selectRow(0)

    def _update_details(self):
        """Update details panel with selected device"""
        selected = self.devices_table.selectedItems()
        if not selected:
            self.details_content.setText("Select a device to view details")
            return
            
        row = selected[0].row()
        device = self._filtered_devices[row] if hasattr(self, '_filtered_devices') and row < len(self._filtered_devices) else None
        
        if device:
            received_date = device.received_at.strftime('%b %d, %Y') if device.received_at else 'N/A'
            details = (
                f"• <b>Barcode:</b> {device.barcode or 'N/A'}<br>"
                f"• <b>Device:</b> {device.brand or 'Unknown'} {device.model or ''}<br>"
                f"• <b>Color:</b> {device.color or 'N/A'}<br>"
                f"• <b>Serial:</b> {device.serial_number or 'N/A'}<br>"
                f"• <b>IMEI:</b> {device.imei or 'N/A'}<br>"
                f"• <b>Status:</b> {device.status.capitalize()} "
                f"(<small>{received_date}</small>)<br>"
                f"• <b>Condition:</b> {device.condition or 'Not specified'}"
            )
            self.details_content.setText(details)

    def _get_status_color(self, status):
        """Return RGB tuple for status colors"""
        status_colors = {
            'received': (52, 152, 219),    # Blue
            'diagnosed': (155, 89, 182),   # Purple
            'repairing': (241, 196, 15),   # Yellow
            'repaired': (39, 174, 96),     # Green
            'completed': (46, 204, 113),   # Bright Green
            'returned': (149, 165, 166)    # Gray
        }
        return status_colors.get(status.lower(), (44, 62, 80))  # Default dark

    def _export_to_csv(self):
        """Export visible devices to CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)")
        
        if not path:
            return
            
        devices = self._filtered_devices if hasattr(self, '_filtered_devices') else []
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    '#', 'Barcode', 'Brand', 'Model', 'Serial', 
                    'IMEI', 'Status', 'Received Date', 'Condition'
                ])
                
                for i, device in enumerate(devices, 1):
                    writer.writerow([
                        i,
                        device.barcode or '',
                        device.brand or '',
                        device.model or '',
                        device.serial_number or '',
                        device.imei or '',
                        device.status.capitalize(),
                        device.received_at.strftime('%Y-%m-%d') if device.received_at else '',
                        device.condition or ''
                    ])
            MessageHandler.show_success(self, "Export Successful", "CSV file exported successfully")
        except Exception as e:
            MessageHandler.show_critical(self, "Export Error", f"Failed to export CSV: {str(e)}")

    def _export_to_pdf(self):
        """Export visible devices to PDF with professional formatting"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)")
        
        if not path:
            return
            
        devices = self._filtered_devices if hasattr(self, '_filtered_devices') else []
        
        try:
            pdf = FPDF()
            pdf.set_margins(15, 15, 15)  # Left, Top, Right margins
            
            # We will handle page breaks manually to ensure the footer is placed correctly
            pdf.set_auto_page_break(auto=False)
            
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            
            # Title with customer name
            pdf.set_font("Arial", 'B', 14)
            title = f"{self.customer_name}'s Device Report" if hasattr(self, 'customer_name') else "Device Report"
            pdf.cell(200, 10, txt=title, ln=1, align='C')
            
            # Metadata line with username and date
            pdf.set_font("Arial", size=10)
            username = f"@{self.current_user}" if hasattr(self, 'current_user') else "@system"
            pdf.cell(200, 8, 
                    txt=f"Generated by {username} | {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                    ln=1)
            pdf.ln(8)
            
            # Table headers
            col_widths = [8, 30, 20, 35, 25, 30, 20, 20]  # Adjusted column widths
            headers = ["#", "Barcode", "Brand", "Model", "Serial", "IMEI", "Status", "Received"]
            
            # Header row with bold font
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(200, 220, 255)  # Light blue header
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, txt=header, border=1, align='C', fill=True)
            pdf.ln()
            
            # Device rows
            pdf.set_font("Arial", size=8)
            
            # We'll check the space before each new row
            row_height = 10
            footer_height = 15
            
            for i, device in enumerate(devices, 1):
                # Check if a new page is needed.
                # We add an additional margin for the footer.
                if pdf.get_y() + row_height + footer_height > pdf.h - pdf.b_margin:
                    pdf.add_page()
                    # Re-print the headers on the new page
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_fill_color(200, 220, 255)
                    for header_i, header_txt in enumerate(headers):
                        pdf.cell(col_widths[header_i], 10, txt=header_txt, border=1, align='C', fill=True)
                    pdf.ln()
                    pdf.set_font("Arial", size=8)
                    
                # Alternate row coloring
                if i % 2 == 0:
                    pdf.set_fill_color(240, 240, 240)
                else:
                    pdf.set_fill_color(255, 255, 255)
                
                # Cell data
                pdf.cell(col_widths[0], 10, txt=str(i), border=1, align='C', fill=True)
                pdf.cell(col_widths[1], 10, txt=device.barcode or 'N/A', border=1, fill=True)
                pdf.cell(col_widths[2], 10, txt=device.brand or '', border=1, fill=True)
                pdf.cell(col_widths[3], 10, txt=device.model or '', border=1, fill=True)
                pdf.cell(col_widths[4], 10, txt=device.serial_number or 'N/A', border=1, fill=True)
                pdf.cell(col_widths[5], 10, txt=device.imei or 'N/A', border=1, fill=True)
                
                # Status with color coding
                status = device.status.capitalize()
                if device.status.lower() == 'repaired':
                    pdf.set_text_color(39, 174, 96)  # Green
                elif device.status.lower() == 'completed':
                    pdf.set_text_color(46, 204, 113)  # Brighter green
                else:
                    pdf.set_text_color(0, 0, 0)  # Black
                
                pdf.cell(col_widths[6], 10, txt=status, border=1, align='C', fill=True)
                pdf.set_text_color(0, 0, 0)  # Reset to black
                
                # Received date
                received_date = device.received_at.strftime('%Y-%m-%d') if device.received_at else 'N/A'
                pdf.cell(col_widths[7], 10, txt=received_date, border=1, align='C', fill=True)
                pdf.ln()
            
            # Footer is now guaranteed to be on the last page because we managed the space.
            pdf.set_y(-15)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, txt=f"Page {pdf.page_no()}", align='C')
            
            pdf.output(path)
            MessageHandler.show_success(self, "Export Successful", "PDF file exported successfully")
        except Exception as e:
            MessageHandler.show_critical(self, "Export Error", f"Failed to export PDF: {str(e)}")