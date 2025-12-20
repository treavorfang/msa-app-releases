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
    QTableWidgetItem, QHeaderView, QMenu, QFileDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor
from typing import List, Dict
try:
    from decimal import Decimal, InvalidOperation
except ImportError:
    from decimal import Decimal
    InvalidOperation = Exception # Fallback
import csv
from datetime import datetime
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
from views.components.new_dashboard_widgets import is_dark_theme


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
        
        # Export button with menu
        export_btn = QPushButton(f"📥 {self.lm.get('Common.export', 'Export')}")
        export_menu = QMenu(self)
        
        # CSV Action
        export_csv_action = QAction(self.lm.get("Customers.export_csv", "Export CSV"), self)
        export_csv_action.triggered.connect(self._export_customers_csv)
        export_menu.addAction(export_csv_action)
        
        # PDF Action
        export_pdf_action = QAction(self.lm.get("Customers.export_pdf", "Export PDF"), self)
        export_pdf_action.triggered.connect(self._export_customers_pdf)
        export_menu.addAction(export_pdf_action)
        
        export_btn.setMenu(export_menu)
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
        
        self._connect_theme_signal()

    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        self._load_customers()
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
                    # Ensure all values are Decimal
                    def safe_decimal(val):
                        try:
                            return Decimal(str(val))
                        except (ValueError, TypeError, InvalidOperation):
                            return Decimal('0.00')

                    balance_info = {
                        'total_invoices': server_balance.get('total_invoices', 0),
                        'total_owed': safe_decimal(server_balance.get('total_owed', 0)),
                        'total_credit': safe_decimal(server_balance.get('total_credit', 0)),
                        'balance': safe_decimal(server_balance.get('balance', 0))
                    }
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
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        text_main = "white" if dark_mode else "#1F2937"
        text_sub = "#9CA3AF" if dark_mode else "#6B7280"
        
        card = QFrame()
        card.setObjectName("customerCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        # Initial style is handled by _update_card_selection_style logic or here for base
        # Logic in _update_card_selection_style will overwrite this, but we set base props here via stylesheet if needed
        # Actually, we rely on _update_card_selection_style at the end, but let's set a base style to be safe
        card.setStyleSheet(f"""
            QFrame#customerCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#customerCard:hover {{
                border-color: #3B82F6;
                background-color: {bg_color};
            }}
        """)
        
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
        name.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_main};")
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
        phone.setStyleSheet(f"font-size: 12px; color: {text_sub};")
        layout.addWidget(phone)
        
        # Email
        email = QLabel(customer.email if customer.email else "No email")
        email.setStyleSheet(f"font-size: 11px; color: {text_sub};")
        layout.addWidget(email)
        
        # Address (truncated)
        if customer.address:
            address = QLabel(customer.address[:40] + "..." if len(customer.address) > 40 else customer.address)
            address.setStyleSheet(f"font-size: 11px; color: {text_sub};")
            layout.addWidget(address)
        
        # Device count and last visit
        devices = self.customer_controller.get_customer_devices(customer.id)
        device_count = len(devices)
        last_visit = customer.updated_at.strftime("%Y-%m-%d") if customer.updated_at else "Never"
        
        details = f"{self.lm.get('Customers.device_count', 'Devices')}: {device_count} | {self.lm.get('Customers.last_visit', 'Last Visit')}: {last_visit}"
        details_label = QLabel(details)
        details_label.setStyleSheet(f"font-size: 10px; color: {text_sub};")
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
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        # Base colors
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        
        # Selection colors
        sel_bg = "#374151" if dark_mode else "#EFF6FF"
        sel_border = "#3B82F6" # Stay blue
        
        if is_selected:
            card.setStyleSheet(f"""
                QFrame#customerCard {{
                    background-color: {sel_bg};
                    border: 2px solid {sel_border};
                    border-radius: 8px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame#customerCard {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                }}
                QFrame#customerCard:hover {{
                    border-color: {sel_border};
                    background-color: {bg_color};
                }}
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
    
    def _export_customers_csv(self):
        """Export customers to CSV"""
        if not hasattr(self, '_current_customer_list') or not self._current_customer_list:
            MessageHandler.show_info(self, self.lm.get("Common.info", "Info"), self.lm.get("Customers.no_customers_to_export", "No customers to export"))
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            self.lm.get("Customers.save_csv", "Save CSV"), 
            f"customers_{datetime.now().strftime('%Y%m%d')}.csv", 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return
            
        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write Headers
                writer.writerow([
                    self.lm.get("Customers.customer_name", "Name"),
                    self.lm.get("Customers.customer_phone", "Phone"),
                    self.lm.get("Customers.customer_email", "Email"),
                    self.lm.get("Customers.customer_address", "Address"),
                    self.lm.get("Customers.balance", "Balance"),
                    self.lm.get("Customers.device_count", "Devices"),
                    self.lm.get("Customers.last_visit", "Last Visit")
                ])
                
                # Write Data
                for customer in self._current_customer_list:
                    # Calculate proper balance
                    balance_info = self._calculate_customer_balance(customer.id)
                    balance = balance_info['balance']
                    devices = self.customer_controller.get_customer_devices(customer.id)
                    
                    writer.writerow([
                        customer.name or "",
                        phone_formatter.format_phone_number(customer.phone) if customer.phone else "",
                        customer.email or "",
                        customer.address or "",
                        f"{balance:.2f}",
                        len(devices),
                        customer.updated_at.strftime("%Y-%m-%d") if customer.updated_at else ""
                    ])
            
            MessageHandler.show_success(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Customers.export_success', 'Successfully exported')} {len(self._current_customer_list)} {self.lm.get('Customers.customers', 'customers')}."
            )
            
        except Exception as e:
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Customers.export_failed', 'Failed to export customers')}: {str(e)}"
            )

    def _export_customers_pdf(self):
        """Export customers to PDF report using WeasyPrint"""
        if not hasattr(self, '_current_customer_list') or not self._current_customer_list:
            MessageHandler.show_info(self, self.lm.get("Common.info", "Info"), self.lm.get("Customers.no_customers_to_export", "No customers to export"))
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            self.lm.get("Customers.export_pdf", "Save PDF"), 
            f"customers_report_{datetime.now().strftime('%Y%m%d')}.pdf", 
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
                    
                    /* Balance Colors */
                    .balance-debit {{ color: #E74C3C; font-weight: bold; }}
                    .balance-credit {{ color: #27AE60; font-weight: bold; }}
                    .balance-zero {{ color: #7F8C8D; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Customers.report_title", "CUSTOMERS REPORT")}</h1>
                <div class="meta">{self.lm.get("Common.generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            """
            
            # Calculate Summary
            total_customers = len(self._current_customer_list)
            total_owed = Decimal('0.00') # Customers owe us (positive)
            total_credit = Decimal('0.00') # We owe customers (negative)
            net_balance = Decimal('0.00')
            
            for customer in self._current_customer_list:
                balance_info = self._calculate_customer_balance(customer.id)
                balance = balance_info['balance']
                
                if balance > 0:
                    total_owed += balance
                elif balance < 0:
                    total_credit += abs(balance)
                    
                net_balance += balance
            
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Customers.total_customers", "Total Customers")}</div>
                        <div class="summary-value">{total_customers}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Customers.total_receivable", "Total Receivable")}</div>
                        <div class="summary-value" style="color: #E74C3C;">{self.cf.format(total_owed)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Customers.total_payable", "Total Payable")}</div>
                        <div class="summary-value" style="color: #27AE60;">{self.cf.format(total_credit)}</div>
                    </div>
                </div>
            """
            
            # Table Header
            html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Customers.customer_name", "Name")}</th>
                            <th>{self.lm.get("Customers.customer_phone", "Phone")}</th>
                            <th>{self.lm.get("Customers.customer_email", "Email")}</th>
                            <th>{self.lm.get("Customers.customer_address", "Address")}</th>
                            <th>{self.lm.get("Customers.device_count", "Devices")}</th>
                            <th>{self.lm.get("Customers.balance", "Balance")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Table Rows
            for customer in self._current_customer_list:
                balance_info = self._calculate_customer_balance(customer.id)
                balance = balance_info['balance']
                devices = self.customer_controller.get_customer_devices(customer.id)
                
                balance_class = "balance-zero"
                formatted_balance = self.cf.format(0)
                
                if balance > 0:
                    balance_class = "balance-debit"
                    formatted_balance = f"+{self.cf.format(balance)}"
                elif balance < 0:
                    balance_class = "balance-credit"
                    formatted_balance = f"-{self.cf.format(abs(balance))}"
                
                html += f"""
                    <tr>
                        <td>{customer.name or ""}</td>
                        <td>{phone_formatter.format_phone_number(customer.phone) if customer.phone else ""}</td>
                        <td>{customer.email or ""}</td>
                        <td>{customer.address or ""}</td>
                        <td>{len(devices)}</td>
                        <td class="{balance_class}">{formatted_balance}</td>
                    </tr>
                """
                
            html += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Generate PDF
            HTML(string=html).write_pdf(target=path, stylesheets=[CSS(string="")])
            
            MessageHandler.show_success(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Customers.export_success', 'Successfully exported')} {len(self._current_customer_list)} {self.lm.get('Customers.customers', 'customers')}."
            )
            
        except Exception as e:
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Customers.export_failed', 'Failed to export to PDF')}: {str(e)}"
            )
        
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

