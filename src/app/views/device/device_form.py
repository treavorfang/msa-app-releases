# src/app/views/components/device_form.py
from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, 
                              QDialogButtonBox, QComboBox, QTextEdit)
from views.components.customer_input import CustomerInput
from views.components.device_input import DeviceInput
from dtos.device_dto import DeviceDTO
from utils.validation.input_validator import InputValidator
from utils.validation.message_handler import MessageHandler
from utils.validation.phone_formatter import phone_formatter

class DeviceForm(QDialog):
    def __init__(self, device_dto: DeviceDTO, parent=None):
        super().__init__(parent)
        self.device_dto = device_dto
        
        if device_dto:
            self.setWindowTitle(f"Edit Device - {device_dto.barcode}")
        else:
            self.setWindowTitle("New Device")
            
        self.setMinimumWidth(500)
        
        self._setup_ui()
        self._load_initial_values()
        self._connect_validation_signals()
        
    def _setup_ui(self):
        self.layout = QFormLayout(self)
        
        # Customer selection
        self.customer_input = CustomerInput()
        self.layout.addRow(self.customer_input)
        
        # Device details
        self.device_input = DeviceInput()
        self.layout.addRow(self.device_input.brand_combo)
        self.layout.addRow(self.device_input.model_input)
        
        # Other fields
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Color")
        self.layout.addRow(self.color_input)
        
        self.imei_input = QLineEdit()
        self.imei_input.setPlaceholderText("IMEI (15 or 16 digits)")
        self.imei_input.setMaxLength(19)
        self.layout.addRow(self.imei_input)
        
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Serial Number...")
        self.serial_input.setMaxLength(20)
        self.layout.addRow(self.serial_input)
        
        # Condition field (multi-line)
        self.condition_input = QTextEdit()
        self.condition_input.setPlaceholderText("Device condition...")
        self.condition_input.setMaximumHeight(100)
        self.layout.addRow(self.condition_input)
        
        # Status ComboBox (editable)
        self.status_combo = QComboBox()
        self.status_map = {
            "Received": "received",
            "Diagnosed": "diagnosed", 
            "Repairing": "repairing",
            "Repaired": "repaired",
            "Completed": "completed",
            "Returned": "returned"
        }
        self.status_combo.addItems(self.status_map.keys())
        self.layout.addRow(self.status_combo)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)
    
    def _connect_validation_signals(self):
        """Connect signals for real-time validation and formatting"""
        self.device_input.brand_combo.currentTextChanged.connect(self._validate_brand)
        self.device_input.model_input.textChanged.connect(self._validate_model)
        
        # IMEI - format and validate in real-time
        self.imei_input.textChanged.connect(self._on_imei_changed)
        
        # Serial - format and validate in real-time
        self.serial_input.textChanged.connect(self._on_serial_changed)
    
    def _on_imei_changed(self, text):
        """Handle IMEI text changes with real-time formatting"""
        self._format_input_field(self.imei_input, InputValidator.format_imei)
        self._validate_imei()
    
    def _on_serial_changed(self, text):
        """Handle serial number text changes with real-time formatting"""
        self._format_input_field(self.serial_input, InputValidator.format_serial_number)
        self._validate_serial()
    
    def _format_input_field(self, field, formatter):
        """Generic input field formatting helper (same as in TicketReceipt)"""
        formatted = formatter(field.text())
        if formatted != field.text():
            field.blockSignals(True)
            field.setText(formatted)
            field.setCursorPosition(len(formatted))
            field.blockSignals(False)
    
    def _validate_brand(self):
        """Validate brand selection"""
        brand = self.device_input.brand_combo.currentText().strip()
        is_valid = bool(brand)
        self._set_field_style(self.device_input.brand_combo, is_valid)
        return is_valid
    
    def _validate_model(self):
        """Validate model input"""
        model = self.device_input.model_input.text().strip()
        is_valid = bool(model) and InputValidator.validate_device_model(model)
        self._set_field_style(self.device_input.model_input, is_valid)
        return is_valid
    
    def _validate_imei(self):
        """Validate IMEI format"""
        imei = self.imei_input.text().strip()
        if not imei:  # IMEI is optional
            self._set_field_style(self.imei_input, True)
            return True
        
        is_valid = InputValidator.validate_imei(imei)
        self._set_field_style(self.imei_input, is_valid)
        return is_valid
    
    def _validate_serial(self):
        """Validate serial number format"""
        serial = self.serial_input.text().strip()
        if not serial:  # Serial is optional
            self._set_field_style(self.serial_input, True)
            return True
        
        is_valid = InputValidator.validate_serial_number(serial)
        self._set_field_style(self.serial_input, is_valid)
        return is_valid
    
    def _set_field_style(self, widget, is_valid):
        """Set field style based on validation result"""
        if is_valid:
            widget.setStyleSheet("")
        else:
            widget.setStyleSheet("border: 1px solid red; background-color: #FFF0F0;")
    
    def _load_initial_values(self):
        """Load the device's current values into the form"""
        if not self.device_dto:
            return

        if self.device_dto.customer_id:
            index = self.customer_input.customer_combo.findData(self.device_dto.customer_id)
            if index >= 0:
                self.customer_input.customer_combo.setCurrentIndex(index)
        
        brand_index = self.device_input.brand_combo.findText(self.device_dto.brand)
        if brand_index >= 0:
            self.device_input.brand_combo.setCurrentIndex(brand_index)
        
        self.device_input.model_input.setText(self.device_dto.model)
        self.color_input.setText(self.device_dto.color or "")
        self.imei_input.setText(self.device_dto.imei or "")
        self.serial_input.setText(self.device_dto.serial_number or "")
        self.condition_input.setPlainText(self.device_dto.condition or "")
        
        # Set current status by finding the display text
        for display_text, db_value in self.status_map.items():
            if db_value == self.device_dto.status:
                self.status_combo.setCurrentText(display_text)
                break
        
        # Validate initial values
        self._validate_brand()
        self._validate_model()
        self._validate_imei()
        self._validate_serial()
    
    def _validate_and_accept(self):
        """Validate all inputs before accepting"""
        # Validate all fields
        brand_valid = self._validate_brand()
        model_valid = self._validate_model()
        imei_valid = self._validate_imei()
        serial_valid = self._validate_serial()
        
        error_messages = []
        
        if not brand_valid:
            error_messages.append("• Brand is required")
        if not model_valid:
            error_messages.append("• Model is required and must be valid")
        if not imei_valid:
            error_messages.append("• IMEI must be 15 or 16 digits if provided")
        if not serial_valid:
            error_messages.append("• Serial number must be valid if provided")
        
        if error_messages:
            MessageHandler.show_warning(
                self, 
                "Validation Error", 
                "Please fix the following issues:\n\n" + "\n".join(error_messages)
            )
            return
        
        # Additional validation for IMEI uniqueness (if IMEI is provided and changed)
        imei = self.imei_input.text().strip()
        if imei and imei != (self.device_dto.imei or ""):
            # Check if IMEI already exists for another device
            try:
                from services.device_service import DeviceService
                from services.audit_service import AuditService
                
                device_service = DeviceService(AuditService())
                existing_device = device_service.get_device_by_imei(imei)
                
                if existing_device and existing_device.id != self.device_dto.id:
                    MessageHandler.show_warning(
                        self,
                        "IMEI Conflict",
                        f"IMEI {imei} already exists for device:\n"
                        f"• Barcode: {existing_device.barcode}\n"
                        f"• Brand/Model: {existing_device.brand} {existing_device.model}"
                    )
                    return
            except Exception as e:
                MessageHandler.show_warning(
                    self,
                    "Validation Error",
                    f"Could not verify IMEI uniqueness: {str(e)}"
                )
                return
        
        self.accept()
    
    def get_updated_data(self):
        """Return the updated data as a dictionary"""
        return {
            'customer_id': self.customer_input.customer_combo.currentData(),
            'brand': self.device_input.brand_combo.currentText(),
            'model': self.device_input.model_input.text(),
            'color': self.color_input.text() or None,
            'imei': self.imei_input.text() or None,
            'serial_number': self.serial_input.text() or None,
            'condition': self.condition_input.toPlainText() or None,
            'status': self.status_map.get(self.status_combo.currentText(), "received")
        }