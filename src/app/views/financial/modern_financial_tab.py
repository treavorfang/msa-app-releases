"""
Modern Financial Tab - Income and Expense Management.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QScrollArea, QGridLayout, 
                             QDateEdit, QComboBox, QMessageBox, QFileDialog, QMenu)
from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtGui import QColor
from datetime import datetime, timedelta
import warnings

from views.components.metric_card import MetricCard
from views.financial.dialogs.add_transaction_dialog import AddTransactionDialog
from views.components.donut_chart import ExpenseBreakdownCard
from utils.currency_formatter import currency_formatter
from utils.language_manager import language_manager
from core.event_bus import EventBus
from core.events import BranchContextChangedEvent

class ModernFinancialTab(QWidget):
    def __init__(self, container, user=None):
        super().__init__()
        self.container = container
        self.financial_service = container.financial_service
        self.user = user
        self.lm = language_manager
        self.cf = currency_formatter
        
        # Initialize branch from user OR default to 1 (Main Branch)
        self.current_branch_id = getattr(self.user, 'branch_id', 1) or 1
        
        self._setup_ui()
        self._refresh_data()
        
        # Branch context handling
        EventBus.subscribe(BranchContextChangedEvent, self._on_branch_changed)
        
        # Theme handling
        if hasattr(self.container, 'theme_controller'):
             self.container.theme_controller.theme_changed.connect(self._on_theme_changed)
             # Apply current theme
             self._on_theme_changed(self.container.theme_controller.current_theme)
        
    def _on_branch_changed(self, event):
        """Update branch ID and refresh data when branch context changes."""
        self.current_branch_id = event.branch_id
        self._refresh_data()
        
    def _on_theme_changed(self, theme_name):
        """Update chart theme when application theme changes"""
        if hasattr(self, 'chart_card'):
            self.chart_card.update_theme(theme_name)
            
        # Update button styles based on theme
        if hasattr(self, 'manage_btn') and hasattr(self, 'btn_export') and hasattr(self, 'add_btn'):
            if theme_name == 'dark':
                primary_bg = "#3B82F6"
                primary_hover = "#2563EB"
                secondary_bg = "#4B5563"
                secondary_hover = "#6B7280"
                export_bg = "#374151"
                export_hover = "#4B5563"
                text_color = "white"
            else:
                primary_bg = "#2563EB"
                primary_hover = "#1D4ED8"
                secondary_bg = "#E5E7EB"
                secondary_hover = "#D1D5DB"
                export_bg = "#F3F4F6"
                export_hover = "#E5E7EB"
                text_color = "#374151" # Dark text for light buttons
                primary_text = "white"

            # Manage Categories (Secondary)
            self.manage_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {secondary_bg};
                    color: {text_color};
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {secondary_hover}; }}
            """)
            
            # Export (Secondary/Tertiary)
            self.btn_export.setStyleSheet(f"""
                QPushButton {{
                    background-color: {export_bg};
                    color: {text_color};
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {export_hover}; }}
            """)
            
            # Add Transaction (Primary)
            # Primary button usually has white text in both themes
            self.add_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_bg};
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ background-color: {primary_hover}; }}
            """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        
        title = QLabel(self.lm.get("Financial.title", "Financial Management"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Date Filter
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            self.lm.get("Financial.period_this_month", "This Month"),
            self.lm.get("Financial.period_last_month", "Last Month"),
            self.lm.get("Financial.period_this_year", "This Year")
        ])
        self.date_filter.currentIndexChanged.connect(self._refresh_data)
        header_layout.addWidget(self.date_filter)
        
        
        # Manage Categories
        self.manage_btn = QPushButton(self.lm.get("Financial.categories", "Categories"))
        # Clean initialization without hardcoded styles - set in theme handler
        self.manage_btn.clicked.connect(self._open_manage_categories)
        header_layout.addWidget(self.manage_btn)
        
        # Export Button
        self.btn_export = QPushButton(self.lm.get("Common.export", "Export"))
        self.btn_export.clicked.connect(self._export_data)
        header_layout.addWidget(self.btn_export)

        # Add Transaction Button
        self.add_btn = QPushButton(self.lm.get("Financial.add_transaction", "+ Add Transaction"))
        self.add_btn.clicked.connect(self._open_add_dialog)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # --- Metrics ---
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(15)
        
        # Income Card
        self.card_income = MetricCard("💰", "$0.00", 
                                    self.lm.get("Financial.income", "Income"), 
                                    "Includes Sales", "#10B981")
        metrics_layout.addWidget(self.card_income)
        
        # Expense Card
        self.card_expense = MetricCard("💸", "$0.00", 
                                     self.lm.get("Financial.expense", "Expenses"), 
                                     "Manual Entry", "#EF4444")
        metrics_layout.addWidget(self.card_expense)
        
        # Balance Card
        self.card_balance = MetricCard("⚖️", "$0.00", 
                                     self.lm.get("Financial.net_balance", "Net Balance"), 
                                     "Income - Expense", "#3B82F6")
        metrics_layout.addWidget(self.card_balance)
        
        layout.addLayout(metrics_layout)
        
        # --- Split View: List (Left) & Chart (Right) ---
        content_split = QHBoxLayout()
        
        # List Frame (Left)
        list_frame = QFrame()
        list_frame.setObjectName("cardFrame")
        if not list_frame.styleSheet():
            list_frame.setStyleSheet("QFrame { background-color: transparent; }")
            
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_title = QLabel(self.lm.get("Financial.recent_transactions", "Recent Transactions"))
        list_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        list_layout.addWidget(list_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            self.lm.get("Financial.date", "Date"),
            self.lm.get("Financial.type", "Type"),
            self.lm.get("Financial.category", "Category"),
            self.lm.get("Financial.description", "Description"),
            self.lm.get("Financial.amount", "Amount")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        list_layout.addWidget(self.table)
        content_split.addWidget(list_frame, 3) # 75% width
        
        # Chart (Right)
        self.chart_card = ExpenseBreakdownCard()
        content_split.addWidget(self.chart_card, 1) # 25% width
        
        layout.addLayout(content_split)
        
    def _open_add_dialog(self):
        dialog = AddTransactionDialog(self, self.financial_service, user=self.user, branch_id=self.current_branch_id)
        if dialog.exec():
            self._refresh_data()
            
    def _get_date_range(self):
        index = self.date_filter.currentIndex()
        today = datetime.now().date()
        
        if index == 0: # This Month
            start = today.replace(day=1)
            end = today
        elif index == 1: # Last Month
            first = today.replace(day=1) 
            end = first - timedelta(days=1)
            start = end.replace(day=1)
        else: # This Year
            start = today.replace(month=1, day=1)
            end = today
            
        return start, end

    def _refresh_data(self):
        start_date, end_date = self._get_date_range()
        
        # 1. Update Metrics
        summary = self.financial_service.get_dashboard_summary(start_date, end_date, self.current_branch_id)
        
        self.card_income.update_value(self.cf.format(summary['total_income']))
        self.card_expense.update_value(self.cf.format(summary['total_expense']))
        self.card_balance.update_value(self.cf.format(summary.get('net_profit', 0)))
        
        # 2. Update Chart
        expense_breakdown = self.financial_service.get_expense_breakdown(start_date, end_date, self.current_branch_id)
        income_breakdown = self.financial_service.get_income_breakdown(start_date, end_date, self.current_branch_id)
        
        self.chart_card.set_data(expense_breakdown, income_breakdown)
        
        # 3. Update Table
        transactions = self.financial_service.get_recent_transactions(limit=100, branch_id=self.current_branch_id)
        
        self.table.setRowCount(0)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Disconnect existing signals to avoid duplicates
        # Suppress RuntimeWarning for first disconnect (when no connection exists)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                self.table.customContextMenuRequested.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.table.itemDoubleClicked.disconnect()
            except (RuntimeError, TypeError):
                pass
        
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(self._on_table_double_click)
        
        for t in transactions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Date
            date_item = QTableWidgetItem(t.date.strftime("%Y-%m-%d"))
            date_item.setData(Qt.UserRole, t.id) # Store ID
            self.table.setItem(row, 0, date_item)
            
            # Type
            type_str = self.lm.get("Financial.type_income", "Income") if t.type == 'income' else self.lm.get("Financial.type_expense", "Expense")
            type_item = QTableWidgetItem(type_str)
            if t.type == 'income':
                type_item.setForeground(QColor("#10B981"))
            else:
                type_item.setForeground(QColor("#EF4444"))
            self.table.setItem(row, 1, type_item)
            
            # Category
            cat_name = t.category_name or "-"
            self.table.setItem(row, 2, QTableWidgetItem(cat_name))
            
            # Description
            self.table.setItem(row, 3, QTableWidgetItem(t.description or ""))
            
            # Amount
            amt_item = QTableWidgetItem(self.cf.format(t.amount))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, amt_item)

    def _on_table_double_click(self, item):
        """Handle double click to edit"""
        row = item.row()
        # ID is stored in the first column (Date)
        id_item = self.table.item(row, 0)
        if id_item:
            transaction_id = id_item.data(Qt.UserRole)
            self._edit_transaction(transaction_id)

    def _show_context_menu(self, position):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
            
        menu = QMenu(self)
        
        edit_action = menu.addAction(self.lm.get("Common.edit", "Edit"))
        delete_action = menu.addAction(self.lm.get("Common.delete", "Delete"))
        
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        
        # Get ID from row
        row = index.row()
        id_item = self.table.item(row, 0)
        transaction_id = id_item.data(Qt.UserRole)
        
        if action == edit_action:
            self._edit_transaction(transaction_id)
        elif action == delete_action:
            self._delete_transaction(transaction_id)

    def _export_data(self):
        """Show export options"""
        menu = QMenu(self)
        
        csv_action = menu.addAction(self.lm.get("Financial.export_csv", "Export to CSV"))
        pdf_action = menu.addAction(self.lm.get("Financial.export_pdf", "Export to PDF"))
        
        action = menu.exec(self.btn_export.mapToGlobal(QPoint(0, self.btn_export.height())))
        
        if action == csv_action:
            self._export_csv()
        elif action == pdf_action:
            self._export_pdf()
            
    def _export_csv(self):
        start_date, end_date = self._get_date_range()
        
        # Reuse service logic
        filename = f"financial_export_{datetime.now().strftime('%Y%m%d')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", filename, "CSV Files (*.csv)")
        
        if path:
            success = self.financial_service.export_to_csv(start_date, end_date, path, self.current_branch_id)
            if success:
                 QMessageBox.information(self, "Success", self.lm.get("Financial.export_success", "Export Successful"))
            else:
                 QMessageBox.warning(self, "Error", self.lm.get("Financial.export_failed", "Export Failed"))

    def _export_pdf(self):
        """Export financial data to PDF report using WeasyPrint"""
        start_date, end_date = self._get_date_range()
        
        # Get transactions for the selected period
        transactions = self.financial_service.get_recent_transactions(limit=1000, branch_id=self.current_branch_id)
        
        # Filter by date range
        # Convert datetime to date for comparison if needed
        filtered_transactions = [
            t for t in transactions 
            if start_date <= (t.date.date() if hasattr(t.date, 'date') else t.date) <= end_date
        ]
        
        if not filtered_transactions:
            QMessageBox.information(
                self,
                self.lm.get("Common.info", "Info"),
                self.lm.get("Financial.no_transactions_to_export", "No transactions to export for the selected period")
            )
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.lm.get("Financial.export_pdf", "Save PDF"),
            f"financial_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not path:
            return
        
        try:
            # Import WeasyPrint (lazy import)
            import platform
            import os
            from decimal import Decimal
            
            # MacOS Fix for WeasyPrint
            if platform.system() == 'Darwin':
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
            
            from weasyprint import HTML, CSS
            
            # Use fonts that support Burmese
            font_family = "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"
            
            # Get summary data
            summary = self.financial_service.get_dashboard_summary(start_date, end_date, self.current_branch_id)
            
            html = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4; margin: 15mm; }}
                    body {{ font-family: {font_family}; }}
                    h1 {{ color: #2980B9; margin-bottom: 5px; }}
                    .meta {{ font-size: 10pt; color: #7F8C8D; margin-bottom: 20px; }}
                    
                    /* Summary Boxes */
                    .summary-container {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .summary-box {{ 
                        border: 1px solid #BDC3C7; 
                        padding: 10px; 
                        width: 150px;
                        background-color: #ECF0F1;
                        border-radius: 4px;
                    }}
                    .summary-label {{ font-size: 9pt; color: #7F8C8D; }}
                    .summary-value {{ font-size: 11pt; font-weight: bold; color: #2C3E50; }}
                    
                    /* Table */
                    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 20px; }}
                    th {{ 
                        background-color: #3498DB; 
                        color: white; 
                        padding: 8px; 
                        text-align: left; 
                        border: 1px solid #2980B9;
                    }}
                    td {{ 
                        padding: 6px; 
                        border: 1px solid #BDC3C7; 
                        color: #2C3E50;
                    }}
                    tr:nth-child(even) {{ background-color: #F8F9F9; }}
                    
                    /* Type Colors */
                    .type-income {{ color: #27AE60; font-weight: bold; }}
                    .type-expense {{ color: #E74C3C; font-weight: bold; }}
                    
                    .amount-right {{ text-align: right; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Financial.report_title", "FINANCIAL REPORT")}</h1>
                <div class="meta">{self.lm.get("Common.generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                <div class="meta">{self.lm.get("Financial.period", "Period")}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}</div>
            """
            
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Financial.income", "Income")}</div>
                        <div class="summary-value" style="color: #27AE60;">{self.cf.format(summary['total_income'])}</div>
                    </div>
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Financial.expense", "Expenses")}</div>
                        <div class="summary-value" style="color: #E74C3C;">{self.cf.format(summary['total_expense'])}</div>
                    </div>
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Financial.net_balance", "Net Balance")}</div>
                        <div class="summary-value" style="color: #3B82F6;">{self.cf.format(summary.get('net_profit', 0))}</div>
                    </div>
                </div>
            """
            
            # Table Header
            html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Financial.date", "Date")}</th>
                            <th>{self.lm.get("Financial.type", "Type")}</th>
                            <th>{self.lm.get("Financial.category", "Category")}</th>
                            <th>{self.lm.get("Financial.description", "Description")}</th>
                            <th style="text-align: right;">{self.lm.get("Financial.amount", "Amount")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Sort transactions by date (newest first)
            sorted_transactions = sorted(filtered_transactions, key=lambda x: x.date, reverse=True)
            
            # Table Rows
            for t in sorted_transactions:
                type_str = self.lm.get("Financial.type_income", "Income") if t.type == 'income' else self.lm.get("Financial.type_expense", "Expense")
                type_class = "type-income" if t.type == 'income' else "type-expense"
                cat_name = t.category_name or "-"
                description = t.description or ""
                
                html += f"""
                    <tr>
                        <td>{t.date.strftime('%Y-%m-%d')}</td>
                        <td class="{type_class}">{type_str}</td>
                        <td>{cat_name}</td>
                        <td>{description}</td>
                        <td class="amount-right">{self.cf.format(t.amount)}</td>
                    </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Generate PDF
            HTML(string=html).write_pdf(path)
            
            QMessageBox.information(
                self,
                self.lm.get("Common.success", "Success"),
                self.lm.get("Financial.export_success", "Financial report exported successfully!")
            )
            
        except ImportError as e:
            QMessageBox.critical(
                self,
                self.lm.get("Common.error", "Error"),
                f"{self.lm.get('Financial.weasyprint_not_installed', 'WeasyPrint is not installed')}: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.lm.get("Common.error", "Error"),
                f"{self.lm.get('Financial.export_failed', 'Failed to export PDF')}: {str(e)}"
            )

    def _edit_transaction(self, transaction_id):
        transaction = self.financial_service.get_transaction(transaction_id)
        if transaction:
            dialog = AddTransactionDialog(self, self.financial_service, transaction_obj=transaction, user=self.user, branch_id=self.current_branch_id)
            if dialog.exec():
                self._refresh_data()
        
    def _delete_transaction(self, transaction_id):
        # Confirm
        reply = QMessageBox.question(self, 
            self.lm.get("Common.confirm", "Confirm"),
            self.lm.get("Financial.confirm_delete", "Are you sure you want to delete this transaction?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            if self.financial_service.delete_transaction(transaction_id, current_user=self.user, ip_address=None):
                self._refresh_data()
            else:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), 
                                  self.lm.get("Financial.delete_failed", "Failed to delete transaction"))

    def _open_manage_categories(self):
        from views.financial.dialogs.manage_categories_dialog import ManageCategoriesDialog
        dialog = ManageCategoriesDialog(self, self.financial_service, user=self.user)
        dialog.exec()
        self._refresh_data() 

