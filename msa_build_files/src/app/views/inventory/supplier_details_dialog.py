# src/app/views/inventory/supplier_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QGroupBox, QTabWidget, 
                               QWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class SupplierDetailsDialog(QDialog):
    """Dialog for viewing detailed supplier information including financial data"""
    
    def __init__(self, container, supplier, parent=None):
        super().__init__(parent)
        self.container = container
        self.supplier = supplier
        self.lm = language_manager
        self.cf = currency_formatter
        self._setup_ui()
    
    def _get_localized_po_status(self, status: str) -> str:
        """Get localized PO status text"""
        status_map = {
            'draft': self.lm.get('Inventory.status_draft', 'Draft'),
            'sent': self.lm.get('Inventory.status_sent', 'Sent'),
            'received': self.lm.get('Common.received', 'Received'),
            'cancelled': self.lm.get('Common.cancelled', 'Cancelled'),
        }
        return status_map.get(status, status)
    
    def _get_localized_invoice_status(self, status: str) -> str:
        """Get localized invoice status text"""
        status_map = {
            'pending': self.lm.get('Common.pending', 'Pending'),
            'partial': self.lm.get('Inventory.partial', 'Partial'),
            'paid': self.lm.get('Common.paid', 'Paid'),
            'overdue': self.lm.get('Inventory.overdue', 'Overdue'),
        }
        return status_map.get(status, status)
        
    def _setup_ui(self):
        self.setWindowTitle(f"Supplier Details - {self.supplier.name}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"🏢 {self.supplier.name}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Basic Info Tab
        tabs.addTab(self._create_basic_info_tab(), self.lm.get("Inventory.basic_info", "Basic Info"))
        
        # PO History Tab
        tabs.addTab(self._create_po_history_tab(), self.lm.get("Inventory.purchase_orders", "Purchase Orders"))
        
        # Financial Summary Tab
        tabs.addTab(self._create_financial_tab(), self.lm.get("Inventory.financial_summary", "Financial Summary"))
        
        # Invoices Tab
        tabs.addTab(self._create_invoices_tab(), self.lm.get("Inventory.invoices", "Invoices"))
        
        # Payments Tab
        tabs.addTab(self._create_payments_tab(), self.lm.get("Inventory.payments", "Payments"))
        
        layout.addWidget(tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        create_invoice_btn = QPushButton(self.lm.get("Inventory.create_invoice", "Create Invoice"))
        create_invoice_btn.clicked.connect(self._on_create_invoice)
        button_layout.addWidget(create_invoice_btn)
        
        record_payment_btn = QPushButton(self.lm.get("Inventory.record_payment", "Record Payment"))
        record_payment_btn.clicked.connect(self._on_record_payment)
        button_layout.addWidget(record_payment_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_basic_info_tab(self):
        """Create basic information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Contact details
        details_group = QGroupBox(self.lm.get("Inventory.contact_information", "Contact Information"))
        details_layout = QFormLayout(details_group)
        
        details_layout.addRow(f"{self.lm.get('Common.name', 'Name')}:", QLabel(self.supplier.name))
        details_layout.addRow(f"{self.lm.get('Inventory.contact_person', 'Contact Person')}:", QLabel(self.supplier.contact_person or self.lm.get("Common.not_applicable", "N/A")))
        details_layout.addRow(f"{self.lm.get('Common.email', 'Email')}:", QLabel(self.supplier.email or self.lm.get("Common.not_applicable", "N/A")))
        details_layout.addRow(f"{self.lm.get('Common.phone', 'Phone')}:", QLabel(self.supplier.phone or self.lm.get("Common.not_applicable", "N/A")))
        details_layout.addRow(f"{self.lm.get('Common.address', 'Address')}:", QLabel(self.supplier.address or self.lm.get("Common.not_applicable", "N/A")))
        details_layout.addRow(f"{self.lm.get('Inventory.tax_id', 'Tax ID')}:", QLabel(self.supplier.tax_id or self.lm.get("Common.not_applicable", "N/A")))
        details_layout.addRow(f"{self.lm.get('Inventory.payment_terms', 'Payment Terms')}:", QLabel(self.supplier.payment_terms or self.lm.get("Common.not_applicable", "N/A")))
        
        layout.addWidget(details_group)
        
        # Notes
        if self.supplier.notes:
            notes_group = QGroupBox(self.lm.get("Common.notes", "Notes"))
            notes_layout = QVBoxLayout(notes_group)
            notes_label = QLabel(self.supplier.notes)
            notes_label.setWordWrap(True)
            notes_layout.addWidget(notes_label)
            layout.addWidget(notes_group)
        
        layout.addStretch()
        return widget
    
    def _create_po_history_tab(self):
        """Create purchase order history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PO table
        po_table = QTableWidget()
        po_table.setColumnCount(5)
        po_table.setHorizontalHeaderLabels([
            self.lm.get("Inventory.po_number", "PO Number"),
            self.lm.get("Common.date", "Date"),
            self.lm.get("Common.status", "Status"),
            self.lm.get("Inventory.total_amount", "Total Amount"),
            self.lm.get("Inventory.received_date", "Received Date")
        ])
        po_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        po_table.setSelectionBehavior(QTableWidget.SelectRows)
        po_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Get POs for this supplier
        pos = [po for po in self.container.purchase_order_service.list_purchase_orders() 
               if po.supplier_id == self.supplier.id]
        
        po_table.setRowCount(len(pos))
        
        for row, po in enumerate(pos):
            po_table.setItem(row, 0, QTableWidgetItem(po.po_number))
            po_table.setItem(row, 1, QTableWidgetItem(po.order_date.strftime("%Y-%m-%d")))
            
            status_item = QTableWidgetItem(self._get_localized_po_status(po.status))
            if po.status == 'received':
                status_item.setForeground(Qt.green)
            elif po.status == 'sent':
                status_item.setForeground(Qt.blue)
            po_table.setItem(row, 2, status_item)
            
            po_table.setItem(row, 3, QTableWidgetItem(self.cf.format(po.total_amount)))
            
            received = po.received_date.strftime("%Y-%m-%d") if po.received_date else self.lm.get("Common.not_applicable", "N/A")
            po_table.setItem(row, 4, QTableWidgetItem(received))
        
        layout.addWidget(po_table)
        
        # Summary
        total_spent = sum(float(po.total_amount) for po in pos if po.status == 'received')
        summary_label = QLabel(f"{self.lm.get('Inventory.total_spent', 'Total Spent')}: {self.cf.format(total_spent)} | {self.lm.get('Inventory.total_pos', 'Total POs')}: {len(pos)}")
        summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(summary_label)
        
        return widget
    
    def _create_financial_tab(self):
        """Create financial summary tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Get financial data
        pos = [po for po in self.container.purchase_order_service.list_purchase_orders() 
               if po.supplier_id == self.supplier.id]
        
        total_spent = sum(float(po.total_amount) for po in pos if po.status == 'received')
        pending_orders = sum(float(po.total_amount) for po in pos if po.status in ['draft', 'sent'])
        
        # Financial summary
        summary_group = QGroupBox(self.lm.get("Inventory.financial_summary", "Financial Summary"))
        summary_layout = QFormLayout(summary_group)
        
        summary_layout.addRow(f"{self.lm.get('Inventory.total_spent', 'Total Spent')}:", QLabel(self.cf.format(total_spent)))
        summary_layout.addRow(f"{self.lm.get('Inventory.pending_orders', 'Pending Orders')}:", QLabel(self.cf.format(pending_orders)))
        summary_layout.addRow(f"{self.lm.get('Inventory.total_pos', 'Total POs')}:", QLabel(str(len(pos))))
        summary_layout.addRow(f"{self.lm.get('Inventory.received_pos', 'Received POs')}:", QLabel(str(len([po for po in pos if po.status == 'received']))))
        
        layout.addWidget(summary_group)
        
        # Payment terms reminder
        if self.supplier.payment_terms:
            terms_group = QGroupBox(self.lm.get("Inventory.payment_terms", "Payment Terms"))
            terms_layout = QVBoxLayout(terms_group)
            terms_label = QLabel(self.supplier.payment_terms)
            terms_label.setStyleSheet("font-size: 12px;")
            terms_layout.addWidget(terms_label)
            layout.addWidget(terms_group)
        
        layout.addStretch()
        return widget
    
    def _create_invoices_tab(self):
        """Create invoices tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Invoices table
        invoices_table = QTableWidget()
        invoices_table.setColumnCount(6)
        invoices_table.setHorizontalHeaderLabels([
            self.lm.get("Inventory.invoice_number", "Invoice #"),
            self.lm.get("Inventory.po_number", "PO #"),
            self.lm.get("Common.date", "Date"),
            self.lm.get("Inventory.due_date", "Due Date"),
            self.lm.get("Inventory.amount", "Amount"),
            self.lm.get("Common.status", "Status")
        ])
        invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Get invoices for this supplier
        invoices = self.container.supplier_invoice_service.get_invoices_by_supplier(self.supplier.id)
        
        invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            invoices_table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))
            invoices_table.setItem(row, 1, QTableWidgetItem(invoice.po_number or self.lm.get("Common.not_applicable", "N/A")))
            invoices_table.setItem(row, 2, QTableWidgetItem(invoice.invoice_date.strftime("%Y-%m-%d")))
            invoices_table.setItem(row, 3, QTableWidgetItem(invoice.due_date.strftime("%Y-%m-%d")))
            invoices_table.setItem(row, 4, QTableWidgetItem(self.cf.format(invoice.total_amount)))
            
            status_item = QTableWidgetItem(self._get_localized_invoice_status(invoice.status))
            if invoice.status == 'paid':
                status_item.setForeground(Qt.green)
            elif invoice.status == 'overdue':
                status_item.setForeground(Qt.red)
            elif invoice.status == 'partial':
                status_item.setForeground(Qt.blue)
            invoices_table.setItem(row, 5, status_item)
        
        layout.addWidget(invoices_table)
        
        # Summary
        outstanding = sum(invoice.outstanding_amount for invoice in invoices)
        summary_label = QLabel(f"{self.lm.get('Inventory.outstanding_balance', 'Outstanding Balance')}: {self.cf.format(outstanding)} | {self.lm.get('Inventory.total_invoices', 'Total Invoices')}: {len(invoices)}")
        summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: #e74c3c;")
        layout.addWidget(summary_label)
        
        return widget
    
    def _create_payments_tab(self):
        """Create payments tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Payments table
        payments_table = QTableWidget()
        payments_table.setColumnCount(5)
        payments_table.setHorizontalHeaderLabels([
            self.lm.get("Common.date", "Date"),
            self.lm.get("Inventory.invoice_number", "Invoice #"),
            self.lm.get("Inventory.amount", "Amount"),
            self.lm.get("Inventory.method", "Method"),
            self.lm.get("Inventory.reference", "Reference")
        ])
        payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Get payments for this supplier
        payments = self.container.supplier_payment_service.get_payments_by_supplier(self.supplier.id)
        
        payments_table.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            payments_table.setItem(row, 0, QTableWidgetItem(payment.payment_date.strftime("%Y-%m-%d")))
            payments_table.setItem(row, 1, QTableWidgetItem(payment.invoice_number or self.lm.get("Common.not_applicable", "N/A")))
            payments_table.setItem(row, 2, QTableWidgetItem(self.cf.format(payment.amount)))
            payments_table.setItem(row, 3, QTableWidgetItem(payment.payment_method.replace('_', ' ').title()))
            payments_table.setItem(row, 4, QTableWidgetItem(payment.reference_number or self.lm.get("Common.not_applicable", "N/A")))
        
        layout.addWidget(payments_table)
        
        # Summary
        total_paid = sum(float(payment.amount) for payment in payments)
        summary_label = QLabel(f"{self.lm.get('Inventory.total_paid', 'Total Paid')}: {self.cf.format(total_paid)} | {self.lm.get('Inventory.total_payments', 'Total Payments')}: {len(payments)}")
        summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: #2ecc71;")
        layout.addWidget(summary_label)
        
        return widget
    
    def _on_create_invoice(self):
        """Open create invoice dialog"""
        from views.inventory.create_invoice_dialog import CreateInvoiceDialog
        dialog = CreateInvoiceDialog(self.container, self.supplier, parent=self)
        if dialog.exec():
            # Refresh the dialog
            self.close()
            new_dialog = SupplierDetailsDialog(self.container, self.supplier, parent=self.parent())
            new_dialog.exec()
    
    def _on_record_payment(self):
        """Open record payment dialog"""
        from views.inventory.record_payment_dialog import RecordPaymentDialog
        dialog = RecordPaymentDialog(self.container, self.supplier, parent=self)
        if dialog.exec():
            # Refresh the dialog
            self.close()
            new_dialog = SupplierDetailsDialog(self.container, self.supplier, parent=self.parent())
            new_dialog.exec()
