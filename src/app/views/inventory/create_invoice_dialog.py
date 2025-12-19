# src/app/views/inventory/create_invoice_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QComboBox, QLineEdit, 
                               QDateEdit, QTextEdit, QMessageBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta

class CreateInvoiceDialog(QDialog):
    """Dialog for creating supplier invoices from purchase orders"""
    
    def __init__(self, container, supplier, parent=None):
        super().__init__(parent)
        self.container = container
        self.supplier = supplier
        self.selected_po = None
        self._setup_ui()
        self._load_pos()
        
    def _setup_ui(self):
        self.setWindowTitle(f"Create Invoice - {self.supplier.name}")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # PO Selection
        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self._on_po_selected)
        form_layout.addRow("Purchase Order:", self.po_combo)
        
        # Invoice Number
        self.invoice_number_input = QLineEdit()
        self.invoice_number_input.setPlaceholderText("INV-001")
        form_layout.addRow("Invoice Number:*", self.invoice_number_input)
        
        # Invoice Date
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        form_layout.addRow("Invoice Date:", self.invoice_date_input)
        
        # Due Date
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_input)
        
        # Total Amount
        # Total Amount
        from views.components.money_input import MoneyInput
        self.amount_input = MoneyInput()
        self.amount_input.setPlaceholderText("0.00")
        form_layout.addRow("Total Amount:*", self.amount_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Optional notes...")
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("Create Invoice")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_pos(self):
        """Load received POs for this supplier"""
        pos = self.container.purchase_order_service.list_purchase_orders()
        received_pos = [po for po in pos 
                       if po.supplier and po.supplier.id == self.supplier.id 
                       and po.status == 'received']
        
        self.po_combo.clear()
        if not received_pos:
            self.po_combo.addItem("No received POs available", None)
            self.save_btn.setEnabled(False)
            return
        
        for po in received_pos:
            self.po_combo.addItem(f"{po.po_number} - ${float(po.total_amount):.2f}", po)
    
    def _on_po_selected(self, index):
        """Handle PO selection"""
        po = self.po_combo.itemData(index)
        if po:
            self.selected_po = po
            self.amount_input.setValue(float(po.total_amount))
            # Auto-generate invoice number
            self.invoice_number_input.setText(f"INV-{po.po_number}")
    
    def _on_save(self):
        """Save the invoice"""
        # Validation
        if not self.invoice_number_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Invoice number is required")
            return
        
        if not self.selected_po:
            QMessageBox.warning(self, "Validation Error", "Please select a purchase order")
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0")
            return
        
        # Create invoice
        invoice_data = {
            'purchase_order': self.selected_po.id,
            'invoice_number': self.invoice_number_input.text().strip(),
            'invoice_date': self.invoice_date_input.date().toPython(),
            'due_date': self.due_date_input.date().toPython(),
            'total_amount': self.amount_input.value(),
            'notes': self.notes_input.toPlainText().strip() or None
        }
        
        try:
            invoice = self.container.supplier_invoice_service.create_invoice(invoice_data)
            QMessageBox.information(self, "Success", 
                                  f"Invoice {invoice.invoice_number} created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create invoice: {str(e)}")
