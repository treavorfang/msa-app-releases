# src/app/views/tickets/ticket_receipt.py
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QCheckBox, QLineEdit, QComboBox, QGridLayout, QTextEdit
from PySide6.QtCore import QDate, Signal
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime
from dtos.ticket_dto import TicketDTO
from utils.validation.message_handler import MessageHandler
from .ticket_receipt_customer import TicketReceiptCustomer
from .ticket_receipt_device import TicketReceiptDevice
from .ticket_receipt_issue import TicketReceiptIssue
from .ticket_receipt_controls import TicketReceiptControls
from .ticket_receipt_actions import TicketReceiptActions
from utils.language_manager import language_manager

class TicketReceipt(QWidget):
    ticket_created = Signal(TicketDTO)
    ticket_updated = Signal(TicketDTO)
    
    def __init__(self, user_id, container, parent=None):
        super().__init__() # Do not pass parent to make it a top-level window
        self.user_id = user_id
        self.container = container
        self.ticket_service = container.ticket_service
        self.device_service = container.device_service
        self.customer_service = container.customer_service
        self.technician_service = container.technician_service
        self.business_settings_service = container.business_settings_service
        self.lm = language_manager
        self.current_ticket = None
        self.edit_mode = False
        
        # Initialize functional area classes
        self.customer_section = TicketReceiptCustomer(self)
        self.device_section = TicketReceiptDevice(self)
        self.issue_section = TicketReceiptIssue(self)
        self.controls_section = TicketReceiptControls(self)
        self.actions = TicketReceiptActions(self)
        
        self._init_ui()
        self._connect_signals()
        self.device_section.connect_signals()
        self.controls_section.connect_signals()
        self._load_technicians()
        self._update_ticket_number_preview()
        
    def _init_ui(self):
        """Initialize all UI components"""
        self.setWindowTitle(self.lm.get("Tickets.new_repair_ticket", "New Repair Ticket"))
        self.setMinimumSize(850, 800)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Add UI sections using functional area classes
        main_layout.addLayout(self._create_header_section())
        main_layout.addWidget(self._create_customer_device_section_no_frame())
        main_layout.addWidget(self._create_issue_lock_section())
        main_layout.addWidget(self.controls_section.create_controls_section())
        main_layout.addWidget(self.controls_section.create_cost_section())
        main_layout.addLayout(self.actions.create_button_section())
    
    def _create_header_section(self):
        """Create and return the ticket header section"""
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        
        self.ticket_number_label = QLabel(self.lm.get("Tickets.ticket_number_label", "Ticket #:"))
        self.ticket_number_label.setFont(header_font)
        self.ticket_number = QLabel()
        self.ticket_number.setFont(header_font)
        self.ticket_number.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        today_date = QLabel(QDate.currentDate().toString("MMM d, yyyy"))
        today_date.setFont(header_font)
        
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(self.ticket_number_label)
        layout.addWidget(self.ticket_number)
        layout.addStretch()
        layout.addWidget(QLabel(self.lm.get("Common.date", "Date:")))
        layout.addWidget(today_date)
        
        return layout
    
    def _create_customer_device_section_no_frame(self):
        """Create customer and device sections without any surrounding frame"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Get the customer group from customer_section but without extra frames
        customer_group = QGroupBox(self.lm.get("Tickets.customer_info", "CUSTOMER INFORMATION"))
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.setContentsMargins(8, 12, 8, 8)
        customer_layout.setSpacing(6)
        
        # Add customer search and fields directly
        customer_layout.addWidget(self.customer_section.customer_search)
        customer_layout.addWidget(self.customer_section.customer_name)
        customer_layout.addWidget(self.customer_section.customer_phone)
        customer_layout.addWidget(self.customer_section.customer_email)
        customer_layout.addWidget(self.customer_section.customer_address)
        customer_layout.addWidget(self.customer_section.customer_note)
        
        # Get the device group from device_section
        device_group = QGroupBox(self.lm.get("Tickets.device_info", "DEVICE DETAILS"))
        device_layout = QVBoxLayout(device_group)
        device_layout.setContentsMargins(8, 12, 8, 8)
        device_layout.setSpacing(6)
        
        # Add device fields directly - REMOVED passcode_input since we have lock section
        device_layout.addWidget(self.device_section.device_input.brand_combo)
        device_layout.addWidget(self.device_section.device_input.model_input)
        device_layout.addWidget(self.device_section.imei_input)
        device_layout.addWidget(self.device_section.serial_input)
        device_layout.addWidget(self.device_section.color_input)
        device_layout.addWidget(self.device_section.condition_input)
        
        layout.addWidget(customer_group, 0, 0)
        layout.addWidget(device_group, 0, 1)
        
        # Set column stretch to make them equal width
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        
        return widget
    
    def _create_issue_lock_section(self):
        """Create combined issue details and lock/accessories side by side"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Left side: Issue Details
        issue_group = QGroupBox(self.lm.get("Tickets.issue_details", "ISSUE DETAILS"))
        issue_layout = QVBoxLayout(issue_group)
        issue_layout.setContentsMargins(8, 12, 8, 8)
        issue_layout.setSpacing(6)
        
        # Error input
        self.issue_section.error_input = QComboBox()
        self.issue_section.error_input.setEditable(True)
        self.issue_section.error_input.setInsertPolicy(QComboBox.NoInsert)
        self.issue_section.error_input.addItem("")
        self.issue_section.error_input.lineEdit().setPlaceholderText(
            self.lm.get("Tickets.select_error_desc", "Select or enter error...")
        )
        self._populate_error_categories()
        self.issue_section.error_input.lineEdit().textEdited.connect(self.issue_section.clear_error_placeholder)
        
        # Description input
        self.issue_section.description_input = QTextEdit()
        self.issue_section.description_input.setPlaceholderText(
            self.lm.get("Tickets.detailed_problem_desc", "Detailed problem description...")
        )
        self.issue_section.description_input.setFixedHeight(80)
        
        issue_layout.addWidget(QLabel(self.lm.get("Tickets.error_label", "Error:")))
        issue_layout.addWidget(self.issue_section.error_input)
        issue_layout.addWidget(QLabel(self.lm.get("Tickets.description_label", "Description:")))
        issue_layout.addWidget(self.issue_section.description_input)
        
        layout.addWidget(issue_group)
        
        # Right side: Lock Information & Accessories
        lock_group = QGroupBox(self.lm.get("Tickets.lock_accessories", "LOCK & ACCESSORIES"))
        lock_layout = QVBoxLayout(lock_group)
        lock_layout.setContentsMargins(8, 12, 8, 8)
        lock_layout.setSpacing(8)
        
        # Lock Type and Value side by side
        lock_row_layout = QHBoxLayout()
        lock_row_layout.setSpacing(10)
        
        # Lock Type (ComboBox with PIN, Password, Pattern)
        lock_type_layout = QVBoxLayout()
        lock_type_layout.setSpacing(4)
        lock_type_label = QLabel(self.lm.get("Tickets.lock_type", "Lock Type:"))
        self.lock_type_combo = QComboBox()
        # Localize lock types
        lock_types = [
            (self.lm.get("Common.none", "None"), "None"),
            (self.lm.get("Tickets.lock_pin", "PIN"), "PIN"),  # Technial term but allow translation
            (self.lm.get("Devices.passcode", "Password"), "Password"),
            (self.lm.get("Tickets.lock_pattern", "Pattern"), "Pattern"),
            (self.lm.get("Tickets.lock_faceid", "Face ID"), "Face ID"),
            (self.lm.get("Tickets.lock_fingerprint", "Fingerprint"), "Fingerprint")
        ]
        
        for display, value in lock_types:
            self.lock_type_combo.addItem(display, value)
        
        # Lock Value
        lock_value_layout = QVBoxLayout()
        lock_value_layout.setSpacing(4)
        lock_value_label = QLabel(self.lm.get("Tickets.lock_value", "Value:"))
        self.lock_value = QLineEdit()
        self.lock_value.setPlaceholderText(
            self.lm.get("Tickets.lock_value_placeholder", "Lock value...")
        )
        # self.lock_value.setEchoMode(QLineEdit.Password)
        
        lock_value_layout.addWidget(lock_value_label)
        lock_value_layout.addWidget(self.lock_value)
        
        lock_row_layout.addLayout(lock_type_layout)
        lock_row_layout.addLayout(lock_value_layout)
        
        # Connect lock type change to enable/disable value field
        self.lock_type_combo.currentIndexChanged.connect(self._on_lock_type_changed)
        
        lock_type_layout.addWidget(lock_type_label)
        lock_type_layout.addWidget(self.lock_type_combo)
        
        lock_layout.addLayout(lock_row_layout)
        
        # Initially disable lock value since default is "None"
        self._update_lock_value_state()
        
        # Accessories
        accessories_layout = QVBoxLayout()
        accessories_layout.setSpacing(6)
        accessories_label = QLabel(self.lm.get("Tickets.accessories_received", "Accessories Received:"))
        accessories_layout.addWidget(accessories_label)
        
        # Accessories checkboxes in a 2x3 grid
        acc_grid_layout = QGridLayout()
        acc_grid_layout.setHorizontalSpacing(15)
        acc_grid_layout.setVerticalSpacing(8)
        
        # Localize accessory names
        self.acc_sim = QCheckBox(self.lm.get("Tickets.accessory_sim", "SIM Card"))
        self.acc_case = QCheckBox(self.lm.get("Tickets.accessory_case", "Case"))
        self.acc_charger = QCheckBox(self.lm.get("Tickets.accessory_charger", "Charger"))
        self.acc_box = QCheckBox(self.lm.get("Tickets.accessory_box", "Box"))
        self.acc_earphones = QCheckBox(self.lm.get("Tickets.accessory_earphones", "Earphones"))
        self.acc_other = QCheckBox(self.lm.get("Common.other", "Other"))
        
        # Row 1
        acc_grid_layout.addWidget(self.acc_sim, 0, 0)
        acc_grid_layout.addWidget(self.acc_case, 0, 1)
        acc_grid_layout.addWidget(self.acc_charger, 0, 2)
        
        # Row 2
        acc_grid_layout.addWidget(self.acc_box, 1, 0)
        acc_grid_layout.addWidget(self.acc_earphones, 1, 1)
        acc_grid_layout.addWidget(self.acc_other, 1, 2)
        
        accessories_layout.addLayout(acc_grid_layout)
        
        # Other accessories text input
        other_layout = QHBoxLayout()
        other_layout.setSpacing(8)
        other_label = QLabel(self.lm.get("Common.other", "Other:"))
        self.acc_other_input = QLineEdit()
        self.acc_other_input.setPlaceholderText(
            self.lm.get("Tickets.specify_other", "Specify...")
        )
        self.acc_other_input.setEnabled(False)
        self.acc_other.toggled.connect(self.acc_other_input.setEnabled)
        other_layout.addWidget(other_label)
        other_layout.addWidget(self.acc_other_input)
        
        accessories_layout.addLayout(other_layout)
        lock_layout.addLayout(accessories_layout)
        
        layout.addWidget(lock_group)
        
        # Set stretch factors
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        
        return widget
    
    def _on_lock_type_changed(self, index):
        """Handle lock type selection change"""
        self._update_lock_value_state()
        
    def _update_lock_value_state(self):
        """Enable/disable lock value field based on lock type selection"""
        lock_type = self.lock_type_combo.currentData()
        
        if lock_type == "None" or not lock_type:
            self.lock_value.setEnabled(False)
            self.lock_value.clear()
            self.lock_value.setPlaceholderText(
                self.lm.get("Tickets.no_lock_required", "No lock required")
            )
        else:
            self.lock_value.setEnabled(True)
            self.lock_value.setPlaceholderText(
                self.lm.get("Tickets.lock_value_placeholder", "Lock value...")
            )
    
    def _populate_error_categories(self):
        """Populate the error combo box with categories"""
        from config.config_manager import config_manager
        error_categories = config_manager.phone_error_categories
        for category, errors in error_categories.items():
            # Localize category name if possible
            category_key = f"ErrorCategories.{category}"
            display_category = self.lm.get(category_key, category.replace('_', ' ').title())
            self.issue_section.error_input.addItem(f"--- {display_category} ---")
            self.issue_section.error_input.model().item(self.issue_section.error_input.count()-1).setEnabled(False)
            for error in errors:
                # Try to localize each error if a translation exists
                error_key = f"ErrorTypes.{error}"
                display_error = self.lm.get(error_key, error)
                self.issue_section.error_input.addItem(display_error)
    
    def _connect_signals(self):
        """Connect all signals to their slots"""
        # Customer signals
        self.customer_section.connect_signals()
        
        # Device signals
        self.device_section.connect_signals()
        
        # Submit button
        self.actions.submit_btn.clicked.connect(self._handle_submit)
        
        # Technician controller signals
        if hasattr(self.container, 'technician_controller'):
            self.container.technician_controller.technician_created.connect(self._load_technicians)
            self.container.technician_controller.technician_updated.connect(self._load_technicians)
    
    def _handle_submit(self):
        """Handle form submission based on mode"""
        # Use the TicketReceiptActions validation
        if not self.actions.validate_inputs_silent():
            errors = []
            
            # Localize error messages
            if not self.customer_section.validate_silent():
                errors.append(self.lm.get("Validation.check_customer_info", "Please check customer information"))
            if not self.device_section.validate_silent():
                errors.append(self.lm.get("Validation.check_device_info", "Please check device information"))
            if not self.issue_section.validate_silent():
                errors.append(self.lm.get("Validation.check_issue_details", "Please check issue details"))
            if not self.controls_section.validate_costs_silent():
                errors.append(self.lm.get("Validation.check_cost_info", "Please check cost information"))
                
            if errors:
                MessageHandler.show_warning(
                    self, 
                    self.lm.get("Validation.validation_error", "Validation Error"), 
                    "\n".join(errors)
                )
            return
            
        if self.edit_mode:
            self._update_ticket_with_lock_info()
        else:
            self._create_ticket_with_lock_info()
    
    def _create_ticket_with_lock_info(self):
        """Create a new ticket with lock information"""
        try:
            # Get all form data
            customer_data = self.customer_section.get_customer_data()
            lock_data = self.get_lock_data()
            accessories_str = self.get_accessories_data()
            
            # 1. Handle Customer
            if 'customer_id' in customer_data:
                customer_id = customer_data['customer_id']
            else:
                # Create new customer
                customer = self.container.customer_controller.create_customer({
                    'name': customer_data['name'],
                    'phone': customer_data['phone'],
                    'email': customer_data.get('email'),
                    'address': customer_data.get('address'),
                    'notes': customer_data.get('notes'),
                    'created_by': self.user_id
                })
                customer_id = customer.id
            
            # 2. Handle Device (include lock value in passcode field)
            technician_id = self.controls_section.technician_input.currentData()
            device_data = self.device_section.get_device_data(customer_id, technician_id)
            
            # Add lock value to device passcode if not None
            if lock_data['lock_value']:
                device_data['passcode'] = lock_data['lock_value']
            
            # Add lock type to device
            if lock_data['lock_type']:
                device_data['lock_type'] = lock_data['lock_type']
            
            # Create device
            device_dto = self.container.device_controller.create_device(
                device_data,
                current_user=None,
                ip_address=None
            )
            
            # 3. Create Ticket
            ticket_data = {
                'device_id': device_dto.id,
                'created_by_id': self.user_id,
                **self.issue_section.get_issue_data(),
                **self.controls_section.get_controls_data(),
                'accessories': accessories_str
            }
            
            # Set initial status based on technician assignment
            technician_id = self.controls_section.technician_input.currentData()
            ticket_data['status'] = "diagnosed" if technician_id else "open"
            
            ticket_dto = self.container.ticket_controller.create_ticket(
                ticket_data,
                current_user=None,  # Will be handled by controller
                ip_address=None
            )
            
            if self.actions.print_chk.isChecked():
                from utils.print.ticket_generator import TicketReceiptGenerator
                print_generator = TicketReceiptGenerator(self, self.business_settings_service)
                print_data = self._gather_ticket_data_for_print(ticket_dto)
                
                # Get print format preference
                user_settings = self.container.settings_service.get_user_settings(self.user_id)
                print_data['print_format'] = user_settings.get('print_format', 'Standard A5')
                
                print_generator.print_ticket(print_data)
            
            self.ticket_created.emit(ticket_dto)
            self.close()
            
        except Exception as e:
            MessageHandler.show_critical(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('TicketMessages.create_failed', 'Failed to create ticket')}: {str(e)}"
            )
    
    def _update_ticket_with_lock_info(self):
        """Update existing ticket with lock information"""
        try:
            # Get all form data
            customer_data = self.customer_section.get_customer_data()
            lock_data = self.get_lock_data()
            accessories_str = self.get_accessories_data()
            
            if 'customer_id' not in customer_data:
                raise ValueError(self.lm.get("Validation.customer_required", "Customer selection is required for updates"))
            
            # Update device with lock value
            device_data = self.device_section.get_device_data(
                customer_data['customer_id'],
                self.controls_section.technician_input.currentData()
            )
            
            # Add lock value to device passcode if not None
            if lock_data['lock_value']:
                device_data['passcode'] = lock_data['lock_value']
            else:
                device_data['passcode'] = None
                
            # Add lock type to device
            if lock_data['lock_type']:
                device_data['lock_type'] = lock_data['lock_type']
            else:
                device_data['lock_type'] = None
            
            # Update device
            updated_device = self.container.device_controller.update_device(
                self.current_ticket.device_id,
                device_data,
                current_user=None,
                ip_address=None
            )
            
            if not updated_device:
                raise RuntimeError(self.lm.get("TicketMessages.update_device_failed", "Failed to update device information"))
            
            # Update ticket
            ticket_data = {
                **self.issue_section.get_issue_data(),
                **self.controls_section.get_controls_data(),
                'accessories': accessories_str
            }
            
            # Handle status changes based on technician assignment
            technician_id = self.controls_section.technician_input.currentData()
            current_status = self.current_ticket.status
            
            new_status = current_status
            if technician_id and current_status == "open":
                new_status = "diagnosed"
            elif not technician_id and current_status == "diagnosed":
                new_status = "open"
            
            ticket_data['status'] = new_status
            
            # Update ticket
            updated_ticket = self.container.ticket_controller.update_ticket(
                self.current_ticket.id,
                ticket_data,
                current_user=None,
                ip_address=None
            )
            
            self.ticket_updated.emit(updated_ticket)
            
            if self.actions.print_chk.isChecked():
                from utils.print.ticket_generator import TicketReceiptGenerator
                print_generator = TicketReceiptGenerator(self, self.business_settings_service)
                print_data = self._gather_ticket_data_for_print(updated_ticket)
                
                # Get print format preference
                user_settings = self.container.settings_service.get_user_settings(self.user_id)
                print_data['print_format'] = user_settings.get('print_format', 'Standard A5')
                
                print_generator.print_ticket(print_data)
                
            self.close()
            
        except ValueError as e:
            MessageHandler.show_warning(
                self, 
                self.lm.get("Validation.validation_error", "Validation Error"), 
                str(e)
            )
        except RuntimeError as e:
            MessageHandler.show_critical(
                self, 
                self.lm.get("Common.error", "Error"), 
                str(e)
            )
        except Exception as e:
            MessageHandler.show_critical(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('TicketMessages.update_failed', 'Failed to update ticket')}: {str(e)}"
            )
    
    def _gather_ticket_data_for_print(self, ticket_dto=None):
        """Gather all current form data for printing"""
        customer_data = self.customer_section.get_customer_data()
        lock_data = self.get_lock_data()
        device_data = self.device_section.get_device_data(0, None)  # Placeholder
        
        data = {
            'customer_name': self.customer_section.customer_name.text() if hasattr(self.customer_section, 'customer_name') else '',
            'customer_phone': self.customer_section.customer_phone.text() if hasattr(self.customer_section, 'customer_phone') else '',
            'customer_email': self.customer_section.customer_email.text() if hasattr(self.customer_section, 'customer_email') else '',
            'customer_address': self.customer_section.customer_address.text() if hasattr(self.customer_section, 'customer_address') else '',
            'brand': device_data.get('brand', ''),
            'model': device_data.get('model', ''),
            'imei': device_data.get('imei', ''),
            'serial_number': device_data.get('serial_number', ''),
            'color': device_data.get('color', ''),
            'condition': device_data.get('condition', ''),
            'issue_type': self.issue_section.error_input.currentText(),
            'description': self.issue_section.description_input.toPlainText(),
            'lock_type': lock_data.get('lock_type', ''),
            'passcode': lock_data.get('lock_value', ''),
            'accessories': self.get_accessories_data(),
            **self.controls_section.get_controls_data()
        }
        
        if ticket_dto:
            data['ticket_number'] = ticket_dto.ticket_number
        elif self.current_ticket:
            data['ticket_number'] = self.current_ticket.ticket_number
            
        return data
    
    def _load_technicians(self):
        """Load technicians from the service"""
        try:
            technicians = self.technician_service.get_active_technicians()
            self.controls_section.populate_technician_filter(technicians)
        except Exception as e:
            print(f"{self.lm.get('Common.error', 'Error')} loading technicians: {e}")
            self.controls_section.populate_technician_filter([])
    
    def _update_ticket_number_preview(self):
        """Update the ticket number preview"""
        from models.ticket import Ticket
        from models.user import User
        
        today_yyyymmdd = datetime.now().strftime("%y%m%d")
        
        # Get current branch ID
        branch_id = 1
        try:
            current_user = User.get_by_id(self.user_id)
            if current_user and current_user.branch:
                branch_id = current_user.branch.id
        except Exception:
            # Fallback to default if user not found or other error
            pass
        
        # Get the last ticket number globally (not just today)
        last_ticket = Ticket.select().order_by(Ticket.ticket_number.desc()).first()
        
        if last_ticket:
            # Extract sequence (look for last 4 digits)
            match = re.search(r"-(\d{4})$", last_ticket.ticket_number)
            if match:
                sequence = int(match.group(1)) + 1
                # Reset to 1 if we've reached 9999
                if sequence > 9999:
                    sequence = 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        self.ticket_number.setText(f"RPT-{branch_id}{today_yyyymmdd}-{sequence:04d}")
    
    def set_edit_mode(self, ticket: TicketDTO):
        """Configure the form for editing an existing ticket"""
        self.edit_mode = True
        self.current_ticket = ticket
        self.setWindowTitle(
            f"{self.lm.get('Tickets.edit_ticket', 'Edit Ticket')} - {ticket.ticket_number}"
        )
        self.actions.submit_btn.setText(self.lm.get("Tickets.update_ticket", "Update Ticket"))
        
        # Populate using the existing populate_form methods
        self.actions.populate_form(ticket)
        
        # Additional population for our new fields
        self._populate_lock_info(ticket)
        self._populate_accessories(ticket)
        
        self._update_ticket_number_preview()
    
    def _populate_lock_info(self, ticket: TicketDTO):
        """Populate lock information"""
        # First check device passcode
        if hasattr(ticket, 'device') and ticket.device:
            device = ticket.device
            
            # Check device passcode field for lock value
            if hasattr(device, 'passcode') and device.passcode:
                self.lock_value.setText(device.passcode)
            
            # Check device lock_type field first
            if hasattr(device, 'lock_type') and device.lock_type:
                # Find data instead of setting text directly to handle localization
                index = self.lock_type_combo.findData(device.lock_type)
                if index >= 0:
                    self.lock_type_combo.setCurrentIndex(index)
                else:
                    # Fallback for old data: try matching text if data not found
                    self.lock_type_combo.setCurrentText(device.lock_type)
            # Fallback: Try to determine lock type from passcode format or internal notes
            elif hasattr(device, 'passcode') and device.passcode:
                if device.passcode.isdigit() and len(device.passcode) <= 6:
                    self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("PIN"))
                elif len(device.passcode) > 6:
                    self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("Password"))
                else:
                    # Default to Pattern for non-numeric passcodes
                    self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("Pattern"))
            else:
                # No passcode, check ticket internal notes for lock type (Legacy support)
                if hasattr(ticket, 'internal_notes') and ticket.internal_notes:
                    import re
                    match = re.search(r'Lock Type:\s*(\w+)', ticket.internal_notes)
                    if match:
                        lock_type = match.group(1)
                        index = self.lock_type_combo.findData(lock_type)
                        if index >= 0:
                            self.lock_type_combo.setCurrentIndex(index)
                        else:
                            self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("None"))
                    else:
                        self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("None"))
                else:
                    self.lock_type_combo.setCurrentIndex(self.lock_type_combo.findData("None"))
        
        # Update lock value state based on selected type
        self._update_lock_value_state()
    
    def _populate_accessories(self, ticket: TicketDTO):
        """Populate accessories from ticket data"""
        if hasattr(ticket, 'accessories') and ticket.accessories:
            accessories_str = str(ticket.accessories) if ticket.accessories else ""
            accessories_list = [acc.strip().lower() for acc in accessories_str.split(',') if acc.strip()]
            
            # Localized accessory names for matching
            accessory_mapping = {
                'sim': self.acc_sim,
                'sim card': self.acc_sim,
                'case': self.acc_case,
                'charger': self.acc_charger,
                'box': self.acc_box,
                'earphones': self.acc_earphones,
                'headphones': self.acc_earphones
            }
            
            # Get localized text for matching
            sim_text = self.lm.get("Tickets.accessory_sim", "SIM Card").lower()
            case_text = self.lm.get("Tickets.accessory_case", "Case").lower()
            charger_text = self.lm.get("Tickets.accessory_charger", "Charger").lower()
            box_text = self.lm.get("Tickets.accessory_box", "Box").lower()
            earphones_text = self.lm.get("Tickets.accessory_earphones", "Earphones").lower()
            
            # Set checkboxes
            other_accessories = []
            for accessory in accessories_list:
                found = False
                
                # Check if accessory matches localized text
                if sim_text in accessory:
                    self.acc_sim.setChecked(True)
                    found = True
                elif case_text in accessory:
                    self.acc_case.setChecked(True)
                    found = True
                elif charger_text in accessory:
                    self.acc_charger.setChecked(True)
                    found = True
                elif box_text in accessory:
                    self.acc_box.setChecked(True)
                    found = True
                elif earphones_text in accessory:
                    self.acc_earphones.setChecked(True)
                    found = True
                
                # Collect other accessories
                if not found and accessory:
                    other_accessories.append(accessory.title())
            
            # Handle "Other" accessories
            if other_accessories:
                self.acc_other.setChecked(True)
                self.acc_other_input.setText(', '.join(other_accessories))
        else:
            # Also check if there are accessories in the issue section
            # (for backward compatibility with existing tickets)
            if hasattr(self.issue_section, 'acc_sim') and self.issue_section.acc_sim:
                # Use accessories from the issue section
                if self.issue_section.acc_sim.isChecked():
                    self.acc_sim.setChecked(True)
                if self.issue_section.acc_case.isChecked():
                    self.acc_case.setChecked(True)
                if self.issue_section.acc_charger.isChecked():
                    self.acc_charger.setChecked(True)
                if self.issue_section.acc_box.isChecked():
                    self.acc_box.setChecked(True)
    
    def get_accessories_data(self):
        """Get accessories data including "Other" for submission"""
        # Compile accessories
        accessories = []
        if self.acc_sim.isChecked(): 
            accessories.append(self.lm.get("Tickets.accessory_sim", "SIM Card"))
        if self.acc_case.isChecked(): 
            accessories.append(self.lm.get("Tickets.accessory_case", "Case"))
        if self.acc_charger.isChecked(): 
            accessories.append(self.lm.get("Tickets.accessory_charger", "Charger"))
        if self.acc_box.isChecked(): 
            accessories.append(self.lm.get("Tickets.accessory_box", "Box"))
        if self.acc_earphones.isChecked(): 
            accessories.append(self.lm.get("Tickets.accessory_earphones", "Earphones"))
        if self.acc_other.isChecked() and self.acc_other_input.text().strip():
            accessories.append(self.acc_other_input.text().strip())
        
        accessories_str = ', '.join(accessories) if accessories else ''
        
        return accessories_str
    
    def get_lock_data(self):
        """Get lock/pattern data for submission"""
        lock_type = self.lock_type_combo.currentData()
        lock_value = self.lock_value.text().strip() if lock_type != "None" else ""
        
        return {
            'lock_type': lock_type if lock_type != "None" else None,
            'lock_value': lock_value if lock_value else None
        }