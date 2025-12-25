from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QLineEdit, QLabel, QGroupBox, QMessageBox, QFrame,
                               QComboBox, QMenu)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QAction
from config.constants import UIColors
from views.inventory.part_dialog import PartDialog
from views.inventory.restock_dialog import RestockDialog
from views.inventory.part_details_dialog import PartDetailsDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class ModernPartsListTab(QWidget):
    """Modern parts list tab with enhanced UI and functionality"""
    
    def __init__(self, container, user, parent=None):
        super().__init__(parent)
        self.container = container
        self.user = user
        self.lm = language_manager
        
        # Search timer for debounce
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._setup_ui()
        self._connect_signals()
        
        # Theme handling
        self.current_theme = 'dark'
        if hasattr(self.container, 'theme_controller'):
             self.container.theme_controller.theme_changed.connect(self._on_theme_changed)
             self.current_theme = self.container.theme_controller.current_theme
             
        self._update_all_styles()
        
        # self._load_data()
        self._data_loaded = False
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Summary Cards
        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(12)
        layout.addLayout(self.summary_layout)
        
        # Initialize summary cards
        self.total_parts_card = self._create_summary_card(self.lm.get("Inventory.total_parts", "Total Parts"), "0", "#3B82F6", "📦")
        self.low_stock_card = self._create_summary_card(self.lm.get("Inventory.low_stock", "Low Stock"), "0", "#F59E0B", "⚠️")
        self.out_stock_card = self._create_summary_card(self.lm.get("Inventory.out_of_stock", "Out of Stock"), "0", "#EF4444", "🚫")
        self.total_value_card = self._create_summary_card(self.lm.get("Inventory.total_value", "Total Value"), currency_formatter.format(0), "#10B981", "💰")
        
        self.summary_layout.addWidget(self.total_parts_card)
        self.summary_layout.addWidget(self.low_stock_card)
        self.summary_layout.addWidget(self.out_stock_card)
        self.summary_layout.addWidget(self.total_value_card)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_parts", "Search parts by SKU, name, brand..."))
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_parts", "Search parts by SKU, name, brand..."))
        # Style set by _update_input_style
        """
        self.search_input.setStyleSheet(\"\"\"
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #374151;
                border-radius: 6px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        \"\"\")
        """
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        toolbar_layout.addStretch()
        
        # Action Buttons
        self.new_part_btn = self._create_action_button(self.lm.get("Inventory.new_part", "New Part"), "#3B82F6", "plus")
        self.new_part_btn.clicked.connect(self._on_new_part)
        
        self.restock_btn = self._create_action_button(self.lm.get("Inventory.restock", "Restock"), "#10B981", "box")
        self.restock_btn.clicked.connect(self._on_restock)
        
        self.po_btn = self._create_action_button(self.lm.get("Inventory.purchase_orders", "Purchase Orders"), "#8B5CF6", "file-text")
        self.po_btn.clicked.connect(self._on_purchase_orders)
        
        toolbar_layout.addWidget(self.new_part_btn)
        toolbar_layout.addWidget(self.restock_btn)
        toolbar_layout.addWidget(self.po_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Parts Table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(9)
        headers = [
            self.lm.get("Inventory.barcode", "Barcode"),
            self.lm.get("Inventory.sku", "SKU"),
            self.lm.get("Inventory.part_name", "Name"),
            self.lm.get("Inventory.device_brand", "Brand"),
            self.lm.get("Inventory.category", "Category"),
            self.lm.get("Inventory.device_model", "Compatible Model"),
            self.lm.get("Inventory.stock", "Stock"),
            self.lm.get("Inventory.cost", "Unit Price"),
            self.lm.get("Inventory.value", "Total Value")
        ]
        self.parts_table.setHorizontalHeaderLabels(headers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parts_table.verticalHeader().setVisible(False)
        self.parts_table.setShowGrid(False)
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.parts_table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.parts_table.doubleClicked.connect(self._on_part_double_clicked)
        
        # Table Styling
        # Table Styling handled by _update_table_style
        """
        self.parts_table.setStyleSheet(\"\"\"
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
        \"\"\")
        """
        
        layout.addWidget(self.parts_table)
        
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

    def _create_action_button(self, text, color, icon_name=None):
        """Create a styled action button"""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """)
        return btn

    def _on_theme_changed(self, theme_name):
        """Handle theme changes"""
        self.current_theme = theme_name
        self._update_all_styles()
        self._load_data()
        
    def _update_all_styles(self):
        """Update all styles based on current theme"""
        self._update_table_style()
        self._update_input_style()
        
    def _update_table_style(self):
        """Update table widget style"""
        is_dark = self.current_theme == 'dark'
        border_color = "#374151" if is_dark else "#E5E7EB"
        
        self.parts_table.setStyleSheet(f"""
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
                min-width: 250px;
                background-color: {bg_color};
                color: {text_color};
            }}
            QLineEdit:focus {{
                border-color: #3B82F6;
            }}
        """)

    def _connect_signals(self):
        # Connect signals for auto-refresh
        if hasattr(self.container, 'part_controller'):
            self.container.part_controller.data_changed.connect(self._load_data)
        if hasattr(self.container, 'repair_part_controller'):
            self.container.repair_part_controller.repair_part_changed.connect(self._load_data)
        if hasattr(self.container, 'purchase_order_controller'):
            self.container.purchase_order_controller.status_changed.connect(self._on_po_status_changed)
        if hasattr(self.container, 'purchase_return_controller'):
            self.container.purchase_return_controller.return_approved.connect(self._load_data)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_data)
            self._data_loaded = True

    def _load_data(self):
        """Load real data from the database"""
        self._update_summary()
        self._load_parts_table()

    def _update_summary(self):
        """Update summary cards with real data"""
        part_service = self.container.part_service
        total_parts = len(part_service.get_all_parts())
        low_stock = len(part_service.get_low_stock_parts())
        out_of_stock = len(part_service.get_out_of_stock_parts())
        total_value = part_service.get_total_inventory_value()
        
        self._update_card_value(self.total_parts_card, str(total_parts))
        self._update_card_value(self.low_stock_card, str(low_stock))
        self._update_card_value(self.out_stock_card, str(out_of_stock))
        self._update_card_value(self.total_value_card, currency_formatter.format(total_value))

    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        # Value label is the second item in the text layout (which is the second item in main layout)
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)

    def _load_parts_table(self, parts=None):
        """Load parts into the table"""
        if parts is None:
            parts = self.container.part_service.get_all_parts()
        
        self.parts_table.setRowCount(len(parts))
        
        for row, part in enumerate(parts):
            self._add_part_to_table(row, part)

    def _add_part_to_table(self, row, part):
        """Add a single part to the table"""
        data = [
            part.barcode or "N/A",
            part.sku,
            part.name,
            part.brand or "N/A",
            part.category_name or "N/A",
            part.model_compatibility or "N/A",
            str(part.current_stock),
            currency_formatter.format(part.cost_price),
            currency_formatter.format(part.cost_price * part.current_stock)
        ]
        
        for col, value in enumerate(data):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            
            # Highlight stock levels
            if col == 6:  # Stock column
                is_dark = self.current_theme == 'dark'
                if part.current_stock <= 0:
                    item.setForeground(QColor("#EF4444") if not is_dark else QColor("#F87171")) # Red
                    # Light red bg for light mode, Dark red bg for dark mode (transparent/darker)
                    item.setBackground(QColor("#FEF2F2") if not is_dark else QColor("#7F1D1D")) 
                elif part.current_stock <= part.min_stock_level:
                    item.setForeground(QColor("#F59E0B") if not is_dark else QColor("#FBBF24")) # Orange
                    item.setBackground(QColor("#FFFBEB") if not is_dark else QColor("#78350F")) # Dark orange bg
            
            self.parts_table.setItem(row, col, item)

    def _on_search_changed(self, text):
        self.search_timer.start()

    def _perform_search(self):
        query = self.search_input.text().strip()
        if query:
            parts = self.container.part_service.search_parts(query)
            self._load_parts_table(parts)
        else:
            self._load_parts_table()

    def _on_new_part(self):
        dialog = PartDialog(self.container, parent=self)
        if dialog.exec():
            self._load_data()

    def _on_restock(self):
        selected_row = self.parts_table.currentRow()
        if selected_row >= 0:
            part = self._get_selected_part(selected_row)
            if part:
                dialog = RestockDialog(self.container, part, user=self.user, parent=self)
                if dialog.exec():
                    self._load_data()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.part_not_found", "Could not find selected part"))
        else:
            QMessageBox.warning(self, self.lm.get("Common.warning", "No Selection"), self.lm.get("Inventory.select_part_restock", "Please select a part to restock"))

    def _on_purchase_orders(self):
        from views.inventory.purchase_order_list_dialog import PurchaseOrderListDialog
        dialog = PurchaseOrderListDialog(self.container, parent=self)
        dialog.exec()

    def _on_part_double_clicked(self, index):
        part = self._get_selected_part(index.row())
        if part:
            dialog = PartDetailsDialog(self.container, part, parent=self)
            dialog.exec()

    def _get_selected_part(self, row):
        sku = self.parts_table.item(row, 1).text()
        return self.container.part_service.get_part_by_sku(sku)

    def _on_po_status_changed(self, po_id, new_status):
        if new_status == 'received':
            self._load_data()
    
    def _on_table_context_menu(self, position):
        """Handle context menu for table"""
        table = self.sender()
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        part = self._get_selected_part(row)
        if part:
            self._show_context_menu(part)
    
    def _show_context_menu(self, part):
        """Show context menu for part"""
        menu = QMenu(self)
        
        # View Details
        view_action = QAction(f"📄 {self.lm.get('Inventory.view_details', 'View Details')}", self)
        view_action.triggered.connect(lambda: self._open_part_details(part))
        menu.addAction(view_action)
        
        # Edit Part
        edit_action = QAction(f"✏️ {self.lm.get('Inventory.edit_part', 'Edit Part')}", self)
        edit_action.triggered.connect(lambda: self._edit_part(part))
        menu.addAction(edit_action)
        
        # Restock
        restock_action = QAction(f"📦 {self.lm.get('Inventory.restock', 'Restock')}", self)
        restock_action.triggered.connect(lambda: self._restock_part(part))
        menu.addAction(restock_action)
        
        menu.exec(self.cursor().pos())
    
    def _open_part_details(self, part):
        """Open part details dialog"""
        dialog = PartDetailsDialog(self.container, part, parent=self)
        dialog.exec()
    
    def _edit_part(self, part):
        """Open edit part dialog"""
        dialog = PartDialog(self.container, part=part, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _restock_part(self, part):
        """Open restock dialog"""
        dialog = RestockDialog(self.container, part, user=self.user, parent=self)
        if dialog.exec():
            self._load_data()
