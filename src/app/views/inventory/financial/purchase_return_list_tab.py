# src/app/views/financial/purchase_return_list_tab.py
"""
Modern Purchase Return List Tab with enhanced UI features:
- Card/List view toggle
- Summary cards with key metrics
- Status-based color coding
- Advanced filtering
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor
from typing import List
from decimal import Decimal
from views.inventory.purchase_return_dialog import PurchaseReturnDialog
from views.inventory.purchase_return_details_dialog import PurchaseReturnDetailsDialog
from config.constants import PurchaseReturnStatus, UIColors
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class PurchaseReturnListTab(QWidget):
    """Modern purchase return management interface"""
    
    data_changed = Signal()
    
    def __init__(self, container, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.user = user
        self.return_controller = container.purchase_return_controller
        self.current_view = 'cards'
        self.lm = language_manager
        self.cf = currency_formatter
        
        self._setup_ui()
        self._connect_signals()
        # self._load_returns()
        self._data_loaded = False
    
    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)

        # Theme handling
        self.current_theme = 'dark'
        if hasattr(self.container, 'theme_controller'):
             self.container.theme_controller.theme_changed.connect(self._on_theme_changed)
             self.current_theme = self.container.theme_controller.current_theme
        
        # Summary Cards
        summary_layout = self._create_summary_cards()
        layout.addLayout(summary_layout)
        
        # Filters
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

        # Apply initial theme
        self._on_theme_changed(self.current_theme)
    
    def _create_header(self):
        """Create header with title and view switcher"""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("Returns.returns_title", "Purchase Returns"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Returns.view", "View") + ":")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Returns.cards_view', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Returns.list_view', 'List')}")
        
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
        self.total_returns_card = self._create_summary_card(self.lm.get("Returns.total_returns", "Total Returns"), "0", "#3B82F6", "↩️")
        self.draft_returns_card = self._create_summary_card(self.lm.get("Returns.draft", "Draft"), "0", "#6B7280", "📝")
        self.approved_returns_card = self._create_summary_card(self.lm.get("Returns.approved", "Approved"), "0", "#10B981", "✅")
        self.total_value_card = self._create_summary_card(self.lm.get("Returns.total_value", "Total Value"), self.cf.format(0), "#EF4444", "💰")
        
        layout.addWidget(self.total_returns_card)
        layout.addWidget(self.draft_returns_card)
        layout.addWidget(self.approved_returns_card)
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
        layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Returns.search_placeholder", "🔍 Search by return #, PO #, supplier..."))
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
        layout.addWidget(self.search_input)
        
        # Status filter
        layout.addWidget(QLabel(self.lm.get("Returns.status", "Status") + ":"))
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("Returns.all", "All"), None)
        self.status_filter.addItem(self.lm.get("Returns.draft", "Draft"), PurchaseReturnStatus.DRAFT)
        self.status_filter.addItem(self.lm.get("Returns.approved", "Approved"), PurchaseReturnStatus.APPROVED)
        self.status_filter.addItem(self.lm.get("Returns.completed", "Completed"), PurchaseReturnStatus.COMPLETED)
        self.status_filter.setMinimumWidth(150)
        layout.addWidget(self.status_filter)
        
        layout.addStretch()
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Approve button
        self.approve_btn = QPushButton(self.lm.get("Returns.approve_selected", "✓ Approve Selected"))
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        layout.addWidget(self.approve_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Returns.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_returns)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def _create_cards_view(self):
        """Create card/grid view"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.cards_layout = QGridLayout(container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(container)
        return scroll
    
    def _create_list_view(self):
        """Create traditional list/table view"""
        self.returns_table = QTableWidget()
        self.returns_table.setColumnCount(8)
        headers = [
            "✓",
            self.lm.get("Returns.return_number", "Return #"),
            self.lm.get("Returns.po_number", "PO #"),
            self.lm.get("Returns.supplier", "Supplier"),
            self.lm.get("Returns.date", "Date"),
            self.lm.get("Returns.reason", "Reason"),
            self.lm.get("Returns.amount", "Amount"),
            self.lm.get("Returns.status_header", "Status")
        ]
        self.returns_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.returns_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.returns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.returns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.returns_table.setAlternatingRowColors(True)
        self.returns_table.setColumnWidth(0, 40)
        self.returns_table.verticalHeader().setVisible(False)
        self.returns_table.setShowGrid(False)
        
        # Table Styling
        self.returns_table.setStyleSheet("""
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
        
        return self.returns_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search)
        self.status_filter.currentIndexChanged.connect(self._on_filter)
        
        # Actions
        self.approve_btn.clicked.connect(self._on_approve)
        
        # Table double click
        self.returns_table.doubleClicked.connect(self._on_table_double_click)
        
        # Controller signals
        self.return_controller.return_created.connect(self._load_returns)
        self.return_controller.return_updated.connect(self._load_returns)
        self.return_controller.return_approved.connect(self._load_returns)
    
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
        
        # Reload returns for the new view
        self._load_returns()
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status badge"""
        status_colors = {
            PurchaseReturnStatus.DRAFT: '#6B7280',      # Gray
            PurchaseReturnStatus.APPROVED: '#10B981',   # Green
            PurchaseReturnStatus.COMPLETED: '#3B82F6'   # Blue
        }
        return status_colors.get(status, '#6B7280')
    
    def _load_returns(self):
        """Load and display returns"""
        try:
            status_filter = self.status_filter.currentData()
            returns = self.return_controller.list_returns(status=status_filter)
            
            # Apply search filter
            search_term = self.search_input.text().strip()
            if search_term:
                search_lower = search_term.lower()
                returns = [
                    r for r in returns
                    if (search_lower in r.return_number.lower() or
                        search_lower in (r.purchase_order.po_number if r.purchase_order else '').lower() or
                        search_lower in (r.purchase_order.supplier.name if r.purchase_order and r.purchase_order.supplier else '').lower())
                ]
            
            # Update summary
            self._update_summary(returns)
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(returns)
            elif self.current_view == 'list':
                self._populate_list_view(returns)
        
        except Exception as e:
            print(f"Error loading returns: {e}")
    
    def _update_summary(self, returns: List):
        """Update summary cards"""
        total = len(returns)
        draft = sum(1 for r in returns if r.status == PurchaseReturnStatus.DRAFT)
        approved = sum(1 for r in returns if r.status == PurchaseReturnStatus.APPROVED)
        total_value = sum(Decimal(str(r.total_amount or 0)) for r in returns)
        
        self._update_card_value(self.total_returns_card, str(total))
        self._update_card_value(self.draft_returns_card, str(draft))
        self._update_card_value(self.approved_returns_card, str(approved))
        self._update_card_value(self.total_value_card, self.cf.format(total_value))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, returns: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add return cards
        for idx, return_obj in enumerate(returns):
            row = idx // 3
            col = idx % 3
            card = self._create_return_card(return_obj)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_return_card(self, return_obj):
        """Create a return card widget"""
        card = QFrame()
        card.setObjectName("returnCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        status_color = self._get_status_color(return_obj.status)
        card.status_color = status_color
        
        # Store return data
        card.return_id = return_obj.id
        card.mousePressEvent = lambda event: self._on_card_clicked(return_obj)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Return # and status
        header = QHBoxLayout()
        
        return_label = QLabel(return_obj.return_number)
        return_label.setObjectName("returnLabel")
        return_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(return_label)
        
        header.addStretch()
        
        status_badge = QLabel(return_obj.status.upper())
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
        
        # PO and Supplier
        if return_obj.purchase_order:
            po_label = QLabel(f"📦 {self.lm.get('Returns.po', 'PO')}: {return_obj.purchase_order.po_number}")
            po_label.setObjectName("metaLabel")
            po_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(po_label)
            
            if return_obj.purchase_order.supplier:
                supplier_label = QLabel(f"🏢 {return_obj.purchase_order.supplier.name}")
                supplier_label.setObjectName("metaLabel")
                supplier_label.setStyleSheet("font-size: 12px;")
                layout.addWidget(supplier_label)
        
        # Date
        return_date = return_obj.return_date.strftime("%Y-%m-%d") if return_obj.return_date else "N/A"
        date_label = QLabel(f"📅 {return_date}")
        date_label.setObjectName("metaLabel")
        date_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(date_label)
        
        # Reason (truncated)
        reason = return_obj.reason[:40] + "..." if len(return_obj.reason) > 40 else return_obj.reason
        reason_label = QLabel(f"💬 {reason}")
        reason_label.setObjectName("metaLabel")
        reason_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(reason_label)
        
        layout.addStretch()
        
        # Footer - Amount
        amount_label = QLabel(self.cf.format(return_obj.total_amount))
        amount_label.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: bold;")
        layout.addWidget(amount_label)
        
        # Initial style
        self._update_card_style(card)
        
        return card
    
    def _populate_list_view(self, returns: List):
        """Populate list view"""
        self.returns_table.setRowCount(len(returns))
        
        for row, return_obj in enumerate(returns):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.returns_table.setItem(row, 0, checkbox_item)
            
            # Return number
            return_item = QTableWidgetItem(return_obj.return_number)
            return_item.setData(Qt.UserRole, return_obj.id)
            self.returns_table.setItem(row, 1, return_item)
            
            # PO number
            po_number = return_obj.purchase_order.po_number if return_obj.purchase_order else "N/A"
            self.returns_table.setItem(row, 2, QTableWidgetItem(po_number))
            
            # Supplier
            supplier_name = "N/A"
            if return_obj.purchase_order and return_obj.purchase_order.supplier:
                supplier_name = return_obj.purchase_order.supplier.name
            self.returns_table.setItem(row, 3, QTableWidgetItem(supplier_name))
            
            # Date
            return_date = return_obj.return_date.strftime("%Y-%m-%d") if return_obj.return_date else "N/A"
            self.returns_table.setItem(row, 4, QTableWidgetItem(return_date))
            
            # Reason (truncated)
            reason = return_obj.reason[:50] + "..." if len(return_obj.reason) > 50 else return_obj.reason
            self.returns_table.setItem(row, 5, QTableWidgetItem(reason))
            
            # Amount
            self.returns_table.setItem(row, 6, QTableWidgetItem(self.cf.format(float(return_obj.total_amount))))
            
            # Status
            status_item = QTableWidgetItem(return_obj.status.upper())
            status_item.setForeground(QColor(self._get_status_color(return_obj.status)))
            self.returns_table.setItem(row, 7, status_item)
    
    def _on_search(self, text):
        """Handle search"""
        QTimer.singleShot(300, self._load_returns)
    
    def _on_filter(self):
        """Handle filter change"""
        self._load_returns()
    
    def _on_card_clicked(self, return_obj):
        """Handle card click"""
        dialog = PurchaseReturnDetailsDialog(self.container, return_obj, parent=self)
        dialog.exec()
        self._load_returns()
    
    def _on_table_double_click(self, index):
        """Handle table double click"""
        return_id = self.returns_table.item(index.row(), 1).data(Qt.UserRole)
        purchase_return = self.return_controller.get_return(return_id)
        if purchase_return:
            dialog = PurchaseReturnDetailsDialog(self.container, purchase_return, parent=self)
            dialog.exec()
            self._load_returns()
    
    def _on_approve(self):
        """Approve selected return"""
        selected_rows = self.returns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.lm.get("Returns.no_selection", "No Selection"), self.lm.get("Returns.select_return_to_approve", "Please select a return to approve."))
            return
        
        row = selected_rows[0].row()
        return_id = self.returns_table.item(row, 1).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.lm.get("Returns.confirm_approval", "Confirm Approval"),
            self.lm.get("Returns.approval_message", "Are you sure you want to approve this return? This will:\n- Reduce inventory stock\n- Generate a credit note\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.return_controller.approve_return(return_id, current_user=self.user)
            if result:
                QMessageBox.information(self, self.lm.get("Returns.success", "Success"), self.lm.get("Returns.return_approved", "Return approved and credit note generated!"))
                self._load_returns()
            else:
                QMessageBox.warning(self, self.lm.get("Returns.error", "Error"), self.lm.get("Returns.failed_to_approve", "Failed to approve return."))
    def _update_card_style(self, card):
        """Update card style based on theme"""
        status_color = getattr(card, 'status_color', '#3B82F6')
        is_dark = self.current_theme == 'dark'
        
        if is_dark:
            bg_color = "#1F2937"
            border_color = "#374151"
            hover_bg = "#374151"
            hover_border = status_color
            text_color = "white"
            meta_color = "#9CA3AF" # Gray 400
        else: # Light
            bg_color = "#FFFFFF"
            border_color = "#E5E7EB"
            hover_bg = "#F9FAFB" # Gray 50
            hover_border = status_color
            text_color = "#111827" # Gray 900
            meta_color = "#4B5563" # Gray 600

        card.setStyleSheet(f"""
            QFrame#returnCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#returnCard:hover {{
                border-color: {hover_border};
                background-color: {hover_bg};
            }}
            QLabel#returnLabel {{
                color: {text_color};
            }}
            QLabel#metaLabel {{
                color: {meta_color};
            }}
        """)

    def _on_theme_changed(self, theme_name):
        """Handle theme changes"""
        self.current_theme = theme_name
        self._update_all_cards_style()
        
    def _update_all_cards_style(self):
        """Update style for all cards"""
        # Ensure cards_layout exists before iterating
        if not hasattr(self, 'cards_layout'):
            return 
            
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                self._update_card_style(card)
    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_returns)
            self._data_loaded = True
