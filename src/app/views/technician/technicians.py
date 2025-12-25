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
from typing import List, Optional
from decimal import Decimal
from models.technician import Technician
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from views.components.new_dashboard_widgets import is_dark_theme
from utils.security.password_utils import hash_password
from views.technician.performance_dashboard_dialog import PerformanceDashboardDialog
from views.technician.bonus_management_dialog import BonusManagementDialog


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
        
        # Theme handling
        self.current_theme = 'dark'
        if hasattr(self.container, 'theme_controller'):
             self.current_theme = self.container.theme_controller.current_theme

        # Apply initial theme
        self._update_all_styles()
        
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
        
        self.title_label = QLabel(self.lm.get("Users.technicians_title", "Technicians"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(self.title_label)
        
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
        
        # Add context menu support
        self.technicians_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.technicians_table.customContextMenuRequested.connect(self._on_table_context_menu)
        
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
        
        self._connect_theme_signal()

    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        self.current_theme = theme_name
        self._update_all_styles()
        self.load_technicians() # Reload data to refresh cards with new theme

    def _update_all_styles(self):
        """Update all styles"""
        self._update_header_style()
        self._update_input_style()
        self._update_table_style()

    def _update_header_style(self):
        """Update header text color"""
        is_dark = self.current_theme == 'dark'
        text_color = "white" if is_dark else "#1F2937"
        self.title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {text_color};")

    def _update_input_style(self):
        """Update input field style"""
        is_dark = self.current_theme == 'dark'
        border_color = "#374151" if is_dark else "#D1D5DB"
        bg_color = "#1F2937" if is_dark else "#FFFFFF"
        text_color = "white" if is_dark else "black"
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {border_color};
                border-radius: 6px;
                background-color: {bg_color};
                color: {text_color};
            }}
            QLineEdit:focus {{
                border-color: #3B82F6;
            }}
        """)

    def _update_table_style(self):
        """Update table style"""
        is_dark = self.current_theme == 'dark'
        border_color = "#374151" if is_dark else "#E5E7EB"
        
        self.technicians_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {border_color};
                border-radius: 8px;
                gridline-color: {border_color};
                background-color: {'#1F2937' if is_dark else '#FFFFFF'};
                color: {'white' if is_dark else 'black'};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {border_color};
                color: {'white' if is_dark else 'black'};
            }}
            QHeaderView::section {{
                padding: 8px;
                border: none;
                border-bottom: 2px solid {border_color};
                font-weight: bold;
                background-color: {'#374151' if is_dark else '#F3F4F6'};
                color: {'white' if is_dark else 'black'};
            }}
        """)


    
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
        card.status_color = status_color
        self._update_card_style(card, tech.id in self.selected_technicians)
        
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
        
        # Display name check
        display_name = tech.full_name
        if tech.user:
            display_name = tech.user.full_name
            
        name_label = QLabel(display_name)
        name_label.setObjectName("nameLabel")
        # Style set by _update_card_style
        name_label.setStyleSheet(f"font-size: 16px; font-weight: bold;")
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
            spec_label.setObjectName("metaLabel")
            spec_label.setStyleSheet(f"font-size: 13px;")
            layout.addWidget(spec_label)
        
        if tech.certification:
            cert_label = QLabel(f"📜 {tech.certification}")
            cert_label.setObjectName("metaLabel")
            cert_label.setStyleSheet(f"font-size: 12px;")
            layout.addWidget(cert_label)
        
        # Contact info
        if tech.email:
            email_label = QLabel(f"📧 {tech.email}")
            email_label.setObjectName("metaLabel")
            email_label.setStyleSheet(f"font-size: 11px;")
            layout.addWidget(email_label)
        
        if tech.phone:
            phone_label = QLabel(f"📱 {tech.phone}")
            phone_label.setObjectName("metaLabel")
            phone_label.setStyleSheet(f"font-size: 11px;")
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
            display_name = tech.full_name
            if tech.user:
                display_name = tech.user.full_name
            self.technicians_table.setItem(row, 2, QTableWidgetItem(display_name))
            
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
        """Wrapper for _update_card_style to maintain compatibility"""
        self._update_card_style(card, is_selected)

    def _update_card_style(self, card, is_selected):
        """Update card style based on selection and theme"""
        # Get status color for hover effect
        status_color = getattr(card, 'status_color', '#10B981')
        
        # Theme colors
        is_dark = self.current_theme == 'dark'
        
        if is_dark:
            bg_color = "#374151" if is_selected else "#1F2937"
            border_color = "#3B82F6" if is_selected else "#374151"
            hover_bg = "#374151"
            hover_border = status_color
            text_main = "white"
            text_sub = "#9CA3AF"
        else: # Light
            bg_color = "#EFF6FF" if is_selected else "#FFFFFF"
            border_color = "#3B82F6" if is_selected else "#E5E7EB"
            hover_bg = "#F9FAFB"
            hover_border = status_color
            text_main = "#1F2937"
            text_sub = "#6B7280"

        card.setStyleSheet(f"""
            QFrame#techCard {{
                background-color: {bg_color};
                border: {'2px' if is_selected else '1px'} solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#techCard:hover {{
                border-color: {hover_border};
                background-color: {hover_bg if not is_selected else bg_color};
            }}
            QLabel#nameLabel {{
                color: {text_main};
            }}
            QLabel#metaLabel {{
                color: {text_sub};
            }}
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
        item = self.technicians_table.item(row, 1)
        if not item:
            return
        tech_id = int(item.text())
        technician = self.technician_controller.get_technician(tech_id)
        if technician:
            self.show_technician_details(technician)
            
    def _on_table_context_menu(self, pos):
        """Handle right-click on technicians table"""
        row = self.technicians_table.rowAt(pos.y())
        if row < 0:
            return
            
        item = self.technicians_table.item(row, 1)
        if not item:
            return
            
        tech_id = int(item.text())
        technician = self.technician_controller.get_technician(tech_id)
        
        if technician:
            menu = QMenu(self)
            
            view_action = menu.addAction(f"👁️ {self.lm.get('Common.view_details', 'View Details')}")
            view_action.triggered.connect(lambda: self.show_technician_details(technician))
            
            menu.addSeparator()
            
            edit_action = menu.addAction(f"✏️ {self.lm.get('Common.edit', 'Edit')}")
            edit_action.triggered.connect(lambda: self._edit_technician(technician))
            
            if technician.is_active:
                deactivate_action = menu.addAction(f"🚫 {self.lm.get('Users.deactivate', 'Deactivate')}")
                deactivate_action.triggered.connect(lambda: self._toggle_technician_status(technician))
            else:
                activate_action = menu.addAction(f"✅ {self.lm.get('Users.activate', 'Activate')}")
                activate_action.triggered.connect(lambda: self._toggle_technician_status(technician))
            
            menu.addSeparator()
            
            delete_action = menu.addAction(f"🗑️ {self.lm.get('Common.delete', 'Delete')}")
            delete_action.triggered.connect(lambda: self._delete_technician(technician))
            
            menu.exec(self.technicians_table.viewport().mapToGlobal(pos))
    
    def show_technician_details(self, technician):
        """Show technician details dialog"""
        from views.technician.technician_details_dialog import TechnicianDetailsDialog
        dialog = TechnicianDetailsDialog(self.container, technician, parent=self)
        dialog.exec()
        self.load_technicians()  # Refresh after dialog closes
    
    def show_add_technician_dialog(self, technician=None):
        """Show dialog to add or edit technician with modern compact UI"""
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QGridLayout
        from views.components.money_input import MoneyInput
        
        # Detect theme
        dark_mode = is_dark_theme(self)
        
        # Define theme-aware colors
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        label_color = "#E5E7EB" if dark_mode else "#374151"
        input_bg = "#374151" if dark_mode else "#F9FAFB"
        input_border = "#4B5563" if dark_mode else "#D1D5DB"
        input_text = "#F9FAFB" if dark_mode else "#111827"
        input_focus_bg = "#4B5563" if dark_mode else "#FFFFFF"
        primary_color = "#3B82F6"
        primary_hover = "#2563EB"
        
        # Suffix colors (Ks, %)
        ks_bg = "#065F46" if dark_mode else "#DCFCE7"
        ks_text = "#10B981" if dark_mode else "#059669"
        pct_bg = "#1E3A8A" if dark_mode else "#DBEAFE"
        pct_text = "#3B82F6" if dark_mode else "#1D4ED8"
        
        dialog = QDialog(self)
        title_text = self.lm.get("Technicians.edit_technician", "Edit Technician") if technician else self.lm.get("Technicians.add_new_technician", "Add New Technician")
        dialog.setWindowTitle(title_text)
        dialog.setFixedSize(650, 540)
        
        # Modern dynamic theme styling
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {label_color};
            }}
            QLineEdit {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 6px;
                padding: 8px 10px;
                color: {input_text};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {primary_color};
                background-color: {input_focus_bg};
            }}
            QLineEdit:hover {{
                border-color: #6B7280;
            }}
            QPushButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {primary_hover};
            }}
            QPushButton:pressed {{
                background-color: #1D4ED8;
            }}
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
        personal_header.setStyleSheet(f"font-weight: bold; color: {primary_color}; font-size: 14px; padding-top: 5px;")
        form_layout.addWidget(personal_header, row, 0, 1, 4)
        row += 1
        
        # Full Name (spans 2 columns)
        full_name_label = QLabel("✏️ " + self.lm.get("Common.full_name", "Full Name") + " *")
        full_name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        full_name_input = QLineEdit()
        if technician:
            # Prefer User name if linked
            name_val = technician.user.full_name if (technician.user and hasattr(technician.user, 'full_name')) else (technician.full_name or "")
            full_name_input.setText(name_val)
        full_name_input.setPlaceholderText(self.lm.get("Common.enter_full_name", "Enter full name"))
        form_layout.addWidget(full_name_label, row, 0)
        form_layout.addWidget(full_name_input, row, 1, 1, 3)
        row += 1
        
        # Email and Phone in same row
        email_label = QLabel("📧 " + self.lm.get("Common.email", "Email"))
        email_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        email_input = QLineEdit()
        if technician:
            # Prefer User email if linked
            email_val = technician.user.email if (technician.user and technician.user.email) else (technician.email or "")
            email_input.setText(email_val)
        email_input.setPlaceholderText("example@gmail.com")
        email_regex = QRegularExpression(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        email_validator = QRegularExpressionValidator(email_regex)
        email_input.setValidator(email_validator)
        
        phone_label = QLabel("📱 " + self.lm.get("Common.phone", "Phone"))
        phone_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        phone_input = QLineEdit()
        if technician:
            phone_input.setText(technician.phone or "")
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
        if technician:
            address_input.setText(technician.address or "")
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
        if technician:
            certification_input.setText(technician.certification or "")
        certification_input.setPlaceholderText(self.lm.get("Technicians.enter_certification", "Enter certification"))
        
        spec_label = QLabel("🔧 " + self.lm.get("Technicians.specialization", "Specialization"))
        spec_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        specialization_input = QLineEdit()
        if technician:
            specialization_input.setText(technician.specialization or "")
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
        if technician:
            salary_input.setValue(float(technician.salary or 0))
        salary_input.setPlaceholderText("0.00")
        
        salary_layout.addWidget(salary_input)
        
        salary_currency = QLabel("Ks")
        salary_currency.setAlignment(Qt.AlignCenter)
        salary_currency.setStyleSheet(f"""
            background-color: {ks_bg};
            color: {ks_text};
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
        if technician:
            commission_input.setText(str(float(technician.commission_rate or 0)))
        commission_input.setPlaceholderText("0.00")
        commission_regex = QRegularExpression(r"^\d+(\.\d{0,2})?$")
        commission_validator = QRegularExpressionValidator(commission_regex)
        commission_input.setValidator(commission_validator)
        commission_layout.addWidget(commission_input)
        
        commission_percent = QLabel("%")
        commission_percent.setAlignment(Qt.AlignCenter)
        commission_percent.setStyleSheet(f"""
            background-color: {pct_bg};
            color: {pct_text};
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)
        commission_layout.addWidget(commission_percent)
        
        form_layout.addWidget(commission_label, row, 2)
        form_layout.addWidget(commission_container, row, 3)
        row += 1
        
        # Account Access
        access_header = QLabel("🔐 " + self.lm.get("Technicians.account_access", "Account Access"))
        access_header.setStyleSheet("font-weight: bold; color: #F59E0B; font-size: 14px; padding-top: 5px;")
        form_layout.addWidget(access_header, row, 0, 1, 4)
        row += 1
        
        pass_label = QLabel("🔑 " + self.lm.get("Common.password", "Password"))
        pass_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText(self.lm.get("Common.enter_password", "Enter password"))
        
        form_layout.addWidget(pass_label, row, 0)
        form_layout.addWidget(password_input, row, 1, 1, 3)
        
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
            commission_input,
            password_input,
            technician # Pass existing technician if editing
        ))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _add_technician_logic(self, dialog, full_name_input, email_input, phone_input, 
                       address_input, certification_input, specialization_input,
                       salary_input, commission_input, password_input, existing_technician=None):
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
        
        # Only update password if input is not empty
        password_val = password_input.text().strip()
        if password_val:
            technician_data["password"] = hash_password(password_val)
        
        try:
            if existing_technician:
                # Update existing technician
                self.technician_controller.update_technician(
                    existing_technician.id,
                    technician_data
                )
                success_msg = self.lm.get("Technicians.technician_updated_successfully", "Technician updated successfully")
            else:
                # Create new technician
                self.technician_controller.create_technician(
                    technician_data
                )
                success_msg = self.lm.get("Technicians.technician_added_successfully", "Technician added successfully")
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), success_msg)
            self.load_technicians()
            dialog.close()
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Technicians.failed_to_add_technician', 'Failed to add technician')}: {str(e)}")

    def get_selected_technician_id(self) -> Optional[int]:
        """Get the ID of the currently selected technician."""
        if self.current_view == 'cards':
            if self.selected_technicians:
                return self.selected_technicians[0]
        elif self.current_view == 'list':
            current_row = self.technicians_table.currentRow()
            if current_row >= 0:
                item = self.technicians_table.item(current_row, 1)
                if item:
                    return item.data(Qt.UserRole)
        return None

    def _show_dashboard(self):
        """Show performance dashboard dialog."""
        tech_id = self.get_selected_technician_id()
        
        if not tech_id:
            QMessageBox.warning(
                self, 
                self.lm.get("Common.warning", "Warning"), 
                self.lm.get("Technicians.select_technician_first", "Please select a technician first.")
            )
            return

        technician = self.technician_controller.get_technician(tech_id)
        if not technician:
            return
            
        dialog = PerformanceDashboardDialog(self.container, technician, parent=self)
        dialog.exec()

    def _show_bonus_dialog(self):
        """Show bonus management dialog."""
        tech_id = self.get_selected_technician_id()
        
        if not tech_id:
            QMessageBox.warning(
                self, 
                self.lm.get("Common.warning", "Warning"), 
                self.lm.get("Technicians.select_technician_first", "Please select a technician first.")
            )
            return

        technician = self.technician_controller.get_technician(tech_id)
        if not technician:
            return

        dialog = BonusManagementDialog(self.container, technician, parent=self)
        dialog.exec()

    def _edit_technician(self, technician):
        """Open dialog to edit technician details."""
        self.show_add_technician_dialog(technician)

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