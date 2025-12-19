from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QLineEdit, QMessageBox, QComboBox)
from PySide6.QtCore import Qt
from views.inventory.purchase_order_dialog import PurchaseOrderDialog

class PurchaseOrderListDialog(QDialog):
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.setWindowTitle("Purchase Orders")
        self.resize(1000, 600)
        self._setup_ui()
        self._load_data()
        
        # Connect signals
        self.container.purchase_order_controller.po_created.connect(self._load_data)
        self.container.purchase_order_controller.po_updated.connect(self._load_data)
        self.container.purchase_order_controller.po_deleted.connect(self._load_data)
        self.container.purchase_order_controller.status_changed.connect(self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Actions
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search PO Number...")
        self.search_input.textChanged.connect(self._on_search)
        top_layout.addWidget(self.search_input)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "draft", "sent", "received", "cancelled"])
        self.status_filter.currentTextChanged.connect(self._on_filter)
        top_layout.addWidget(self.status_filter)
        
        self.new_btn = QPushButton("New Purchase Order")
        self.new_btn.clicked.connect(self._on_new)
        top_layout.addWidget(self.new_btn)
        
        layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PO Number", "Supplier", "Status", "Date", "Total Amount", "Expected Delivery"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
        
        # Close button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

    def _load_data(self):
        status = self.status_filter.currentText()
        if status == "All Status":
            status = None
            
        pos = self.container.purchase_order_controller.list_purchase_orders(status=status)
        self.table.setRowCount(len(pos))
        
        for row, po in enumerate(pos):
            self.table.setItem(row, 0, QTableWidgetItem(po.po_number))
            self.table.setItem(row, 1, QTableWidgetItem(po.supplier_name if po.supplier_name else "N/A"))
            self.table.setItem(row, 2, QTableWidgetItem(po.status))
            self.table.setItem(row, 3, QTableWidgetItem(str(po.order_date.date())))
            self.table.setItem(row, 4, QTableWidgetItem(f"${po.total_amount:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(po.expected_delivery.date()) if po.expected_delivery else "N/A"))
            
            # Store ID in first item
            self.table.item(row, 0).setData(Qt.UserRole, po.id)

    def _on_search(self, text):
        if text:
            pos = self.container.purchase_order_controller.search_purchase_orders(text)
            self.table.setRowCount(len(pos))
            for row, po in enumerate(pos):
                self.table.setItem(row, 0, QTableWidgetItem(po.po_number))
                self.table.setItem(row, 1, QTableWidgetItem(po.supplier_name if po.supplier_name else "N/A"))
                self.table.setItem(row, 2, QTableWidgetItem(po.status))
                self.table.setItem(row, 3, QTableWidgetItem(str(po.order_date.date())))
                self.table.setItem(row, 4, QTableWidgetItem(f"${po.total_amount:.2f}"))
                self.table.setItem(row, 5, QTableWidgetItem(str(po.expected_delivery.date()) if po.expected_delivery else "N/A"))
                self.table.item(row, 0).setData(Qt.UserRole, po.id)
        else:
            self._load_data()

    def _on_filter(self):
        self._load_data()

    def _on_new(self):
        dialog = PurchaseOrderDialog(self.container, parent=self)
        dialog.exec()

    def _on_double_click(self, index):
        po_id = self.table.item(index.row(), 0).data(Qt.UserRole)
        po = self.container.purchase_order_controller.get_purchase_order(po_id)
        if po:
            dialog = PurchaseOrderDialog(self.container, po, parent=self)
            dialog.exec()
