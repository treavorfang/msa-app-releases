# src/app/views/components/customer_input.py
import re
from PySide6.QtWidgets import QComboBox, QMessageBox, QCompleter, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from services.customer_service import CustomerService
from utils.language_manager import language_manager  # Add this import

class CustomerInput(QWidget):
    def __init__(self, customer_service: CustomerService = None):
        super().__init__()
        self.customer_service = customer_service or CustomerService()
        self.lm = language_manager  # Initialize language manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.NoInsert)
        
        # Localize placeholder text
        placeholder = self.lm.get("Customers.search_customers", "Search customer or enter new details...")
        self.customer_combo.lineEdit().setPlaceholderText(placeholder)
        
        layout.addWidget(self.customer_combo)
        
        completer = QCompleter(self.customer_combo.model())
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.customer_combo.setCompleter(completer)
        
        self._load_customers()
        self.customer_combo.setCurrentIndex(0)  # Set to empty selection initially

    def _load_customers(self):
        """Load existing customers from service using DTOs"""
        try:
            customers = self.customer_service.get_all_customers()
            self.customer_combo.clear()
            
            # Localize empty option text
            empty_text = self.lm.get("Common.na", "N/A")  # or use more specific key if needed
            self.customer_combo.addItem("", None)  # Empty default with explicit None
            
            for customer_dto in customers:
                # Format display text: "Name (Phone)" or just "Name" if no phone
                display_text = customer_dto.name
                if customer_dto.phone:
                    display_text += f" ({customer_dto.phone})"
                self.customer_combo.addItem(display_text, customer_dto.id)
        except Exception as e:
            # Localize error message
            error_title = self.lm.get("Common.error", "Error")
            error_message = self.lm.get("Customers.load_failed", "Failed to load customers").format(str(e))
            QMessageBox.warning(self, error_title, error_message)
            self.customer_combo.clear()
            self.customer_combo.addItem("", None)

    # Optional: Add method to get selected customer
    def get_selected_customer_id(self):
        """Get the ID of the currently selected customer"""
        return self.customer_combo.currentData()
    
    # Optional: Add method to set selected customer
    def set_selected_customer(self, customer_id):
        """Set the selected customer by ID"""
        for index in range(self.customer_combo.count()):
            if self.customer_combo.itemData(index) == customer_id:
                self.customer_combo.setCurrentIndex(index)
                return True
        return False

    # Optional: Add method to get display text for selected customer
    def get_selected_customer_text(self):
        """Get the display text of the currently selected customer"""
        return self.customer_combo.currentText()
    
    # Optional: Add method to refresh customers list
    def refresh(self):
        """Refresh the customer list from the service"""
        self._load_customers()