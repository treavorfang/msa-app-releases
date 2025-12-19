from typing import Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QLineEdit, QLabel, QComboBox, QDateEdit, QFormLayout,
                               QGroupBox, QMessageBox)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from views.inventory.add_po_item_dialog import AddPOItemDialog
from dtos.purchase_order_dto import PurchaseOrderDTO
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from decimal import Decimal

class PurchaseOrderDialog(QDialog):
    def __init__(self, container, po: Optional[PurchaseOrderDTO] = None, parent=None):
        super().__init__(parent)
        self.container = container
        self.po = po  # Type: PurchaseOrderDTO
        self.lm = language_manager
        self.cf = currency_formatter
        
        # Set window title
        if po:
            title = self.lm.get("Inventory.purchase_order_details", "Purchase Order Details")
        else:
            title = self.lm.get("Inventory.new_purchase_order", "New Purchase Order")
        self.setWindowTitle(title)
        self.resize(900, 700)
        self._setup_ui()
        
        if po:
            self._load_data()
            self._load_items()
            
            # Connect signals for item updates
            self.container.purchase_order_controller.items_changed.connect(self._on_items_changed)
            self.container.purchase_order_controller.status_changed.connect(self._on_status_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header Info
        info_group = QGroupBox(self.lm.get("Inventory.order_information", "Order Information"))
        form_layout = QFormLayout(info_group)
        
        self.po_number = QLineEdit()
        if not self.po:
            # Generate PO number in RPT format: PO-YYMMDD-####
            self.po_number.setText(self._generate_po_number())
        form_layout.addRow(self.lm.get("Inventory.po_number", "PO Number") + ":", self.po_number)
        
        self.supplier_combo = QComboBox()
        # REFACTORED: Use Controller/DTO instead of Repository
        suppliers = self.container.supplier_controller.list_suppliers()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)
        form_layout.addRow(self.lm.get("Inventory.supplier", "Supplier") + ":", self.supplier_combo)
        
        self.status_combo = QComboBox()
        # Add localized status options
        self.status_combo.addItem(self.lm.get("Inventory.status_draft", "Draft"), "draft")
        self.status_combo.addItem(self.lm.get("Inventory.status_sent", "Sent"), "sent")
        self.status_combo.addItem(self.lm.get("Common.received", "Received"), "received")
        self.status_combo.addItem(self.lm.get("Common.cancelled", "Cancelled"), "cancelled")
        self.status_combo.setEnabled(False)  # Status managed via actions
        form_layout.addRow(self.lm.get("Common.status", "Status") + ":", self.status_combo)
        
        self.expected_date = QDateEdit()
        self.expected_date.setCalendarPopup(True)
        self.expected_date.setDate(QDate.currentDate().addDays(7))
        form_layout.addRow(self.lm.get("Inventory.expected_delivery", "Expected Delivery") + ":", self.expected_date)
        
        layout.addWidget(info_group)
        
        # Items
        items_group = QGroupBox(self.lm.get("Inventory.line_items", "Line Items"))
        items_layout = QVBoxLayout(items_group)
        
        actions_layout = QHBoxLayout()
        self.add_item_btn = QPushButton(self.lm.get("Inventory.add_item", "Add Item"))
        self.add_item_btn.clicked.connect(self._on_add_item)
        self.remove_item_btn = QPushButton(self.lm.get("Inventory.remove_item", "Remove Item"))
        self.remove_item_btn.clicked.connect(self._on_remove_item)
        actions_layout.addWidget(self.add_item_btn)
        actions_layout.addWidget(self.remove_item_btn)
        actions_layout.addStretch()
        
        # Total Amount Display (on the right side)
        total_label = QLabel(self.lm.get("Inventory.total_amount", "Total Amount") + ":")
        total_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        actions_layout.addWidget(total_label)
        
        self.total_amount_label = QLabel(self.cf.format(0))
        self.total_amount_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3B82F6; padding: 4px 8px; background-color: rgba(59, 130, 246, 0.1); border-radius: 4px;")
        actions_layout.addWidget(self.total_amount_label)
        
        items_layout.addLayout(actions_layout)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            self.lm.get("Inventory.part", "Part"),
            self.lm.get("Inventory.sku", "SKU"),
            self.lm.get("Common.quantity", "Quantity"),
            self.lm.get("Inventory.unit_cost", "Unit Cost"),
            self.lm.get("Inventory.total_cost", "Total Cost")
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        items_layout.addWidget(self.items_table)
        
        layout.addWidget(items_group)
        
        # Footer Actions
        btn_layout = QHBoxLayout()
        
        self.receive_btn = QPushButton(self.lm.get("Inventory.receive_order", "Receive Order"))
        self.receive_btn.clicked.connect(self._on_receive)
        btn_layout.addWidget(self.receive_btn)

        self.send_btn = QPushButton(self.lm.get("Inventory.send_order", "Send Order"))
        self.send_btn.clicked.connect(self._on_send)
        btn_layout.addWidget(self.send_btn)
        
        self.cancel_btn = QPushButton(self.lm.get("Inventory.cancel_order", "Cancel Order"))
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        
        if not self.po:
            self.receive_btn.hide()
            self.send_btn.hide()
            self.cancel_btn.hide()
            
        btn_layout.addStretch()
        
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.po_number.setText(self.po.po_number)
        index = self.supplier_combo.findData(self.po.supplier_id)
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
        # Find and set status by data value
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.po.status:
                self.status_combo.setCurrentIndex(i)
                break
        if self.po.expected_delivery:
            # DTO might return datetime or None
            self.expected_date.setDate(self.po.expected_delivery.date())
            
        self._update_ui_state()

    def _load_items(self):
        # Controller returns PurchaseOrderItemDTOs
        items = self.container.purchase_order_controller.get_items(self.po.id)
        self.items_table.setRowCount(len(items))
        total = Decimal('0')
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.part_name or self.lm.get("Common.not_applicable", "N/A")))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.part_sku or self.lm.get("Common.not_applicable", "N/A")))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
            self.items_table.setItem(row, 3, QTableWidgetItem(self.cf.format(item.unit_cost)))
            self.items_table.setItem(row, 4, QTableWidgetItem(self.cf.format(item.total_cost)))
            self.items_table.item(row, 0).setData(Qt.UserRole, item.id)
            total += Decimal(str(item.total_cost))
        
        # Update total amount display
        self.total_amount_label.setText(self.cf.format(total))

    def _update_ui_state(self):
        is_draft = self.po.status == 'draft'
        self.add_item_btn.setEnabled(is_draft)
        self.remove_item_btn.setEnabled(is_draft)
        self.receive_btn.setEnabled(self.po.status == 'sent')
        self.send_btn.setEnabled(is_draft)
        self.cancel_btn.setEnabled(self.po.status in ['draft', 'sent'])
        self.save_btn.setEnabled(is_draft)
        self.po_number.setEnabled(is_draft)
        self.supplier_combo.setEnabled(is_draft)
        self.expected_date.setEnabled(is_draft)

    def _on_save(self):
        # Validate supplier is selected
        if self.supplier_combo.currentData() is None:
            QMessageBox.warning(
                self, 
                self.lm.get("Validation.validation_error", "Validation Error"), 
                self.lm.get("Inventory.supplier_required", "Please select a supplier before creating a purchase order.")
            )
            return
            
        data = {
            'po_number': self.po_number.text(),
            'supplier': self.supplier_combo.currentData(),
            'expected_delivery': datetime.combine(self.expected_date.date().toPython(), datetime.min.time()),
            'status': 'draft'
        }
        
        if self.po:
            self.container.purchase_order_controller.update_purchase_order(self.po.id, data)
            QMessageBox.information(
                self, 
                self.lm.get("Common.success", "Success"), 
                self.lm.get("Inventory.po_updated", "Purchase Order updated successfully!")
            )
            self.accept()
        else:
            po = self.container.purchase_order_controller.create_purchase_order(data)
            if po:
                self.po = po
                self.setWindowTitle(self.lm.get("Inventory.purchase_order_details", "Purchase Order Details"))
                self._load_data()
                self._load_items()
                self.receive_btn.show()
                self.send_btn.show()
                self.cancel_btn.show()
                self._update_ui_state()
                msg = self.lm.get("Inventory.po_created", "Purchase Order {po_number} created successfully!\\nYou can now add items.")
                QMessageBox.information(
                    self, 
                    self.lm.get("Common.success", "Success"), 
                    msg.format(po_number=po.po_number)
                )

    def _on_add_item(self):
        # Auto-save if not saved yet
        if not self.po:
            self._on_save()
            if not self.po:  # If save failed or was cancelled
                return
            
        dialog = AddPOItemDialog(self.container, parent=self)
        if dialog.exec():
            part, quantity, unit_cost = dialog.get_selected_data()
            if part:
                self.container.purchase_order_controller.add_item(self.po.id, {
                    'part': part.id,
                    'quantity': quantity,
                    'unit_cost': unit_cost
                })


    def _on_remove_item(self):
        row = self.items_table.currentRow()
        if row >= 0:
            item_id = self.items_table.item(row, 0).data(Qt.UserRole)
            self.container.purchase_order_controller.remove_item(item_id)

    def _on_send(self):
        reply = QMessageBox.question(
            self, 
            self.lm.get("Inventory.confirm_send", "Confirm Send"), 
            self.lm.get("Inventory.confirm_send_msg", "Are you sure you want to send this order? You will not be able to edit items after sending."),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.container.purchase_order_controller.update_status(self.po.id, 'sent')

    def _on_receive(self):
        reply = QMessageBox.question(
            self, 
            self.lm.get("Inventory.confirm_receive", "Confirm Receipt"), 
            self.lm.get("Inventory.confirm_receive_msg", "Are you sure you want to receive this order? This will update inventory stock."),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.container.purchase_order_controller.update_status(self.po.id, 'received')

    def _on_cancel(self):
        reply = QMessageBox.question(
            self, 
            self.lm.get("Inventory.confirm_cancel", "Confirm Cancel"), 
            self.lm.get("Inventory.confirm_cancel_msg", "Are you sure you want to cancel this order?"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.container.purchase_order_controller.update_status(self.po.id, 'cancelled')

    def _on_items_changed(self, po_id):
        if self.po and self.po.id == po_id:
            self._load_items()

    def _on_status_changed(self, po_id, new_status):
        if self.po and self.po.id == po_id:
            self.po.status = new_status
            self._load_data()
    
    def _generate_po_number(self) -> str:
        """Generate PO number using model logic."""
        from models.purchase_order import PurchaseOrder
        
        # Get branch ID (default to 1 if not available)
        branch_id = 1
        if hasattr(self.container, 'current_user') and self.container.current_user:
            if hasattr(self.container.current_user, 'branch_id'):
                branch_id = self.container.current_user.branch_id or 1
        
        return PurchaseOrder.generate_po_number(branch_id=branch_id)
