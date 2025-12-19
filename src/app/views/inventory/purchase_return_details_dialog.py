from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QPushButton, QGroupBox, QFormLayout, QTextEdit)
from PySide6.QtCore import Qt
from config.constants import ReturnCondition

class PurchaseReturnDetailsDialog(QDialog):
    """Dialog for viewing purchase return details"""
    
    def __init__(self, container, purchase_return, parent=None):
        super().__init__(parent)
        self.container = container
        self.purchase_return = purchase_return
        self.setWindowTitle(f"Return Details: {purchase_return.return_number}")
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header Info
        info_group = QGroupBox("Return Information")
        info_layout = QFormLayout(info_group)
        
        self.lbl_return_number = QLabel()
        info_layout.addRow("Return Number:", self.lbl_return_number)
        
        self.lbl_status = QLabel()
        info_layout.addRow("Status:", self.lbl_status)
        
        self.lbl_date = QLabel()
        info_layout.addRow("Date:", self.lbl_date)
        
        self.lbl_supplier = QLabel()
        info_layout.addRow("Supplier:", self.lbl_supplier)
        
        self.lbl_po = QLabel()
        info_layout.addRow("Purchase Order:", self.lbl_po)
        
        self.lbl_reason = QLabel()
        info_layout.addRow("Reason:", self.lbl_reason)
        
        layout.addWidget(info_group)
        
        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setMaximumHeight(60)
        notes_layout.addWidget(self.txt_notes)
        layout.addWidget(notes_group)
        
        # Items
        items_group = QGroupBox("Returned Items")
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Part", "Quantity", "Unit Cost", "Condition", "Total Refund"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        items_layout.addWidget(self.items_table)
        
        layout.addWidget(items_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        
        self.lbl_total = QLabel("Total Refund: $0.00")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold;")
        footer_layout.addWidget(self.lbl_total)
        
        footer_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_btn)
        
        layout.addLayout(footer_layout)
        
    def _load_data(self):
        # Header data
        self.lbl_return_number.setText(self.purchase_return.return_number)
        self.lbl_status.setText(self.purchase_return.status.title())
        self.lbl_date.setText(self.purchase_return.return_date.strftime("%Y-%m-%d %H:%M"))
        
        po = self.purchase_return.purchase_order
        self.lbl_supplier.setText(po.supplier.name if po and po.supplier else "N/A")
        self.lbl_po.setText(po.po_number if po else "N/A")
        
        self.lbl_reason.setText(self.purchase_return.reason)
        self.txt_notes.setText(self.purchase_return.notes or "")
        
        # Items
        items = self.container.purchase_return_controller.get_items(self.purchase_return.id)
        self.items_table.setRowCount(len(items))
        
        total_amount = 0
        
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.part.name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"${item.unit_cost:.2f}"))
            
            condition_display = ReturnCondition.DISPLAY_NAMES.get(item.condition, item.condition)
            self.items_table.setItem(row, 3, QTableWidgetItem(condition_display))
            
            line_total = item.quantity * float(item.unit_cost)
            total_amount += line_total
            self.items_table.setItem(row, 4, QTableWidgetItem(f"${line_total:.2f}"))
            
        self.lbl_total.setText(f"Total Refund: ${total_amount:.2f}")
