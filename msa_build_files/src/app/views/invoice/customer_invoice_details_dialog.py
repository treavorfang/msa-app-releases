from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                               QHeaderView, QGroupBox, QWidget, QFrame, QFileDialog)
from PySide6.QtCore import Qt, QSettings
import os
from utils.print.invoice_generator import InvoiceGenerator
from views.invoice.record_customer_payment_dialog import RecordCustomerPaymentDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class CustomerInvoiceDetailsDialog(QDialog):
    def __init__(self, container, invoice_id, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.invoice_id = invoice_id
        self.user = user
        self.invoice = None
        self.customer_name = "Unknown"
        self.lm = language_manager
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        self.invoice = self.container.invoice_controller.get_invoice(self.invoice_id)
        
        # Fetch customer name
        if self.invoice:
            if self.invoice.customer_name:
                self.customer_name = self.invoice.customer_name
            else:
                try:
                    for item in self.invoice.items:
                        if item.item_type == 'service':
                            ticket = self.container.ticket_controller.get_ticket(item.item_id)
                            if ticket and ticket.customer:
                                self.customer_name = ticket.customer.name
                            break
                except:
                    pass

    def _setup_ui(self):
        if not self.invoice:
            self.setWindowTitle("Error")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Invoice not found"))
            return

        self.setWindowTitle(f"{self.lm.get('Invoices.invoice_details_title', 'Invoice Details')} - {self.invoice.invoice_number}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        layout = QVBoxLayout(self)
        
        # Top Section: Info and Totals side-by-side
        top_layout = QHBoxLayout()
        
        # --- Left: Invoice Information ---
        info_group = QGroupBox(self.lm.get("Invoices.invoice_info", "Invoice Information"))
        info_layout = QFormLayout(info_group)
        info_layout.setLabelAlignment(Qt.AlignLeft)
        
        info_layout.addRow(f"{self.lm.get('Invoices.invoice_number', 'Invoice Number')}:", QLabel(self.invoice.invoice_number))
        
        date_str = self.invoice.created_at.strftime("%Y-%m-%d %H:%M") if self.invoice.created_at else "N/A"
        info_layout.addRow(f"{self.lm.get('Invoices.date', 'Date')}:", QLabel(date_str))
        
        due_date_str = self.invoice.due_date.strftime("%Y-%m-%d") if self.invoice.due_date else "N/A"
        info_layout.addRow(f"{self.lm.get('Invoices.due_date', 'Due Date')}:", QLabel(due_date_str))
        
        info_layout.addRow(f"{self.lm.get('Invoices.customer', 'Customer')}:", QLabel(self.customer_name))
        
        # Device & Issue
        if self.invoice.device_brand:
            device_str = f"{self.invoice.device_brand} {self.invoice.device_model or ''}"
            info_layout.addRow(f"{self.lm.get('Invoices.device', 'Device')}:", QLabel(device_str))
            
        if self.invoice.error_description:
            issue_label = QLabel(self.invoice.error_description)
            issue_label.setWordWrap(True)
            info_layout.addRow(f"{self.lm.get('Invoices.issue', 'Issue')}:", issue_label)
        
        status_label = QLabel(self.invoice.payment_status.upper().replace('_', ' '))
        status_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow(f"{self.lm.get('Invoices.status', 'Status')}:", status_label)
        
        top_layout.addWidget(info_group, stretch=3)
        
        # --- Right: Totals ---
        totals_group = QGroupBox(self.lm.get("Invoices.grand_total", "Totals"))
        totals_layout = QFormLayout(totals_group)
        totals_layout.setLabelAlignment(Qt.AlignLeft)
        
        # Helper for right aligned values
        def create_value_lbl(text, is_bold=False):
            l = QLabel(text)
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if is_bold:
                l.setStyleSheet("font-weight: bold; font-size: 16px;")
            return l
        
        totals_layout.addRow(f"{self.lm.get('Invoices.subtotal', 'Subtotal')}:", 
                             create_value_lbl(currency_formatter.format(self.invoice.subtotal)))
        
        totals_layout.addRow(f"{self.lm.get('Invoices.tax_amount', 'Tax')}:", 
                             create_value_lbl(currency_formatter.format(self.invoice.tax)))
        
        totals_layout.addRow(f"{self.lm.get('Invoices.discount', 'Discount')}:", 
                             create_value_lbl(currency_formatter.format(self.invoice.discount)))
        
        totals_layout.addRow(f"{self.lm.get('Invoices.grand_total', 'Total Due')}:", 
                             create_value_lbl(currency_formatter.format(self.invoice.total), is_bold=True))
        
        # Add a stretch to push totals to the top of the group box if needed, 
        # but FormLayout usually handles it. 
        # Making the totals column narrower than info column
        top_layout.addWidget(totals_group, stretch=2)
        
        layout.addLayout(top_layout)
        
        # Items Table
        items_group = QGroupBox(self.lm.get("Invoices.items", "Line Items"))
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            self.lm.get("Invoices.description_header", "Description"),
            self.lm.get("Invoices.qty_header", "Quantity"),
            self.lm.get("Invoices.unit_price_header", "Unit Price"),
            self.lm.get("Invoices.total_header", "Total")
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        for item in self.invoice.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            desc = item.item_name or "Unknown Item"
            # Fallback descriptions if name not hydrated or generic
            if item.item_type == 'service' and (not item.item_name or item.item_name.startswith("Item #")):
                 desc = "Repair Service / Labor"
            elif item.item_type == 'custom' and not item.item_name:
                 desc = "Custom Item"
            
            self.items_table.setItem(row, 0, QTableWidgetItem(desc))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            self.items_table.setItem(row, 2, QTableWidgetItem(currency_formatter.format(item.unit_price)))
            self.items_table.setItem(row, 3, QTableWidgetItem(currency_formatter.format(item.total)))
            
        items_layout.addWidget(self.items_table)
        layout.addWidget(items_group)
        
        # Payments
        payments_group = QGroupBox(self.lm.get("Invoices.payment_history", "Payment History"))
        payments_layout = QVBoxLayout(payments_group)
        
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels([
            self.lm.get("Invoices.payment_date", "Date"),
            self.lm.get("Invoices.payment_method", "Method"),
            self.lm.get("Invoices.payment_amount", "Amount")
        ])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        total_paid = 0
        for payment in self.invoice.payments:
            row = self.payments_table.rowCount()
            self.payments_table.insertRow(row)
            
            date_str = payment.paid_at.strftime("%Y-%m-%d %H:%M") if payment.paid_at else "N/A"
            self.payments_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.payments_table.setItem(row, 1, QTableWidgetItem(payment.payment_method))
            self.payments_table.setItem(row, 2, QTableWidgetItem(currency_formatter.format(payment.amount)))
            total_paid += float(payment.amount)
            
        payments_layout.addWidget(self.payments_table)
        layout.addWidget(payments_group)
        
        # Balance
        balance = float(self.invoice.total) - total_paid
        balance_label = QLabel(f"{self.lm.get('Invoices.balance', 'Balance Due')}: {currency_formatter.format(balance)}")
        if balance > 0.01: # Tolerance for float
            balance_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        else:
            balance_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        layout.addWidget(balance_label)
        
        # Payment Actions
        if balance > 0.01:
            pay_btn = QPushButton(self.lm.get("Invoices.record_payment", "Add Payment"))
            pay_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
            pay_btn.clicked.connect(self._add_payment)
            layout.addWidget(pay_btn)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.print_btn = QPushButton(self.lm.get("Invoices.print_invoice", "Print Invoice"))
        self.print_btn.clicked.connect(self._print_invoice)
        btn_layout.addWidget(self.print_btn)
        
        self.preview_btn = QPushButton(self.lm.get("Common.preview", "Preview"))
        self.preview_btn.clicked.connect(self._preview_invoice)
        btn_layout.addWidget(self.preview_btn)
        
        self.save_pdf_btn = QPushButton(self.lm.get("Common.save_pdf", "Save PDF"))
        self.save_pdf_btn.clicked.connect(self._save_pdf)
        btn_layout.addWidget(self.save_pdf_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _get_invoice_data(self):
        items = []
        for row in range(self.items_table.rowCount()):
            items.append({
                'description': self.items_table.item(row, 0).text(),
                'quantity': int(self.items_table.item(row, 1).text()),
                'unit_price': currency_formatter.parse(self.items_table.item(row, 2).text()),
                'total': currency_formatter.parse(self.items_table.item(row, 3).text())
            })
            
        total_paid = 0
        for payment in self.invoice.payments:
            total_paid += float(payment.amount)
        
        # Get customer phone
        customer_phone = self.invoice.customer_phone or "N/A"
        if not self.invoice.customer_phone:
            try:
                for item in self.invoice.items:
                    if item.item_type == 'service':
                        ticket = self.container.ticket_controller.get_ticket(item.item_id)
                        if ticket and ticket.customer and ticket.customer.phone:
                            customer_phone = ticket.customer.phone
                        break
            except:
                pass
            
        # Get user settings for print format
        print_format = 'Standard A5'
        if self.user and self.container.settings_service:
            try:
                settings = self.container.settings_service.get_user_settings(self.user.id)
                print_format = settings.get('print_format', 'Standard A5')
            except Exception:
                pass
            
        return {
            'invoice_number': self.invoice.invoice_number,
            'date': self.invoice.created_at.strftime("%Y-%m-%d"),
            'customer_name': self.customer_name,
            'customer_phone': customer_phone,
            'ticket_number': self._get_ticket_number(),
            'device': f"{self.invoice.device_brand} {self.invoice.device_model or ''}" if self.invoice.device_brand else "N/A",
            'issue': self.invoice.error_description or "N/A",
            'items': items,
            'subtotal': float(self.invoice.subtotal),
            'tax': float(self.invoice.tax),
            'discount': float(self.invoice.discount),
            'total': float(self.invoice.total),
            'amount_paid': total_paid,
            'change_due': 0,
            'print_format': print_format
        }

    def _get_ticket_number(self):
        try:
            for item in self.invoice.items:
                if item.item_type == 'service':
                    ticket = self.container.ticket_controller.get_ticket(item.item_id)
                    if ticket:
                        return ticket.ticket_number
        except:
            pass
        return "N/A"

    def _add_payment(self):
        dialog = RecordCustomerPaymentDialog(self.container, self.invoice, self.user, self)
        if dialog.exec():
            self._load_data()
            # Refresh UI - easiest way is to close and reopen or manually update fields
            # For now, let's just close and let the parent refresh, or we can try to refresh in-place
            # But _setup_ui adds widgets, so calling it again would duplicate them.
            # Ideally we should have separate _update_ui method.
            # Since the parent (ModernInvoiceTab) refreshes on dialog close, accepting here is fine
            # But user might want to see the updated balance.
            # Let's just accept to close and refresh parent list.
            self.accept()

    def _print_invoice(self):
        data = self._get_invoice_data()
        generator = InvoiceGenerator(self, self.container.business_settings_service)
        generator.print_invoice(data)

    def _preview_invoice(self):
        data = self._get_invoice_data()
        generator = InvoiceGenerator(self, self.container.business_settings_service)
        generator.preview_invoice(data)

    def _save_pdf(self):
        try:
            data = self._get_invoice_data()
            generator = InvoiceGenerator(self, self.container.business_settings_service)
            
            # Use safe filename logic
            invoice_number = data.get('invoice_number', 'Invoice')
            safe_filename = f"Invoice-{invoice_number.replace('/', '-').replace('\\', '-')}.pdf"
            
            # Prompt user for location
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                self.lm.get("Invoices.save_pdf_dialog", "Save Invoice as PDF"),
                os.path.join(os.path.expanduser("~/Desktop"), safe_filename),
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                generator._print_to_pdf(data, file_path)
                from utils.validation.message_handler import MessageHandler
                MessageHandler.show_info(self, "Success", f"Invoice saved to {file_path}")
                
        except Exception as e:
            from utils.validation.message_handler import MessageHandler
            MessageHandler.show_critical(self, "Error", f"Failed to save PDF: {str(e)}")
