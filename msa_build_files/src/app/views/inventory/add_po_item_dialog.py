"""Dialog for adding parts to a Purchase Order."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QFormLayout, QDoubleSpinBox,
                               QSpinBox)
from PySide6.QtCore import Qt, QTimer
from views.inventory.part_dialog import PartDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class AddPOItemDialog(QDialog):
    """Dialog for selecting and adding a part to a Purchase Order."""
    
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.selected_part = None
        self.quantity = 0
        self.unit_cost = 0.0
        self.lm = language_manager
        
        # Initialize timer for search debounce
        self.search_timer = QTimer()
        self.search_timer.setInterval(300)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._setup_ui()
        self._load_parts()
        
    def _setup_ui(self):
        from PySide6.QtGui import QPalette
        
        self.setWindowTitle(self.lm.get("Inventory.add_part_po_title", "Add Part to Purchase Order"))
        self.setMinimumSize(700, 550)
        
        # Detect theme
        palette = self.palette()
        is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Theme-aware colors
        instruction_color = "#a0aec0" if is_dark else "#555"
        
        layout = QVBoxLayout(self)
        
        # Header instruction
        instruction = QLabel(self.lm.get("Inventory.select_part_instruction", "Select a part from the list below, then double-click to set quantity and price."))
        instruction.setStyleSheet(f"color: {instruction_color}; font-style: italic; padding: 5px;")
        layout.addWidget(instruction)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel(f"{self.lm.get('Common.search', 'Search')}:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Inventory.search_placeholder", "Search by Name, SKU, or Brand..."))
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Parts table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        headers = [
            self.lm.get("Inventory.part_name", "Part Name"),
            self.lm.get("Inventory.brand", "Brand"),
            self.lm.get("Inventory.sku", "SKU"),
            self.lm.get("Inventory.current_stock", "Current Stock"),
            self.lm.get("Inventory.cost_price", "Cost Price")
        ]
        self.parts_table.setHorizontalHeaderLabels(headers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Connect double-click to add item
        self.parts_table.doubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.parts_table)
        
        # Bottom action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.create_part_btn = QPushButton(self.lm.get("Inventory.create_new_part", "Create New Part"))
        self.create_part_btn.clicked.connect(self._on_create_part)
        action_layout.addWidget(self.create_part_btn)
        
        self.cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(action_layout)
        
    def _load_parts(self, query=None):
        """Load parts into the table."""
        if query:
            parts = self.container.part_service.search_parts(query)
        else:
            parts = self.container.part_service.get_all_parts()
            
        # Show only active parts
        parts = [p for p in parts if p.is_active]
        
        self.parts_table.setRowCount(len(parts))
        
        for row, part in enumerate(parts):
            self.parts_table.setItem(row, 0, QTableWidgetItem(part.name))
            self.parts_table.setItem(row, 1, QTableWidgetItem(part.brand or ""))
            self.parts_table.setItem(row, 2, QTableWidgetItem(part.sku or ""))
            
            stock_item = QTableWidgetItem(str(part.current_stock))
            if part.current_stock <= 0:
                stock_item.setForeground(Qt.red)
            elif part.current_stock <= part.min_stock_level:
                stock_item.setForeground(Qt.darkYellow)
            self.parts_table.setItem(row, 3, stock_item)
            
            self.parts_table.setItem(row, 4, QTableWidgetItem(currency_formatter.format(part.cost_price)))
            
            # Store part object in first column
            self.parts_table.item(row, 0).setData(Qt.UserRole, part)
            
    def _on_search_changed(self):
        """Debounce search input."""
        self.search_timer.start()
        
    def _perform_search(self):
        """Execute the search."""
        query = self.search_input.text().strip()
        self._load_parts(query)
        
    def _on_double_click(self, index):
        """Handle double-click on a part to add it."""
        row = index.row()
        part = self.parts_table.item(row, 0).data(Qt.UserRole)
        
        if not part:
            return
            
        # Open dialog to get quantity and unit cost
        dialog = POItemDetailsDialog(part, parent=self)
        if dialog.exec():
            self.selected_part = part
            self.quantity = dialog.quantity
            self.unit_cost = dialog.unit_cost
            self.accept()
            
    def _on_create_part(self):
        """Open dialog to create a new part."""
        dialog = PartDialog(self.container, parent=self)
        if dialog.exec():
            # Refresh the parts list
            self._load_parts(self.search_input.text().strip())
            
    def get_selected_data(self):
        """Return the selected part, quantity, and unit cost."""
        return self.selected_part, self.quantity, self.unit_cost


class POItemDetailsDialog(QDialog):
    """Dialog for entering quantity and unit cost for a purchase order item."""
    
    def __init__(self, part, parent=None):
        super().__init__(parent)
        self.part = part
        self.quantity = 1
        self.unit_cost = float(part.cost_price)
        self.lm = language_manager
        
        self._setup_ui()
        
    def _setup_ui(self):
        from PySide6.QtGui import QPalette, QDoubleValidator
        
        self.setWindowTitle(self.lm.get("Inventory.set_qty_price_title", "Set Quantity and Price"))
        self.setMinimumWidth(400)
        
        # Detect theme
        palette = self.palette()
        is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Theme-aware colors
        if is_dark:
            info_bg_color = "#2d3748"
            info_text_color = "#e2e8f0"
            total_text_color = "#90cdf4"
            button_bg_color = "#48bb78"
            button_hover_color = "#38a169"
        else:
            info_bg_color = "#f0f0f0"
            info_text_color = "#2d3748"
            total_text_color = "#2c5282"
            button_bg_color = "#2ecc71"
            button_hover_color = "#27ae60"
        
        layout = QVBoxLayout(self)
        
        # Part info
        info_label = QLabel(f"<b>{self.lm.get('Inventory.part', 'Part')}:</b> {self.part.name}<br><b>{self.lm.get('Inventory.sku', 'SKU')}:</b> {self.part.sku or 'N/A'}")
        info_label.setStyleSheet(f"""
            padding: 10px;
            background-color: {info_bg_color};
            color: {info_text_color};
            border-radius: 5px;
        """)
        layout.addWidget(info_label)
        
        # Form for quantity and price
        form_layout = QFormLayout()
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self._update_total)
        form_layout.addRow(f"{self.lm.get('Inventory.quantity', 'Quantity')}:", self.quantity_spin)
        
        from views.components.money_input import MoneyInput
        self.unit_cost_input = MoneyInput(default_value=float(self.part.cost_price))
        self.unit_cost_input.textChanged.connect(self._update_total)
        form_layout.addRow(f"{self.lm.get('Inventory.unit_cost', 'Unit Cost')}:", self.unit_cost_input)
        
        # Total cost display
        self.total_label = QLabel()
        self.total_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: {total_text_color};
        """)
        self._update_total()
        form_layout.addRow(f"{self.lm.get('Inventory.total_cost', 'Total Cost')}:", self.total_label)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton(self.lm.get("Inventory.add_to_po", "Add to Purchase Order"))
        add_btn.setStyleSheet(f"""
            background-color: {button_bg_color};
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
        """)
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)
        
        layout.addLayout(btn_layout)
        
    def _update_total(self):
        """Update the total cost display."""
        quantity = self.quantity_spin.value()
        unit_cost = self.unit_cost_input.value()
            
        total = quantity * unit_cost
        
        # Use currency formatter if available, else standard format
        symbol = currency_formatter.get_currency_symbol()
        self.total_label.setText(f"<b>{symbol} {total:,.2f}</b>")
        
    def _on_add(self):
        """Validate and accept the dialog."""
        self.quantity = self.quantity_spin.value()
        self.unit_cost = self.unit_cost_input.value()
        
        if self.quantity <= 0:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.invalid_quantity", "Please enter a quantity greater than 0."))
            return
            
        if self.unit_cost < 0:
            # Depending on business rules, cost might be allowed to be 0 (free sample?)
            # But usually not negative.
             QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.invalid_price", "Please enter a valid unit cost."))
             return
            
        self.accept()
