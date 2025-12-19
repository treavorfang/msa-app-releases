from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QComboBox, QLineEdit, 
                               QDateEdit, QTextEdit, QMessageBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QDate
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class RecordCustomerPaymentDialog(QDialog):
    """Dialog for recording payments against customer invoices"""
    
    def __init__(self, container, invoice, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.invoice = invoice
        self.user = user
        self.lm = language_manager
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Invoices.record_payment_title', 'Record Payment')} - {self.lm.get('Invoices.invoice_number', 'Invoice #')}{self.invoice.invoice_number}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Outstanding Balance
        outstanding = self._calculate_outstanding()
        self.outstanding_label = QLabel(currency_formatter.format(outstanding))
        self.outstanding_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        form_layout.addRow(f"{self.lm.get('Invoices.total_outstanding', 'Outstanding Balance')}:", self.outstanding_label)
        
        # Payment Amount
        # Payment Amount
        from views.components.money_input import MoneyInput
        self.amount_input = MoneyInput(default_value=float(outstanding))
        form_layout.addRow(f"{self.lm.get('Invoices.amount_label', 'Payment Amount')}:*", self.amount_input)
        
        # Payment Date
        self.payment_date_input = QDateEdit()
        self.payment_date_input.setDate(QDate.currentDate())
        self.payment_date_input.setCalendarPopup(True)
        form_layout.addRow(f"{self.lm.get('Invoices.payment_date_label', 'Payment Date')}:", self.payment_date_input)
        
        # Payment Method - store English values as data
        self.payment_method_combo = QComboBox()
        payment_methods = [
            ('cash', self.lm.get("Invoices.payment_method_cash", "Cash")),
            ('card', self.lm.get("Invoices.payment_method_card", "Card")),
            ('bank_transfer', self.lm.get("Invoices.payment_method_bank", "Bank Transfer")),
            ('check', self.lm.get("Invoices.payment_method_check", "Check")),
            ('other', self.lm.get("Invoices.payment_method_other", "Other"))
        ]
        for method_key, method_label in payment_methods:
            self.payment_method_combo.addItem(method_label, method_key)
        
        form_layout.addRow(f"{self.lm.get('Invoices.payment_method_label', 'Payment Method')}:", self.payment_method_combo)
        
        # Reference Number
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText(self.lm.get("Invoices.reference_placeholder", "Transaction ID, Check #, etc."))
        form_layout.addRow(f"{self.lm.get('Invoices.payment_reference', 'Reference #')}:", self.reference_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText(self.lm.get("Common.notes_placeholder", "Optional notes..."))
        form_layout.addRow(f"{self.lm.get('Invoices.payment_notes_label', 'Notes')}:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton(self.lm.get("Invoices.record_payment", "Record Payment"))
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
    def _calculate_outstanding(self):
        total = float(self.invoice.total)
        paid = 0.0
        for payment in self.invoice.payments:
            paid += float(payment.amount)
        return max(0.0, total - paid)
    
    def _on_save(self):
        amount = self.amount_input.value()
        
        if amount <= 0:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Invoices.payment_amount_invalid", "Payment amount must be greater than 0"))
            return
            
        outstanding = self._calculate_outstanding()
        if amount > outstanding + 0.01: # Tolerance
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Invoices.payment_amount_exceeds", "Payment amount cannot exceed outstanding balance"))
            return
            
        # Get English payment method from combo box data (not the display text)
        method = self.payment_method_combo.currentData()
        
        payment_data = {
            'invoice': self.invoice.id,
            'amount': amount,
            'paid_at': self.payment_date_input.date().toPython(),
            'payment_method': method,
            'transaction_id': self.reference_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None
        }
        
        try:
            # Assuming payment_service is available via container
            # If not, we might need to use invoice_controller or similar
            # Based on previous check, payment_service exists
            # Use payment_controller to ensure events are published
            if hasattr(self.container, 'payment_controller'):
                self.container.payment_controller.create_payment(
                    payment_data, 
                    current_user=self.user,
                    ip_address='127.0.0.1' 
                )
            else:
                # Use controller to trigger EventBus events
                self.container.payment_controller.create_payment(
                    payment_data,
                    current_user=self.user,
                    ip_address='127.0.0.1'
                ) 
                
            # Update invoice status if fully paid
            new_outstanding = outstanding - amount
            if new_outstanding <= 0.01:
                update_data = {
                    'payment_status': 'paid',
                    'paid_date': self.payment_date_input.date().toPython()
                }
                self.container.invoice_controller.update_invoice(self.invoice.id, update_data)
            elif new_outstanding < float(self.invoice.total):
                self.container.invoice_controller.update_invoice(self.invoice.id, {'payment_status': 'partially_paid'})
                
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Invoices.payment_recorded", "Payment recorded successfully"))
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.error', 'Error')}: {str(e)}")
