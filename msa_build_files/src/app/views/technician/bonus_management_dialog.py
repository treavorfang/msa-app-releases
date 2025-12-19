# src/app/views/technician/bonus_management_dialog.py
"""
Bonus Management Dialog

Allows viewing, adding, and managing bonuses for a technician.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFormLayout, QDialogButtonBox, QDoubleSpinBox, QTextEdit,
    QDateEdit, QCheckBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class BonusManagementDialog(QDialog):
    """Dialog for managing technician bonuses"""
    
    def __init__(self, container, technician, parent=None):
        super().__init__(parent)
        self.container = container
        self.technician = technician
        self.bonus_controller = container.technician_bonus_controller
        self.lm = language_manager
        
        self.setWindowTitle(f"{self.lm.get('Users.bonus_title', 'Bonus Management')} - {technician.full_name}")
        self.setMinimumSize(900, 600)
        
        self._setup_ui()
        self._load_bonuses()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Summary section
        summary_layout = self._create_summary_section()
        layout.addLayout(summary_layout)
        
        # Bonuses table
        table_label = QLabel(self.lm.get("Users.bonus_history", "Bonus History"))
        table_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(table_label)
        
        self.bonuses_table = QTableWidget()
        self.bonuses_table.setColumnCount(7)
        self.bonuses_table.setHorizontalHeaderLabels([
            self.lm.get("Users.bonus_date", "Date"),
            self.lm.get("Common.type", "Type"),
            self.lm.get("Users.bonus_amount", "Amount"),
            self.lm.get("Users.bonus_reason", "Reason"),
            self.lm.get("Common.period", "Period"),
            self.lm.get("Common.paid", "Paid"),
            self.lm.get("Users.actions_header", "Actions")
        ])
        self.bonuses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bonuses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bonuses_table.setAlternatingRowColors(True)
        layout.addWidget(self.bonuses_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_custom_btn = QPushButton(f"➕ {self.lm.get('Users.add_bonus', 'Add Custom Bonus')}")
        self.add_custom_btn.clicked.connect(self._add_custom_bonus)
        button_layout.addWidget(self.add_custom_btn)
        
        self.auto_calculate_btn = QPushButton(f"🔄 {self.lm.get('Users.auto_calculate', 'Auto-Calculate Monthly Bonuses')}")
        self.auto_calculate_btn.clicked.connect(self._auto_calculate_bonuses)
        button_layout.addWidget(self.auto_calculate_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_summary_section(self):
        """Create summary section showing bonus totals"""
        layout = QHBoxLayout()
        
        # Total bonuses
        total_group = QGroupBox(self.lm.get("Users.total_bonuses", "Total Bonuses"))
        total_layout = QVBoxLayout(total_group)
        self.total_bonuses_label = QLabel(currency_formatter.format(0))
        self.total_bonuses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #10B981;")
        total_layout.addWidget(self.total_bonuses_label)
        layout.addWidget(total_group)
        
        # Unpaid bonuses
        unpaid_group = QGroupBox(self.lm.get("Users.unpaid_bonuses", "Unpaid Bonuses"))
        unpaid_layout = QVBoxLayout(unpaid_group)
        self.unpaid_bonuses_label = QLabel(currency_formatter.format(0))
        self.unpaid_bonuses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F59E0B;")
        unpaid_layout.addWidget(self.unpaid_bonuses_label)
        layout.addWidget(unpaid_group)
        
        # This year
        year_group = QGroupBox(self.lm.get("Users.this_year", "This Year"))
        year_layout = QVBoxLayout(year_group)
        self.year_bonuses_label = QLabel(currency_formatter.format(0))
        self.year_bonuses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3B82F6;")
        year_layout.addWidget(self.year_bonuses_label)
        layout.addWidget(year_group)
        
        return layout
    
    def _load_bonuses(self):
        """Load and display bonuses"""
        bonuses = self.bonus_controller.list_bonuses(technician_id=self.technician.id)
        
        # Update summary
        total = self.bonus_controller.get_total_bonuses(self.technician.id)
        unpaid = self.bonus_controller.get_unpaid_bonuses_total(self.technician.id)
        
        year_start = date(datetime.now().year, 1, 1)
        year_total = self.bonus_controller.get_total_bonuses(
            self.technician.id,
            start_date=year_start
        )
        
        self.total_bonuses_label.setText(currency_formatter.format(total))
        self.unpaid_bonuses_label.setText(currency_formatter.format(unpaid))
        self.year_bonuses_label.setText(currency_formatter.format(year_total))
        
        # Update table
        self.bonuses_table.setRowCount(len(bonuses))
        
        for row, bonus in enumerate(bonuses):
            # Date
            date_str = bonus.awarded_date.strftime("%Y-%m-%d")
            self.bonuses_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Type
            type_item = QTableWidgetItem(bonus.bonus_type.title())
            type_colors = {
                'performance': '#3B82F6',
                'quality': '#10B981',
                'revenue': '#8B5CF6',
                'custom': '#F59E0B'
            }
            type_item.setForeground(QColor(type_colors.get(bonus.bonus_type, '#6B7280')))
            self.bonuses_table.setItem(row, 1, type_item)
            
            # Amount
            amount_item = QTableWidgetItem(currency_formatter.format(float(bonus.amount)))
            amount_item.setForeground(QColor("#10B981"))
            self.bonuses_table.setItem(row, 2, amount_item)
            
            # Reason
            self.bonuses_table.setItem(row, 3, QTableWidgetItem(bonus.reason or ""))
            
            # Period
            if bonus.period_start and bonus.period_end:
                period = f"{bonus.period_start} to {bonus.period_end}"
            else:
                period = "N/A"
            self.bonuses_table.setItem(row, 4, QTableWidgetItem(period))
            
            # Paid status
            paid_item = QTableWidgetItem(self.lm.get("Common.yes", "Yes") if bonus.paid else self.lm.get("Common.no", "No"))
            paid_item.setForeground(QColor("#10B981" if bonus.paid else "#EF4444"))
            self.bonuses_table.setItem(row, 5, paid_item)
            
            # Actions button
            if not bonus.paid:
                mark_paid_btn = QPushButton(self.lm.get("Users.mark_paid", "Mark Paid"))
                mark_paid_btn.clicked.connect(lambda checked, b=bonus: self._mark_as_paid(b.id))
                self.bonuses_table.setCellWidget(row, 6, mark_paid_btn)
    
    def _add_custom_bonus(self):
        """Show dialog to add custom bonus"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Users.add_bonus", "Add Custom Bonus"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Amount
        # Amount
        from views.components.money_input import MoneyInput
        amount_input = MoneyInput()
        form.addRow(f"{self.lm.get('Users.bonus_amount', 'Amount')}:*", amount_input)
        
        # Reason
        reason_input = QTextEdit()
        reason_input.setMaximumHeight(80)
        form.addRow(f"{self.lm.get('Users.bonus_reason', 'Reason')}:*", reason_input)
        
        # Period
        period_start = QDateEdit()
        period_start.setCalendarPopup(True)
        period_start.setDate(QDate.currentDate())
        form.addRow(f"{self.lm.get('Users.period_start', 'Period Start')}:", period_start)
        
        period_end = QDateEdit()
        period_end.setCalendarPopup(True)
        period_end.setDate(QDate.currentDate())
        form.addRow(f"{self.lm.get('Users.period_end', 'Period End')}:", period_end)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._save_custom_bonus(
            dialog, amount_input, reason_input, period_start, period_end
        ))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec()
    
    def _save_custom_bonus(self, dialog, amount_input, reason_input, period_start, period_end):
        """Save custom bonus"""
        amount = Decimal(str(amount_input.value()))
        reason = reason_input.toPlainText().strip()
        
        if amount <= 0:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Users.enter_valid_amount", "Please enter a valid amount"))
            return
        
        if not reason:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Users.enter_reason", "Please enter a reason"))
            return
        
        try:
            self.bonus_controller.create_bonus(
                technician_id=self.technician.id,
                bonus_type='custom',
                amount=amount,
                reason=reason,
                period_start=period_start.date().toPython(),
                period_end=period_end.date().toPython(),
                user_id=None  # TODO: Get from session
            )
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Users.bonus_added", "Custom bonus added successfully"))
            self._load_bonuses()
            dialog.accept()
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_add_bonus', 'Failed to add bonus')}: {str(e)}")
    
    def _auto_calculate_bonuses(self):
        """Auto-calculate bonuses for current month"""
        current_month = date(datetime.now().year, datetime.now().month, 1)
        
        reply = QMessageBox.question(
            self,
            self.lm.get("Users.auto_calculate", "Auto-Calculate Bonuses"),
            f"{self.lm.get('Users.calculate_bonuses_confirm', 'Calculate bonuses for')} {current_month.strftime('%B %Y')}?\n\n"
            f"{self.lm.get('Users.bonus_criteria', 'This will create bonuses based on:')}\n"
            f"- {self.lm.get('Users.criteria_performance', 'Performance (tickets completed)')}\n"
            f"- {self.lm.get('Users.criteria_quality', 'Quality (customer ratings)')}\n"
            f"- {self.lm.get('Users.criteria_revenue', 'Revenue (revenue targets)')}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                bonuses = self.bonus_controller.auto_calculate_bonuses(
                    technician_id=self.technician.id,
                    month=current_month,
                    user_id=None  # TODO: Get from session
                )
                
                if bonuses:
                    total = sum(Decimal(str(b.amount)) for b in bonuses)
                    QMessageBox.information(
                        self,
                        self.lm.get("Common.success", "Success"),
                        f"{self.lm.get('Users.bonuses_created', 'Created')} {len(bonuses)} {self.lm.get('Users.bonus_count', 'bonus(es) totaling')} {currency_formatter.format(total)}"
                    )
                else:
                    QMessageBox.information(
                        self,
                        self.lm.get("Users.no_bonuses", "No Bonuses"),
                        self.lm.get("Users.no_bonuses_qualified", "No bonuses qualified for this month based on performance metrics.")
                    )
                
                self._load_bonuses()
            except Exception as e:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_calculate_bonuses', 'Failed to calculate bonuses')}: {str(e)}")
    
    def _mark_as_paid(self, bonus_id: int):
        """Mark bonus as paid"""
        reply = QMessageBox.question(
            self,
            self.lm.get("Users.mark_paid", "Mark as Paid"),
            self.lm.get("Users.mark_paid_confirm", "Mark this bonus as paid?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.bonus_controller.mark_as_paid(bonus_id):
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Users.bonus_marked_paid", "Bonus marked as paid"))
                self._load_bonuses()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), self.lm.get("Users.failed_mark_paid", "Failed to mark bonus as paid"))
