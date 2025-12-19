# src/app/views/technician/technicians.py
"""
Modern Technician Management Tab with enhanced UI features:
- Card/List view toggle
- Summary cards with key metrics
- Compensation tracking (salary, commission)
- Performance metrics display
- Advanced filtering
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor, QPixmap
from typing import List
from decimal import Decimal
from models.technician import Technician
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class TechniciansTab(QWidget):
    """Modern technician management interface"""
    
    technician_selected = Signal(Technician)
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        self.cf = currency_formatter
        self.technician_controller = container.technician_controller
        self.current_view = 'cards'
        self.selected_technicians = []
        
        self._setup_ui()
        self._connect_signals()
        # self.load_technicians() - Moved to lazy loading
        self._data_loaded = False

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            QTimer.singleShot(100, self.load_technicians)
            self._data_loaded = True
    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(self.lm.get("Users.technicians_title", "Technicians"))
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action Buttons
        self.dashboard_btn = QPushButton(self.lm.get("Users.performance_dashboard", "Performance Dashboard"))
        self.dashboard_btn.clicked.connect(self._show_dashboard)
        header_layout.addWidget(self.dashboard_btn)
        
        self.bonus_btn = QPushButton(self.lm.get("Users.manage_bonuses", "Manage Bonuses"))
        self.bonus_btn.clicked.connect(self._show_bonus_dialog)
        header_layout.addWidget(self.bonus_btn)
        
        self.add_btn = QPushButton(self.lm.get("Users.add_technician", "Add Technician"))
        self.add_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.add_btn.clicked.connect(self.show_add_technician_dialog) # Connect to existing add dialog
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Summary Cards
        summary_layout = self._create_summary_cards()
        layout.addLayout(summary_layout)
        
        # Filters and Search
        filter_search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Users.search_placeholder", "🔍 Search technicians..."))
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
        filter_search_layout.addWidget(self.search_input)
        
        filter_search_layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Common.view", "View:"))
        filter_search_layout.addWidget(view_label)
        
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
            filter_search_layout.addWidget(btn)
        
        layout.addLayout(filter_search_layout)
        
        # Stacked widget for different views
        self.view_stack = QStackedWidget()
        
        # Create different view widgets
        self.cards_view = self._create_cards_view()
        self.list_view = self._create_list_view()
        
        self.view_stack.addWidget(self.cards_view)
        self.view_stack.addWidget(self.list_view)
        
        layout.addWidget(self.view_stack, 1)
    
    def _create_summary_cards(self):
        """Create summary cards section"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Initialize summary cards
        self.total_techs_card = self._create_summary_card(self.lm.get("Technicians.total_technicians", "Total Technicians"), "0", "#3B82F6", "👥")
        self.active_techs_card = self._create_summary_card(self.lm.get("Technicians.active", "Active"), "0", "#10B981", "✅")
        self.monthly_payroll_card = self._create_summary_card(self.lm.get("Technicians.monthly_payroll", "Monthly Payroll"), "$0.00", "#8B5CF6", "💰")
        self.avg_performance_card = self._create_summary_card(self.lm.get("Technicians.avg_performance", "Avg Performance"), "0", "#F59E0B", "⭐")
        
        layout.addWidget(self.total_techs_card)
        layout.addWidget(self.active_techs_card)
        layout.addWidget(self.monthly_payroll_card)
        layout.addWidget(self.avg_performance_card)
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
        card.setFixedHeight(100)
        
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
    
    def _create_cards_view(self):
        """Create cards view widget"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        self.cards_layout = QGridLayout(container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # Install event filter for click-to-deselect
        scroll.viewport().installEventFilter(self)
        
        scroll.setWidget(container)
        return scroll
    
    def _create_list_view(self):
        """Create traditional list/table view"""
        self.technicians_table = QTableWidget()
        self.technicians_table.setColumnCount(9)
        headers = [
            self.lm.get("Common.checkbox_header", "✓"),
            self.lm.get("Common.id_header", "ID"),
            self.lm.get("Common.name_header", "Name"),
            self.lm.get("Technicians.certification_header", "Certification"),
            self.lm.get("Technicians.specialization_header", "Specialization"),
            self.lm.get("Technicians.salary_header", "Salary"),
            self.lm.get("Technicians.commission_header", "Commission %"),
            self.lm.get("Common.status_header", "Status"),
            self.lm.get("Technicians.joined_header", "Joined")
        ]
        self.technicians_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.technicians_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        
        self.technicians_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.technicians_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.technicians_table.setAlternatingRowColors(True)
        self.technicians_table.setColumnWidth(0, 40)
        self.technicians_table.setColumnWidth(1, 60)
        self.technicians_table.verticalHeader().setVisible(False)
        self.technicians_table.setShowGrid(False)
        
        # Table Styling
        self.technicians_table.setStyleSheet("""
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
        
        return self.technicians_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_search)
        # self.status_filter.currentTextChanged.connect(self._on_filter) # Removed status filter combobox
        
        # Table double click
        self.technicians_table.cellDoubleClicked.connect(self._on_table_double_click)
    
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
        
        # Reload technicians for the new view
        self.load_technicians()
    
    def _get_status_color(self, is_active: bool) -> str:
        """Get color for status badge"""
        return "#10B981" if is_active else "#6B7280"
    
    def load_technicians(self):
        """Load and display technicians"""
        try:
            search_term = self.search_input.text()
            technicians = self.technician_controller.search_technicians(search_term)
            
            # Apply status filter (if re-introduced, otherwise remove)
            # status_filter = self.status_filter.currentText()
            # if status_filter == "Active":
            #     technicians = [t for t in technicians if t.is_active]
            # elif status_filter == "Inactive":
            #     technicians = [t for t in technicians if not t.is_active]
            
            # Update summary
            self._update_summary(technicians)
            
            # Update current view
            if self.current_view == 'cards':
                self._populate_cards_view(technicians)
            elif self.current_view == 'list':
                self._populate_list_view(technicians)
        
        except Exception as e:
            print(f"Error loading technicians: {e}")
    
    def _update_summary(self, technicians: List):
        """Update summary cards"""
        total = len(technicians)
        active = sum(1 for t in technicians if t.is_active)
        monthly_payroll = sum(Decimal(str(t.salary or 0)) for t in technicians if t.is_active)
        
        # Calculate average performance (placeholder - will be enhanced later)
        avg_performance = 0  # TODO: Calculate from ticket data
        
        self._update_card_value(self.total_techs_card, str(total))
        self._update_card_value(self.active_techs_card, str(active))
        self._update_card_value(self.monthly_payroll_card, self.cf.format(monthly_payroll))
        self._update_card_value(self.avg_performance_card, str(avg_performance))
    
    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)
    
    def _populate_cards_view(self, technicians: List):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add technician cards
        for idx, tech in enumerate(technicians):
            row = idx // 3
            col = idx % 3
            card = self._create_technician_card(tech)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_technician_card(self, tech):
        """Create a technician card widget"""
        card = QFrame()
        card.setObjectName("techCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(220)
        card.setMaximumHeight(260)
        
        status_color = self._get_status_color(tech.is_active)
        
        # Style card
        card.setStyleSheet(f"""
            QFrame#techCard {{
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#techCard:hover {{
                border-color: {status_color};
                background-color: #374151;
            }}
        """)
        
        # Store tech data
        card.tech_id = tech.id
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, tech)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
                
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(tech)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        # Add context menu support
        card.setContextMenuPolicy(Qt.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos: self._show_card_context_menu(card, tech, pos))
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Name and status
        header = QHBoxLayout()
        
        name_label = QLabel(tech.full_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(name_label)
        
        header.addStretch()
        
        status_text = self.lm.get("Common.active", "ACTIVE") if tech.is_active else self.lm.get("Common.inactive", "INACTIVE")
        status_badge = QLabel(status_text)
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
        
        # Professional info
        if tech.specialization:
            spec_label = QLabel(f"🔧 {tech.specialization}")
            spec_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
            layout.addWidget(spec_label)
        
        if tech.certification:
            cert_label = QLabel(f"📜 {tech.certification}")
            cert_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            layout.addWidget(cert_label)
        
        # Contact info
        if tech.email:
            email_label = QLabel(f"📧 {tech.email}")
            email_label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
            layout.addWidget(email_label)
        
        if tech.phone:
            phone_label = QLabel(f"📱 {tech.phone}")
            phone_label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
            layout.addWidget(phone_label)
        
        layout.addStretch()
        
        # Footer - Compensation
        footer = QVBoxLayout()
        footer.setSpacing(4)
        
        salary_label = QLabel(f"{self.lm.get('Technicians.salary', 'Salary')}: {self.cf.format(float(tech.salary))}/mo")
        salary_label.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
        footer.addWidget(salary_label)
        
        if tech.commission_rate and float(tech.commission_rate) > 0:
            commission_label = QLabel(f"{self.lm.get('Technicians.commission', 'Commission')}: {float(tech.commission_rate)}%")
            commission_label.setStyleSheet("color: #3B82F6; font-size: 12px; font-weight: bold;")
            footer.addWidget(commission_label)
        
        layout.addLayout(footer)
        
        # Initial style
        self._update_card_selection_style(card, tech.id in self.selected_technicians)
        
        return card
    
    def _populate_list_view(self, technicians: List):
        """Populate list view"""
        self.technicians_table.setRowCount(len(technicians))
        
        for row, tech in enumerate(technicians):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.technicians_table.setItem(row, 0, checkbox_item)
            
            # ID
            id_item = QTableWidgetItem(str(tech.id))
            id_item.setData(Qt.UserRole, tech.id)
            self.technicians_table.setItem(row, 1, id_item)
            
            # Name
            self.technicians_table.setItem(row, 2, QTableWidgetItem(tech.full_name))
            
            # Certification
            self.technicians_table.setItem(row, 3, QTableWidgetItem(tech.certification or ""))
            
            # Specialization
            self.technicians_table.setItem(row, 4, QTableWidgetItem(tech.specialization or ""))
            
            # Salary
            salary_item = QTableWidgetItem(self.cf.format(float(tech.salary)))
            salary_item.setForeground(QColor("#10B981"))
            self.technicians_table.setItem(row, 5, salary_item)
            
            # Commission
            commission_item = QTableWidgetItem(f"{float(tech.commission_rate)}%")
            commission_item.setForeground(QColor("#3B82F6"))
            self.technicians_table.setItem(row, 6, commission_item)
            
            # Status
            status_text = self.lm.get("Common.active", "Active") if tech.is_active else self.lm.get("Common.inactive", "Inactive")
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(self._get_status_color(tech.is_active)))
            self.technicians_table.setItem(row, 7, status_item)
            
            # Joined date
            joined = tech.joined_at.strftime("%Y-%m-%d") if tech.joined_at else "N/A"
            self.technicians_table.setItem(row, 8, QTableWidgetItem(joined))
    
    def _on_search(self, text):
        """Handle search"""
        QTimer.singleShot(300, self.load_technicians)
    
    def _on_filter(self):
        """Handle filter change"""
        self.load_technicians()
    
    def _on_card_clicked(self, card, tech):
        """Handle card click (toggle selection)"""
        if tech.id in self.selected_technicians:
            self.selected_technicians.remove(tech.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_technicians.append(tech.id)
            self._update_card_selection_style(card, True)
            
    def _on_card_double_clicked(self, tech):
        """Handle card double click (open details)"""
        self.show_technician_details(tech)
            
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        # Get status color for hover effect
        tech_id = getattr(card, 'tech_id', None)
        status_color = "#10B981" # Default green
        
        # Try to find status badge to get correct color if possible, or default
        # Ideally we'd pass the tech object or status, but for now we use default or extract
        
        if is_selected:
            card.setStyleSheet("""
                QFrame#techCard {
                    background-color: #374151;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        else:
            # We need to preserve the hover effect with dynamic color
            # Since we can't easily access the specific color here without passing it,
            # we'll use a generic hover color or try to reconstruct it.
            # For simplicity in this refactor, we'll use a standard hover color
            card.setStyleSheet("""
                QFrame#techCard {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame#techCard:hover {
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
        self.selected_technicians.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
    
    def eventFilter(self, obj, event):
        """Event filter to handle click-to-deselect"""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Check if click was on the viewport (background)
                if obj == self.cards_view.viewport():
                    self._deselect_all()
        return super().eventFilter(obj, event)
    
    def _show_card_context_menu(self, card, tech, pos):
        """Show context menu for technician card"""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        view_action = menu.addAction(f"👁️ {self.lm.get('Common.view_details', 'View Details')}")
        view_action.triggered.connect(lambda: self.show_technician_details(tech))
        
        menu.addSeparator()
        
        edit_action = menu.addAction(f"✏️ {self.lm.get('Common.edit', 'Edit')}")
        edit_action.triggered.connect(lambda: self._edit_technician(tech))
        
        if tech.is_active:
            deactivate_action = menu.addAction(f"🚫 {self.lm.get('Users.deactivate', 'Deactivate')}")
            deactivate_action.triggered.connect(lambda: self._toggle_technician_status(tech))
        else:
            activate_action = menu.addAction(f"✅ {self.lm.get('Users.activate', 'Activate')}")
            activate_action.triggered.connect(lambda: self._toggle_technician_status(tech))
        
        menu.addSeparator()
        
        delete_action = menu.addAction(f"🗑️ {self.lm.get('Common.delete', 'Delete')}")
        delete_action.triggered.connect(lambda: self._delete_technician(tech))
        
        menu.exec(card.mapToGlobal(pos))
    
    def _toggle_technician_status(self, tech):
        """Toggle technician active/inactive status"""
        try:
            new_status = not tech.is_active
            self.technician_controller.update_technician(tech.id, {'is_active': new_status})
            status_text = self.lm.get("Users.activated", "activated") if new_status else self.lm.get("Users.deactivated", "deactivated")
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), f"{self.lm.get('Users.technician', 'Technician')} {status_text} {self.lm.get('Common.successfully', 'successfully')}")
            self.load_technicians()
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.error_occurred', 'An error occurred')}: {str(e)}")
    
    def _on_table_double_click(self, row, column):
        """Handle table double click"""
        tech_id = int(self.technicians_table.item(row, 1).text())
        technician = self.technician_controller.get_technician(tech_id)
        if technician:
            self.show_technician_details(technician)
    
    def show_technician_details(self, technician):
        """Show technician details dialog"""
        from views.technician.technician_details_dialog import TechnicianDetailsDialog
        dialog = TechnicianDetailsDialog(self.container, technician, parent=self)
        dialog.exec()
        self.load_technicians()  # Refresh after dialog closes
    
    def show_add_technician_dialog(self):
        """Show dialog to add new technician with modern compact UI"""
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QGridLayout
        from views.components.money_input import MoneyInput
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Technicians.add_new_technician", "Add New Technician"))
        dialog.setFixedSize(650, 540)
        
        # Modern dark theme styling
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1F2937;
            }
            QLabel {
                color: #E5E7EB;
            }
            QLineEdit {
                background-color: #374151;
                border: 2px solid #4B5563;
                border-radius: 6px;
                padding: 8px 10px;
                color: #F9FAFB;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: #4B5563;
            }
            QLineEdit:hover {
                border-color: #6B7280;
            }
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form in grid layout for compactness
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)
        
        row = 0
        
        # Personal Information - 2 columns
        personal_header = QLabel("👤 " + self.lm.get("Common.personal_information", "Personal Information"))
        personal_header.setStyleSheet("font-weight: bold; color: #3B82F6; font-size: 14px; padding-top: 5px;")
        form_layout.addWidget(personal_header, row, 0, 1, 4)
        row += 1
        
        # Full Name (spans 2 columns)
        full_name_label = QLabel("✏️ " + self.lm.get("Common.full_name", "Full Name") + " *")
        full_name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        full_name_input = QLineEdit()
        full_name_input.setPlaceholderText(self.lm.get("Common.enter_full_name", "Enter full name"))
        form_layout.addWidget(full_name_label, row, 0)
        form_layout.addWidget(full_name_input, row, 1, 1, 3)
        row += 1
        
        # Email and Phone in same row
        email_label = QLabel("📧 " + self.lm.get("Common.email", "Email"))
        email_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        email_input = QLineEdit()
        email_input.setPlaceholderText("example@gmail.com")
        email_regex = QRegularExpression(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        email_validator = QRegularExpressionValidator(email_regex)
        email_input.setValidator(email_validator)
        
        phone_label = QLabel("📱 " + self.lm.get("Common.phone", "Phone"))
        phone_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("09xxxxxxxxx")
        phone_regex = QRegularExpression(r"^(\+?959|09)\d{7,9}$")
        phone_validator = QRegularExpressionValidator(phone_regex)
        phone_input.setValidator(phone_validator)
        
        form_layout.addWidget(email_label, row, 0)
        form_layout.addWidget(email_input, row, 1)
        form_layout.addWidget(phone_label, row, 2)
        form_layout.addWidget(phone_input, row, 3)
        row += 1
        
        # Address (spans 2 columns)
        address_label = QLabel("📍 " + self.lm.get("Common.address", "Address"))
        address_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        address_input = QLineEdit()
        address_input.setPlaceholderText(self.lm.get("Common.enter_address", "Enter address"))
        form_layout.addWidget(address_label, row, 0)
        form_layout.addWidget(address_input, row, 1, 1, 3)
        row += 1
        
        # Professional Details
        professional_header = QLabel("🎓 " + self.lm.get("Technicians.professional_details", "Professional Details"))
        professional_header.setStyleSheet("font-weight: bold; color: #8B5CF6; font-size: 14px; padding-top: 5px;")
        form_layout.addWidget(professional_header, row, 0, 1, 4)
        row += 1
        
        # Certification and Specialization in same row
        cert_label = QLabel("📜 " + self.lm.get("Technicians.certification", "Certification"))
        cert_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        certification_input = QLineEdit()
        certification_input.setPlaceholderText(self.lm.get("Technicians.enter_certification", "Enter certification"))
        
        spec_label = QLabel("🔧 " + self.lm.get("Technicians.specialization", "Specialization"))
        spec_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        specialization_input = QLineEdit()
        specialization_input.setPlaceholderText(self.lm.get("Technicians.enter_specialization", "Enter specialization"))
        
        form_layout.addWidget(cert_label, row, 0)
        form_layout.addWidget(certification_input, row, 1)
        form_layout.addWidget(spec_label, row, 2)
        form_layout.addWidget(specialization_input, row, 3)
        row += 1
        
        # Compensation
        compensation_header = QLabel("💰 " + self.lm.get("Technicians.compensation", "Compensation"))
        compensation_header.setStyleSheet("font-weight: bold; color: #10B981; font-size: 14px; padding-top: 5px;")
        form_layout.addWidget(compensation_header, row, 0, 1, 4)
        row += 1
        
        # Salary
        salary_label = QLabel("💵 " + self.lm.get("Technicians.base_salary", "Base Salary"))
        salary_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        salary_container = QWidget()
        salary_layout = QHBoxLayout(salary_container)
        salary_layout.setContentsMargins(0, 0, 0, 0)
        salary_layout.setSpacing(8)
        
        salary_input = MoneyInput()
        salary_input.setPlaceholderText("0.00")
        
        # Remove the regex validator since we're handling formatting manually
        salary_layout.addWidget(salary_input)
        
        salary_currency = QLabel("Ks")
        salary_currency.setStyleSheet("""
            background-color: #065F46;
            color: #10B981;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)
        salary_layout.addWidget(salary_currency)
        
        form_layout.addWidget(salary_label, row, 0)
        form_layout.addWidget(salary_container, row, 1)
        
        # Commission
        commission_label = QLabel("📊 " + self.lm.get("Technicians.commission_rate", "Commission Rate"))
        commission_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        commission_container = QWidget()
        commission_layout = QHBoxLayout(commission_container)
        commission_layout.setContentsMargins(0, 0, 0, 0)
        commission_layout.setSpacing(8)
        
        commission_input = QLineEdit()
        commission_input.setPlaceholderText("0.00")
        commission_regex = QRegularExpression(r"^\d+(\.\d{0,2})?$")
        commission_validator = QRegularExpressionValidator(commission_regex)
        commission_input.setValidator(commission_validator)
        commission_layout.addWidget(commission_input)
        
        commission_percent = QLabel("%")
        commission_percent.setStyleSheet("""
            background-color: #1E3A8A;
            color: #3B82F6;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)
        commission_layout.addWidget(commission_percent)
        
        form_layout.addWidget(commission_label, row, 2)
        form_layout.addWidget(commission_container, row, 3)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("✓ " + self.lm.get("Common.save", "Save"))
        save_btn.clicked.connect(lambda: self._add_technician_logic(
            dialog,
            full_name_input,
            email_input,
            phone_input,
            address_input,
            certification_input,
            specialization_input,
            salary_input,
            commission_input
        ))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _add_technician_logic(self, dialog, full_name_input, email_input, phone_input, 
                       address_input, certification_input, specialization_input,
                       salary_input, commission_input):
        """
        Logic to add new technician.
        Validates inputs and creates a new technician record.
        """
        from decimal import Decimal
        from PySide6.QtWidgets import QMessageBox
        full_name = full_name_input.text().strip()
        email = email_input.text().strip()
        phone = phone_input.text().strip()
        
        # Validate full name
        if not full_name:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Technicians.enter_full_name", "Please enter full name"))
            return
        
        # Validate email if provided
        if email and not email_input.hasAcceptableInput():
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_email", "Please enter a valid email address"))
            return
        
        # Validate phone if provided
        if phone and not phone_input.hasAcceptableInput():
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_phone", "Please enter a valid phone number (09xxxxxxxxx)"))
            return
        
        # Validate salary
        try:
            salary_value = Decimal(str(salary_input.value()))
            if salary_value < 0:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_salary", "Salary cannot be negative"))
                return
        except:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_salary_format", "Please enter a valid salary amount"))
            return
        
        # Validate commission
        try:
            commission_value = Decimal(commission_input.text() or "0")
            if commission_value < 0 or commission_value > 100:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_commission", "Commission rate must be between 0 and 100"))
                return
        except:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Common.invalid_commission_format", "Please enter a valid commission rate"))
            return
        
        technician_data = {
            "full_name": full_name,
            "email": email or None,
            "phone": phone or None,
            "address": address_input.text().strip() or None,
            "certification": certification_input.text().strip() or None,
            "specialization": specialization_input.text().strip() or None,
            "salary": salary_value,
            "commission_rate": commission_value,
            "is_active": True
        }
        
        try:
            technician = self.technician_controller.create_technician(
                technician_data
            )
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Technicians.technician_added_successfully", "Technician added successfully"))
            self.load_technicians()
            dialog.close()
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Technicians.failed_to_add_technician', 'Failed to add technician')}: {str(e)}")

    def _show_dashboard(self):
        """Show performance dashboard dialog."""
        dialog = PerformanceDashboardDialog(self.container, self.user, parent=self)
        dialog.exec()

    def _show_bonus_dialog(self):
        """Show bonus management dialog."""
        dialog = BonusManagementDialog(self.container, self.user, parent=self)
        dialog.exec()

    def _edit_technician(self, technician):
        """Open dialog to edit technician details."""
        self.show_technician_details(technician) # Re-use existing details dialog for editing

    def _delete_technician(self, technician):
        """Delete a technician after confirmation."""
        reply = QMessageBox.question(
            self, 
            self.lm.get("Common.confirm", "Confirm"), 
            self.lm.get("Users.confirm_delete", "Are you sure you want to delete this technician?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Assuming technician_controller has a delete method
                self.technician_controller.delete_technician(technician.id)
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Users.technician_deleted", "Technician deleted successfully"))
                self.load_technicians()
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.error_occurred', 'Failed to delete technician')}: {str(e)}")