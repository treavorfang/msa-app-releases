# src/app/views/financial/credit_note_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QGroupBox, QFormLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from config.constants import UIColors, CreditNoteStatus
from datetime import datetime


class CreditNoteDetailsDialog(QDialog):
    """Dialog for viewing credit note details"""
    
    def __init__(self, container, credit_note, parent=None):
        super().__init__(parent)
        self.container = container
        self.credit_note = credit_note
        self.setWindowTitle(f"Credit Note Details - {credit_note.credit_note_number}")
        self.setMinimumSize(800, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Credit Note Information
        info_group = self._create_credit_note_info_section()
        layout.addWidget(info_group)
        
        # Supplier Information
        supplier_group = self._create_supplier_info_section()
        layout.addWidget(supplier_group)
        
        # Purchase Return Details
        return_group = self._create_return_info_section()
        layout.addWidget(return_group)
        
        # Financial Summary
        financial_group = self._create_financial_summary_section()
        layout.addWidget(financial_group)
        
        # Application History (if any)
        if self.credit_note.supplier_invoice:
            history_group = self._create_application_history_section()
            layout.addWidget(history_group)
        
        # Notes
        if self.credit_note.notes:
            notes_group = self._create_notes_section()
            layout.addWidget(notes_group)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_credit_note_info_section(self):
        """Create credit note information section"""
        group = QGroupBox("Credit Note Information")
        form_layout = QFormLayout(group)
        
        # Credit note number
        cn_number_label = QLabel(self.credit_note.credit_note_number)
        cn_number_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Credit Note #:", cn_number_label)
        
        # Issue date
        issue_date = self.credit_note.issue_date.strftime("%Y-%m-%d %H:%M") if self.credit_note.issue_date else "N/A"
        form_layout.addRow("Issue Date:", QLabel(issue_date))
        
        # Expiry date
        if self.credit_note.expiry_date:
            expiry_date = self.credit_note.expiry_date.strftime("%Y-%m-%d")
            expiry_label = QLabel(expiry_date)
            if self.credit_note.is_expired:
                expiry_label.setStyleSheet(f"color: {UIColors.ERROR}; font-weight: bold;")
            form_layout.addRow("Expiry Date:", expiry_label)
        else:
            form_layout.addRow("Expiry Date:", QLabel("No Expiry"))
        
        # Status
        status_label = QLabel(self.credit_note.status.upper())
        if self.credit_note.status == CreditNoteStatus.APPLIED:
            status_label.setStyleSheet(f"color: {UIColors.SUCCESS}; font-weight: bold;")
        elif self.credit_note.status == CreditNoteStatus.EXPIRED:
            status_label.setStyleSheet(f"color: {UIColors.ERROR}; font-weight: bold;")
        elif self.credit_note.status == CreditNoteStatus.PENDING:
            status_label.setStyleSheet(f"color: {UIColors.WARNING}; font-weight: bold;")
        form_layout.addRow("Status:", status_label)
        
        return group
    
    def _create_supplier_info_section(self):
        """Create supplier information section"""
        group = QGroupBox("Supplier Information")
        form_layout = QFormLayout(group)
        
        if self.credit_note.supplier:
            supplier = self.credit_note.supplier
            
            # Supplier name
            name_label = QLabel(supplier.name)
            name_label.setStyleSheet("font-weight: bold;")
            form_layout.addRow("Name:", name_label)
            
            # Contact
            if supplier.contact_person:
                form_layout.addRow("Contact Person:", QLabel(supplier.contact_person))
            
            if supplier.phone:
                form_layout.addRow("Phone:", QLabel(supplier.phone))
            
            if supplier.email:
                form_layout.addRow("Email:", QLabel(supplier.email))
        else:
            form_layout.addRow("Supplier:", QLabel("N/A"))
        
        return group
    
    def _create_return_info_section(self):
        """Create purchase return information section"""
        group = QGroupBox("Purchase Return Details")
        form_layout = QFormLayout(group)
        
        if self.credit_note.purchase_return:
            pr = self.credit_note.purchase_return
            
            # Return number
            return_label = QLabel(pr.return_number)
            return_label.setStyleSheet("font-weight: bold;")
            form_layout.addRow("Return #:", return_label)
            
            # Return date
            return_date = pr.return_date.strftime("%Y-%m-%d") if pr.return_date else "N/A"
            form_layout.addRow("Return Date:", QLabel(return_date))
            
            # Reason
            form_layout.addRow("Reason:", QLabel(pr.reason))
            
            # PO number
            if pr.purchase_order:
                form_layout.addRow("PO #:", QLabel(pr.purchase_order.po_number))
        else:
            form_layout.addRow("Return:", QLabel("N/A"))
        
        return group
    
    def _create_financial_summary_section(self):
        """Create financial summary section"""
        group = QGroupBox("Financial Summary")
        form_layout = QFormLayout(group)
        
        # Credit amount
        credit_amount_label = QLabel(f"${float(self.credit_note.credit_amount):,.2f}")
        credit_amount_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addRow("Credit Amount:", credit_amount_label)
        
        # Applied amount
        applied_amount = float(self.credit_note.applied_amount)
        applied_label = QLabel(f"${applied_amount:,.2f}")
        if applied_amount > 0:
            applied_label.setStyleSheet(f"color: {UIColors.WARNING};")
        form_layout.addRow("Applied Amount:", applied_label)
        
        # Remaining credit
        remaining = float(self.credit_note.remaining_credit)
        remaining_label = QLabel(f"${remaining:,.2f}")
        if remaining > 0:
            remaining_label.setStyleSheet(f"color: {UIColors.SUCCESS}; font-weight: bold; font-size: 14px;")
        else:
            remaining_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addRow("Remaining Credit:", remaining_label)
        
        return group
    
    def _create_application_history_section(self):
        """Create application history section"""
        group = QGroupBox("Application History")
        layout = QVBoxLayout(group)
        
        if self.credit_note.supplier_invoice:
            invoice = self.credit_note.supplier_invoice
            
            info_label = QLabel(
                f"Applied to Invoice: {invoice.invoice_number}\n"
                f"Amount Applied: ${float(self.credit_note.applied_amount):,.2f}"
            )
            layout.addWidget(info_label)
        else:
            layout.addWidget(QLabel("No applications yet"))
        
        return group
    
    def _create_notes_section(self):
        """Create notes section"""
        group = QGroupBox("Notes")
        layout = QVBoxLayout(group)
        
        notes_text = QTextEdit()
        notes_text.setPlainText(self.credit_note.notes)
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(100)
        layout.addWidget(notes_text)
        
        return group
