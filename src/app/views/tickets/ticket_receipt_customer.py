# src/app/views/tickets/ticket_receipt_customer.py
from views.components.customer_input import CustomerInput
from utils.validation.input_validator import InputValidator
from utils.validation.phone_formatter import phone_formatter
from utils.language_manager import language_manager

class TicketReceiptCustomer:
    def __init__(self, ticket_receipt):
        self.ticket_receipt = ticket_receipt
        self.lm = language_manager
        self._create_widgets()
    
    def _create_widgets(self):
        """Create customer-related widgets"""
        self.customer_search = CustomerInput()
        self.customer_name = self._create_line_edit(self.lm.get("Customers.ph_customer_name", "Enter full name"))
        self.customer_phone = self._create_line_edit(self.lm.get("Customers.ph_customer_phone", "e.g. +95 9 111 2222 (Myanmar)"))
        self.customer_email = self._create_line_edit(self.lm.get("Customers.ph_customer_email", "example@domain.com"))
        self.customer_address = self._create_line_edit(self.lm.get("Customers.ph_customer_address", "Address"))
        self.customer_note = self._create_line_edit(self.lm.get("Customers.ph_customer_note", "Notes..."))
    
    def _create_line_edit(self, placeholder="", max_length=None):
        """Helper to create consistent line edits"""
        from PySide6.QtWidgets import QLineEdit
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        if max_length:
            line_edit.setMaxLength(max_length)
        return line_edit
    
    def create_customer_device_section(self):
        """Create and return the customer/device section"""
        from PySide6.QtWidgets import QFrame, QGridLayout, QGroupBox, QFormLayout, QLabel
        
        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        layout = QGridLayout(section)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Customer Information
        customer_group = QGroupBox(self.lm.get("Tickets.customer_info", "CUSTOMER INFORMATION"))
        customer_layout = QFormLayout(customer_group)
        
        customer_layout.addRow(self.customer_search)
        customer_layout.addRow(self.customer_name)
        customer_layout.addRow(self.customer_phone)
        customer_layout.addRow(self.customer_email)
        customer_layout.addRow(self.customer_address)
        customer_layout.addRow(self.customer_note)
        
        # Add device section from device module
        device_group = self.ticket_receipt.device_section.create_device_group()
        
        layout.addWidget(customer_group, 0, 0)
        layout.addWidget(device_group, 0, 1)
        
        return section
    
    def connect_signals(self):
        """Connect customer-related signals"""
        self.customer_search.customer_combo.currentIndexChanged.connect(
            self.fill_customer_details
        )
        self.customer_name.textChanged.connect(self.validate_name_field)
        self.customer_phone.textChanged.connect(self.validate_phone_field)
        self.customer_email.textChanged.connect(self.validate_email_field)
    
    def fill_customer_details(self):
        """Fill customer details when a customer is selected"""
        customer_id = self.customer_search.customer_combo.currentData()
        if not customer_id:
            self.clear_customer_fields()
            return
            
        customer = self.ticket_receipt.customer_service.get_customer(customer_id)
        if customer:
            self.customer_name.setText(customer.name)
            self.customer_phone.setText(customer.phone)
            self.customer_email.setText(customer.email or "")
            self.customer_address.setText(customer.address or "")
            self.customer_note.setText(customer.notes or "")
    
    def clear_customer_fields(self):
        """Clear all customer fields"""
        self.customer_name.clear()
        self.customer_phone.clear()
        self.customer_email.clear()
        self.customer_address.clear()
        self.customer_note.clear()
    
    def validate_silent(self) -> bool:
        """Validate customer without showing error messages"""
        customer_id = self.customer_search.customer_combo.currentData()
        if customer_id:
            return True
            
        name = self.customer_name.text().strip()
        phone = self.customer_phone.text().strip()
        email = self.customer_email.text().strip()
        
        if not name or not InputValidator.validate_name(name):
            return False
        
        if not phone or not InputValidator.validate_phone(phone):
            return False
        
        if email and not InputValidator.validate_email(email):
            return False
        
        return True
    
    def validate_name_field(self):
        """Validate and style the name field"""
        name = self.customer_name.text().strip()
        name_valid = bool(name) and InputValidator.validate_name(name)
        self.customer_name.setStyleSheet("border: 1px solid red;" if not name_valid else "")

    def validate_phone_field(self):
        """Validate, format, and style the phone field"""
        phone = self.customer_phone.text().strip()
        phone_valid = bool(phone) and InputValidator.validate_phone(phone)
        self.customer_phone.setStyleSheet("border: 1px solid red;" if not phone_valid else "")
        
        if phone_valid:
            formatted = phone_formatter.format_phone_number(phone)
            if formatted != phone:
                self.customer_phone.blockSignals(True)
                self.customer_phone.setText(formatted)
                self.customer_phone.blockSignals(False)

    def validate_email_field(self):
        email = self.customer_email.text()
        if email:
            is_valid, _ = InputValidator.validate_email(email)
            self.customer_email.setStyleSheet("border: 1px solid red;" if not is_valid else "")
    
    def get_customer_data(self):
        """Get customer data for submission"""
        customer_id = self.customer_search.customer_combo.currentData()
        if customer_id:
            return {'customer_id': customer_id}
            
        return {
            'name': self.customer_name.text(),
            'phone': self.customer_phone.text(),
            'email': self.customer_email.text() or None,
            'address': self.customer_address.text() or None,
            'notes': self.customer_note.text() or None,
            'created_by': self.ticket_receipt.user_id
        }