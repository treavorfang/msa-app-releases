# src/app/views/settings/tabs/categories.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLineEdit, QMenu, QDialog, QDialogButtonBox,
                              QLabel, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
                              QTreeWidget, QTreeWidgetItem, QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from models.category import Category
from utils.validation.message_handler import MessageHandler
from typing import Optional, List

class CategoryFormDialog(QDialog):
    """Dialog for creating/editing categories"""
    def __init__(self, container, category: Optional[Category] = None, parent=None):
        super().__init__(parent)
        self.container = container
        self.category = category
        self.setWindowTitle("Edit Category" if category else "New Category")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter category name")
        form_layout.addRow("Name:", self.name_input)
        
        # Description field
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter category description")
        form_layout.addRow("Description:", self.description_input)
        
        # Parent category dropdown
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("None (Top Level)", None)
        
        # Populate with existing categories
        categories = self.container.category_service.list_categories(include_inactive=True)
        for cat in categories:
            if self.category and cat.id == self.category.id:
                continue  # Skip current category to avoid circular reference
            self.parent_combo.addItem(cat.name, cat.id)
        
        form_layout.addRow("Parent Category:", self.parent_combo)
        
        # Default markup percentage
        self.markup_spinbox = QDoubleSpinBox()
        self.markup_spinbox.setRange(0, 100)
        self.markup_spinbox.setSuffix("%")
        self.markup_spinbox.setDecimals(2)
        form_layout.addRow("Default Markup:", self.markup_spinbox)
        
        # Active checkbox
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("Status:", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Pre-fill form if editing
        if self.category:
            self.name_input.setText(self.category.name or "")
            self.description_input.setText(self.category.description or "")
            self.markup_spinbox.setValue(float(self.category.default_markup_percentage or 0))
            self.active_checkbox.setChecked(self.category.is_active)
            
            # Set parent selection
            if self.category.parent:
                for i in range(self.parent_combo.count()):
                    if self.parent_combo.itemData(i) == self.category.parent.id:
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

class CategoriesTab(QWidget):
    """Categories management tab with hierarchical tree view"""
    data_changed = Signal()
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.controller = self.container.category_controller
        self.user = user
        
        # Initialize timers
        self.search_timer = QTimer()
        self.search_timer.setInterval(300)
        self.search_timer.setSingleShot(True)
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_tree()

    def setup_ui(self):
        """Setup the UI components with hierarchical tree view"""
        layout = QVBoxLayout(self)
        
        # Filter/search controls
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search categories...")
        self.search_input.setClearButtonEnabled(True)
        filter_layout.addWidget(self.search_input)
        
        # Add show deleted checkbox
        self.show_deleted_checkbox = QCheckBox("Show Deleted")
        self.show_deleted_checkbox.stateChanged.connect(self.refresh_tree)
        filter_layout.addWidget(self.show_deleted_checkbox)

        layout.addLayout(filter_layout)

        #Button layout
        btn_layout= QHBoxLayout()
        
        self.new_category_btn = QPushButton("New Category")
        self.edit_category_btn = QPushButton("Edit Category")
        self.delete_category_btn = QPushButton("Delete Category")
        self.restore_category_btn = QPushButton("Restore Category")  # Add restore button
        self.expand_all_btn = QPushButton("Expand All")
        self.collapse_all_btn = QPushButton("Collapse All")
        
        btn_layout.addWidget(self.new_category_btn)
        btn_layout.addWidget(self.edit_category_btn)
        btn_layout.addWidget(self.delete_category_btn)
        btn_layout.addWidget(self.restore_category_btn)  # Add restore button
        btn_layout.addWidget(self.expand_all_btn)
        btn_layout.addWidget(self.collapse_all_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Categories tree setup
        self.categories_tree = QTreeWidget()
        self.categories_tree.setColumnCount(4)
        headers = ["Name", "Description", "Markup %", "Status"]
        self.categories_tree.setHeaderLabels(headers)
        
        # Configure tree
        self.categories_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.categories_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.categories_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.categories_tree.setAlternatingRowColors(True)
        self.categories_tree.setExpandsOnDoubleClick(True)
        
        # Set column widths
        self.categories_tree.setColumnWidth(0, 200)  # Name
        self.categories_tree.setColumnWidth(1, 250)  # Description
        self.categories_tree.setColumnWidth(2, 80)   # Markup %
        self.categories_tree.setColumnWidth(3, 80)   # Status
        
        # INCREASE FONT SIZE - Set a reasonable size (20 is too large, try 12-14)
        font = self.categories_tree.font()
        font.setPointSize(12)  # More reasonable size
        self.categories_tree.setFont(font)
        
        # Also increase header font size (40 is too large, try 12-14)
        header_font = self.categories_tree.header().font()
        header_font.setPointSize(12)
        self.categories_tree.header().setFont(header_font)
        
        layout.addWidget(self.categories_tree)

    def connect_signals(self):
        """Connect all signals to their slots"""
        self.new_category_btn.clicked.connect(self.handle_new_category)
        self.edit_category_btn.clicked.connect(self.handle_edit_category)
        self.delete_category_btn.clicked.connect(self.handle_delete_category)
        self.restore_category_btn.clicked.connect(self.handle_restore_category)  # Connect restore
        self.expand_all_btn.clicked.connect(self.categories_tree.expandAll)
        self.collapse_all_btn.clicked.connect(self.categories_tree.collapseAll)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_timer.timeout.connect(self.perform_search)
        self.controller.category_created.connect(self.refresh_tree)
        self.controller.category_updated.connect(self.refresh_tree)
        self.controller.category_deleted.connect(self.refresh_tree)
        self.controller.category_restored.connect(self.refresh_tree)  # Connect restore signal
        self.categories_tree.itemDoubleClicked.connect(self.handle_tree_double_click)
        self.categories_tree.customContextMenuRequested.connect(self.show_context_menu)

    def build_category_tree(self, categories: List[Category]):
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
                status_text = "Deleted"
            else:
                status_text = "Active" if category.is_active else "Inactive"
            item.setText(3, status_text)
            
            item.setData(0, Qt.UserRole, category.id)
            
            # SET FONT SIZE FOR INDIVIDUAL ITEMS
            for col in range(4):
                font = item.font(col)
                font.setPointSize(12)
                item.setFont(col, font)
            
            # Style inactive and deleted categories
            if category.deleted_at:
                # Red text for deleted items
                for col in range(4):
                    item.setForeground(col, QBrush(QColor(255, 0, 0)))
                    font = item.font(col)
                    font.setItalic(True)
                    item.setFont(col, font)
            elif not category.is_active:
                # Gray text for inactive items
                for col in range(4):
                    item.setForeground(col, QBrush(QColor(128, 128, 128)))
                    font = item.font(col)
                    font.setItalic(True)
                    item.setFont(col, font)
            
            items_by_id[category.id] = item
        
        # Second pass: build hierarchy (only for non-deleted items)
        for category in categories:
            item = items_by_id[category.id]
            if category.parent_id and category.parent_id in items_by_id:
                parent_item = items_by_id[category.parent_id]
                parent_item.addChild(item)
                
                # Make parent items bold and slightly larger
                for col in range(4):
                    font = parent_item.font(col)
                    font.setPointSize(13)
                    parent_item.setFont(col, font)
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
        view_details_action = menu.addAction("View Details")
        view_details_action.setShortcut("Ctrl+D")
        view_details_action.triggered.connect(lambda: self.handle_view_details(category_id))
        
        if not category or not category.deleted_at:
            # Edit Category (only for non-deleted)
            edit_action = menu.addAction("Edit Category")
            edit_action.setShortcut("Ctrl+E")
            edit_action.triggered.connect(lambda: self.perform_edit(category_id))
            
            # Add Subcategory (only for non-deleted)
            add_subcategory_action = menu.addAction("Add Subcategory")
            add_subcategory_action.setShortcut("Ctrl+S")
            add_subcategory_action.triggered.connect(lambda: self.handle_add_subcategory(category_id))
            
            menu.addSeparator()
            
            # Delete Category (only for non-deleted)
            delete_action = menu.addAction("Delete Category")
            delete_action.setShortcut("Del")
            delete_action.triggered.connect(lambda: self.handle_delete_category(category_id))
        else:
            # Restore Category (only for deleted)
            restore_action = menu.addAction("Restore Category")
            restore_action.setShortcut("Ctrl+R")
            restore_action.triggered.connect(lambda: self.handle_restore_category(category_id))
        
        menu.addSeparator()
        
        # Create New Category (top level)
        new_category_action = menu.addAction("Create New Top Category")
        new_category_action.setShortcut("Ctrl+N")
        new_category_action.triggered.connect(self.handle_new_category)
        
        menu.exec_(self.categories_tree.viewport().mapToGlobal(position))

    def display_categories_tree(self, categories: List[Category]):
        """Display categories in hierarchical tree view"""
        try:
            self.categories_tree.clear()
            
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
                f"<b>Parent Category:</b> {category.parent.name if category.parent else 'None'}",
                f"<b>Default Markup:</b> {category.default_markup_percentage}%",
                f"<b>Status:</b> {'Active' if category.is_active else 'Inactive'}",
                f"<b>Created:</b> {category.created_at.strftime('%Y-%m-%d %H:%M') if category.created_at else 'Unknown'}",
                f"<b>Last Updated:</b> {category.updated_at.strftime('%Y-%m-%d %H:%M') if category.updated_at else 'Unknown'}"
            ]
            
            # Add deleted info if applicable
            if category.deleted_at:
                details.append(f"<b>Deleted:</b> {category.deleted_at.strftime('%Y-%m-%d %H:%M')}")
                if category.deleted_by:
                    details.append(f"<b>Deleted By:</b> {category.deleted_by.username}")
            
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
        return [cat for cat in categories if cat.parent and cat.parent.id == category_id]

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

    def handle_edit_category(self):
        """Handle edit category button click"""
        try:
            category_id = self.get_selected_category_id()
            if category_id:
                self.perform_edit(category_id)
            else:
                MessageHandler.show_warning(self, "Warning", "Please select a category to edit")
        except Exception as e:
            MessageHandler.show_critical(self, "Error", f"Could not edit category: {str(e)}")

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