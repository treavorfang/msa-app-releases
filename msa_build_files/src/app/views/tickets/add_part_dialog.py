# src/app/views/tickets/add_part_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QLineEdit, QTableWidget, 
                              QTableWidgetItem, QHeaderView, QSpinBox, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from views.inventory.part_dialog import PartDialog
from utils.language_manager import language_manager

class AddPartDialog(QDialog):
    """Dialog for selecting and adding a part to a ticket"""
    
    def __init__(self, container, ticket=None, parent=None, check_stock=True):
        super().__init__(parent)
        self.container = container
        self.lm = language_manager
        self.ticket = ticket
        self.check_stock = check_stock
        self.selected_part = None
        
        # Initialize timer for search debounce
        self.search_timer = QTimer()
        self.search_timer.setInterval(300)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._setup_ui()
        self._load_parts()
        
    def _setup_ui(self):
        self.setWindowTitle(self.lm.get("TicketActions.add_part_title", "Add Part to Ticket"))
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search parts by Name, SKU, or Brand...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Parts table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        headers = [
            self.lm.get("Inventory.part_name", "Name"),
            self.lm.get("Tickets.brand", "Brand"),
            self.lm.get("Inventory.sku", "SKU"),
            self.lm.get("Inventory.stock", "Stock"),
            self.lm.get("Invoices.unit_price_header", "Price")
        ]
        self.parts_table.setHorizontalHeaderLabels(headers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parts_table.itemSelectionChanged.connect(self._on_part_selected)
        layout.addWidget(self.parts_table)
        
        # Quantity and Add
        action_layout = QHBoxLayout()
        
        action_layout.addWidget(QLabel("Quantity:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(1)
        action_layout.addWidget(self.quantity_spin)
        
        action_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.lm.get("TicketActions.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(self.cancel_btn)

        self.create_part_btn = QPushButton(self.lm.get("TicketActions.create_part", "Create Part"))
        self.create_part_btn.clicked.connect(self._on_create_clicked)
        action_layout.addWidget(self.create_part_btn)
        
        self.add_btn = QPushButton(self.lm.get("TicketActions.add_part", "Add Part"))
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.add_btn.setEnabled(False)
        self.add_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        action_layout.addWidget(self.add_btn)
        
        layout.addLayout(action_layout)
        
    def _load_parts(self, query=None):
        """Load parts into the table"""
        if query:
            parts = self.container.part_service.search_parts(query)
        else:
            parts = self.container.part_service.get_all_parts()
            
        # Filter out inactive parts or parts with 0 stock?
        # Maybe show 0 stock but disable selection?
        # For now, let's show all active parts
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
                stock_item.setForeground(Qt.darkYellow) # Orange-ish
            self.parts_table.setItem(row, 3, stock_item)
            
            self.parts_table.setItem(row, 4, QTableWidgetItem(f"${part.cost_price:.2f}"))
            
            # Store part object in first column
            self.parts_table.item(row, 0).setData(Qt.UserRole, part)
            
    def _on_search_changed(self):
        self.search_timer.start()
        
    def _perform_search(self):
        query = self.search_input.text().strip()
        self._load_parts(query)
        
    def _on_part_selected(self):
        selected_items = self.parts_table.selectedItems()
        if selected_items:
            self.selected_part = self.parts_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
            self.add_btn.setEnabled(True)
            
            # Update max quantity based on stock
            if self.check_stock:
                if self.selected_part.current_stock > 0:
                    self.quantity_spin.setMaximum(self.selected_part.current_stock)
                    self.quantity_spin.setValue(1)
                else:
                    self.quantity_spin.setMaximum(0)
                    self.add_btn.setEnabled(False) # Cannot add if out of stock
            else:
                # For Purchase Orders, we can order as much as we want
                self.quantity_spin.setMaximum(999999)
                self.quantity_spin.setValue(1)
        else:
            self.selected_part = None
            self.add_btn.setEnabled(False)
            
    def _on_add_clicked(self):
        if not self.selected_part:
            return
            
        quantity = self.quantity_spin.value()
        if quantity <= 0:
            QMessageBox.warning(self, self.lm.get("Common.warning", "Warning"), self.lm.get("TicketMessages.invalid_quantity", "Please select a valid quantity."))
            return
            
        try:
            # We need the current user (technician) to record who added the part
            # Assuming we can get it from the container or passed in
            # For now, let's try to get the current user from the main window context if possible
            # Or we might need to pass user_id to this dialog
            
            # Wait, the controller needs a User object for technician.
            # Let's assume the logged-in user is the technician performing this action.
            # We need to pass the user to this dialog.
            
            # For now, let's return the selection and let the caller handle the actual creation
            # This keeps the dialog focused on selection.
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.part_add_failed', 'Failed to add part')}: {str(e)}")

    def _on_create_clicked(self):
        dialog = PartDialog(self.container, parent=self)
        if dialog.exec():
            # Refresh list and potentially select the new part
            self._load_parts(self.search_input.text().strip())
            
    def get_selected_part_data(self):
        """Return the selected part and quantity"""
        return self.selected_part, self.quantity_spin.value()
