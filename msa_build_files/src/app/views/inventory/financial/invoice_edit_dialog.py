# src/app/views/financial/invoice_edit_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QPushButton, QGroupBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from utils.validation.message_handler import MessageHandler
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class InvoiceEditDialog(QDialog):
    """Dialog for editing supplier invoice discount and shipping"""
    
    def __init__(self, container, invoice, parent=None):
        super().__init__(parent)
        self.container = container
        self.invoice = invoice
        self.invoice_service = container.supplier_invoice_service
        self.lm = language_manager
        self.cf = currency_formatter
        
        self.setWindowTitle(f"{self.lm.get('Inventory.edit_invoice', 'Edit Invoice')} - {invoice.invoice_number}")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Invoice info (read-only)
        info_group = QGroupBox(self.lm.get("Inventory.invoice_information", "Invoice Information"))
        info_layout = QFormLayout(info_group)
        
        self.invoice_number_label = QLabel()
        info_layout.addRow(f"{self.lm.get('Inventory.invoice_number', 'Invoice Number')}:", self.invoice_number_label)
        
        self.po_number_label = QLabel()
        info_layout.addRow(f"{self.lm.get('Inventory.po_number', 'PO Number')}:", self.po_number_label)
        
        self.supplier_label = QLabel()
        info_layout.addRow(f"{self.lm.get('Inventory.supplier', 'Supplier')}:", self.supplier_label)
        
        self.invoice_date_label = QLabel()
        info_layout.addRow(f"{self.lm.get('Inventory.invoice_date', 'Invoice Date')}:", self.invoice_date_label)
        
        layout.addWidget(info_group)
        
        # Editable amounts
        amounts_group = QGroupBox(self.lm.get("Inventory.amounts", "Amounts"))
        amounts_layout = QFormLayout(amounts_group)
        
        self.subtotal_label = QLabel()
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        amounts_layout.addRow(f"{self.lm.get('Inventory.subtotal', 'Subtotal')}:", self.subtotal_label)
        
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("0.00")
        self.discount_input.textChanged.connect(self._update_total)
        amounts_layout.addRow(f"{self.lm.get('Inventory.discount', 'Discount')}:", self.discount_input)
        
        self.shipping_input = QLineEdit()
        self.shipping_input.setPlaceholderText("0.00")
        self.shipping_input.textChanged.connect(self._update_total)
        amounts_layout.addRow(f"{self.lm.get('Inventory.shipping_fee', 'Shipping Fee')}:", self.shipping_input)
        
        # Total (calculated)
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2563EB;")
        amounts_layout.addRow(f"{self.lm.get('Inventory.total_amount', 'Total Amount')}:", self.total_label)
        
        layout.addWidget(amounts_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self):
        """Load invoice data"""
        self.invoice_number_label.setText(self.invoice.invoice_number)
        
        # Use flattened fields from DTO
        if self.invoice.po_number:
            self.po_number_label.setText(self.invoice.po_number)
        else:
            self.po_number_label.setText(self.lm.get("Common.not_applicable", "N/A"))
            
        if self.invoice.supplier_name:
            self.supplier_label.setText(self.invoice.supplier_name)
        else:
            self.supplier_label.setText(self.lm.get("Common.not_applicable", "N/A"))
        
        self.invoice_date_label.setText(self.invoice.invoice_date.strftime("%Y-%m-%d"))
        
        # Set amounts
        self.subtotal_label.setText(self.cf.format(self.invoice.subtotal))
        self.discount_input.setText(str(float(self.invoice.discount)))
        self.shipping_input.setText(str(float(self.invoice.shipping_fee)))
        
        self._update_total()
    
    def _update_total(self):
        """Update total amount display"""
        try:
            subtotal = float(self.invoice.subtotal)
            discount = float(self.discount_input.text() or 0)
            shipping = float(self.shipping_input.text() or 0)
            
            total = subtotal + shipping - discount
            self.total_label.setText(self.cf.format(total))
        except ValueError:
            self.total_label.setText(self.cf.format(0))
    
    def _on_save(self):
        """Save changes"""
        try:
            discount = Decimal(self.discount_input.text() or "0")
            shipping = Decimal(self.shipping_input.text() or "0")
            
            # Validate
            if discount < 0:
                MessageHandler.show_warning(self, self.lm.get("Validation.invalid_discount", "Invalid Discount"), self.lm.get("Validation.discount_negative", "Discount cannot be negative."))
                return
            
            if shipping < 0:
                MessageHandler.show_warning(self, self.lm.get("Validation.invalid_shipping", "Invalid Shipping"), self.lm.get("Validation.shipping_negative", "Shipping fee cannot be negative."))
                return
            
            # Update invoice
            update_data = {
                'discount': discount,
                'shipping_fee': shipping
            }
            
            updated_invoice = self.invoice_service.update_invoice(self.invoice.id, update_data)
            
            if updated_invoice:
                MessageHandler.show_success(self, self.lm.get("Common.success", "Success"), self.lm.get("Inventory.invoice_updated", "Invoice updated successfully!"))
                self.accept()
            else:
                MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.invoice_update_failed", "Failed to update invoice."))
        
        except ValueError:
            MessageHandler.show_error(self, self.lm.get("Validation.invalid_input", "Invalid Input"), self.lm.get("Validation.enter_valid_numbers", "Please enter valid numbers for discount and shipping."))
        except Exception as e:
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.error_occurred', 'An error occurred')}: {str(e)}")
