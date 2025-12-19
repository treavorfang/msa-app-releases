# src/app/views/tickets/ticket_receipt_issue.py
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QComboBox, QTextEdit
from config.config_manager import config_manager
from utils.language_manager import language_manager

class TicketReceiptIssue:
    def __init__(self, ticket_receipt):
        self.ticket_receipt = ticket_receipt
        self.lm = language_manager
        self._create_widgets()
    
    def _create_widgets(self):
        """Create issue-related widgets"""
        from PySide6.QtWidgets import QCheckBox, QHBoxLayout
        
        self.error_input = QComboBox()
        self.description_input = QTextEdit()
        
        # Accessories checkboxes
        self.acc_sim = QCheckBox("SIM Card")
        self.acc_case = QCheckBox("Case")
        self.acc_charger = QCheckBox("Charger")
        self.acc_box = QCheckBox("Box")
    
    def create_issue_section(self):
        """Create and return the issue details section"""
        from PySide6.QtWidgets import QHBoxLayout
        
        group = QGroupBox("ISSUE DETAILS")
        layout = QVBoxLayout(group)
        
        self.error_input.setEditable(True)
        self.error_input.setInsertPolicy(QComboBox.NoInsert)
        self.error_input.addItem("")
        self.error_input.lineEdit().setPlaceholderText(self.lm.get("Tickets.select_error_desc", "Select or enter error description..."))
        self._populate_error_categories()
        self.error_input.lineEdit().textEdited.connect(self.clear_error_placeholder)
        
        self.description_input.setPlaceholderText(self.lm.get("Tickets.detailed_problem_desc", "Detailed description of the problem..."))
        self.description_input.setFixedHeight(100)
        
        layout.addWidget(QLabel("Error:"))
        layout.addWidget(self.error_input)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        
        # Accessories section
        layout.addWidget(QLabel("Accessories Received:"))
        acc_layout = QHBoxLayout()
        acc_layout.addWidget(self.acc_sim)
        acc_layout.addWidget(self.acc_case)
        acc_layout.addWidget(self.acc_charger)
        acc_layout.addWidget(self.acc_box)
        acc_layout.addStretch()
        layout.addLayout(acc_layout)
        
        return group
    
    def _populate_error_categories(self):
        """Populate the error combo box with categories"""
        error_categories = config_manager.phone_error_categories
        for category, errors in error_categories.items():
            self.error_input.addItem(f"--- {category.replace('_', ' ').title()} ---")
            self.error_input.model().item(self.error_input.count()-1).setEnabled(False)
            for error in errors:
                self.error_input.addItem(error)
    
    def clear_error_placeholder(self):
        """Clear the placeholder text when user starts typing"""
        if self.error_input.lineEdit().placeholderText():
            self.error_input.lineEdit().setPlaceholderText("")
    
    def validate_silent(self) -> bool:
        """Validate issue without showing error messages"""
        error = self.error_input.currentText().strip()
        description = self.description_input.toPlainText().strip()
        
        # Skip validation if error is empty or is a separator (starts with ---)
        if not error or error.startswith('---'):
            return False
            
        if len(error) > 100:
            return False
            
        if len(description) > 1000:
            return False
            
        return True
    
    def get_issue_data(self):
        """Get issue data for submission"""
        return {
            'error': self.error_input.currentText(),
            'error_description': self.description_input.toPlainText()
        }
    
    def populate_form(self, ticket):
        """Populate issue fields with existing data"""
        self.error_input.setCurrentText(ticket.error or "")
        self.description_input.setPlainText(ticket.error_description or "")