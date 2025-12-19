"""
Main window for License Generator - Final Compact Design with Tabs
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
                              QMessageBox, QFrame, QComboBox, QApplication, QDateEdit,
                              QFileDialog, QTabWidget)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QFont

from core import (LicenseGeneratorCore, HistoryManager, DURATION_OPTIONS, 
                 DEFAULT_DURATION_INDEX, LOGO_PATH, PAYMENT_STATUS_OPTIONS,
                 PAYMENT_METHOD_OPTIONS, PRICING_MAP_MMK, PRICING_MAP_USD, CURRENCY_OPTIONS)
from core.license_invoice_generator import LicenseInvoiceGenerator
from .styles import (MAIN_WINDOW_STYLE, COMBOBOX_STYLE, GENERATE_BUTTON_STYLE, 
                     HISTORY_BUTTON_STYLE, GROUP_BOX_STYLE, TAB_STYLE)
from .history_dialog import HistoryView 


class LicenseGeneratorWindow(QMainWindow):
    """Main application window - Compact Professional Design"""
    
    def __init__(self):
        super().__init__()
        self.generator = LicenseGeneratorCore()
        self.history = HistoryManager()
        self.invoice_generator = LicenseInvoiceGenerator()
        self.invoice_counter = self._get_next_invoice_number()
        
        self.setWindowTitle("MSA License Generator")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        self._setup_ui()
        self._check_private_key()
    
    def _get_next_invoice_number(self):
        """Generate next invoice number"""
        today = datetime.now()
        return f"INV-{today.strftime('%Y')}-{today.strftime('%m%d')}-001"
    
    def _setup_ui(self):
        """Setup compact professional UI with Tabs"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header (Common)
        layout.addLayout(self._create_header())
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        
        # Tab 1: Generator
        self.generator_tab = QWidget()
        self._setup_generator_tab(self.generator_tab)
        self.tabs.addTab(self.generator_tab, "📝 Generate License")
        
        # Tab 2: Dashboard (History)
        self.history_tab = HistoryView()
        self.tabs.addTab(self.history_tab, "📊 Customer Dashboard")
        
        layout.addWidget(self.tabs)
        
        self.statusBar().showMessage("Ready")
        
        # Verify initial amount
        self._update_amount()
    
    def _create_header(self):
        """Create compact header"""
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        
        layout = QHBoxLayout()
        layout.setSpacing(5)
        
        # Logo
        if os.path.exists(LOGO_PATH):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO_PATH)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label)
        
        # Title
        title = QLabel("License Generator System")
        title.setFont(header_font)
        title.setStyleSheet("color: #3b82f6; font-size: 18px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Date
        today = QLabel(QDate.currentDate().toString("MMM d, yyyy"))
        today.setFont(header_font)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(today)
        
        return layout
    
    def _setup_generator_tab(self, tab):
        """Setup the generator tab content"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Row 1: Customer & License Info
        # We can reuse the existing method which returns a widget containing both side-by-side
        # OR we can split them if we want more control. 
        # Currently _create_customer_license_section creates a widget with a GridLayout(0,0 -> Customer, 0,1 -> License)
        # This is already perfect for Row 1!
        layout.addWidget(self._create_customer_license_section())
        
        # Row 2: Invoice Info & Generated Key
        # We need to construct a similar side-by-side widget for these two
        layout.addWidget(self._create_invoice_output_section())
        
        # Actions
        layout.addLayout(self._create_action_buttons())
        
        layout.addStretch()

    def _create_customer_license_section(self):
        """Create customer and license sections side by side"""
        widget = QWidget()
        main_layout = QGridLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Customer Information (Left)
        main_layout.addWidget(self._create_customer_group(), 0, 0)
        
        # License Configuration (Right)
        main_layout.addWidget(self._create_license_group(), 0, 1)
        
        return widget

    def _create_invoice_output_section(self):
        """Create Invoice and Output sections side by side"""
        widget = QWidget()
        main_layout = QGridLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Invoice Information (Left)
        main_layout.addWidget(self._create_invoice_group(), 0, 0)
        
        # Generated Key (Right)
        # We want the output box to match height, so we might need to adjust it
        main_layout.addWidget(self._create_output_group(), 0, 1)
        
        return widget

    def _create_customer_group(self):
        """Create styling Customer Group"""
        group = QGroupBox("CUSTOMER INFORMATION")
        group.setStyleSheet(GROUP_BOX_STYLE)
        layout = QGridLayout()
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        
        label_width = 70
        
        row = 0
        name_label = QLabel("Name *")
        name_label.setMinimumWidth(label_width)
        layout.addWidget(name_label, row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("John Doe")
        layout.addWidget(self.name_input, row, 1)
        
        row += 1
        email_label = QLabel("Email")
        email_label.setMinimumWidth(label_width)
        layout.addWidget(email_label, row, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("john@example.com")
        layout.addWidget(self.email_input, row, 1)
        
        row += 1
        phone_label = QLabel("Phone")
        phone_label.setMinimumWidth(label_width)
        layout.addWidget(phone_label, row, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1 234 567 8900")
        layout.addWidget(self.phone_input, row, 1)
        
        row += 1
        city_label = QLabel("City")
        city_label.setMinimumWidth(label_width)
        layout.addWidget(city_label, row, 0)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Yangon")
        layout.addWidget(self.city_input, row, 1)
        
        row += 1
        country_label = QLabel("Country")
        country_label.setMinimumWidth(label_width)
        layout.addWidget(country_label, row, 0)
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("Myanmar")
        layout.addWidget(self.country_input, row, 1)
        
        group.setLayout(layout)
        return group

    def _create_license_group(self):
        """Create styling License Group"""
        group = QGroupBox("LICENSE CONFIGURATION")
        group.setStyleSheet(GROUP_BOX_STYLE)
        layout = QGridLayout()
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        
        label_width = 70
        
        row = 0
        hwid_label = QLabel("HWID *")
        hwid_label.setMinimumWidth(label_width)
        layout.addWidget(hwid_label, row, 0)
        self.hwid_input = QLineEdit()
        self.hwid_input.setPlaceholderText("Machine Fingerprint")
        layout.addWidget(self.hwid_input, row, 1)
        
        row += 1
        duration_label = QLabel("Duration *")
        duration_label.setMinimumWidth(label_width)
        layout.addWidget(duration_label, row, 0)
        self.duration_combo = QComboBox()
        for label, days in DURATION_OPTIONS:
            self.duration_combo.addItem(label, days)
        self.duration_combo.setCurrentIndex(DEFAULT_DURATION_INDEX)
        self.duration_combo.setStyleSheet(COMBOBOX_STYLE)
        self.duration_combo.currentIndexChanged.connect(self._update_amount)
        layout.addWidget(self.duration_combo, row, 1)
        
        row += 1
        renewal_label = QLabel("Renewal")
        renewal_label.setMinimumWidth(label_width)
        layout.addWidget(renewal_label, row, 0)
        self.renewal_date = QDateEdit()
        self.renewal_date.setCalendarPopup(True)
        self.renewal_date.setDate(QDate.currentDate().addYears(1))
        self.renewal_date.setDisplayFormat("MMM d, yyyy")
        layout.addWidget(self.renewal_date, row, 1)
        
        # Add a stretch to align items to top
        layout.setRowStretch(3, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_invoice_group(self):
        """Create Invoice information section"""
        group = QGroupBox("INVOICE INFORMATION")
        group.setStyleSheet(GROUP_BOX_STYLE)
        layout = QGridLayout()
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        
        label_width = 70
        
        # Row 1: Invoice & Amount
        invoice_label = QLabel("Invoice #")
        invoice_label.setMinimumWidth(label_width)
        layout.addWidget(invoice_label, 0, 0)
        self.invoice_input = QLineEdit()
        self.invoice_input.setText(self.invoice_counter)
        self.invoice_input.setReadOnly(True)
        self.invoice_input.setStyleSheet("background-color: #1e293b;")
        layout.addWidget(self.invoice_input, 0, 1)
        
        # Row 2: Currency & Amount
        currency_label = QLabel("Currency")
        currency_label.setMinimumWidth(label_width)
        layout.addWidget(currency_label, 1, 0)
        
        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(5)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(CURRENCY_OPTIONS)
        self.currency_combo.setStyleSheet(COMBOBOX_STYLE)
        self.currency_combo.setFixedWidth(80)
        self.currency_combo.currentIndexChanged.connect(self._update_amount)
        amount_layout.addWidget(self.currency_combo)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        amount_layout.addWidget(self.amount_input)
        
        layout.addLayout(amount_layout, 1, 1)
        
        # Row 3: Method
        method_label = QLabel("Method")
        method_label.setMinimumWidth(label_width)
        layout.addWidget(method_label, 2, 0)
        self.payment_method_combo = QComboBox()
        for method in PAYMENT_METHOD_OPTIONS:
            self.payment_method_combo.addItem(method)
        self.payment_method_combo.setStyleSheet(COMBOBOX_STYLE)
        layout.addWidget(self.payment_method_combo, 2, 1)

        # Row 4: Status
        status_label = QLabel("Status")
        status_label.setMinimumWidth(label_width)
        layout.addWidget(status_label, 3, 0)
        self.payment_status_combo = QComboBox()
        for status in PAYMENT_STATUS_OPTIONS:
            self.payment_status_combo.addItem(status)
        self.payment_status_combo.setStyleSheet(COMBOBOX_STYLE)
        layout.addWidget(self.payment_status_combo, 3, 1)

        # Row 5: Notes
        notes_label = QLabel("Notes")
        notes_label.setMinimumWidth(label_width)
        layout.addWidget(notes_label, 4, 0)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Special notes...")
        layout.addWidget(self.notes_input, 4, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_output_group(self):
        """Create output section"""
        group = QGroupBox("GENERATED LICENSE KEY")
        group.setStyleSheet(GROUP_BOX_STYLE)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 20, 12, 12)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("License key will appear here...")
        # Make it fill the available height to match the neighbor
        self.output_area.setStyleSheet("font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.output_area)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # Generate License Key button
        self.generate_btn = QPushButton("🔑 Generate License Key")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self._generate_license)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet(GENERATE_BUTTON_STYLE)
        layout.addWidget(self.generate_btn)
        
        # Copy Button
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setObjectName("copyButton")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.copy_btn.setMinimumHeight(40)
        layout.addWidget(self.copy_btn)
        
        # Save to PDF button
        self.pdf_btn = QPushButton("💾 Save to PDF")
        self.pdf_btn.setCursor(Qt.PointingHandCursor)
        self.pdf_btn.clicked.connect(self._save_to_pdf)
        self.pdf_btn.setMinimumHeight(40)
        self.pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        layout.addWidget(self.pdf_btn)
        
        # Note: History button removed as it's now a tab
        
        return layout
    
    def _update_amount(self):
        """Auto-populate amount based on selected duration and currency"""
        if not hasattr(self, 'duration_combo') or not hasattr(self, 'currency_combo'):
            return
            
        duration_text = self.duration_combo.currentText()
        currency = self.currency_combo.currentText()
        
        if currency == "MMK":
            price = PRICING_MAP_MMK.get(duration_text, 0)
            self.amount_input.setText(f"{price:,}")
        else: # USD
            price = PRICING_MAP_USD.get(duration_text, 0)
            self.amount_input.setText(f"{price:.2f}")
            
    def _check_private_key(self):
        """Check if private key exists"""
        try:
            if not self.generator.is_key_loaded():
                QMessageBox.critical(self, "Error", "Private key not found.\n\nPlease run 'generate_keys.py' first.")
                self.generate_btn.setEnabled(False)
                self.statusBar().showMessage("Error: Private key missing")
            else:
                self.statusBar().showMessage("✓ Ready to generate licenses")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load private key:\n{str(e)}")
    
    def _generate_license(self):
        """Generate license with all information"""
        name = self.name_input.text().strip()
        hwid = self.hwid_input.text().strip()
        duration_days = self.duration_combo.currentData()
        
        try:
            # Generate license
            license_data = self.generator.generate(name, hwid, duration_days)
            
            # Add all optional fields
            license_data['email'] = self.email_input.text().strip()
            license_data['phone'] = self.phone_input.text().strip()
            license_data['city'] = self.city_input.text().strip()
            license_data['country'] = self.country_input.text().strip()
            license_data['license_type'] = self.duration_combo.currentText()
            license_data['invoice_number'] = self.invoice_input.text().strip()
            
            # Save Currency and Amount
            currency = self.currency_combo.currentText()
            raw_amount = self.amount_input.text().strip()
            # Combine formatting: "USD 50.00" or "MMK 200,000"
            license_data['amount'] = f"{currency} {raw_amount}"
            
            license_data['payment_method'] = self.payment_method_combo.currentText()
            license_data['payment_status'] = self.payment_status_combo.currentText()
            license_data['renewal_reminder'] = self.renewal_date.date().toString("yyyy-MM-dd")
            license_data['notes'] = self.notes_input.text().strip()
            
            # Store for PDF generation
            self.current_license_data = license_data
            
            # Display
            self.output_area.setText(license_data['license_key'])
            self.statusBar().showMessage("✓ License generated successfully!")
            
            # Save to History
            self.history.save_license(license_data)
            
            # Trigger History Refresh via Tab switch or direct call?
            # It will auto refresh when user clicks the History tab because of showEvent
            
            # Update invoice number
            self.invoice_counter = self._increment_invoice_number(self.invoice_counter)
            self.invoice_input.setText(self.invoice_counter)
            
            QMessageBox.information(self, "Success", f"License generated for {name}!")
            
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate license:\n{str(e)}")
    
    def _increment_invoice_number(self, current):
        """Increment invoice number"""
        parts = current.split('-')
        if len(parts) == 4:
            num = int(parts[3]) + 1
            return f"{parts[0]}-{parts[1]}-{parts[2]}-{num:03d}"
        return current
    
    def _copy_to_clipboard(self):
        """Copy license key to clipboard"""
        key = self.output_area.toPlainText()
        if key:
            clipboard = QApplication.clipboard()
            clipboard.setText(key)
            self.statusBar().showMessage("✓ Copied to clipboard!")
        else:
            QMessageBox.warning(self, "Empty", "No license key to copy.")
    
    def _save_to_pdf(self):
        """Save license invoice to PDF using ReportLab"""
        if not hasattr(self, 'current_license_data'):
            QMessageBox.warning(self, "No License", "Please generate a license first.")
            return
        
        # Ask where to save
        default_filename = f"License_Invoice_{self.current_license_data.get('invoice_number', 'INV')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save License Invoice",
            os.path.join(os.path.expanduser("~"), "Desktop", default_filename),
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                self.invoice_generator.generate_pdf(self.current_license_data, file_path)
                QMessageBox.information(self, "Success", f"Invoice saved to:\n{file_path}")
                self.statusBar().showMessage(f"✓ Saved to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{str(e)}")
