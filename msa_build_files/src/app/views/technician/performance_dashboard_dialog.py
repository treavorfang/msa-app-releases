# src/app/views/technician/performance_dashboard_dialog.py
"""
Performance Dashboard Dialog

Displays comprehensive performance metrics and analytics for a technician.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QGroupBox, QFormLayout, QTabWidget, QWidget, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from utils.performance_charts import PerformanceChartWidget
from utils.performance_export import PerformanceExporter
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter


class PerformanceDashboardDialog(QDialog):
    """Dialog for viewing technician performance metrics"""
    
    def __init__(self, container, technician, parent=None):
        super().__init__(parent)
        self.container = container
        self.technician = technician
        self.performance_controller = container.technician_performance_controller
        self.lm = language_manager
        
        self.setWindowTitle(f"{self.lm.get('Users.dashboard_title', 'Performance Dashboard')} - {technician.full_name}")
        self.setMinimumSize(1000, 700)
        
        self._setup_ui()
        self._load_current_month()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Header with month selector
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Tab widget for different views
        tabs = QTabWidget()
        
        # Current Month tab
        self.current_tab = self._create_current_month_tab()
        tabs.addTab(self.current_tab, self.lm.get("Users.current_month", "Current Month"))
        
        # History tab
        self.history_tab = self._create_history_tab()
        tabs.addTab(self.history_tab, self.lm.get("Users.performance_history", "Performance History"))
        
        # Year-to-Date tab
        self.ytd_tab = self._create_ytd_tab()
        tabs.addTab(self.ytd_tab, self.lm.get("Users.year_to_date", "Year-to-Date"))
        
        # Team Comparison tab
        self.comparison_tab = self._create_comparison_tab()
        tabs.addTab(self.comparison_tab, self.lm.get("Users.team_comparison", "Team Comparison"))
        
        # Charts tab
        self.charts_tab = self._create_charts_tab()
        tabs.addTab(self.charts_tab, f"📊 {self.lm.get('Users.charts', 'Charts')}")
        
        layout.addWidget(tabs)
        
        # Export and action buttons
        button_layout = QHBoxLayout()
        
        export_csv_btn = QPushButton(f"📄 {self.lm.get('Common.export_csv', 'Export to CSV')}")
        export_csv_btn.clicked.connect(self._export_to_csv)
        button_layout.addWidget(export_csv_btn)
        
        export_report_btn = QPushButton(f"📋 {self.lm.get('Users.generate_report', 'Generate Report')}")
        export_report_btn.clicked.connect(self._generate_report)
        button_layout.addWidget(export_report_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header(self):
        """Create header with month selector"""
        layout = QHBoxLayout()
        
        title = QLabel(self.lm.get("Users.dashboard_title", "Performance Dashboard"))
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Month selector
        layout.addWidget(QLabel(f"{self.lm.get('Users.select_month', 'Select Month')}:"))
        self.month_selector = QComboBox()
        
        # Add last 12 months
        current = date.today()
        for i in range(12):
            month = current - relativedelta(months=i)
            month_first = date(month.year, month.month, 1)
            self.month_selector.addItem(
                month.strftime("%B %Y"),
                month_first
            )
        
        self.month_selector.currentIndexChanged.connect(self._on_month_changed)
        layout.addWidget(self.month_selector)
        
        # Recalculate button
        recalc_btn = QPushButton(f"🔄 {self.lm.get('Users.recalculate', 'Recalculate')}")
        recalc_btn.clicked.connect(self._recalculate_performance)
        layout.addWidget(recalc_btn)
        
        return layout
    
    def _create_current_month_tab(self):
        """Create current month performance tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # KPI Summary Cards
        kpi_layout = QHBoxLayout()
        
        self.tickets_card = self._create_kpi_card(self.lm.get("Users.tickets_completed", "Tickets Completed"), "0", "#3B82F6")
        self.revenue_card = self._create_kpi_card(self.lm.get("Users.revenue_generated", "Revenue Generated"), currency_formatter.format(0), "#10B981")
        self.commission_card = self._create_kpi_card(self.lm.get("Users.commission_earned", "Commission Earned"), currency_formatter.format(0), "#8B5CF6")
        self.efficiency_card = self._create_kpi_card(self.lm.get("Users.efficiency_score", "Efficiency Score"), "0.00", "#F59E0B")
        
        kpi_layout.addWidget(self.tickets_card)
        kpi_layout.addWidget(self.revenue_card)
        kpi_layout.addWidget(self.commission_card)
        kpi_layout.addWidget(self.efficiency_card)
        
        layout.addLayout(kpi_layout)
        
        # Detailed metrics
        details_group = QGroupBox(self.lm.get("Users.detailed_metrics", "Detailed Metrics"))
        details_layout = QFormLayout(details_group)
        
        self.pending_label = QLabel("0")
        self.avg_completion_label = QLabel(f"0.00 {self.lm.get('Common.days', 'days')}")
        self.bonuses_label = QLabel(currency_formatter.format(0))
        self.rating_label = QLabel("N/A")
        
        details_layout.addRow(f"{self.lm.get('Users.pending_tickets', 'Pending Tickets')}:", self.pending_label)
        details_layout.addRow(f"{self.lm.get('Users.avg_completion_time', 'Avg Completion Time')}:", self.avg_completion_label)
        details_layout.addRow(f"{self.lm.get('Users.bonuses_earned', 'Bonuses Earned')}:", self.bonuses_label)
        details_layout.addRow(f"{self.lm.get('Users.customer_rating', 'Customer Rating')}:", self.rating_label)
        
        layout.addWidget(details_group)
        
        # Total compensation
        comp_group = QGroupBox(self.lm.get("Users.monthly_compensation", "Monthly Compensation Breakdown"))
        comp_layout = QFormLayout(comp_group)
        
        self.base_salary_label = QLabel(currency_formatter.format(float(self.technician.salary)))
        self.commission_total_label = QLabel(currency_formatter.format(0))
        self.bonuses_total_label = QLabel(currency_formatter.format(0))
        self.total_comp_label = QLabel(currency_formatter.format(0))
        self.total_comp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        
        comp_layout.addRow(f"{self.lm.get('Technicians.base_salary', 'Base Salary')}:", self.base_salary_label)
        comp_layout.addRow(f"{self.lm.get('Technicians.commission', 'Commission')}:", self.commission_total_label)
        comp_layout.addRow(f"{self.lm.get('Users.bonuses', 'Bonuses')}:", self.bonuses_total_label)
        comp_layout.addRow(f"{self.lm.get('Users.total_compensation', 'Total Compensation')}:", self.total_comp_label)
        
        layout.addWidget(comp_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_history_tab(self):
        """Create performance history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            self.lm.get("Common.month", "Month"),
            self.lm.get("Users.tickets", "Tickets"),
            self.lm.get("Users.revenue", "Revenue"),
            self.lm.get("Technicians.commission", "Commission"),
            self.lm.get("Users.bonuses", "Bonuses"),
            self.lm.get("Users.efficiency", "Efficiency"),
            self.lm.get("Users.avg_days", "Avg Days")
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def _create_ytd_tab(self):
        """Create year-to-date summary tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # YTD Summary Cards
        ytd_layout = QHBoxLayout()
        
        self.ytd_tickets_card = self._create_kpi_card(self.lm.get("Users.total_tickets", "Total Tickets"), "0", "#3B82F6")
        self.ytd_revenue_card = self._create_kpi_card(self.lm.get("Users.total_revenue", "Total Revenue"), currency_formatter.format(0), "#10B981")
        self.ytd_commission_card = self._create_kpi_card(self.lm.get("Users.total_commission", "Total Commission"), currency_formatter.format(0), "#8B5CF6")
        self.ytd_bonuses_card = self._create_kpi_card(self.lm.get("Users.total_bonuses", "Total Bonuses"), currency_formatter.format(0), "#F59E0B")
        
        ytd_layout.addWidget(self.ytd_tickets_card)
        ytd_layout.addWidget(self.ytd_revenue_card)
        ytd_layout.addWidget(self.ytd_commission_card)
        ytd_layout.addWidget(self.ytd_bonuses_card)
        
        layout.addLayout(ytd_layout)
        
        # YTD Averages
        avg_group = QGroupBox(self.lm.get("Users.ytd_averages", "Year-to-Date Averages"))
        avg_layout = QFormLayout(avg_group)
        
        self.ytd_avg_completion_label = QLabel(f"0.00 {self.lm.get('Common.days', 'days')}")
        self.ytd_avg_efficiency_label = QLabel("0.00")
        self.ytd_months_label = QLabel(f"0 {self.lm.get('Common.months', 'months')}")
        
        avg_layout.addRow(f"{self.lm.get('Users.avg_completion_time', 'Avg Completion Time')}:", self.ytd_avg_completion_label)
        avg_layout.addRow(f"{self.lm.get('Users.avg_efficiency_score', 'Avg Efficiency Score')}:", self.ytd_avg_efficiency_label)
        avg_layout.addRow(f"{self.lm.get('Users.months_tracked', 'Months Tracked')}:", self.ytd_months_label)
        
        layout.addWidget(avg_group)
        
        # Total YTD Compensation
        ytd_comp_group = QGroupBox(self.lm.get("Users.ytd_compensation", "Year-to-Date Compensation"))
        ytd_comp_layout = QFormLayout(ytd_comp_group)
        
        self.ytd_base_label = QLabel(currency_formatter.format(0))
        self.ytd_comm_label = QLabel(currency_formatter.format(0))
        self.ytd_bonus_label = QLabel(currency_formatter.format(0))
        self.ytd_total_label = QLabel(currency_formatter.format(0))
        self.ytd_total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        
        ytd_comp_layout.addRow(f"{self.lm.get('Technicians.base_salary', 'Base Salary')} (YTD):", self.ytd_base_label)
        ytd_comp_layout.addRow(f"{self.lm.get('Technicians.commission', 'Commission')} (YTD):", self.ytd_comm_label)
        ytd_comp_layout.addRow(f"{self.lm.get('Users.bonuses', 'Bonuses')} (YTD):", self.ytd_bonus_label)
        ytd_comp_layout.addRow(f"{self.lm.get('Users.total_compensation', 'Total Compensation')}:", self.ytd_total_label)
        
        layout.addWidget(ytd_comp_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_comparison_tab(self):
        """Create team comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(self.lm.get("Users.team_comparison_info", "Compare performance with team members for the selected month"))
        info_label.setStyleSheet("color: #9CA3AF; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(6)
        self.comparison_table.setHorizontalHeaderLabels([
            self.lm.get("Users.rank", "Rank"),
            self.lm.get("Users.role_technician", "Technician"),
            self.lm.get("Users.tickets", "Tickets"),
            self.lm.get("Users.revenue", "Revenue"),
            self.lm.get("Users.efficiency", "Efficiency"),
            self.lm.get("Users.avg_days", "Avg Days")
        ])
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comparison_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.comparison_table)
        
        return widget
    
    def _create_kpi_card(self, title, value, color):
        """Create a KPI card"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Store reference to value label
        card.value_label = value_label
        
        return card
    
    def _load_current_month(self):
        """Load current month performance"""
        selected_month = self.month_selector.currentData()
        current_month = date(datetime.now().year, datetime.now().month, 1)
        
        try:
            # If viewing current month, force recalculation to ensure fresh data
            if selected_month == current_month:
                perf = self.performance_controller.calculate_monthly_performance(
                    self.technician.id,
                    selected_month
                )
            else:
                perf = self.performance_controller.get_performance(
                    self.technician.id,
                    selected_month
                )
            
            # Update KPI cards
            self.tickets_card.value_label.setText(str(perf.tickets_completed))
            self.revenue_card.value_label.setText(currency_formatter.format(float(perf.revenue_generated)))
            self.commission_card.value_label.setText(currency_formatter.format(float(perf.commission_earned)))
            self.efficiency_card.value_label.setText(f"{float(perf.efficiency_score):.2f}")
            
            # Update detailed metrics
            self.pending_label.setText(str(perf.tickets_pending))
            self.avg_completion_label.setText(f"{float(perf.avg_completion_days):.2f} {self.lm.get('Common.days', 'days')}")
            self.bonuses_label.setText(currency_formatter.format(float(perf.bonuses_earned)))
            
            if perf.avg_customer_rating > 0:
                self.rating_label.setText(f"{float(perf.avg_customer_rating):.2f} ⭐")
            else:
                self.rating_label.setText("N/A")
            
            # Update compensation breakdown
            base = Decimal(str(self.technician.salary))
            commission = Decimal(str(perf.commission_earned))
            bonuses = Decimal(str(perf.bonuses_earned))
            total = base + commission + bonuses
            
            self.commission_total_label.setText(currency_formatter.format(commission))
            self.bonuses_total_label.setText(currency_formatter.format(bonuses))
            self.total_comp_label.setText(currency_formatter.format(total))
            
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_load_performance', 'Failed to load performance')}: {str(e)}")
        
        # Load other tabs
        self._load_history()
        self._load_ytd()
        self._load_comparison()
    
    def _load_history(self):
        """Load performance history"""
        history = self.performance_controller.get_performance_history(self.technician.id, 12)
        
        self.history_table.setRowCount(len(history))
        
        for row, perf in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(perf.month.strftime("%B %Y")))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(perf.tickets_completed)))
            self.history_table.setItem(row, 2, QTableWidgetItem(currency_formatter.format(float(perf.revenue_generated))))
            self.history_table.setItem(row, 3, QTableWidgetItem(currency_formatter.format(float(perf.commission_earned))))
            self.history_table.setItem(row, 4, QTableWidgetItem(currency_formatter.format(float(perf.bonuses_earned))))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"{float(perf.efficiency_score):.2f}"))
            self.history_table.setItem(row, 6, QTableWidgetItem(f"{float(perf.avg_completion_days):.2f}"))
    
    def _load_ytd(self):
        """Load year-to-date summary"""
        summary = self.performance_controller.get_year_to_date_summary(self.technician.id)
        
        # Update YTD cards
        self.ytd_tickets_card.value_label.setText(str(summary['total_tickets']))
        self.ytd_revenue_card.value_label.setText(currency_formatter.format(summary['total_revenue']))
        self.ytd_commission_card.value_label.setText(currency_formatter.format(summary['total_commission']))
        self.ytd_bonuses_card.value_label.setText(currency_formatter.format(summary['total_bonuses']))
        
        # Update averages
        self.ytd_avg_completion_label.setText(f"{summary['avg_completion_days']:.2f} {self.lm.get('Common.days', 'days')}")
        self.ytd_avg_efficiency_label.setText(f"{summary['avg_efficiency']:.2f}")
        self.ytd_months_label.setText(f"{summary['months_tracked']} {self.lm.get('Common.months', 'months')}")
        
        # Update YTD compensation
        base_ytd = Decimal(str(self.technician.salary)) * summary['months_tracked']
        self.ytd_base_label.setText(currency_formatter.format(base_ytd))
        self.ytd_comm_label.setText(currency_formatter.format(summary['total_commission']))
        self.ytd_bonus_label.setText(currency_formatter.format(summary['total_bonuses']))
        
        total_ytd = base_ytd + summary['total_commission'] + summary['total_bonuses']
        self.ytd_total_label.setText(currency_formatter.format(total_ytd))
    
    def _load_comparison(self):
        """Load team comparison"""
        selected_month = self.month_selector.currentData()
        comparison = self.performance_controller.get_team_comparison(selected_month)
        
        self.comparison_table.setRowCount(len(comparison))
        
        for row, data in enumerate(comparison):
            rank = row + 1
            
            # Highlight current technician
            is_current = data['technician_id'] == self.technician.id
            
            rank_item = QTableWidgetItem(str(rank))
            if is_current:
                rank_item.setBackground(QColor("#3B82F6"))
                rank_item.setForeground(QColor("white"))
            self.comparison_table.setItem(row, 0, rank_item)
            
            name_item = QTableWidgetItem(data['technician_name'])
            if is_current:
                name_item.setBackground(QColor("#3B82F6"))
                name_item.setForeground(QColor("white"))
                name_item.setText(f"{data['technician_name']} (You)")
            self.comparison_table.setItem(row, 1, name_item)
            
            self.comparison_table.setItem(row, 2, QTableWidgetItem(str(data['tickets_completed'])))
            self.comparison_table.setItem(row, 3, QTableWidgetItem(currency_formatter.format(float(data['revenue_generated']))))
            self.comparison_table.setItem(row, 4, QTableWidgetItem(f"{float(data['efficiency_score']):.2f}"))
            self.comparison_table.setItem(row, 5, QTableWidgetItem(f"{float(data['avg_completion_days']):.2f}"))
    
    def _on_month_changed(self):
        """Handle month selection change"""
        self._load_current_month()
    
    def _recalculate_performance(self):
        """Recalculate performance for selected month"""
        selected_month = self.month_selector.currentData()
        
        reply = QMessageBox.question(
            self,
            self.lm.get("Users.recalculate", "Recalculate Performance"),
            f"{self.lm.get('Users.recalculate_confirm', 'Recalculate performance for')} {selected_month.strftime('%B %Y')}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.performance_controller.calculate_monthly_performance(
                    self.technician.id,
                    selected_month
                )
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Users.recalculate_success", "Performance recalculated successfully"))
                self._load_current_month()
            except Exception as e:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_recalculate', 'Failed to recalculate')}: {str(e)}")
    
    def _create_charts_tab(self):
        """Create charts visualization tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chart type selector
        chart_selector_layout = QHBoxLayout()
        chart_selector_layout.addWidget(QLabel(f"{self.lm.get('Users.select_chart', 'Select Chart')}:"))
        
        self.chart_type_selector = QComboBox()
        self.chart_type_selector.addItems([
            self.lm.get("Users.tickets_trend", "Tickets Trend"),
            self.lm.get("Users.revenue_commission", "Revenue & Commission"),
            self.lm.get("Users.efficiency_metrics", "Efficiency Metrics"),
            self.lm.get("Users.compensation_breakdown", "Compensation Breakdown"),
            self.lm.get("Users.team_comparison", "Team Comparison")
        ])
        self.chart_type_selector.currentTextChanged.connect(self._update_chart)
        chart_selector_layout.addWidget(self.chart_type_selector)
        chart_selector_layout.addStretch()
        
        layout.addLayout(chart_selector_layout)
        
        # Chart widget
        self.chart_widget = PerformanceChartWidget()
        layout.addWidget(self.chart_widget)
        
        return widget
    
    def _update_chart(self):
        """Update chart based on selection"""
        chart_type = self.chart_type_selector.currentText()
        history = self.performance_controller.get_performance_history(self.technician.id, 12)
        selected_month = self.month_selector.currentData()
        
        try:
            if chart_type == "Tickets Trend":
                self.chart_widget.plot_tickets_trend(history)
            elif chart_type == "Revenue & Commission":
                self.chart_widget.plot_revenue_trend(history)
            elif chart_type == "Efficiency Metrics":
                self.chart_widget.plot_efficiency_trend(history)
            elif chart_type == "Compensation Breakdown":
                perf = self.performance_controller.get_performance(self.technician.id, selected_month)
                self.chart_widget.plot_compensation_breakdown(perf, self.technician.salary)
            elif chart_type == "Team Comparison":
                comparison = self.performance_controller.get_team_comparison(selected_month)
                self.chart_widget.plot_team_comparison(comparison)
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_generate_chart', 'Failed to generate chart')}: {str(e)}")
    
    def _export_to_csv(self):
        """Export performance data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.lm.get("Users.export_performance", "Export Performance Data"),
            f"performance_{self.technician.full_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                history = self.performance_controller.get_performance_history(self.technician.id, 12)
                ytd_summary = self.performance_controller.get_year_to_date_summary(self.technician.id)
                
                PerformanceExporter.export_to_csv(
                    self.technician,
                    history,
                    ytd_summary,
                    filename
                )
                
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), f"{self.lm.get('Users.export_success', 'Performance data exported to')}:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.export_failed', 'Failed to export')}: {str(e)}")
    
    def _generate_report(self):
        """Generate and save monthly performance report"""
        selected_month = self.month_selector.currentData()
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.lm.get("Users.save_report", "Save Performance Report"),
            f"report_{self.technician.full_name.replace(' ', '_')}_{selected_month.strftime('%Y%m')}.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                perf = self.performance_controller.get_performance(self.technician.id, selected_month)
                
                # Get bonuses for the month
                from models.technician_bonus import TechnicianBonus
                month_end = selected_month + relativedelta(months=1)
                bonuses = TechnicianBonus.select().where(
                    (TechnicianBonus.technician == self.technician.id) &
                    (TechnicianBonus.period_start >= selected_month) &
                    (TechnicianBonus.period_start < month_end)
                )
                
                report_text = PerformanceExporter.generate_monthly_report_text(
                    self.technician,
                    perf,
                    list(bonuses)
                )
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                
                QMessageBox.information(self, self.lm.get("Common.success", "Success"), f"{self.lm.get('Users.report_generated', 'Report generated')}:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Users.failed_generate_report', 'Failed to generate report')}: {str(e)}")

