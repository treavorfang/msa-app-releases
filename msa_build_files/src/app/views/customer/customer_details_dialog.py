# src/app/views/customer/customer_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QGroupBox, QTabWidget, 
                              QWidget, QListWidget, QListWidgetItem, QFrame,
                              QScrollArea, QGridLayout, QFileDialog, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt
from datetime import datetime
from config.constants import UIColors
import csv

from utils.validation.message_handler import MessageHandler
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class CustomerDetailsDialog(QDialog):
    """Dialog for viewing detailed customer information"""
    
    def __init__(self, customer, devices=None, balance_info=None, container=None, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.devices = devices or []
        self.balance_info = balance_info
        self.container = container
        self.lm = language_manager
        self.cf = currency_formatter
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Customers.customer_details', 'Customer Details')} - {self.customer.name}")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Header with customer name
        header_layout = QHBoxLayout()
        
        title = QLabel(f"👤 {self.customer.name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Balance Badge
        if self.balance_info:
            balance = self.balance_info.get('balance', 0)
            
            if balance > 0:
                color = '#EF4444' # Red
                text = f"{self.lm.get('Customers.balance_label', 'Balance')}: +{self.cf.format(balance)}"
            elif balance < 0:
                color = '#10B981' # Green
                text = f"{self.lm.get('Customers.balance_label', 'Balance')}: -{self.cf.format(abs(balance))}"
            else:
                color = '#6B7280' # Gray
                text = f"{self.lm.get('Customers.balance_label', 'Balance')}: {self.cf.format(0)}"
            
            balance_badge = QLabel(text)
            balance_badge.setStyleSheet(f"""
                background-color: {color}; 
                color: white; 
                border-radius: 4px; 
                padding: 4px 8px; 
                font-weight: bold;
            """)
            header_layout.addWidget(balance_badge)
        
        # Status badge (Active/Deleted)
        status_text = self.lm.get("Common.deleted", "Deleted") if self.customer.deleted_at else self.lm.get("Common.active", "Active")
        status_color = UIColors.ERROR if self.customer.deleted_at else UIColors.SUCCESS
        status_badge = QLabel(f" {status_text} ")
        status_badge.setStyleSheet(f"""
            background-color: {status_color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
        header_layout.addWidget(status_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Contact Info Tab
        contact_tab = self._create_contact_tab()
        tabs.addTab(contact_tab, self.lm.get("Customers.contact_info", "Contact Info"))
        
        # Devices Tab
        devices_tab = self._create_devices_tab()
        tabs.addTab(devices_tab, f"{self.lm.get('Customers.devices', 'Devices')} ({len(self.devices)})")
        
        # History Tab
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, self.lm.get("Customers.history_notes", "Notes & History"))
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_contact_tab(self):
        """Create contact information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Contact Details Group
        contact_group = QGroupBox(self.lm.get("Customers.contact_details_group", "Contact Details"))
        contact_layout = QFormLayout(contact_group)
        
        contact_layout.addRow(self.lm.get("Customers.phone_label", "Phone") + ":", QLabel(self.customer.phone or self.lm.get("Common.not_applicable", "N/A")))
        contact_layout.addRow(self.lm.get("Customers.email_label", "Email") + ":", QLabel(self.customer.email or self.lm.get("Common.not_applicable", "N/A")))
        contact_layout.addRow(self.lm.get("Customers.address_label", "Address") + ":", QLabel(self.customer.address or self.lm.get("Common.not_applicable", "N/A")))
        
        pref_method = self.customer.preferred_contact_method.title() if self.customer.preferred_contact_method else self.lm.get("Customers.phone_label", "Phone")
        contact_layout.addRow(self.lm.get("Customers.preferred_contact_label", "Preferred Contact") + ":", QLabel(pref_method))
        
        layout.addWidget(contact_group)
        layout.addStretch()
        
        return widget
    
    def _create_devices_tab(self):
        """Create devices list tab with list view and detail card"""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        if not self.devices:
            no_devices_label = QLabel(self.lm.get("Customers.no_registered_devices", "No registered devices."))
            no_devices_label.setAlignment(Qt.AlignCenter)
            no_devices_label.setStyleSheet("color: gray; font-style: italic; font-size: 14px;")
            main_layout.addWidget(no_devices_label)
        else:
            # Left side - Device list
            list_container = QWidget()
            list_layout = QVBoxLayout(list_container)
            list_layout.setContentsMargins(0, 0, 0, 0)
            list_layout.setSpacing(4)
            
            # Header with label and export buttons
            header_layout = QHBoxLayout()
            
            list_label = QLabel(f"{self.lm.get('Customers.devices_count', 'Devices')} ({len(self.devices)})")
            list_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #9CA3AF;")
            header_layout.addWidget(list_label)
            
            header_layout.addStretch()
            
            # Export buttons
            export_csv_btn = QPushButton("CSV")
            export_csv_btn.setFixedWidth(50)
            export_csv_btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: white;
                    border: 1px solid #4B5563;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #4B5563;
                }
            """)
            export_csv_btn.clicked.connect(self._export_devices_to_csv)
            header_layout.addWidget(export_csv_btn)
            
            export_pdf_btn = QPushButton("PDF")
            export_pdf_btn.setFixedWidth(50)
            export_pdf_btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: white;
                    border: 1px solid #4B5563;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #4B5563;
                }
            """)
            export_pdf_btn.clicked.connect(self._export_devices_to_pdf)
            header_layout.addWidget(export_pdf_btn)
            
            list_layout.addLayout(header_layout)
            
            self.device_list = QListWidget()
            self.device_list.setStyleSheet("""
                QListWidget {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #374151;
                }
                QListWidget::item:selected {
                    background-color: #3B82F6;
                    color: white;
                }
                QListWidget::item:hover {
                    background-color: #374151;
                }
            """)
            
            for device in self.devices:
                item_text = f"{device.brand or 'Unknown'} {device.model or ''}"
                if device.barcode:
                    item_text += f"\n📱 {device.barcode}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, device)  # Store device object
                self.device_list.addItem(item)
            
            list_layout.addWidget(self.device_list)
            main_layout.addWidget(list_container, 1)
            
            # Right side - Device detail card
            self.device_detail_container = QWidget()
            detail_layout = QVBoxLayout(self.device_detail_container)
            detail_layout.setContentsMargins(0, 0, 0, 0)
            
            detail_label = QLabel(self.lm.get("Customers.devices_count", "Device Details"))
            detail_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #9CA3AF;")
            detail_layout.addWidget(detail_label)
            
            # Placeholder for device card
            self.device_card_placeholder = QLabel(self.lm.get("Customers.select_device_prompt", "Select a device to view details"))
            self.device_card_placeholder.setAlignment(Qt.AlignCenter)
            self.device_card_placeholder.setStyleSheet("""
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 40px;
                color: #6B7280;
                font-style: italic;
            """)
            detail_layout.addWidget(self.device_card_placeholder)
            
            main_layout.addWidget(self.device_detail_container, 2)
            
            # Connect selection signal
            self.device_list.currentItemChanged.connect(self._on_device_selected)
            
            # Select first device by default
            if self.devices:
                self.device_list.setCurrentRow(0)
            
        return widget
    
    def _on_device_selected(self, current, previous):
        """Handle device selection from list"""
        if not current:
            return
        
        device = current.data(Qt.UserRole)
        if not device:
            return
        
        # Remove old card if exists
        if hasattr(self, 'current_device_card') and self.current_device_card:
            self.device_detail_container.layout().removeWidget(self.current_device_card)
            self.current_device_card.deleteLater()
        
        # Remove placeholder
        if hasattr(self, 'device_card_placeholder') and self.device_card_placeholder:
            self.device_card_placeholder.hide()
        
        # Create and add new card
        self.current_device_card = self._create_device_detail_card(device)
        self.device_detail_container.layout().addWidget(self.current_device_card)
    
    def _create_device_detail_card(self, device):
        """Create a detailed device card for the selected device"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header row - Brand/Model and Status
        header = QHBoxLayout()
        
        device_name = f"{device.brand or 'Unknown'} {device.model or ''}"
        name_label = QLabel(device_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        header.addWidget(name_label)
        
        header.addStretch()
        
        # Status badge
        status_colors = {
            'received': '#4169E1',
            'diagnosed': '#20B2AA',
            'repairing': '#FFD700',
            'repaired': '#BA55D3',
            'completed': '#32CD32',
            'returned': '#90EE90'
        }
        status_color = status_colors.get(device.status.lower(), '#6B7280')
        
        status_badge = QLabel(device.status.upper())
        status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(status_badge)
        
        layout.addLayout(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #374151;")
        layout.addWidget(separator)
        
        # Device details in a grid
        details_grid = QGridLayout()
        details_grid.setSpacing(8)
        details_grid.setColumnStretch(1, 1)
        
        row = 0
        
        # Barcode
        if device.barcode:
            self._add_detail_row(details_grid, row, self.lm.get("Devices.barcode", "Barcode") + ":", device.barcode)
            row += 1
        
        # Color
        if device.color:
            self._add_detail_row(details_grid, row, self.lm.get("Devices.color", "Color") + ":", device.color)
            row += 1
        
        # Condition
        if device.condition:
            self._add_detail_row(details_grid, row, self.lm.get("Devices.condition", "Condition") + ":", device.condition)
            row += 1
        
        # IMEI
        if device.imei:
            self._add_detail_row(details_grid, row, self.lm.get("Devices.imei", "IMEI") + ":", device.imei)
            row += 1
        
        # Serial Number
        if device.serial_number:
            self._add_detail_row(details_grid, row, self.lm.get("Devices.serial_number", "Serial Number") + ":", device.serial_number)
            row += 1
        
        # Received date
        if device.received_at:
            date_str = device.received_at.strftime('%Y-%m-%d %H:%M')
            self._add_detail_row(details_grid, row, self.lm.get("Common.received", "Received") + ":", date_str)
            row += 1
        
        layout.addLayout(details_grid)
        layout.addStretch()
        
        return card
    
    def _add_detail_row(self, grid_layout, row, label_text, value_text):
        """Add a detail row to the grid layout"""
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #9CA3AF;")
        
        value = QLabel(str(value_text))
        value.setStyleSheet("font-size: 12px; color: #E5E7EB;")
        value.setWordWrap(True)
        
        grid_layout.addWidget(label, row, 0, Qt.AlignTop)
        grid_layout.addWidget(value, row, 1)
    
    def _create_history_tab(self):
        """Create history and notes tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Notes Group
        notes_group = QGroupBox(self.lm.get("Customers.internal_notes_group", "Internal Notes"))
        notes_layout = QVBoxLayout(notes_group)
        
        notes_text = self.customer.notes or ""
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(notes_text)
        self.notes_edit.setPlaceholderText(self.lm.get("Customers.add_notes_placeholder", "Add internal notes here..."))
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        notes_layout.addWidget(self.notes_edit)
        
        # Save Notes Button
        save_notes_btn = QPushButton(self.lm.get("Customers.save_notes", "Save Notes"))
        save_notes_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        save_notes_btn.clicked.connect(self._save_notes)
        notes_layout.addWidget(save_notes_btn, alignment=Qt.AlignRight)
        
        layout.addWidget(notes_group)
        
        # Timeline Group
        time_group = QGroupBox(self.lm.get("Customers.timeline_group", "Timeline"))
        time_layout = QFormLayout(time_group)
        
        created_at = self.customer.created_at.strftime("%Y-%m-%d %H:%M") if self.customer.created_at else self.lm.get("Common.not_applicable", "N/A")
        time_layout.addRow(self.lm.get("Customers.created_label", "Created") + ":", QLabel(created_at))
        
        updated_at = self.customer.updated_at.strftime("%Y-%m-%d %H:%M") if self.customer.updated_at else self.lm.get("Common.not_applicable", "N/A")
        time_layout.addRow(self.lm.get("Customers.last_updated_label", "Last Updated") + ":", QLabel(updated_at))
        
        layout.addWidget(time_group)
        layout.addStretch()
        
        return widget
    
    def _export_devices_to_csv(self):
        """Export customer devices to CSV"""
        if not self.devices:
            MessageHandler.show_warning(self, self.lm.get("Customers.no_devices_title", "No Devices"), self.lm.get("Customers.no_devices_to_export", "No devices to export"))
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, self.lm.get("Customers.save_csv_title", "Save CSV"), f"{self.customer.name}_devices.csv", "CSV Files (*.csv)")
        
        if not path:
            return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    '#', 'Barcode', 'Brand', 'Model', 'Color', 'Serial', 
                    'IMEI', 'Status', 'Condition', 'Received Date'
                ])
                
                for i, device in enumerate(self.devices, 1):
                    writer.writerow([
                        i,
                        device.barcode or '',
                        device.brand or '',
                        device.model or '',
                        device.color or '',
                        device.serial_number or '',
                        device.imei or '',
                        device.status.capitalize(),
                        device.condition or '',
                        device.received_at.strftime('%Y-%m-%d %H:%M') if device.received_at else ''
                    ])
            MessageHandler.show_success(self, self.lm.get("Customers.export_successful_title", "Export Successful"), self.lm.get("Customers.csv_exported_message", "CSV file exported successfully"))
        except Exception as e:
            MessageHandler.show_critical(self, self.lm.get("Customers.export_error_title", "Export Error"), f"{self.lm.get('Customers.failed_to_export_csv', 'Failed to export CSV')}: {str(e)}")
    
    def _export_devices_to_pdf(self):
        """Export customer devices to PDF with professional report styling using WeasyPrint"""
        if not self.devices:
            MessageHandler.show_warning(self, self.lm.get("Customers.no_devices_title", "No Devices"), self.lm.get("Customers.no_devices_to_export", "No devices to export"))
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, self.lm.get("Customers.save_pdf_title", "Save PDF"), f"{self.customer.name}_devices.pdf", "PDF Files (*.pdf)")
        
        if not path:
            return
        
        try:
             # Import WeasyPrint (lazy import)
            import platform
            import os
            
            # MacOS Fix for WeasyPrint
            if platform.system() == 'Darwin':
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
            
            from weasyprint import HTML, CSS
            
            # Use fonts that support Burmese
            font_family = "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"

            # Calculate status summary
            status_counts = {}
            for device in self.devices:
                status = device.status.capitalize()
                status_counts[status] = status_counts.get(status, 0) + 1
            status_summary = ", ".join([f"{k}: {v}" for k, v in status_counts.items()])
            
            html = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4 landscape; margin: 15mm; }}
                    body {{ font-family: {font_family}; color: #333; }}
                    h1 {{ color: #2980B9; margin-bottom: 5px; }}
                    .meta {{ font-size: 10pt; color: #7F8C8D; margin-bottom: 20px; }}
                    
                    /* Summary Box */
                    .summary-container {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .summary-box {{ 
                        border: 1px solid #BDC3C7; 
                        padding: 10px; 
                        background-color: #ECF0F1;
                        border-radius: 4px;
                        flex: 1;
                    }}
                    .summary-label {{ font-size: 9pt; color: #7F8C8D; font-weight: bold; }}
                    .summary-value {{ font-size: 11pt; color: #2C3E50; margin-bottom: 5px; }}
                    
                    /* Table */
                    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
                    th {{ 
                        background-color: #3498DB; 
                        color: white; 
                        padding: 8px; 
                        text-align: left; 
                        border: 1px solid #2980B9;
                    }}
                    td {{ 
                        padding: 6px; 
                        border: 1px solid #BDC3C7; 
                        color: #2C3E50;
                    }}
                    tr:nth-child(even) {{ background-color: #F8F9F9; }}
                    
                    /* Status Colors */
                    .status-completed, .status-repaired {{ color: #27AE60; font-weight: bold; }}
                    .status-repairing {{ color: #E67E22; font-weight: bold; }}
                    .status-received {{ color: #3498DB; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Customers.pdf_report_title", "DEVICE INVENTORY REPORT")}</h1>
                <div class="meta">{self.lm.get('Customers.pdf_customer_label', 'Customer')}: {self.customer.name}</div>
                
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get('Customers.pdf_report_date', 'Report Date')}</div>
                        <div class="summary-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                        <div class="summary-label">{self.lm.get('Customers.pdf_total_devices', 'Total Devices')}</div>
                        <div class="summary-value">{len(self.devices)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get('Customers.pdf_status_summary', 'Status Summary')}</div>
                         <div class="summary-value">{status_summary}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get('Customers.contact_info', 'Contact Info')}</div>
                        <div class="summary-value">{self.lm.get('Customers.phone_label', 'Phone')}: {self.customer.phone or 'N/A'}</div>
                        <div class="summary-value">{self.lm.get('Customers.email_label', 'Email')}: {self.customer.email or 'N/A'}</div>
                    </div>
                </div>
                
                <h3>{self.lm.get("Customers.pdf_device_details", "DEVICE DETAILS")}</h3>
                <table>
                    <thead>
                        <tr>
                            <th width="5%">#</th>
                            <th width="12%">{self.lm.get("Customers.pdf_header_barcode", "Barcode")}</th>
                            <th width="10%">{self.lm.get("Customers.pdf_header_brand", "Brand")}</th>
                            <th width="15%">{self.lm.get("Customers.pdf_header_model", "Model")}</th>
                            <th width="8%">{self.lm.get("Customers.pdf_header_color", "Color")}</th>
                            <th width="15%">{self.lm.get("Customers.pdf_header_serial", "Serial")}</th>
                            <th width="15%">{self.lm.get("Customers.pdf_header_imei", "IMEI")}</th>
                            <th width="10%">{self.lm.get("Customers.pdf_header_status", "Status")}</th>
                            <th width="10%">{self.lm.get("Customers.pdf_header_received", "Received")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for idx, device in enumerate(self.devices, 1):
                bg_color = "#F8F9F9" if idx % 2 == 0 else "#FFFFFF"
                status_class = f"status-{device.status.lower()}"
                received_date = device.received_at.strftime('%Y-%m-%d') if device.received_at else 'N/A'
                
                html += f"""
                    <tr style="background-color: {bg_color};">
                        <td style="text-align: center;">{idx}</td>
                        <td>{device.barcode or ''}</td>
                        <td>{device.brand or ''}</td>
                        <td>{device.model or ''}</td>
                        <td>{device.color or ''}</td>
                        <td>{device.serial_number or ''}</td>
                        <td>{device.imei or ''}</td>
                        <td class="{status_class}" style="text-align: center;">{device.status.capitalize()}</td>
                        <td style="text-align: center;">{received_date}</td>
                    </tr>
                """

            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 20px; font-size: 8pt; color: #7F8C8D; border-top: 1px solid #BDC3C7; padding-top: 10px;">
                    {self.lm.get("Customers.pdf_generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
                    {self.lm.get("Customers.pdf_confidential", "Confidential - For Internal Use Only")}
                </div>
            </body>
            </html>
            """
            
            HTML(string=html).write_pdf(path)
            
            MessageHandler.show_success(self, self.lm.get("Customers.export_successful_title", "Export Successful"), self.lm.get("Customers.pdf_exported_message", "PDF report exported successfully"))
            
        except Exception as e:
            MessageHandler.show_critical(self, self.lm.get("Customers.export_error_title", "Export Error"), f"{self.lm.get('Customers.failed_to_export_pdf', 'Failed to export PDF')}: {str(e)}")

    def _save_notes(self):
        """Save updated notes"""
        if not self.container:
            return
            
        new_notes = self.notes_edit.toPlainText().strip()
        
        # Update customer
        data = {
            'name': self.customer.name,
            'phone': self.customer.phone,
            'email': self.customer.email,
            'address': self.customer.address,
            'notes': new_notes,
            'preferred_contact_method': self.customer.preferred_contact_method,
            'updated_by': self.customer.updated_by # Ideally current user ID
        }
        
        if self.container.customer_controller.update_customer(self.customer.id, data):
            MessageHandler.show_success(self, self.lm.get("Customers.success_title", "Success"), self.lm.get("Customers.notes_updated_message", "Notes updated successfully"))
            # Update local object
            self.customer.notes = new_notes
        else:
            MessageHandler.show_error(self, self.lm.get("Customers.error_title", "Error"), self.lm.get("Customers.failed_to_update_notes", "Failed to update notes"))


