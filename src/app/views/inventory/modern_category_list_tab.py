from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QMenu, QDialog, QDialogButtonBox,
                               QLabel, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
                               QTreeWidget, QTreeWidgetItem, QAbstractItemView, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QIcon
from utils.validation.message_handler import MessageHandler
from utils.language_manager import language_manager
from typing import Optional, List
from dtos.category_dto import CategoryDTO

class CategoryFormDialog(QDialog):
    """Dialog for creating/editing categories"""
    def __init__(self, container, category: Optional[CategoryDTO] = None, parent=None):
        super().__init__(parent)
        self.container = container
        self.category = category
        self.lm = language_manager
        self.setWindowTitle(self.lm.get("Categories.edit_category", "Edit Category") if category else self.lm.get("Categories.new_category", "New Category"))
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.lm.get("Categories.enter_category_name", "Enter category name"))
        form_layout.addRow(self.lm.get("Categories.name_label", "Name") + ":", self.name_input)
        
        # Description field
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(self.lm.get("Categories.enter_description", "Enter category description"))
        form_layout.addRow(self.lm.get("Categories.description_label", "Description") + ":", self.description_input)
        
        # Parent category dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.addItem(self.lm.get("Categories.none_top_level", "None (Top Level)"), None)
        
        # Populate with existing categories
        categories = self.container.category_service.list_categories(include_inactive=True)
        for cat in categories:
            if self.category and cat.id == self.category.id:
                continue  # Skip current category to avoid circular reference
            self.parent_combo.addItem(cat.name, cat.id)
        
        form_layout.addRow(self.lm.get("Categories.parent_category", "Parent Category") + ":", self.parent_combo)
        
        # Default markup percentage
        self.markup_spinbox = QDoubleSpinBox()
        self.markup_spinbox.setRange(0, 100)
        self.markup_spinbox.setSuffix("%")
        self.markup_spinbox.setDecimals(2)
        form_layout.addRow(self.lm.get("Categories.default_markup", "Default Markup") + ":", self.markup_spinbox)
        
        # Active checkbox
        self.active_checkbox = QCheckBox(self.lm.get("Common.active", "Active"))
        self.active_checkbox.setChecked(True)
        form_layout.addRow(self.lm.get("Common.status", "Status") + ":", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Pre-fill form if editing
        if self.category:
            self.name_input.setText(self.category.name or "")
            self.description_input.setText(self.category.description or "")
            self.markup_spinbox.setValue(float(self.category.default_markup_percentage or 0))
            self.active_checkbox.setChecked(self.category.is_active)
            
            # Set parent selection
            if self.category.parent_id:
                for i in range(self.parent_combo.count()):
                    if self.parent_combo.itemData(i) == self.category.parent_id:
                        self.parent_combo.setCurrentIndex(i)
                        break
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_form_data(self):
        """Return form data as dictionary"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.text().strip() or None,
            'parent': self.parent_combo.currentData(),
            'default_markup_percentage': self.markup_spinbox.value(),
            'is_active': self.active_checkbox.isChecked()
        }

class ModernCategoryListTab(QWidget):
    """Modern categories management tab with hierarchical tree view"""
    data_changed = Signal()
    
    def __init__(self, container, user=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.controller = self.container.category_controller
        self.user = user
        self.lm = language_manager
        
        # Initialize timers
        self.search_timer = QTimer(self)
        self.search_timer.setInterval(300)
        self.search_timer.setSingleShot(True)
        
        self.setup_ui()
        self.connect_signals()
        
        # Theme handling
        self.current_theme = 'dark'
        if hasattr(self.container, 'theme_controller'):
             self.container.theme_controller.theme_changed.connect(self._on_theme_changed)
             self.current_theme = self.container.theme_controller.current_theme
             
        self._update_all_styles()
        
        # self.refresh_tree()
        self._data_loaded = False

    def setup_ui(self):
        """Setup the UI components with hierarchical tree view"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Summary Cards
        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(12)
        layout.addLayout(self.summary_layout)
        
        # Initialize summary cards
        self.total_cats_card = self._create_summary_card(self.lm.get("Categories.total_categories", "Total Categories"), "0", "#3B82F6", "📂")
        self.active_cats_card = self._create_summary_card(self.lm.get("Categories.active_categories", "Active Categories"), "0", "#10B981", "✅")
        self.inactive_cats_card = self._create_summary_card(self.lm.get("Categories.inactive_categories", "Inactive Categories"), "0", "#6B7280", "⏸️")
        
        self.summary_layout.addWidget(self.total_cats_card)
        self.summary_layout.addWidget(self.active_cats_card)
        self.summary_layout.addWidget(self.inactive_cats_card)
        self.summary_layout.addStretch()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Categories.search_categories", "Search categories..."))
        # Style will be set by _update_input_style
        """
        self.search_input.setStyleSheet(\"\"\"
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #374151;
                border-radius: 6px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        \"\"\")
        """
        toolbar_layout.addWidget(self.search_input)
        
        # Show deleted checkbox
        self.show_deleted_checkbox = QCheckBox(self.lm.get("Common.show_deleted", "Show Deleted"))
        toolbar_layout.addWidget(self.show_deleted_checkbox)
        
        toolbar_layout.addStretch()
        
        # Action Buttons
        self.new_category_btn = self._create_action_button(self.lm.get("Categories.new_category", "New Category"), "#3B82F6")
        self.expand_all_btn = self._create_action_button(self.lm.get("Categories.expand_all", "Expand All"), "#6B7280")
        self.collapse_all_btn = self._create_action_button(self.lm.get("Categories.collapse_all", "Collapse All"), "#6B7280")
        
        toolbar_layout.addWidget(self.new_category_btn)
        toolbar_layout.addWidget(self.expand_all_btn)
        toolbar_layout.addWidget(self.collapse_all_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Categories tree setup
        self.categories_tree = QTreeWidget()
        self.categories_tree.setColumnCount(4)
        headers = [
            self.lm.get("Categories.name_header", "Name"),
            self.lm.get("Categories.description_header", "Description"),
            self.lm.get("Categories.markup_header", "Markup %"),
            self.lm.get("Categories.status_header", "Status")
        ]
        self.categories_tree.setHeaderLabels(headers)
        
        # Configure tree
        self.categories_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.categories_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.categories_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.categories_tree.setAlternatingRowColors(True)
        self.categories_tree.setExpandsOnDoubleClick(True)
        
        # Set column widths
        self.categories_tree.setColumnWidth(0, 300)  # Name
        self.categories_tree.setColumnWidth(1, 400)  # Description
        self.categories_tree.setColumnWidth(2, 100)   # Markup %
        self.categories_tree.setColumnWidth(3, 100)   # Status
        
        # Tree Styling
        # Tree Styling handled by _update_tree_style
        """
        self.categories_tree.setStyleSheet(\"\"\"
            QTreeWidget {
                border: 1px solid #374151;
                border-radius: 8px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #374151;
            }
            QHeaderView::section {
                padding: 8px;
                border: none;
                border-bottom: 2px solid #374151;
                font-weight: bold;
            }
        \"\"\")
        """
        
        layout.addWidget(self.categories_tree)

    def _create_summary_card(self, title, value, color, icon):
        """Create a styled summary card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
            }}
        """)
        card.setFixedHeight(80)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 24px;
            background-color: transparent;
            border-radius: 8px;
            padding: 8px;
        """)
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px; font-weight: 500;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return card

    def _create_action_button(self, text, color):
        """Create a styled action button"""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """)
        return btn

    def _update_summary(self, categories):
        """Update summary cards"""
        total = len(categories)
        active = sum(1 for c in categories if c.is_active and not c.deleted_at)
        inactive = sum(1 for c in categories if not c.is_active and not c.deleted_at)
        
        self._update_card_value(self.total_cats_card, str(total))
        self._update_card_value(self.active_cats_card, str(active))
        self._update_card_value(self.inactive_cats_card, str(inactive))

    def _update_card_value(self, card, value):
        """Update value label in summary card"""
        text_layout = card.layout().itemAt(1).layout()
        value_label = text_layout.itemAt(1).widget()
        value_label.setText(value)

    def _on_theme_changed(self, theme_name):
        """Handle theme changes"""
        self.current_theme = theme_name
        self._update_all_styles()
        
    def _update_all_styles(self):
        """Update all styles based on current theme"""
        self._update_tree_style()
        self._update_input_style()
        
    def _update_tree_style(self):
        """Update tree widget style"""
        is_dark = self.current_theme == 'dark'
        border_color = "#374151" if is_dark else "#E5E7EB"
        
        self.categories_tree.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {border_color};
                border-radius: 8px;
                background-color: {'#1F2937' if is_dark else '#FFFFFF'};
                color: {'white' if is_dark else 'black'};
            }}
            QTreeWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {border_color};
                color: {'white' if is_dark else 'black'};
            }}
            QHeaderView::section {{
                padding: 8px;
                border: none;
                border-bottom: 2px solid {border_color};
                font-weight: bold;
                background-color: {'#374151' if is_dark else '#F3F4F6'};
                color: {'white' if is_dark else 'black'};
            }}
        """)
        
    def _update_input_style(self):
        """Update input field style"""
        is_dark = self.current_theme == 'dark'
        border_color = "#374151" if is_dark else "#D1D5DB"
        bg_color = "#1F2937" if is_dark else "#FFFFFF"
        text_color = "white" if is_dark else "black"
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {border_color};
                border-radius: 6px;
                min-width: 250px;
                background-color: {bg_color};
                color: {text_color};
            }}
            QLineEdit:focus {{
                border-color: #3B82F6;
            }}
        """)

    def connect_signals(self):
        """Connect all signals to their slots"""
        self.new_category_btn.clicked.connect(self.handle_new_category)
        self.expand_all_btn.clicked.connect(self.categories_tree.expandAll)
        self.collapse_all_btn.clicked.connect(self.categories_tree.collapseAll)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_timer.timeout.connect(self.perform_search)
        self.show_deleted_checkbox.stateChanged.connect(self.refresh_tree)
        
        self.controller.category_created.connect(self.refresh_tree)
        self.controller.category_updated.connect(self.refresh_tree)
        self.controller.category_deleted.connect(self.refresh_tree)
        self.controller.category_restored.connect(self.refresh_tree)
        
        self.categories_tree.itemDoubleClicked.connect(self.handle_tree_double_click)
        self.categories_tree.customContextMenuRequested.connect(self.show_context_menu)

    def build_category_tree(self, categories: List[CategoryDTO]):
        """Build hierarchical tree from flat category list"""
        # Create a dictionary for quick lookup
        category_dict = {cat.id: cat for cat in categories}
        top_level_items = []
        
        # First pass: create all items
        items_by_id = {}
        for category in categories:
            item = QTreeWidgetItem()
            item.setText(0, category.name or "")
            item.setText(1, category.description or "")
            item.setText(2, f"{category.default_markup_percentage}%")
            
            # Update status text to show deleted status
            if category.deleted_at:
                status_text = self.lm.get("Common.deleted", "Deleted")
            else:
                status_text = self.lm.get("Common.active", "Active") if category.is_active else self.lm.get("Categories.inactive", "Inactive")
            item.setText(3, status_text)
            
            item.setData(0, Qt.UserRole, category.id)
            
            # Style inactive and deleted categories
            if category.deleted_at:
                # Red text for deleted items
                for col in range(4):
                    item.setForeground(col, QBrush(QColor(239, 68, 68))) # Red
            elif not category.is_active:
                # Gray text for inactive items
                for col in range(4):
                    item.setForeground(col, QBrush(QColor(156, 163, 175))) # Gray
            
            items_by_id[category.id] = item
        
        # Second pass: build hierarchy (only for non-deleted items)
        for category in categories:
            item = items_by_id[category.id]
            if category.parent_id and category.parent_id in items_by_id:
                parent_item = items_by_id[category.parent_id]
                parent_item.addChild(item)
            else:
                top_level_items.append(item)
        
        return top_level_items
    
    def show_context_menu(self, position):
        """Show context menu for category operations"""
        item = self.categories_tree.itemAt(position)
        if not item:
            return
                
        category_id = item.data(0, Qt.UserRole)
        category = self.controller.get_category(category_id)
        menu = QMenu(self)
        
        # View Category Details
        view_details_action = menu.addAction(self.lm.get("Categories.view_details", "View Details"))
        view_details_action.triggered.connect(lambda: self.handle_view_details(category_id))
        
        if not category or not category.deleted_at:
            # Edit Category (only for non-deleted)
            edit_action = menu.addAction(self.lm.get("Categories.edit_category", "Edit Category"))
            edit_action.triggered.connect(lambda: self.perform_edit(category_id))
            
            # Add Subcategory (only for non-deleted)
            add_subcategory_action = menu.addAction(self.lm.get("Categories.add_subcategory", "Add Subcategory"))
            add_subcategory_action.triggered.connect(lambda: self.handle_add_subcategory(category_id))
            
            menu.addSeparator()
            
            # Delete Category (only for non-deleted)
            delete_action = menu.addAction(self.lm.get("Categories.delete_category", "Delete Category"))
            delete_action.triggered.connect(lambda: self.handle_delete_category(category_id))
        else:
            # Restore Category (only for deleted)
            restore_action = menu.addAction(self.lm.get("Categories.restore_category", "Restore Category"))
            restore_action.triggered.connect(lambda: self.handle_restore_category(category_id))
        
        menu.exec_(self.categories_tree.viewport().mapToGlobal(position))

    def display_categories_tree(self, categories: List[CategoryDTO]):
        """Display categories in hierarchical tree view"""
        try:
            self.categories_tree.clear()
            self._update_summary(categories)
            
            if not categories:
                return
            
            # Build hierarchical tree
            top_level_items = self.build_category_tree(categories)
            
            # Add to tree widget
            self.categories_tree.addTopLevelItems(top_level_items)
            
            # Expand all items by default
            self.categories_tree.expandAll()
            
            # Sort by name
            self.categories_tree.sortItems(0, Qt.AscendingOrder)
            
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Failed to display categories: {str(e)}")

    def get_selected_category_id(self):
        """Get the ID of the currently selected category"""
        selected_items = self.categories_tree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(0, Qt.UserRole)

    def handle_add_subcategory(self, parent_category_id):
        """Handle adding a subcategory to the selected category"""
        try:
            parent_category = self.controller.get_category(parent_category_id)
            if not parent_category:
                MessageHandler.show_warning(self, "Error", "Parent category not found")
                return
            
            dialog = CategoryFormDialog(self.container, parent=self)
            # Pre-set the parent in the dialog
            for i in range(dialog.parent_combo.count()):
                if dialog.parent_combo.itemData(i) == parent_category_id:
                    dialog.parent_combo.setCurrentIndex(i)
                    break
            
            dialog.setWindowTitle(f"Add Subcategory to {parent_category.name}")
            
            if dialog.exec_() == QDialog.Accepted:
                category_data = dialog.get_form_data()
                result = self.controller.create_category(category_data)
                if result:
                    MessageHandler.show_info(self, "Success", "Subcategory created successfully")
                    self.refresh_tree()
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not create subcategory: {str(e)}")

    def handle_view_details(self, category_id):
        """Show detailed category information"""
        try:
            category = self.controller.get_category(category_id)
            if not category:
                MessageHandler.show_warning(self, "Error", "Category not found")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Category Details")
            layout = QVBoxLayout()
            
            # Create formatted details
            details = [
                f"<b>Name:</b> {category.name or 'Not specified'}",
                f"<b>Description:</b> {category.description or 'Not specified'}",
                f"<b>Parent Category:</b> {category.parent_name if category.parent_name else 'None'}",
                f"<b>Default Markup:</b> {category.default_markup_percentage}%",
                f"<b>Status:</b> {'Active' if category.is_active else 'Inactive'}",
                f"<b>Created:</b> {category.created_at.strftime('%Y-%m-%d %H:%M') if category.created_at else 'Unknown'}",
                f"<b>Last Updated:</b> {category.updated_at.strftime('%Y-%m-%d %H:%M') if category.updated_at else 'Unknown'}"
            ]
            
            # Add deleted info if applicable
            if category.deleted_at:
                details.append(f"<b>Deleted:</b> {category.deleted_at.strftime('%Y-%m-%d %H:%M')}")
                if category.deleted_by_name:
                    details.append(f"<b>Deleted By:</b> {category.deleted_by_name}")
            
            # Add child categories if any
            children = self.get_child_categories(category_id)
            if children:
                child_names = ", ".join([child.name for child in children[:5]])
                details.append(f"<b>Child Categories ({len(children)}):</b> {child_names}")
                if len(children) > 5:
                    details[-1] += f" (+{len(children)-5} more)"
            
            # Add labels for each detail
            for detail in details:
                label = QLabel(detail)
                label.setTextFormat(Qt.RichText)
                label.setWordWrap(True)
                layout.addWidget(label)
            
            # Add close button
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            dialog.resize(500, 400)
            dialog.exec_()
            
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not show details: {str(e)}")

    def get_child_categories(self, category_id):
        """Get child categories for a given parent"""
        categories = self.controller.list_categories(include_inactive=True)
        return [cat for cat in categories if cat.parent_id == category_id]

    def handle_new_category(self):
        """Handle new category creation"""
        try:
            dialog = CategoryFormDialog(self.container, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                category_data = dialog.get_form_data()
                result = self.controller.create_category(category_data, self.user)
                if result:
                    MessageHandler.show_info(self, "Success", "Category created successfully")
                    self.refresh_tree()
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not create category: {str(e)}")

    def handle_tree_double_click(self, item, column):
        """Handle double-click on tree item"""
        try:
            category_id = item.data(0, Qt.UserRole)
            if category_id:
                self.perform_edit(category_id)
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not edit category: {str(e)}")

    def perform_edit(self, category_id: int):
        """Execute the edit operation"""
        try:
            if not category_id:
                MessageHandler.show_warning(self, "Warning", "No category selected")
                return
            
            category = self.controller.get_category(category_id)
            if not category:
                MessageHandler.show_warning(self, "Error", "Category not found")
                return
            
            if category.deleted_at:
                MessageHandler.show_warning(self, "Error", "Cannot edit a deleted category")
                return
            
            dialog = CategoryFormDialog(self.container, category, self)
            if dialog.exec_() == QDialog.Accepted:
                update_data = dialog.get_form_data()
                result = self.controller.update_category(category_id, update_data, self.user)
                if result:
                    MessageHandler.show_info(self, "Success", "Category updated successfully")
                    self.refresh_tree()
                    
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not perform edit: {str(e)}")

    def handle_delete_category(self, category_id=None):
        """Handle category deletion with confirmation"""
        try:
            if category_id is None:
                category_id = self.get_selected_category_id()
            
            if not category_id:
                MessageHandler.show_warning(self, "Warning", "Please select a category to delete")
                return
            
            category = self.controller.get_category(category_id)
            if not category:
                MessageHandler.show_warning(self, "Error", "Category not found")
                return
            
            if category.deleted_at:
                MessageHandler.show_warning(self, "Error", "Category is already deleted")
                return
            
            # Check if category has children
            children = self.get_child_categories(category_id)
            if children:
                MessageHandler.show_warning(
                    self,
                    "Cannot Delete",
                    "This category has child categories. Please move or delete the child categories first."
                )
                return
            
            if MessageHandler.show_question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the category '{category.name}'?\nThis action will soft delete the category."
            ):
                success = self.controller.delete_category(category_id, self.user)
                if success:
                    MessageHandler.show_info(self, "Success", "Category deleted successfully")
                    self.refresh_tree()
                else:
                    MessageHandler.show_warning(self, "Error", "Could not delete category")
                    
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not delete category: {str(e)}")

    def handle_restore_category(self, category_id=None):
        """Handle category restoration"""
        try:
            if category_id is None:
                category_id = self.get_selected_category_id()
            
            if not category_id:
                MessageHandler.show_warning(self, "Warning", "Please select a category to restore")
                return
            
            category = self.controller.get_category(category_id)
            if not category:
                MessageHandler.show_warning(self, "Error", "Category not found")
                return
            
            if not category.deleted_at:
                MessageHandler.show_warning(self, "Error", "Category is not deleted")
                return
            
            if MessageHandler.show_question(
                self,
                "Confirm Restore",
                f"Are you sure you want to restore the category '{category.name}'?"
            ):
                success = self.controller.restore_category(category_id, self.user)
                if success:
                    MessageHandler.show_info(self, "Success", "Category restored successfully")
                    self.refresh_tree()
                else:
                    MessageHandler.show_warning(self, "Error", "Could not restore category")
                    
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not restore category: {str(e)}")

    def on_search_changed(self):
        """Trigger search after debounce delay"""
        self.search_timer.start()

    def perform_search(self):
        """Execute search with current query"""
        search_text = self.search_input.text().strip()
        show_deleted = self.show_deleted_checkbox.isChecked()
        
        try:
            if search_text:
                # Search across categories
                categories = self.controller.search_categories(search_text, show_deleted)
            else:
                # Show all categories
                categories = self.controller.list_categories(include_inactive=True, include_deleted=show_deleted)
            
            self.display_categories_tree(categories)
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Search failed: {str(e)}")

    def refresh_tree(self):
        """Refresh the tree with current data"""
        self.perform_search()

    def set_current_user(self, user):
        """Set the current user for audit logging"""
        self.user = user

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self.refresh_tree)
            self._data_loaded = True
