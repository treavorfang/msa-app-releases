from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from views.inventory.modern_parts_list_tab import ModernPartsListTab
from views.inventory.modern_supplier_list_tab import ModernSupplierListTab
from views.inventory.modern_category_list_tab import ModernCategoryListTab
from views.inventory.financial.purchase_order_list_tab import PurchaseOrderListTab
from views.inventory.financial.invoice_list_tab import InvoiceListTab
from views.inventory.financial.payment_list_tab import PaymentListTab
from views.inventory.financial.purchase_return_list_tab import PurchaseReturnListTab
from views.inventory.financial.credit_note_list_tab import CreditNoteListTab
from utils.language_manager import language_manager

class ModernInventoryTab(QWidget):
    """Modern inventory tab container with lazy loading"""
    
    def __init__(self, container, user, parent=None):
        super().__init__(parent)
        self.container = container
        self.user = user
        self.lm = language_manager
        
        # Track which tabs have been initialized
        self._tab_instances = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #374151;
                border-top: none;
            }
            QTabBar::tab {
                padding: 12px 24px;
                border: 1px solid #374151;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                border-bottom: 2px solid #3B82F6;
            }
        """)
        
        # Define tab configurations (index, key, label)
        self.tab_config = [
            (0, "parts", self.lm.get("Inventory.parts", "Parts")),
            (1, "categories", self.lm.get("Inventory.categories", "Categories")),
            (2, "suppliers", self.lm.get("Inventory.suppliers", "Suppliers")),
            (3, "purchase_orders", self.lm.get("Inventory.purchase_orders", "Purchase Orders")),
            (4, "invoices", self.lm.get("Inventory.invoices", "Invoices")),
            (5, "payments", self.lm.get("Inventory.payments", "Payments")),
            (6, "returns", self.lm.get("Inventory.returns", "Returns")),
            (7, "credit_notes", self.lm.get("Inventory.credit_notes", "Credit Notes"))
        ]
        
        # Create placeholders for all tabs
        for idx, key, label in self.tab_config:
            self.tabs.addTab(QWidget(), label)
            
        layout.addWidget(self.tabs)
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Load the first tab immediately
        self._on_tab_changed(0)
    
    def _on_tab_changed(self, index):
        """Lazy load the tab at the given index if not already loaded"""
        if index < 0 or index >= len(self.tab_config):
            return
            
        key = self.tab_config[index][1]
        
        if key not in self._tab_instances:
            # Create and initialize the tab instance
            tab_widget = self._create_tab_by_key(key)
            if tab_widget:
                self._tab_instances[key] = tab_widget
                # Replace the placeholder widget
                self.tabs.removeTab(index)
                self.tabs.insertTab(index, tab_widget, self.tab_config[index][2])
                self.tabs.setCurrentIndex(index)
        
    def _create_tab_by_key(self, key):
        """Factory method to create tab instances on demand"""
        if key == "parts":
            return ModernPartsListTab(self.container, self.user, self)
        elif key == "categories":
            return ModernCategoryListTab(self.container, self.user, self)
        elif key == "suppliers":
            return ModernSupplierListTab(self.container, self)
        elif key == "purchase_orders":
            tab = PurchaseOrderListTab(self.container, user=self.user, parent=self)
            tab.data_changed.connect(self.refresh_all)
            return tab
        elif key == "invoices":
            return InvoiceListTab(self.container, self)
        elif key == "payments":
            return PaymentListTab(self.container, self)
        elif key == "returns":
            return PurchaseReturnListTab(self.container, user=self.user, parent=self)
        elif key == "credit_notes":
            tab = CreditNoteListTab(self.container, user=self.user, parent=self)
            tab.data_changed.connect(self.refresh_all)
            return tab
        return None

    def refresh(self):
        """Refresh the current tab"""
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
        elif hasattr(current_widget, '_load_data'):
            current_widget._load_data()
        elif hasattr(current_widget, '_load_purchase_orders'):
            current_widget._load_purchase_orders()
        elif hasattr(current_widget, '_load_invoices'):
            current_widget._load_invoices()
        elif hasattr(current_widget, '_load_payments'):
            current_widget._load_payments()
        elif hasattr(current_widget, '_load_returns'):
            current_widget._load_returns()
        elif hasattr(current_widget, '_load_credit_notes'):
            current_widget._load_credit_notes()
    
    def refresh_all(self):
        """Refresh all initialized tabs"""
        for tab in self._tab_instances.values():
            if hasattr(tab, 'refresh'):
                tab.refresh()
            elif hasattr(tab, '_load_data'):
                tab._load_data()
            elif hasattr(tab, '_load_purchase_orders'):
                tab._load_purchase_orders()
            elif hasattr(tab, '_load_invoices'):
                tab._load_invoices()
            elif hasattr(tab, '_load_payments'):
                tab._load_payments()
            elif hasattr(tab, '_load_returns'):
                tab._load_returns()
            elif hasattr(tab, '_load_credit_notes'):
                tab._load_credit_notes()
