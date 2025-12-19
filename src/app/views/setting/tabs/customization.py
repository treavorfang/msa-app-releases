
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QScrollArea, QMessageBox, QGroupBox,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from utils.language_manager import language_manager

class CustomizationTab(QWidget):
    settings_changed = Signal()

    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        container_widget = QWidget()
        main_layout = QVBoxLayout(container_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Helper for common styling ---
        card_style = """
            QFrame#CustomCard {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 12px;
            }
        """
        
        def create_card_title(text):
            label = QLabel(text)
            label.setStyleSheet("font-weight: bold; font-size: 16px; color: #3B82F6; margin-bottom: 5px;")
            return label

        # 1. Numbering Formats Group (3 Columns Modern)
        num_card = QFrame()
        num_card.setObjectName("CustomCard")
        num_card.setStyleSheet(card_style)
        num_card_layout = QVBoxLayout(num_card)
        num_card_layout.setContentsMargins(20, 20, 20, 20)
        num_card_layout.setSpacing(15)
        
        num_card_layout.addWidget(create_card_title(self.lm.get("Customization.numbering_group", "Document Numbering")))
        
        cols_container = QHBoxLayout()
        cols_container.setSpacing(20)
        
        # Ticket Format
        tkt_col = QVBoxLayout()
        tkt_col.addWidget(QLabel(self.lm.get("Customization.ticket_format", "Ticket Format")))
        self.ticket_format = QLineEdit()
        self.ticket_format.setPlaceholderText("RPT-{branch}{date}-{seq}")
        self._style_input(self.ticket_format)
        tkt_col.addWidget(self.ticket_format)
        cols_container.addLayout(tkt_col, 1)
        
        # Invoice Format
        inv_col = QVBoxLayout()
        inv_col.addWidget(QLabel(self.lm.get("Customization.invoice_format", "Invoice Format")))
        self.invoice_format = QLineEdit()
        self.invoice_format.setPlaceholderText("INV-{branch}{date}-{seq}")
        self._style_input(self.invoice_format)
        inv_col.addWidget(self.invoice_format)
        cols_container.addLayout(inv_col, 1)
        
        # PO Format
        po_col = QVBoxLayout()
        po_col.addWidget(QLabel(self.lm.get("Customization.po_format", "PO Format")))
        self.po_format = QLineEdit()
        self.po_format.setPlaceholderText("PO-{branch}{date}-{seq}")
        self._style_input(self.po_format)
        po_col.addWidget(self.po_format)
        cols_container.addLayout(po_col, 1)
        
        num_card_layout.addLayout(cols_container)
        main_layout.addWidget(num_card)
        
        # 2. Ticket Terms Group
        tkt_card = QFrame()
        tkt_card.setObjectName("CustomCard")
        tkt_card.setStyleSheet(card_style)
        tkt_card_layout = QVBoxLayout(tkt_card)
        tkt_card_layout.setContentsMargins(20, 20, 20, 20)
        tkt_card_layout.setSpacing(10)
        
        tkt_card_layout.addWidget(create_card_title(self.lm.get("Customization.ticket_terms_group", "Ticket Terms (Max 4 Lines)")))
        
        tkt_grid = QFormLayout()
        tkt_grid.setSpacing(10)
        self.ticket_term_lines = []
        for i in range(1, 5):
            line = QLineEdit()
            line.setMaxLength(60)
            self._style_input(line)
            tkt_grid.addRow(f"{self.lm.get('Customization.line', 'Line')} {i}:", line)
            self.ticket_term_lines.append(line)
        tkt_card_layout.addLayout(tkt_grid)
        main_layout.addWidget(tkt_card)
        
        # 3. Invoice Terms Group
        inv_card = QFrame()
        inv_card.setObjectName("CustomCard")
        inv_card.setStyleSheet(card_style)
        inv_card_layout = QVBoxLayout(inv_card)
        inv_card_layout.setContentsMargins(20, 20, 20, 20)
        inv_card_layout.setSpacing(10)
        
        inv_card_layout.addWidget(create_card_title(self.lm.get("Customization.invoice_terms_group", "Invoice Terms (Max 4 Lines)")))
        
        inv_grid = QFormLayout()
        inv_grid.setSpacing(10)
        self.invoice_term_lines = []
        for i in range(1, 5):
            line = QLineEdit()
            line.setMaxLength(60)
            self._style_input(line)
            inv_grid.addRow(f"{self.lm.get('Customization.line', 'Line')} {i}:", line)
            self.invoice_term_lines.append(line)
        inv_card_layout.addLayout(inv_grid)
        main_layout.addWidget(inv_card)
        
        # Save Button
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        self.save_btn = QPushButton(f"  {self.lm.get('Common.save_settings', 'Save Settings')}  ")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setMinimumWidth(200)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        btn_container.addWidget(self.save_btn)
        main_layout.addLayout(btn_container)
        
        main_layout.addStretch()
        scroll.setWidget(container_widget)
        layout.addWidget(scroll)

    def _style_input(self, widget):
        widget.setFixedHeight(35)
        widget.setStyleSheet("""
            QLineEdit {
                border: 1px solid palette(mid);
                border-radius: 6px;
                padding: 5px 10px;
                background-color: palette(base);
                color: palette(text);
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)

    def _load_settings(self):
        try:
            settings = self.container.business_settings_service.get_settings()
            self.ticket_format.setText(settings.ticket_number_format)
            self.invoice_format.setText(settings.invoice_number_format)
            self.po_format.setText(settings.po_number_format)
            
            # Split existing terms by newline and fill lines
            tkt_terms = settings.ticket_terms or ""
            tkt_lines = tkt_terms.split("\n")
            for i, line in enumerate(self.ticket_term_lines):
                if i < len(tkt_lines):
                    line.setText(tkt_lines[i])
                    
            inv_terms = settings.invoice_terms or ""
            inv_lines = inv_terms.split("\n")
            for i, line in enumerate(self.invoice_term_lines):
                if i < len(inv_lines):
                    line.setText(inv_lines[i])
                    
        except Exception as e:
            print(f"Error loading customization settings: {e}")

    def _save_settings(self):
        try:
            # Join lines with newlines
            tkt_terms = "\n".join([line.text().strip() for line in self.ticket_term_lines if line.text().strip()])
            inv_terms = "\n".join([line.text().strip() for line in self.invoice_term_lines if line.text().strip()])
            
            data = {
                'ticket_number_format': self.ticket_format.text().strip(),
                'invoice_number_format': self.invoice_format.text().strip(),
                'po_number_format': self.po_format.text().strip(),
                'ticket_terms': tkt_terms,
                'invoice_terms': inv_terms
            }
            
            # Use business_settings_service to update
            # Note: We need to get current full DTO and only update these fields
            current_settings_dto = self.container.business_settings_service.get_settings()
            settings_dict = current_settings_dto.to_dict()
            settings_dict.update(data)
            
            from dtos.business_settings_dto import BusinessSettingsDTO
            updated_dto = BusinessSettingsDTO(**settings_dict)
            
            if self.container.business_settings_service.update_settings(updated_dto, self.user):
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), 
                                      self.lm.get("Customization.saved_msg", "Settings saved successfully."))
                self.settings_changed.emit()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), 
                                  self.lm.get("Customization.save_error", "Failed to save settings."))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
