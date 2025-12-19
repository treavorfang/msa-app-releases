from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QCompleter
from PySide6.QtCore import QStringListModel, Qt
from config.config_manager import config_manager

class DeviceInput(QWidget):
    def __init__(self):
        super().__init__()
        
        # Brand Combo (with new entry handling)
        self.brand_combo = QComboBox()
        self.brand_combo.setEditable(True)
        self.brand_combo.addItems(config_manager.available_brands)
        
        # Set Apple as default selected brand
        apple_index = self.brand_combo.findText("Apple")
        if apple_index >= 0:
            self.brand_combo.setCurrentIndex(apple_index)
        
        # Model Input (dynamic based on brand)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Model")
        
        # Setup Model Autocomplete with custom filtering
        self.model_completer = QCompleter()
        self.model_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.model_completer.setFilterMode(Qt.MatchContains)  # Key change 1
        self.model_completer.setCompletionMode(QCompleter.PopupCompletion)
        
        # Initialize with empty model
        self.model_completer.setModel(QStringListModel())
        self.model_input.setCompleter(self.model_completer)
        
        # Connect signals
        self.brand_combo.currentTextChanged.connect(self._update_model_suggestions)
        self.model_input.textEdited.connect(self._update_completer_model)  # Key change 2
        
        # Initialize suggestions for default brand
        self._update_model_suggestions(self.brand_combo.currentText())

    def _update_model_suggestions(self, brand):
        """Update available models based on brand"""
        self.current_brand_models = config_manager.get_brand_models(brand)
        self._update_completer_model(self.model_input.text())

    def _update_completer_model(self, text):
        """Update the completer model based on current text"""
        if not hasattr(self, 'current_brand_models'):
            return
            
        # Filter models that contain the input text (case-insensitive)
        filtered_models = [
            model for model in self.current_brand_models
            if text.lower() in model.lower()
        ]
        
        # Update the completer model
        self.model_completer.model().setStringList(filtered_models)