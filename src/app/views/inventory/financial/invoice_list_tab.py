# src/app/views/financial/invoice_list_tab.py
"""
Modern Supplier Invoice List Tab with enhanced UI features:
- Card/List view toggle
- Summary cards with key metrics
- Status-based color coding
- Advanced filtering
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor, QAction
from typing import List
from decimal import Decimal
from config.constants import InvoiceStatus, UIColors
from datetime import datetime
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class InvoiceListTab(QWidget):
    """Modern supplier invoice management interface"""
    
    data_changed = Signal()
    
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.invoice_service = container.supplier_invoice_service
        self.payment_service = container.supplier_payment_service

        self.current_view = 'cards'
        self.selected_invoices = []
        self.lm = language_manager
        self.cf = currency_formatter
        
        self._setup_ui()
        self._connect_signals()
        # self._load_invoices()
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
        title = QLabel(self.lm.get("Inventory.supplier_invoices", "Supplier Invoices"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(f"{self.lm.get('Common.view', 'View')}:")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Common.cards', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Common.list', 'List')}")
        
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
        self.total_invoices_card = self._create_summary_card(self.lm.get("Inventory.total_invoices", "Total Invoices"), "0", "#3B82F6", "📄")
        self.outstanding_card = self._create_summary_card(self.lm.get("Inventory.outstanding", "Outstanding"), self.cf.format(0), "#EF4444", "💰")
        self.overdue_card = self._create_summary_card(self.lm.get("Inventory.overdue", "Overdue"), "0", "#F59E0B", "⚠️")
        self.paid_card = self._create_summary_card(self.lm.get("Inventory.paid_this_month", "Paid This Month"), self.cf.format(0), "#10B981", "✅")
        
        layout.addWidget(self.total_invoices_card)
        layout.addWidget(self.outstanding_card)
        layout.addWidget(self.overdue_card)
        layout.addWidget(self.paid_card)
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
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_invoice_placeholder", "🔍 Search by invoice #, supplier, PO #..."))
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
        layout.addWidget(QLabel(f"{self.lm.get('Common.status', 'Status')}:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("Common.all", "All"), None)
        self.status_filter.addItem(self.lm.get("Common.pending", "Pending"), InvoiceStatus.PENDING)
        self.status_filter.addItem(self.lm.get("Inventory.partial", "Partial"), InvoiceStatus.PARTIAL)
        self.status_filter.addItem(self.lm.get("Common.paid", "Paid"), InvoiceStatus.PAID)
        self.status_filter.addItem(self.lm.get("Inventory.overdue", "Overdue"), InvoiceStatus.OVERDUE)
        self.status_filter.setMinimumWidth(150)
        layout.addWidget(self.status_filter)
        
        layout.addStretch()
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Record payment button
        self.record_payment_btn = QPushButton(f"💳 {self.lm.get('Inventory.record_payment', 'Record Payment')}")
        self.record_payment_btn.setStyleSheet("""
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
        layout.addWidget(self.record_payment_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_invoices)
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
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(10)
        headers = [
            "✓",
            self.lm.get("Inventory.invoice_number", "Invoice #"),
            self.lm.get("Inventory.supplier", "Supplier"),
            self.lm.get("Inventory.po_number", "PO #"),
            self.lm.get("Inventory.invoice_date", "Invoice Date"),
            self.lm.get("Inventory.due_date", "Due Date"),
            self.lm.get("Inventory.total", "Total"),
            self.lm.get("Common.paid", "Paid"),
            self.lm.get("Inventory.outstanding", "Outstanding"),
            self.lm.get("Common.status", "Status")
        ]
        self.invoices_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setColumnWidth(0, 40)
        self.invoices_table.verticalHeader().setVisible(False)
        self.invoices_table.setShowGrid(False)
        self.invoices_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.invoices_table.customContextMenuRequested.connect(self._on_table_context_menu)
        
        # Table Styling
        self.invoices_table.setStyleSheet("""
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
        
        return self.invoices_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search)
        self.status_filter.currentIndexChanged.connect(self._on_filter)
        
        # Actions
        self.record_payment_btn.clicked.connect(self._on_record_payment)
        
        # Table double click
        self.invoices_table.doubleClicked.connect(self._on_table_double_click)
    
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
        
        # Reload invoices for the new view
        self._load_invoices()
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status badge"""
        status_colors = {
            InvoiceStatus.PENDING: '#6B7280',    # Gray
            InvoiceStatus.PARTIAL: '#F59E0B',    # Orange
            InvoiceStatus.PAID: '#10B981',       # Green
            InvoiceStatus.OVERDUE: '#EF4444'     # Red
        }
        return status_colors.get(status, '#6B7280')
    
    def _load_invoices(self):
        """Load and display invoices"""
        try:
            # Get filter
            status_filter = self.status_filter.currentData()
            
            # Get all invoices
            if status_filter:
                invoices = self.invoice_service.get_invoices_by_status(status_filter)
            else:
                invoices = self.invoice_service.list_invoices()
            
            # Apply search filter
            search_term = self.search_input.text().strip()
            if search_term:
                search_lower = search_term.lower()
                invoices = [
                    inv for inv in invoices
                    if (search_lower in inv.invoice_number.lower() or
                        search_lower in (inv.supplier_name or '').lower() or
                        search_lower in (inv.po_number or '').lower())
                ]
            
            # Update summary
            self._update_summary(invoices)
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(invoices)
            elif self.current_view == 'list':
                self._populate_list_view(invoices)
            
        except Exception as e:
            print(f"Error loading invoices: {e}")

    
    def _update_summary(self, invoices: List):
        """Update summary cards"""
        total = len(invoices)
        total_outstanding = Decimal('0.00')
        overdue_count = 0
        paid_this_month = Decimal('0.00')
        
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for inv in invoices:
            outstanding = float(inv.total_amount) - float(inv.paid_amount)
            if outstanding > 0:
                total_outstanding += Decimal(str(outstanding))
            
            if inv.status == InvoiceStatus.OVERDUE:
                overdue_count += 1
            
            if inv.status == InvoiceStatus.PAID and inv.invoice_date and inv.invoice_date >= current_month_start:
                paid_this_month += Decimal(str(inv.total_amount))
        
        self._update_card_value(self.total_invoices_card, str(total))
        self._update_card_value(self.outstanding_card, self.cf.format(total_outstanding))
        self._update_card_value(self.overdue_card, str(overdue_count))
        self._update_card_value(self.paid_card, self.cf.format(paid_this_month))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, invoices: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add invoice cards
        for idx, invoice in enumerate(invoices):
            row = idx // 3
            col = idx % 3
            card = self._create_invoice_card(invoice)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_invoice_card(self, invoice):
        """Create an invoice card widget"""
        card = QFrame()
        card.setObjectName("invoiceCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        status_color = self._get_status_color(invoice.status)
        card.status_color = status_color # Store for selection styling
        
        # Store invoice data
        card.invoice_id = invoice.id
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, invoice)
                event.accept()
            elif event.button() == Qt.RightButton:
                self._show_context_menu(invoice)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
                
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(invoice)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Invoice # and status
        header = QHBoxLayout()
        
        invoice_label = QLabel(invoice.invoice_number)
        invoice_label.setObjectName("invoiceLabel")
        invoice_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(invoice_label)
        
        header.addStretch()
        
        status_badge = QLabel(invoice.status.upper())
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
        
        # Supplier and PO
        if invoice.supplier_name:
            supplier_label = QLabel(f"🏢 {invoice.supplier_name}")
            supplier_label.setObjectName("metaLabel")
            supplier_label.setStyleSheet("font-size: 13px;")
            layout.addWidget(supplier_label)
        
        if invoice.po_number:
            po_label = QLabel(f"📦 PO: {invoice.po_number}")
            po_label.setObjectName("metaLabel")
            po_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(po_label)
        
        # Dates
        invoice_date = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "N/A"
        date_label = QLabel(f"📅 {invoice_date}")
        date_label.setObjectName("metaLabel")
        date_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(date_label)
        
        if invoice.due_date:
            due_label = QLabel(f"⏰ Due: {invoice.due_date.strftime('%Y-%m-%d')}")
            due_label.setObjectName("metaLabel")
            due_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(due_label)
        
        layout.addStretch()
        
        # Footer - Amounts
        footer = QVBoxLayout()
        footer.setSpacing(4)
        
        total_label = QLabel(f"{self.lm.get('Inventory.total', 'Total')}: {self.cf.format(invoice.total_amount)}")
        total_label.setStyleSheet("color: #3B82F6; font-size: 14px; font-weight: bold;")
        footer.addWidget(total_label)
        
        outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
        outstanding_label = QLabel(f"{self.lm.get('Inventory.outstanding', 'Outstanding')}: {self.cf.format(outstanding)}")
        outstanding_color = "#EF4444" if outstanding > 0 else "#10B981"
        outstanding_label.setStyleSheet(f"color: {outstanding_color}; font-size: 16px; font-weight: bold;")
        footer.addWidget(outstanding_label)
        
        layout.addLayout(footer)
        
        # Initial style
        self._update_card_style(card, invoice.id in self.selected_invoices)
        
        return card
    
    def _populate_list_view(self, invoices: List):
        """Populate list view"""
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.invoices_table.setItem(row, 0, checkbox_item)
            
            # Invoice number
            invoice_item = QTableWidgetItem(invoice.invoice_number)
            invoice_item.setData(Qt.UserRole, invoice.id)
            self.invoices_table.setItem(row, 1, invoice_item)
            
            # Supplier
            supplier_name = invoice.supplier_name if invoice.supplier_name else self.lm.get("Common.not_applicable", "N/A")
            self.invoices_table.setItem(row, 2, QTableWidgetItem(supplier_name))
            
            # PO number
            po_number = invoice.po_number if invoice.po_number else self.lm.get("Common.not_applicable", "N/A")
            self.invoices_table.setItem(row, 3, QTableWidgetItem(po_number))
            
            # Invoice date
            invoice_date = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else self.lm.get("Common.not_applicable", "N/A")
            self.invoices_table.setItem(row, 4, QTableWidgetItem(invoice_date))
            
            # Due date
            due_date = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else self.lm.get("Common.not_applicable", "N/A")
            self.invoices_table.setItem(row, 5, QTableWidgetItem(due_date))
            
            # Total amount
            self.invoices_table.setItem(row, 6, QTableWidgetItem(self.cf.format(invoice.total_amount)))
            
            # Paid amount
            self.invoices_table.setItem(row, 7, QTableWidgetItem(self.cf.format(invoice.paid_amount)))
            
            # Outstanding
            outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
            outstanding_item = QTableWidgetItem(self.cf.format(outstanding))
            if outstanding > 0:
                outstanding_item.setForeground(QColor("#EF4444"))
            else:
                outstanding_item.setForeground(QColor("#10B981"))
            self.invoices_table.setItem(row, 8, outstanding_item)
            
            # Status
            status_item = QTableWidgetItem(invoice.status.upper())
            status_item.setForeground(QColor(self._get_status_color(invoice.status)))
            self.invoices_table.setItem(row, 9, status_item)
    
    def _on_search(self, text):
        """Handle search"""
        QTimer.singleShot(300, self._load_invoices)
    
    def _on_filter(self):
        """Handle filter change"""
        self._load_invoices()
        
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
                self._update_card_style(card, card.invoice_id in self.selected_invoices)
    
    def _on_card_clicked(self, card, invoice):
        """Handle card click (toggle selection)"""
        if invoice.id in self.selected_invoices:
            self.selected_invoices.remove(invoice.id)
            self._update_card_style(card, False)
        else:
            self.selected_invoices.append(invoice.id)
            self._update_card_style(card, True)
            
    def _on_card_double_clicked(self, invoice):
        """Handle card double click (open edit dialog)"""
        from views.inventory.financial.invoice_edit_dialog import InvoiceEditDialog
        dialog = InvoiceEditDialog(self.container, invoice, parent=self)
        if dialog.exec():
            self._load_invoices()
            
    def _update_card_style(self, card, is_selected):
        """Update card style based on selection and theme"""
        status_color = getattr(card, 'status_color', '#3B82F6')
        is_dark = self.current_theme == 'dark'
        
        if is_dark:
            bg_color = "#374151" if is_selected else "#1F2937"
            border_color = "#3B82F6" if is_selected else "#374151"
            hover_bg = "#374151"
            hover_border = status_color
            text_color = "white"
            meta_color = "#9CA3AF" # Gray 400
        else: # Light
            bg_color = "#EFF6FF" if is_selected else "#FFFFFF" # Blue 50 or White
            border_color = "#3B82F6" if is_selected else "#E5E7EB" # Blue 500 or Gray 200
            hover_bg = "#F9FAFB" # Gray 50
            hover_border = status_color
            text_color = "#111827" # Gray 900
            meta_color = "#4B5563" # Gray 600

        card.setStyleSheet(f"""
            QFrame#invoiceCard {{
                background-color: {bg_color};
                border: {'2px' if is_selected else '1px'} solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#invoiceCard:hover {{
                border-color: {hover_border};
                background-color: {hover_bg if not is_selected else bg_color};
            }}
            QLabel#invoiceLabel {{
                color: {text_color};
            }}
            QLabel#metaLabel {{
                color: {meta_color};
            }}
        """)

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_invoices.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_style(item.widget(), False)
    
    def _on_table_double_click(self, index):
        """Handle table double click"""
        invoice_id = self.invoices_table.item(index.row(), 1).data(Qt.UserRole)
        invoice = self.invoice_service.get_invoice(invoice_id)
        if invoice:
            from views.inventory.financial.invoice_edit_dialog import InvoiceEditDialog
            dialog = InvoiceEditDialog(self.container, invoice, parent=self)
            if dialog.exec():
                self._load_invoices()
    
    def _on_record_payment(self):
        """Handle record payment button"""
        invoice_id = None
        
        if self.current_view == 'cards':
            if not self.selected_invoices:
                from utils.validation.message_handler import MessageHandler
                MessageHandler.show_warning(self, self.lm.get("Common.no_selection", "No Selection"), self.lm.get("Inventory.select_invoice_payment", "Please select an invoice to record payment."))
                return
            invoice_id = self.selected_invoices[0]
        else:
            selected_rows = self.invoices_table.selectionModel().selectedRows()
            if not selected_rows:
                from utils.validation.message_handler import MessageHandler
                MessageHandler.show_warning(self, self.lm.get("Common.no_selection", "No Selection"), self.lm.get("Inventory.select_invoice_payment", "Please select an invoice to record payment."))
                return
            row = selected_rows[0].row()
            invoice_id = self.invoices_table.item(row, 1).data(Qt.UserRole)
        
        # Open payment dialog
        if invoice_id:
            invoice = self.invoice_service.get_invoice(invoice_id)
            if invoice:
                from views.inventory.record_payment_dialog import RecordPaymentDialog
                dialog = RecordPaymentDialog(self.container, invoice, parent=self)
                if dialog.exec():
                    self._load_invoices()
    
    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        table = self.sender()
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        invoice_id = table.item(row, 1).data(Qt.UserRole)
        if invoice_id:
            invoice = self.invoice_service.get_invoice(invoice_id)
            if invoice:
                self._show_context_menu(invoice)
    
    def _show_context_menu(self, invoice):
        """Show context menu for supplier invoice"""
        menu = QMenu(self)
        
        # View/Edit Invoice
        view_action = QAction(f"📄 {self.lm.get('Inventory.view_edit_invoice', 'View/Edit Invoice')}", self)
        view_action.triggered.connect(lambda: self._open_invoice_dialog(invoice))
        menu.addAction(view_action)
        
        # Check if invoice has outstanding balance
        outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
        
        if outstanding > 0:
            menu.addSeparator()
            
            # Record Payment
            payment_action = QAction(f"💳 {self.lm.get('Inventory.record_payment', 'Record Payment')}", self)
            payment_action.triggered.connect(lambda: self._record_payment_for_invoice(invoice))
            menu.addAction(payment_action)
            
            # Mark as Paid
            mark_paid_action = QAction(f"✅ {self.lm.get('Inventory.mark_as_paid', 'Mark as Paid')}", self)
            mark_paid_action.triggered.connect(lambda: self._mark_as_paid(invoice))
            menu.addAction(mark_paid_action)
        
        menu.exec(self.cursor().pos())
    
    def _open_invoice_dialog(self, invoice):
        """Open invoice edit dialog"""
        from views.inventory.financial.invoice_edit_dialog import InvoiceEditDialog
        dialog = InvoiceEditDialog(self.container, invoice, parent=self)
        if dialog.exec():
            self._load_invoices()
    
    def _record_payment_for_invoice(self, invoice):
        """Record payment for invoice"""
        from views.inventory.record_payment_dialog import RecordPaymentDialog
        dialog = RecordPaymentDialog(self.container, invoice, parent=self)
        if dialog.exec():
            self._load_invoices()
    
    def _mark_as_paid(self, invoice):
        """Mark invoice as fully paid"""
        outstanding = float(invoice.total_amount) - float(invoice.paid_amount)
        
        if QMessageBox.question(
            self,
            self.lm.get("Inventory.confirm_mark_paid", "Confirm Mark as Paid"),
            self.lm.get("Inventory.mark_invoice_paid_question", "Mark invoice '{invoice_number}' as fully paid?\nOutstanding amount: {amount}").format(
                invoice_number=invoice.invoice_number,
                amount=self.cf.format(outstanding)
            ),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                # Record a payment for the outstanding amount
                payment_data = {
                    'invoice': invoice.id,
                    'amount': outstanding,
                    'payment_date': datetime.now(),
                    'payment_method': 'Manual',
                    'notes': 'Marked as paid via context menu'
                }
                self.payment_service.record_payment(payment_data)
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Inventory.invoice_marked_paid", "Invoice marked as paid"))
                self._load_invoices()
            except Exception as e:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.failed_mark_paid", "Failed to mark as paid: {error}").format(error=str(e)))

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_invoices)
            self._data_loaded = True
