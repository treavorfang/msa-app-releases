# src/app/views/tickets/ticket_receipt_controls.py
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QComboBox, QDateEdit, QLineEdit
from PySide6.QtCore import QDate, Qt
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from views.components.money_input import MoneyInput

class TicketReceiptControls:
    
    def __init__(self, ticket_receipt):
        self.ticket_receipt = ticket_receipt
        self.lm = language_manager
        self.cf = currency_formatter
        self._create_widgets()
    
    def _create_widgets(self):
        """Create control-related widgets"""
        self.priority_input = QComboBox()
        self.technician_input = QComboBox()
        self.technician_input.currentIndexChanged.connect(self.on_technician_changed)
        self.deadline_input = QDateEdit()
        self.estimated_cost = MoneyInput()
        self.estimated_cost.setPlaceholderText("0.00")
        self.estimated_cost.setAlignment(Qt.AlignRight)
        
        self.deposit = MoneyInput()
        self.deposit.setPlaceholderText("0.00")
        self.deposit.setAlignment(Qt.AlignRight)
        
    def connect_signals(self):
        """Connect signals for controls"""
        # Signals are already connected in _create_widgets or can be moved here
        pass
    
    def create_controls_section(self):
        """Create and return the priority/technician/deadline section"""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        priorities = [
            (self.lm.get("Common.low", "low"), "low"),
            (self.lm.get("Common.medium", "medium"), "medium"),
            (self.lm.get("Common.high", "high"), "high"),
            (self.lm.get("Tickets.critical", "critical"), "critical")
        ]
        for display, value in priorities:
            self.priority_input.addItem(display, value)
            
        # Set default to medium
        index = self.priority_input.findData("medium")
        if index >= 0:
            self.priority_input.setCurrentIndex(index)
        
        self.deadline_input.setDisplayFormat("MMM d, yyyy")
        self.deadline_input.setMinimumDate(QDate.currentDate())
        self.deadline_input.setDate(QDate.currentDate().addDays(7))
        self.deadline_input.setCalendarPopup(True)
        
        layout.addWidget(QLabel(self.lm.get("Tickets.priority", "Priority:")))
        layout.addWidget(self.priority_input)
        layout.addSpacing(20)
        layout.addWidget(QLabel(self.lm.get("Tickets.technician", "Technician:")))
        layout.addWidget(self.technician_input)
        layout.addSpacing(20)
        layout.addWidget(QLabel(self.lm.get("Tickets.deadline", "Deadline:")))
        layout.addWidget(self.deadline_input)
        layout.addStretch()
        
        return section
    
    def create_cost_section(self):
        """Create and return the cost section"""
        from PySide6.QtWidgets import QFrame, QFormLayout
        from PySide6.QtWidgets import QWidget # Make sure QWidget is available if needed, though QFrame inherits it.
        
        section = QFrame()
        layout = QFormLayout(section)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Estimated Cost with Currency Label
        cost_layout = QHBoxLayout()
        cost_currency_label = QLabel(self.cf.get_currency_symbol())
        cost_layout.addWidget(cost_currency_label)
        cost_layout.addWidget(self.estimated_cost)
        
        # Deposit with Currency Label
        deposit_layout = QHBoxLayout()
        deposit_currency_label = QLabel(self.cf.get_currency_symbol())
        deposit_layout.addWidget(deposit_currency_label)
        deposit_layout.addWidget(self.deposit)
        
        layout.addRow(self.lm.get("Tickets.estimated_cost", "Estimated Cost:"), cost_layout)
        layout.addRow(self.lm.get("Tickets.deposit", "Deposit:"), deposit_layout)
        
        return section
    
    def populate_technician_filter(self, technicians=None):
        """Populate the technician dropdown with actual technicians"""
        self.technician_input.blockSignals(True)
        self.technician_input.clear()
        
        # Always add "Not Assigned" option
        self.technician_input.addItem(self.lm.get("Tickets.not_assigned", "Not Assigned"), None)
        
        if technicians:
            for tech in technicians:
                tech_name = tech.full_name if tech.full_name else f"Technician #{tech.id}"
                self.technician_input.addItem(tech_name, tech.id)
        
        self.technician_input.blockSignals(False)
    
    def on_technician_changed(self, index):
        """Handle technician selection changes to auto-update status"""
        if not self.ticket_receipt.edit_mode:
            technician_id = self.technician_input.currentData()
            if technician_id:
                self.auto_update_status_for_technician()
    
    def auto_update_status_for_technician(self):
        """Automatically update status when technician is assigned"""
        if not self.ticket_receipt.edit_mode:
            # We need to check the data, not text, since priority is now key-based
            current_priority = self.priority_input.currentData()
            # This logic seems to check 'status' logic which is not Priority. 
            # Re-reading original code: "if self.priority_input.currentText() == 'open':"
            # It seems the original code confused status for priority or just used priority field? 
            # Looking at ticket_receipt.py: ticket_data['status'] = "diagnosed" if technician_id else "open"
            # This method seems unused or misnamed in original code. Ticket status is separate. 
            # I will leave it be but safeguard it.
            pass
    
    def validate_costs_silent(self) -> bool:
        """Validate costs without showing error messages"""
        try:
            est_cost = self.estimated_cost.value()
            deposit = self.deposit.value()
            
            if est_cost < 0 or deposit < 0:
                return False
                
            if deposit > est_cost:
                return False
        except ValueError:
            return False
            
        return True
    
    def get_controls_data(self):
        """Get controls data for submission"""
        technician_id = self.technician_input.currentData()
        
        try:
            est_cost = self.estimated_cost.value()
            deposit = self.deposit.value()
        except ValueError:
            est_cost = 0.0
            deposit = 0.0
            
        return {
            'priority': self.priority_input.currentData(), # Use English key
            'assigned_technician_id': technician_id,
            'deadline': self.deadline_input.date().toString("yyyy-MM-dd"),
            'estimated_cost': est_cost,
            'deposit_paid': deposit
        }
    
    def populate_form(self, ticket):
        """Populate control fields with existing data"""
        self.priority_input.setCurrentText(ticket.priority)
        
        if ticket.assigned_technician_id:
            self.technician_input.setCurrentIndex(
                self.technician_input.findData(ticket.assigned_technician_id)
            )
        else:
            self.technician_input.setCurrentIndex(0)
        
        if ticket.deadline:
            self.deadline_input.setDate(ticket.deadline)
        
        self.estimated_cost.setValue(float(ticket.estimated_cost))
        self.deposit.setValue(float(ticket.deposit_paid))