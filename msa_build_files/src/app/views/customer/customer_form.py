# src/app/views/customer/customer_form.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QDialogButtonBox, QTextEdit, QMessageBox,
    QGroupBox
)
from utils.validation.input_validator import InputValidator
from utils.validation.phone_formatter import phone_formatter
from utils.language_manager import language_manager

class CustomerForm(QDialog):
    def __init__(self, controller, user_id: int, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.user_id = user_id
        self.lm = language_manager
        self.customer_id = None  # Initialize customer_id
        self._setup_ui()
    
    def _setup_ui(self):
        # Set title based on whether we're creating or editing
        if self.customer_id:
            title = self.lm.get("Customers.edit_customer", "Edit Customer")
        else:
            title = self.lm.get("Customers.new_customer", "New Customer")
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Essential Details Group ---
        essential_group = QGroupBox(self.lm.get("Customers.essential_info", "Essential Details"))
        essential_layout = QFormLayout(essential_group)
        essential_layout.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.lm.get("Customers.ph_customer_name", "Enter full name"))
        self.name_input.setMinimumHeight(35)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(self.lm.get("Customers.ph_customer_phone", "e.g. +95 9 111 2222"))
        self.phone_input.setMaxLength(20)
        self.phone_input.setMinimumHeight(35)
        
        self.contact_method = QComboBox()
        self.contact_method.addItems([
            self.lm.get("Customers.contact_phone", "phone"),
            self.lm.get("Customers.contact_email", "email"),
            self.lm.get("Customers.contact_sms", "sms")
        ])
        self.contact_method.setMinimumHeight(35)
        
        essential_layout.addRow(self.lm.get("Customers.customer_name", "Name") + "*:", self.name_input)
        essential_layout.addRow(self.lm.get("Customers.customer_phone", "Phone") + ":", self.phone_input)
        essential_layout.addRow(self.lm.get("Customers.contact_method", "Contact Method") + ":", self.contact_method)
        
        layout.addWidget(essential_group)
        
        # --- Additional Details Group ---
        additional_group = QGroupBox(self.lm.get("Customers.additional_info", "Additional Details"))
        additional_layout = QFormLayout(additional_group)
        additional_layout.setSpacing(15)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(self.lm.get("Customers.ph_customer_email", "example@domain.com"))
        self.email_input.setMinimumHeight(35)
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText(self.lm.get("Customers.ph_customer_address", "Enter customer address"))
        self.address_input.setMinimumHeight(35)
        
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText(self.lm.get("Customers.ph_customer_notes", "Additional notes..."))
        self.note_input.setMaximumHeight(80)
        
        additional_layout.addRow(self.lm.get("Customers.customer_email", "Email") + ":", self.email_input)
        additional_layout.addRow(self.lm.get("Customers.customer_address", "Address") + ":", self.address_input)
        additional_layout.addRow(self.lm.get("Customers.customer_notes", "Notes") + ":", self.note_input)
        
        layout.addWidget(additional_group)
        
        # Connect validation signals
        self.phone_input.textChanged.connect(self._validate_phone)
        self.email_input.textChanged.connect(self._validate_email)
        
        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        
        # Style buttons (optional, if theme doesn't cover)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText(self.lm.get("Common.save", "Save"))
        ok_btn.setMinimumHeight(35)
        
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.setMinimumHeight(35)
        
        layout.addWidget(buttons)
    
    def _validate_phone(self):
        phone = self.phone_input.text()
        if phone:  # Phone is optional unless it's provided
            if not InputValidator.validate_phone(phone):
                self.phone_input.setStyleSheet("border: 1px solid red;")
            else:
                self.phone_input.setStyleSheet("")
                # Auto-format if valid
                formatted = phone_formatter.format_phone_number(phone)
                if formatted != phone:
                    self.phone_input.setText(formatted)
        else:
            self.phone_input.setStyleSheet("")
    
    def _validate_email(self):
        email = self.email_input.text()
        if email:  # Email is optional unless it's provided
            is_valid, _ = InputValidator.validate_email(email)
            self.email_input.setStyleSheet("border: 1px solid red;" if not is_valid else "")
        else:
            self.email_input.setStyleSheet("")
    
    def _validate_form(self) -> bool:
        """Validate all form fields and show appropriate error messages."""
        errors = []
        
        # Validate name (required)
        name = self.name_input.text().strip()
        if not name:
            errors.append(self.lm.get("Customers.name_required", "Name is required"))
        elif not InputValidator.validate_name(name):
            errors.append(self.lm.get("Customers.name_invalid", "Name contains invalid characters"))
        
        # Validate phone (required if contact method is phone)
        phone = self.phone_input.text().strip()
        current_method = self.contact_method.currentText()
        phone_method_label = self.lm.get("Customers.contact_phone", "phone")
        sms_method_label = self.lm.get("Customers.contact_sms", "sms")
        
        if (current_method == phone_method_label or current_method == sms_method_label) and not phone:
             errors.append(self.lm.get("Customers.phone_required", "Phone is required for this contact method"))
        elif phone:
            if len(phone) > 20:  # Double-check length in case input bypassed UI restriction
                errors.append(self.lm.get("Customers.phone_too_long", "Phone number too long (max 20 characters)"))
            elif not InputValidator.validate_phone(phone):
                errors.append(self.lm.get("Customers.phone_invalid", "Invalid phone number format"))
        
        # Validate email (required if contact method is email)
        email = self.email_input.text().strip()
        email_method_label = self.lm.get("Customers.contact_email", "email")
        
        if current_method == email_method_label and not email:
            errors.append(self.lm.get("Customers.email_required", "Email is required when contact method is 'email'"))
        elif email:
            is_valid, msg = InputValidator.validate_email(email)
            if not is_valid:
                errors.append(f"{self.lm.get('Customers.customer_email', 'Email')}: {msg}")
        
        if errors:
            QMessageBox.warning(self, self.lm.get("Common.warning", "Validation Error"), "\n".join(errors))
            return False
        return True
    
    def _save(self):
        if not self._validate_form():
            return
            
        data = {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'email': self.email_input.text().strip().lower(),
            'preferred_contact_method': self.contact_method.currentText(),
            'address': self.address_input.text().strip(),
            'notes': self.note_input.toPlainText().strip(),
            'created_by': self.user_id,
            'updated_by': self.user_id
        }
            
        try:
            if self.customer_id:  # Edit mode
                success = self.controller.update_customer(self.customer_id, data)
                if success:
                    self.accept()
                else:
                    QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Customers.update_failed", "Failed to update customer"))
            else:  # Create mode
                customer = self.controller.create_customer(data)
                if customer:  # Check if customer DTO was returned
                    self.accept()
                else:
                    QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Customers.create_failed", "Failed to create customer"))
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Customers.operation_failed', 'Operation failed')}: {str(e)}")