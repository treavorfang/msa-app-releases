# src/app/views/inventory/record_payment_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QComboBox, QLineEdit, 
                               QDateEdit, QTextEdit, QMessageBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QDate

class RecordPaymentDialog(QDialog):
    """Dialog for recording payments against supplier invoices"""
    
    def __init__(self, container, supplier_or_invoice, parent=None):
        super().__init__(parent)
        self.container = container
        
        # Handle both supplier and invoice objects
        if hasattr(supplier_or_invoice, 'invoice_number'):  # It's an invoice
            self.invoice = supplier_or_invoice
            if hasattr(supplier_or_invoice, 'purchase_order') and supplier_or_invoice.purchase_order:
                 self.supplier = supplier_or_invoice.purchase_order.supplier
            elif hasattr(supplier_or_invoice, 'purchase_order_id') and supplier_or_invoice.purchase_order_id:
                # Fetch supplier via PO
                po = container.purchase_order_service.get_purchase_order(supplier_or_invoice.purchase_order_id)
                self.supplier = container.supplier_service.get_supplier(po.supplier_id) if po else None
            else:
                self.supplier = None
            self.preselected_invoice = supplier_or_invoice
        else:  # It's a supplier
            self.supplier = supplier_or_invoice
            self.invoice = None
            self.preselected_invoice = None
            
        self.selected_invoice = None
        self._setup_ui()
        self._load_invoices()
        
    def _setup_ui(self):
        """Setup the UI"""
        # Get supplier name
        supplier_name = self.supplier.name if self.supplier else "Unknown Supplier"
        self.setWindowTitle(f"Record Payment - {supplier_name}")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Invoice Selection
        self.invoice_combo = QComboBox()
        self.invoice_combo.currentIndexChanged.connect(self._on_invoice_selected)
        form_layout.addRow("Invoice:", self.invoice_combo)
        
        # Outstanding Balance (read-only)
        self.outstanding_label = QLabel("$0.00")
        self.outstanding_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        form_layout.addRow("Outstanding Balance:", self.outstanding_label)
        
        # Payment Amount
        # Payment Amount
        from views.components.money_input import MoneyInput
        self.amount_input = MoneyInput()
        form_layout.addRow("Payment Amount:*", self.amount_input)
        
        # Payment Date
        self.payment_date_input = QDateEdit()
        self.payment_date_input.setDate(QDate.currentDate())
        self.payment_date_input.setCalendarPopup(True)
        form_layout.addRow("Payment Date:", self.payment_date_input)
        
        # Payment Method
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Bank Transfer", "Cash", "Check", "Credit Card", "Other"])
        form_layout.addRow("Payment Method:", self.payment_method_combo)
        
        # Reference Number
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Transaction/Check number...")
        form_layout.addRow("Reference #:", self.reference_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Optional notes...")
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("Record Payment")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_invoices(self):
        """Load outstanding invoices for this supplier"""
        if not self.supplier:
            self.invoice_combo.addItem("No supplier found", None)
            self.save_btn.setEnabled(False)
            return
            
        # If a specific invoice was passed, only show that one
        if self.preselected_invoice:
            outstanding = self.preselected_invoice.outstanding_amount
            self.invoice_combo.addItem(
                f"{self.preselected_invoice.invoice_number} - Outstanding: ${outstanding:.2f}", 
                self.preselected_invoice
            )
            self.invoice_combo.setCurrentIndex(0)
            self._on_invoice_selected(0)
            return
        
        # Otherwise load all outstanding invoices for the supplier
        invoices = self.container.supplier_invoice_service.get_outstanding_invoices(self.supplier.id)
        
        self.invoice_combo.clear()
        if not invoices:
            self.invoice_combo.addItem("No outstanding invoices", None)
            self.save_btn.setEnabled(False)
            return
        
        for invoice in invoices:
            outstanding = invoice.outstanding_amount
            self.invoice_combo.addItem(
                f"{invoice.invoice_number} - Outstanding: ${outstanding:.2f}", 
                invoice
            )
    
    def _on_invoice_selected(self, index):
        """Handle invoice selection"""
        invoice = self.invoice_combo.itemData(index)
        if invoice:
            self.selected_invoice = invoice
            outstanding = invoice.outstanding_amount
            self.outstanding_label.setText(f"${outstanding:.2f}")
            self.amount_input.setValue(outstanding)
            self.amount_input.setValue(outstanding)
    
    def _on_save(self):
        """Save the payment"""
        # Validation
        if not self.selected_invoice:
            QMessageBox.warning(self, "Validation Error", "Please select an invoice")
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Payment amount must be greater than 0")
            return
        
        if self.amount_input.value() > self.selected_invoice.outstanding_amount:
            QMessageBox.warning(self, "Validation Error", 
                              "Payment amount cannot exceed outstanding balance")
            return
        
        # Map payment method
        method_map = {
            "Bank Transfer": "bank_transfer",
            "Cash": "cash",
            "Check": "check",
            "Credit Card": "credit_card",
            "Other": "other"
        }
        
        # Create payment
        payment_data = {
            'invoice': self.selected_invoice.id,
            'amount': self.amount_input.value(),
            'payment_date': self.payment_date_input.date().toPython(),
            'payment_method': method_map[self.payment_method_combo.currentText()],
            'reference_number': self.reference_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None
        }
        
        try:
            payment = self.container.supplier_payment_service.record_payment(payment_data)
            QMessageBox.information(self, "Success", 
                                  f"Payment of ${payment.amount:.2f} recorded successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")
