# src/app/views/financial/credit_note_list_tab.py
"""
Modern Credit Note List Tab with enhanced UI features:
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
from config.constants import UIColors, CreditNoteStatus
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class CreditNoteListTab(QWidget):
    """Modern credit note management interface"""
    
    data_changed = Signal()
    
    def __init__(self, container, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.user = user
        self.credit_note_service = container.credit_note_service
        self.current_view = 'cards'
        self.lm = language_manager
        self.cf = currency_formatter
        
        self._setup_ui()
        self._connect_signals()
        # self._load_credit_notes()
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
    
    def _create_header(self):
        """Create header with title and view switcher"""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("CreditNotes.credit_notes_title", "Credit Notes"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("CreditNotes.view", "View") + ":")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(f"📇 {self.lm.get('CreditNotes.cards_view', 'Cards')}")
        self.list_view_btn = QPushButton(f"📋 {self.lm.get('CreditNotes.list_view', 'List')}")
        
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
        self.total_credits_card = self._create_summary_card(self.lm.get("CreditNotes.total_credits", "Total Credits"), "0", "#3B82F6", "💳")
        self.available_card = self._create_summary_card(self.lm.get("CreditNotes.available", "Available"), self.cf.format(0), "#10B981", "✅")
        self.pending_card = self._create_summary_card(self.lm.get("CreditNotes.pending", "Pending"), "0", "#F59E0B", "⏳")
        self.expired_card = self._create_summary_card(self.lm.get("CreditNotes.expired", "Expired"), "0", "#EF4444", "❌")
        
        layout.addWidget(self.total_credits_card)
        layout.addWidget(self.available_card)
        layout.addWidget(self.pending_card)
        layout.addWidget(self.expired_card)
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
        self.search_input.setPlaceholderText(self.lm.get("CreditNotes.search_placeholder", "🔍 Search by credit note #, supplier..."))
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
        layout.addWidget(QLabel(self.lm.get("CreditNotes.status", "Status") + ":"))
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("CreditNotes.all", "All"), None)
        self.status_filter.addItem(self.lm.get("CreditNotes.pending", "Pending"), CreditNoteStatus.PENDING)
        self.status_filter.addItem(self.lm.get("CreditNotes.applied", "Applied"), CreditNoteStatus.APPLIED)
        self.status_filter.addItem(self.lm.get("CreditNotes.expired", "Expired"), CreditNoteStatus.EXPIRED)
        self.status_filter.setMinimumWidth(150)
        layout.addWidget(self.status_filter)
        
        layout.addStretch()
        
        return layout
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Apply credit button
        self.apply_credit_btn = QPushButton(self.lm.get("CreditNotes.apply_credit", "💰 Apply Credit"))
        self.apply_credit_btn.setStyleSheet("""
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
        layout.addWidget(self.apply_credit_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('CreditNotes.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_credit_notes)
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
        self.credit_notes_table = QTableWidget()
        self.credit_notes_table.setColumnCount(9)
        headers = [
            "✓",
            self.lm.get("CreditNotes.credit_note_number", "Credit Note #"),
            self.lm.get("CreditNotes.supplier", "Supplier"),
            self.lm.get("CreditNotes.return_number", "Return #"),
            self.lm.get("CreditNotes.issue_date", "Issue Date"),
            self.lm.get("CreditNotes.credit_amount", "Credit Amount"),
            self.lm.get("CreditNotes.applied_amount", "Applied"),
            self.lm.get("CreditNotes.remaining", "Remaining"),
            self.lm.get("CreditNotes.status_header", "Status")
        ]
        self.credit_notes_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.credit_notes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.credit_notes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.credit_notes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.credit_notes_table.setAlternatingRowColors(True)
        self.credit_notes_table.setColumnWidth(0, 40)
        self.credit_notes_table.verticalHeader().setVisible(False)
        self.credit_notes_table.setShowGrid(False)
        
        # Table Styling
        self.credit_notes_table.setStyleSheet("""
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
        
        return self.credit_notes_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search)
        self.status_filter.currentIndexChanged.connect(self._on_filter)
        
        # Actions
        self.apply_credit_btn.clicked.connect(self._on_apply_credit)
        
        # Table double click
        self.credit_notes_table.doubleClicked.connect(self._on_table_double_click)
    
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
        
        # Reload credit notes for the new view
        self._load_credit_notes()
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status badge"""
        status_colors = {
            CreditNoteStatus.PENDING: '#F59E0B',   # Orange
            CreditNoteStatus.APPLIED: '#10B981',   # Green
            CreditNoteStatus.EXPIRED: '#EF4444'    # Red
        }
        return status_colors.get(status, '#6B7280')
    
    def _load_credit_notes(self):
        """Load and display credit notes"""
        try:
            # Get filter
            status_filter = self.status_filter.currentData()
            
            # Get all credit notes
            if status_filter:
                credit_notes = self.credit_note_service.list_credit_notes(status=status_filter)
            else:
                credit_notes = self.credit_note_service.list_credit_notes()
            
            # Apply search filter
            search_term = self.search_input.text().strip()
            if search_term:
                search_lower = search_term.lower()
                credit_notes = [
                    cn for cn in credit_notes
                    if (search_lower in cn.credit_note_number.lower() or
                        search_lower in (cn.supplier.name if cn.supplier else '').lower())
                ]
            
            # Update summary
            self._update_summary(credit_notes)
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(credit_notes)
            elif self.current_view == 'list':
                self._populate_list_view(credit_notes)
            
        except Exception as e:
            print(f"Error loading credit notes: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_summary(self, credit_notes: List):
        """Update summary cards"""
        total = len(credit_notes)
        total_available = Decimal('0.00')
        pending_count = 0
        expired_count = 0
        
        for cn in credit_notes:
            remaining = float(cn.remaining_credit)
            if cn.status == CreditNoteStatus.PENDING and remaining > 0:
                total_available += Decimal(str(remaining))
                pending_count += 1
            if cn.status == CreditNoteStatus.EXPIRED:
                expired_count += 1
        
        self._update_card_value(self.total_credits_card, str(total))
        self._update_card_value(self.available_card, self.cf.format(total_available))
        self._update_card_value(self.pending_card, str(pending_count))
        self._update_card_value(self.expired_card, str(expired_count))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, credit_notes: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add credit note cards
        for idx, credit_note in enumerate(credit_notes):
            row = idx // 3
            col = idx % 3
            card = self._create_credit_note_card(credit_note)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_credit_note_card(self, credit_note):
        """Create a credit note card widget"""
        card = QFrame()
        card.setObjectName("creditNoteCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(200)
        card.setMaximumHeight(240)
        
        status_color = self._get_status_color(credit_note.status)
        
        # Style card
        card.setStyleSheet(f"""
            QFrame#creditNoteCard {{
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#creditNoteCard:hover {{
                border-color: {status_color};
                background-color: #374151;
            }}
        """)
        
        # Store credit note data
        card.credit_note_id = credit_note.id
        card.mousePressEvent = lambda event: self._on_card_clicked(credit_note)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Credit Note # and status
        header = QHBoxLayout()
        
        cn_label = QLabel(credit_note.credit_note_number)
        cn_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(cn_label)
        
        header.addStretch()
        
        status_badge = QLabel(credit_note.status.upper())
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
        if credit_note.supplier:
            supplier_label = QLabel(f"🏢 {credit_note.supplier.name}")
            supplier_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
            layout.addWidget(supplier_label)
        
        # Return number
        if credit_note.purchase_return:
            return_label = QLabel(f"↩️ {self.lm.get('CreditNotes.return', 'Return')}: {credit_note.purchase_return.return_number}")
            return_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(return_label)
        
        # Issue date
        issue_date = credit_note.issue_date.strftime("%Y-%m-%d") if credit_note.issue_date else "N/A"
        date_label = QLabel(f"📅 {issue_date}")
        date_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(date_label)
        
        layout.addStretch()
        
        # Footer - Amounts
        footer = QVBoxLayout()
        footer.setSpacing(4)
        
        credit_label = QLabel(f"{self.lm.get('CreditNotes.credit', 'Credit')}: {self.cf.format(float(credit_note.credit_amount))}")
        credit_label.setStyleSheet("color: #3B82F6; font-size: 14px; font-weight: bold;")
        footer.addWidget(credit_label)
        
        remaining = float(credit_note.remaining_credit)
        remaining_label = QLabel(f"{self.lm.get('CreditNotes.remaining', 'Remaining')}: {self.cf.format(remaining)}")
        remaining_color = "#10B981" if remaining > 0 else "#6B7280"
        remaining_label.setStyleSheet(f"color: {remaining_color}; font-size: 16px; font-weight: bold;")
        footer.addWidget(remaining_label)
        
        layout.addLayout(footer)
        
        return card
    
    def _populate_list_view(self, credit_notes: List):
        """Populate list view"""
        self.credit_notes_table.setRowCount(len(credit_notes))
        
        for row, credit_note in enumerate(credit_notes):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.credit_notes_table.setItem(row, 0, checkbox_item)
            
            # Credit note number
            cn_item = QTableWidgetItem(credit_note.credit_note_number)
            cn_item.setData(Qt.UserRole, credit_note.id)
            self.credit_notes_table.setItem(row, 1, cn_item)
            
            # Supplier
            supplier_name = credit_note.supplier.name if credit_note.supplier else "N/A"
            self.credit_notes_table.setItem(row, 2, QTableWidgetItem(supplier_name))
            
            # Return number
            return_number = credit_note.purchase_return.return_number if credit_note.purchase_return else "N/A"
            self.credit_notes_table.setItem(row, 3, QTableWidgetItem(return_number))
            
            # Issue date
            issue_date = credit_note.issue_date.strftime("%Y-%m-%d") if credit_note.issue_date else "N/A"
            self.credit_notes_table.setItem(row, 4, QTableWidgetItem(issue_date))
            
            # Credit amount
            self.credit_notes_table.setItem(row, 5, QTableWidgetItem(self.cf.format(float(credit_note.credit_amount))))
            
            # Applied amount
            self.credit_notes_table.setItem(row, 6, QTableWidgetItem(self.cf.format(float(credit_note.applied_amount))))
            
            # Remaining credit
            remaining = float(credit_note.remaining_credit)
            remaining_item = QTableWidgetItem(self.cf.format(remaining))
            if remaining > 0:
                remaining_item.setForeground(QColor("#10B981"))
            self.credit_notes_table.setItem(row, 7, remaining_item)
            
            # Status
            status_item = QTableWidgetItem(credit_note.status.upper())
            status_item.setForeground(QColor(self._get_status_color(credit_note.status)))
            self.credit_notes_table.setItem(row, 8, status_item)
    
    def _on_search(self, text):
        """Handle search"""
        QTimer.singleShot(300, self._load_credit_notes)
    
    def _on_filter(self):
        """Handle filter change"""
        self._load_credit_notes()
    
    def _on_card_clicked(self, credit_note):
        """Handle card click"""
        from views.inventory.financial.credit_note_details_dialog import CreditNoteDetailsDialog
        dialog = CreditNoteDetailsDialog(self.container, credit_note, parent=self)
        dialog.exec()
    
    def _on_table_double_click(self, index):
        """Handle table double click"""
        credit_note_id = self.credit_notes_table.item(index.row(), 1).data(Qt.UserRole)
        credit_note = self.credit_note_service.get_credit_note(credit_note_id)
        if credit_note:
            from views.inventory.financial.credit_note_details_dialog import CreditNoteDetailsDialog
            dialog = CreditNoteDetailsDialog(self.container, credit_note, parent=self)
            dialog.exec()
    
    def _on_apply_credit(self):
        """Handle apply credit button"""
        selected_rows = self.credit_notes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.lm.get("CreditNotes.no_selection", "No Selection"), self.lm.get("CreditNotes.select_credit_to_apply", "Please select a credit note to apply."))
            return
        
        row = selected_rows[0].row()
        credit_note_id = self.credit_notes_table.item(row, 1).data(Qt.UserRole)
        
        # Get credit note
        credit_note = self.credit_note_service.get_credit_note(credit_note_id)
        if not credit_note:
            QMessageBox.warning(self, self.lm.get("CreditNotes.error", "Error"), self.lm.get("CreditNotes.credit_note_not_found", "Credit note not found."))
            return
        
        # Check if credit is available
        if float(credit_note.remaining_credit) <= 0:
            QMessageBox.warning(self, self.lm.get("CreditNotes.no_credit_available", "No Credit Available"), self.lm.get("CreditNotes.no_remaining_credit", "This credit note has no remaining credit to apply."))
            return
        
        if credit_note.status == CreditNoteStatus.EXPIRED:
            QMessageBox.warning(self, self.lm.get("CreditNotes.expired_credit", "Expired Credit"), self.lm.get("CreditNotes.expired_cannot_apply", "This credit note has expired and cannot be applied."))
            return
        
        # Open apply credit dialog
        try:
            from views.inventory.financial.apply_credit_dialog import ApplyCreditDialog
            dialog = ApplyCreditDialog(self.container, credit_note, user=self.user, parent=self)
            if dialog.exec():
                self._load_credit_notes()  # Refresh after applying credit
                self.data_changed.emit()   # Notify parent to refresh other tabs
        except Exception as e:
            import traceback
            error_msg = f"Error opening Apply Credit dialog:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, self.lm.get("CreditNotes.error", "Error"), error_msg)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_credit_notes)
            self._data_loaded = True
