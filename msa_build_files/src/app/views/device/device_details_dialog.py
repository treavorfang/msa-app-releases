# src/app/views/device/device_details_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QGroupBox, QTabWidget, 
                              QWidget)
from PySide6.QtCore import Qt
from datetime import datetime
from utils.language_manager import language_manager

class DeviceDetailsDialog(QDialog):
    """Dialog for viewing detailed device information"""
    
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.lm = language_manager
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Devices.device_details_title', 'Device Details')} - {self.device.barcode}")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Header with device name
        header_layout = QHBoxLayout()
        
        device_name = f"{self.device.brand} {self.device.model}"
        title = QLabel(f"📱 {device_name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Status badge
        status_color = self._get_status_color(self.device.status)
        status_key = f"Common.{self.device.status}"
        status_text = self.lm.get(status_key, self.device.status.replace('_', ' ').title())
        status_badge = QLabel(f" {status_text} ")
        status_badge.setStyleSheet(f"""
            background-color: {status_color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
        header_layout.addWidget(status_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Device Info Tab
        info_tab = self._create_info_tab()
        tabs.addTab(info_tab, self.lm.get("Devices.device_info_tab", "Device Info"))
        
        # History Tab
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, self.lm.get("Devices.status_history_tab", "Status & History"))
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _get_status_color(self, status):
        """Get color for status badge"""
        colors = {
            "received": "#4169E1",   # Royal Blue
            "diagnosed": "#20B2AA",  # Light Sea Green
            "repairing": "#FFD700",  # Gold
            "repaired": "#BA55D3",   # Medium Orchid
            "completed": "#32CD32",  # Lime Green
            "returned": "#90EE90",   # Light Green
        }
        return colors.get(status, '#808080')
    
    def _create_info_tab(self):
        """Create device information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Identifiers Group
        id_group = QGroupBox(self.lm.get("Devices.identifiers_group", "Identifiers"))
        id_layout = QFormLayout(id_group)
        
        id_layout.addRow(self.lm.get("Devices.barcode", "Barcode") + ":", QLabel(f"<b>{self.device.barcode}</b>"))
        id_layout.addRow(self.lm.get("Devices.serial_number", "Serial Number") + ":", QLabel(self.device.serial_number or self.lm.get("Common.not_applicable", "N/A")))
        id_layout.addRow(self.lm.get("Devices.imei", "IMEI") + ":", QLabel(self.device.imei or self.lm.get("Common.not_applicable", "N/A")))
        
        layout.addWidget(id_group)
        
        # Physical Specs Group
        specs_group = QGroupBox(self.lm.get("Devices.physical_specs_group", "Physical Specs"))
        specs_layout = QFormLayout(specs_group)
        
        specs_layout.addRow(self.lm.get("Devices.color", "Color") + ":", QLabel(self.device.color or self.lm.get("Common.not_applicable", "N/A")))
        specs_layout.addRow(self.lm.get("Devices.condition", "Condition") + ":", QLabel(self.device.condition or self.lm.get("Common.not_applicable", "N/A")))
        
        layout.addWidget(specs_group)
        
        # Security/Lock Group
        if self.device.passcode:
            security_group = QGroupBox(self.lm.get("Devices.security_group", "Security / Lock Information"))
            security_layout = QFormLayout(security_group)
            
            passcode_label = QLabel(f"🔒 {self.device.passcode}")
            passcode_label.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 14px;")
            security_layout.addRow(self.lm.get("Devices.passcode", "Passcode") + ":", passcode_label)
            
            layout.addWidget(security_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_history_tab(self):
        """Create history information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ownership Group
        owner_group = QGroupBox(self.lm.get("Devices.ownership_group", "Ownership"))
        owner_layout = QFormLayout(owner_group)
        
        customer_name = self.device.customer_name or self.lm.get("Common.unknown", "Unknown")
        owner_layout.addRow(self.lm.get("Devices.customer", "Customer") + ":", QLabel(f"<b>{customer_name}</b>"))
        
        layout.addWidget(owner_group)
        
        # Timeline Group
        time_group = QGroupBox(self.lm.get("Common.timeline", "Timeline"))
        time_layout = QFormLayout(time_group)
        
        received_at = self.device.received_at.strftime("%Y-%m-%d %H:%M") if self.device.received_at else self.lm.get("Common.not_applicable", "N/A")
        time_layout.addRow(self.lm.get("Common.received", "Received") + ":", QLabel(received_at))
        
        completed_at = self.device.completed_at.strftime("%Y-%m-%d %H:%M") if self.device.completed_at else self.lm.get("Devices.not_completed", "Not Completed")
        time_layout.addRow(self.lm.get("Common.completed", "Completed") + ":", QLabel(completed_at))
        
        layout.addWidget(time_group)
        
        # Status Group
        status_group = QGroupBox(self.lm.get("Devices.current_status_group", "Current Status"))
        status_layout = QVBoxLayout(status_group)
        
        status_key = f"Common.{self.device.status}"
        status_text = self.lm.get(status_key, self.device.status.replace('_', ' ').title())
        status_label = QLabel(status_text)
        status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_layout.addWidget(status_label)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return widget
