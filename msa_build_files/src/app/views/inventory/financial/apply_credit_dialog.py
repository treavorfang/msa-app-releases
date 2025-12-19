# src/app/views/financial/apply_credit_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QGroupBox, QFormLayout, QPushButton, QComboBox,
                              QDoubleSpinBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from config.constants import UIColors, InvoiceStatus


class ApplyCreditDialog(QDialog):
    """Dialog for applying credit to an invoice"""
    
    def __init__(self, container, credit_note, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.credit_note = credit_note
        self.user = user
        self.invoice_service = container.supplier_invoice_service
        self.credit_note_service = container.credit_note_service
        
        self.setWindowTitle(f"Apply Credit - {credit_note.credit_note_number}")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_invoices()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Credit Note Info
        info_group = QGroupBox("Credit Note Information")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Credit Note #:", QLabel(self.credit_note.credit_note_number))
        
        remaining_label = QLabel(f"${float(self.credit_note.remaining_credit):,.2f}")
        remaining_label.setStyleSheet(f"color: {UIColors.SUCCESS}; font-weight: bold;")
        info_layout.addRow("Available Credit:", remaining_label)
        
        if self.credit_note.supplier:
            info_layout.addRow("Supplier:", QLabel(self.credit_note.supplier.name))
        
        layout.addWidget(info_group)
        
        # Application Form
        form_group = QGroupBox("Apply Credit")
        form_layout = QFormLayout(form_group)
        
        # Invoice selection
        self.invoice_combo = QComboBox()
        self.invoice_combo.currentIndexChanged.connect(self._on_invoice_changed)
        form_layout.addRow("Select Invoice:", self.invoice_combo)
        
        # Invoice details
        self.invoice_details_label = QLabel("Select an invoice to see details")
        form_layout.addRow("Invoice Balance:", self.invoice_details_label)
        
        # Amount input
        # Amount input
        from views.components.money_input import MoneyInput
        self.amount_spin = MoneyInput()
        self.amount_spin.valueChanged.connect(self._update_preview)
        form_layout.addRow("Amount to Apply:", self.amount_spin)
        
        layout.addWidget(form_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout(preview_group)
        
        self.new_balance_label = QLabel("-")
        preview_layout.addRow("New Invoice Balance:", self.new_balance_label)
        
        self.remaining_credit_label = QLabel("-")
        preview_layout.addRow("Remaining Credit:", self.remaining_credit_label)
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply Credit")
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setStyleSheet(f"background-color: {UIColors.INFO}; color: white;")
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
    
    def _load_invoices(self):
        """Load outstanding invoices for the supplier"""
        if not self.credit_note.supplier:
            return
            
        # Get pending and partial invoices for this supplier
        # Note: We need to filter manually since we don't have a direct method for this specific query
        all_invoices = self.invoice_service.list_invoices()
        supplier_invoices = []
        
        for invoice in all_invoices:
            # Check if invoice belongs to same supplier
            if (invoice.purchase_order and 
                invoice.purchase_order.supplier and 
                invoice.purchase_order.supplier.id == self.credit_note.supplier.id):
                
                # Check if invoice has outstanding balance
                outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
                if outstanding > 0 and invoice.status != InvoiceStatus.PAID:
                    supplier_invoices.append((invoice, outstanding))
        
        # Populate combo box
        self.invoice_combo.clear()
        self.invoice_combo.addItem("Select Invoice...", None)
        
        for invoice, outstanding in supplier_invoices:
            self.invoice_combo.addItem(
                f"{invoice.invoice_number} (Outstanding: ${outstanding:,.2f})", 
                invoice
            )
    
    def _on_invoice_changed(self):
        """Handle invoice selection change"""
        invoice = self.invoice_combo.currentData()
        
        if invoice:
            outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
            self.invoice_details_label.setText(f"${outstanding:,.2f}")
            
            # Set max amount to min(outstanding, remaining_credit)
            max_amount = min(outstanding, float(self.credit_note.remaining_credit))
            self.amount_spin.setValue(max_amount)  # Default to max possible
            
            self._update_preview()
        else:
            self.invoice_details_label.setText("-")
            self.new_balance_label.setText("-")
            self.remaining_credit_label.setText("-")
    
    def _update_preview(self):
        """Update preview calculations"""
        invoice = self.invoice_combo.currentData()
        if not invoice:
            return
            
        amount = self.amount_spin.value()
        outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
        remaining_credit = float(self.credit_note.remaining_credit)
        
        new_balance = outstanding - amount
        new_remaining = remaining_credit - amount
        
        self.new_balance_label.setText(f"${new_balance:,.2f}")
        self.remaining_credit_label.setText(f"${new_remaining:,.2f}")
    
    def _on_apply(self):
        """Apply the credit"""
        invoice = self.invoice_combo.currentData()
        if not invoice:
            QMessageBox.warning(self, "Validation Error", "Please select an invoice.")
            return
            
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0.")
            return

        outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
        max_amount = min(outstanding, float(self.credit_note.remaining_credit))
        if amount > max_amount:
            QMessageBox.warning(self, "Validation Error", f"Amount cannot exceed ${max_amount:,.2f}")
            return
            
        try:
            success = self.credit_note_service.apply_credit_to_invoice(
                credit_note_id=self.credit_note.id,
                invoice_id=invoice.id,
                amount=amount,
                current_user=self.user
            )
            
            if success:
                QMessageBox.information(self, "Success", "Credit applied successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to apply credit. Please try again.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
