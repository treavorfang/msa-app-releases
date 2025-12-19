# src/app/views/financial/purchase_order_list_tab.py
"""
Modern Purchase Order List Tab with enhanced UI features:
- Card/List view toggle
- Summary cards with key metrics
- Advanced filtering
- Status-based color coding
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QComboBox, QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor, QAction
from typing import List, Dict
from decimal import Decimal
from views.inventory.purchase_order_dialog import PurchaseOrderDialog
from views.inventory.purchase_return_dialog import PurchaseReturnDialog
from utils.print.purchase_order_generator import PurchaseOrderGenerator
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class PurchaseOrderListTab(QWidget):
    """Modern purchase order management interface"""
    
    data_changed = Signal()
    
    def __init__(self, container, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.user = user
        self.current_view = 'cards'
        self.selected_pos = []
        self.lm = language_manager
        self.cf = currency_formatter
        
        # Initialize PO generator
        self.po_generator = PurchaseOrderGenerator(
            parent=self,
            business_settings_service=container.business_settings_service if hasattr(container, 'business_settings_service') else None
        )
        
        self._setup_ui()
        self._connect_signals()
        # self._load_purchase_orders()
        self._data_loaded = False
    
    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Summary Cards
        summary_layout = self._create_summary_cards()
        layout.addLayout(summary_layout)
        
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
        title = QLabel(self.lm.get("Inventory.purchase_orders", "Purchase Orders"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Inventory.view", "View") + ":")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(self.lm.get("Common.cards", "📇 Cards"))
        self.list_view_btn = QPushButton(self.lm.get("Common.list", "📋 List"))
        
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
    
    def _create_summary_cards(self):
        """Create summary cards section"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Initialize summary cards
        self.total_pos_card = self._create_summary_card(self.lm.get("Inventory.total_orders", "Total Orders"), "0", "#3B82F6", "📦")
        self.pending_pos_card = self._create_summary_card(self.lm.get("Common.pending", "Pending"), "0", "#F59E0B", "⏳")
        self.received_pos_card = self._create_summary_card(self.lm.get("Common.received", "Received"), "0", "#10B981", "✅")
        self.total_value_card = self._create_summary_card(self.lm.get("Inventory.total_value", "Total Value"), self.cf.format(0), "#8B5CF6", "💰")
        
        layout.addWidget(self.total_pos_card)
        layout.addWidget(self.pending_pos_card)
        layout.addWidget(self.received_pos_card)
        layout.addWidget(self.total_value_card)
        layout.addStretch()
        
        return layout
    
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
    
    def _create_filters(self):
        """Create filter controls"""
        layout = QVBoxLayout()
        
        # First row - Search and status filter
        row1 = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_po_placeholder", "🔍 Search by PO number, supplier..."))
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
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([self.lm.get("Inventory.all_status", "All Status"), "draft", "sent", "received", "cancelled"])
        self.status_filter.setMinimumWidth(150)
        row1.addWidget(self.status_filter)
        
        row1.addStretch()
        
        layout.addLayout(row1)
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # New PO button
        self.new_btn = QPushButton("➕ " + self.lm.get("Inventory.new_purchase_order", "New Purchase Order"))
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
        
        # Return button
        self.return_btn = QPushButton("↩️ " + self.lm.get("Inventory.create_return", "Create Return"))
        layout.addWidget(self.return_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 " + self.lm.get("Inventory.refresh", "Refresh"))
        refresh_btn.clicked.connect(self._load_purchase_orders)
        layout.addWidget(refresh_btn)
        
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
            self.lm.get("Inventory.po_number", "PO Number"), 
            self.lm.get("Inventory.supplier", "Supplier"), 
            self.lm.get("Common.status", "Status"), 
            self.lm.get("Common.date", "Date"), 
            self.lm.get("Inventory.total_cost", "Total Amount"), 
            self.lm.get("Inventory.expected_delivery", "Expected Delivery")
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
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search)
        self.status_filter.currentTextChanged.connect(self._on_filter)
        
        # Actions
        self.new_btn.clicked.connect(self._on_new)
        self.return_btn.clicked.connect(self._on_create_return)
        
        # Table double click
        self.table.doubleClicked.connect(self._on_table_double_click)
        
        # Controller signals
        self.container.purchase_order_controller.po_created.connect(self._on_po_changed)
        self.container.purchase_order_controller.po_updated.connect(self._on_po_changed)
        self.container.purchase_order_controller.po_deleted.connect(self._on_po_changed)
        self.container.purchase_order_controller.status_changed.connect(self._on_po_changed)
    
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
        
        # Reload POs for the new view
        self._load_purchase_orders()
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status badge"""
        status_colors = {
            'draft': '#6B7280',      # Gray
            'sent': '#F59E0B',       # Orange
            'approved': '#3B82F6',   # Blue
            'received': '#10B981',   # Green
            'cancelled': '#EF4444'   # Red
        }
        return status_colors.get(status, '#6B7280')
    
    def _get_localized_status(self, status: str) -> str:
        """Get localized status text"""
        status_map = {
            'draft': 'Inventory.status_draft',
            'sent': 'Inventory.status_sent',
            'approved': 'Inventory.status_approved',
            'received': 'Common.received',
            'cancelled': 'Common.cancelled'
        }
        key = status_map.get(status.lower(), 'Common.unknown')
        return self.lm.get(key, status.capitalize())
    
    def _load_purchase_orders(self):
        """Load purchase orders with current filters"""
        # Use index instead of text to handle localization
        status_index = self.status_filter.currentIndex()
        if status_index == 0:  # "All Status" is always first
            status = None
        else:
            # Get the actual status value (draft, sent, received, cancelled)
            status = self.status_filter.itemText(status_index)
        
        pos = self.container.purchase_order_controller.list_purchase_orders(status=status)
        
        # Apply search filter
        search_term = self.search_input.text().strip()
        if search_term:
            search_lower = search_term.lower()
            pos = [
                po for po in pos
                if (search_lower in po.po_number.lower() or
                    search_lower in (po.supplier_name or '').lower())
            ]
        
        # Update summary
        self._update_summary(pos)
        
        # Update current view
        if self.current_view == 'cards':
            self._populate_cards_view(pos)
        elif self.current_view == 'list':
            self._populate_list_view(pos)
    
    def _update_summary(self, pos: List):
        """Update summary cards"""
        total = len(pos)
        pending = sum(1 for po in pos if po.status in ['draft', 'sent', 'approved'])
        received = sum(1 for po in pos if po.status == 'received')
        total_value = sum(Decimal(str(po.total_amount or 0)) for po in pos)
        
        self._update_card_value(self.total_pos_card, str(total))
        self._update_card_value(self.pending_pos_card, str(pending))
        self._update_card_value(self.received_pos_card, str(received))
        self._update_card_value(self.total_value_card, self.cf.format(total_value))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, pos: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add PO cards
        for idx, po in enumerate(pos):
            row = idx // 3
            col = idx % 3
            card = self._create_po_card(po)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_po_card(self, po):
        """Create a purchase order card widget"""
        card = QFrame()
        card.setObjectName("poCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        status_color = self._get_status_color(po.status)
        
        # Style card
        card.setStyleSheet(f"""
            QFrame#poCard {{
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#poCard:hover {{
                border-color: #3B82F6;
                background-color: #374151;
            }}
        """)
        
        # Store PO data
        card.po_id = po.id
        card.status_color = status_color
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, po)
                event.accept()
            elif event.button() == Qt.RightButton:
                self._show_context_menu(po)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
                
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(po)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - PO Number and status
        header = QHBoxLayout()
        
        po_label = QLabel(po.po_number)
        po_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(po_label)
        
        header.addStretch()
        
        status_badge = QLabel(self._get_localized_status(po.status).upper())
        status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(status_badge)
        
        layout.addLayout(header)
        
        # Supplier
        if po.supplier_name:
            supplier_label = QLabel(f"🏢 {po.supplier_name}")
            supplier_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
            layout.addWidget(supplier_label)
        
        # Date info
        date_label = QLabel(f"📅 {po.order_date.strftime('%Y-%m-%d')}")
        date_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(date_label)
        
        if po.expected_delivery:
            delivery_label = QLabel(f"🚚 Expected: {po.expected_delivery.strftime('%Y-%m-%d')}")
            delivery_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(delivery_label)
        
        layout.addStretch()
        
        # Footer - Amount
        amount_label = QLabel(self.cf.format(po.total_amount))
        amount_label.setStyleSheet("color: #3B82F6; font-size: 18px; font-weight: bold;")
        layout.addWidget(amount_label)
        
        # Initial style
        self._update_card_selection_style(card, po.id in self.selected_pos)
        
        return card
    
    def _populate_list_view(self, pos: List):
        """Populate list view"""
        self.table.setRowCount(len(pos))
        
        for row, po in enumerate(pos):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, checkbox_item)
            
            # PO Number
            po_item = QTableWidgetItem(po.po_number)
            po_item.setData(Qt.UserRole, po.id)
            self.table.setItem(row, 1, po_item)
            
            # Supplier
            self.table.setItem(row, 2, QTableWidgetItem(po.supplier_name or self.lm.get("Common.not_applicable", "N/A")))
            
            # Status
            status_text = self._get_localized_status(po.status)
            status_item = QTableWidgetItem(status_text.upper())
            status_item.setForeground(QColor(self._get_status_color(po.status)))
            self.table.setItem(row, 3, status_item)
            
            # Date
            self.table.setItem(row, 4, QTableWidgetItem(str(po.order_date.date())))
            
            # Total Amount
            self.table.setItem(row, 5, QTableWidgetItem(self.cf.format(po.total_amount)))
            
            # Expected Delivery
            self.table.setItem(row, 6, QTableWidgetItem(
                str(po.expected_delivery.date()) if po.expected_delivery else self.lm.get("Common.not_applicable", "N/A")
            ))
    
    def _on_search(self, text):
        """Handle search"""
        QTimer.singleShot(300, self._load_purchase_orders)
    
    def _on_filter(self):
        """Handle status filter change"""
        self._load_purchase_orders()
    
    def _on_new(self):
        """Create new purchase order"""
        dialog = PurchaseOrderDialog(self.container, parent=self)
        dialog.exec()
    
    def _on_card_clicked(self, card, po):
        """Handle card click (toggle selection)"""
        if po.id in self.selected_pos:
            self.selected_pos.remove(po.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_pos.append(po.id)
            self._update_card_selection_style(card, True)
            
    def _on_card_double_clicked(self, po):
        """Handle card double click (open details)"""
        dialog = PurchaseOrderDialog(self.container, po, parent=self)
        dialog.exec()
            
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        status_color = getattr(card, 'status_color', '#3B82F6')
        
        if is_selected:
            card.setStyleSheet("""
                QFrame#poCard {
                    background-color: #374151;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        else:
            card.setStyleSheet(f"""
                QFrame#poCard {{
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 12px;
                }}
                QFrame#poCard:hover {{
                    border-color: #3B82F6;
                    background-color: #374151;
                }}
            """)

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_pos.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
    
    def _on_table_double_click(self, index):
        """Handle table double click"""
        po_id = self.table.item(index.row(), 1).data(Qt.UserRole)
        po = self.container.purchase_order_controller.get_purchase_order(po_id)
        if po:
            dialog = PurchaseOrderDialog(self.container, po, parent=self)
            dialog.exec()
    
    def _on_create_return(self):
        """Create return for selected PO"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.lm.get("Common.no_selection", "No Selection"), self.lm.get("Inventory.select_po_for_return", "Please select a Purchase Order to create a return."))
            return
        
        row = selected_rows[0].row()
        po_id = self.table.item(row, 1).data(Qt.UserRole)
        po = self.container.purchase_order_controller.get_purchase_order(po_id)
        
        if not po:
            return
        
        # Only allow returns for received POs
        if po.status != 'received':
            QMessageBox.warning(self, self.lm.get("Inventory.invalid_status", "Invalid Status"), self.lm.get("Inventory.only_received_returns", "You can only create returns for 'received' Purchase Orders."))
            return
        
        dialog = PurchaseReturnDialog(self.container, po, user=self.user, parent=self)
        dialog.exec()
    
    def _on_po_changed(self):
        """Handle PO data changes"""
        self._load_purchase_orders()
        self.data_changed.emit()  # Notify parent to refresh other tabs
    
    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        table = self.sender()
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        po_id = table.item(row, 1).data(Qt.UserRole)
        if po_id:
            po = self.container.purchase_order_controller.get_purchase_order(po_id)
            if po:
                self._show_context_menu(po)
    
    def _show_context_menu(self, po):
        """Show context menu for purchase order"""
        menu = QMenu(self)
        
        # View/Edit PO
        view_action = QAction(self.lm.get("Inventory.view_edit_po", "📄 View/Edit PO"), self)
        view_action.triggered.connect(lambda: self._open_po_dialog(po))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        # Mark as Received (only for sent/approved POs)
        if po.status in ['sent', 'approved']:
            receive_action = QAction(self.lm.get("Inventory.mark_as_received", "✅ Mark as Received"), self)
            receive_action.triggered.connect(lambda: self._mark_as_received(po))
            menu.addAction(receive_action)
        
        # Create Return (only for received POs)
        if po.status == 'received':
            return_action = QAction(self.lm.get("Inventory.create_return_action", "↩️ Create Return"), self)
            return_action.triggered.connect(lambda: self._create_return_for_po(po))
            menu.addAction(return_action)
        
        # Cancel PO (only for draft/sent POs)
        if po.status in ['draft', 'sent']:
            menu.addSeparator()
            cancel_action = QAction(self.lm.get("Inventory.cancel_po", "❌ Cancel PO"), self)
            cancel_action.triggered.connect(lambda: self._cancel_po(po))
            menu.addAction(cancel_action)
        
        # Always available actions
        menu.addSeparator()
        
        # Preview PO
        preview_action = QAction(self.lm.get("Inventory.preview_po", "👁️ Preview PO"), self)
        preview_action.triggered.connect(lambda: self._preview_po(po))
        menu.addAction(preview_action)
        
        # Print PO
        print_action = QAction(self.lm.get("Inventory.print_po", "🖨️ Print PO"), self)
        print_action.triggered.connect(lambda: self._print_po(po))
        menu.addAction(print_action)
        
        menu.exec(self.cursor().pos())
    
    def _open_po_dialog(self, po):
        """Open purchase order dialog"""
        dialog = PurchaseOrderDialog(self.container, po, parent=self)
        dialog.exec()
    
    def _mark_as_received(self, po):
        """Mark purchase order as received"""
        if QMessageBox.question(
            self,
            self.lm.get("Inventory.confirm_receive", "Confirm Receive"),
            self.lm.get("Inventory.mark_po_received_question", "Mark Purchase Order '{po_number}' as received?").format(po_number=po.po_number),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.container.purchase_order_controller.update_status(po.id, 'received'):
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Inventory.po_marked_received", "Purchase Order marked as received"))
                self._load_purchase_orders()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.failed_update_status", "Failed to update status"))
    
    def _create_return_for_po(self, po):
        """Create return for purchase order"""
        dialog = PurchaseReturnDialog(self.container, po, user=self.user, parent=self)
        dialog.exec()
    
    def _cancel_po(self, po):
        """Cancel purchase order"""
        if QMessageBox.question(
            self,
            self.lm.get("Inventory.confirm_cancel", "Confirm Cancel"),
            self.lm.get("Inventory.cancel_po_question", "Are you sure you want to cancel Purchase Order '{po_number}'?").format(po_number=po.po_number),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.container.purchase_order_controller.update_status(po.id, 'cancelled'):
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Inventory.po_cancelled", "Purchase Order cancelled"))
                self._load_purchase_orders()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.failed_cancel_po", "Failed to cancel purchase order"))
    
    def _prepare_po_data(self, po):
        """Prepare PO data for PDF generation"""
        items = []
        # Use items from DTO
        if hasattr(po, 'items') and po.items:
            for item in po.items:
                items.append({
                    'part_name': item.part_name or 'N/A',
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_cost),
                    'total': float(item.quantity * item.unit_cost)
                })
        
        return {
            'po_number': po.po_number,
            'order_date': po.order_date.strftime('%Y-%m-%d') if po.order_date else 'N/A',
            'expected_delivery': po.expected_delivery.strftime('%Y-%m-%d') if po.expected_delivery else 'N/A',
            'status': po.status,
            'supplier_name': po.supplier_name or 'N/A',
            'supplier_contact': po.supplier_contact or 'N/A',
            'supplier_phone': po.supplier_phone or 'N/A',
            'items': items,
            'total_amount': float(po.total_amount),
            'notes': po.notes if hasattr(po, 'notes') else ''
        }
    
    def _preview_po(self, po):
        """Preview purchase order PDF"""
        try:
            po_data = self._prepare_po_data(po)
            self.po_generator.preview_pdf(po_data)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to preview PO: {str(e)}")
    
    def _print_po(self, po):
        """Print purchase order PDF"""
        try:
            po_data = self._prepare_po_data(po)
            if self.po_generator.print_pdf(po_data):
                QMessageBox.information(self, "Success", "Purchase Order sent to printer")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to print PO: {str(e)}")

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_purchase_orders)
            self._data_loaded = True
