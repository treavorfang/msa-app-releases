# src/app/views/inventory/restock_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QSpinBox, QPushButton, QLabel, QMessageBox, 
                              QGroupBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt
from utils.language_manager import language_manager

class RestockDialog(QDialog):
    """Dialog for restocking parts"""
    
    def __init__(self, container, part, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.part = part
        self.user = user
        self.part_service = container.part_service
        self.lm = language_manager
        self._setup_ui()

    def _setup_ui(self):
        title = f"{self.lm.get('Inventory.restock_part', 'Restock Part')} - {self.part.name}"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Part info section
        info_group = QGroupBox(self.lm.get("Inventory.part_info", "Part Information"))
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow(f"{self.lm.get('Inventory.sku', 'SKU')}:", QLabel(self.part.sku))
        info_layout.addRow(f"{self.lm.get('Inventory.name', 'Name')}:", QLabel(self.part.name))
        info_layout.addRow(f"{self.lm.get('Inventory.brand', 'Brand')}:", QLabel(self.part.brand or "N/A"))
        info_layout.addRow(f"{self.lm.get('Inventory.current_stock', 'Current Stock')}:", QLabel(f"<b>{self.part.current_stock}</b>"))
        info_layout.addRow(f"{self.lm.get('Inventory.min_stock', 'Min Stock Level')}:", QLabel(str(self.part.min_stock_level)))
        
        layout.addWidget(info_group)
        
        # Restock options
        restock_group = QGroupBox(self.lm.get("Inventory.restock_options", "Restock Options"))
        restock_layout = QVBoxLayout(restock_group)
        
        # Radio buttons for operation type
        self.operation_group = QButtonGroup(self)
        self.add_radio = QRadioButton(self.lm.get("Inventory.add_to_stock", "Add to stock"))
        self.set_radio = QRadioButton(self.lm.get("Inventory.set_stock_to", "Set stock to"))
        self.remove_radio = QRadioButton(self.lm.get("Inventory.remove_from_stock", "Remove from stock"))
        
        self.add_radio.setChecked(True)
        
        self.operation_group.addButton(self.add_radio, 1)
        self.operation_group.addButton(self.set_radio, 2)
        self.operation_group.addButton(self.remove_radio, 3)
        
        restock_layout.addWidget(self.add_radio)
        restock_layout.addWidget(self.set_radio)
        restock_layout.addWidget(self.remove_radio)
        
        # Quantity input
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel(f"{self.lm.get('Common.quantity', 'Quantity')}:"))
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(99999)
        self.quantity_input.setValue(0)
        self.quantity_input.valueChanged.connect(self._update_preview)
        
        quantity_layout.addWidget(self.quantity_input)
        quantity_layout.addStretch()
        
        restock_layout.addLayout(quantity_layout)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("font-weight: bold; color: #2ecc71; padding: 10px;")
        self._update_preview()
        restock_layout.addWidget(self.preview_label)
        
        layout.addWidget(restock_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton(self.lm.get("Inventory.update_stock", "Update Stock"))
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Connect radio buttons to update preview
        self.add_radio.toggled.connect(self._update_preview)
        self.set_radio.toggled.connect(self._update_preview)
        self.remove_radio.toggled.connect(self._update_preview)
    
    def _update_preview(self):
        """Update the preview of new stock level"""
        quantity = self.quantity_input.value()
        current = self.part.current_stock
        
        if self.add_radio.isChecked():
            new_stock = current + quantity
            operation = f"{self.lm.get('Common.add', 'Add')} {quantity}"
        elif self.set_radio.isChecked():
            new_stock = quantity
            operation = f"{self.lm.get('Common.set_to', 'Set to')} {quantity}"
        else:  # remove
            new_stock = max(0, current - quantity)
            operation = f"{self.lm.get('Common.remove', 'Remove')} {quantity}"
        
        # Color code based on stock level
        if new_stock == 0:
            color = "#e74c3c"  # Red
        elif new_stock <= self.part.min_stock_level:
            color = "#f39c12"  # Orange
        else:
            color = "#2ecc71"  # Green
        
        new_stock_text = self.lm.get('Inventory.new_stock', 'New Stock')
        self.preview_label.setText(
            f"{operation} → {new_stock_text}: <span style='color: {color};'>{new_stock}</span>"
        )
        self.preview_label.setStyleSheet(f"font-weight: bold; padding: 10px;")
    
    def _on_save(self):
        """Handle save button click"""
        quantity = self.quantity_input.value()
        
        if quantity == 0 and not self.set_radio.isChecked():
            QMessageBox.warning(self, self.lm.get("Validation.invalid_quantity", "Invalid Quantity"), 
                              self.lm.get("Validation.enter_quantity_gt_0", "Please enter a quantity greater than 0"))
            return
        
        # Calculate new stock
        current = self.part.current_stock
        if self.add_radio.isChecked():
            new_stock = current + quantity
        elif self.set_radio.isChecked():
            new_stock = quantity
        else:  # remove
            new_stock = max(0, current - quantity)
            if new_stock == 0 and current - quantity < 0:
                msg = self.lm.get("Inventory.insufficient_stock_warning", 
                                "Cannot remove {qty} units. Only {curr} units available.\n\nSet stock to 0?").format(qty=quantity, curr=current)
                reply = QMessageBox.question(
                    self, 
                    self.lm.get("Inventory.insufficient_stock", "Insufficient Stock"),
                    msg,
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        # Confirm the action
        msg = self.lm.get("Inventory.confirm_stock_update_msg", "Update stock from {old} to {new}?").format(old=current, new=new_stock)
        reply = QMessageBox.question(
            self,
            self.lm.get("Inventory.confirm_stock_update", "Confirm Stock Update"),
            msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Update stock using controller to trigger EventBus events
                operation = "add" if self.add_radio.isChecked() else "set" if self.set_radio.isChecked() else "remove"
                
                # Localize the reason if possible, or keep as technical log
                reason_text = f"Stock update via Restock Dialog ({operation})"
                
                update_data = {
                    'stock': new_stock,
                    'price_change_reason': reason_text
                }
                updated_part = self.container.part_controller.update_part(
                    self.part.id,
                    **update_data,
                    user=self.user
                )
                if updated_part:
                    success_msg = self.lm.get("Inventory.stock_update_success", "Stock updated successfully!\n\nOld: {old}\nNew: {new}").format(old=current, new=new_stock)
                    QMessageBox.information(
                        self, 
                        self.lm.get("Common.success", "Success"), 
                        success_msg
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, self.lm.get("Common.error", "Error"), self.lm.get("Inventory.stock_update_failed", "Failed to update stock"))
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Inventory.stock_update_failed', 'Failed to update stock')}: {str(e)}")
