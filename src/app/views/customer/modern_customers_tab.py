# src/app/views/customer/modern_customers_tab.py
"""
Modern Customers Tab with enhanced UI features:
- Card/Grid view
- Credit/Debit tracking
- Advanced filtering
- Bulk operations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QCheckBox, QFrame, QScrollArea,
    QGridLayout, QStackedWidget, QDialog, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor
from typing import List, Dict
from decimal import Decimal
from dtos.customer_dto import CustomerDTO
from utils.validation.message_handler import MessageHandler
from utils.validation.phone_formatter import phone_formatter
from views.customer.customer_details_dialog import CustomerDetailsDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from core.event_bus import EventBus
from core.events import (
    CustomerCreatedEvent, CustomerUpdatedEvent, CustomerDeletedEvent,
    InvoiceCreatedEvent, InvoiceUpdatedEvent
)
from views.components.loading_overlay import LoadingOverlay


class ModernCustomersTab(QWidget):
    """Modern customer management interface with financial tracking"""
    
    customer_selected = Signal(CustomerDTO)
    
    def __init__(
        self,
        customer_controller,
        invoice_controller,
        user,
        container=None
    ):
        """
        Initialize the customers tab.
        
        Args:
            customer_controller: Controller for customer operations
            invoice_controller: Controller for invoice operations (for balance calculation)
            user: Current user
            container: Legacy dependency container (optional)
        """
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        self.cf = currency_formatter
        
        # Explicit dependencies
        self.customer_controller = customer_controller
        self.invoice_controller = invoice_controller
        
        self.customers = []
        self.selected_customers = []
        self.current_view = 'cards'
        self._customer_balances = {}  # Cache for customer balances
        
        self.loading_overlay = LoadingOverlay(self)
        
        self._setup_ui()
        self._connect_signals()
        
        # self._load_customers()
        self._data_loaded = False
        
    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
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
        
        self.view_stack.addWidget(self.cards_view)
        self.view_stack.addWidget(self.list_view)
        
        layout.addWidget(self.view_stack, 1)
        
    def _create_header(self):
        """Create header with title and view switcher"""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("Customers.customers_title", "Customers"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Common.view", "View") + ":")
        view_label.setObjectName("metricLabel")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Tickets.cards_view', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Tickets.list_view', 'List')}")
        
        self.cards_view_btn.setCheckable(True)
        self.list_view_btn.setCheckable(True)
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
        
        for btn in [self.cards_view_btn, self.list_view_btn]:
            btn.setStyleSheet(view_btn_style)
            layout.addWidget(btn)
        
        return layout
    
    def _create_advanced_filters(self):
        """Create advanced filter controls"""
        layout = QVBoxLayout()
        
        # First row - Search and basic filters
        row1 = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {self.lm.get('Customers.search_customers', 'Search by name, phone, email, address...')}")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(300)
        row1.addWidget(self.search_input)
        
        # Balance filter
        self.balance_filter = QComboBox()
        self.balance_filter.addItem(self.lm.get("Customers.all_customers", "All Balances"), "all")
        self.balance_filter.addItem(self.lm.get("Customers.has_balance", "Has Debit (Owes)"), "debit")
        self.balance_filter.addItem(self.lm.get("Customers.credit", "Has Credit"), "credit")
        self.balance_filter.addItem(self.lm.get("Customers.no_balance", "Zero Balance"), "zero")
        self.balance_filter.setMinimumWidth(150)
        row1.addWidget(self.balance_filter)
        
        row1.addStretch()
        
        layout.addLayout(row1)
        
        # Second row - Additional filters
        row2 = QHBoxLayout()
        
        # Show deleted
        self.show_deleted_checkbox = QCheckBox(self.lm.get("Customers.show_deleted", "Show Deleted"))
        row2.addWidget(self.show_deleted_checkbox)
        
        row2.addStretch()
        
        # Clear filters button
        clear_btn = QPushButton(f"🔄 {self.lm.get('Tickets.clear_filters', 'Clear Filters')}")
        clear_btn.clicked.connect(self._clear_filters)
        row2.addWidget(clear_btn)
        
        layout.addLayout(row2)
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # New customer button (primary)
        self.new_customer_btn = QPushButton(f"➕ {self.lm.get('Customers.new_customer', 'New Customer')}")
        self.new_customer_btn.setStyleSheet("""
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
        layout.addWidget(self.new_customer_btn)
        
        # Bulk delete button
        self.bulk_delete_btn = QPushButton(f"🗑️ {self.lm.get('Customers.bulk_delete', 'Bulk Delete')}")
        self.bulk_delete_btn.setEnabled(False)
        layout.addWidget(self.bulk_delete_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_customers)
        layout.addWidget(refresh_btn)
        
        # Export button
        export_btn = QPushButton(f"📥 {self.lm.get('Common.export', 'Export')}")
        export_btn.clicked.connect(self._export_customers)
        layout.addWidget(export_btn)
        
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
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        headers = [
            "✓",
            self.lm.get("Customers.customer_name", "Name"),
            self.lm.get("Customers.customer_phone", "Phone"),
            self.lm.get("Customers.customer_email", "Email"),
            self.lm.get("Customers.balance", "Balance"),
            self.lm.get("Customers.device_count", "Devices"),
            self.lm.get("Customers.last_visit", "Last Visit")
        ]
        self.customers_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customers_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customers_table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setColumnWidth(0, 40)
        
        return self.customers_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.balance_filter.currentTextChanged.connect(self._on_filter_changed)
        self.show_deleted_checkbox.stateChanged.connect(self._on_filter_changed)
        
        # Actions
        self.new_customer_btn.clicked.connect(self._create_new_customer)
        self.bulk_delete_btn.clicked.connect(self._bulk_delete_customers)
        self.customers_table.itemChanged.connect(self._update_bulk_buttons_state)
        
        # Table double click
        self.customers_table.doubleClicked.connect(self._on_table_double_click)
        
        # Subscribe to EventBus events
        EventBus.subscribe(CustomerCreatedEvent, self._handle_customer_event)
        EventBus.subscribe(CustomerUpdatedEvent, self._handle_customer_event)
        EventBus.subscribe(CustomerDeletedEvent, self._handle_customer_event)
        EventBus.subscribe(InvoiceCreatedEvent, self._handle_customer_event)  # Balance changes
        EventBus.subscribe(InvoiceUpdatedEvent, self._handle_customer_event)  # Balance changes
    
    def _switch_view(self, view_mode):
        """Switch between different view modes"""
        self.current_view = view_mode
        
        # Update button states
        self.cards_view_btn.setChecked(view_mode == 'cards')
        self.list_view_btn.setChecked(view_mode == 'list')
        
        # Switch view
        if view_mode == 'cards':
            self.view_stack.setCurrentWidget(self.cards_view)
        elif view_mode == 'list':
            self.view_stack.setCurrentWidget(self.list_view)
        
        # Reload customers for the new view
        self._load_customers()
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.balance_filter.setCurrentIndex(0)
        self.show_deleted_checkbox.setChecked(False)
    
    def _on_filter_changed(self, *args):
        """Handle filter changes"""
        QTimer.singleShot(300, self._load_customers)
    
    def _update_bulk_buttons_state(self, *args):
        """Enable bulk action buttons when any row is checked or card selected"""
        any_checked = False
        
        if self.current_view == 'list':
            for row in range(self.customers_table.rowCount()):
                item = self.customers_table.item(row, 0)
                if item and item.checkState() == Qt.Checked:
                    any_checked = True
                    break
        else:
            any_checked = len(self.selected_customers) > 0
        
        self.bulk_delete_btn.setEnabled(any_checked)
    
    def _get_selected_customer_ids(self):
        """Collect customer IDs from checked rows OR selected cards"""
        if self.current_view == 'list':
            ids = []
            for row in range(self.customers_table.rowCount()):
                checkbox_item = self.customers_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    customer_item = self.customers_table.item(row, 1)
                    if customer_item:
                        cid = customer_item.data(Qt.UserRole)
                        if cid:
                            ids.append(cid)
            return ids
        else:
            return self.selected_customers.copy()
    
    def _calculate_customer_balance(self, customer_id: int) -> Dict:
        """Calculate customer's financial balance from invoices"""
        # Check cache first
        if customer_id in self._customer_balances:
            return self._customer_balances[customer_id]
        
        balance_info = {
            'total_invoices': 0,
            'total_owed': Decimal('0.00'),
            'total_credit': Decimal('0.00'),
            'balance': Decimal('0.00')
        }
        
        try:
            if self.invoice_controller:
                server_balance = self.invoice_controller.get_customer_balance_info(customer_id)
                if server_balance:
                    balance_info = server_balance
        except Exception as e:
            print(f"Error calculating balance for customer {customer_id}: {e}")
            import traceback
            traceback.print_exc()
        
        # Cache the result
        self._customer_balances[customer_id] = balance_info
        return balance_info
    
    def _get_balance_color(self, balance: Decimal) -> str:
        """Get color for balance display"""
        if balance > 0:
            return '#EF4444'  # Red - customer owes
        elif balance < 0:
            return '#10B981'  # Green - customer has credit
        else:
            return '#6B7280'  # Gray - zero balance
    
    def _format_balance(self, balance: Decimal) -> str:
        """Format balance for display"""
        if balance > 0:
            return f"+{self.cf.format(balance)}"
        elif balance < 0:
            return f"-{self.cf.format(abs(balance))}"
        else:
            return self.cf.format(0)
    
    def _load_customers(self):
        """Load customers with current filters"""
        try:
            self.loading_overlay.start(self.lm.get("Common.loading_customers", "Loading customers..."))
            
            # Clear balance cache
            self._customer_balances = {}
            
            search_term = self.search_input.text().strip()
            
            # Get all customers
            if self.show_deleted_checkbox.isChecked():
                customers = self.customer_controller.get_all_customers_including_deleted()
            else:
                customers = self.customer_controller.get_all_customers()
            
            # Apply search filter
            if search_term:
                search_lower = search_term.lower()
                customers = [
                    c for c in customers
                    if (search_lower in (c.name or '').lower() or
                        search_lower in (c.phone or '').lower() or
                        search_lower in (c.email or '').lower() or
                        search_lower in (c.address or '').lower())
                ]
            
            # Apply balance filter
            balance_key = self.balance_filter.currentData()
            if balance_key and balance_key != "all":
                filtered = []
                for c in customers:
                    balance_info = self._calculate_customer_balance(c.id)
                    balance = balance_info['balance']
                    
                    if balance_key == "debit" and balance > 0:
                        filtered.append(c)
                    elif balance_key == "credit" and balance < 0:
                        filtered.append(c)
                    elif balance_key == "zero" and balance == 0:
                        filtered.append(c)
                customers = filtered
            
            # Store current customers for reference
            self._current_customer_list = customers
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(customers)
            elif self.current_view == 'list':
                self._populate_list_view(customers)
                
        except Exception as e:
            print(f"Error loading customers: {e}")
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), f"Failed to load customers: {str(e)}")
        finally:
            self.loading_overlay.stop()

    
    def _build_filters(self) -> Dict:
        """Build filter dictionary from UI"""
        filters = {}
        filters['include_deleted'] = self.show_deleted_checkbox.isChecked()
        return filters
    
    def _populate_cards_view(self, customers: List[CustomerDTO]):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add customer cards
        for idx, customer in enumerate(customers):
            row = idx // 3
            col = idx % 3
            card = self._create_customer_card(customer)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_customer_card(self, customer: CustomerDTO):
        """Create a customer card widget"""
        card = QFrame()
        card.setObjectName("customerCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        # Store customer data
        card.customer_id = customer.id
        card.customer_dto = customer
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, customer)
                event.accept()
            elif event.button() == Qt.RightButton:
                self._show_context_menu(customer)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(customer)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Name and balance
        header = QHBoxLayout()
        
        name = QLabel(customer.name or "Unknown")
        name.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(name)
        
        header.addStretch()
        
        # Balance badge
        balance_info = self._calculate_customer_balance(customer.id)
        balance = balance_info['balance']
        balance_color = self._get_balance_color(balance)
        balance_text = self._format_balance(balance)
        
        balance_badge = QLabel(balance_text)
        balance_badge.setStyleSheet(f"""
            background-color: {balance_color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(balance_badge)
        
        layout.addLayout(header)
        
        # Phone
        phone = QLabel(phone_formatter.format_phone_number(customer.phone) if customer.phone else "No phone")
        phone.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        layout.addWidget(phone)
        
        # Email
        email = QLabel(customer.email if customer.email else "No email")
        email.setStyleSheet("font-size: 11px; color: #6B7280;")
        layout.addWidget(email)
        
        # Address (truncated)
        if customer.address:
            address = QLabel(customer.address[:40] + "..." if len(customer.address) > 40 else customer.address)
            address.setStyleSheet("font-size: 11px; color: #6B7280;")
            layout.addWidget(address)
        
        # Device count and last visit
        devices = self.customer_controller.get_customer_devices(customer.id)
        device_count = len(devices)
        last_visit = customer.updated_at.strftime("%Y-%m-%d") if customer.updated_at else "Never"
        
        details = f"{self.lm.get('Customers.device_count', 'Devices')}: {device_count} | {self.lm.get('Customers.last_visit', 'Last Visit')}: {last_visit}"
        details_label = QLabel(details)
        details_label.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        layout.addWidget(details_label)
        
        layout.addStretch()
        
        # Initial style
        self._update_card_selection_style(card, customer.id in self.selected_customers)
        
        return card
    
    def _populate_list_view(self, customers: List[CustomerDTO]):
        """Populate list/table view"""
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.customers_table.setItem(row, 0, checkbox_item)
            
            # Name (store customer id in UserRole)
            name_item = QTableWidgetItem(customer.name or "")
            name_item.setData(Qt.UserRole, customer.id)
            self.customers_table.setItem(row, 1, name_item)
            
            # Phone
            phone = phone_formatter.format_phone_number(customer.phone) if customer.phone else ""
            self.customers_table.setItem(row, 2, QTableWidgetItem(phone))
            
            # Email
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer.email or ""))
            
            # Balance with color
            balance_info = self._calculate_customer_balance(customer.id)
            balance = balance_info['balance']
            balance_text = self._format_balance(balance)
            balance_item = QTableWidgetItem(balance_text)
            balance_item.setForeground(QColor(self._get_balance_color(balance)))
            self.customers_table.setItem(row, 4, balance_item)
            
            # Devices
            devices = self.customer_controller.get_customer_devices(customer.id)
            self.customers_table.setItem(row, 5, QTableWidgetItem(str(len(devices))))
            
            # Last Visit
            last_visit = customer.updated_at.strftime("%Y-%m-%d") if customer.updated_at else ""
            self.customers_table.setItem(row, 6, QTableWidgetItem(last_visit))
    
    def _on_table_double_click(self, index):
        """Open customer detail dialog on double click"""
        row = index.row()
        customer_item = self.customers_table.item(row, 1)
        if not customer_item:
            return
        customer_id = customer_item.data(Qt.UserRole)
        if not customer_id:
            return
        customer_dto = self.customer_controller.get_customer(customer_id)
        if customer_dto:
            devices = self.customer_controller.get_customer_devices(customer_id)
            balance_info = self._calculate_customer_balance(customer_id)
            dialog = CustomerDetailsDialog(customer_dto, devices, balance_info, self.container, parent=self)
            dialog.exec()
    
    def _on_card_clicked(self, card, customer: CustomerDTO):
        """Handle card click (toggle selection)"""
        if customer.id in self.selected_customers:
            self.selected_customers.remove(customer.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_customers.append(customer.id)
            self._update_card_selection_style(card, True)
        
        self._update_bulk_buttons_state()
        
    def _on_card_double_clicked(self, customer: CustomerDTO):
        """Handle card double click (open details)"""
        devices = self.customer_controller.get_customer_devices(customer.id)
        balance_info = self._calculate_customer_balance(customer.id)
        dialog = CustomerDetailsDialog(customer, devices, balance_info, self.container, parent=self)
        dialog.exec()
        
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        if is_selected:
            card.setStyleSheet("""
                QFrame#customerCard {
                    background-color: #374151;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#customerCard {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                }
                QFrame#customerCard:hover {
                    border-color: #3B82F6;
                    background-color: #374151;
                }
            """)

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_customers.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
        
        self._update_bulk_buttons_state()
    
    def _create_new_customer(self):
        """Create new customer"""
        self.customer_controller.show_new_customer_form(user_id=self.user.id, parent=self)
    
    def _bulk_delete_customers(self):
        """Bulk delete selected customers"""
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            MessageHandler.show_warning(self, "No customers selected", "Please select customers to delete.")
            return
        
        if MessageHandler.show_question(
            self,
            "Confirm Bulk Delete",
            f"Are you sure you want to delete {len(selected_ids)} customers?"
        ):
            for cid in selected_ids:
                self.customer_controller.delete_customer(cid, self.user.id)
            MessageHandler.show_info(self, "Bulk Delete", f"Deleted {len(selected_ids)} customers.")
            self._load_customers()
    
    def _export_customers(self):
        """Export customers to CSV"""
        MessageHandler.show_info(self, "Coming Soon", "Export feature coming soon!")
        
    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        table = self.sender()
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        name_item = table.item(row, 1)
        if not name_item:
            return
            
        customer_id = name_item.data(Qt.UserRole)
        if customer_id:
            customer = next((c for c in self._current_customer_list if c.id == customer_id), None)
            if customer:
                self._show_context_menu(customer)

    def _show_context_menu(self, customer):
        """Show context menu for customer"""
        menu = QMenu(self)
        
        # Actions
        view_action = QAction(f"📄 {self.lm.get('Customers.view_details', 'View Details')}", self)
        view_action.triggered.connect(lambda: self._on_card_double_clicked(customer))
        menu.addAction(view_action)
        
        edit_action = QAction(f"✏️ {self.lm.get('Customers.edit_customer', 'Edit Customer')}", self)
        edit_action.triggered.connect(lambda: self.customer_controller.show_edit_customer_form(customer.id, self.user.id, self))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction(f"🗑️ {self.lm.get('Customers.delete_customer', 'Delete Customer')}", self)
        delete_action.triggered.connect(lambda: self._delete_single_customer(customer))
        menu.addAction(delete_action)
        
        menu.exec(self.cursor().pos())
        
    def _delete_single_customer(self, customer):
        """Delete a single customer"""
        if MessageHandler.show_question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete customer '{customer.name}'?"
        ):
            if self.customer_controller.delete_customer(customer.id, self.user.id):
                MessageHandler.show_success(self, "Success", "Customer deleted successfully")
                self._load_customers()
    
    def _on_customer_changed(self, *args):
        """Handle customer changes"""
        QTimer.singleShot(500, self._load_customers)
    
    def _handle_customer_event(self, event):
        """Handle customer-related EventBus events"""
        # Refresh customer list when any customer or invoice event occurs
        QTimer.singleShot(500, self._load_customers)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # Use timer to let UI render first
            QTimer.singleShot(100, self._load_customers)
            self._data_loaded = True

