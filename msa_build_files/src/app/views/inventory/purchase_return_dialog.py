# src/app/views/inventory/purchase_return_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                               QPushButton, QHeaderView, QMessageBox, QDateEdit,
                               QTextEdit)
from PySide6.QtCore import Qt, QDate
from config.constants import ReturnCondition


class PurchaseReturnDialog(QDialog):
    """Dialog for creating a purchase return"""
    
    def __init__(self, container, purchase_order, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.purchase_order = purchase_order
        self.user = user
        self.setWindowTitle(f"Create Return for PO: {purchase_order.po_number}")
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_items()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Header info
        info_layout = QHBoxLayout()
        
        info_layout.addWidget(QLabel(f"Supplier: {self.purchase_order.supplier_name}"))
        info_layout.addStretch()
        po_date = self.purchase_order.order_date.strftime('%Y-%m-%d') if self.purchase_order.order_date else 'N/A'
        info_layout.addWidget(QLabel(f"PO Date: {po_date}"))
        
        layout.addLayout(info_layout)
        
        # Return Details
        details_group = QVBoxLayout()
        
        # Reason
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("Reason for Return:"))
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., Defective items, Wrong shipment")
        reason_layout.addWidget(self.reason_input)
        details_group.addLayout(reason_layout)
        
        # Notes
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        notes_layout.addWidget(self.notes_input)
        details_group.addLayout(notes_layout)
        
        layout.addLayout(details_group)
        
        # Items Table
        layout.addWidget(QLabel("Select Items to Return:"))
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)  # Added Current Stock column
        self.items_table.setHorizontalHeaderLabels([
            "Part", "Received Qty", "Current Stock", "Unit Cost", "Return Qty", "Condition", "Total Refund"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setDefaultSectionSize(45)
        layout.addWidget(self.items_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Create Return")
        self.save_btn.clicked.connect(self._save_return)
        self.save_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_items(self):
        """Load items from PO"""
        # Get PO items
        items = self.container.purchase_order_controller.get_items(self.purchase_order.id)
        
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            # Get latest part data for current stock
            part = self.container.part_controller.get_part(item.part_id)
            current_stock = part.current_stock if part else 0
            
            # Part Name
            self.items_table.setItem(row, 0, QTableWidgetItem(item.part_name or "N/A"))
            
            # Received Qty (Max returnable)
            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setFlags(Qt.ItemIsEnabled)  # Read-only
            self.items_table.setItem(row, 1, qty_item)
            
            # Current Stock
            stock_item = QTableWidgetItem(str(current_stock))
            stock_item.setFlags(Qt.ItemIsEnabled)
            if current_stock < item.quantity:
                stock_item.setForeground(Qt.red)
            self.items_table.setItem(row, 2, stock_item)
            
            # Unit Cost
            cost_item = QTableWidgetItem(f"{item.unit_cost:.2f}")
            cost_item.setFlags(Qt.ItemIsEnabled)
            self.items_table.setItem(row, 3, cost_item)
            
            # Return Qty (Editable)
            return_qty = QLineEdit("0")
            return_qty.setValidator(None)  # TODO: Add int validator
            self.items_table.setCellWidget(row, 4, return_qty)
            
            # Condition (ComboBox)
            condition_cb = QComboBox()
            for condition in ReturnCondition.ALL:
                condition_cb.addItem(ReturnCondition.DISPLAY_NAMES.get(condition, condition), condition)
            self.items_table.setCellWidget(row, 5, condition_cb)
            
            # Total Refund (Calculated)
            self.items_table.setItem(row, 6, QTableWidgetItem("$0.00"))
            
            # Store item data and current stock
            item_data_obj = item
            item_data_obj.current_stock = current_stock  # Attach current stock to object for validation
            self.items_table.item(row, 0).setData(Qt.UserRole, item_data_obj)
            
            # Connect change signal
            return_qty.textChanged.connect(lambda text, r=row: self._update_row_total(r))
    
    def _update_row_total(self, row):
        """Update total for a row"""
        try:
            qty_widget = self.items_table.cellWidget(row, 4)
            qty = int(qty_widget.text() or 0)
            
            item = self.items_table.item(row, 0).data(Qt.UserRole)
            unit_cost = float(item.unit_cost)
            
            total = qty * unit_cost
            self.items_table.item(row, 6).setText(f"${total:.2f}")
            
        except ValueError:
            pass
    
    def _save_return(self):
        """Save the return"""
        reason = self.reason_input.text()
        if not reason:
            QMessageBox.warning(self, "Validation Error", "Please enter a reason for the return.")
            return
        
        # Collect items
        return_items = []
        total_amount = 0
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 4)
            try:
                qty = int(qty_widget.text() or 0)
            except ValueError:
                continue
                
            if qty > 0:
                item = self.items_table.item(row, 0).data(Qt.UserRole)
                current_stock = getattr(item, 'current_stock', 0)
                
                # Validate quantity against received quantity
                if qty > item.quantity:
                    QMessageBox.warning(self, "Validation Error", 
                                      f"Return quantity for {item.part_name} cannot exceed received quantity ({item.quantity}).")
                    return
                
                # Validate quantity against current stock
                if qty > current_stock:
                    QMessageBox.warning(self, "Validation Error", 
                                      f"Return quantity for {item.part_name} cannot exceed current stock ({current_stock}).\n"
                                      "You cannot return items that are not in stock.")
                    return
                
                condition_widget = self.items_table.cellWidget(row, 5)
                condition = condition_widget.currentData()
                
                return_items.append({
                    'part': item.part_id,
                    'quantity': qty,
                    'unit_cost': item.unit_cost,
                    'condition': condition
                })
                
                total_amount += qty * float(item.unit_cost)
        
        if not return_items:
            QMessageBox.warning(self, "Validation Error", "Please select at least one item to return.")
            return
        
        # Create return
        try:
            return_data = {
                'purchase_order': self.purchase_order.id,
                'reason': reason,
                'notes': self.notes_input.toPlainText(),
                'total_amount': total_amount,
                'status': 'draft'
            }
            
            # Create return header
            purchase_return = self.container.purchase_return_controller.create_return(return_data)
            
            # Add items
            for item_data in return_items:
                self.container.purchase_return_controller.add_item(purchase_return.id, item_data)
            
            QMessageBox.information(self, "Success", f"Return {purchase_return.return_number} created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create return: {str(e)}")
