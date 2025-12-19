from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QFrame, QMessageBox, QComboBox, QCheckBox, QScrollArea,
    QGridLayout, QStackedWidget, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QAction
from typing import List, Dict
from decimal import Decimal
from views.inventory.supplier_dialog import SupplierDialog
from views.inventory.supplier_details_dialog import SupplierDetailsDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class ModernSupplierListTab(QWidget):
    """Modern supplier list tab with card/list view and balance tracking"""
    
    supplier_selected = Signal(object)
    
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.current_view = 'cards'
        self.selected_suppliers = []
        self._supplier_balances = {}  # Cache for supplier balances
        self.lm = language_manager
        
        # Search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._setup_ui()
        self._connect_signals()
        # self._load_data()
        self._data_loaded = False
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Summary Cards
        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(12)
        layout.addLayout(self.summary_layout)
        
        # Initialize summary cards
        self.total_suppliers_card = self._create_summary_card(self.lm.get("Inventory.suppliers", "Total Suppliers"), "0", "#3B82F6", "🏢")
        self.active_suppliers_card = self._create_summary_card(self.lm.get("Inventory.active_suppliers", "Active Suppliers"), "0", "#10B981", "✅")
        self.total_owed_card = self._create_summary_card(self.lm.get("Inventory.total_owed", "Total Owed"), currency_formatter.format(0), "#EF4444", "💰")
        
        self.summary_layout.addWidget(self.total_suppliers_card)
        self.summary_layout.addWidget(self.active_suppliers_card)
        self.summary_layout.addWidget(self.total_owed_card)
        self.summary_layout.addStretch()
        
        # Filters and search
        filter_layout = self._create_filters()
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
        title = QLabel(self.lm.get("Inventory.suppliers", "Suppliers"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(f"{self.lm.get('Common.view', 'View')}:")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Invoices.view_cards', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Invoices.view_list', 'List')}")
        
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
    
    def _create_filters(self):
        """Create filter controls"""
        layout = QVBoxLayout()
        
        # First row - Search and balance filter
        row1 = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_suppliers", "🔍 Search by name, contact, email, phone..."))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #374151;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        row1.addWidget(self.search_input)
        
        # Balance filter
        self.balance_filter = QComboBox()
        self.balance_filter.addItems([
            self.lm.get("Inventory.all_balances", "All Balances"),
            self.lm.get("Inventory.has_debit", "Has Debit (We Owe)"),
            self.lm.get("Inventory.has_credit", "Has Credit"),
            self.lm.get("Inventory.zero_balance", "Zero Balance")
        ])
        self.balance_filter.setMinimumWidth(150)
        row1.addWidget(self.balance_filter)
        
        row1.addStretch()
        
        layout.addLayout(row1)
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # New supplier button
        self.new_btn = QPushButton(f"➕ {self.lm.get('Inventory.new_supplier', 'New Supplier')}")
        self.new_btn.setStyleSheet("""
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
        layout.addWidget(self.new_btn)
        
        layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        layout.addWidget(self.refresh_btn)
        
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
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        headers = [
            "✓",
            self.lm.get("Inventory.supplier_name", "Name"),
            self.lm.get("Inventory.contact_person", "Contact Person"),
            self.lm.get("Inventory.supplier_email", "Email"),
            self.lm.get("Inventory.supplier_phone", "Phone"),
            self.lm.get("Inventory.payment_terms", "Payment Terms"),
            self.lm.get("Inventory.balance_owed", "Balance")
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(0, 40)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        
        # Table Styling
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #374151;
            }
            QHeaderView::section {
                padding: 8px;
                border: none;
                border-bottom: 2px solid #374151;
                font-weight: bold;
            }
        """)
        
        return self.table
    
    def _create_summary_card(self, title, value, color, icon):
        """Create a styled summary card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
            }}
        """)
        card.setFixedHeight(80)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 24px;
            background-color: transparent;
            border-radius: 8px;
            padding: 8px;
        """)
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px; font-weight: 500;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return card
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search_changed)
        self.balance_filter.currentTextChanged.connect(self._on_filter_changed)
        
        # Actions
        self.new_btn.clicked.connect(self._on_new)
        self.refresh_btn.clicked.connect(lambda: self._load_data())
        
        # Table double click
        self.table.doubleClicked.connect(self._on_table_double_click)
    
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
        
        # Reload suppliers for the new view
        self._load_data()
    
    def _on_filter_changed(self, *args):
        """Handle filter changes"""
        QTimer.singleShot(300, self._load_data)
    
    def _calculate_supplier_balance(self, supplier_id: int) -> Dict:
        """Calculate supplier's financial balance from supplier invoices"""
        # Check cache first
        if supplier_id in self._supplier_balances:
            return self._supplier_balances[supplier_id]
        
        balance_info = {
            'total_orders': 0,
            'total_owed': Decimal('0.00'),
            'total_paid': Decimal('0.00'),
            'balance': Decimal('0.00')
        }
        
        try:
            # Get supplier invoices to calculate actual outstanding balance
            if hasattr(self.container, 'supplier_invoice_service'):
                invoices = self.container.supplier_invoice_service.get_invoices_by_supplier(supplier_id)
                
                total_invoice_amount = Decimal('0.00')
                total_paid_amount = Decimal('0.00')
                
                for invoice in invoices:
                    total_invoice_amount += Decimal(str(invoice.total_amount))
                    total_paid_amount += Decimal(str(invoice.paid_amount))
                
                outstanding = total_invoice_amount - total_paid_amount
                
                balance_info = {
                    'total_orders': len(invoices),
                    'total_owed': outstanding,  # What we owe the supplier
                    'total_paid': total_paid_amount,
                    'balance': outstanding  # Positive = we owe them
                }
        except Exception as e:
            print(f"Error calculating balance for supplier {supplier_id}: {e}")
        
        # Cache the result
        self._supplier_balances[supplier_id] = balance_info
        return balance_info
    
    def _get_balance_color(self, balance: Decimal) -> str:
        """Get color for balance display"""
        if balance > 0:
            return '#EF4444'  # Red - we owe supplier
        elif balance < 0:
            return '#10B981'  # Green - supplier owes us (credit)
        else:
            return '#6B7280'  # Gray - zero balance
    
    def _format_balance(self, balance: Decimal) -> str:
        """Format balance for display"""
        if balance > 0:
            return f"+{currency_formatter.format(balance)}"
        elif balance < 0:
            return f"-{currency_formatter.format(abs(balance))}"
        else:
            return currency_formatter.format(0)
    
    def _load_data(self, suppliers=None):
        """Load suppliers with current filters"""
        # Clear balance cache
        self._supplier_balances = {}
        
        if suppliers is None:
            suppliers = self.container.supplier_controller.list_suppliers()
        
        # Apply search filter
        search_term = self.search_input.text().strip()
        if search_term:
            search_lower = search_term.lower()
            suppliers = [
                s for s in suppliers
                if (search_lower in (s.name or '').lower() or
                    search_lower in (s.contact_person or '').lower() or
                    search_lower in (s.email or '').lower() or
                    search_lower in (s.phone or '').lower())
            ]
        
        # Apply balance filter
        balance_filter = self.balance_filter.currentText()
        if balance_filter != self.lm.get("Inventory.all_balances", "All Balances"):
            filtered = []
            for s in suppliers:
                balance_info = self._calculate_supplier_balance(s.id)
                balance = balance_info['balance']
                
                if balance_filter == self.lm.get("Inventory.has_debit", "Has Debit (We Owe)") and balance > 0:
                    filtered.append(s)
                elif balance_filter == self.lm.get("Inventory.has_credit", "Has Credit") and balance < 0:
                    filtered.append(s)
                elif balance_filter == self.lm.get("Inventory.zero_balance", "Zero Balance") and balance == 0:
                    filtered.append(s)
            suppliers = filtered
        
        # Update summary
        self._update_summary(suppliers)
        
        # Update current view
        if self.current_view == 'cards':
            self._populate_cards_view(suppliers)
        elif self.current_view == 'list':
            self._populate_list_view(suppliers)
    
    def _update_summary(self, suppliers):
        """Update summary cards"""
        total = len(suppliers)
        active = len(suppliers)  # Assuming all listed are active
        
        # Calculate total owed
        total_owed = Decimal('0.00')
        for supplier in suppliers:
            balance_info = self._calculate_supplier_balance(supplier.id)
            if balance_info['balance'] > 0:
                total_owed += balance_info['balance']
        
        self._update_card_value(self.total_suppliers_card, str(total))
        self._update_card_value(self.active_suppliers_card, str(active))
        self._update_card_value(self.total_owed_card, currency_formatter.format(total_owed))

    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, suppliers: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add supplier cards
        for idx, supplier in enumerate(suppliers):
            row = idx // 3
            col = idx % 3
            card = self._create_supplier_card(supplier)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_supplier_card(self, supplier):
        """Create a supplier card widget"""
        card = QFrame()
        card.setObjectName("supplierCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        # Calculate balance
        balance_info = self._calculate_supplier_balance(supplier.id)
        balance = balance_info['balance']
        balance_color = self._get_balance_color(balance)
        
        # Store supplier data
        card.supplier_id = supplier.id
        card.supplier_dto = supplier
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, supplier)
                event.accept()
            elif event.button() == Qt.RightButton:
                self._show_context_menu(supplier)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(supplier)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Name and balance
        header = QHBoxLayout()
        
        name_label = QLabel(supplier.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(name_label)
        
        header.addStretch()
        
        balance_label = QLabel(self._format_balance(balance))
        balance_label.setStyleSheet(f"color: {balance_color}; font-weight: bold; font-size: 14px;")
        header.addWidget(balance_label)
        
        layout.addLayout(header)
        
        # Contact info
        if supplier.contact_person:
            contact_label = QLabel(f"👤 {supplier.contact_person}")
            contact_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(contact_label)
        
        if supplier.phone:
            phone_label = QLabel(f"📞 {supplier.phone}")
            phone_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(phone_label)
        
        if supplier.email:
            email_label = QLabel(f"📧 {supplier.email}")
            email_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(email_label)
        
        layout.addStretch()
        
        # Footer - Stats
        footer = QHBoxLayout()
        
        orders_label = QLabel(f"📦 {balance_info['total_orders']} {self.lm.get('Inventory.orders', 'Orders')}")
        orders_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        footer.addWidget(orders_label)
        
        footer.addStretch()
        
        if supplier.payment_terms:
            terms_label = QLabel(f"💳 {supplier.payment_terms}")
            terms_label.setStyleSheet("color: #6B7280; font-size: 11px;")
            footer.addWidget(terms_label)
        
        layout.addLayout(footer)
        
        # Initial style
        self._update_card_selection_style(card, supplier.id in self.selected_suppliers)
        
        return card
    
    def _populate_list_view(self, suppliers: List):
        """Populate list view"""
        self.table.setRowCount(len(suppliers))
        
        for row, supplier in enumerate(suppliers):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, checkbox_item)
            
            # Name
            name_item = QTableWidgetItem(supplier.name)
            name_item.setData(Qt.UserRole, supplier.id)
            self.table.setItem(row, 1, name_item)
            
            # Contact Person
            self.table.setItem(row, 2, QTableWidgetItem(supplier.contact_person or ""))
            
            # Email
            self.table.setItem(row, 3, QTableWidgetItem(supplier.email or ""))
            
            # Phone
            self.table.setItem(row, 4, QTableWidgetItem(supplier.phone or ""))
            
            # Payment Terms
            self.table.setItem(row, 5, QTableWidgetItem(supplier.payment_terms or ""))
            
            # Balance
            balance_info = self._calculate_supplier_balance(supplier.id)
            balance = balance_info['balance']
            balance_item = QTableWidgetItem(self._format_balance(balance))
            balance_item.setForeground(QColor(self._get_balance_color(balance)))
            self.table.setItem(row, 6, balance_item)

    def _on_search_changed(self, text):
        self.search_timer.start()

    def _perform_search(self):
        self._load_data()

    def _on_new(self):
        dialog = SupplierDialog(self.container, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _on_card_clicked(self, card, supplier):
        """Handle card click (toggle selection)"""
        if supplier.id in self.selected_suppliers:
            self.selected_suppliers.remove(supplier.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_suppliers.append(supplier.id)
            self._update_card_selection_style(card, True)
            
    def _on_card_double_clicked(self, supplier):
        """Handle card double click (open details)"""
        dialog = SupplierDetailsDialog(self.container, supplier, parent=self)
        dialog.exec()
        self._load_data()  # Refresh after dialog closes
        
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        if is_selected:
            card.setStyleSheet("""
                QFrame#supplierCard {
                    background-color: #374151;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#supplierCard {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame#supplierCard:hover {
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
        self.selected_suppliers.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
    
    def _on_table_double_click(self, index):
        """Handle table double click"""
        supplier_id = self.table.item(index.row(), 1).data(Qt.UserRole)
        supplier = self.container.supplier_controller.get_supplier(supplier_id)
        if supplier:
            dialog = SupplierDetailsDialog(self.container, supplier, parent=self)
            dialog.exec()
            self._load_data()  # Refresh after dialog closes
    
    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        table = self.sender()
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        supplier_id = table.item(row, 1).data(Qt.UserRole)
        if supplier_id:
            supplier = self.container.supplier_controller.get_supplier(supplier_id)
            if supplier:
                self._show_context_menu(supplier)
    
    def _show_context_menu(self, supplier):
        """Show context menu for supplier"""
        menu = QMenu(self)
        
        # View Details
        view_action = QAction(f"📄 {self.lm.get('Inventory.view_details', 'View Details')}", self)
        view_action.triggered.connect(lambda: self._open_supplier_details(supplier))
        menu.addAction(view_action)
        
        # Edit Supplier
        edit_action = QAction(f"✏️ {self.lm.get('Inventory.edit_supplier', 'Edit Supplier')}", self)
        edit_action.triggered.connect(lambda: self._edit_supplier(supplier))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        # Delete Supplier
        delete_action = QAction(f"🗑️ {self.lm.get('Inventory.delete_supplier', 'Delete Supplier')}", self)
        delete_action.triggered.connect(lambda: self._delete_supplier(supplier))
        menu.addAction(delete_action)
        
        menu.exec(self.cursor().pos())
    
    def _open_supplier_details(self, supplier):
        """Open supplier details dialog"""
        dialog = SupplierDetailsDialog(self.container, supplier, parent=self)
        dialog.exec()
        self._load_data()
    
    def _edit_supplier(self, supplier):
        """Open edit supplier dialog"""
        dialog = SupplierDialog(self.container, supplier=supplier, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _delete_supplier(self, supplier):
        """Delete a supplier"""
        if QMessageBox.question(
            self,
            self.lm.get("Common.confirm", "Confirm"),
            f"{self.lm.get('Inventory.confirm_delete_supplier', 'Are you sure you want to delete supplier')} '{supplier.name}'?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.container.supplier_controller.delete_supplier(supplier.id):
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Inventory.supplier_deleted", "Supplier deleted successfully"))
                self._load_data()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.supplier_delete_failed", "Failed to delete supplier"))

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_data)
            self._data_loaded = True
