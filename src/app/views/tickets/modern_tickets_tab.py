# src/app/views/tickets/modern_tickets_tab.py
"""
Modern Tickets Tab with enhanced UI features:
- Card/Grid view
- Kanban board
- Advanced filtering
- Statistics dashboard
- Quick actions
- Bulk operations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QCheckBox, QFrame, QScrollArea,
    QGridLayout, QStackedWidget, QMenu, QDialog, QFormLayout,
    QDialogButtonBox, QDateEdit, QSpinBox, QGroupBox, QButtonGroup,
    QRadioButton, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QColor, QCursor, QIcon
from typing import List, Dict
import csv
from datetime import datetime, timedelta
from dtos.ticket_dto import TicketDTO
from utils.validation.message_handler import MessageHandler
from utils.print.ticket_generator import TicketReceiptGenerator
from views.tickets.ticket_details_dialog import TicketDetailsDialog
from views.components.metric_card import MetricCard
from views.components.new_dashboard_widgets import is_dark_theme
from views.tickets.ticket_base import TicketBaseWidget
from views.tickets.kanban_view import KanbanView
from views.components.loading_overlay import LoadingOverlay
from utils.language_manager import language_manager
from core.event_bus import EventBus
from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
    TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent,
    InvoiceCreatedEvent,
    TechnicianCreatedEvent, TechnicianUpdatedEvent, TechnicianDeactivatedEvent,
    BranchContextChangedEvent
)

class ModernTicketsTab(TicketBaseWidget):

    ticket_selected = Signal(TicketDTO)
    
    def __init__(self, 
                 ticket_controller,
                 technician_controller,
                 ticket_service,
                 business_settings_service,
                 user,
                 invoice_controller=None,
                 container=None):
        """
        Initialize ModernTicketsTab with explicit dependencies (Google 3X: Excellence).
        
        Args:
            ticket_controller: Controller for ticket operations
            technician_controller: Controller for technician operations
            ticket_service: Service for ticket business logic
            business_settings_service: Service for settings
            user: Current user context
            invoice_controller: Optional controller for invoices
            container: Legacy dependency container (Deprecated: will be removed in future refactoring)
        """
        super().__init__()
        
        self.ticket_controller = ticket_controller
        self.technician_controller = technician_controller
        self.ticket_service = ticket_service
        self.business_settings_service = business_settings_service
        self.invoice_controller = invoice_controller
        self.user = user
        self.container = container # Legacy support for child dialogs
        
        # Initialize language manager
        self.lm = language_manager
        
        self.technicians = []
        self.selected_tickets = []  # For bulk operations
        self.selected_tickets = []  # For bulk operations
        self.current_view = 'cards'  # 'cards', 'list', 'kanban'
        self.current_branch_id = None
        
        self._setup_ui()
        self._connect_signals()
        # Subscribe to events
        self._subscribe_to_events()
        
        # Initialize loading overlay
        self.loading_overlay = LoadingOverlay(self)
        
        # Load initial data
        # self._load_technicians()
        # self._load_tickets()
        self._data_loaded = False

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # Use timer to let UI render first
            QTimer.singleShot(100, self._load_initial_data)
            self._data_loaded = True
            
    def _load_initial_data(self):
        """Load initial data sequentially"""
        self._load_technicians()
        self._load_tickets()

    def _on_table_context_menu(self, position):
        """Show context menu for table items"""
        index = self.tickets_table.indexAt(position)
        if not index.isValid():
            return
        
        row = index.row()
        ticket_item = self.tickets_table.item(row, 1)
        if not ticket_item:
            return
        ticket_id = ticket_item.data(Qt.UserRole)
        ticket = self.ticket_service.get_ticket(ticket_id)
        if ticket:
            self._show_context_menu(self.tickets_table.viewport().mapToGlobal(position), ticket)

    def _show_context_menu(self, position, ticket):
        """Show context menu for ticket"""
        if not ticket:
            return
            
        menu = QMenu()
        
        # 1. Ticket Detail
        detail_action = menu.addAction(f"📄 {self.lm.get('Tickets.ticket_details', 'Ticket Detail')}")
        detail_action.triggered.connect(lambda: self._show_ticket_details(ticket))
        
        # 2. Update Status
        status_menu = menu.addMenu(f"🔄 {self.lm.get('Tickets.update_status_menu', 'Update Status')}")
        statuses = [
            ('open', self.lm.get('Common.open', 'Open')),
            ('diagnosed', self.lm.get('Common.diagnosed', 'Diagnosed')),
            ('in_progress', self.lm.get('Common.in_progress', 'In Progress')),
            ('awaiting_parts', self.lm.get('Common.awaiting_parts', 'Awaiting Parts')),
            ('completed', self.lm.get('Common.completed', 'Completed')),
            ('cancelled', self.lm.get('Common.cancelled', 'Cancelled')),
            ('unrepairable', self.lm.get('Common.unrepairable', 'Unrepairable'))
        ]
        for status_key, status_label in statuses:
            action = status_menu.addAction(status_label)
            action.triggered.connect(lambda checked, s=status_key: self._update_ticket_status(ticket, s))

        # 3. Assign Technician
        assign_menu = menu.addMenu(f"👤 {self.lm.get('Tickets.assignment', 'Assign Technician')}")
        
        # Not Assigned option
        not_assigned_action = assign_menu.addAction(self.lm.get('Tickets.not_assigned', 'Not Assigned'))
        not_assigned_action.triggered.connect(lambda: self._assign_technician_direct(ticket, None))
        
        assign_menu.addSeparator()
        
        # List technicians
        for tech in self.technicians:
            name = tech.full_name if tech.full_name else f"{self.lm.get('Tickets.technician', 'Technician')} #{tech.id}"
            # Add checkmark if currently assigned
            if ticket.assigned_technician_id == tech.id:
                name = f"✓ {name}"
            
            action = assign_menu.addAction(name)
            action.triggered.connect(lambda checked, t_id=tech.id: self._assign_technician_direct(ticket, t_id))

        # 4. Create Invoice
        invoice_action = menu.addAction(f"💰 {self.lm.get('TicketActions.create_invoice', 'Create Invoice')}")
        invoice_action.triggered.connect(lambda: self._create_invoice(ticket))
        # Enable only if completed/cancelled/unrepairable
        if ticket.status not in ['completed', 'cancelled', 'unrepairable']:
            invoice_action.setEnabled(False)
            
        # 5. Edit Ticket
        edit_action = menu.addAction(f"✏️ {self.lm.get('Tickets.edit_ticket_menu', 'Edit Ticket')}")
        edit_action.triggered.connect(lambda: self._edit_ticket(ticket))
        
        # 6. Preview Ticket
        preview_action = menu.addAction(f"👁️ {self.lm.get('TicketActions.preview_ticket', 'Preview Ticket')}")
        preview_action.triggered.connect(lambda: self._preview_ticket(ticket))
        
        # 7. Delete/Restore Ticket
        if not ticket.is_deleted:
            # Check permissions
            has_delete_perm = True
            if self.container and self.container.role_service:
                has_delete_perm = self.container.role_service.user_has_permission(self.user, 'tickets:delete')
            
            if has_delete_perm:
                delete_action = menu.addAction(f"🗑️ {self.lm.get('TicketActions.delete_ticket', 'Delete Ticket')}")
                delete_action.triggered.connect(lambda: self._delete_ticket(ticket))
        else:
            restore_action = menu.addAction(f"↩️ {self.lm.get('TicketActions.restore_ticket', 'Restore Ticket')}")
            restore_action.triggered.connect(lambda: self._restore_ticket(ticket))
        
        menu.exec(position)

    def _assign_technician_direct(self, ticket, tech_id):
        """Assign technician directly without dialog"""
        try:
            # Get User model from user ID
            from models.user import User
            from PySide6.QtWidgets import QInputDialog
            user_model = User.get_by_id(self.user.id) if self.user else None
            
            # Check if this is a transfer (previously assigned and new tech is different)
            transfer_reason = None
            if ticket.assigned_technician_id and tech_id and ticket.assigned_technician_id != tech_id:
                reason_text, ok = QInputDialog.getText(
                    self, 
                    self.lm.get("Tickets.transfer_reason_title", "Transfer Reason"),
                    self.lm.get("Tickets.enter_transfer_reason", "Reason for transferring to new technician:"),
                )
                if ok and reason_text:
                    transfer_reason = reason_text
            
            self.ticket_controller.assign_ticket(
                ticket.id, 
                tech_id, 
                reason=transfer_reason,
                current_user=user_model, 
                ip_address='127.0.0.1'
            )
            
            tech_name = self.lm.get('Tickets.not_assigned', 'Unassigned')
            if tech_id:
                for tech in self.technicians:
                    if tech.id == tech_id:
                        tech_name = tech.full_name or f"{self.lm.get('Tickets.technician', 'Technician')} #{tech.id}"
                        break
            
            MessageHandler.show_info(self, self.lm.get('Common.success', 'Success'), f"{self.lm.get('TicketMessages.ticket_assigned_to', 'Ticket assigned to')} {tech_name}.")
            self._load_tickets()
        except Exception as e:
            MessageHandler.show_error(self, self.lm.get('Common.error', 'Error'), f"{self.lm.get('TicketMessages.failed_to_assign_technician', 'Failed to assign technician')}: {str(e)}")

    def _show_ticket_details(self, ticket):
        dialog = TicketDetailsDialog(
            ticket=ticket,
            ticket_service=self.ticket_service,
            ticket_controller=self.ticket_controller,
            technician_controller=self.technician_controller,
            repair_part_controller=self.container.repair_part_controller if self.container else None,
            work_log_controller=self.container.work_log_controller if self.container else None,
            business_settings_service=self.business_settings_service,
            part_service=self.container.part_service if self.container else None,
            technician_repository=self.container.technician_repository if self.container else None,
            user=self.user,
            container=self.container,
            parent=self
        )
        dialog.exec()

    def _on_table_double_click(self, index):
        """Open ticket detail dialog on double click"""
        row = index.row()
        ticket_item = self.tickets_table.item(row, 1)
        if not ticket_item:
            return
        ticket_id = ticket_item.data(Qt.UserRole)
        if not ticket_id:
            return
        ticket_dto = self.ticket_service.get_ticket(ticket_id)
        if ticket_dto:
            self._show_ticket_details(ticket_dto)
    
    def _on_card_clicked(self, card, ticket: TicketDTO):
        """Handle card click (toggle selection)"""
        if ticket.id in self.selected_tickets:
            self.selected_tickets.remove(ticket.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_tickets.append(ticket.id)
            self._update_card_selection_style(card, True)
        
        self._update_bulk_buttons_state()
        
    def _on_card_double_clicked(self, ticket: TicketDTO):
        """Handle card double click (open details)"""
        self._show_ticket_details(ticket)

    def _update_ticket_status(self, ticket, new_status):
        """Update ticket status"""
        if ticket.status == new_status:
            return
        try:
            # Get User model from user ID
            from models.user import User
            user_model = User.get_by_id(self.user.id) if self.user else None
            
            self.ticket_controller.change_ticket_status(
                ticket_id=ticket.id,
                new_status=new_status,
                reason=self.lm.get('TicketMessages.status_updated_from_context_menu', 'Status updated from context menu'),
                current_user=user_model,
                ip_address='127.0.0.1'
            )
            self._load_tickets()
        except Exception as e:
            MessageHandler.show_error(self, self.lm.get('Common.error', 'Error'), f"{self.lm.get('TicketMessages.failed_to_update_status', 'Failed to update status')}: {str(e)}")

    def _create_invoice(self, ticket):
        """Create invoice for ticket"""
        try:
            from views.invoice.create_customer_invoice_dialog import CreateCustomerInvoiceDialog
            dialog = CreateCustomerInvoiceDialog(self.container, ticket, self.user, self)
            dialog.exec()
        except ImportError:
            MessageHandler.show_error(self, self.lm.get('Common.error', 'Error'), self.lm.get('TicketMessages.could_not_import_invoice_dialog', 'Could not import CreateCustomerInvoiceDialog'))
        except Exception as e:
            MessageHandler.show_error(self, self.lm.get('Common.error', 'Error'), f"{self.lm.get('TicketMessages.failed_to_open_invoice_dialog', 'Failed to open invoice dialog')}: {str(e)}")

    def _edit_ticket(self, ticket):
        """Open ticket in edit mode"""
        self.ticket_controller.show_edit_ticket_form(ticket.id, self)

    def _preview_ticket(self, ticket):
        """Preview ticket receipt"""
        
        # Get user settings for print format
        print_format = 'Standard A5'
        if self.user and self.container and self.container.settings_service:
            try:
                settings = self.container.settings_service.get_user_settings(self.user.id)
                print_format = settings.get('print_format', 'Standard A5')
            except Exception:
                pass

        generator = TicketReceiptGenerator(self, self.business_settings_service)
        print_data = {
            'print_format': print_format,
            'customer_name': ticket.customer.name if ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_phone': ticket.customer.phone if ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_email': ticket.customer.email if ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'customer_address': ticket.customer.address if ticket.customer else self.lm.get('Common.not_applicable', 'N/A'),
            'brand': ticket.device.brand if ticket.device else '',
            'model': ticket.device.model if ticket.device else '',
            'imei': ticket.device.imei if ticket.device else '',
            'serial_number': ticket.device.serial_number if ticket.device else '',
            'color': ticket.device.color if ticket.device else '',
            'condition': ticket.device.condition if ticket.device else '',
            'lock_type': ticket.device.lock_type if ticket.device else '',
            'passcode': ticket.device.passcode if ticket.device else '',
            'issue_type': ticket.error or self.lm.get('Common.not_applicable', 'N/A'),
            'description': ticket.error_description or ticket.error or self.lm.get('Common.not_applicable', 'N/A'),
            'accessories': ticket.accessories or self.lm.get('Tickets.none_accessories', 'None'),
            'deadline': ticket.deadline.strftime("%Y-%m-%d") if ticket.deadline else self.lm.get('Common.not_applicable', 'N/A'),
            'estimated_cost': ticket.estimated_cost or 0.0,
            'deposit_paid': ticket.deposit_paid or 0.0,
            'ticket_number': ticket.ticket_number
        }
        generator.preview_ticket(print_data)

    def _delete_ticket(self, ticket):
        """Delete the selected ticket with confirmation"""
        # Double check permissions
        if self.container and self.container.role_service:
            if not self.container.role_service.user_has_permission(self.user, 'tickets:delete'):
                MessageHandler.show_warning(self, self.lm.get('Common.error', 'Error'), "Access Denied: You do not have permission to delete tickets.")
                return

        if MessageHandler.show_question(
            self,
            self.lm.get('Common.confirm_delete', 'Confirm Delete'),
            f"{self.lm.get('TicketMessages.confirm_delete_ticket', 'Are you sure you want to delete ticket')} #{ticket.ticket_number}?",
        ):
            success = self.ticket_controller.delete_ticket(
                ticket.id,
                current_user=self.user,
                ip_address='127.0.0.1'
            )
            if success:
                QTimer.singleShot(300, self._load_tickets)
                MessageHandler.show_info(self, 
                    self.lm.get('Common.deleted', 'Deleted'), 
                    f"{self.lm.get('TicketMessages.ticket_deleted_successfully', 'Ticket deleted successfully')} #{ticket.ticket_number}"
                )
            else:
                MessageHandler.show_warning(self, 
                    self.lm.get('Common.error', 'Error'), 
                    f"{self.lm.get('TicketMessages.failed_to_delete_ticket', 'Failed to delete ticket')} #{ticket.ticket_number}"
                )

    def _restore_ticket(self, ticket):
        """Restore the selected ticket with confirmation"""
        if MessageHandler.show_question(
            self,
            self.lm.get('Common.confirm_restore', 'Confirm Restore'),
            f"{self.lm.get('TicketMessages.confirm_restore_ticket', 'Are you sure you want to restore ticket')} #{ticket.ticket_number}?",
        ):
            success = self.ticket_controller.restore_ticket(
                ticket.id,
                current_user=self.user,
                ip_address='127.0.0.1'
            )
            if success:
                QTimer.singleShot(300, self._load_tickets)
                MessageHandler.show_info(self, 
                    self.lm.get('Common.restored', 'Restored'), 
                    f"{self.lm.get('TicketMessages.ticket_restored_successfully', 'Ticket restored successfully')} #{ticket.ticket_number}"
                )
            else:
                MessageHandler.show_warning(self, 
                    self.lm.get('Common.error', 'Error'), 
                    f"{self.lm.get('TicketMessages.failed_to_restore_ticket', 'Failed to restore ticket')} #{ticket.ticket_number}"
                )

    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Statistics Dashboard
        stats_dashboard = self._create_statistics_dashboard()
        layout.addWidget(stats_dashboard)
        
        # Filters and search
        filter_layout = self._create_advanced_filters()
        layout.addLayout(filter_layout)
        
        # Action buttons
        action_layout = self._create_action_buttons()
        layout.addLayout(action_layout)
        
        # Stacked widget for different views
        self.view_stack = QStackedWidget()
        
        # Create different view widgets
        self.cards_view = self._create_cards_view()
        self.list_view = self._create_list_view()
        self.kanban_view = self._create_kanban_view()  # Add kanban view
        
        self.view_stack.addWidget(self.cards_view)
        self.view_stack.addWidget(self.list_view)
        self.view_stack.addWidget(self.kanban_view)  # Add to stack
        
        layout.addWidget(self.view_stack, 1)
        
    def _create_header(self):
        """Create header with title and view switcher"""
        layout = QHBoxLayout()
        # We don't parent yet, but ensure it's returned and used immediately
        
        # Title
        title = QLabel(self.lm.get("Tickets.tickets_title", "Tickets"), self)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Common.view", "View") + ":")
        view_label.setObjectName("metricLabel")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Tickets.cards_view', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Tickets.list_view', 'List')}")
        self.kanban_view_btn = QPushButton(f"📊 {self.lm.get('Tickets.kanban_view', 'Kanban')}")  # Add kanban button
        
        self.cards_view_btn.setCheckable(True)
        self.list_view_btn.setCheckable(True)
        self.kanban_view_btn.setCheckable(True)  # Make checkable
        self.cards_view_btn.setChecked(True)
        
        # Style for view buttons
        view_btn_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #374151;
                background-color: transparent;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                color: white;
                border-color: #3B82F6;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.1);
            }
        """
        
        for btn in [self.cards_view_btn, self.list_view_btn, self.kanban_view_btn]:
            btn.setStyleSheet(view_btn_style)
            layout.addWidget(btn)
        
        return layout
    
    def _create_statistics_dashboard(self):
        """Create statistics dashboard with metric cards"""
        container = QFrame()
        container.setObjectName("cardFrame")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title with collapse button
        header = QHBoxLayout()
        layout.addLayout(header)
        title = QLabel(self.lm.get("Tickets.overview", "Overview"))
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        
        self.collapse_stats_btn = QPushButton("▼")
        self.collapse_stats_btn.setFixedSize(20, 20)
        self.collapse_stats_btn.setCheckable(True)
        self.collapse_stats_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 10px;
            }
        """)
        
        
        
        # Metrics row (collapsible)
        self.metrics_widget = QWidget()
        metrics_container = QVBoxLayout(self.metrics_widget)
        metrics_container.setContentsMargins(0, 0, 0, 0)
        
        # Connect collapse button (Placed after widget creation to avoid AttributeError)
        self.collapse_stats_btn.toggled.connect(self.metrics_widget.setHidden)
        
        # Use QHBoxLayout for single row
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(12)
        
        # Placeholder metrics (will be updated with real data)
        self.metric_cards = {}
        metrics = [
            ("total", "🎫", "0", self.lm.get("Tickets.total_tickets", "Total Tickets"), "#3B82F6"), # Blue
            ("open", "📋", "0", self.lm.get("Common.open", "Open"), "#6B7280"), # Gray
            ("in_progress", "🔧", "0", self.lm.get("Common.in_progress", "In Progress"), "#F59E0B"), # Orange
            ("completed", "✅", "0", self.lm.get("Common.completed", "Completed"), "#10B981"), # Green
            ("overdue", "⏰", "0", self.lm.get("Tickets.overdue", "Overdue"), "#EF4444"), # Red
            ("avg_time", "⏱️", "0h", self.lm.get("Tickets.avg_time", "Avg Time"), "#8B5CF6"), # Purple
        ]
        
        for key, icon, value, label, color in metrics:
            card = MetricCard(icon, value, label, None, color=color)
            card.setFixedHeight(100) # Reduced height
            self.metric_cards[key] = card
            self.metrics_layout.addWidget(card)
        
        metrics_container.addLayout(self.metrics_layout)
        
        layout.addWidget(self.metrics_widget)
        
        return container
    
    def _create_advanced_filters(self):
        """Create advanced filter controls"""
        main_filter_layout = QVBoxLayout()
        
        # First row - Search and basic filters
        row1 = QHBoxLayout()
        main_filter_layout.addLayout(row1)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {self.lm.get('Tickets.search_placeholder', 'Search tickets, customers, devices...')}")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(300)
        row1.addWidget(self.search_input)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("Tickets.all_statuses", "All Statuses"), None)
        status_items = [
            ('open', self.lm.get("Common.open", "Open")),
            ('diagnosed', self.lm.get("Common.diagnosed", "Diagnosed")),
            ('in_progress', self.lm.get("Common.in_progress", "In Progress")),
            ('awaiting_parts', self.lm.get("Common.awaiting_parts", "Awaiting Parts")),
            ('completed', self.lm.get("Common.completed", "Completed")),
            ('cancelled', self.lm.get("Common.cancelled", "Cancelled")),
            ('unrepairable', self.lm.get("Common.unrepairable", "Unrepairable"))
        ]
        for key, label in status_items:
            self.status_filter.addItem(label, key)
        self.status_filter.setMinimumWidth(150)
        row1.addWidget(self.status_filter)
        
        # Priority filter
        self.priority_filter = QComboBox()
        self.priority_filter.addItem(self.lm.get("Tickets.all_priorities", "All Priorities"), None)
        priority_items = [
            ('low', self.lm.get("Common.low", "Low")),
            ('medium', self.lm.get("Common.medium", "Medium")),
            ('high', self.lm.get("Common.high", "High")),
            ('urgent', self.lm.get("Common.urgent", "Urgent"))
        ]
        for key, label in priority_items:
            self.priority_filter.addItem(label, key)
        self.priority_filter.setMinimumWidth(150)
        row1.addWidget(self.priority_filter)
        
        # Technician filter
        self.tech_filter = QComboBox()
        self.tech_filter.setMinimumWidth(150)
        row1.addWidget(self.tech_filter)
        
        row1.addStretch()
        
        # Advanced filters toggle
        self.advanced_filter_btn = QPushButton(f"⚙️ {self.lm.get('Tickets.advanced_filters', 'Advanced Filters')}")
        self.advanced_filter_btn.setCheckable(True)
        row1.addWidget(self.advanced_filter_btn)
        
        # Second row - Advanced filters (initially hidden)
        self.advanced_filters_widget = QWidget()
        row2 = QHBoxLayout(self.advanced_filters_widget)
        row2.setContentsMargins(0, 0, 0, 0)
        
        # Date range
        row2.addWidget(QLabel(self.lm.get("Tickets.from", "From") + ":"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        row2.addWidget(self.date_from)
        
        row2.addWidget(QLabel(self.lm.get("Tickets.to", "To") + ":"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        row2.addWidget(self.date_to)
        
        # Show deleted
        self.show_deleted_checkbox = QCheckBox(self.lm.get("Tickets.show_deleted", "Show Deleted"))
        row2.addWidget(self.show_deleted_checkbox)
        
        # Show overdue only
        self.show_overdue_checkbox = QCheckBox(self.lm.get("Tickets.overdue_only", "Overdue Only"))
        row2.addWidget(self.show_overdue_checkbox)
        
        # Show all tickets (including returned)
        self.show_all_checkbox = QCheckBox(self.lm.get("Tickets.show_all", "Show All Tickets"))
        self.show_all_checkbox.setToolTip(self.lm.get("Tickets.show_all_tickets_tooltip", "Show tickets even if device is returned"))
        row2.addWidget(self.show_all_checkbox)
        
        row2.addStretch()
        
        # Clear filters button
        clear_btn = QPushButton(f"🔄 {self.lm.get('Tickets.clear_filters', 'Clear Filters')}")
        clear_btn.clicked.connect(self._clear_filters)
        row2.addWidget(clear_btn)
        
        self.advanced_filters_widget.setVisible(False)
        main_filter_layout.addWidget(self.advanced_filters_widget)
        
        return main_filter_layout
    
    def _update_bulk_buttons_state(self, *args):
        """Enable bulk action buttons when any row is checked or card selected"""
        any_checked = False
        has_returned = False
        
        if self.current_view == 'list':
            for row in range(self.tickets_table.rowCount()):
                item = self.tickets_table.item(row, 0)
                if item and item.checkState() == Qt.Checked:
                    any_checked = True
                    # Check if ticket is returned
                    ticket_item = self.tickets_table.item(row, 1)
                    if ticket_item:
                        tid = ticket_item.data(Qt.UserRole)
                        # Find ticket in current list
                        ticket = next((t for t in self._current_ticket_list if t.id == tid), None)
                        if ticket and ticket.device and ticket.device.status == 'returned':
                            has_returned = True
                            break
        else:
            any_checked = len(self.selected_tickets) > 0
            # Check selected tickets for returned status
            for tid in self.selected_tickets:
                ticket = next((t for t in self._current_ticket_list if t.id == tid), None)
                if ticket and ticket.device and ticket.device.status == 'returned':
                    has_returned = True
                    break
        
        self.bulk_update_btn.setEnabled(any_checked and not has_returned)
        self.bulk_assign_btn.setEnabled(any_checked and not has_returned)
        
        if has_returned:
            self.bulk_update_btn.setToolTip(self.lm.get("Tickets.cannot_update_returned", "Cannot update returned tickets"))
            self.bulk_assign_btn.setToolTip(self.lm.get("Tickets.cannot_assign_returned", "Cannot assign returned tickets"))
        else:
            self.bulk_update_btn.setToolTip("")
            self.bulk_assign_btn.setToolTip("")
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # New ticket button (primary)
        self.new_ticket_btn = QPushButton(f"➕ {self.lm.get('Tickets.new_ticket', 'New Ticket')}")
        self.new_ticket_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        layout.addWidget(self.new_ticket_btn)
        
        # Bulk actions (enabled when tickets selected)
        self.bulk_update_btn = QPushButton(f"📝 {self.lm.get('Tickets.bulk_update', 'Bulk Update')}")
        self.bulk_update_btn.setEnabled(False)
        layout.addWidget(self.bulk_update_btn)
        
        self.bulk_assign_btn = QPushButton(f"👤 {self.lm.get('Tickets.bulk_assign', 'Bulk Assign')}")
        self.bulk_assign_btn.setEnabled(False)
        layout.addWidget(self.bulk_assign_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_tickets)
        layout.addWidget(refresh_btn)
        
        # Export button
        # Export button with menu
        self.export_btn = QPushButton(f"📥 {self.lm.get('Common.export', 'Export')}")
        self.export_menu = QMenu(self.export_btn)
        
        csv_action = self.export_menu.addAction(f"📄 {self.lm.get('Tickets.save_csv', 'Export CSV')}")
        csv_action.triggered.connect(self._export_tickets_csv)
        
        pdf_action = self.export_menu.addAction(f"📑 {self.lm.get('Tickets.export_pdf', 'Export PDF')}")
        pdf_action.triggered.connect(self._export_tickets_pdf)
        
        self.export_btn.setMenu(self.export_menu)
        layout.addWidget(self.export_btn)
        
        return layout
    
    def _create_cards_view(self):
        """Create card/grid view"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        # Handle background click to deselect
        container.mousePressEvent = self._on_background_clicked
        
        self.cards_layout = QGridLayout(container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(container)
        return scroll
    
    def _create_list_view(self):
        """Create traditional list/table view"""
        self.tickets_table = QTableWidget()
        self.tickets_table.setColumnCount(10)
        headers = [
            "✓",
            self.lm.get("Tickets.ticket_num", "Ticket #"),
            self.lm.get("Tickets.customer", "Customer"),
            self.lm.get("Tickets.device", "Device"),
            self.lm.get("Tickets.issue", "Issue"),
            self.lm.get("Tickets.status", "Status"),
            self.lm.get("Tickets.priority", "Priority"),
            self.lm.get("Tickets.technician", "Technician"),
            self.lm.get("Tickets.created", "Created"),
            self.lm.get("Tickets.deadline", "Due")
        ]
        self.tickets_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes - checkbox column fixed, others stretch
        header = self.tickets_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Checkbox column fixed
        
        self.tickets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tickets_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tickets_table.setAlternatingRowColors(True)
        self.tickets_table.setColumnWidth(0, 40)  # Checkbox column - reduced and fixed
        
        # Enable context menu
        self.tickets_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tickets_table.customContextMenuRequested.connect(self._on_table_context_menu)
        
        return self.tickets_table
    
    def _create_kanban_view(self):
        """Create Kanban board view"""
        self.kanban_view = KanbanView()
        
        # Connect signals
        self.kanban_view.ticket_clicked.connect(self._on_kanban_card_clicked)
        self.kanban_view.ticket_double_clicked.connect(self._on_card_double_clicked)
        self.kanban_view.context_menu_requested.connect(self._show_context_menu)
        
        return self.kanban_view
    

    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        self.kanban_view_btn.clicked.connect(lambda: self._switch_view('kanban'))  # Add kanban signal
        
        # Filters
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        self.priority_filter.currentTextChanged.connect(self._on_filter_changed)
        self.tech_filter.currentTextChanged.connect(self._on_filter_changed)
        self.show_deleted_checkbox.stateChanged.connect(self._on_filter_changed)
        self.show_overdue_checkbox.stateChanged.connect(self._on_filter_changed)
        self.show_all_checkbox.stateChanged.connect(self._on_filter_changed)
        self.date_from.dateChanged.connect(self._on_filter_changed)
        self.date_to.dateChanged.connect(self._on_filter_changed)
        
        # Advanced filters toggle
        self.advanced_filter_btn.toggled.connect(self._toggle_advanced_filters)
        
        # Actions
        self.new_ticket_btn.clicked.connect(self._create_new_ticket)
        self.bulk_update_btn.clicked.connect(self._bulk_update_status)
        self.bulk_assign_btn.clicked.connect(self._bulk_assign_technician)
        # Enable bulk buttons when any checkbox is selected
        self.tickets_table.itemChanged.connect(self._update_bulk_buttons_state)
        
        # Table double click for details
        self.tickets_table.doubleClicked.connect(self._on_table_double_click)
        
        # Controller signals
        # We subscribe to these as a backup to EventBus to ensure UI consistency
        if hasattr(self, 'ticket_controller') and self.ticket_controller:
            self.ticket_controller.ticket_created.connect(self._on_ticket_changed)
            self.ticket_controller.ticket_updated.connect(self._on_ticket_changed)
            self.ticket_controller.ticket_deleted.connect(self._on_ticket_changed)
            self.ticket_controller.ticket_restored.connect(self._on_ticket_changed)
            self.ticket_controller.status_changed.connect(self._on_ticket_changed)
            self.ticket_controller.technician_assigned.connect(self._on_ticket_changed)
            
        self._connect_theme_signal()

    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            # Check if signal exists (requires update to ThemeController)
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        # Reload current view to refresh styles
        self._load_tickets()
    
    def _switch_view(self, view_mode):
        """Switch between different view modes"""
        self.current_view = view_mode
        
        # Update button states
        self.cards_view_btn.setChecked(view_mode == 'cards')
        self.list_view_btn.setChecked(view_mode == 'list')
        self.kanban_view_btn.setChecked(view_mode == 'kanban')  # Update kanban button
        
        # Switch view
        if view_mode == 'cards':
            self.view_stack.setCurrentWidget(self.cards_view)
        elif view_mode == 'list':
            self.view_stack.setCurrentWidget(self.list_view)
        elif view_mode == 'kanban':  # Handle kanban view
            self.view_stack.setCurrentWidget(self.kanban_view)
            self._populate_kanban_view(self._current_ticket_list if hasattr(self, '_current_ticket_list') else [])
        
        # Reload tickets for the new view
        self._load_tickets()
    
    def _toggle_stats(self, checked):
        """Toggle statistics dashboard visibility"""
        self.metrics_widget.setVisible(not checked)
        self.collapse_stats_btn.setText("▶" if checked else "▼")
    
    def _toggle_advanced_filters(self, checked):
        """Toggle advanced filters visibility"""
        self.advanced_filters_widget.setVisible(checked)
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.priority_filter.setCurrentIndex(0)
        self.tech_filter.setCurrentIndex(0)
        self.show_deleted_checkbox.setChecked(False)
        self.show_overdue_checkbox.setChecked(False)
        self.show_all_checkbox.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
    
    def _load_technicians(self, *args):
        """Load technicians for filter"""
        try:
            self.technicians = self.technician_controller.list_technicians(active_only=True)
            self._populate_tech_filter()
        except Exception as e:
            print(f"{self.lm.get('Common.error', 'Error')} loading technicians: {e}")
            self.technicians = []
    
    def _populate_tech_filter(self):
        """Populate technician filter"""
        self.tech_filter.clear()
        self.tech_filter.addItem(self.lm.get("Tickets.all_technicians", "All Technicians"), "all")
        self.tech_filter.addItem(self.lm.get("Tickets.not_assigned", "Not Assigned"), "none")
        
        for tech in self.technicians:
            tech_name = tech.full_name if tech.full_name else f"{self.lm.get('Tickets.technician', 'Technician')} #{tech.id}"
            self.tech_filter.addItem(tech_name, tech.id)
    
    def _on_filter_changed(self, *args):
        """Handle filter changes"""
        QTimer.singleShot(300, self._load_tickets)
    
    def _get_selected_ticket_ids(self):
        """Collect ticket IDs from checked rows OR selected cards"""
        if self.current_view == 'list':
            ids = []
            for row in range(self.tickets_table.rowCount()):
                checkbox_item = self.tickets_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    ticket_item = self.tickets_table.item(row, 1)
                    if ticket_item:
                        tid = ticket_item.data(Qt.UserRole)
                        if tid:
                            ids.append(tid)
            return ids
        else:
            return self.selected_tickets.copy()
    
    def _load_tickets(self):
        """Load tickets with current filters"""
        try:
            self.loading_overlay.start(self.lm.get("Common.loading_tickets", "Loading tickets..."))
            
            search_text = self.search_input.text().strip()
            
            if search_text:
                tickets = self.ticket_controller.search_tickets(search_text)
            else:
                filters = self._build_filters()
                tickets = self.ticket_controller.list_tickets(filters)
            
            # Filter out returned tickets unless "Show All" is checked
            if not self.show_all_checkbox.isChecked():
                tickets = [t for t in tickets if not (t.device and t.device.status == 'returned')]
            
            # Sort tickets by ID descending (newest first)
            tickets.sort(key=lambda x: x.id, reverse=True)

            self._current_ticket_list = tickets
            self._update_statistics(tickets)
            
            if self.current_view == 'cards':
                self._populate_cards_view(tickets)
            elif self.current_view == 'list':
                self._populate_list_view(tickets)
            elif self.current_view == 'kanban':
                self._populate_kanban_view(tickets)
                
        except Exception as e:
            print(f"{self.lm.get('Common.error', 'ERROR')} in _load_tickets: {e}")
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(
                self, 
                self.lm.get('Common.error', 'Error'),
                f"{self.lm.get('TicketMessages.failed_to_load_tickets', 'Failed to load tickets')}: {str(e)}"
            )
        finally:
            if hasattr(self, 'loading_overlay'):
                self.loading_overlay.stop()

    
    def _build_filters(self) -> Dict:
        """Build filter dictionary from UI"""
        filters = {}
        
        # Include deleted
        filters['include_deleted'] = self.show_deleted_checkbox.isChecked()
        
        # Status filter
        status_data = self.status_filter.currentData()
        if status_data:
            filters['status'] = status_data
        
        # Priority filter
        priority_data = self.priority_filter.currentData()
        if priority_data:
            filters['priority'] = priority_data
        
        # Technician filter
        tech_data = self.tech_filter.currentData()
        if tech_data == "none":
            filters['technician_id'] = None
        elif tech_data != "all" and tech_data is not None:
            filters['technician_id'] = tech_data
            
        # Branch context
        if self.current_branch_id:
            filters['branch_id'] = self.current_branch_id
        
        return filters
    
    def _update_statistics(self, tickets: List[TicketDTO]):
        """Update statistics dashboard"""
        total = len(tickets)
        
        # Count all statuses properly
        status_counts = {
            'open': 0,
            'diagnosed': 0,
            'in_progress': 0,
            'awaiting_parts': 0,
            'completed': 0,
            'cancelled': 0,
            'unrepairable': 0
        }
        
        for ticket in tickets:
            if ticket.status in status_counts:
                status_counts[ticket.status] += 1
        
        # Calculate overdue (tickets past deadline)
        now = datetime.now()
        overdue = sum(1 for t in tickets if t.deadline and t.deadline < now and t.status not in ['completed', 'cancelled'])
        
        # Calculate average completion time
        completed_tickets = [t for t in tickets if t.status == 'completed' and t.completed_at and t.created_at]
        if completed_tickets:
            total_hours = sum((t.completed_at - t.created_at).total_seconds() / 3600 for t in completed_tickets)
            avg_time = total_hours / len(completed_tickets)
        else:
            avg_time = 0
        
        # Update metric cards - ensure all statuses are properly counted
        self.metric_cards['total'].update_value(str(total))
        self.metric_cards['open'].update_value(str(status_counts['open']))
        self.metric_cards['in_progress'].update_value(str(status_counts['in_progress']))
        self.metric_cards['completed'].update_value(str(status_counts['completed']))
        self.metric_cards['overdue'].update_value(str(overdue))
        self.metric_cards['avg_time'].update_value(f"{avg_time:.1f}h")
    
    def _populate_cards_view(self, tickets: List[TicketDTO]):
        """Populate cards view"""
        # Clear existing cards
        if self.cards_layout:
            while self.cards_layout.count():
                item = self.cards_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                    else:
                        layout = item.layout()
                        if layout:
                            # Recursively clear sub-layouts
                            self._clear_layout(layout)
        
        # Add ticket cards
        for idx, ticket in enumerate(tickets):
            row = idx // 3
            col = idx % 3
            card = self._create_ticket_card(ticket)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_ticket_card(self, ticket: TicketDTO):
        """Create a ticket card widget"""
        card = QFrame()
        card.setObjectName("ticketCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(180)
        card.setMaximumHeight(220)
        
        # Store ticket data
        card.ticket_id = ticket.id
        card.ticket_dto = ticket
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, ticket)
                event.accept()
            elif event.button() == Qt.RightButton:
                try:
                    global_pos = event.globalPosition().toPoint()
                except AttributeError:
                    global_pos = event.globalPos()
                
                self._show_context_menu(global_pos, ticket)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(ticket)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Ticket number and priority
        header = QHBoxLayout()
        layout.addLayout(header)
        
        ticket_num = QLabel(ticket.ticket_number)
        ticket_num.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(ticket_num)
        
        header.addStretch()
        
        # Priority badge
        priority_key = f"Common.{ticket.priority}"
        priority_text = self.lm.get(priority_key, ticket.priority.upper())
        priority_badge = QLabel(priority_text)
        priority_color = self.get_priority_color(ticket.priority)
        priority_badge.setStyleSheet(f"""
            background-color: {priority_color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(priority_badge)
        
        # Customer name
        customer = QLabel(ticket.customer.name if ticket.customer else self.lm.get("Tickets.no_customer", "No Customer"))
        customer.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        layout.addWidget(customer)
        
        # Device info
        device_info = f"{ticket.device.brand} {ticket.device.model}" if ticket.device else self.lm.get("Tickets.unknown_device", "No Device")
        device = QLabel(device_info)
        device.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(device)
        
        # Issue (truncated)
        issue_text = ticket.error[:50] + "..." if ticket.error and len(ticket.error) > 50 else (ticket.error or self.lm.get("Tickets.issue", "Issue"))
        issue = QLabel(issue_text)
        issue.setStyleSheet("font-size: 11px; color: #6B7280;")
        issue.setWordWrap(True)
        layout.addWidget(issue)
        
        layout.addStretch()
        
        # Footer - Status and technician
        footer = QHBoxLayout()
        
        # Status badge
        status_key = f"Common.{ticket.status}"
        status_text = self.lm.get(status_key, ticket.status.replace('_', ' ').title())
        status_badge = QLabel(status_text)
        status_color = self.get_status_color(ticket.status)
        status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        footer.addWidget(status_badge)
        
        footer.addStretch()
        
        # Technician
        tech_name = ticket.technician_name or self.lm.get("Tickets.not_assigned", "Unassigned")
        tech_label = QLabel(f"👤 {tech_name}")
        tech_label.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        footer.addWidget(tech_label)
        
        layout.addLayout(footer)
        
        # Initial style
        self._update_card_selection_style(card, ticket.id in self.selected_tickets)
        
        return card
    
    def _populate_list_view(self, tickets: List[TicketDTO]):
        """Populate list/table view"""
        self.tickets_table.setRowCount(len(tickets))
        
        for row, ticket in enumerate(tickets):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.tickets_table.setItem(row, 0, checkbox_item)
            
            # Ticket number (store ticket id in UserRole)
            ticket_item = QTableWidgetItem(ticket.ticket_number)
            ticket_item.setData(Qt.UserRole, ticket.id)
            if ticket.is_deleted:
                ticket_item.setForeground(QColor(255, 0, 0))
                font = ticket_item.font()
                font.setItalic(True)
                ticket_item.setFont(font)
            self.tickets_table.setItem(row, 1, ticket_item)
            
            # Customer
            customer_name = ticket.customer.name if ticket.customer else self.lm.get("Tickets.no_customer", "No Customer")
            self.tickets_table.setItem(row, 2, QTableWidgetItem(customer_name))
            
            # Device
            device_str = f"{ticket.device.brand} {ticket.device.model}" if ticket.device else ""
            self.tickets_table.setItem(row, 3, QTableWidgetItem(device_str))
            
            # Issue
            self.tickets_table.setItem(row, 4, QTableWidgetItem(ticket.error or ""))
            
            # Status with color
            status_key = f"Common.{ticket.status}"
            status_text = self.lm.get(status_key, ticket.status.replace('_', ' ').title())
            status_item = QTableWidgetItem(status_text)
            status_color = self.get_status_color(ticket.status)
            status_item.setForeground(QColor(status_color))
            self.tickets_table.setItem(row, 5, status_item)
            
            # Priority with color
            priority_key = f"Common.{ticket.priority}"
            priority_text = self.lm.get(priority_key, ticket.priority.upper())
            priority_item = QTableWidgetItem(priority_text)
            priority_color = self.get_priority_color(ticket.priority)
            priority_item.setForeground(QColor(priority_color))
            self.tickets_table.setItem(row, 6, priority_item)
            
            # Technician
            tech_text = ticket.technician_name or self.lm.get("Tickets.not_assigned", "Unassigned")
            self.tickets_table.setItem(row, 7, QTableWidgetItem(tech_text))
            
            # Created date
            created_str = ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else ""
            self.tickets_table.setItem(row, 8, QTableWidgetItem(created_str))
            
            # Due date
            due_str = ticket.deadline.strftime("%Y-%m-%d") if ticket.deadline else ""
            self.tickets_table.setItem(row, 9, QTableWidgetItem(due_str))
            
            # Visual indicator for deleted tickets
            if ticket.is_deleted:
                for col in range(self.tickets_table.columnCount()):
                    item = self.tickets_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 230, 230))  # Light red background
    
    def _populate_kanban_view(self, tickets: List[TicketDTO]):
        """Populate Kanban board view"""
        self.kanban_view.populate(tickets, self.selected_tickets)
    
    def _on_kanban_card_clicked(self, card, ticket: TicketDTO):
        """Handle kanban card click"""
        if ticket.id in self.selected_tickets:
            self.selected_tickets.remove(ticket.id)
            self.kanban_view.update_card_style(card, False)
        else:
            self.selected_tickets.append(ticket.id)
            self.kanban_view.update_card_style(card, True)
        
        self._update_bulk_buttons_state()
    
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        obj_name = card.objectName()
        
        if is_selected:
            dark_mode = is_dark_theme(self)
            sel_bg = "#374151" if dark_mode else "#EFF6FF"
            
            card.setStyleSheet(f"""
                QFrame#{obj_name} {{
                    background-color: {sel_bg};
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                }}
            """)
        else:
            dark_mode = is_dark_theme(self)
            bg_color = "#1F2937" if dark_mode else "#FFFFFF"
            border_color = "#374151" if dark_mode else "#E5E7EB"
            
            if obj_name == "ticketCard":
                card.setStyleSheet(f"""
                    QFrame#ticketCard {{
                        background-color: {bg_color};
                        border: 1px solid {border_color};
                        border-radius: 8px;
                    }}
                    QFrame#ticketCard:hover {{
                        border-color: #3B82F6;
                        background-color: {bg_color};
                    }}
                """)
            elif obj_name == "kanbanCard":
                card.setStyleSheet(f"""
                    QFrame#kanbanCard {{
                        background-color: {bg_color};
                        border: 1px solid {border_color};
                        border-radius: 6px;
                    }}
                    QFrame#kanbanCard:hover {{
                        border-color: #3B82F6;
                        background-color: {bg_color};
                    }}
                """)

    def _clear_layout(self, layout):
        """Helper to recursively clear a layout and its widgets"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_tickets.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
        
        self._update_bulk_buttons_state()
    
    def _create_new_ticket(self):
        """Create new ticket"""
        self.ticket_controller.show_new_ticket_receipt(self.user.id, self)
    
    def _bulk_update_status(self):
        """Bulk update status for selected tickets"""
        selected_ids = self._get_selected_ticket_ids()
        if not selected_ids:
            MessageHandler.show_warning(self, 
                self.lm.get("Common.warning", "Warning"), 
                self.lm.get("Tickets.select_tickets_warning", "Please select tickets to update.")
            )
            return
            
        # Simple status selection dialog
        status_dialog = QDialog(self)
        status_dialog.setWindowTitle(self.lm.get("Tickets.bulk_update", "Bulk Update Status"))
        layout = QVBoxLayout(status_dialog)
        combo = QComboBox()
        
        status_items = [
            ('open', self.lm.get("Common.open", "Open")),
            ('diagnosed', self.lm.get("Common.diagnosed", "Diagnosed")),
            ('in_progress', self.lm.get("Common.in_progress", "In Progress")),
            ('awaiting_parts', self.lm.get("Common.awaiting_parts", "Awaiting Parts")),
            ('completed', self.lm.get("Common.completed", "Completed")),
            ('cancelled', self.lm.get("Common.cancelled", "Cancelled")),
            ('unrepairable', self.lm.get("Common.unrepairable", "Unrepairable"))
        ]
        for key, label in status_items:
            combo.addItem(label, key)
            
        layout.addWidget(QLabel(self.lm.get("Common.select_status", "Select new status") + ":"))
        layout.addWidget(combo)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btns)
        btns.accepted.connect(status_dialog.accept)
        btns.rejected.connect(status_dialog.reject)
        
        if status_dialog.exec() == QDialog.Accepted:
            new_status = combo.currentData()
            for tid in selected_ids:
                self.ticket_controller.change_ticket_status(
                    tid, new_status, 
                    reason=self.lm.get('TicketMessages.status_updated_bulk', 'Bulk Update'),
                    current_user=self.user, 
                    ip_address='127.0.0.1'
                )
            MessageHandler.show_info(self, 
                self.lm.get("Tickets.bulk_update", "Bulk Update"), 
                f"{self.lm.get('TicketMessages.tickets_updated_to', 'Updated')} {len(selected_ids)} {self.lm.get('Tickets.tickets', 'tickets')} {self.lm.get('TicketMessages.to_status', 'to')} {new_status}."
            )
            self._load_tickets()
    
    def _bulk_assign_technician(self):
        """Bulk assign a technician to selected tickets"""
        selected_ids = self._get_selected_ticket_ids()
        if not selected_ids:
            MessageHandler.show_warning(self, 
                self.lm.get("Common.warning", "Warning"), 
                self.lm.get("Tickets.select_tickets_warning", "Please select tickets to assign.")
            )
            return
            
        # Technician selection dialog
        tech_dialog = QDialog(self)
        tech_dialog.setWindowTitle(self.lm.get("Tickets.bulk_assign", "Bulk Assign Technician"))
        layout = QVBoxLayout(tech_dialog)
        combo = QComboBox()
        combo.addItem(self.lm.get("Tickets.not_assigned", "Not Assigned"), None)
        for tech in self.technicians:
            name = tech.full_name if tech.full_name else f"{self.lm.get('Tickets.technician', 'Technician')} #{tech.id}"
            combo.addItem(name, tech.id)
        layout.addWidget(QLabel(self.lm.get("Common.select_technician", "Select technician") + ":"))
        layout.addWidget(combo)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btns)
        btns.accepted.connect(tech_dialog.accept)
        btns.rejected.connect(tech_dialog.reject)
        
        if tech_dialog.exec() == QDialog.Accepted:
            tech_id = combo.currentData()
            for tid in selected_ids:
                # Use assign_ticket method
                self.ticket_controller.assign_ticket(
                    tid, tech_id, 
                    current_user=self.user, 
                    ip_address='127.0.0.1'
                )
            MessageHandler.show_info(self, 
                self.lm.get("Tickets.bulk_assign", "Bulk Assign"), 
                f"{self.lm.get('TicketMessages.assigned_tickets', 'Assigned')} {len(selected_ids)} {self.lm.get('Tickets.tickets', 'tickets')}."
            )
            self._load_tickets()
    
    def _export_tickets_csv(self):
        """Export tickets to CSV"""
        if not self._current_ticket_list:
            MessageHandler.show_info(self, self.lm.get("Common.info", "Info"), self.lm.get("Tickets.no_tickets_to_export", "No tickets to export"))
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            self.lm.get("Tickets.save_csv", "Save CSV"), 
            f"tickets_{datetime.now().strftime('%Y%m%d')}.csv", 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return
            
        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write Headers
                writer.writerow([
                    self.lm.get("Tickets.ticket_num", "Ticket #"),
                    self.lm.get("Tickets.customer", "Customer"),
                    self.lm.get("Tickets.device", "Device"),
                    self.lm.get("Tickets.issue", "Issue"),
                    self.lm.get("Tickets.status", "Status"),
                    self.lm.get("Tickets.priority", "Priority"),
                    self.lm.get("Tickets.technician", "Technician"),
                    self.lm.get("Tickets.created", "Created"),
                    self.lm.get("Tickets.deadline", "Due Date"),
                    self.lm.get("Tickets.estimated_cost", "Est. Cost"),
                    self.lm.get("Tickets.paid", "Paid"),
                    self.lm.get("Tickets.balance", "Balance"),
                    self.lm.get("Tickets.internal_notes", "Internal Notes")
                ])
                
                # Write Data
                for ticket in self._current_ticket_list:
                    # formatted data
                    customer_name = ticket.customer.name if ticket.customer else "N/A"
                    device_name = f"{ticket.device.brand} {ticket.device.model}" if ticket.device else "N/A"
                    technician_name = ticket.technician_name or "Unassigned"
                    created_str = ticket.created_at.strftime("%Y-%m-%d %H:%M") if ticket.created_at else ""
                    due_str = ticket.deadline.strftime("%Y-%m-%d") if ticket.deadline else ""
                    
                    est_cost = ticket.estimated_cost or 0.0
                    paid = ticket.deposit_paid or 0.0
                    balance = est_cost - paid
                    
                    writer.writerow([
                        ticket.ticket_number,
                        customer_name,
                        device_name,
                        ticket.error or "",
                        ticket.status,
                        ticket.priority,
                        technician_name,
                        created_str,
                        due_str,
                        f"{est_cost:.2f}",
                        f"{paid:.2f}",
                        f"{balance:.2f}",
                        ticket.internal_notes or ""
                    ])
            
            MessageHandler.show_success(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Tickets.export_success', 'Successfully exported')} {len(self._current_ticket_list)} {self.lm.get('Tickets.tickets', 'tickets')}."
            )
            
        except Exception as e:
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Tickets.export_failed', 'Failed to export tickets')}: {str(e)}"
            )
    
    def _export_tickets_pdf(self):
        """Export tickets to PDF report using WeasyPrint"""
        if not self._current_ticket_list:
            MessageHandler.show_info(self, self.lm.get("Common.info", "Info"), self.lm.get("Tickets.no_tickets_to_export", "No tickets to export"))
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            self.lm.get("Tickets.export_pdf", "Save PDF"), 
            f"tickets_report_{datetime.now().strftime('%Y%m%d')}.pdf", 
            "PDF Files (*.pdf)"
        )
        
        if not path:
            return
            
        try:
            # Import WeasyPrint (lazy import)
            import platform
            import os
            
            # MacOS Fix for WeasyPrint
            if platform.system() == 'Darwin':
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
            
            from weasyprint import HTML, CSS
            
            # Use fonts that support Burmese
            font_family = "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"
            
            html = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4 landscape; margin: 15mm; }}
                    body {{ font-family: {font_family}; }}
                    h1 {{ color: #2980B9; margin-bottom: 5px; }}
                    .meta {{ font-size: 10pt; color: #7F8C8D; margin-bottom: 20px; }}
                    
                    /* Summary Boxes */
                    .summary-container {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .summary-box {{ 
                        border: 1px solid #BDC3C7; 
                        padding: 10px; 
                        width: 200px;
                        background-color: #ECF0F1;
                        border-radius: 4px;
                    }}
                    .summary-label {{ font-size: 9pt; color: #7F8C8D; }}
                    .summary-value {{ font-size: 11pt; font-weight: bold; color: #2C3E50; }}
                    
                    /* Table */
                    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
                    th {{ 
                        background-color: #3498DB; 
                        color: white; 
                        padding: 8px; 
                        text-align: left; 
                        border: 1px solid #2980B9;
                    }}
                    td {{ 
                        padding: 6px; 
                        border: 1px solid #BDC3C7; 
                        color: #2C3E50;
                    }}
                    tr:nth-child(even) {{ background-color: #F8F9F9; }}
                    
                    /* Status Colors */
                    .status-open {{ color: #2980B9; }}
                    .status-completed {{ color: #27AE60; font-weight: bold; }}
                    .status-cancelled {{ color: #C0392B; }}
                    .status-in_progress {{ color: #E67E22; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Tickets.report_title", "TICKETS REPORT")}</h1>
                <div class="meta">{self.lm.get("Tickets.generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            """
            
            # Calculate Summary
            total_est = 0.0
            total_paid = 0.0
            open_count = 0
            completed_count = 0
            
            rows_html = ""
            
            for ticket in self._current_ticket_list:
                est = ticket.estimated_cost or 0.0
                paid = ticket.deposit_paid or 0.0
                total_est += est
                total_paid += paid
                
                if ticket.status == 'completed':
                    completed_count += 1
                elif ticket.status not in ['cancelled', 'unrepairable']:
                    open_count += 1
                    
                customer_name = ticket.customer.name if ticket.customer else "N/A"
                device_name = f"{ticket.device.brand} {ticket.device.model}" if ticket.device else "N/A"
                technician_name = ticket.technician_name or "Unassigned"
                created_str = ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else ""
                
                rows_html += f"""
                <tr>
                    <td>{ticket.ticket_number}</td>
                    <td>{customer_name}</td>
                    <td>{device_name}</td>
                    <td><span class="status-{ticket.status}">{ticket.status.replace('_', ' ').title()}</span></td>
                    <td>{technician_name}</td>
                    <td>{created_str}</td>
                    <td>{est:,.0f}</td>
                    <td>{paid:,.0f}</td>
                </tr>
                """
            
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Tickets.total_tickets", "Total Tickets")}</div>
                        <div class="summary-value">{len(self._current_ticket_list)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Tickets.open_tickets", "Open Tickets")}</div>
                        <div class="summary-value">{open_count}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Tickets.completed_tickets", "Completed Tickets")}</div>
                        <div class="summary-value">{completed_count}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Tickets.total_estimated", "Total Estimated")}</div>
                        <div class="summary-value">{total_est:,.0f}</div>
                    </div>
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Tickets.total_paid", "Total Paid")}</div>
                        <div class="summary-value">{total_paid:,.0f}</div>
                    </div>
                </div>
            """
            
            # Add Table
            html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Tickets.ticket_num", "Ticket #")}</th>
                            <th>{self.lm.get("Tickets.customer", "Customer")}</th>
                            <th>{self.lm.get("Tickets.device", "Device")}</th>
                            <th>{self.lm.get("Tickets.status", "Status")}</th>
                            <th>{self.lm.get("Tickets.technician", "Technician")}</th>
                            <th>{self.lm.get("Tickets.created", "Created")}</th>
                            <th>{self.lm.get("Tickets.estimated_cost", "Est. Cost")}</th>
                            <th>{self.lm.get("Tickets.paid", "Paid")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Generate PDF
            HTML(string=html).write_pdf(path)
            
            MessageHandler.show_success(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Tickets.export_success', 'Successfully exported')} {len(self._current_ticket_list)} {self.lm.get('Tickets.tickets', 'tickets')}."
            )
            
        except Exception as e:
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Tickets.export_failed', 'Failed to export tickets')}: {str(e)}"
            )

    def _on_ticket_changed(self, *args):
        """Handle ticket changes"""
        QTimer.singleShot(500, self._load_tickets)

    def _subscribe_to_events(self):
        """Subscribe to domain events"""
        EventBus.subscribe(TicketCreatedEvent, self._handle_ticket_event)
        EventBus.subscribe(TicketUpdatedEvent, self._handle_ticket_event)
        EventBus.subscribe(TicketDeletedEvent, self._handle_ticket_event)
        EventBus.subscribe(TicketRestoredEvent, self._handle_ticket_event)
        EventBus.subscribe(TicketStatusChangedEvent, self._handle_ticket_event)
        EventBus.subscribe(TicketTechnicianAssignedEvent, self._handle_ticket_event)
        EventBus.subscribe(InvoiceCreatedEvent, self._handle_ticket_event)
        
        # Technician events
        EventBus.subscribe(TechnicianCreatedEvent, self._handle_technician_event)
        EventBus.subscribe(TechnicianUpdatedEvent, self._handle_technician_event)
        EventBus.subscribe(TechnicianDeactivatedEvent, self._handle_technician_event)
        
        # Branch events
        EventBus.subscribe(BranchContextChangedEvent, self._handle_branch_changed_event)

    def _handle_branch_changed_event(self, event: BranchContextChangedEvent):
        """Handle branch context change"""
        self.current_branch_id = event.branch_id
        # Reload tickets
        QTimer.singleShot(50, self._load_tickets)

    def _handle_technician_event(self, event):
        """Handle technician events"""
        QTimer.singleShot(100, self._load_technicians)

    def _handle_ticket_event(self, event):
        """Handle ticket domain events"""
        print(f"DEBUG: ModernTicketsTab received event: {event}")
        # Call _load_tickets directly for immediate refresh (no double debouncing)
        # Use minimal delay to ensure UI updates happen on main thread
        QTimer.singleShot(100, self._load_tickets)

    def closeEvent(self, event):
        """Clean up resources"""
        self._unsubscribe_from_events()
        super().closeEvent(event)

    def _unsubscribe_from_events(self):
        """Unsubscribe from domain events"""
        events = [
            TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
            TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent,
            InvoiceCreatedEvent
        ]
        for event_type in events:
            EventBus.unsubscribe(event_type, self._handle_ticket_event)