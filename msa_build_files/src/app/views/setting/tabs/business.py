# src/app/views/setting/tabs/business.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFormLayout, QScrollArea,
    QMessageBox, QDoubleSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
from utils.language_manager import language_manager

class BusinessSettingsTab(QWidget):
    """Simple Business Settings Tab"""
    settings_changed = Signal()
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.business_service = container.business_settings_service
        self.lm = language_manager
        self.current_settings = None
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup simple UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Business Name
        self.business_name = QLineEdit()
        self.business_name.setPlaceholderText(self.lm.get("SettingsBusiness.ph_business_name", "Enter business name"))
        self._style_input(self.business_name)
        form.addRow(f"{self.lm.get('SettingsBusiness.business_name', 'Business Name')}:", self.business_name)
        
        # Phone
        self.business_phone = QLineEdit()
        self.business_phone.setPlaceholderText(self.lm.get("SettingsBusiness.ph_phone", "Enter phone number"))
        self._style_input(self.business_phone)
        form.addRow(f"{self.lm.get('SettingsBusiness.phone', 'Phone')}:", self.business_phone)
        
        # Address
        self.address = QTextEdit()
        self.address.setPlaceholderText(self.lm.get("SettingsBusiness.ph_address", "Enter business address"))
        self.address.setMaximumHeight(70)
        self._style_input(self.address)
        form.addRow(f"{self.lm.get('SettingsBusiness.address', 'Address')}:", self.address)
        
        # Tax ID
        self.tax_id = QLineEdit()
        self.tax_id.setPlaceholderText(self.lm.get("SettingsBusiness.ph_tax_id", "Tax ID / Registration number"))
        self._style_input(self.tax_id)
        form.addRow(f"{self.lm.get('SettingsBusiness.tax_id', 'Tax ID')}:", self.tax_id)
        
        # Default Tax Rate
        self.default_tax_rate = QDoubleSpinBox()
        self.default_tax_rate.setRange(0, 100)
        self.default_tax_rate.setDecimals(2)
        self.default_tax_rate.setSuffix(" %")
        self._style_input(self.default_tax_rate)
        form.addRow(f"{self.lm.get('SettingsBusiness.tax_rate', 'Tax Rate')}:", self.default_tax_rate)
        
        # Logo
        logo_layout = QHBoxLayout()
        self.logo_url = QLineEdit()
        self.logo_url.setPlaceholderText(self.lm.get("SettingsBusiness.ph_logo", "Logo path"))
        self.logo_url.setReadOnly(True)
        self._style_input(self.logo_url)
        logo_layout.addWidget(self.logo_url)
        
        upload_btn = QPushButton(self.lm.get("SettingsBusiness.choose_logo", "Choose"))
        # upload_btn.setFixedWidth(80) # Removed fixed width
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        upload_btn.clicked.connect(self._choose_logo)
        logo_layout.addWidget(upload_btn)
        
        form.addRow(f"{self.lm.get('SettingsBusiness.logo', 'Logo')}:", logo_layout)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(self.lm.get("SettingsBusiness.ph_notes", "Additional notes"))
        self.notes.setMaximumHeight(70)
        self._style_input(self.notes)
        form.addRow(f"{self.lm.get('SettingsBusiness.notes', 'Notes')}:", self.notes)
        
        layout.addLayout(form)
        
        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton(self.lm.get("SettingsBusiness.save_changes", "Save Changes"))
        # self.save_btn.setFixedWidth(150) # Removed fixed width
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def _style_input(self, widget):
        """Apply simple styling to input widgets"""
        widget.setStyleSheet("""
            QLineEdit, QTextEdit, QDoubleSpinBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 8px;
                color: #F3F4F6;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
                border-color: #3B82F6;
            }
        """)
    
    def _choose_logo(self):
        """Open file dialog to choose logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.lm.get("SettingsBusiness.choose_logo_title", "Choose Business Logo"),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.logo_url.setText(file_path)
    
    def _load_settings(self):
        """Load current business settings"""
        self.current_settings = self.business_service.get_settings()
        
        if self.current_settings:
            self.business_name.setText(self.current_settings.business_name or "")
            self.business_phone.setText(self.current_settings.business_phone or "")
            self.address.setPlainText(self.current_settings.address or "")
            self.tax_id.setText(self.current_settings.tax_id or "")
            self.notes.setPlainText(self.current_settings.notes or "")
            self.default_tax_rate.setValue(float(self.current_settings.default_tax_rate or 0))
            
            if self.current_settings.logo_url:
                self.logo_url.setText(self.current_settings.logo_url)
    
    def _save_settings(self):
        """Save business settings"""
        if not self.business_name.text().strip():
            QMessageBox.warning(self, self.lm.get("SettingsBusiness.validation_error", "Validation Error"), self.lm.get("SettingsBusiness.business_name_required", "Business name is required"))
            return
        
        settings_data = {
            'business_name': self.business_name.text().strip(),
            'business_phone': self.business_phone.text().strip(),
            'address': self.address.toPlainText().strip(),
            'tax_id': self.tax_id.text().strip(),
            'notes': self.notes.toPlainText().strip(),
            'default_tax_rate': self.default_tax_rate.value(),
            'logo_url': self.logo_url.text().strip() if self.logo_url.text().strip() else None,
            'create_by': self.user.id
        }
        
        try:
            updated_settings = self.business_service.update_settings(
                settings_data,
                current_user=self.user
            )
            
            if updated_settings:
                self.current_settings = updated_settings
                self.settings_changed.emit()
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("SettingsBusiness.save_success", "Settings saved successfully!"))
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("SettingsBusiness.save_error", "Failed to save settings"))
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.error', 'Error')}: {str(e)}")
