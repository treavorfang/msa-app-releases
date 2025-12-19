from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QTextEdit, QPushButton, QMessageBox)

from utils.language_manager import language_manager

class SupplierDialog(QDialog):
    def __init__(self, container, supplier=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.supplier = supplier
        self.lm = language_manager
        title = self.lm.get("Inventory.supplier_details", "Supplier Details") if supplier else self.lm.get("Inventory.new_supplier", "New Supplier")
        self.setWindowTitle(title)
        self.resize(500, 600)
        self._setup_ui()
        
        if supplier:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.supplier_name", "Name") + ":", self.name_input)
        
        self.contact_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.contact_person", "Contact Person") + ":", self.contact_input)
        
        self.email_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.supplier_email", "Email") + ":", self.email_input)
        
        self.phone_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.supplier_phone", "Phone") + ":", self.phone_input)
        
        self.address_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.supplier_address", "Address") + ":", self.address_input)
        
        self.tax_id_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.tax_id", "Tax ID") + ":", self.tax_id_input)
        
        self.payment_terms_input = QLineEdit()
        form_layout.addRow(self.lm.get("Inventory.payment_terms", "Payment Terms") + ":", self.payment_terms_input)
        
        self.notes_input = QTextEdit()
        form_layout.addRow(self.lm.get("Inventory.supplier_notes", "Notes") + ":", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.name_input.setText(self.supplier.name)
        self.contact_input.setText(self.supplier.contact_person or "")
        self.email_input.setText(self.supplier.email or "")
        self.phone_input.setText(self.supplier.phone or "")
        self.address_input.setText(self.supplier.address or "")
        self.tax_id_input.setText(self.supplier.tax_id or "")
        self.payment_terms_input.setText(self.supplier.payment_terms or "")
        self.notes_input.setText(self.supplier.notes or "")

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, self.lm.get("Common.warning", "Validation Error"), self.lm.get("Inventory.supplier_name_required", "Name is required."))
            return
            
        data = {
            'name': name,
            'contact_person': self.contact_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'phone': self.phone_input.text().strip() or None,
            'address': self.address_input.text().strip() or None,
            'tax_id': self.tax_id_input.text().strip() or None,
            'payment_terms': self.payment_terms_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None
        }
        
        try:
            if self.supplier:
                result = self.container.supplier_controller.update_supplier(self.supplier.id, data)
                if result:
                    QMessageBox.information(self, "Success", "Supplier updated successfully!")
                    self.accept()
                else:
                    raise Exception("Update returned None")
            else:
                result = self.container.supplier_controller.create_supplier(data)
                if result:
                    QMessageBox.information(self, "Success", f"Supplier '{result.name}' created successfully!")
                    self.accept()
                else:
                    raise Exception("Create returned None")
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Inventory.supplier_create_failed' if not self.supplier else 'Inventory.supplier_update_failed', 'Failed to save supplier')}: {str(e)}")
