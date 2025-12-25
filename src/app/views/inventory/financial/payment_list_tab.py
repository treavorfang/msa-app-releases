# src/app/views/financial/payment_list_tab.py
"""
Modern Payment List Tab with enhanced UI features:
- Card/List view toggle
- Summary cards with key metrics
- Advanced filtering
- Payment method color coding
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QDateEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import QColor, QCursor
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta
from config.constants import PaymentMethod, UIColors
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from core.event_bus import EventBus
from core.events import PaymentCreatedEvent, PaymentUpdatedEvent, PaymentDeletedEvent


class PaymentListTab(QWidget):
    """Modern payment management interface"""
    
    data_changed = Signal()
    
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.payment_service = container.supplier_payment_service
        self.lm = language_manager
        self.cf = currency_formatter

        self.current_view = 'cards'
        self.selected_payments = []
        
        self._setup_ui()
        self._connect_signals()
        # self._load_payments()
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
        title = QLabel(self.lm.get("Payments.payments_title", "Payments"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Payments.view", "View") + ":")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('Payments.cards_view', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('Payments.list_view', 'List')}")
        
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
        self.today_card = self._create_summary_card(self.lm.get("Payments.today", "Today"), self.cf.format(0), "#10B981", "📅")
        self.week_card = self._create_summary_card(self.lm.get("Payments.this_week", "This Week"), self.cf.format(0), "#3B82F6", "📊")
        self.month_card = self._create_summary_card(self.lm.get("Payments.this_month", "This Month"), self.cf.format(0), "#8B5CF6", "📈")
        self.total_card = self._create_summary_card(self.lm.get("Payments.total", "Total"), self.cf.format(0), "#F59E0B", "💰")
        
        layout.addWidget(self.today_card)
        layout.addWidget(self.week_card)
        layout.addWidget(self.month_card)
        layout.addWidget(self.total_card)
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
        
        # First row - Date range
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel(self.lm.get("Payments.from", "From") + ":"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setStyleSheet("""
            QDateEdit {
                padding: 6px 12px;
                border: 1px solid #374151;
                border-radius: 6px;
            }
        """)
        row1.addWidget(self.from_date)
        
        row1.addWidget(QLabel(self.lm.get("Payments.to", "To") + ":"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setStyleSheet("""
            QDateEdit {
                padding: 6px 12px;
                border: 1px solid #374151;
                border-radius: 6px;
            }
        """)
        row1.addWidget(self.to_date)
        
        # Payment method filter
        row1.addWidget(QLabel(self.lm.get("Payments.method", "Method") + ":"))
        self.method_filter = QComboBox()
        self.method_filter.addItem(self.lm.get("Payments.all_methods", "All"), None)
        for method, display_name in PaymentMethod.DISPLAY_NAMES.items():
            self.method_filter.addItem(display_name, method)
        self.method_filter.setMinimumWidth(150)
        row1.addWidget(self.method_filter)
        
        row1.addStretch()
        
        layout.addLayout(row1)
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Payments.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_payments)
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
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(7)
        headers = [
            "✓",
            self.lm.get("Payments.payment_date", "Payment Date"),
            self.lm.get("Payments.invoice_number", "Invoice #"),
            self.lm.get("Payments.supplier", "Supplier"),
            self.lm.get("Payments.amount", "Amount"),
            self.lm.get("Payments.payment_method", "Method"),
            self.lm.get("Payments.reference", "Reference")
        ]
        self.payments_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setColumnWidth(0, 40)
        self.payments_table.verticalHeader().setVisible(False)
        self.payments_table.setShowGrid(False)
        
        # Table Styling
        self.payments_table.setStyleSheet("""
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
        
        return self.payments_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.from_date.dateChanged.connect(self._on_filter_changed)
        self.to_date.dateChanged.connect(self._on_filter_changed)
        self.method_filter.currentIndexChanged.connect(self._on_filter_changed)
        
        # Subscribe to EventBus events
        EventBus.subscribe(PaymentCreatedEvent, self._handle_payment_event)
        EventBus.subscribe(PaymentUpdatedEvent, self._handle_payment_event)
        EventBus.subscribe(PaymentDeletedEvent, self._handle_payment_event)
    
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
        
        # Reload payments for the new view
        self._load_payments()
    
    def _on_filter_changed(self):
        """Handle filter changes"""
        QTimer.singleShot(300, self._load_payments)
    
    def _get_method_color(self, method: str) -> str:
        """Get color for payment method"""
        method_colors = {
            'cash': '#10B981',           # Green
            'credit_card': '#3B82F6',    # Blue
            'bank_transfer': '#8B5CF6',  # Purple
            'check': '#F59E0B',          # Orange
            'other': '#6B7280'           # Gray
        }
        return method_colors.get(method, '#6B7280')
    
    def _load_payments(self):
        """Load and display payments"""
        try:
            # Get all payments
            payments = self.payment_service.list_payments()
            
            # Get filter values
            from_date = self.from_date.date().toPython()
            to_date = self.to_date.date().toPython()
            method_filter = self.method_filter.currentData()
            
            # Filter payments
            filtered_payments = []
            for payment in payments:
                payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
                
                # Date filter
                if payment_date < from_date or payment_date > to_date:
                    continue
                
                # Method filter
                if method_filter and payment.payment_method != method_filter:
                    continue
                
                filtered_payments.append(payment)
            
            # Update summary
            self._update_summary(filtered_payments)
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(filtered_payments)
            elif self.current_view == 'list':
                self._populate_list_view(filtered_payments)
            
        except Exception as e:
            print(f"Error loading payments: {e}")
    
    def _update_summary(self, payments: List):
        """Update summary cards"""
        total_today = Decimal('0.00')
        total_week = Decimal('0.00')
        total_month = Decimal('0.00')
        total_all = Decimal('0.00')
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        for payment in payments:
            payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
            amount = Decimal(str(payment.amount))
            
            total_all += amount
            
            if payment_date == today:
                total_today += amount
            if payment_date >= week_ago:
                total_week += amount
            if payment_date >= month_ago:
                total_month += amount
        
        self._update_card_value(self.today_card, self.cf.format(total_today))
        self._update_card_value(self.week_card, self.cf.format(total_week))
        self._update_card_value(self.month_card, self.cf.format(total_month))
        self._update_card_value(self.total_card, self.cf.format(total_all))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, payments: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add payment cards
        for idx, payment in enumerate(payments):
            row = idx // 3
            col = idx % 3
            card = self._create_payment_card(payment)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_payment_card(self, payment):
        """Create a payment card widget"""
        card = QFrame()
        card.setObjectName("paymentCard")
        card.setMinimumHeight(180)
        card.setMaximumHeight(220)
        
        method_color = self._get_method_color(payment.payment_method)
        card.method_color = method_color # Store for selection styling
        card.payment_id = payment.id
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, payment)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
                
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(payment)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Date and method
        header = QHBoxLayout()
        
        payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
        date_label = QLabel(payment_date.strftime("%Y-%m-%d"))
        date_label.setObjectName("dateLabel")
        date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(date_label)
        
        header.addStretch()
        
        method_display = PaymentMethod.DISPLAY_NAMES.get(payment.payment_method, payment.payment_method)
        method_badge = QLabel(method_display)
        method_badge.setStyleSheet(f"""
            background-color: {method_color};
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(method_badge)
        
        layout.addLayout(header)
        
        # Invoice number
        invoice_number = payment.invoice_number if payment.invoice_number else "N/A"
        invoice_label = QLabel(f"📄 {self.lm.get('Payments.invoice', 'Invoice')}: {invoice_number}")
        invoice_label.setObjectName("metaLabel")
        invoice_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(invoice_label)
        
        # Supplier
        supplier_name = "N/A"
        if payment.supplier_name:
            supplier_name = payment.supplier_name
        supplier_label = QLabel(f"🏢 {supplier_name}")
        supplier_label.setObjectName("metaLabel")
        supplier_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(supplier_label)
        
        # Reference
        if payment.reference_number:
            ref_label = QLabel(f"🔖 {self.lm.get('Payments.ref', 'Ref')}: {payment.reference_number}")
            ref_label.setObjectName("metaLabel")
            ref_label.setStyleSheet("font-size: 11px;")
            layout.addWidget(ref_label)
        
        layout.addStretch()
        
        # Footer - Amount
        amount_label = QLabel(self.cf.format(payment.amount))
        amount_label.setStyleSheet(f"color: {method_color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(amount_label)
        
        # Initial style
        self._update_card_style(card, payment.id in self.selected_payments)
        
        return card
    
    def _populate_list_view(self, payments: List):
        """Populate list view"""
        self.payments_table.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.payments_table.setItem(row, 0, checkbox_item)
            
            # Payment date
            payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
            self.payments_table.setItem(row, 1, QTableWidgetItem(payment_date.strftime("%Y-%m-%d")))
            
            # Invoice number
            invoice_number = payment.invoice_number if payment.invoice_number else "N/A"
            self.payments_table.setItem(row, 2, QTableWidgetItem(invoice_number))
            
            # Supplier
            supplier_name = "N/A"
            if payment.supplier_name:
                supplier_name = payment.supplier_name
            self.payments_table.setItem(row, 3, QTableWidgetItem(supplier_name))
            
            # Amount
            amount_item = QTableWidgetItem(self.cf.format(payment.amount))
            amount_item.setForeground(QColor(self._get_method_color(payment.payment_method)))
            self.payments_table.setItem(row, 4, amount_item)
            
            # Method
            method_display = PaymentMethod.DISPLAY_NAMES.get(payment.payment_method, payment.payment_method)
            method_item = QTableWidgetItem(method_display)
            method_item.setForeground(QColor(self._get_method_color(payment.payment_method)))
            self.payments_table.setItem(row, 5, method_item)
            
            # Reference
    def _on_card_clicked(self, card, payment):
        """Handle card click (toggle selection)"""
        if payment.id in self.selected_payments:
            self.selected_payments.remove(payment.id)
            self._update_card_style(card, False)
        else:
            self.selected_payments.append(payment.id)
            self._update_card_style(card, True)
            
    def _on_card_double_clicked(self, payment):
        """Handle card double click (open details)"""
        # Payment details dialog not yet implemented, but we can add a placeholder or just pass
        # For now, let's just print or do nothing as there's no edit dialog mentioned in imports
        pass
            
    def _update_card_style(self, card, is_selected):
        """Update card style based on selection and theme"""
        method_color = getattr(card, 'method_color', '#3B82F6')
        is_dark = self.current_theme == 'dark'
        
        if is_dark:
            bg_color = "#374151" if is_selected else "#1F2937"
            border_color = "#3B82F6" if is_selected else "#374151"
            hover_bg = "#374151"
            hover_border = method_color
            text_color = "white"
            meta_color = "#9CA3AF" # Gray 400
        else: # Light
            bg_color = "#EFF6FF" if is_selected else "#FFFFFF" # Blue 50 or White
            border_color = "#3B82F6" if is_selected else "#E5E7EB" # Blue 500 or Gray 200
            hover_bg = "#F9FAFB" # Gray 50
            hover_border = method_color
            text_color = "#111827" # Gray 900
            meta_color = "#4B5563" # Gray 600

        card.setStyleSheet(f"""
            QFrame#paymentCard {{
                background-color: {bg_color};
                border: {'2px' if is_selected else '1px'} solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#paymentCard:hover {{
                border-color: {hover_border};
                background-color: {hover_bg if not is_selected else bg_color};
            }}
            QLabel#dateLabel {{
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
                self._update_card_style(card, card.payment_id in self.selected_payments)

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_payments.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_style(item.widget(), False)
    
    def _handle_payment_event(self, event):
        """Handle payment-related EventBus events"""
        # Refresh payment list when any payment event occurs
        QTimer.singleShot(500, self._load_payments)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_payments)
            self._data_loaded = True
