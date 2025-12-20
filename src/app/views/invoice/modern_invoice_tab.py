# src/app/views/financial/modern_invoice_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QPushButton, QLabel, QComboBox,
                              QHeaderView, QFrame, QLineEdit, QCheckBox, QScrollArea,
                              QGridLayout, QProgressBar, QFileDialog, QMenu, QMessageBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal, QSettings
from PySide6.QtGui import QColor
from config.constants import UIColors
from datetime import datetime, timedelta
from decimal import Decimal
from views.invoice.customer_invoice_details_dialog import CustomerInvoiceDetailsDialog
from views.invoice.record_customer_payment_dialog import RecordCustomerPaymentDialog
from utils.print.invoice_generator import InvoiceGenerator
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
import csv
from core.event_bus import EventBus
from core.events import InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent, BranchContextChangedEvent
from views.components.new_dashboard_widgets import is_dark_theme

class ModernInvoiceTab(QWidget):
    """Modern invoice tab with card/list views and enhanced features"""
    
    invoice_updated = Signal()
    
    def showEvent(self, event):
        super().showEvent(event)
        if not self._data_loaded:
            QTimer.singleShot(100, self._load_invoices)
            self._data_loaded = True
            
    def __init__(
        self,
        invoice_controller,
        ticket_controller,
        business_settings_service,
        part_service,
        user,
        container=None,
        parent=None
    ):
        super().__init__(parent)
        self.container = container
        self.user = user
        
        # Explicit dependencies
        self.invoice_controller = invoice_controller
        self.ticket_controller = ticket_controller
        self.business_settings_service = business_settings_service
        self.part_service = part_service
        
        # State
        self.current_view = 'cards'
        self.current_branch_id = None
        self._current_invoice_list = []
        self.selected_invoices = []
        self._customer_cache = {}  # Cache customer names
        
        # Search timer for debounce
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._load_invoices)
        
        # Initialize invoice generator
        self.invoice_generator = InvoiceGenerator(self, self.business_settings_service)
        
        self.lm = language_manager
        
        self._setup_ui()
        self._connect_signals()

        self._subscribe_to_events()
        
        # Flag to track if data has been loaded
        self._data_loaded = False
        # self._load_invoices()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header with summary cards
        summary_section = self._create_summary_cards()
        layout.addLayout(summary_section)
        
        # Toolbar with search, filters, and view toggle
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # Advanced filters (collapsible)
        filter_section = self._create_advanced_filters()
        layout.addLayout(filter_section)
        
        # View container (cards or list)
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view_container)
    
    def _create_summary_cards(self):
        """Create summary cards showing key metrics"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Total Outstanding
        self.outstanding_card = self._create_summary_card(
            self.lm.get("Invoices.total_outstanding", "Total Outstanding"),
            currency_formatter.format(0),
            "#E74C3C",  # Red
            "💰"
        )
        layout.addWidget(self.outstanding_card)
        
        # Paid This Month
        self.paid_month_card = self._create_summary_card(
            self.lm.get("Invoices.paid_this_month", "Paid This Month"),
            currency_formatter.format(0),
            "#27AE60",  # Green
            "✓"
        )
        layout.addWidget(self.paid_month_card)
        
        # Overdue Count
        self.overdue_card = self._create_summary_card(
            self.lm.get("Invoices.overdue_invoices", "Overdue Invoices"),
            "0",
            "#E67E22",  # Orange
            "⚠"
        )
        layout.addWidget(self.overdue_card)
        
        # Total Invoices
        self.total_card = self._create_summary_card(
            self.lm.get("Invoices.total_invoices", "Total Invoices"),
            "0",
            "#3498DB",  # Blue
            "#"
        )
        layout.addWidget(self.total_card)
        
        return layout
    
    def _create_summary_card(self, title, value, color, icon):
        """Create a summary card widget"""
        card = QFrame()
        card.setObjectName("summary_card")
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            #summary_card {{
                background-color: {color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        # ✅ ADD THIS LINE to match ticket metric cards:
        card.setFixedHeight(100)  # Match ticket metric card height
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Icon and title
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; color: white; border: none; padding: 0;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.9); font-weight: bold; border: none; padding: 0;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; color: white; font-weight: bold; border: none; padding: 0;")
        value_label.setObjectName("card_value")
        layout.addWidget(value_label)
        
        return card
    
    def _create_toolbar(self):
        """Create toolbar with search and view toggle"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Invoices.search_placeholder", "🔍 Search by invoice #, customer name..."))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(300)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        # View toggle buttons
        view_label = QLabel(self.lm.get("Common.view", "View") + ":")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(self.lm.get("Invoices.view_cards", "📇 Cards"))
        self.cards_view_btn.setCheckable(True)
        self.cards_view_btn.setChecked(True)
        self.cards_view_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #3498DB;
                color: white;
            }
        """)
        layout.addWidget(self.cards_view_btn)
        
        self.list_view_btn = QPushButton(self.lm.get("Invoices.view_list", "📋 List"))
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #3498DB;
                color: white;
            }
        """)
        layout.addWidget(self.list_view_btn)
        
        return layout
    
    def _create_advanced_filters(self):
        """Create advanced filter controls"""
        layout = QVBoxLayout()
        
        # First row - Status and date filters
        row1 = QHBoxLayout()
        
        # Status filter
        row1.addWidget(QLabel(self.lm.get("Invoices.status_filter", "Status:")))
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("Invoices.all_statuses", "All Statuses"), "all")
        self.status_filter.addItem(self.lm.get("Invoices.status_unpaid", "Unpaid"), "unpaid")
        self.status_filter.addItem(self.lm.get("Invoices.status_partially_paid", "Partially Paid"), "partially_paid")
        self.status_filter.addItem(self.lm.get("Invoices.status_paid", "Paid"), "paid")
        self.status_filter.addItem(self.lm.get("Invoices.status_cancelled", "Cancelled"), "cancelled")
        self.status_filter.setMinimumWidth(150)
        row1.addWidget(self.status_filter)
        
        # Overdue filter
        self.overdue_checkbox = QCheckBox(self.lm.get("Invoices.show_overdue", "Show Only Overdue"))
        row1.addWidget(self.overdue_checkbox)
        
        # Show cancelled
        self.show_cancelled_checkbox = QCheckBox(self.lm.get("Invoices.show_cancelled", "Show Cancelled"))
        row1.addWidget(self.show_cancelled_checkbox)
        
        row1.addStretch()
        
        # Clear filters button
        clear_btn = QPushButton(self.lm.get("Invoices.clear_filters", "🔄 Clear Filters"))
        clear_btn.clicked.connect(self._clear_filters)
        row1.addWidget(clear_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton(self.lm.get("Common.refresh", "🔄 Refresh"))
        row1.addWidget(self.refresh_btn)

        # Export button with menu
        export_btn = QPushButton(f"📥 {self.lm.get('Common.export', 'Export')}")
        export_menu = QMenu(self)
        
        # CSV Action
        export_csv_action = QAction(self.lm.get("Invoices.export_csv", "Export CSV"), self)
        export_csv_action.triggered.connect(self._export_to_csv)
        export_menu.addAction(export_csv_action)
        
        # PDF Action
        export_pdf_action = QAction(self.lm.get("Invoices.export_pdf", "Export PDF"), self)
        export_pdf_action.triggered.connect(self._export_to_pdf)
        export_menu.addAction(export_pdf_action)
        
        export_btn.setMenu(export_menu)
        row1.addWidget(export_btn)
        
        layout.addLayout(row1)
        
        return layout
    
    def _connect_signals(self):
        """Connect all signals"""
        self.search_input.textChanged.connect(self._on_search_changed)
        self.status_filter.currentTextChanged.connect(self._load_invoices)
        self.overdue_checkbox.stateChanged.connect(self._load_invoices)
        self.show_cancelled_checkbox.stateChanged.connect(self._load_invoices)
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        self.refresh_btn.clicked.connect(self._load_invoices)
        # Export actions are now connected directly in _create_action_buttons
        
        # Invoice events are now handled by EventBus
        self._connect_theme_signal()

    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        self._load_invoices()
    
    def _on_search_changed(self):
        """Handle search input change with debounce"""
        self.search_timer.start()
    
    def _switch_view(self, view_mode):
        """Switch between card and list views"""
        self.current_view = view_mode
        
        if view_mode == 'cards':
            self.cards_view_btn.setChecked(True)
            self.list_view_btn.setChecked(False)
        else:
            self.cards_view_btn.setChecked(False)
            self.list_view_btn.setChecked(True)
        
        self._load_invoices()
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.overdue_checkbox.setChecked(False)
        self.show_cancelled_checkbox.setChecked(False)
    
    def _load_invoices(self):
        """Load and display invoices with current filters"""
        try:
            print("DEBUG: _load_invoices called")
            # Get all invoices
            invoices = self.invoice_controller.list_invoices(branch_id=self.current_branch_id)
            print(f"DEBUG: Retrieved {len(invoices)} invoices")
            
            # Apply filters
            filtered_invoices = self._apply_filters(invoices)
            print(f"DEBUG: After filters: {len(filtered_invoices)} invoices")
            
            # Store for reference
            self._current_invoice_list = filtered_invoices
            
            # Update summary cards
            print("DEBUG: Updating summary cards...")
            self._update_summary_cards(invoices, filtered_invoices)
            print("DEBUG: Summary cards updated")
            
            # Display in current view
            print(f"DEBUG: Displaying in {self.current_view} view")
            if self.current_view == 'cards':
                self._populate_cards_view(filtered_invoices)
            else:
                self._populate_list_view(filtered_invoices)
            print("DEBUG: View populated successfully")
                
        except Exception as e:
            print(f"ERROR loading invoices: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_filters(self, invoices):
        """Apply current filters to invoice list"""
        filtered = invoices
        
        # Search filter
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered = [inv for inv in filtered if self._matches_search(inv, search_text)]
        
        # Status filter
        status_key = self.status_filter.currentData()
        if status_key and status_key != "all":
            filtered = [inv for inv in filtered if inv.payment_status == status_key]
        
        # Overdue filter
        if self.overdue_checkbox.isChecked():
            filtered = [inv for inv in filtered if self._is_overdue(inv)]
        
        # Show cancelled filter
        if not self.show_cancelled_checkbox.isChecked():
            filtered = [inv for inv in filtered if inv.payment_status != 'cancelled']
        
        return filtered
    
    def _matches_search(self, invoice, search_text):
        """Check if invoice matches search text"""
        # Search in invoice number
        if search_text in invoice.invoice_number.lower():
            return True
        
        # Search in customer name
        customer_name = self._get_customer_name(invoice)
        if search_text in customer_name.lower():
            return True
        
        return False
    
    def _is_overdue(self, invoice):
        """Check if invoice is overdue"""
        if invoice.payment_status == 'paid' or not invoice.due_date:
            return False
        return datetime.now() > invoice.due_date
    
    def _get_customer_name(self, invoice):
        """Get customer name for invoice (DTO optimized)"""
        return invoice.customer_name or self.lm.get("Common.unknown", "Unknown")
    
    def _calculate_paid_amount(self, invoice):
        """Calculate total paid amount for invoice"""
        paid = Decimal('0.00')
        if hasattr(invoice, 'payments') and invoice.payments:
            for payment in invoice.payments:
                paid += Decimal(str(payment.amount))
        return paid
    
    def _calculate_balance(self, invoice):
        """Calculate remaining balance"""
        total = Decimal(str(invoice.total))
        paid = self._calculate_paid_amount(invoice)
        return total - paid
    
    def _update_summary_cards(self, all_invoices, filtered_invoices):
        """Update summary card values"""
        total_outstanding = Decimal('0.00')
        paid_this_month = Decimal('0.00')
        overdue_count = 0
        
        try:
            # Calculate from all invoices (not filtered)
            # Update summary cards
            for invoice in all_invoices:
                try:
                    balance = invoice.balance_due
                    
                    # Outstanding
                    if balance > 0 and invoice.payment_status != 'cancelled':
                        total_outstanding += balance
                    
                    # Paid this month
                    if invoice.payments:
                        for payment in invoice.payments:
                            if payment.paid_at:
                                p_date = payment.paid_at
                                if p_date.month == datetime.now().month and p_date.year == datetime.now().year:
                                    paid_this_month += payment.amount
                    
                    # Overdue
                    if self._is_overdue(invoice):
                        overdue_count += 1
                except Exception as e:
                    print(f"Error processing invoice {invoice.id}: {e}")
                    continue
            
            # Update card values safely
            try:
                outstanding_label = self.outstanding_card.findChild(QLabel, "card_value")
                if outstanding_label:
                    outstanding_label.setText(currency_formatter.format(total_outstanding))
                    
                paid_label = self.paid_month_card.findChild(QLabel, "card_value")
                if paid_label:
                    paid_label.setText(currency_formatter.format(paid_this_month))
                    
                overdue_label = self.overdue_card.findChild(QLabel, "card_value")
                if overdue_label:
                    overdue_label.setText(str(overdue_count))
                    
                total_label = self.total_card.findChild(QLabel, "card_value")
                if total_label:
                    total_label.setText(str(len(filtered_invoices)))
            except Exception as e:
                print(f"Error updating summary card labels: {e}")
                
        except Exception as e:
            print(f"Error in _update_summary_cards: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _populate_cards_view(self, invoices):
        """Populate card view with invoices"""
        # Clear existing view
        while self.view_layout.count():
            child = self.view_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not invoices:
        # Note: Using hardcoded string here as it's a fallback, but could be externalized
            no_data_label = QLabel(self.lm.get("Common.no_data", "No data found"))
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: gray; font-size: 14px; padding: 40px;")
            self.view_layout.addWidget(no_data_label)
            return
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        # Handle background click to deselect
        container.mousePressEvent = self._on_background_clicked
        grid_layout = QGridLayout(container)
        grid_layout.setSpacing(12)
        
        # Sort by date (newest first)
        sorted_invoices = sorted(invoices, key=lambda x: x.created_at, reverse=True)
        
        # Create cards (2 columns)
        for idx, invoice in enumerate(sorted_invoices):
            card = self._create_invoice_card(invoice)
            row = idx // 2
            col = idx % 2
            grid_layout.addWidget(card, row, col)
        
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)
        
        scroll.setWidget(container)
        self.view_layout.addWidget(scroll)
    
    def _create_invoice_card(self, invoice):
        """Create an invoice card"""
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        bg_color = "#2C3E50" if dark_mode else "#FFFFFF"
        border_color = "#34495E" if dark_mode else "#BDC3C7"
        text_main = "white" if dark_mode else "#2C3E50"
        text_sub = "#BDC3C7" if dark_mode else "#7F8C8D"
        text_date = "#95A5A6" if dark_mode else "#95A5A6"
        text_total = "#ECF0F1" if dark_mode else "#2C3E50"
        
        card = QFrame()
        card.setObjectName("invoice_card")
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            #invoice_card {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            #invoice_card:hover {{
                border-color: #3498DB;
                background-color: {bg_color};
            }}
            QLabel {{
                border: none;
                padding: 0;
                background: transparent;
            }}
        """)
        card.setMinimumHeight(160)
        card.setCursor(Qt.PointingHandCursor)
        
        # Store invoice data
        card.invoice_id = invoice.id
        card.invoice_dto = invoice
        
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
        
        # Header: Invoice # and Status
        header = QHBoxLayout()
        
        invoice_label = QLabel(f"#{invoice.invoice_number}")
        invoice_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_main};")
        header.addWidget(invoice_label)
        
        header.addStretch()
        
        # Status badge
        status_badge = self._create_status_badge(invoice)
        header.addWidget(status_badge)
        
        layout.addLayout(header)
        
        # Customer name
        customer_name = self._get_customer_name(invoice)
        customer_label = QLabel(f"👤 {customer_name}")
        customer_label.setStyleSheet(f"font-size: 12px; color: {text_sub};")
        layout.addWidget(customer_label)
        
        # Date
        date_str = invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else "N/A"
        date_label = QLabel(f"📅 {date_str}")
        date_label.setStyleSheet(f"font-size: 11px; color: {text_date};")
        layout.addWidget(date_label)

        # Device
        if invoice.device_brand:
            device_label = QLabel(f"📱 {invoice.device_brand} {invoice.device_model or ''}")
            device_label.setStyleSheet(f"font-size: 11px; color: {text_sub};")
            layout.addWidget(device_label)
            
        if invoice.error_description:
            issue_label = QLabel(f"🔧 {invoice.error_description}")
            issue_label.setStyleSheet(f"font-size: 11px; color: {text_sub}; font-style: italic;")
            issue_label.setWordWrap(True)
            layout.addWidget(issue_label)
        
        # Amounts
        total = invoice.total
        paid = invoice.paid_amount
        balance = invoice.balance_due
        
        amounts_layout = QHBoxLayout()
        
        total_lbl = QLabel(f"{self.lm.get('Invoices.total_header', 'Total')}: {currency_formatter.format(total)}")
        total_lbl.setStyleSheet(f"color: {text_total};")
        amounts_layout.addWidget(total_lbl)
        
        paid_lbl = QLabel(f"{self.lm.get('Invoices.paid', 'Paid')}: {currency_formatter.format(paid)}")
        paid_lbl.setStyleSheet("color: #2ECC71;")
        amounts_layout.addWidget(paid_lbl)
        
        balance_lbl = QLabel(f"{self.lm.get('Invoices.balance', 'Balance')}: {currency_formatter.format(balance)}")
        balance_lbl.setStyleSheet("color: #E74C3C;")
        amounts_layout.addWidget(balance_lbl)
        
        layout.addLayout(amounts_layout)
        
        # Payment progress bar
        if total > 0:
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setValue(int((paid / total) * 100))
            progress.setTextVisible(True)
            progress.setFormat(f"{int((paid / total) * 100)}%")
            
            # Color based on status
            if invoice.payment_status == 'paid':
                progress.setStyleSheet("QProgressBar::chunk { background-color: #27AE60; }")
            elif invoice.payment_status == 'partially_paid':
                progress.setStyleSheet("QProgressBar::chunk { background-color: #E67E22; }")
            else:
                progress.setStyleSheet("QProgressBar::chunk { background-color: #E74C3C; }")
            
            layout.addWidget(progress)
        
        # Overdue indicator
        if self._is_overdue(invoice):
            days_overdue = (datetime.now() - invoice.due_date).days
            overdue_label = QLabel(f"⚠ {self.lm.get('Invoices.status_overdue', 'OVERDUE')} {days_overdue} days")
            overdue_label.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 11px;")
            layout.addWidget(overdue_label)
            
        # Initial style
        self._update_card_selection_style(card, invoice.id in self.selected_invoices)
        
        return card
    
    def _create_status_badge(self, invoice):
        """Create status badge for invoice"""
        status_colors = {
            'paid': '#27AE60',
            'unpaid': '#E74C3C',
            'partially_paid': '#E67E22',
            'cancelled': '#95A5A6'
        }
        
        status_text = invoice.payment_status.upper().replace('_', ' ')
        # Try to translate status
        if invoice.payment_status == 'paid':
            status_text = self.lm.get("Invoices.status_paid", "Paid").upper()
        elif invoice.payment_status == 'unpaid':
            status_text = self.lm.get("Invoices.status_unpaid", "Unpaid").upper()
        elif invoice.payment_status == 'partially_paid':
            status_text = self.lm.get("Invoices.status_partially_paid", "Partially Paid").upper()
        elif invoice.payment_status == 'cancelled':
            status_text = self.lm.get("Invoices.status_cancelled", "Cancelled").upper()
            
        color = status_colors.get(invoice.payment_status, '#95A5A6')
        
        badge = QLabel(status_text)
        badge.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 4px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        
        return badge
    
    def _populate_list_view(self, invoices):
        """Populate list view with invoices"""
        # Clear existing view
        while self.view_layout.count():
            child = self.view_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create table
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            self.lm.get("Invoices.invoice_number", "Invoice #"),
            self.lm.get("Invoices.date", "Date"),
            self.lm.get("Invoices.customer", "Customer"),
            self.lm.get("Invoices.device", "Device"),
            self.lm.get("Invoices.issue", "Issue"),
            self.lm.get("Invoices.total", "Total"),
            self.lm.get("Invoices.paid", "Paid"),
            self.lm.get("Invoices.balance", "Balance"),
            self.lm.get("Invoices.status", "Status"),
            self.lm.get("Invoices.due_date", "Due Date")
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._on_table_context_menu)
        table.doubleClicked.connect(lambda index: self._on_table_double_clicked(index, table))
        
        # Sort by date (newest first)
        sorted_invoices = sorted(invoices, key=lambda x: x.created_at, reverse=True)
        
        table.setRowCount(len(sorted_invoices))
        
        for row, invoice in enumerate(sorted_invoices):
            # Invoice number
            table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))
            
            # Date
            date_str = invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else "N/A"
            table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Customer
            customer_name = self._get_customer_name(invoice)
            table.setItem(row, 2, QTableWidgetItem(customer_name))
            
            # Device
            device_str = f"{invoice.device_brand} {invoice.device_model}" if invoice.device_brand else "N/A"
            table.setItem(row, 3, QTableWidgetItem(device_str))
            
            # Issue
            issue_str = invoice.error_description if invoice.error_description else "N/A"
            table.setItem(row, 4, QTableWidgetItem(issue_str))
            
            # Total
            total = invoice.total
            table.setItem(row, 5, QTableWidgetItem(currency_formatter.format(total)))
            
            # Paid
            paid = invoice.paid_amount
            table.setItem(row, 6, QTableWidgetItem(currency_formatter.format(paid)))
            
            # Balance
            balance = invoice.balance_due
            balance_item = QTableWidgetItem(currency_formatter.format(balance))
            if balance > 0:
                balance_item.setForeground(QColor("#E74C3C"))
            table.setItem(row, 7, balance_item)
            
            # Status
            status_text = invoice.payment_status.upper().replace('_', ' ')
            if invoice.payment_status == 'paid':
                status_text = self.lm.get("Invoices.status_paid", "Paid").upper()
            elif invoice.payment_status == 'unpaid':
                status_text = self.lm.get("Invoices.status_unpaid", "Unpaid").upper()
            elif invoice.payment_status == 'partially_paid':
                status_text = self.lm.get("Invoices.status_partially_paid", "Partially Paid").upper()
            elif invoice.payment_status == 'cancelled':
                status_text = self.lm.get("Invoices.status_cancelled", "Cancelled").upper()
            
            status_item = QTableWidgetItem(status_text)
            
            # Color
            if invoice.payment_status == 'paid':
                status_item.setForeground(QColor("#27AE60"))
            elif invoice.payment_status == 'unpaid':
                status_item.setForeground(QColor("#E74C3C"))
            elif invoice.payment_status == 'partially_paid':
                status_item.setForeground(QColor("#E67E22"))
            
            table.setItem(row, 8, status_item)
            
            # Due Date
            due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"
            table.setItem(row, 9, QTableWidgetItem(due_str))
            
        self.view_layout.addWidget(table)

    def _subscribe_to_events(self):
        """Subscribe to domain events"""
        EventBus.subscribe(InvoiceCreatedEvent, self._handle_invoice_event)
        EventBus.subscribe(InvoiceUpdatedEvent, self._handle_invoice_event)
        EventBus.subscribe(InvoiceDeletedEvent, self._handle_invoice_event)
        EventBus.subscribe(BranchContextChangedEvent, self._handle_branch_changed_event)

    def _handle_branch_changed_event(self, event: BranchContextChangedEvent):
        """Handle branch context change"""
        self.current_branch_id = event.branch_id
        # Reload invoices
        QTimer.singleShot(50, self._load_invoices)

    def _handle_invoice_event(self, event):
        """Handle invoice domain events"""
        QTimer.singleShot(300, self._load_invoices)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # Use timer to let UI render first
            QTimer.singleShot(100, self._load_invoices)
            self._data_loaded = True

    def closeEvent(self, event):
        """Clean up resources"""
        self._unsubscribe_from_events()
        super().closeEvent(event)

    def _unsubscribe_from_events(self):
        """Unsubscribe from domain events"""
        EventBus.unsubscribe(InvoiceCreatedEvent, self._handle_invoice_event)
        EventBus.unsubscribe(InvoiceUpdatedEvent, self._handle_invoice_event)
        EventBus.unsubscribe(InvoiceDeletedEvent, self._handle_invoice_event)

    
    def _on_card_clicked(self, card, invoice):
        """Handle card click (toggle selection)"""
        if invoice.id in self.selected_invoices:
            self.selected_invoices.remove(invoice.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_invoices.append(invoice.id)
            self._update_card_selection_style(card, True)
            
    def _on_card_double_clicked(self, invoice):
        """Handle card double click (open details)"""
        dialog = CustomerInvoiceDetailsDialog(self.container, invoice.id, self.user, self)
        dialog.exec()
        self._load_invoices()  # Refresh after dialog closes
        
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        # Base colors
        bg_color = "#2C3E50" if dark_mode else "#FFFFFF"
        border_color = "#34495E" if dark_mode else "#BDC3C7"
        
        # Selection colors
        sel_bg = "#34495E" if dark_mode else "#EFF6FF"
        sel_border = "#3498DB" # Stay blue
        
        if is_selected:
            card.setStyleSheet(f"""
                #invoice_card {{
                    background-color: {sel_bg};
                    border: 2px solid {sel_border};
                    border-radius: 8px;
                }}
                QLabel {{
                    border: none;
                    padding: 0;
                    background: transparent;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                #invoice_card {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                }}
                #invoice_card:hover {{
                    border-color: {sel_border};
                    background-color: {bg_color};
                }}
                QLabel {{
                    border: none;
                    padding: 0;
                    background: transparent;
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
        # Need to find the grid layout in the scroll area
        scroll = self.view_layout.itemAt(0).widget()
        if isinstance(scroll, QScrollArea):
            container = scroll.widget()
            if container and container.layout():
                layout = container.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        self._update_card_selection_style(item.widget(), False)
    
    def _on_table_double_clicked(self, index, table):
        """Handle table double-click"""
        row = index.row()
        invoice_id = table.item(row, 0).data(Qt.UserRole)
        
        if invoice_id:
            # Create a dummy object with just the ID since _on_card_double_clicked only needs ID
            class InvoiceObj:
                def __init__(self, id):
                    self.id = id
            
            self._on_card_double_clicked(InvoiceObj(invoice_id))
    
    def _export_to_csv(self):
        """Export invoices to CSV"""
        if not self._current_invoice_list:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "invoices.csv", "CSV Files (*.csv)")
        
        if not path:
            return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'Invoice #', 'Date', 'Customer', 'Total', 'Paid', 'Balance', 
                    'Status', 'Due Date', 'Overdue'
                ])
                
                for invoice in self._current_invoice_list:
                    customer_name = self._get_customer_name(invoice)
                    total = Decimal(str(invoice.total))
                    paid = self._calculate_paid_amount(invoice)
                    balance = total - paid
                    date_str = invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else ""
                    due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else ""
                    overdue = self.lm.get("Common.yes", "Yes") if self._is_overdue(invoice) else self.lm.get("Common.no", "No")
                    
                    writer.writerow([
                        invoice.invoice_number,
                        date_str,
                        customer_name,
                        f"{total:.2f}",
                        f"{paid:.2f}",
                        f"{balance:.2f}",
                        invoice.payment_status,
                        due_str,
                        overdue
                    ])
            
            print(f"Exported {len(self._current_invoice_list)} invoices to CSV")
        except Exception as e:
            print(f"Error exporting CSV: {e}")
    
    def _export_to_pdf(self):
        """Export invoices to PDF report using WeasyPrint"""
        if not self._current_invoice_list:
            QMessageBox.information(
                self,
                self.lm.get("Common.info", "Info"),
                self.lm.get("Invoices.no_invoices_to_export", "No invoices to export")
            )
            return
    
        path, _ = QFileDialog.getSaveFileName(
            self, 
            self.lm.get("Invoices.export_pdf", "Save PDF"), 
            f"invoices_report_{datetime.now().strftime('%Y%m%d')}.pdf", 
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
                    .status-paid {{ color: #27AE60; font-weight: bold; }}
                    .status-unpaid {{ color: #E74C3C; font-weight: bold; }}
                    .status-partially-paid {{ color: #E67E22; font-weight: bold; }}
                    .status-overdue {{ color: #E74C3C; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Invoices.report_title", "INVOICES REPORT")}</h1>
                <div class="meta">{self.lm.get("Common.generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            """
        
            # Calculate Summary
            total_amount = Decimal('0.00')
            total_paid = Decimal('0.00')
            total_balance = Decimal('0.00')
            overdue_count = 0
            
            # Sort invoices
            sorted_invoices = sorted(self._current_invoice_list, key=lambda x: x.created_at, reverse=True)
        
            for invoice in sorted_invoices:
                total = Decimal(str(invoice.total))
                paid = self._calculate_paid_amount(invoice)
                balance = total - paid
            
                total_amount += total
                total_paid += paid
                total_balance += balance
            
                if self._is_overdue(invoice):
                    overdue_count += 1
        
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Invoices.total_invoices", "Total Invoices")}</div>
                        <div class="summary-value">{len(self._current_invoice_list)} ({self.lm.get("Invoices.overdue", "Overdue")}: {overdue_count})</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Invoices.total_amount", "Total Amount")}</div>
                        <div class="summary-value">{currency_formatter.format(total_amount)}</div>
                        <div class="summary-label">{self.lm.get("Invoices.total_paid", "Total Paid")}</div>
                        <div class="summary-value" style="color: #27AE60;">{currency_formatter.format(total_paid)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Invoices.outstanding_balance", "Outstanding Balance")}</div>
                        <div class="summary-value" style="color: #E74C3C;">{currency_formatter.format(total_balance)}</div>
                    </div>
                </div>
            """
        
            # Table Header
            html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Invoices.invoice_number", "Invoice #")}</th>
                            <th>{self.lm.get("Common.date", "Date")}</th>
                            <th>{self.lm.get("Invoices.customer", "Customer")}</th>
                            <th>{self.lm.get("Invoices.total", "Total")}</th>
                            <th>{self.lm.get("Invoices.paid", "Paid")}</th>
                            <th>{self.lm.get("Invoices.balance", "Balance")}</th>
                            <th>{self.lm.get("Invoices.status", "Status")}</th>
                            <th>{self.lm.get("Invoices.due_date", "Due Date")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
        
            # Table Rows
            for invoice in sorted_invoices:
                customer_name = self._get_customer_name(invoice)
                total = Decimal(str(invoice.total))
                paid = self._calculate_paid_amount(invoice)
                balance = total - paid
                
                date_str = invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else "N/A"
                due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"
                
                
                status_key = f"Invoices.{invoice.payment_status}_status"
                status_text = self.lm.get(status_key, invoice.payment_status.upper().replace('_', ' '))
                
                status_class = ""
                if invoice.payment_status == 'paid':
                    status_class = "status-paid"
                elif invoice.payment_status == 'unpaid':
                    status_class = "status-unpaid"
                elif invoice.payment_status == 'partially_paid':
                    status_class = "status-partially-paid"
                
                due_class = ""
                if self._is_overdue(invoice):
                    due_class = "status-overdue"
            
                html += f"""
                    <tr>
                        <td>{invoice.invoice_number}</td>
                        <td>{date_str}</td>
                        <td>{customer_name}</td>
                        <td style="text-align: right;">{currency_formatter.format(total)}</td>
                        <td style="text-align: right;">{currency_formatter.format(paid)}</td>
                        <td style="text-align: right;">{currency_formatter.format(balance)}</td>
                        <td class="{status_class}" style="text-align: center;">{status_text}</td>
                        <td class="{due_class}" style="text-align: center;">{due_str}</td>
                    </tr>
                """
            
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 20px; font-size: 8pt; color: #7F8C8D; border-top: 1px solid #BDC3C7; padding-top: 10px;">
                    {self.lm.get("Common.confidential_notice", "Confidential - For Internal Use Only")}
                </div>
            </body>
            </html>
            """
        
            # Generate PDF
            HTML(string=html).write_pdf(target=path, stylesheets=[CSS(string="")])
        
            try:
                # Try to open the file
                import subprocess
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(('open', path))
                elif platform.system() == 'Windows':    # Windows
                    os.startfile(path)
                else:                                   # linux variants
                    subprocess.call(('xdg-open', path))
            except:
                pass # Ignore if can't open
            
            QMessageBox.information(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Invoices.export_success', 'Successfully exported')} {len(self._current_invoice_list)} {self.lm.get('Invoices.invoices', 'invoices')}."
            )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Invoices.export_failed', 'Failed to export to PDF')}: {str(e)}"
            )
            
            # Calculate Summary
            total_amount = Decimal('0.00')
            total_paid = Decimal('0.00')
            total_balance = Decimal('0.00')
            overdue_count = 0
            
            for invoice in self._current_invoice_list:
                total = Decimal(str(invoice.total))
                paid = self._calculate_paid_amount(invoice)
                balance = total - paid
                
                total_amount += total
                total_paid += paid
                total_balance += balance
                
                if self._is_overdue(invoice):
                    overdue_count += 1
            
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div style="float: left; width: 30%; background: #F5F5F5; padding: 10px; border: 1px solid #DDD; margin-right: 10px;">
                        <div class="summary-label">{self.lm.get("Invoices.total_invoices", "Total Invoices")}</div>
                        <div class="summary-value">{len(self._current_invoice_list)} ({self.lm.get("Invoices.overdue", "Overdue")}: {overdue_count})</div>
                    </div>
                     <div style="float: left; width: 30%; background: #F5F5F5; padding: 10px; border: 1px solid #DDD; margin-right: 10px;">
                        <div class="summary-label">{self.lm.get("Invoices.total_amount", "Total Amount")}</div>
                        <div class="summary-value">{currency_formatter.format(total_amount)}</div>
                        <div class="summary-label">{self.lm.get("Invoices.total_paid", "Total Paid")}</div>
                        <div class="summary-value">{currency_formatter.format(total_paid)}</div>
                    </div>
                     <div style="float: left; width: 30%; background: #F5F5F5; padding: 10px; border: 1px solid #DDD;">
                        <div class="summary-label">{self.lm.get("Invoices.outstanding_balance", "Outstanding Balance")}</div>
                        <div class="summary-value">{currency_formatter.format(total_balance)}</div>
                    </div>
                    <div style="clear: both;"></div>
                </div>
                <br>
                <h3>{self.lm.get("Invoices.invoice_details", "INVOICE DETAILS")}</h3>
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Invoices.invoice_number", "Invoice #")}</th>
                            <th>{self.lm.get("Common.date", "Date")}</th>
                            <th>{self.lm.get("Invoices.customer", "Customer")}</th>
                            <th>{self.lm.get("Invoices.total", "Total")}</th>
                            <th>{self.lm.get("Invoices.paid", "Paid")}</th>
                            <th>{self.lm.get("Invoices.balance", "Balance")}</th>
                            <th>{self.lm.get("Invoices.status", "Status")}</th>
                            <th>{self.lm.get("Invoices.due_date", "Due Date")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Sort invoices
            sorted_invoices = sorted(self._current_invoice_list, key=lambda x: x.created_at, reverse=True)
            
            for invoice in sorted_invoices:
                customer_name = self._get_customer_name(invoice)
                total = Decimal(str(invoice.total))
                paid = self._calculate_paid_amount(invoice)
                balance = total - paid
                
                date_str = invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else "N/A"
                due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"
                
                
                status_key = f"Invoices.{invoice.payment_status}_status"
                status_text = self.lm.get(status_key, invoice.payment_status.upper().replace('_', ' '))
                
                status_class = ""
                if invoice.payment_status == 'paid':
                    status_class = "status-paid"
                elif invoice.payment_status == 'unpaid':
                    status_class = "status-unpaid"
                elif invoice.payment_status == 'partially_paid':
                    status_class = "status-partially-paid"
                
                due_class = ""
                if self._is_overdue(invoice):
                    due_class = "status-overdue"
                    if invoice.payment_status != 'paid':
                         # Append overdue text if needed, or rely on color. 
                         # For now just keep content as status text but color it red if overdue
                         pass
                
                html += f"""
                    <tr>
                        <td>{invoice.invoice_number}</td>
                        <td>{date_str}</td>
                        <td>{customer_name}</td>
                        <td style="text-align: right;">{currency_formatter.format(total)}</td>
                        <td style="text-align: right;">{currency_formatter.format(paid)}</td>
                        <td style="text-align: right;">{currency_formatter.format(balance)}</td>
                        <td class="{status_class}" style="text-align: center;">{status_text}</td>
                        <td class="{due_class}" style="text-align: center;">{due_str}</td>
                    </tr>
                """
                
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 20px; font-size: 8pt; color: #7F8C8D; border-top: 1px solid #BDC3C7; padding-top: 10px;">
                    {self.lm.get("Common.confidential_notice", "Confidential - For Internal Use Only")}
                </div>
            </body>
            </html>
            """
            
            HTML(string=html).write_pdf(path)
            
            print(f"Exported {len(self._current_invoice_list)} invoices to PDF")
            QMessageBox.information(self, "Export Successful", f"Successfully exported {len(self._current_invoice_list)} invoices.")
            
        except Exception as e:
            print(f"Error exporting PDF: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def _add_invoice_pdf_footer(self, pdf):
        """Add footer to invoice PDF"""
        pdf.set_draw_color(41, 128, 185)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.h - 15, 282, pdf.h - 15)
        
        pdf.set_y(-12)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        
        pdf.set_x(15)
        pdf.cell(90, 5, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align='L')
        
        pdf.set_x(105)
        pdf.cell(67, 5, txt="Confidential - For Internal Use Only", align='C')
        
        pdf.set_x(172)
        pdf.cell(90, 5, txt=f"Page {pdf.page_no()}", align='R')

    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        # Get the table widget (sender)
        table = self.sender()
        if not table:
            return
            
        # Get the item at the position
        item = table.itemAt(position)
        if not item:
            return
            
        # Get invoice ID from the first column of the row
        row = item.row()
        invoice_id = table.item(row, 0).data(Qt.UserRole)
        
        if invoice_id:
            # Find the invoice object
            invoice = next((inv for inv in self._current_invoice_list if inv.id == invoice_id), None)
            if invoice:
                self._show_context_menu(invoice)

    def _show_context_menu(self, invoice):
        """Show context menu for invoice"""
        menu = QMenu(self)
        
        # Actions
        view_action = QAction("📄 View Details", self)
        view_action.triggered.connect(lambda: self._on_card_double_clicked(invoice))
        menu.addAction(view_action)
        
        # Add Payment option if not fully paid
        if invoice.payment_status != 'paid' and invoice.payment_status != 'cancelled':
            pay_action = QAction("💰 Record Payment", self)
            pay_action.triggered.connect(lambda: self._record_payment(invoice))
            menu.addAction(pay_action)
        
        menu.addSeparator()
        
        print_action = QAction("🖨️ Print Invoice", self)
        print_action.triggered.connect(lambda: self._print_invoice(invoice))
        menu.addAction(print_action)
        
        preview_action = QAction("👁️ Preview Invoice", self)
        preview_action.triggered.connect(lambda: self._preview_invoice(invoice))
        menu.addAction(preview_action)
        
        # Show menu at cursor position
        menu.exec(self.cursor().pos())
        
    def _record_payment(self, invoice):
        """Open dialog to record payment"""
        dialog = RecordCustomerPaymentDialog(self.container, invoice, self.user, self)
        if dialog.exec():
            self._load_invoices()
        
    def _print_invoice(self, invoice):
        """Print invoice"""
        data = self._prepare_invoice_data(invoice)
        self.invoice_generator.print_invoice(data)
        
    def _preview_invoice(self, invoice):
        """Preview invoice"""
        data = self._prepare_invoice_data(invoice)
        self.invoice_generator.preview_invoice(data)
        
    def _prepare_invoice_data(self, invoice):
        """Prepare invoice data for generator"""
        # Get customer info
        customer_name = self.lm.get("Common.unknown", "Unknown")
        customer_phone = self.lm.get("Common.na", "N/A")
        customer_address = self.lm.get("Common.na", "N/A")
        
        if getattr(invoice, 'device', None) and getattr(invoice.device, 'customer', None):
            customer = invoice.device.customer
            customer_name = customer.name
            customer_phone = customer.phone or self.lm.get("Common.na", "N/A")
            customer_address = customer.address or self.lm.get("Common.na", "N/A")
        else:
            # Try to get from items -> ticket
            for item in invoice.items:
                if item.item_type == 'service':
                    ticket = self.ticket_controller.get_ticket(item.item_id)
                    if ticket and ticket.customer:
                        customer_name = ticket.customer.name
                        customer_phone = ticket.customer.phone or self.lm.get("Common.na", "N/A")
                        customer_address = ticket.customer.address or self.lm.get("Common.na", "N/A")
                    break
        
        # Prepare items
        items_data = []
        for item in invoice.items:
            # Get description based on item type
            description = self.lm.get("Common.na", "N/A")
            if item.item_type == 'part':
                # Use get_part_by_id instead of get_part
                part = self.part_service.get_part_by_id(item.item_id)
                if part:
                    description = part.name
            elif item.item_type == 'service':
                # For services, we could look up the ticket or use a generic description
                description = self.lm.get("Invoices.service", "Service")
            
            items_data.append({
                'description': description,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.total)
            })
            
        # Calculate paid amount
        amount_paid = float(self._calculate_paid_amount(invoice))
        
        # Calculate tax amount safely - check if attribute exists
        tax_amount = 0.0
        if hasattr(invoice, 'tax_amount') and invoice.tax_amount is not None:
            tax_amount = float(invoice.tax_amount)
        elif hasattr(invoice, 'tax') and invoice.tax is not None:
            tax_amount = float(invoice.tax)
        
        # Calculate discount amount safely
        discount_amount = 0.0
        if hasattr(invoice, 'discount_amount') and invoice.discount_amount is not None:
            discount_amount = float(invoice.discount_amount)
        elif hasattr(invoice, 'discount') and invoice.discount is not None:
            discount_amount = float(invoice.discount)
        
        # Calculate subtotal safely
        subtotal = float(invoice.total)
        if hasattr(invoice, 'subtotal') and invoice.subtotal is not None:
            subtotal = float(invoice.subtotal)
        else:
            # Calculate subtotal from items if not available
            subtotal = sum(float(item.total) for item in invoice.items)
        
        # Try to find linked ticket for ticket number
        ticket_number_display = f"T-{invoice.id}" # Default fallback
        
        for item in invoice.items:
            if item.item_type == 'service':
                try:
                    ticket = self.ticket_controller.get_ticket(item.item_id)
                    if ticket:
                        # If ticket has a specific ticket_number field, use it
                        if hasattr(ticket, 'ticket_number') and ticket.ticket_number:
                            ticket_number_display = str(ticket.ticket_number)
                        # Otherwise use ticket ID
                        elif hasattr(ticket, 'id'):
                            ticket_number_display = f"T-{ticket.id}"
                        break
                except Exception:
                    pass

        # Get user settings for print format
        print_format = 'Standard A5'
        if self.user and self.container and self.container.settings_service:
            try:
                settings = self.container.settings_service.get_user_settings(self.user.id)
                print_format = settings.get('print_format', 'Standard A5')
            except Exception:
                pass
        
        return {
            'invoice_number': invoice.invoice_number,
            'date': invoice.created_at.strftime("%B %d, %Y"),
            'ticket_number': ticket_number_display,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_address': customer_address,
            'device': f"{invoice.device_brand} {invoice.device_model}" if invoice.device_brand else "N/A",
            'issue': invoice.error_description or "N/A",
            'items': items_data,
            'subtotal': subtotal,
            'tax': tax_amount,
            'discount': discount_amount,
            'total': float(invoice.total),
            'amount_paid': amount_paid,
            'balance_due': float(invoice.total) - amount_paid,
            'print_format': print_format
        }
