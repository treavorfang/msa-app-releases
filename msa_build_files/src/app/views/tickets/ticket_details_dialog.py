# src/app/views/tickets/ticket_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QGroupBox, QTabWidget, 
                              QWidget, QTableWidget, QTableWidgetItem, QHeaderView, 
                              QMessageBox, QComboBox, QDialogButtonBox, QTextEdit)
from PySide6.QtCore import Qt
from datetime import datetime
from views.tickets.add_part_dialog import AddPartDialog
from views.tickets.ticket_base import TicketBaseDialog
from utils.print.ticket_generator import TicketReceiptGenerator
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
import traceback

class TicketDetailsDialog(TicketBaseDialog):
    """Dialog for viewing detailed ticket information"""
    
    def __init__(self, 
                 ticket, 
                 ticket_service,
                 ticket_controller,
                 technician_controller,
                 repair_part_controller,
                 work_log_controller,
                 business_settings_service,
                 part_service,
                 technician_repository,
                 user,
                 container=None,
                 parent=None):
        # Initialize the base class first (QDialog part)
        super().__init__(parent)
        
        # Then set up our ticket-specific attributes
        self.ticket = ticket
        self.ticket_service = ticket_service
        self.ticket_controller = ticket_controller
        self.technician_controller = technician_controller
        self.repair_part_controller = repair_part_controller
        self.work_log_controller = work_log_controller
        self.business_settings_service = business_settings_service
        self.part_service = part_service
        self.technician_repository = technician_repository
        self.user = user
        self.container = container # Legacy support
        
        # Initialize language and currency formatters
        self.lm = language_manager
        self.cf = currency_formatter
        
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Tickets.ticket_details', 'Ticket Details')} - #{self.ticket.ticket_number}")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Header with ticket number and status
        header_layout = QHBoxLayout()
        
        title = QLabel(f"🎫 {self.lm.get('Tickets.ticket_number', 'Ticket')} #{self.ticket.ticket_number}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Status badge - using base class method
        status_color = self.get_status_color(self.ticket.status)
        status_key = f"Common.{self.ticket.status}"
        status_text = self.lm.get(status_key, self.ticket.status.replace('_', ' ').title())
        status_badge = QLabel(f" {status_text} ")
        status_badge.setStyleSheet(f"""
            background-color: {status_color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
        header_layout.addWidget(status_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different sections
        self.tabs = QTabWidget()
        
        # General Info Tab
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, self.lm.get("Tickets.general_info", "General Info"))
        
        # Financials Tab
        financial_tab = self._create_financial_tab()
        self.tabs.addTab(financial_tab, self.lm.get("Tickets.financials", "Financials"))
        
        # Technician Tab
        tech_tab = self._create_tech_tab()
        self.tabs.addTab(tech_tab, self.lm.get("Tickets.tech_notes", "Technician Notes"))

        # Parts Used Tab
        parts_tab = self._create_parts_tab()
        self.tabs.addTab(parts_tab, self.lm.get("Tickets.parts_used", "Parts Used"))
        
        # Work Log Tab
        work_log_tab = self._create_work_log_widget()
        self.tabs.addTab(work_log_tab, self.lm.get("Tickets.work_log", "Work Log"))
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()

        # Action buttons (only if not deleted)
        if not self.ticket.is_deleted and self.user:
            # Combined Update Ticket button (status + technician)
            update_ticket_btn = QPushButton(f"📝 {self.lm.get('Tickets.update_ticket', 'Update Ticket')}")
            update_ticket_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px;")
            update_ticket_btn.clicked.connect(self._update_ticket)
            button_layout.addWidget(update_ticket_btn)
            
            # Edit Ticket Button
            edit_btn = QPushButton(f"✏️ {self.lm.get('Tickets.edit_ticket', 'Edit Ticket')}")
            edit_btn.clicked.connect(self._edit_ticket)
            button_layout.addWidget(edit_btn)
            
            # Preview Ticket Button
            preview_btn = QPushButton(f"👁️ {self.lm.get('Common.preview', 'Preview')}")
            preview_btn.clicked.connect(self._preview_ticket)
            button_layout.addWidget(preview_btn)
            
            # Store as instance variable so we can update it later
            self.create_invoice_btn = QPushButton(f"💰 {self.lm.get('TicketActions.create_invoice', 'Create Invoice')}")
            self.create_invoice_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px;")
            self.create_invoice_btn.clicked.connect(self._create_invoice)
            
            # Update button state
            self._update_create_invoice_button()
            
            button_layout.addWidget(self.create_invoice_btn)

        button_layout.addStretch()

        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
    
    def _create_general_tab(self):
        """Create general information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Customer & Device Group
        info_group = QGroupBox(self.lm.get("Tickets.customer_device", "Customer & Device"))
        info_layout = QFormLayout(info_group)
        
        customer_name = self.ticket.customer.name if self.ticket.customer else self.lm.get("Common.unknown", "Unknown")
        customer_phone = self.ticket.customer.phone if self.ticket.customer else self.lm.get("Common.not_applicable", "N/A")
        info_layout.addRow(self.lm.get("Tickets.customer", "Customer") + ":", QLabel(f"<b>{customer_name}</b> ({customer_phone})"))
        
        device_name = f"{self.ticket.device.brand} {self.ticket.device.model}" if self.ticket.device else self.lm.get("Tickets.unknown_device", "Unknown Device")
        info_layout.addRow(self.lm.get("Tickets.device", "Device") + ":", QLabel(device_name))
        
        info_layout.addRow(self.lm.get("Tickets.issue", "Issue") + ":", QLabel(self.ticket.error or self.lm.get("Common.not_applicable", "N/A")))
        
        # priority_color = "red" if self.ticket.priority == "high" else "orange" if self.ticket.priority == "medium" else "green"
        # FIXED: Localized priority with color coding for all priorities including critical
        priority_color_map = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred',  # Added critical priority
        }
        
        priority_color = priority_color_map.get(self.ticket.priority, 'gray')

        # priority_label = QLabel(f"<span style='color: {priority_color}; font-weight: bold;'>{self.ticket.priority.upper()}</span>")
        # Get localized priority text
        priority_key = f"Common.{self.ticket.priority}"
        priority_text = self.lm.get(priority_key, self.ticket.priority.upper())
        
        priority_label = QLabel(f"<span style='color: {priority_color}; font-weight: bold;'>{priority_text}</span>")
        info_layout.addRow(self.lm.get("Tickets.priority", "Priority") + ":", priority_label)
        
        layout.addWidget(info_group)
        
        # Dates Group
        date_group = QGroupBox(self.lm.get("Tickets.timeline", "Timeline"))
        date_layout = QFormLayout(date_group)
        
        created_at = self.ticket.created_at.strftime("%Y-%m-%d %H:%M") if self.ticket.created_at else self.lm.get("Common.not_applicable", "N/A")
        date_layout.addRow(self.lm.get("Tickets.created", "Created") + ":", QLabel(created_at))
        
        deadline = self.ticket.deadline.strftime("%Y-%m-%d") if self.ticket.deadline else self.lm.get("Tickets.no_deadline", "No Deadline")
        date_layout.addRow(self.lm.get("Tickets.deadline", "Deadline") + ":", QLabel(deadline))
        
        completed_at = self.ticket.completed_at.strftime("%Y-%m-%d %H:%M") if self.ticket.completed_at else self.lm.get("Tickets.not_completed", "Not Completed")
        date_layout.addRow(self.lm.get("Tickets.completed", "Completed") + ":", QLabel(completed_at))
        
        layout.addWidget(date_group)
        layout.addStretch()
        
        return widget
    
    def _create_financial_tab(self):
        """Create financial information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        finance_group = QGroupBox(self.lm.get("Tickets.cost_breakdown", "Cost Breakdown"))
        finance_layout = QFormLayout(finance_group)
        
        est_cost = float(self.ticket.estimated_cost)
        finance_layout.addRow(self.lm.get("Tickets.estimated_cost", "Estimated Cost") + ":", QLabel(self.cf.format(est_cost)))
        
        actual_cost = float(self.ticket.actual_cost)
        finance_layout.addRow(self.lm.get("Tickets.actual_cost", "Actual Cost") + ":", QLabel(f"<b>{self.cf.format(actual_cost)}</b>"))
        
        deposit = float(self.ticket.deposit_paid)
        finance_layout.addRow(self.lm.get("Tickets.deposit", "Deposit Paid") + ":", QLabel(self.cf.format(deposit)))
        
        # Calculate balance
        total = actual_cost if actual_cost > 0 else est_cost
        balance = total - deposit
        
        balance_label = QLabel(f"<b>{self.cf.format(balance)}</b>")
        if balance > 0:
            balance_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
        else:
            balance_label.setStyleSheet("color: #2ecc71; font-size: 14px;")
            
        finance_layout.addRow(self.lm.get("Tickets.balance_due", "Balance Due") + ":", balance_label)
        
        layout.addWidget(finance_group)
        
        # Warranty
        warranty_group = QGroupBox(self.lm.get("Tickets.warranty", "Warranty"))
        warranty_layout = QFormLayout(warranty_group)
        
        is_covered = self.lm.get("Common.yes", "Yes") if self.ticket.warranty_covered else self.lm.get("Common.no", "No")
        warranty_layout.addRow(self.lm.get("Tickets.warranty_covered", "Warranty Covered") + ":", QLabel(is_covered))
        
        layout.addWidget(warranty_group)
        layout.addStretch()
        
        return widget

    def _create_tech_tab(self):
        """Create technician notes tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        tech_group = QGroupBox(self.lm.get("Tickets.assignment", "Assignment"))
        tech_layout = QFormLayout(tech_group)
        
        tech_name = self.ticket.technician_name or self.lm.get("Tickets.unassigned", "Unassigned")
        tech_layout.addRow(self.lm.get("Tickets.technician", "Technician") + ":", QLabel(f"<b>{tech_name}</b>"))
        
        layout.addWidget(tech_group)
        
        # Description
        desc_group = QGroupBox(self.lm.get("Tickets.detailed_desc", "Detailed Description"))
        desc_layout = QVBoxLayout(desc_group)
        
        desc_text = self.ticket.error_description or self.lm.get("Tickets.no_detailed_description", "No detailed description provided.")
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_layout.addWidget(desc_label)
        
        layout.addWidget(desc_group)
        
        # Internal Notes
        notes_group = QGroupBox(self.lm.get("Tickets.internal_notes", "Internal Notes"))
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setPlainText(self.ticket.internal_notes or "")
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_text)
        
        update_notes_btn = QPushButton(self.lm.get("Tickets.update_notes", "Update Notes"))
        update_notes_btn.clicked.connect(self._update_internal_notes)
        notes_layout.addWidget(update_notes_btn)
        
        layout.addWidget(notes_group)
        layout.addStretch()
        
        return widget

    def _edit_ticket(self):
        """Open ticket in edit mode using the legacy ticket receipt"""
        if self.user:
            self.hide()  # Hide the details dialog instead of closing it
            self.ticket_controller.show_edit_ticket_form(self.ticket.id, self)

    def _preview_ticket(self):
        # Get user print preference
        print_format = 'Standard A5'
        if self.container and self.user:
            settings = self.container.settings_service.get_user_settings(self.user.id)
            print_format = settings.get('print_format', 'Standard A5')

        generator = TicketReceiptGenerator(self, self.business_settings_service)
        print_data = {
            'print_format': print_format,
            'customer_name': self.ticket.customer.name if self.ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_phone': self.ticket.customer.phone if self.ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_email': self.ticket.customer.email if self.ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_address': self.ticket.customer.address if self.ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'brand': self.ticket.device.brand if self.ticket.device else '',
            'model': self.ticket.device.model if self.ticket.device else '',
            'imei': self.ticket.device.imei if self.ticket.device else '',
            'serial_number': self.ticket.device.serial_number if self.ticket.device else '',
            'color': self.ticket.device.color if self.ticket.device else '',
            'condition': self.ticket.device.condition if self.ticket.device else '',
            'lock_type': self.ticket.device.lock_type if self.ticket.device else '',
            'passcode': self.ticket.device.passcode if self.ticket.device else '',
            'issue_type': self.ticket.error or self.lm.get('Common.not_applicable', 'N/A'),
            'description': self.ticket.error_description or self.ticket.error or self.lm.get('Common.not_applicable', 'N/A'),
            'accessories': self.ticket.accessories or '',
            'deadline': self.ticket.deadline.strftime("%Y-%m-%d") if self.ticket.deadline else self.lm.get('Common.not_applicable', 'N/A'),
            'estimated_cost': self.ticket.estimated_cost or 0.0,
            'deposit_paid': self.ticket.deposit_paid or 0.0,
            'ticket_number': self.ticket.ticket_number
        }
        generator.preview_ticket(print_data)

    def _update_internal_notes(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Tickets.update_internal_notes", "Update Internal Notes"))
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(self.ticket.internal_notes or "")
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            new_notes = text_edit.toPlainText()
            try:
                self.ticket_controller.update_ticket(self.ticket.id, {'internal_notes': new_notes}, current_user=self.user, ip_address='127.0.0.1')
                self.ticket.internal_notes = new_notes
                self.notes_text.setPlainText(new_notes)
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("TicketMessages.notes_updated", "Internal notes updated."))
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.notes_update_failed', 'Failed to update notes')}: {str(e)}")

    def _create_parts_tab(self):
        """Create parts used tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Parts Table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        headers = [
            self.lm.get("Tickets.part_name_col", "Part Name"),
            self.lm.get("Tickets.sku", "SKU"),
            self.lm.get("Tickets.quantity_col", "Quantity"),
            self.lm.get("Tickets.cost_col", "Unit Cost"),
            self.lm.get("Tickets.total", "Total")
        ]
        self.parts_table.setHorizontalHeaderLabels(headers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.parts_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_part_btn = QPushButton(self.lm.get("TicketActions.add_part", "Add Part"))
        self.add_part_btn.clicked.connect(self._on_add_part)
        # Only enable if we have container context (needed for controllers)
        self.add_part_btn.setEnabled(True)
        
        self.remove_part_btn = QPushButton(self.lm.get("TicketActions.remove_part", "Remove Part"))
        self.remove_part_btn.clicked.connect(self._on_remove_part)
        self.remove_part_btn.setEnabled(True)
        
        btn_layout.addWidget(self.add_part_btn)
        btn_layout.addWidget(self.remove_part_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Load initial data
        self._load_parts_used()
            
        return widget

    def _load_parts_used(self):
        """Load parts used for this ticket"""
        if not self.container:
            return

        try:
            # Get all parts for the ticket
            ticket_parts = self.repair_part_controller.get_parts_used_in_ticket(self.ticket.id)
            
            self.parts_table.setRowCount(len(ticket_parts))
            
            total_parts_cost = 0
            
            for row, rp in enumerate(ticket_parts):
                self.parts_table.setItem(row, 0, QTableWidgetItem(rp.part_name or self.lm.get("Common.unknown", "Unknown")))
                self.parts_table.setItem(row, 1, QTableWidgetItem(rp.part_sku or ""))
                self.parts_table.setItem(row, 2, QTableWidgetItem(str(rp.quantity)))
                
                unit_cost = float(rp.part_cost) if rp.part_cost is not None else 0
                self.parts_table.setItem(row, 3, QTableWidgetItem(self.cf.format(unit_cost)))
                
                total = rp.quantity * unit_cost
                self.parts_table.setItem(row, 4, QTableWidgetItem(self.cf.format(total)))
                
                total_parts_cost += total
                
                # Store ID
                self.parts_table.item(row, 0).setData(Qt.UserRole, rp.id)
                
        except Exception as e:
            print(f"{self.lm.get('Common.error', 'Error')} loading parts: {e}")

    def _on_add_part(self):
        """Handle adding a part"""
        if not self.user:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("TicketMessages.system_context_missing", "System context missing"))
            return
            
        dialog = AddPartDialog(self.container, self.ticket, self)
        if dialog.exec():
            part, quantity = dialog.get_selected_part_data()
            if part:
                try:
                    # Look up technician ID for current user
                    tech_id = None
                    if self.user and self.user.email:
                        techs = self.technician_repository.search(self.user.email)
                        if techs:
                            tech_id = techs[0].id
                            
                    # Pass IDs directly to controller
                    self.repair_part_controller.create_repair_part(
                        ticket_id=self.ticket.id,
                        part_id=part.id,
                        technician_id=tech_id,
                        current_user=self.user,
                        quantity=quantity
                    )
                    
                    self._load_parts_used()
                    QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("TicketMessages.part_added_success", "Part added successfully"))
                    
                except Exception as e:
                    QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.part_add_failed', 'Failed to add part')}: {str(e)}")

    def _on_remove_part(self):
        """Handle removing a part"""
        selected_rows = self.parts_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        repair_part_id = self.parts_table.item(row, 0).data(Qt.UserRole)
        
        # Localize the confirmation dialog
        if QMessageBox.question(
            self, 
            self.lm.get("Common.confirm", "Confirm"),
            self.lm.get("TicketMessages.confirm_remove_part", "Remove this part from the ticket?")
            ) == QMessageBox.Yes:
            try:
                self.repair_part_controller.delete_repair_part(repair_part_id)
                self._load_parts_used()
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.part_remove_failed', 'Failed to remove part')}: {str(e)}")
    
    def _update_ticket(self):
        """Show combined dialog to update ticket status and assign technician"""
        from PySide6.QtWidgets import QInputDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.lm.get('Tickets.update_ticket', 'Update Ticket')} - #{self.ticket.ticket_number}")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Status dropdown - store English values as data
        status_combo = QComboBox()
        
        # Define status options with English keys and localized display text
        status_options = [
            ('open', self.lm.get("Common.open", "Open")),
            ('diagnosed', self.lm.get("Common.diagnosed", "Diagnosed")),
            ('in_progress', self.lm.get("Common.in_progress", "In Progress")),
            ('awaiting_parts', self.lm.get("Common.awaiting_parts", "Awaiting Parts")),
            ('completed', self.lm.get("Common.completed", "Completed")),
            ('cancelled', self.lm.get("Common.cancelled", "Cancelled")),
            ('unrepairable', self.lm.get("Common.unrepairable", "Unrepairable"))
        ]
        
        for status_key, status_label in status_options:
            status_combo.addItem(status_label, status_key)  # Display text, stored data
        
        # Preselect current status by finding the matching data value
        current_status_index = status_combo.findData(self.ticket.status)
        if current_status_index >= 0:
            status_combo.setCurrentIndex(current_status_index)
        
        layout.addRow(f"{self.lm.get('Tickets.status', 'Status')}:", status_combo)
        
        # Technician dropdown
        tech_combo = QComboBox()
        tech_combo.addItem(self.lm.get("Tickets.not_assigned", "Not Assigned"), None)
        
        # Load technicians
        try:
            technicians = self.technician_controller.list_technicians(active_only=True)
            for tech in technicians:
                name = tech.full_name if tech.full_name else f"{self.lm.get('Tickets.technician', 'Technician')} #{tech.id}"
                tech_combo.addItem(name, tech.id)
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.load_technicians_failed', 'Failed to load technicians')}: {str(e)}")
            return
        
        # Preselect current technician
        if self.ticket.assigned_technician_id:
            index = tech_combo.findData(self.ticket.assigned_technician_id)
            if index >= 0:
                tech_combo.setCurrentIndex(index)
        
        layout.addRow(f"{self.lm.get('Tickets.technician', 'Technician')}:", tech_combo)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec() == QDialog.Accepted:
            # Get the English status value from combo box data (not the display text)
            new_status = status_combo.currentData()
            new_tech_id = tech_combo.currentData()
            
            status_changed = new_status != self.ticket.status
            tech_changed = new_tech_id != self.ticket.assigned_technician_id
            
            if not status_changed and not tech_changed:
                QMessageBox.information(self, self.lm.get("TicketMessages.no_changes_title", "No Changes"), self.lm.get("TicketMessages.no_changes", "No changes were made to the ticket."))
                return
            
            try:
                # Update status if changed
                if status_changed:
                    updated_ticket = self.ticket_controller.change_ticket_status(
                        ticket_id=self.ticket.id,
                        new_status=new_status,
                        reason=self.lm.get("TicketMessages.status_updated_from_details", "Status updated from ticket details"),
                        current_user=self.user,
                        ip_address='127.0.0.1'
                    )
                    if updated_ticket:
                        self.ticket = updated_ticket
                
                # Update technician if changed
                if tech_changed:
                    # Prompt for reason if transferring FROM a technician (not just assigning for first time)
                    transfer_reason = None
                    if self.ticket.assigned_technician_id and new_tech_id:
                        reason_text, ok = QInputDialog.getText(
                            self, 
                            self.lm.get("Tickets.transfer_reason_title", "Transfer Reason"),
                            self.lm.get("Tickets.enter_transfer_reason", "Reason for transferring to new technician:"),
                        )
                        if ok and reason_text:
                            transfer_reason = reason_text
                    
                    updated_ticket = self.ticket_controller.assign_ticket(
                        ticket_id=self.ticket.id,
                        technician_id=new_tech_id,
                        reason=transfer_reason,
                        current_user=self.user,
                        ip_address='127.0.0.1'
                    )
                    if updated_ticket:
                        self.ticket = updated_ticket
                
                # Build success message
                changes = []
                if status_changed:
                    changes.append(f"{self.lm.get('Tickets.status', 'Status')} → {status_combo.currentText()}")
                if tech_changed:
                    changes.append(f"{self.lm.get('Tickets.technician', 'Technician')} → {tech_combo.currentText()}")
                
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), f"{self.lm.get('TicketMessages.ticket_updated', 'Ticket updated')}:\n" + "\n".join(changes))
                
                # Refresh the UI to reflect changes instead of closing
                self._refresh_ui()
                
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"Ticket Update Error: {error_trace}")
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.update_failed', 'Failed to update ticket')}: {str(e)}\n\nDebug Info:\n{error_trace}")
    
    def _update_status(self):
        """Legacy method - redirects to combined update"""
        self._update_ticket()
    
    def _assign_technician(self):
        """Legacy method - redirects to combined update"""
        self._update_ticket()
    
    def _update_create_invoice_button(self):
        """Update the create invoice button state based on ticket status"""
        if not hasattr(self, 'create_invoice_btn'):
            return
            
        # Enable only if completed/cancelled/unrepairable
        if self.ticket.status not in ['completed', 'cancelled', 'unrepairable']:
            self.create_invoice_btn.setEnabled(False)
            self.create_invoice_btn.setToolTip(self.lm.get("TicketMessages.invoice_only_for_completed", "Invoice can only be created for completed, cancelled, or unrepairable tickets"))
        elif self.ticket.device and self.ticket.device.status == 'returned':
            self.create_invoice_btn.setEnabled(False)
            self.create_invoice_btn.setToolTip(self.lm.get("TicketMessages.invoice_already_created", "Invoice already created - device has been returned"))
        else:
            self.create_invoice_btn.setEnabled(True)
            self.create_invoice_btn.setToolTip("")
    
    def _refresh_ui(self):
        """Refresh the UI to reflect current ticket state"""
        # Reload ticket data from database to get latest changes
        try:
            refreshed_ticket = self.ticket_service.get_ticket(self.ticket.id)
            if refreshed_ticket:
                self.ticket = refreshed_ticket
        except Exception as e:
            print(f"Error reloading ticket data: {e}")
        
        # Update window title
        self.setWindowTitle(f"{self.lm.get('Tickets.ticket_details', 'Ticket Details')} - #{self.ticket.ticket_number}")
        
        # Update create invoice button
        self._update_create_invoice_button()
        
        # Refresh work log tab to show updated data
        try:
            # Find the work log tab and refresh it
            work_log_tab_index = None
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == self.lm.get("Tickets.work_log", "Work Log"):
                    work_log_tab_index = i
                    break
            
            if work_log_tab_index is not None:
                # Remove old work log widget
                old_widget = self.tabs.widget(work_log_tab_index)
                if old_widget:
                    self.tabs.removeTab(work_log_tab_index)
                    old_widget.deleteLater()
                
                # Create new work log widget with updated data
                new_work_log_widget = self._create_work_log_widget()
                self.tabs.insertTab(work_log_tab_index, new_work_log_widget, self.lm.get("Tickets.work_log", "Work Log"))
                
                # Switch to the work log tab to show the update
                self.tabs.setCurrentIndex(work_log_tab_index)
        except Exception as e:
            print(f"Error refreshing work log: {e}")
            import traceback
            traceback.print_exc()

    def _create_invoice(self):
        """Show dialog to create invoice for ticket"""
        try:
            from views.invoice.create_customer_invoice_dialog import CreateCustomerInvoiceDialog
            dialog = CreateCustomerInvoiceDialog(self.container, self.ticket, self.user, self)
            dialog.exec()
        except ImportError:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), self.lm.get("TicketMessages.invoice_dialog_import_error", "Could not import CreateCustomerInvoiceDialog"))
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.invoice_dialog_open_error', 'Failed to open invoice dialog')}: {str(e)}")
    
    def _create_work_log_widget(self):
        """Create work log tab showing time tracking for this ticket"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info message as tooltip
        tooltip_text = (
            f"ℹ️ {self.lm.get('Tickets.automatic_time_tracking', 'Automatic Time Tracking')}\n\n"
            f"{self.lm.get('Tickets.work_logs_auto_created', 'Work logs are automatically created when:')}\n"
            f"• {self.lm.get('Tickets.auto_created_when_assigned', 'A ticket is assigned to a technician (starts timer)')}\n"
            f"• {self.lm.get('Tickets.auto_created_when_status_changes', 'Ticket status changes to Completed or Cancelled (stops timer)')}\n\n"
            f"{self.lm.get('Tickets.auto_time_tracking_benefit', 'This provides accurate time tracking without manual intervention.')}"
        )
        widget.setToolTip(tooltip_text)
        
        # Work history section
        history_group = QGroupBox(self.lm.get("Tickets.work_history", "Work History"))
        history_layout = QVBoxLayout(history_group)
        
        # Get all work logs for this ticket
        try:
            work_logs = self.work_log_controller.get_logs_for_ticket(self.ticket.id)
            
            if not work_logs:
                no_logs_label = QLabel(self.lm.get("Tickets.no_work_logged_yet", "No work has been logged for this ticket yet.\nWork will be logged automatically when a technician is assigned."))
                no_logs_label.setAlignment(Qt.AlignCenter)
                no_logs_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
                history_layout.addWidget(no_logs_label)
            else:
                # Calculate total time
                total_minutes = 0
                active_count = 0
                for log in work_logs:
                    if log.end_time:
                        duration = (log.end_time - log.start_time).total_seconds() / 60
                        total_minutes += duration
                    else:
                        active_count += 1
                
                total_hours = total_minutes / 60
                
                # Summary
                summary_layout = QFormLayout()
                summary_layout.addRow(self.lm.get("Tickets.total_time_logged", "Total Time Logged") + ":", QLabel(f"{total_hours:.1f} {self.lm.get('Tickets.hours', 'hours')} ({total_minutes:.0f} {self.lm.get('Tickets.minutes', 'minutes')})"))
                summary_layout.addRow(self.lm.get("Tickets.completed_sessions", "Completed Sessions") + ":", QLabel(str(len(work_logs) - active_count)))
                if active_count > 0:
                    active_label = QLabel(f"{active_count} ({self.lm.get('Tickets.timer_running', 'Timer running')})")
                    active_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    summary_layout.addRow(self.lm.get("Tickets.active_sessions", "Active Sessions") + ":", active_label)
                history_layout.addLayout(summary_layout)
                
                # Work logs table
                self.work_log_table = QTableWidget()
                self.work_log_table.setColumnCount(5)
                self.work_log_table.setHorizontalHeaderLabels([
                    self.lm.get("Tickets.technician", "Technician"),
                    self.lm.get("Tickets.start_time", "Start Time"),
                    self.lm.get("Tickets.end_time", "End Time"),
                    self.lm.get("Tickets.duration", "Duration"),
                    self.lm.get("Tickets.work_description", "Work Description")
                ])
                self.work_log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                self.work_log_table.setSelectionBehavior(QTableWidget.SelectRows)
                self.work_log_table.setEditTriggers(QTableWidget.NoEditTriggers)
                self.work_log_table.setAlternatingRowColors(True)
                
                self.work_log_table.setRowCount(len(work_logs))
                
                for row, log in enumerate(work_logs):
                    # Technician name
                    tech_name = log.technician_name if log.technician_name else self.lm.get("Common.unknown", "Unknown")
                    self.work_log_table.setItem(row, 0, QTableWidgetItem(tech_name))
                    
                    # Start time
                    start_time = log.start_time.strftime("%Y-%m-%d %H:%M") if log.start_time else self.lm.get("Common.not_applicable", "N/A")
                    self.work_log_table.setItem(row, 1, QTableWidgetItem(start_time))
                    
                    # End time
                    if log.end_time:
                        end_time = log.end_time.strftime("%Y-%m-%d %H:%M")
                        self.work_log_table.setItem(row, 2, QTableWidgetItem(end_time))
                    else:
                        in_progress_item = QTableWidgetItem(f"⏱ {self.lm.get('Common.in_progress', 'In Progress')}")
                        in_progress_item.setForeground(Qt.blue)
                        in_progress_item.setBackground(Qt.yellow)
                        self.work_log_table.setItem(row, 2, in_progress_item)
                    
                    # Duration
                    if log.end_time:
                        duration_seconds = (log.end_time - log.start_time).total_seconds()
                        duration_minutes = duration_seconds / 60
                        if duration_minutes < 60:
                            duration_str = f"{duration_minutes:.0f} {self.lm.get('Tickets.min', 'min')}"
                        else:
                            hours = duration_minutes / 60
                            duration_str = f"{hours:.1f} {self.lm.get('Tickets.hrs', 'hrs')}"
                        self.work_log_table.setItem(row, 3, QTableWidgetItem(duration_str))
                    else:
                        # Calculate elapsed time for active logs
                        elapsed = datetime.now() - log.start_time
                        elapsed_minutes = elapsed.total_seconds() / 60
                        elapsed_item = QTableWidgetItem(f"{elapsed_minutes:.0f} {self.lm.get('Tickets.min', 'min')} ({self.lm.get('Tickets.ongoing', 'ongoing')})")
                        elapsed_item.setForeground(Qt.blue)
                        self.work_log_table.setItem(row, 3, elapsed_item)
                    
                    # Work performed
                    work_text = log.work_performed[:50] + "..." if len(log.work_performed) > 50 else log.work_performed
                    self.work_log_table.setItem(row, 4, QTableWidgetItem(work_text))
                
                history_layout.addWidget(self.work_log_table)
        
        except Exception as e:
            error_label = QLabel(f"{self.lm.get('Tickets.error_loading_work_logs', 'Error loading work logs')}: {str(e)}")
            error_label.setStyleSheet("color: red;")
            history_layout.addWidget(error_label)
        
        layout.addWidget(history_group)
        
        return widget
    
    def _on_edit(self):
        """Create a widget for managing work logs for the current user on this ticket."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Check if we have container and user (needed for work log operations)
        if not self.user:
            no_access_label = QLabel(self.lm.get("Tickets.work_log_requires_user_context", "Work log functionality requires user context."))
            no_access_label.setAlignment(Qt.AlignCenter)
            no_access_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_access_label)
            return widget
        
        # Get current technician from user email
        current_technician = None
        try:
            from models.technician import Technician
            if self.user.email:
                techs = list(Technician.select().where(Technician.email == self.user.email))
                if techs:
                    current_technician = techs[0]
        except Exception as e:
            print(f"{self.lm.get('Common.error', 'Error')} finding technician: {e}")
        
        # Active work session section
        active_group = QGroupBox(self.lm.get("Tickets.current_work_session", "Current Work Session"))
        active_layout = QVBoxLayout(active_group)
        
        # Check for active work log
        active_log = None
        if current_technician:
            try:
                active_logs = self.work_log_controller.get_active_logs_for_technician(current_technician.id)
                # Filter for this specific ticket
                active_log = next((log for log in active_logs if log.ticket_id == self.ticket.id), None)
            except Exception as e:
                print(f"{self.lm.get('Common.error', 'Error')} getting active logs: {e}")
        
        if active_log:
            # Show active session info
            from datetime import datetime
            elapsed = datetime.now() - active_log.start_time
            elapsed_minutes = elapsed.total_seconds() / 60
            
            info_layout = QFormLayout()
            info_layout.addRow(f"{self.lm.get('Tickets.started', 'Started')}:", QLabel(active_log.start_time.strftime("%Y-%m-%d %H:%M")))
            info_layout.addRow(f"{self.lm.get('Tickets.elapsed_time', 'Elapsed Time')}:", QLabel(f"{elapsed_minutes:.0f} {self.lm.get('Tickets.minutes', 'minutes')} ({elapsed_minutes/60:.1f} {self.lm.get('Tickets.hours', 'hours')})"))
            
            work_desc = active_log.work_performed[:100] + "..." if len(active_log.work_performed) > 100 else active_log.work_performed
            info_layout.addRow(f"{self.lm.get('Tickets.work_description', 'Work Description')}:", QLabel(work_desc))
            active_layout.addLayout(info_layout)
            
            # Stop button
            stop_btn = QPushButton(f"⏹ {self.lm.get('Tickets.stop_work_session', 'Stop Work Session')}")
            stop_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
            stop_btn.clicked.connect(lambda: self._stop_work_log(active_log.id))
            active_layout.addWidget(stop_btn)
        else:
            # Show start button
            if current_technician:
                no_session_label = QLabel(self.lm.get("Tickets.no_active_work_session", "No active work session for this ticket."))
                no_session_label.setStyleSheet("color: gray; font-style: italic;")
                active_layout.addWidget(no_session_label)
                
                start_btn = QPushButton(f"▶ {self.lm.get('Tickets.start_work_session', 'Start Work Session')}")
                start_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
                start_btn.clicked.connect(lambda: self._start_work_log(current_technician.id))
                active_layout.addWidget(start_btn)
            else:
                no_tech_label = QLabel(self.lm.get("Tickets.must_be_registered_as_technician", "You must be registered as a technician to log work."))
                no_tech_label.setStyleSheet("color: orange; font-style: italic;")
                active_layout.addWidget(no_tech_label)
        
        layout.addWidget(active_group)
        
        # Add the general work log history tab content
        history_widget = self._create_work_log_widget()
        if history_widget.layout().count() > 1:
            history_group_from_tab = history_widget.layout().itemAt(1).widget()
            if isinstance(history_group_from_tab, QGroupBox) and history_group_from_tab.title() == self.lm.get("Tickets.work_history", "Work History"):
                layout.addWidget(history_group_from_tab)
            else:
                layout.addWidget(history_widget)
        else:
            layout.addWidget(history_widget)
        
        return widget
    
    def _start_work_log(self, technician_id):
        """Start a new work log session"""
        # Show dialog to get work description
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Tickets.start_work_session", "Start Work Session"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(self.lm.get("Tickets.describe_work_to_perform", "Describe the work you're about to perform:"))
        layout.addWidget(label)
        
        description_edit = QTextEdit()
        description_edit.setPlaceholderText(self.lm.get("Tickets.work_description_placeholder", "e.g., Diagnosing screen issue, replacing battery, testing components..."))
        description_edit.setMaximumHeight(100)
        layout.addWidget(description_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            description = description_edit.toPlainText().strip()
            if not description:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("TicketMessages.work_desc_required", "Please provide a work description."))
                return
            
            try:
                work_log = self.container.work_log_controller.start_work_log(
                    technician_id=technician_id,
                    ticket_id=self.ticket.id,
                    description=description
                )
                
                if work_log:
                    QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("TicketMessages.work_session_started", "Work session started successfully!"))
                    # Refresh the dialog
                    self.accept()
                else:
                    QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("TicketMessages.work_session_start_failed", "Failed to start work session."))
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.work_session_start_failed', 'Failed to start work session')}: {str(e)}")
    
    def _stop_work_log(self, work_log_id):
        """Stop the active work log session"""
        reply = QMessageBox.question(
            self,
            self.lm.get("Tickets.stop_work_session", "Stop Work Session"),
            self.lm.get("TicketMessages.confirm_stop_work_session", "Are you sure you want to stop this work session?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                work_log = self.container.work_log_controller.end_work_log(work_log_id)
                
                if work_log:
                    from datetime import datetime
                    duration = (work_log.end_time - work_log.start_time).total_seconds() / 60
                    QMessageBox.information(
                        self,
                        self.lm.get("Common.success", "Success"),
                        f"{self.lm.get('TicketMessages.work_session_stopped', 'Work session stopped!')}\n"
                        f"{self.lm.get('Tickets.duration', 'Duration')}: {duration:.0f} {self.lm.get('Tickets.minutes', 'minutes')} ({duration/60:.1f} {self.lm.get('Tickets.hours', 'hours')})"
                    )
                    # Refresh the dialog
                    self.accept()
                else:
                    QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("TicketMessages.work_session_stop_failed", "Failed to stop work session."))
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.work_session_stop_failed', 'Failed to stop work session')}: {str(e)}")