
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLabel, QLineEdit, QComboBox, QDialogButtonBox, 
                               QDateEdit, QGroupBox, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta

from core import (DURATION_OPTIONS, DEFAULT_DURATION_INDEX, PRICING_MAP_MMK, PRICING_MAP_USD, 
                  CURRENCY_OPTIONS, PAYMENT_METHOD_OPTIONS, PAYMENT_STATUS_OPTIONS,
                  LIFETIME_EXPIRY)
from .styles import DIALOG_STYLE, GROUP_BOX_STYLE

class OnlineActivationDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle(f"Activate User: {user_data.get('name', 'Unknown')}")
        self.setFixedWidth(500)
        
        self.result_data = None
        
        self.base_price = 0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. User Info (Read Only)
        info_group = QGroupBox("User Information")
        info_layout = QFormLayout()
        
        self.lbl_name = QLabel(self.user_data.get('name', 'N/A'))
        self.lbl_email = QLabel(self.user_data.get('email', 'N/A'))
        self.lbl_hwid = QLabel(self.user_data.get('hwid', 'N/A'))
        self.lbl_hwid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        info_layout.addRow("Name:", self.lbl_name)
        info_layout.addRow("Email:", self.lbl_email)
        info_layout.addRow("HWID:", self.lbl_hwid)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 2. License Configuration
        lic_group = QGroupBox("License Configuration")
        lic_layout = QFormLayout()
        
        self.combo_duration = QComboBox()
        for label, days in DURATION_OPTIONS:
            self.combo_duration.addItem(label, days)
        self.combo_duration.setCurrentIndex(DEFAULT_DURATION_INDEX)
        self.combo_duration.currentIndexChanged.connect(self._update_expiry_and_price)
        
        self.date_expiry = QDateEdit()
        self.date_expiry.setCalendarPopup(True)
        self.date_expiry.setDisplayFormat("MMM d, yyyy")
        
        lic_layout.addRow("Duration:", self.combo_duration)
        lic_layout.addRow("Expires On:", self.date_expiry)
        lic_group.setLayout(lic_layout)
        layout.addWidget(lic_group)
        
        # 3. Invoice / Payment
        inv_group = QGroupBox("Invoice & Payment")
        inv_layout = QFormLayout()
        
        # Currency & Amount
        amt_container = QWidget()
        amt_layout = QHBoxLayout(amt_container)
        amt_layout.setContentsMargins(0,0,0,0)
        
        self.combo_currency = QComboBox()
        self.combo_currency.addItems(CURRENCY_OPTIONS)
        self.combo_currency.currentIndexChanged.connect(self._update_expiry_and_price)
        
        self.input_amount = QLineEdit()
        
        amt_layout.addWidget(self.input_amount)
        amt_layout.addWidget(self.combo_currency)
        
        # Invoice No
        self.input_invoice = QLineEdit()
        self.input_invoice.setPlaceholderText("Auto-generated if empty")
        
        # Payment Method
        self.combo_method = QComboBox()
        self.combo_method.addItems(PAYMENT_METHOD_OPTIONS)
        
        # Payment Status
        self.combo_status = QComboBox()
        self.combo_status.addItems(PAYMENT_STATUS_OPTIONS)
        self.combo_status.setCurrentText("Paid") # Default to Paid for activation
        
        inv_layout.addRow("Invoice #:", self.input_invoice)
        inv_layout.addRow("Amount:", amt_container)
        
        # Discount
        disc_container = QWidget()
        disc_layout = QHBoxLayout(disc_container)
        disc_layout.setContentsMargins(0,0,0,0)
        
        self.input_discount = QLineEdit()
        self.input_discount.setPlaceholderText("0")
        self.input_discount.textChanged.connect(self._recalc_total)
        
        self.combo_discount_type = QComboBox()
        self.combo_discount_type.addItems(["Fixed", "%"])
        self.combo_discount_type.setFixedWidth(80)
        self.combo_discount_type.currentIndexChanged.connect(self._recalc_total)
        
        disc_layout.addWidget(self.input_discount)
        disc_layout.addWidget(self.combo_discount_type)
        
        inv_layout.addRow("Discount:", disc_container)
        
        inv_layout.addRow("Method:", self.combo_method)
        inv_layout.addRow("Status:", self.combo_status)
        
        inv_group.setLayout(inv_layout)
        layout.addWidget(inv_group)
        
        # Apply Styles
        self.setStyleSheet(DIALOG_STYLE + GROUP_BOX_STYLE)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        # Trigger initial calc
        self._update_expiry_and_price()
        
    def _update_expiry_and_price(self):
        duration_days = self.combo_duration.currentData()
        duration_label = self.combo_duration.currentText()
        currency = self.combo_currency.currentText()
        
        # Calc Expiry
        today = QDate.currentDate()
        if duration_days == -1: # Lifetime
            # Handle lifetime logic if needed, usually just far future
            self.date_expiry.setDate(QDate.fromString(LIFETIME_EXPIRY, "yyyy-MM-dd"))
        else:
            self.date_expiry.setDate(today.addDays(duration_days))
            
        # Calc Base Price
        if currency == "MMK":
            price = PRICING_MAP_MMK.get(duration_label, 0)
        else:
            price = PRICING_MAP_USD.get(duration_label, 0)
        
        self.base_price = price
        self._recalc_total()

    def _recalc_total(self):
        try:
            discount_val = float(self.input_discount.text() or 0)
        except ValueError:
            discount_val = 0
            
        discount_type = self.combo_discount_type.currentText()
        currency = self.combo_currency.currentText()
        
        final_price = self.base_price
        
        if discount_type == "%":
            final_price = self.base_price * (1 - (discount_val / 100))
        else:
            final_price = self.base_price - discount_val
            
        if final_price < 0: final_price = 0
        
        if currency == "MMK":
            self.input_amount.setText(f"{final_price:,.0f}")
        else:
            self.input_amount.setText(f"{final_price:,.2f}")

    def _on_accept(self):
        # Validate and package data
        expiry_qdate = self.date_expiry.date()
        expiry_str = expiry_qdate.toString("yyyy-MM-dd")
        
        self.result_data = {
            "status": "active",
            "expiration_date": expiry_str,
            "license_type": self.combo_duration.currentText(),
            "activated_at": datetime.now().isoformat(),
            "invoice_details": {
                "invoice_number": self.input_invoice.text().strip() or f"INV-{datetime.now().strftime('%Y%m%d%H%M')}",
                "amount": f"{self.combo_currency.currentText()} {self.input_amount.text()}",
                "discount": f"{self.input_discount.text() or '0'} {self.combo_discount_type.currentText()}",
                "payment_method": self.combo_method.currentText(),
                "payment_status": self.combo_status.currentText(),
            },
            # Add user fields to be safe for Invoice Generator
            # Add user fields to be safe for Invoice Generator
            "customer_name": self.user_data.get('name'), # use customer_name for invoice generator
            "name": self.user_data.get('name'),
            "email": self.user_data.get('email'),
            "phone": self.user_data.get('phone', 'N/A'),
            "city": self.user_data.get('city', 'N/A'),
            "country": self.user_data.get('country', 'N/A'),
            "hwid": self.user_data.get('hwid', 'N/A'),
            "renewal_reminder": self.date_expiry.date().addDays(-30).toString("yyyy-MM-dd"), # 30 days before
            "notes": "Online Activation"
        }
        self.accept()
