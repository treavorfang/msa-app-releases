from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                               QHeaderView, QDoubleSpinBox, QLineEdit, QMessageBox,
                               QDateEdit, QGroupBox, QCheckBox, QComboBox)
from PySide6.QtCore import Qt, QDate
from config.constants import UIColors, InvoiceNumbering
from datetime import datetime
from utils.print.invoice_generator import InvoiceGenerator
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from views.components.money_input import MoneyInput

class CreateCustomerInvoiceDialog(QDialog):
    def __init__(self, container, ticket, user, parent=None):
        super().__init__(parent)
        self.container = container
        self.ticket = ticket
        self.user = user
        self.parts_used = []
        self.lm = language_manager
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Invoices.create_invoice_title', 'New Invoice')} - Ticket #{self.ticket.ticket_number}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Header Info
        info_group = QGroupBox(self.lm.get("Invoices.invoice_info", "Invoice Details"))
        info_layout = QFormLayout(info_group)
        
        self.invoice_number_input = QLineEdit()
        # Generate invoice number using constants
        date_str = datetime.now().strftime(InvoiceNumbering.DATE_FORMAT)
        
        # Get branch_id from user
        branch_id = 1
        try:
            if self.user and self.user.branch:
                branch_id = self.user.branch.id
        except Exception:
            pass
        
        try:
            # Get all invoices to find the max ID
            existing_invoices = self.container.invoice_controller.list_invoices()
            
            max_id = 0
            if existing_invoices:
                max_id = max(inv.id for inv in existing_invoices)
            
            # Calculate sequence based on ID: (max_id % 9999) + 1
            new_seq = (max_id % 9999) + 1
            
            seq_str = InvoiceNumbering.SEQUENCE_FORMAT.format(new_seq)
            invoice_num = InvoiceNumbering.FULL_FORMAT.format(
                prefix=InvoiceNumbering.PREFIX,
                branch_id=branch_id,
                date=date_str,
                sequence=seq_str
            )
                
            self.invoice_number_input.setText(invoice_num)
        except Exception:
            # Fallback
            seq_str = InvoiceNumbering.SEQUENCE_FORMAT.format(1)
            invoice_num = InvoiceNumbering.FULL_FORMAT.format(
                prefix=InvoiceNumbering.PREFIX,
                branch_id=branch_id,
                date=date_str,
                sequence=seq_str
            )
            self.invoice_number_input.setText(invoice_num)
            
        info_layout.addRow(f"{self.lm.get('Invoices.invoice_number', 'Invoice Number')}:", self.invoice_number_input)
        
        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_date.setCalendarPopup(True)
        info_layout.addRow(f"{self.lm.get('Invoices.date', 'Date')}:", self.invoice_date)
        
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(14))
        self.due_date.setCalendarPopup(True)
        info_layout.addRow(f"{self.lm.get('Invoices.due_date', 'Due Date')}:", self.due_date)
        
        customer_name = self.ticket.customer.name if self.ticket.customer else "Unknown"
        self.customer_label = QLabel(customer_name)
        info_layout.addRow(f"{self.lm.get('Invoices.customer', 'Customer')}:", self.customer_label)
        
        layout.addWidget(info_group)
        
        # Items Table
        items_group = QGroupBox(self.lm.get("Invoices.items", "Line Items"))
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            self.lm.get("Invoices.description_header", "Description"),
            self.lm.get("Invoices.item_header", "Type"),
            self.lm.get("Invoices.qty_header", "Quantity"),
            f"{self.lm.get('Invoices.unit_price_header', 'Unit Price')} ({currency_formatter.get_currency_symbol()})",
            f"{self.lm.get('Invoices.total_header', 'Total')} ({currency_formatter.get_currency_symbol()})"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.items_table.itemChanged.connect(self._on_item_changed)
        
        items_layout.addWidget(self.items_table)
        
        # Add Item Buttons
        btn_items_layout = QHBoxLayout()
        self.add_labor_btn = QPushButton(self.lm.get("Invoices.add_item", "Add Labor"))
        self.add_labor_btn.clicked.connect(self._add_labor_row)
        btn_items_layout.addWidget(self.add_labor_btn)
        
        self.add_custom_btn = QPushButton(self.lm.get("Invoices.add_item", "Add Custom Item"))
        self.add_custom_btn.clicked.connect(self._add_custom_row)
        btn_items_layout.addWidget(self.add_custom_btn)
        
        self.remove_item_btn = QPushButton(self.lm.get("Common.delete", "Remove Item"))
        self.remove_item_btn.clicked.connect(self._remove_item)
        btn_items_layout.addWidget(self.remove_item_btn)
        
        btn_items_layout.addStretch()
        items_layout.addLayout(btn_items_layout)
        
        layout.addWidget(items_group)
        
        # Bottom Section (Totals and Payment)
        bottom_layout = QHBoxLayout()
        
        # Payment Section
        payment_group = QGroupBox(self.lm.get("Invoices.record_payment_title", "Payment"))
        payment_layout = QFormLayout(payment_group)
        
        self.payment_method = QComboBox()
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            self.lm.get("Invoices.payment_method_cash", "Cash"),
            self.lm.get("Invoices.payment_method_card", "Card"),
            self.lm.get("Invoices.payment_method_bank", "Bank Transfer"),
            self.lm.get("Invoices.payment_method_check", "Check"),
            self.lm.get("Invoices.payment_method_other", "Other")
        ])
        payment_layout.addRow(f"{self.lm.get('Invoices.payment_method_label', 'Payment Method')}:", self.payment_method)
        
        # Payment Amount with Currency Symbol
        
        # Deposit Paid (Read-only)
        deposit_layout = QHBoxLayout()
        self.currency_label_dep = QLabel(currency_formatter.get_currency_symbol())
        self.deposit_input = MoneyInput()
        self.deposit_input.setPlaceholderText("0.00")
        self.deposit_input.setReadOnly(True)
        self.deposit_input.setStyleSheet("background-color: #f3f4f6; color: #374151;") # Grayed out
        deposit_layout.addWidget(self.currency_label_dep)
        deposit_layout.addWidget(self.deposit_input)
        payment_layout.addRow(f"{self.lm.get('Invoices.deposit_paid', 'Deposit Paid')}:", deposit_layout)
        
        # Remaining Balance (Read-only)
        remaining_layout = QHBoxLayout()
        self.currency_label_rem = QLabel(currency_formatter.get_currency_symbol())
        self.remaining_input = MoneyInput()
        self.remaining_input.setPlaceholderText("0.00")
        self.remaining_input.setReadOnly(True)
        self.remaining_input.setStyleSheet("font-weight: bold; color: #d35400; background-color: #f3f4f6;")
        remaining_layout.addWidget(self.currency_label_rem)
        remaining_layout.addWidget(self.remaining_input)
        payment_layout.addRow(f"{self.lm.get('Invoices.remaining_balance', 'Remaining Due')}:", remaining_layout)

        # Amount Paid Input
        amount_layout = QHBoxLayout()
        self.currency_label_pid = QLabel(currency_formatter.get_currency_symbol())
        self.amount_paid_input = MoneyInput()
        self.amount_paid_input.setPlaceholderText("0.00")
        self.amount_paid_input.textChanged.connect(self._calculate_change)
        amount_layout.addWidget(self.currency_label_pid)
        amount_layout.addWidget(self.amount_paid_input)
        
        payment_layout.addRow(f"{self.lm.get('Invoices.payment_amount', 'Amount Paid')}:", amount_layout)
        
        self.change_due_label = QLabel(currency_formatter.format(0))
        self.change_due_label.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 14px;")
        payment_layout.addRow("Change Due:", self.change_due_label)
        
        bottom_layout.addWidget(payment_group)
        
        # Totals Section
        total_group = QGroupBox("Summary")
        total_layout = QFormLayout(total_group)
        
        self.subtotal_label = QLabel(currency_formatter.format(0))
        self.subtotal_label.setAlignment(Qt.AlignRight)
        total_layout.addRow(f"{self.lm.get('Invoices.subtotal', 'Subtotal')}:", self.subtotal_label)
        
        # Tax Input
        tax_layout = QHBoxLayout()
        self.currency_label_tax = QLabel(currency_formatter.get_currency_symbol())
        self.tax_input = MoneyInput()
        self.tax_input.setPlaceholderText("0.00")
        self.tax_input.setAlignment(Qt.AlignRight)
        self.tax_input.textChanged.connect(self._calculate_total)
        tax_layout.addWidget(self.currency_label_tax)
        tax_layout.addWidget(self.tax_input)
        total_layout.addRow(f"{self.lm.get('Invoices.tax_amount', 'Tax')}:", tax_layout)
        
        # Discount Input
        discount_layout = QHBoxLayout()
        self.currency_label_disc = QLabel(currency_formatter.get_currency_symbol())
        self.discount_input = MoneyInput()
        self.discount_input.setPlaceholderText("0.00")
        self.discount_input.setAlignment(Qt.AlignRight)
        self.discount_input.textChanged.connect(self._calculate_total)
        discount_layout.addWidget(self.currency_label_disc)
        discount_layout.addWidget(self.discount_input)
        total_layout.addRow(f"{self.lm.get('Invoices.discount', 'Discount')}:", discount_layout)
        
        self.total_label = QLabel(currency_formatter.format(0))
        self.total_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #2ecc71;")
        self.total_label.setAlignment(Qt.AlignRight)
        total_layout.addRow(f"{self.lm.get('Invoices.grand_total', 'Total')}:", self.total_label)
        
        bottom_layout.addWidget(total_group)
        
        layout.addLayout(bottom_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.print_checkbox = QCheckBox(self.lm.get("Invoices.print_invoice", "Print Invoice"))
        # Load default state from settings
        try:
             settings = self.container.settings_service.get_user_settings(self.user.id if self.user else 1)
             self.print_checkbox.setChecked(settings.get('auto_print_invoice', True))
        except Exception:
             self.print_checkbox.setChecked(True)
        btn_layout.addWidget(self.print_checkbox)
        
        self.hide_prices_checkbox = QCheckBox(self.lm.get("Invoices.hide_prices", "Hide Item Prices"))
        self.hide_prices_checkbox.setToolTip(self.lm.get("Invoices.hide_prices_tooltip", "Hide unit prices and totals for individual items on the printed invoice"))
        btn_layout.addWidget(self.hide_prices_checkbox)
        
        btn_layout.addStretch()
        
        self.preview_btn = QPushButton(self.lm.get("Common.preview", "Preview"))
        self.preview_btn.clicked.connect(self._preview_invoice)
        btn_layout.addWidget(self.preview_btn)
        
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton(self.lm.get("Invoices.create_invoice_title", "Create Invoice"))
        self.create_btn.clicked.connect(self._create_invoice)
        self.create_btn.setDefault(True)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
        
        self.is_loading = False

    def _load_data(self):
        self.is_loading = True
        try:
            # Load parts
            self.parts_used = self.container.repair_part_controller.get_parts_used_in_ticket(self.ticket.id)
            
            for rp in self.parts_used:
                row = self.items_table.rowCount()
                self.items_table.insertRow(row)
                
                # Use flattened DTO fields instead of nested objects
                part_name = rp.part_name if rp.part_name else "Unknown Part"
                self.items_table.setItem(row, 0, QTableWidgetItem(part_name))
                
                type_item = QTableWidgetItem("Part")
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row, 1, type_item)
                
                qty_item = QTableWidgetItem(str(rp.quantity))
                qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row, 2, qty_item)
                
                # Part cost from DTO
                cost = float(rp.part_cost) if rp.part_cost else 0.0
                price = cost * 1.5
                self.items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
                
                total = price * rp.quantity
                total_item = QTableWidgetItem(f"{total:.2f}")
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row, 4, total_item)
                
                # Use scalar part_id from DTO
                self.items_table.item(row, 0).setData(Qt.UserRole, rp.part_id)
                self.items_table.item(row, 0).setData(Qt.UserRole + 1, "part")

            # Add labor row with smart auto-fill from ticket
            self._add_labor_row()
            
            # Pre-fill deposit paid from ticket
            deposit = float(self.ticket.deposit_paid) if self.ticket.deposit_paid else 0.0
            if deposit > 0:
                self.deposit_input.setValue(deposit)
                # Don't pre-fill amount paid - let user enter it
                # self.amount_paid_input.setText(f"{deposit:.2f}")
            
        finally:
            self.is_loading = False
            self._calculate_total()

    def _add_labor_row(self):
        # Disconnect momentarily to avoid trigger
        try:
            self.items_table.itemChanged.disconnect(self._on_item_changed)
        except:
            pass
            
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Calculate total price of parts already added to the table
        total_parts_price = 0.0
        for r in range(row):
            # Check if it's a part (stored in user data, or just assume rows before labor are parts)
            # Safe way: check the type column (col 1)
            type_item = self.items_table.item(r, 1)
            if type_item and type_item.text() == "Part":
                total_item = self.items_table.item(r, 4)
                if total_item:
                    try:
                        total_parts_price += float(total_item.text())
                    except ValueError:
                        pass

        # Smart auto-fill: Use ticket's actual_cost or estimated_cost
        # actual_cost typically represents the TOTAL billable amount (Parts + Labor)
        # So Labor = Total - Parts
        
        labor_cost = 50.00  # Default fallback
        cost_source = "default"
        
        if self.ticket.actual_cost and float(self.ticket.actual_cost) > 0:
            total_cost = float(self.ticket.actual_cost)
            labor_cost = max(0.0, total_cost - total_parts_price)
            cost_source = "actual"
        elif self.ticket.estimated_cost and float(self.ticket.estimated_cost) > 0:
            total_cost = float(self.ticket.estimated_cost)
            labor_cost = max(0.0, total_cost - total_parts_price)
            cost_source = "estimated"
            
        # Override for unrepairable/cancelled if no actual cost set
        if self.ticket.status in ['unrepairable', 'cancelled'] and cost_source != "actual":
            labor_cost = 0.00
            cost_source = "status_override"
        
        # Create description with indicator of source
        if cost_source == "actual":
            description = f"Repair Service / Labor (derived from actual total)"
        elif cost_source == "estimated":
            description = f"Repair Service / Labor (derived from estimate)"
        elif cost_source == "status_override":
            description = f"Repair Service / Labor (Waived - {self.ticket.status.title()})"
        else:
            description = "Repair Service / Labor"
        
        desc_item = QTableWidgetItem(description)
        desc_item.setToolTip(f"Labor charge calculated: Ticket {cost_source} cost ({self.ticket.actual_cost or self.ticket.estimated_cost}) - Parts Total ({total_parts_price:.2f}).")
        self.items_table.setItem(row, 0, desc_item)
        
        type_item = QTableWidgetItem("Service")
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 1, type_item)
        
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        
        # Make price editable - pre-filled from ticket but can be changed
        price_item = QTableWidgetItem(f"{labor_cost:.2f}")
        price_item.setToolTip(f"Auto-filled labor cost. Default: {labor_cost:.2f}")
        self.items_table.setItem(row, 3, price_item)
        
        total_item = QTableWidgetItem(f"{labor_cost:.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 4, total_item)
        
        # Store metadata
        self.items_table.item(row, 0).setData(Qt.UserRole, self.ticket.id)
        self.items_table.item(row, 0).setData(Qt.UserRole + 1, "service")
        self.items_table.item(row, 0).setData(Qt.UserRole + 2, cost_source)  # Store source for reference

        self.items_table.itemChanged.connect(self._on_item_changed)

    def _add_custom_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        self.items_table.setItem(row, 0, QTableWidgetItem("Custom Item"))
        
        type_item = QTableWidgetItem("Custom")
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 1, type_item)
        
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem("0.00"))
        
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 4, total_item)
        
        self.items_table.item(row, 0).setData(Qt.UserRole, None)
        self.items_table.item(row, 0).setData(Qt.UserRole + 1, "custom")

    def _remove_item(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            self._calculate_total()

    def _on_item_changed(self, item):
        if self.is_loading:
            return
            
        row = item.row()
        col = item.column()
        
        if col in [2, 3]:
            try:
                qty_item = self.items_table.item(row, 2)
                price_item = self.items_table.item(row, 3)
                total_item = self.items_table.item(row, 4)
                
                if qty_item and price_item and total_item:
                    qty = float(qty_item.text())
                    price = float(price_item.text())
                    total = qty * price
                    
                    total_item.setText(f"{total:.2f}")
                    self._calculate_total()
            except ValueError:
                pass

    def _calculate_total(self):
        subtotal = 0.0
        for row in range(self.items_table.rowCount()):
            item = self.items_table.item(row, 4)
            if item:
                try:
                    subtotal += float(item.text())
                except ValueError:
                    pass
        
        tax = self.tax_input.value()
        discount = self.discount_input.value()

        total = subtotal + tax - discount
        
        self.subtotal_label.setText(currency_formatter.format(subtotal))
        self.total_label.setText(currency_formatter.format(total))
        
        # Calculate Remaining
        deposit = self.deposit_input.value()
             
        remaining = total - deposit
        if remaining < 0:
            remaining = 0.0
            
        self.remaining_input.setValue(remaining)
        
        self._calculate_change()
        return total

    def _calculate_change(self):
        try:
            # Use Remaining instead of Total for change calculation
            remaining = self.remaining_input.value()
            paid = self.amount_paid_input.value()
                
            change = paid - remaining
            # if change < 0:
            #     change = 0.0
            self.change_due_label.setText(currency_formatter.format(change))
        except ValueError:
            pass

    def _get_invoice_data(self):
        """Collect data for invoice generation"""
        items = []
        for row in range(self.items_table.rowCount()):
            items.append({
                'description': self.items_table.item(row, 0).text(),
                'quantity': int(self.items_table.item(row, 2).text()),
                'unit_price': float(self.items_table.item(row, 3).text()),
                'total': float(self.items_table.item(row, 4).text())
            })
        
        customer_phone = self.ticket.customer.phone if self.ticket.customer and self.ticket.customer.phone else "N/A"
            
        return {
            'invoice_number': self.invoice_number_input.text(),
            'date': self.invoice_date.date().toString("yyyy-MM-dd"),
            'customer_name': self.ticket.customer.name if self.ticket.customer else "Unknown",
            'customer_phone': customer_phone,
            'ticket_number': self.ticket.ticket_number,
            'items': items,
            'subtotal': currency_formatter.parse(self.subtotal_label.text()),
            'tax': self.tax_input.value(),
            'discount': self.discount_input.value(),
            'total': currency_formatter.parse(self.total_label.text()),
            'deposit_paid': self.deposit_input.value(),
            'remaining_due': self.remaining_input.value(),
            'amount_paid': self.amount_paid_input.value(),
            'change_due': currency_formatter.parse(self.change_due_label.text()),
            # Add service details
            'device': f"{self.ticket.device.brand} {self.ticket.device.model}" if self.ticket.device else "Unknown Device",
            'issue': self.ticket.error or "No issue description"
        }

    def _preview_invoice(self):
        data = self._get_invoice_data()
        data['hide_item_prices'] = self.hide_prices_checkbox.isChecked()
        
        # Get print format preference
        user_settings = self.container.settings_service.get_user_settings(self.user.id)
        data['print_format'] = user_settings.get('print_format', 'Standard A5')
        
        generator = InvoiceGenerator(self, self.container.business_settings_service)
        generator.preview_invoice(data)

    def _create_invoice(self):
        """Create the invoice"""
        invoice_number = self.invoice_number_input.text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "Error", "Invoice number is required")
            return
            
        try:
            # Validate
            if self.items_table.rowCount() == 0:
                QMessageBox.warning(self, "Warning", "Cannot create empty invoice")
                return
                
            total_val = currency_formatter.parse(self.total_label.text())
            initial_status = 'unpaid'
            initial_paid_date = None
            
            # Auto-mark as paid if total is 0 (e.g., Warranty, Unrepairable)
            if total_val <= 0:
                initial_status = 'paid'
                initial_paid_date = datetime.now()

            # 1. Create Invoice
            invoice_data = {
                'invoice_number': invoice_number,
                'customer_id': self.ticket.customer.id if self.ticket.customer else None,
                'device_id': self.ticket.device.id if self.ticket.device else None,
                'subtotal': currency_formatter.parse(self.subtotal_label.text()),
                'tax': self.tax_input.value(),
                'discount': self.discount_input.value(),
                'total': total_val,
                'payment_status': initial_status,
                'due_date': self.due_date.date().toPython(), # Use existing due_date
                'paid_date': initial_paid_date,
                'created_by': self.user.id if self.user else None,
                'branch_id': self.user.branch_id if self.user and hasattr(self.user, 'branch_id') else 1, # Assuming default branch 1
                'error_description': self.ticket.error # Keep existing error_description
            }
            
            invoice = self.container.invoice_controller.create_invoice(invoice_data)
            
            if not invoice:
                raise Exception("Failed to create invoice record")
                
            # 2. Create Invoice Items
            for row in range(self.items_table.rowCount()):
                item_type = self.items_table.item(row, 0).data(Qt.UserRole + 1)
                item_id = self.items_table.item(row, 0).data(Qt.UserRole)
                
                if item_id is None:
                    item_id = 0 # Default to 0 if no specific ID (e.g., custom items)
                
                qty = float(self.items_table.item(row, 2).text())
                price = currency_formatter.parse(self.items_table.item(row, 3).text())
                total = currency_formatter.parse(self.items_table.item(row, 4).text())
                
                item_data = {
                    'invoice_id': invoice.id,
                    'item_type': item_type,
                    'item_id': item_id,
                    'description': self.items_table.item(row, 0).text(),
                    'quantity': int(qty), # Ensure quantity is int
                    'unit_price': price,
                    'total': total
                }
                
                self.container.invoice_controller.add_invoice_item(invoice.id, item_data)
            
            # 3. Update Ticket's actual_cost with final invoice total
            try:
                final_total = float(currency_formatter.parse(self.total_label.text()))
                self.container.ticket_service.update_ticket(
                    self.ticket.id,
                    {'actual_cost': final_total}
                )
            except Exception as e:
                print(f"Warning: Failed to update ticket cost: {e}")
                
            # 3.5. Record Deposit as Payment
            deposit_amount = self.deposit_input.value()

            if deposit_amount > 0:
                deposit_payment_data = {
                    'invoice': invoice.id,
                    'amount': min(deposit_amount, float(invoice.total)),
                    'payment_method': 'deposit', 
                    'paid_at': datetime.now(),
                    'received_by': self.user.id if self.user else None,
                    'notes': f"Deposit transferred from Ticket #{self.ticket.ticket_number}"
                }
                
                self.container.payment_controller.create_payment(
                    deposit_payment_data,
                    current_user=self.user,
                    ip_address='127.0.0.1'
                )

            # 4. Record Payment
            paid_amount = self.amount_paid_input.value()
            
            if paid_amount > 0:
                payment_data = {
                    'invoice': invoice.id,
                    'amount': min(paid_amount, float(invoice.total)),
                    'payment_method': self.payment_method.currentText().lower().replace(" ", "_"),
                    'paid_at': datetime.now(),
                    'received_by': self.user.id if self.user else None
                }
                
                self.container.payment_controller.create_payment(
                    payment_data,
                    current_user=self.user,
                    ip_address='127.0.0.1'
                )
                
                # Update status - check if Paid (Amount Paid + Deposit >= Total)
                # Note: We use invoice.total which is the strict db value
                
                deposit_val = self.deposit_input.value()
                total_paid_so_far = paid_amount + deposit_val
                
                if total_paid_so_far >= float(invoice.total) - 0.01: # Small epsilon
                    self.container.invoice_controller.update_invoice(
                        invoice.id,
                        {'payment_status': 'paid', 'paid_date': datetime.now()},
                        current_user=self.user
                    )
                else:
                    self.container.invoice_controller.update_invoice(
                        invoice.id,
                        {'payment_status': 'partially_paid'},
                        current_user=self.user
                    )

            # 5. Update Device Status to 'returned'
            if hasattr(self.ticket, 'device_id') and self.ticket.device_id:
                try:
                    if hasattr(self.container, 'device_controller'):
                        self.container.device_controller.update_device(
                            self.ticket.device_id,
                            {
                                'status': 'returned',
                                'completed_at': datetime.now()
                            },
                            current_user=self.user
                        )
                except Exception as e:
                    print(f"Warning updating device status: {e}")
            
            # 6. Print
            if self.print_checkbox.isChecked():
                data = self._get_invoice_data()
                data['hide_item_prices'] = self.hide_prices_checkbox.isChecked()
                # Add invoice number from created invoice
                data['invoice_number'] = invoice.invoice_number
                
                # Get print format preference
                user_settings = self.container.settings_service.get_user_settings(self.user.id)
                data['print_format'] = user_settings.get('print_format', 'Standard A5')
                
                generator = InvoiceGenerator(self, self.container.business_settings_service) # Pass self and business_settings_service
                generator.print_invoice(data)
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Invoices.invoice_created", "Invoice created successfully!"))
            self.accept()
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(tb)
            QMessageBox.critical(self, "Error", f"Failed to create invoice: {str(e)}\n\n{tb}")

