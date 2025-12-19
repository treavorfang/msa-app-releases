import json
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QScrollArea, QTextEdit, QListWidget, QMessageBox, QRadioButton,
    QButtonGroup, QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTime, QDate
from PySide6.QtGui import QIcon

class SettingsWindow(QMainWindow):
    settings_updated = Signal(dict)

    def __init__(self, current_settings=None):
        super().__init__()
        self.setWindowTitle("Repair Shop Settings")
        self.setWindowIcon(QIcon(":/icons/settings.png"))
        self.resize(1100, 750)

        # Initialize with default settings if none provided
        self.current_settings = current_settings or self.get_default_settings()
        self.modified_settings = {}

        # Main container with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.central_widget = QWidget()
        scroll.setWidget(self.central_widget)
        self.setCentralWidget(scroll)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search settings...")
        self.main_layout.addWidget(self.search_bar)

        # Tab widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Create all tabs
        self.create_business_tab()
        self.create_inventory_tab()
        self.create_customer_tab()
        self.create_workflow_tab()
        self.create_ui_tab()
        self.create_system_tab()
        self.create_integrations_tab()
        self.create_hardware_tab()
        self.create_reporting_tab()
        self.create_advanced_tab()

        # View mode selector
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Basic", "Advanced", "Expert"])
        self.view_mode.currentTextChanged.connect(self.update_view_mode)

        # Save/Cancel buttons
        self.button_box = QHBoxLayout()
        self.reset_btn = QPushButton("Reset Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        
        self.button_box.addWidget(self.view_mode)
        self.button_box.addStretch()
        self.button_box.addWidget(self.reset_btn)
        self.button_box.addWidget(self.save_btn)
        self.button_box.addWidget(self.cancel_btn)
        self.main_layout.addLayout(self.button_box)

        # Initialize view mode
        self.update_view_mode("Basic")

    def get_default_settings(self):
        """Return default settings dictionary"""
        return {
            "company_name": "My Repair Shop",
            "company_address": "",
            "company_phone": "",
            "company_email": "",
            "tax_id": "",
            "company_logo": "",
            "tax_rate": 8.0,
            "currency": "$ USD",
            "payment_methods": ["Cash", "Credit Card"],
            "default_warranty_days": 90,
            "low_stock_threshold": 5,
            "reorder_quantity": 10,
            "barcode_enabled": True,
            # ... other default values
        }

    def create_business_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Company Information
        company_group = QGroupBox("Company Information")
        company_layout = QFormLayout()
        
        self.company_name = QLineEdit(self.current_settings["company_name"])
        self.company_address = QTextEdit(self.current_settings["company_address"])
        self.company_phone = QLineEdit(self.current_settings["company_phone"])
        self.company_email = QLineEdit(self.current_settings["company_email"])
        self.tax_id = QLineEdit(self.current_settings["tax_id"])
        self.company_logo = QLineEdit(self.current_settings["company_logo"])
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_logo)
        
        company_layout.addRow("Business Name:", self.company_name)
        company_layout.addRow("Address:", self.company_address)
        company_layout.addRow("Contact Number:", self.company_phone)
        company_layout.addRow("Email:", self.company_email)
        company_layout.addRow("Tax ID/VAT:", self.tax_id)
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.company_logo)
        logo_layout.addWidget(browse_btn)
        company_layout.addRow("Logo:", logo_layout)
        company_group.setLayout(company_layout)

        # Financial Settings
        finance_group = QGroupBox("Financial Settings")
        finance_layout = QFormLayout()
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(self.current_settings["tax_rate"])
        self.tax_rate.setSuffix(" %")
        
        self.currency = QComboBox()
        self.currency.addItems(["$ USD", "€ EUR", "£ GBP", "¥ JPY"])
        self.currency.setCurrentText(self.current_settings["currency"])
        
        self.payment_methods = QListWidget()
        self.payment_methods.addItems(["Cash", "Credit Card", "Bank Transfer", "Check"])
        for i in range(self.payment_methods.count()):
            item = self.payment_methods.item(i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if item.text() in self.current_settings["payment_methods"] else Qt.Unchecked)
        
        finance_layout.addRow("Default Tax Rate:", self.tax_rate)
        finance_layout.addRow("Currency Symbol:", self.currency)
        finance_layout.addRow("Payment Methods:", self.payment_methods)
        finance_group.setLayout(finance_layout)

        # Repair Defaults
        repair_group = QGroupBox("Repair Defaults")
        repair_layout = QFormLayout()
        
        self.default_warranty = QSpinBox()
        self.default_warranty.setRange(0, 365)
        self.default_warranty.setValue(self.current_settings["default_warranty_days"])
        self.default_warranty.setSuffix(" days")
        
        self.default_priority = QComboBox()
        self.default_priority.addItems(["Low", "Medium", "High", "Urgent"])
        
        repair_layout.addRow("Default Warranty Period:", self.default_warranty)
        repair_layout.addRow("Default Repair Priority:", self.default_priority)
        repair_group.setLayout(repair_layout)

        layout.addWidget(company_group)
        layout.addWidget(finance_group)
        layout.addWidget(repair_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Business")

    def create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Stock Settings
        stock_group = QGroupBox("Stock Settings")
        stock_layout = QFormLayout()
        
        self.low_stock = QSpinBox()
        self.low_stock.setRange(1, 1000)
        self.low_stock.setValue(self.current_settings["low_stock_threshold"])
        
        self.reorder_qty = QSpinBox()
        self.reorder_qty.setRange(1, 1000)
        self.reorder_qty.setValue(self.current_settings["reorder_quantity"])
        
        self.barcode_scan = QCheckBox()
        self.barcode_scan.setChecked(self.current_settings["barcode_enabled"])
        
        stock_layout.addRow("Low Stock Threshold:", self.low_stock)
        stock_layout.addRow("Reorder Quantity:", self.reorder_qty)
        stock_layout.addRow("Barcode Scanning:", self.barcode_scan)
        stock_group.setLayout(stock_layout)

        # Parts Pricing
        pricing_group = QGroupBox("Parts Pricing")
        pricing_layout = QFormLayout()
        
        self.default_markup = QDoubleSpinBox()
        self.default_markup.setRange(0, 500)
        self.default_markup.setValue(30)
        self.default_markup.setSuffix(" %")
        
        pricing_layout.addRow("Default Markup Percentage:", self.default_markup)
        pricing_group.setLayout(pricing_layout)

        layout.addWidget(stock_group)
        layout.addWidget(pricing_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Inventory")

    def create_customer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Customer Defaults
        customer_group = QGroupBox("Customer Defaults")
        customer_layout = QFormLayout()
        
        self.required_fields = QListWidget()
        self.required_fields.addItems(["Name", "Phone", "Email", "Address"])
        for i in range(self.required_fields.count()):
            item = self.required_fields.item(i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
        
        self.comm_method = QComboBox()
        self.comm_method.addItems(["Email", "SMS", "Both"])
        
        customer_layout.addRow("Required Fields:", self.required_fields)
        customer_layout.addRow("Default Communication:", self.comm_method)
        customer_group.setLayout(customer_layout)

        # Privacy Settings
        privacy_group = QGroupBox("Privacy Settings")
        privacy_layout = QFormLayout()
        
        self.data_retention = QSpinBox()
        self.data_retention.setRange(0, 3650)
        self.data_retention.setValue(365)
        self.data_retention.setSuffix(" days")
        
        privacy_layout.addRow("Data Retention Period:", self.data_retention)
        privacy_group.setLayout(privacy_layout)

        layout.addWidget(customer_group)
        layout.addWidget(privacy_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Customers")

    def create_workflow_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Ticket Automation
        ticket_group = QGroupBox("Ticket Automation")
        ticket_layout = QFormLayout()
        
        self.auto_status = QCheckBox("Automatic status changes")
        self.auto_status.setChecked(True)
        
        self.default_tech = QComboBox()
        self.default_tech.addItems(["None", "Tech 1", "Tech 2", "Tech 3"])
        
        ticket_layout.addRow(self.auto_status)
        ticket_layout.addRow("Default Technician:", self.default_tech)
        ticket_group.setLayout(ticket_layout)

        # Notification Settings
        notify_group = QGroupBox("Notification Settings")
        notify_layout = QFormLayout()
        
        self.notify_new_ticket = QCheckBox("New tickets")
        self.notify_new_ticket.setChecked(True)
        
        self.notify_status_change = QCheckBox("Status changes")
        self.notify_status_change.setChecked(True)
        
        notify_layout.addRow(self.notify_new_ticket)
        notify_layout.addRow(self.notify_status_change)
        notify_group.setLayout(notify_layout)

        layout.addWidget(ticket_group)
        layout.addWidget(notify_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Workflow")

    def create_ui_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Display Preferences
        display_group = QGroupBox("Display Preferences")
        display_layout = QFormLayout()
        
        self.theme = QComboBox()
        self.theme.addItems(["Light", "Dark", "System"])
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        
        display_layout.addRow("Theme:", self.theme)
        display_layout.addRow("Font Size:", self.font_size)
        display_group.setLayout(display_layout)

        # Data Presentation
        data_group = QGroupBox("Data Presentation")
        data_layout = QFormLayout()
        
        self.date_format = QComboBox()
        self.date_format.addItems(["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"])
        
        data_layout.addRow("Date Format:", self.date_format)
        data_group.setLayout(data_layout)

        layout.addWidget(display_group)
        layout.addWidget(data_group)
        layout.addStretch()
        self.tabs.addTab(tab, "UI")

    def create_system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # User Management
        user_group = QGroupBox("User Management")
        user_layout = QFormLayout()
        
        self.password_min = QSpinBox()
        self.password_min.setRange(4, 20)
        self.password_min.setValue(8)
        
        self.session_timeout = QSpinBox()
        self.session_timeout.setRange(5, 240)
        self.session_timeout.setValue(30)
        self.session_timeout.setSuffix(" minutes")
        
        user_layout.addRow("Minimum Password Length:", self.password_min)
        user_layout.addRow("Session Timeout:", self.session_timeout)
        user_group.setLayout(user_layout)

        # Data Management
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout()
        
        self.auto_backup = QCheckBox("Automatic Backups")
        self.auto_backup.setChecked(True)
        
        self.backup_freq = QComboBox()
        self.backup_freq.addItems(["Daily", "Weekly", "Monthly"])
        
        data_layout.addRow(self.auto_backup)
        data_layout.addRow("Backup Frequency:", self.backup_freq)
        data_group.setLayout(data_layout)

        layout.addWidget(user_group)
        layout.addWidget(data_group)
        layout.addStretch()
        self.tabs.addTab(tab, "System")

    def create_integrations_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Email Settings
        email_group = QGroupBox("Email Integration")
        email_layout = QFormLayout()
        
        self.smtp_server = QLineEdit("smtp.example.com")
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        
        email_layout.addRow("SMTP Server:", self.smtp_server)
        email_layout.addRow("SMTP Port:", self.smtp_port)
        email_group.setLayout(email_layout)

        layout.addWidget(email_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Integrations")

    def create_hardware_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Peripheral Settings
        peripheral_group = QGroupBox("Peripheral Settings")
        peripheral_layout = QFormLayout()
        
        self.receipt_printer = QComboBox()
        self.receipt_printer.addItems(["Default", "Epson TM-T20", "Star TSP100"])
        
        peripheral_layout.addRow("Receipt Printer:", self.receipt_printer)
        peripheral_group.setLayout(peripheral_layout)

        layout.addWidget(peripheral_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Hardware")

    def create_reporting_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Report Defaults
        report_group = QGroupBox("Report Defaults")
        report_layout = QFormLayout()
        
        self.report_period = QComboBox()
        self.report_period.addItems(["Daily", "Weekly", "Monthly", "Quarterly"])
        
        self.report_format = QComboBox()
        self.report_format.addItems(["PDF", "Excel", "CSV"])
        
        report_layout.addRow("Default Report Period:", self.report_period)
        report_layout.addRow("Default Format:", self.report_format)
        report_group.setLayout(report_layout)

        layout.addWidget(report_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Reporting")

    def create_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Diagnostics
        diag_group = QGroupBox("Diagnostics")
        diag_layout = QFormLayout()
        
        self.log_level = QComboBox()
        self.log_level.addItems(["Debug", "Info", "Warning", "Error"])
        
        diag_layout.addRow("Logging Level:", self.log_level)
        diag_group.setLayout(diag_layout)

        layout.addWidget(diag_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Advanced")

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Company Logo",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.company_logo.setText(file_path)

    def update_view_mode(self, mode):
        """Show/hide advanced settings based on view mode"""
        # Implementation would show/hide advanced widgets
        pass

    def reset_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_settings = self.get_default_settings()
            # Need to update all UI elements to reflect defaults
            self.company_name.setText(self.current_settings["company_name"])
            # ... update all other widgets similarly

    def save_settings(self):
        """Collect all settings from UI and emit signal"""
        self.modified_settings = {
            "company_name": self.company_name.text(),
            "company_address": self.company_address.toPlainText(),
            "company_phone": self.company_phone.text(),
            "company_email": self.company_email.text(),
            "tax_id": self.tax_id.text(),
            "company_logo": self.company_logo.text(),
            "tax_rate": self.tax_rate.value(),
            "currency": self.currency.currentText(),
            "payment_methods": [self.payment_methods.item(i).text() 
                              for i in range(self.payment_methods.count()) 
                              if self.payment_methods.item(i).checkState() == Qt.Checked],
            "default_warranty_days": self.default_warranty.value(),
            "low_stock_threshold": self.low_stock.value(),
            "reorder_quantity": self.reorder_qty.value(),
            "barcode_enabled": self.barcode_scan.isChecked(),
            # ... collect all other settings
        }
        self.settings_updated.emit(self.modified_settings)
        self.close()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    # Example usage
    def handle_settings_update(new_settings):
        print("Settings saved:", new_settings)
        # In real app, save to file/database here
        with open("settings.json", "w") as f:
            json.dump(new_settings, f, indent=2)

    window = SettingsWindow()
    window.settings_updated.connect(handle_settings_update)
    window.show()
    
    sys.exit(app.exec())