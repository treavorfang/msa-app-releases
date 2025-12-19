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
    """Modern inventory tab container"""
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
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
        
        # Parts Tab
        self.parts_tab = ModernPartsListTab(self.container, self.user)
        self.tabs.addTab(self.parts_tab, self.lm.get("Inventory.parts", "Parts"))
        
        # Categories Tab
        self.categories_tab = ModernCategoryListTab(self.container, self.user)
        self.tabs.addTab(self.categories_tab, self.lm.get("Inventory.categories", "Categories"))
        
        # Suppliers Tab
        self.suppliers_tab = ModernSupplierListTab(self.container)
        self.tabs.addTab(self.suppliers_tab, self.lm.get("Inventory.suppliers", "Suppliers"))
        
        # Purchase Orders Tab (from Financial)
        self.purchase_orders_tab = PurchaseOrderListTab(self.container, user=self.user)
        self.purchase_orders_tab.data_changed.connect(self.refresh_all)
        self.tabs.addTab(self.purchase_orders_tab, self.lm.get("Inventory.purchase_orders", "Purchase Orders"))
        
        # Invoices Tab (from Financial)
        self.invoices_tab = InvoiceListTab(self.container)
        self.tabs.addTab(self.invoices_tab, self.lm.get("Inventory.invoices", "Invoices"))
        
        # Payments Tab (from Financial)
        self.payments_tab = PaymentListTab(self.container)
        self.tabs.addTab(self.payments_tab, self.lm.get("Inventory.payments", "Payments"))
        
        # Returns Tab (from Financial)
        self.returns_tab = PurchaseReturnListTab(self.container, user=self.user)
        self.tabs.addTab(self.returns_tab, self.lm.get("Inventory.returns", "Returns"))
        
        # Credit Notes Tab (from Financial)
        self.credit_notes_tab = CreditNoteListTab(self.container, user=self.user)
        self.credit_notes_tab.data_changed.connect(self.refresh_all)
        self.tabs.addTab(self.credit_notes_tab, self.lm.get("Inventory.credit_notes", "Credit Notes"))
        
        layout.addWidget(self.tabs)
    
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
        """Refresh all tabs"""
        # Refresh inventory tabs
        if hasattr(self.parts_tab, 'refresh'):
            self.parts_tab.refresh()
        if hasattr(self.categories_tab, 'refresh'):
            self.categories_tab.refresh()
        if hasattr(self.suppliers_tab, 'refresh'):
            self.suppliers_tab.refresh()
            
        # Refresh financial tabs
        if hasattr(self.purchase_orders_tab, '_load_purchase_orders'):
            self.purchase_orders_tab._load_purchase_orders()
        if hasattr(self.invoices_tab, '_load_invoices'):
            self.invoices_tab._load_invoices()
        if hasattr(self.payments_tab, '_load_payments'):
            self.payments_tab._load_payments()
        if hasattr(self.returns_tab, '_load_returns'):
            self.returns_tab._load_returns()
        if hasattr(self.credit_notes_tab, '_load_credit_notes'):
            self.credit_notes_tab._load_credit_notes()
