# src/app/views/inventory/part_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                               QPushButton, QLabel, QMessageBox, QCheckBox)
from utils.language_manager import language_manager

class PartDialog(QDialog):
    def __init__(self, container, part=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.part = part
        self.is_edit_mode = part is not None
        self.lm = language_manager
        
        title = self.lm.get("Inventory.edit_part", "Edit Part") if self.is_edit_mode else self.lm.get("Inventory.new_part", "Create New Part")
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        self._setup_ui()
        self._load_categories()
        
        if self.is_edit_mode:
            self._load_part_data()

        # Add labels to show what will be auto-generated
        self._setup_auto_generation_hints()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        self.form_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.lm.get("Inventory.ph_part_name", "Enter part name"))
        self.form_layout.addRow(self.lm.get("Inventory.part_name", "Name") + "*:", self.name_input)
        
        # Brand
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText(self.lm.get("Inventory.ph_brand", "Enter brand"))
        self.form_layout.addRow(f"{self.lm.get('Inventory.brand', 'Brand')}:", self.brand_input)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setPlaceholderText(self.lm.get("Inventory.ph_category", "Select or enter category"))
        self.form_layout.addRow(self.lm.get("Inventory.category", "Category") + "*:", self.category_combo)
        
        # Model Compatibility
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(self.lm.get("Inventory.ph_compatible_models", "e.g., iPhone 12, Samsung S21"))
        self.form_layout.addRow(f"{self.lm.get('Inventory.compatible_models', 'Compatible Models')}:", self.model_input)
        
        # Cost Price
        # Cost Price
        from views.components.money_input import MoneyInput
        self.cost_input = MoneyInput(default_value=0.01)
        self.form_layout.addRow(self.lm.get("Inventory.cost_price", "Cost Price") + "*:", self.cost_input)
        
        # Initial Stock
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)
        self.stock_input.setValue(0)
        self.form_layout.addRow(self.lm.get("Inventory.current_stock", "Initial Stock") + ":", self.stock_input)
        
        # Minimum Stock Level
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 9999)
        self.min_stock_input.setValue(5)
        self.min_stock_input.setToolTip(self.lm.get("Inventory.min_stock_tooltip", "Alert when stock falls below this level"))
        self.form_layout.addRow(self.lm.get("Inventory.min_stock", "Min Stock Level") + ":", self.min_stock_input)
        
        # SKU (optional)
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText(self.lm.get("Inventory.ph_sku", "Leave empty to auto-generate"))
        self.form_layout.addRow(self.lm.get("Inventory.sku", "SKU") + ":", self.sku_input)
        
        # Barcode (optional)
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText(self.lm.get("Inventory.ph_barcode", "Leave empty to auto-generate"))
        self.form_layout.addRow(self.lm.get("Inventory.barcode", "Barcode") + ":", self.barcode_input)
        
        # Active status
        self.active_checkbox = QCheckBox(self.lm.get("Common.active", "Active"))
        self.active_checkbox.setChecked(True)
        self.form_layout.addRow(f"{self.lm.get('Common.status', 'Status')}:", self.active_checkbox)
        
        layout.addLayout(self.form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self):
        """Load existing categories into the combo box"""
        # Use controller instead of direct model access
        categories = self.container.category_controller.list_categories(include_inactive=True)
        
        self.category_combo.addItem("", None)
        for category in categories:
            self.category_combo.addItem(category.name, category.id)
    
    def _load_part_data(self):
        """Load existing part data into the form"""
        if not self.part:
            return
            
        self.name_input.setText(self.part.name)
        self.brand_input.setText(self.part.brand or "")
        self.model_input.setText(self.part.model_compatibility or "")
        self.cost_input.setValue(float(self.part.cost_price))
        self.stock_input.setValue(self.part.current_stock)
        self.min_stock_input.setValue(self.part.min_stock_level)
        self.sku_input.setText(self.part.sku or "")
        self.barcode_input.setText(self.part.barcode or "")
        self.active_checkbox.setChecked(self.part.is_active)
        
        # Set category
        if self.part.category_id:
            index = self.category_combo.findData(self.part.category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                self.category_combo.setCurrentText(self.part.category_name or "")

    def _setup_auto_generation_hints(self):
        """Add hints for auto-generated fields"""
        # Add hint labels below SKU and barcode fields
        # Ideally these formats should be configurable, but for now we describe the default behavior
        sku_hint = QLabel(self.lm.get("Inventory.sku_format_hint", "Auto-format: BRAND(3)-CATEGORY(3)-NAME(4)-COUNTER(2)"))
        sku_hint.setStyleSheet("color: gray; font-size: 10px;")
        self.form_layout.addRow("", sku_hint)
        
        barcode_hint = QLabel(self.lm.get("Inventory.barcode_format_hint", "Auto-format: PAR-BRAND(3)MODEL(NO)-XXXX"))
        barcode_hint.setStyleSheet("color: gray; font-size: 10px;")
        self.form_layout.addRow("", barcode_hint)
    
    def _validate_form(self):
        """Validate the form data"""
        errors = []
        
        if not self.name_input.text().strip():
            errors.append(self.lm.get("Validation.part_name_required", "Part name is required"))
        
        if not self.category_combo.currentText().strip():
            errors.append(self.lm.get("Validation.category_required", "Category is required"))
        
        if self.cost_input.value() <= 0:
            errors.append(self.lm.get("Validation.cost_price_gt_0", "Cost price must be greater than 0"))
        
        if self.stock_input.value() < 0:
            errors.append(self.lm.get("Validation.stock_negative", "Stock cannot be negative"))
        
        if self.min_stock_input.value() < 0:
            errors.append(self.lm.get("Validation.min_stock_negative", "Minimum stock level cannot be negative"))
        
        # Check for duplicate SKU if provided
        sku = self.sku_input.text().strip()
        if sku:
            existing_part = self.container.part_service.get_part_by_sku(sku)
            if existing_part and (not self.is_edit_mode or existing_part.id != self.part.id):
                errors.append(self.lm.get("Validation.sku_exists", "SKU '{sku}' already exists").format(sku=sku))
        
        # Check for duplicate barcode if provided
        barcode = self.barcode_input.text().strip()
        if barcode:
            existing_part = self.container.part_service.get_part_by_barcode(barcode)
            if existing_part and (not self.is_edit_mode or existing_part.id != self.part.id):
                errors.append(self.lm.get("Validation.barcode_exists", "Barcode '{barcode}' already exists").format(barcode=barcode))
        
        return errors
    
    def _on_save(self):
        """Handle save button click"""
        errors = self._validate_form()
        if errors:
            QMessageBox.warning(self, self.lm.get("Common.warning", "Validation Error"), "\n".join(errors))
            return
        
        try:
            part_data = {
                'name': self.name_input.text().strip(),
                'brand': self.brand_input.text().strip() or None,
                'category': self.category_combo.currentText().strip(),
                'model_compatibility': self.model_input.text().strip() or None,
                'cost': float(self.cost_input.value()),
                'stock': self.stock_input.value(),
                'min_stock_level': self.min_stock_input.value(),
                'sku': self.sku_input.text().strip() or None,
                'barcode': self.barcode_input.text().strip() or None,
                # 'is_active': self.active_checkbox.isChecked()
            }
            
            if self.is_edit_mode:
                # Update existing part
                part = self.container.part_controller.update_part(
                    self.part.id,
                    **part_data
                )
                message = self.lm.get("Inventory.part_updated_success", "Part '{name}' updated successfully!").format(name=part.name)
            else:
                # Create new part
                part = self.container.part_controller.create_part(
                    brand=part_data['brand'] or '',
                    category=part_data['category'],
                    name=part_data['name'],
                    cost=part_data['cost'],
                    stock=part_data['stock'],
                    sku=part_data['sku'],
                    model_compatibility=part_data['model_compatibility'],
                    min_stock_level=part_data['min_stock_level'],
                    barcode=part_data['barcode'],
                    is_active=self.active_checkbox.isChecked()
                )
                message = self.lm.get("Inventory.part_created_success_detail", "Part '{name}' created successfully!\nSKU: {sku}\nBarcode: {barcode}").format(
                    name=part.name, sku=part.sku, barcode=part.barcode
                )
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), message)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Inventory.part_create_failed' if not self.is_edit_mode else 'Inventory.part_update_failed', 'Failed to save part')}: {str(e)}")
    
    def get_part_data(self):
        """Get the form data as a dictionary"""
        return {
            'name': self.name_input.text().strip(),
            'brand': self.brand_input.text().strip() or None,
            'category': self.category_combo.currentText().strip(),
            'model_compatibility': self.model_input.text().strip() or None,
            'cost': float(self.cost_input.value()),
            'stock': self.stock_input.value(),
            'min_stock_level': self.min_stock_input.value(),
            'sku': self.sku_input.text().strip() or None,
            'barcode': self.barcode_input.text().strip() or None,
            'is_active': self.active_checkbox.isChecked()
        }