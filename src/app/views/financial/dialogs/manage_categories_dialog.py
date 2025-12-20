"""
Manage Categories Dialog - Create, Edit, Delete Categories
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QLineEdit, QCheckBox, QColorDialog, QMessageBox,
                             QFrame, QWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QAction
from utils.language_manager import language_manager

class CategoryFormDialog(QDialog):
    """Dialog to create or edit a single category"""
    def __init__(self, parent=None, category=None, is_income=False):
        super().__init__(parent)
        self.lm = language_manager
        self.category = category
        self.current_color = category.color if category else "#3B82F6"
        self.is_income = is_income if not category else category.is_income
        
        self.setWindowTitle(self.lm.get("Financial.category", "Category"))
        self.setFixedWidth(350)
        
        self._setup_ui()
        
        # Apply initial theme from parent if possible, else default to dark
        current_theme = 'dark'
        if parent and hasattr(parent, 'current_theme'):
             current_theme = parent.current_theme
        elif parent and hasattr(parent, 'container') and hasattr(parent.container, 'theme_controller'):
             current_theme = parent.container.theme_controller.current_theme
             
        self.update_theme(current_theme)
        
    def update_theme(self, theme_name):
        """Update styling based on theme"""
        if theme_name == 'dark':
            bg_color = "#1E1E1E"
            text_color = "white"
            input_bg = "#2D2D2D"
            input_border = "#404040"
            label_color = "#A0A0A0"
            btn_cancel_border = "#404040"
            btn_bg = "#3B82F6"
        else:
            bg_color = "#FFFFFF"
            text_color = "#1F2937"
            input_bg = "#F3F4F6"
            input_border = "#D1D5DB"
            label_color = "#6B7280"
            btn_cancel_border = "#D1D5DB"
            btn_bg = "#2563EB"
            
        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_color}; color: {text_color}; }}
            QLineEdit {{ 
                background-color: {input_bg}; border: 1px solid {input_border}; 
                border-radius: 6px; padding: 8px; color: {text_color};
            }}
            QLabel {{ color: {label_color}; font-size: 13px; }}
            QPushButton {{ 
                background-color: {btn_bg}; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-weight: bold;
            }}
            QPushButton#btnCancel {{
                background-color: transparent; border: 1px solid {btn_cancel_border}; color: {text_color};
            }}
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Name
        layout.addWidget(QLabel(self.lm.get("Financial.name", "Name")))
        self.name_input = QLineEdit()
        if self.category:
            self.name_input.setText(self.category.name)
        layout.addWidget(self.name_input)
        
        # Type
        type_label = self.lm.get("Financial.type", "Type")
        type_val = self.lm.get("Financial.type_income", "Income") if self.is_income else self.lm.get("Financial.type_expense", "Expense")
        layout.addWidget(QLabel(f"{type_label}: {type_val}"))
        
        # Color
        layout.addWidget(QLabel(self.lm.get("Financial.color", "Color")))
        color_layout = QHBoxLayout()
        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(40, 40)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 20px;")
        self.color_preview.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        cancel_btn.setObjectName("btnCancel") # For specific styling
        
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            # Explicitly override stylesheet for this specific button to keep circle shape/color
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 20px;")
            
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "color": self.current_color,
            "is_income": self.is_income
        }

class ManageCategoriesDialog(QDialog):
    def __init__(self, parent=None, financial_service=None, user=None):
        super().__init__(parent)
        self.service = financial_service
        self.user = user
        self.lm = language_manager
        
        self.setWindowTitle(self.lm.get("Financial.manage_categories", "Manage Categories"))
        self.resize(500, 400)
        
        self.is_income_view = False
        self._setup_ui()
        self._toggle_type()
        self._load_categories()
        
        # Apply theme
        # Try to infer theme from parent or use default
        current_theme = 'dark'
        if parent and hasattr(parent, 'container') and hasattr(parent.container, 'theme_controller'):
             self.current_theme = parent.container.theme_controller.current_theme
             current_theme = self.current_theme
        
        self.update_theme(current_theme)

    def update_theme(self, theme_name):
        self.current_theme = theme_name
        if theme_name == 'dark':
            bg_color = "#1E1E1E"
            text_color = "white"
            list_bg = "#2D2D2D"
            list_item_border = "#333"
            list_item_selected = "#333"
            btn_bg = "#3B82F6"
        else:
            bg_color = "#FFFFFF"
            text_color = "#1F2937"
            list_bg = "#F3F4F6"
            list_item_border = "#E5E7EB"
            list_item_selected = "#E5E7EB"
            btn_bg = "#2563EB"
            
        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_color}; color: {text_color}; }}
            QListWidget {{ background-color: {list_bg}; border: none; border-radius: 8px; outline: none; }}
            QListWidget::item {{ padding: 12px; border-bottom: 1px solid {list_item_border}; color: {text_color}; }}
            QListWidget::item:selected {{ background-color: {list_item_selected}; color: {text_color}; }}
            QPushButton {{ 
                background-color: {btn_bg}; color: white; border-radius: 6px; padding: 8px 16px; border: none;
            }}
            QPushButton#btnTypeToggle {{
                /* Specific style handled in toggle logic, but base setup */
                color: white; font-weight: bold;
            }}
        """)
        
        # Refresh logic to update toggle button and list if needed
        self._toggle_type()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header / Filter
        header_layout = QHBoxLayout()
        self.type_toggle = QPushButton()
        self.type_toggle.setObjectName("btnTypeToggle")
        self.type_toggle.setCheckable(True)
        # Style set in _toggle_type
        self.type_toggle.clicked.connect(self._toggle_type)
        header_layout.addWidget(self.type_toggle)
        header_layout.addStretch()
        
        add_btn = QPushButton(self.lm.get("Financial.add_category", "+ Add Category"))
        add_btn.clicked.connect(self._add_category)
        header_layout.addWidget(add_btn)
        main_layout.addLayout(header_layout)
        
        # List
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)
        
        # Context Menu
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _toggle_type(self):
        self.is_income_view = self.type_toggle.isChecked()
        label = self.lm.get("Financial.showing_income", "Showing: Income") if self.is_income_view else self.lm.get("Financial.showing_expense", "Showing: Expense")
        self.type_toggle.setText(label)
        
        # Set colors for toggle button
        if self.is_income_view:
             color = "#10B981" # Green
        else:
             color = "#EF4444" # Red
             
        self.type_toggle.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; font-weight: bold; }}
            QPushButton:hover {{ background-color: {color}; filter: brightness(110%); }}
        """)
        
        self._load_categories()

    def _load_categories(self):
        self.list_widget.clear()
        categories = self.service.get_categories(self.is_income_view)
        for cat in categories:
            item = QListWidgetItem()
            # Custom widget for item? Simple text for now, maybe icon with color
            item.setText(cat.name)
            item.setData(Qt.UserRole, cat)
            
            # Icon for color
            pixmap = QIcon(self._create_color_pixmap(cat.color))
            item.setIcon(pixmap)
            
            self.list_widget.addItem(item)
            
    def _create_color_pixmap(self, color_str):
        from PySide6.QtGui import QPixmap, QPainter
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(color_str))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        painter.end()
        return pixmap

    def _add_category(self):
        dialog = CategoryFormDialog(self, is_income=self.is_income_view)
        # Pass current theme? Dialog tries to get it from parent (self)
        if dialog.exec_():
            data = dialog.get_data()
            if not data['name']:
                return
            self.service.add_category(data['name'], data['is_income'], data['color'], current_user=self.user)
            self._load_categories()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        edit_action = menu.addAction(self.lm.get("Common.edit", "Edit"))
        delete_action = menu.addAction(self.lm.get("Common.delete", "Delete"))
        
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        cat = item.data(Qt.UserRole)
        
        if action == edit_action:
            self._edit_category(cat)
        elif action == delete_action:
            self._delete_category(cat)
            
    def _edit_category(self, cat):
        dialog = CategoryFormDialog(self, category=cat)
        if dialog.exec_():
            data = dialog.get_data()
            if not data['name']: return
            self.service.update_category(cat.id, data['name'], cat.is_income, data['color'], current_user=self.user)
            self._load_categories()
            
    def _delete_category(self, cat):
        confirm_msg = self.lm.get("Financial.confirm_delete_category", "Delete category '{0}'?").format(cat.name)
        if QMessageBox.question(self, self.lm.get("Common.confirm", "Confirm"), confirm_msg) == QMessageBox.Yes:
            self.service.delete_category(cat.id, current_user=self.user)
            self._load_categories()
