# src/app/views/tickets/ticket_receipt_device.py
from PySide6.QtWidgets import QGroupBox, QFormLayout
from views.components.device_input import DeviceInput
from utils.validation.input_validator import InputValidator
from utils.language_manager import language_manager

class TicketReceiptDevice:
    def __init__(self, ticket_receipt):
        self.ticket_receipt = ticket_receipt
        self.lm = language_manager
        self._create_widgets()
    
    def _create_widgets(self):
        """Create device-related widgets"""
        self.device_input = DeviceInput()
        self.serial_input = self._create_line_edit(self.lm.get("Tickets.device_serial", "Serial Number"), max_length=20)
        self.imei_input = self._create_line_edit(self.lm.get("Tickets.device_imei", "IMEI (15 or 16 digits)"), max_length=19)
        # Passcode is handled in the main receipt form (Lock & Accessories section)
        self.color_input = self._create_line_edit(self.lm.get("Tickets.device_color", "Color"))
        self.condition_input = self._create_line_edit(self.lm.get("Tickets.device_condition", "Condition"))
    
    def _create_line_edit(self, placeholder="", max_length=None):
        """Helper to create consistent line edits"""
        from PySide6.QtWidgets import QLineEdit
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        if max_length:
            line_edit.setMaxLength(max_length)
        return line_edit
    
    def create_device_group(self):
        """Create and return the device group"""
        device_group = QGroupBox("DEVICE DETAILS")
        device_layout = QFormLayout(device_group)
        
        device_layout.addRow(self.device_input.brand_combo)
        device_layout.addRow(self.device_input.model_input)
        device_layout.addRow(self.imei_input)
        device_layout.addRow(self.serial_input)
        # Passcode row removed
        device_layout.addRow(self.color_input)
        device_layout.addRow(self.condition_input)
        
        return device_group
    
    def connect_signals(self):
        """Connect device-related signals"""
        self.serial_input.textChanged.connect(self.on_serial_changed)
        self.imei_input.textChanged.connect(self.on_imei_changed)
    
    def on_serial_changed(self, text):
        """Handle serial number text changes"""
        self.format_input_field(self.serial_input, InputValidator.format_serial_number)
    
    def on_imei_changed(self, text):
        """Handle IMEI text changes"""
        self.format_input_field(self.imei_input, InputValidator.format_imei)
    
    def format_input_field(self, field, formatter):
        """Generic input field formatting helper"""
        formatted = formatter(field.text())
        if formatted != field.text():
            field.blockSignals(True)
            field.setText(formatted)
            field.setCursorPosition(len(formatted))
            field.blockSignals(False)
    
    def validate_silent(self) -> bool:
        """Validate device without showing error messages"""
        if not self.device_input.brand_combo.currentText():
            return False
            
        model_text = self.device_input.model_input.text().strip()
        if not model_text or not InputValidator.validate_device_model(model_text):
            return False
            
        imei = self.imei_input.text().strip()
        if imei and not InputValidator.validate_imei(imei):
            return False
            
        serial = self.serial_input.text().strip()
        if serial and not InputValidator.validate_serial_number(serial):
            return False
                    
        return True
    
    def get_device_data(self, customer_id, technician_id=None):
        """Get device data for submission"""
        initial_status = "diagnosed" if technician_id else "received"
        
        return {
            'brand': self.device_input.brand_combo.currentText(),
            'model': self.device_input.model_input.text(),
            'serial_number': self.serial_input.text() or None,
            'imei': self.imei_input.text() or None,
            # Passcode is handled by the main form
            'color': self.color_input.text() or None,
            'condition': self.condition_input.text() or None,
            'customer_id': customer_id,
            'status': initial_status
        }
    
    def populate_form(self, device):
        """Populate device fields with existing data"""
        if device:
            self.device_input.brand_combo.setCurrentText(device.brand)
            self.device_input.model_input.setText(device.model)
            self.serial_input.setText(device.serial_number or "")
            self.imei_input.setText(device.imei or "")
            # Passcode is handled by the main form
            self.color_input.setText(device.color or "")
            self.condition_input.setText(device.condition or "")