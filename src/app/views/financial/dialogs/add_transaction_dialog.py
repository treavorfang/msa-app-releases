"""
Add Transaction Dialog - Modern Redesign
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QDateEdit, 
                             QMessageBox, QFrame, QWidget, QButtonGroup, 
                             QPlainTextEdit)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

from views.components.money_input import MoneyInput
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class AddTransactionDialog(QDialog):
    def __init__(self, parent=None, financial_service=None, transaction_obj=None, user=None, branch_id=None):
        super().__init__(parent)
        self.financial_service = financial_service
        self.user = user
        self.branch_id = branch_id
        self.lm = language_manager
        self.cf = currency_formatter
        self.transaction_obj = transaction_obj
        self.is_income = False 
        
        # Window Setup
        title = self.lm.get("Financial.edit_transaction", "Edit Transaction") if transaction_obj else self.lm.get("Financial.add_transaction", "Add Transaction")
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLabel {
                color: #A0A0A0;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QDateEdit, QPlainTextEdit {
                background-color: #2D2D2D;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #3B82F6;
                background-color: #333333;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #A0A0A0;
                margin-right: 10px;
            }
        """)
        
        self._setup_ui()
        self._load_categories()
        
        # Populate if editing
        if self.transaction_obj:
            self._load_transaction_data()
            
    def _load_transaction_data(self):
        t = self.transaction_obj
        
        # Set Type
        is_inc = (t.type == 'income')
        self._set_type(is_inc)
        
        # Set Date
        self.date_edit.setDate(t.date.date())
        
        # Set Category
        # Need to ensure categories are loaded first. _set_type calls _load_categories
        index = self.cat_combo.findData(t.category_id)
        if index >= 0:
            self.cat_combo.setCurrentIndex(index)
            
        # Set Amount
        self.amt_input.setValue(t.amount)
        
        # Set Description
        self.desc_input.setPlainText(t.description or "")
        
        # Set Payment Method
        method_index = self.method_combo.findText(t.payment_method)
        if method_index >= 0:
            self.method_combo.setCurrentIndex(method_index)
            
        # Update Button Text
        self.save_btn.setText(self.lm.get("Financial.update_transaction", "Update Transaction"))
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # --- 1. Toggle Switch (Segmented Control look) ---
        toggle_container = QFrame()
        toggle_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(4, 4, 4, 4)
        toggle_layout.setSpacing(4)
        
        self.btn_expense = self._create_toggle_btn(self.lm.get("Financial.type_expense", "Expense"), True)
        self.btn_income = self._create_toggle_btn(self.lm.get("Financial.type_income", "Income"), False)
        
        self.btn_expense.clicked.connect(lambda: self._set_type(False))
        self.btn_income.clicked.connect(lambda: self._set_type(True))
        
        toggle_layout.addWidget(self.btn_expense)
        toggle_layout.addWidget(self.btn_income)
        main_layout.addWidget(toggle_container)
        
        # --- 2. Hero Amount Input ---
        amount_container = QVBoxLayout()
        amount_container.setSpacing(8)
        
        lbl_amount = QLabel(self.lm.get("Financial.amount", "Amount").upper())
        lbl_amount.setAlignment(Qt.AlignCenter)
        lbl_amount.setStyleSheet("font-size: 12px; letter-spacing: 1px;")
        
        self.amt_input = MoneyInput()
        self.amt_input.setAlignment(Qt.AlignCenter)
        self.amt_input.setPlaceholderText("0")
        
        # Configure Currency
        self.amt_input.set_currency(self.cf.symbol, self.cf.position)
        
        amount_container.addWidget(lbl_amount)
        amount_container.addWidget(self.amt_input)
        main_layout.addLayout(amount_container)
        
        # --- 3. Details Grid (Date, Category, Payment) ---
        grid_layout = QVBoxLayout()
        grid_layout.setSpacing(16)
        
        # Row 1: Date & Category
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        
        # Date
        date_group = QVBoxLayout()
        date_group.setSpacing(6)
        date_group.addWidget(QLabel(self.lm.get("Financial.date", "Date")))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_group.addWidget(self.date_edit)
        row1.addLayout(date_group)
        
        # Category
        cat_group = QVBoxLayout()
        cat_group.setSpacing(6)
        cat_group.addWidget(QLabel(self.lm.get("Financial.category", "Category")))
        self.cat_combo = QComboBox()
        cat_group.addWidget(self.cat_combo)
        row1.addLayout(cat_group)
        
        grid_layout.addLayout(row1)
        
        # Row 2: Payment Method
        pay_group = QVBoxLayout()
        pay_group.setSpacing(6)
        pay_group.addWidget(QLabel(self.lm.get("Financial.payment_method", "Payment Method")))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            self.lm.get("Financial.payment_cash", "Cash"),
            self.lm.get("Financial.payment_bank", "Bank Transfer"),
            self.lm.get("Financial.payment_card", "Card"),
            self.lm.get("Financial.payment_check", "Check"),
            self.lm.get("Financial.payment_other", "Other")
        ])
        pay_group.addWidget(self.method_combo)
        grid_layout.addLayout(pay_group)
        
        main_layout.addLayout(grid_layout)
        
        # --- 4. Description (Multi-line) ---
        desc_group = QVBoxLayout()
        desc_group.setSpacing(6)
        desc_group.addWidget(QLabel(self.lm.get("Financial.description", "Description")))
        self.desc_input = QPlainTextEdit()
        self.desc_input.setPlaceholderText(self.lm.get("Financial.description", "Description") + "...")
        self.desc_input.setFixedHeight(80) # Fixed height for multi-line
        desc_group.addWidget(self.desc_input)
        main_layout.addLayout(desc_group)
        
        main_layout.addStretch()
        
        # --- 5. Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton(self.lm.get("Financial.cancel", "Cancel"))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        # Using fixed height to ensure consistency with save button
        cancel_btn.setFixedHeight(45) 
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #404040;
                color: #CCCCCC;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333333;
                color: white;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton(self.lm.get("Financial.save", "Save Transaction"))
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(45) # Consistent height
        # Style set in _update_theme
        self.save_btn.clicked.connect(self._save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)
        
        # Initialize
        self._set_type(False) # Start as Expense

    def _create_toggle_btn(self, text, is_active):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(True)
        btn.setFixedHeight(32)
        return btn

    def _set_type(self, is_income):
        self.is_income = is_income
        
        # Update Toggle Visuals
        if is_income:
            self.btn_income.setChecked(True)
            self.btn_expense.setChecked(False)
            active_color = "#10B981" # Green
            self.btn_income.setStyleSheet(f"background-color: {active_color}; color: white; border-radius: 6px; font-weight: bold;")
            self.btn_expense.setStyleSheet("background-color: transparent; color: #808080; border-radius: 6px; font-weight: 500;")
        else:
            self.btn_expense.setChecked(True)
            self.btn_income.setChecked(False)
            active_color = "#EF4444" # Red
            self.btn_expense.setStyleSheet(f"background-color: {active_color}; color: white; border-radius: 6px; font-weight: bold;")
            self.btn_income.setStyleSheet("background-color: transparent; color: #808080; border-radius: 6px; font-weight: 500;")
            
        # Update Amount Input Style
        self.amt_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 32px;
                font-weight: bold;
                color: {active_color};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
            QLineEdit:placeholder {{ color: #404040; }}
        """)
        
        # Update Save Button
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {active_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 14px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        
        self._load_categories()

    def _load_categories(self):
        self.cat_combo.clear()
        if self.financial_service:
            categories = self.financial_service.get_categories(self.is_income)
            for cat in categories:
                self.cat_combo.addItem(cat.name, cat.id)
            if not categories:
                self.cat_combo.addItem(self.lm.get("Common.none", "None"), None)

    def _save(self):
        try:
            amount = self.amt_input.value()
            if amount <= 0:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), 
                                  self.lm.get("Financial.error_amount", "Please enter a valid amount"))
                return
            
            trans_type = 'income' if self.is_income else 'expense'
            date_val = self.date_edit.date().toPython()
            date_obj = datetime.combine(date_val, datetime.min.time())
            cat_id = self.cat_combo.currentData()
            
            if cat_id is None:
                 QMessageBox.warning(self, self.lm.get("Common.error", "Error"), 
                                   self.lm.get("Financial.error_category", "Please select a valid category"))
                 return

            if self.transaction_obj:
                # Update existing
                self.financial_service.update_transaction(
                    transaction_id=self.transaction_obj.id,
                    amount=amount,
                    type=trans_type,
                    category_id=cat_id,
                    date_obj=date_obj,
                    description=self.desc_input.toPlainText(),
                    payment_method=self.method_combo.currentText(),
                    current_user=self.user,
                    ip_address=None
                )
            else:
                # Add new
                user_id = getattr(self.user, 'id', None)
                self.financial_service.add_transaction(
                    amount=amount,
                    type=trans_type,
                    category_id=cat_id,
                    date_obj=date_obj,
                    description=self.desc_input.toPlainText(),
                    payment_method=self.method_combo.currentText(),
                    branch_id=self.branch_id,
                    user_id=user_id,
                    current_user=self.user,
                    ip_address=None
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"Failed to save: {str(e)}")
