# src/app/views/inventory/part_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QGroupBox, QTabWidget, 
                              QWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from datetime import datetime
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class PartDetailsDialog(QDialog):
    """Dialog for viewing detailed part information"""
    
    def __init__(self, container, part, parent=None):
        super().__init__(parent)
        self.container = container
        self.part = part
        self.lm = language_manager
        self.cf = currency_formatter
        self._setup_ui()
        
    def _setup_ui(self):
        title = f"{self.lm.get('Inventory.part_details_title', 'Part Details')} - {self.part.name}"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Header with part name
        header = QLabel(f"📦 {self.part.name}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = self._create_basic_info_tab()
        tabs.addTab(basic_tab, self.lm.get("Inventory.basic_info", "Basic Info"))
        
        # Stock Info Tab
        stock_tab = self._create_stock_info_tab()
        tabs.addTab(stock_tab, self.lm.get("Inventory.stock_info", "Stock Info"))
        
        # Pricing Tab
        pricing_tab = self._create_pricing_tab()
        tabs.addTab(pricing_tab, self.lm.get("Inventory.pricing", "Pricing"))
        
        # Price History Tab
        history_tab = self._create_price_history_tab()
        tabs.addTab(history_tab, self.lm.get("Inventory.price_history", "Price History"))
        
        # Inventory Log Tab
        log_tab = self._create_inventory_log_tab()
        tabs.addTab(log_tab, self.lm.get("Inventory.inventory_log", "Inventory Log"))
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_basic_info_tab(self):
        """Create basic information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Basic details group
        details_group = QGroupBox(self.lm.get("Inventory.part_details_title", "Part Details"))
        details_layout = QFormLayout(details_group)
        
        details_layout.addRow(f"{self.lm.get('Inventory.sku', 'SKU')}:", QLabel(f"<b>{self.part.sku}</b>"))
        details_layout.addRow(f"{self.lm.get('Inventory.barcode', 'Barcode')}:", QLabel(self.part.barcode or "N/A"))
        details_layout.addRow(f"{self.lm.get('Inventory.part_name', 'Name')}:", QLabel(self.part.name))
        details_layout.addRow(f"{self.lm.get('Inventory.brand', 'Brand')}:", QLabel(self.part.brand or "N/A"))
        
        category_name = self.part.category_name or "N/A"
        details_layout.addRow(f"{self.lm.get('Inventory.category', 'Category')}:", QLabel(category_name))
        
        details_layout.addRow(f"{self.lm.get('Inventory.compatible_models', 'Model Compatibility')}:", 
                            QLabel(self.part.model_compatibility or "N/A"))
        
        layout.addWidget(details_group)
        
        # Metadata group
        meta_group = QGroupBox(self.lm.get("Inventory.metadata", "Metadata"))
        meta_layout = QFormLayout(meta_group)
        
        created_at = self.part.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(self.part, 'created_at') and self.part.created_at else "N/A"
        updated_at = self.part.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(self.part, 'updated_at') and self.part.updated_at else "N/A"
        
        meta_layout.addRow(f"{self.lm.get('Common.created', 'Created')}:", QLabel(created_at))
        meta_layout.addRow(f"{self.lm.get('Common.last_updated', 'Last Updated')}:", QLabel(updated_at))
        
        layout.addWidget(meta_group)
        layout.addStretch()
        
        return widget
    
    def _create_stock_info_tab(self):
        """Create stock information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stock levels group
        stock_group = QGroupBox(self.lm.get("Inventory.stock_levels", "Stock Levels"))
        stock_layout = QFormLayout(stock_group)
        
        # Current stock with color coding
        current_stock = self.part.current_stock
        min_stock = self.part.min_stock_level
        
        if current_stock == 0:
            stock_color = "#e74c3c"  # Red
            stock_status = self.lm.get("Inventory.out_of_stock", "OUT OF STOCK")
        elif current_stock <= min_stock:
            stock_color = "#f39c12"  # Orange
            stock_status = self.lm.get("Inventory.low_stock", "LOW STOCK")
        else:
            stock_color = "#2ecc71"  # Green
            stock_status = self.lm.get("Inventory.in_stock", "IN STOCK")
        
        stock_label = QLabel(f"<span style='color: {stock_color}; font-size: 24px; font-weight: bold;'>{current_stock}</span>")
        stock_layout.addRow(f"{self.lm.get('Inventory.current_stock', 'Current Stock')}:", stock_label)
        
        status_label = QLabel(f"<span style='color: {stock_color}; font-weight: bold;'>{stock_status}</span>")
        stock_layout.addRow(f"{self.lm.get('Common.status', 'Status')}:", status_label)
        
        stock_layout.addRow(f"{self.lm.get('Inventory.min_stock', 'Minimum Stock Level')}:", QLabel(str(min_stock)))
        
        # Calculate stock difference
        diff = current_stock - min_stock
        if diff > 0:
            diff_text = self.lm.get("Inventory.above_minimum", "+{0} above minimum").format(diff)
            diff_color = "#2ecc71"
        elif diff == 0:
            diff_text = self.lm.get("Inventory.at_minimum", "At minimum level")
            diff_color = "#f39c12"
        else:
            diff_text = self.lm.get("Inventory.below_minimum", "{0} below minimum").format(diff)
            diff_color = "#e74c3c"
        
        diff_label = QLabel(f"<span style='color: {diff_color};'>{diff_text}</span>")
        stock_layout.addRow(f"{self.lm.get('Inventory.difference', 'Difference')}:", diff_label)
        
        layout.addWidget(stock_group)
        
        # Stock value group
        value_group = QGroupBox(self.lm.get("Inventory.stock_value", "Stock Value"))
        value_layout = QFormLayout(value_group)
        
        unit_value = float(self.part.cost_price)  # Convert Decimal to float
        total_value = unit_value * current_stock
        
        value_layout.addRow(f"{self.lm.get('Inventory.unit_cost', 'Unit Cost')}:", QLabel(self.cf.format(unit_value)))
        value_layout.addRow(f"{self.lm.get('Inventory.total_value', 'Total Value')}:", QLabel(f"<b>{self.cf.format(total_value)}</b>"))
        
        layout.addWidget(value_group)
        layout.addStretch()
        
        return widget
    
    def _create_pricing_tab(self):
        """Create pricing information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Pricing group
        pricing_group = QGroupBox(self.lm.get("Inventory.pricing_info", "Pricing Information"))
        pricing_layout = QFormLayout(pricing_group)
        
        cost_price = float(self.part.cost_price)  # Convert Decimal to float
        
        # Calculate suggested retail prices (example margins)
        retail_30 = cost_price * 1.30  # 30% markup
        retail_50 = cost_price * 1.50  # 50% markup
        retail_100 = cost_price * 2.00  # 100% markup
        
        pricing_layout.addRow(f"{self.lm.get('Inventory.cost_price', 'Cost Price')}:", QLabel(f"<b>{self.cf.format(cost_price)}</b>"))
        pricing_layout.addRow("", QLabel(""))  # Spacer
        pricing_layout.addRow(f"{self.lm.get('Inventory.suggested_retail_30', 'Suggested Retail (30%)')}:", QLabel(self.cf.format(retail_30)))
        pricing_layout.addRow(f"{self.lm.get('Inventory.suggested_retail_50', 'Suggested Retail (50%)')}:", QLabel(self.cf.format(retail_50)))
        pricing_layout.addRow(f"{self.lm.get('Inventory.suggested_retail_100', 'Suggested Retail (100%)')}:", QLabel(self.cf.format(retail_100)))
        
        layout.addWidget(pricing_group)
        
        # Value summary
        summary_group = QGroupBox(self.lm.get("Inventory.value_summary", "Value Summary"))
        summary_layout = QFormLayout(summary_group)
        
        total_cost = cost_price * self.part.current_stock
        potential_30 = retail_30 * self.part.current_stock
        potential_50 = retail_50 * self.part.current_stock
        
        summary_layout.addRow(f"{self.lm.get('Inventory.total_cost_all_stock', 'Total Cost (all stock)')}:", QLabel(self.cf.format(total_cost)))
        summary_layout.addRow(f"{self.lm.get('Inventory.potential_value_30', 'Potential Value (30%)')}:", QLabel(self.cf.format(potential_30)))
        summary_layout.addRow(f"{self.lm.get('Inventory.potential_value_50', 'Potential Value (50%)')}:", QLabel(self.cf.format(potential_50)))
        
        profit_30 = potential_30 - total_cost
        summary_layout.addRow(f"{self.lm.get('Inventory.potential_profit_30', 'Potential Profit (30%)')}:", 
                            QLabel(f"<span style='color: #2ecc71;'>{self.cf.format(profit_30)}</span>"))
        
        layout.addWidget(summary_group)
        layout.addStretch()
        
        return widget
    
    def _create_price_history_tab(self):
        """Create price history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel(self.lm.get("Inventory.price_change_history", "Price Change History"))
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        # Price history table
        history_table = QTableWidget()
        history_table.setColumnCount(4)
        history_table.setHorizontalHeaderLabels([
            self.lm.get("Common.date", "Date"), 
            self.lm.get("Inventory.old_price", "Old Price"), 
            self.lm.get("Inventory.new_price", "New Price"), 
            self.lm.get("Inventory.reason", "Reason")
        ])
        history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_table.setSelectionBehavior(QTableWidget.SelectRows)
        history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Get price history from repository
        from repositories.price_history_repository import PriceHistoryRepository
        price_repo = PriceHistoryRepository()
        history = price_repo.get_history_for_part(self.part.id)
        
        history_table.setRowCount(len(history))
        
        for row, entry in enumerate(history):
            # Date
            date_str = entry.changed_at.strftime("%Y-%m-%d %H:%M")
            history_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Old Price
            old_price = self.cf.format(float(entry.old_price))
            history_table.setItem(row, 1, QTableWidgetItem(old_price))
            
            # New Price
            new_price = self.cf.format(float(entry.new_price))
            new_price_item = QTableWidgetItem(new_price)
            
            # Color code based on price change
            if entry.new_price > entry.old_price:
                new_price_item.setForeground(Qt.red)  # Price increased
            elif entry.new_price < entry.old_price:
                new_price_item.setForeground(Qt.green)  # Price decreased
            
            history_table.setItem(row, 2, new_price_item)
            
            # Reason
            reason = entry.change_reason or "N/A"
            history_table.setItem(row, 3, QTableWidgetItem(reason))
        
        layout.addWidget(history_table)
        
        # Summary info
        if history:
            latest = history[0]
            summary_label = QLabel(
                self.lm.get("Inventory.latest_price_format", "Latest price: {0} (changed on {1})").format(
                    self.cf.format(float(latest.new_price)), 
                    latest.changed_at.strftime('%Y-%m-%d')
                )
            )
            summary_label.setStyleSheet("padding: 5px; font-style: italic;")
            layout.addWidget(summary_label)
        else:
            no_history_label = QLabel(self.lm.get("Inventory.no_price_history", "No price history available for this part."))
            no_history_label.setStyleSheet("padding: 10px; font-style: italic; color: gray;")
            layout.addWidget(no_history_label)
        
        return widget
    
    def _create_inventory_log_tab(self):
        """Create inventory log tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel(self.lm.get("Inventory.stock_movement_history", "Stock Movement History"))
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        # Inventory log table
        log_table = QTableWidget()
        log_table.setColumnCount(6)
        log_table.setHorizontalHeaderLabels([
            self.lm.get("Common.date", "Date"), 
            self.lm.get("Common.action", "Action"), 
            self.lm.get("Inventory.quantity", "Quantity"), 
            self.lm.get("Inventory.reference_type", "Reference Type"), 
            self.lm.get("Inventory.reference_id", "Reference ID"), 
            self.lm.get("Common.notes", "Notes")
        ])
        log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        log_table.setSelectionBehavior(QTableWidget.SelectRows)
        log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Get inventory logs from repository
        from repositories.inventory_log_repository import InventoryLogRepository
        log_repo = InventoryLogRepository()
        logs = log_repo.get_logs_for_part(self.part.id, limit=100)
        
        log_table.setRowCount(len(logs))
        
        for row, log_entry in enumerate(logs):
            # Date
            date_str = log_entry.logged_at.strftime("%Y-%m-%d %H:%M")
            log_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Action Type
            action_item = QTableWidgetItem(log_entry.action_type.upper())
            if log_entry.action_type == 'in':
                action_item.setForeground(Qt.green)
            elif log_entry.action_type == 'out':
                action_item.setForeground(Qt.red)
            else:  # adjust
                action_item.setForeground(Qt.blue)
            log_table.setItem(row, 1, action_item)
            
            # Quantity
            qty_str = str(log_entry.quantity)
            if log_entry.action_type == 'in':
                qty_str = f"+{qty_str}"
            elif log_entry.action_type == 'out':
                qty_str = f"-{qty_str}"
            log_table.setItem(row, 2, QTableWidgetItem(qty_str))
            
            # Reference Type
            ref_type = log_entry.reference_type or "N/A"
            log_table.setItem(row, 3, QTableWidgetItem(ref_type))
            
            # Reference ID
            ref_id = str(log_entry.reference_id) if log_entry.reference_id else "N/A"
            log_table.setItem(row, 4, QTableWidgetItem(ref_id))
            
            # Notes
            notes = log_entry.notes or "N/A"
            log_table.setItem(row, 5, QTableWidgetItem(notes))
        
        layout.addWidget(log_table)
        
        # Summary info
        if logs:
            latest = logs[0]
            summary_label = QLabel(
                self.lm.get("Inventory.latest_movement_format", "Latest change: {0} {1} units on {2}").format(
                    latest.action_type.upper(),
                    latest.quantity,
                    latest.logged_at.strftime('%Y-%m-%d %H:%M')
                )
            )
            summary_label.setStyleSheet("padding: 5px; font-style: italic;")
            layout.addWidget(summary_label)
        else:
            no_log_label = QLabel(self.lm.get("Inventory.no_inventory_movements", "No inventory movements recorded for this part."))
            no_log_label.setStyleSheet("padding: 10px; font-style: italic; color: gray;")
            layout.addWidget(no_log_label)
        
        return widget

