# src/app/views/report/reports.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QLabel, QGroupBox, QTabWidget, QFrame,
                              QScrollArea, QGridLayout, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QCursor
from datetime import datetime, timedelta
from views.components.metric_card import MetricCard
import csv
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from core.event_bus import EventBus
from core.events import BranchContextChangedEvent

class ReportsTab(QWidget):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.ticket_service = container.ticket_service
        self.report_service = container.report_service
        self.lm = language_manager
        self.cf = currency_formatter
        self.current_branch_id = None
        self._setup_ui()
        EventBus.subscribe(BranchContextChangedEvent, self._handle_branch_changed)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        
        # Add Analytics tab
        analytics_tab = self._create_analytics_tab()
        self.tab_widget.addTab(analytics_tab, f"📊 {self.lm.get('Reports.analytics', 'Analytics')}")
        
        # Add Reports tab
        reports_tab = self._create_reports_tab()
        self.tab_widget.addTab(reports_tab, f"📄 {self.lm.get('Reports.reports', 'Reports')}")
        
        # Add Performance tab
        performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(performance_tab, f"🎯 {self.lm.get('Reports.performance', 'Performance')}")
        
        layout.addWidget(self.tab_widget)
        
    def _handle_branch_changed(self, event):
        self.current_branch_id = event.branch_id
        self._refresh_analytics()
        self._load_performance_data()
        # Also refresh current report preview if any
        if hasattr(self, 'generate_btn'):
            # Ideally trigger generation if auto-refresh is desired, or just let user click generate
            pass
    
    def _create_analytics_tab(self):
        """Create analytics tab matching main dashboard style"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header with date range selector
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("Reports.analytics_dashboard", "Analytics Dashboard"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Date range selector
        range_label = QLabel(f"{self.lm.get('Common.period', 'Period')}:")
        range_label.setObjectName("metricLabel")
        header_layout.addWidget(range_label)
        
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            self.lm.get("Common.today", "Today"),
            self.lm.get("Common.this_week", "This Week"),
            self.lm.get("Common.this_month", "This Month"),
            self.lm.get("Common.last_30_days", "Last 30 Days"),
            self.lm.get("Common.last_90_days", "Last 90 Days"),
            self.lm.get("Common.this_year", "This Year")
        ])
        self.date_range_combo.setCurrentIndex(2)  # Default to This Month
        self.date_range_combo.currentIndexChanged.connect(self._on_date_range_changed)
        header_layout.addWidget(self.date_range_combo)
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._refresh_analytics)
        refresh_btn.setStyleSheet("padding: 6px 12px;")
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Store current range
        self.analytics_range = 'month'
        today = datetime.now().date()
        self.analytics_start_date = today.replace(day=1)
        self.analytics_end_date = today
        
        # Metric cards in 2 rows layout
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(10)
        
        self.metric_cards = {}
        # Define metrics with different colors matching modern dashboard
        # Layout: Row 1 has 4 cards, Row 2 has 4 cards (total 8 cards in 2 rows)
        metrics = [
            # Row 1 - Main metrics (4 cards)
            ("total_tickets", "📋", "0", self.lm.get("Reports.total_tickets", "Total Tickets"), "↑ 0%", "#3B82F6", 0, 0),  # Blue
            ("completed", "✅", "0", self.lm.get("Reports.completed", "Completed"), "↑ 0%", "#10B981", 0, 1),  # Green
            ("revenue", "💰", self.cf.format(0), self.lm.get("Reports.revenue", "Revenue"), "↑ 0%", "#8B5CF6", 0, 2),  # Purple
            ("avg_time", "⏱️", "0h", self.lm.get("Reports.avg_time", "Avg Time"), "→ 0%", "#F59E0B", 0, 3),  # Orange
            # Row 2 - Status metrics (4 cards)
            ("pending", "⏳", "0", self.lm.get("Reports.pending", "Pending"), None, "#6366F1", 1, 0),  # Indigo
            ("in_progress", "🔧", "0", self.lm.get("Reports.in_progress", "In Progress"), None, "#14B8A6", 1, 1),  # Teal
            ("cancelled", "❌", "0", self.lm.get("Reports.cancelled", "Cancelled"), None, "#EF4444", 1, 2),  # Red
            ("avg_revenue", "💵", self.cf.format(0), self.lm.get("Reports.avg_revenue_ticket", "Avg Revenue/Ticket"), None, "#EC4899", 1, 3),  # Pink
        ]
        
        for key, icon, value, label, growth, color, row, col in metrics:
            card = MetricCard(icon, value, label, growth, color)
            card.setFixedHeight(100)  # Limit card height to 100px
            self.metric_cards[key] = card
            self.metrics_layout.addWidget(card, row, col)
        
        main_layout.addLayout(self.metrics_layout)
        
        # Charts and stats row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(10)
        
        # Left column - Charts
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        try:
            from views.components.dashboard_charts import StatusDistributionChart
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            
            # Status chart
            status_container = self._create_chart_container(self.lm.get("Reports.status_distribution", "Status Distribution"))
            status_layout = status_container.layout()
            self.status_chart = StatusDistributionChart()
            self.status_chart.setMinimumHeight(300)
            status_layout.addWidget(self.status_chart)
            left_column.addWidget(status_container)
            
            # Revenue chart - Simple design like modern dashboard
            revenue_container = self._create_chart_container(self.lm.get("Reports.revenue_trend", "Revenue Trend"))
            revenue_layout = revenue_container.layout()
            
            # Create matplotlib figure
            self.revenue_figure = Figure(figsize=(10, 4), facecolor='none')
            self.revenue_canvas = FigureCanvas(self.revenue_figure)
            self.revenue_canvas.setStyleSheet("background-color: transparent;")
            self.revenue_canvas.setMinimumHeight(300)
            revenue_layout.addWidget(self.revenue_canvas)
            left_column.addWidget(revenue_container)
            
            self.charts_enabled = True
            
        except ImportError:
            error_container = QFrame()
            error_container.setObjectName("cardFrame")
            error_layout = QVBoxLayout(error_container)
            error_layout.setContentsMargins(40, 40, 40, 40)
            
            error_icon = QLabel("📊")
            error_icon.setStyleSheet("font-size: 48px;")
            error_icon.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_icon)
            
            error_label = QLabel(self.lm.get("Reports.charts_unavailable", "Charts Unavailable"))
            error_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            
            error_desc = QLabel(self.lm.get("Reports.matplotlib_required", "Matplotlib is required for visualizations.\\nInstall it with: pip install matplotlib"))
            error_desc.setObjectName("metricLabel")
            error_desc.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_desc)
            
            left_column.addWidget(error_container)
            self.charts_enabled = False
        
        # Right column - Stats and Activity
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Top Technicians card
        tech_card = self._create_top_technicians_card()
        right_column.addWidget(tech_card)
        
        # Quick Stats card
        stats_card = self._create_quick_stats_card()
        right_column.addWidget(stats_card)
        
        # Add columns to layout
        charts_layout.addLayout(left_column, 2)
        charts_layout.addLayout(right_column, 1)
        
        main_layout.addLayout(charts_layout)
        main_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Load initial data
        self._refresh_analytics()
        
        return scroll
    
    def _create_chart_container(self, title):
        """Create a container for charts matching dashboard style"""
        container = QFrame()
        container.setObjectName("cardFrame")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        return container
    
    def _create_top_technicians_card(self):
        """Create top technicians performance card"""
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title = QLabel(f"🏆 {self.lm.get('Reports.top_technicians', 'Top Technicians')}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Technicians list
        self.tech_list_layout = QVBoxLayout()
        self.tech_list_layout.setSpacing(8)
        layout.addLayout(self.tech_list_layout)
        
        layout.addStretch()
        
        return card
    
    def _create_quick_stats_card(self):
        """Create quick stats breakdown card"""
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title = QLabel(f"📈 {self.lm.get('Reports.quick_stats', 'Quick Stats')}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Stats list
        self.stats_list_layout = QVBoxLayout()
        self.stats_list_layout.setSpacing(6)
        layout.addLayout(self.stats_list_layout)
        
        layout.addStretch()
        
        return card
    
    def _add_technician_row(self, rank, name, tickets, revenue):
        """Add a technician performance row"""
        row = QHBoxLayout()
        
        # Rank badge
        rank_label = QLabel(f"#{rank}")
        rank_label.setStyleSheet("""
            background-color: #3B82F6;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        """)
        rank_label.setFixedWidth(35)
        rank_label.setAlignment(Qt.AlignCenter)
        row.addWidget(rank_label)
        
        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: 600;")
        row.addWidget(name_label)
        
        row.addStretch()
        
        # Stats
        stats_label = QLabel(f"{tickets} tickets • {self.cf.format(revenue)}")
        stats_label.setObjectName("metricLabel")
        row.addWidget(stats_label)
        
        self.tech_list_layout.addLayout(row)
    
    def _add_stat_row(self, label, value, color="#3B82F6"):
        """Add a quick stat row"""
        row = QHBoxLayout()
        
        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("metricLabel")
        row.addWidget(label_widget)
        
        row.addStretch()
        
        # Value
        value_widget = QLabel(str(value))
        value_widget.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")
        row.addWidget(value_widget)
        
        self.stats_list_layout.addLayout(row)
    
    def _on_date_range_changed(self, index):
        """Handle date range selection change"""
        today = datetime.now().date()
        
        if index == 0:  # Today
            self.analytics_start_date = today
            self.analytics_end_date = today
        elif index == 1:  # This Week
            self.analytics_start_date = today - timedelta(days=today.weekday())
            self.analytics_end_date = today
        elif index == 2:  # This Month
            self.analytics_start_date = today.replace(day=1)
            self.analytics_end_date = today
        elif index == 3:  # Last 30 Days
            self.analytics_start_date = today - timedelta(days=30)
            self.analytics_end_date = today
        elif index == 4:  # Last 90 Days
            self.analytics_start_date = today - timedelta(days=90)
            self.analytics_end_date = today
        elif index == 5:  # This Year
            self.analytics_start_date = today.replace(month=1, day=1)
            self.analytics_end_date = today
        
        self._refresh_analytics()
    
    def _refresh_analytics(self):
        """Refresh analytics charts and metrics"""
        if not self.charts_enabled:
            return
        
        # Get stats
        stats = self.ticket_service.get_dashboard_stats_range(
            self.analytics_start_date, self.analytics_end_date,
            branch_id=self.current_branch_id
        )
        avg_time = self.ticket_service.get_average_completion_time(
            self.analytics_start_date, self.analytics_end_date,
            branch_id=self.current_branch_id
        )
        
        # Calculate growth (compare with previous period)
        period_days = (self.analytics_end_date - self.analytics_start_date).days + 1
        prev_start = self.analytics_start_date - timedelta(days=period_days)
        prev_end = self.analytics_start_date - timedelta(days=1)
        
        prev_stats = self.ticket_service.get_dashboard_stats_range(prev_start, prev_end, branch_id=self.current_branch_id)
        
        # Calculate growth percentages
        total_growth = self._calculate_growth(stats['total_tickets'], prev_stats['total_tickets'])
        completed_growth = self._calculate_growth(stats['completed'], prev_stats['completed'])
        revenue_growth = self._calculate_growth(stats['revenue'], prev_stats['revenue'])
        
        # Update metric cards
        self.metric_cards["total_tickets"].update_value(str(stats['total_tickets']))
        self.metric_cards["total_tickets"].update_growth(total_growth)
        
        self.metric_cards["completed"].update_value(str(stats['completed']))
        self.metric_cards["completed"].update_growth(completed_growth)
        
        self.metric_cards["revenue"].update_value(self.cf.format(stats['revenue']))
        self.metric_cards["revenue"].update_growth(revenue_growth)
        
        self.metric_cards["avg_time"].update_value(f"{avg_time:.1f}h")
        
        # Update additional metrics
        pending = stats['total_tickets'] - stats['completed']
        self.metric_cards["pending"].update_value(str(pending))
        
        # Get status distribution for in_progress and cancelled
        status_dist = self.ticket_service.get_status_distribution(
            self.analytics_start_date, self.analytics_end_date,
            branch_id=self.current_branch_id
        )
        
        in_progress = status_dist.get('in_progress', 0)
        cancelled = status_dist.get('cancelled', 0)
        
        self.metric_cards["in_progress"].update_value(str(in_progress))
        self.metric_cards["cancelled"].update_value(str(cancelled))
        
        # Average revenue per ticket
        avg_revenue = stats['revenue'] / stats['total_tickets'] if stats['total_tickets'] > 0 else 0
        self.metric_cards["avg_revenue"].update_value(self.cf.format(avg_revenue))
        
        # Update charts
        self.status_chart.update_chart(status_dist)
        
        # Update revenue chart - Simple design like modern dashboard
        revenue_trend = self.ticket_service.get_revenue_trend(
            self.analytics_start_date, self.analytics_end_date,
            branch_id=self.current_branch_id
        )
        self._update_revenue_chart(revenue_trend)
        
        # Update top technicians
        self._update_top_technicians()
        
        # Update quick stats
        self._update_quick_stats(stats, status_dist)
    
    def _update_revenue_chart(self, trend_data):
        """Update revenue trend chart with simple design"""
        import matplotlib.pyplot as plt
        from datetime import timedelta
        
        # Clear and setup chart
        self.revenue_figure.clear()
        ax = self.revenue_figure.add_subplot(111)
        
        # Make background transparent
        self.revenue_figure.patch.set_alpha(0)
        ax.patch.set_alpha(0)
        
        # Get theme-aware colors
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        palette = QApplication.palette()
        is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        text_color = '#9CA3AF' if is_dark else '#6B7280'
        grid_color = '#374151' if is_dark else '#E5E7EB'
        bg_color = '#1F2937' if is_dark else '#F9FAFB'
        
        # Convert to dictionary for easy lookup
        trend_map = {item['date']: item['revenue'] for item in trend_data}
        
        days = []
        revenues = []
        
        # Calculate number of days
        delta = (self.analytics_end_date - self.analytics_start_date).days
        
        # Determine grouping strategy
        if delta <= 7:
            # Daily view
            date_format = "%a"  # Mon, Tue
            
            for i in range(delta + 1):
                day = self.analytics_start_date + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                
                days.append(day.strftime(date_format))
                revenues.append(trend_map.get(day_str, 0.0))
        else:
            # Weekly grouping
            weekly_data = {}
            week_order = []
            
            for i in range(delta + 1):
                day = self.analytics_start_date + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                revenue = trend_map.get(day_str, 0.0)
                
                # Get week start date (Monday)
                week_start = day - timedelta(days=day.weekday())
                week_label = week_start.strftime("%b %d")
                
                if week_label not in weekly_data:
                    weekly_data[week_label] = 0.0
                    week_order.append(week_label)
                
                weekly_data[week_label] += revenue
            
            days = week_order
            revenues = [weekly_data[lbl] for lbl in days]
        
        # Plot line chart with red color like the modern dashboard
        if revenues:
            ax.plot(days, revenues, color='#EF4444', linewidth=2.5, marker='o', 
                   markersize=4, markerfacecolor='#EF4444', markeredgecolor='#EF4444')
            
            # Add average line (dotted)
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            ax.axhline(y=avg_revenue, color='#EF4444', linestyle='--', 
                      linewidth=1, alpha=0.5)
        
        # Styling - match modern dashboard
        ax.set_facecolor(bg_color)
        ax.set_ylim(bottom=0)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(grid_color)
        ax.spines['bottom'].set_color(grid_color)
        
        # Grid styling - match modern dashboard with dashed lines
        ax.grid(True, alpha=0.3, color=grid_color, linestyle='--', linewidth=0.8)
        ax.set_axisbelow(True)  # Grid behind data
        
        # Tick styling
        ax.tick_params(colors=text_color, labelsize=9)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: self.cf.format(x)))
        
        self.revenue_figure.tight_layout()
        self.revenue_canvas.draw()
    
    def _calculate_growth(self, current, previous):
        """Calculate growth percentage"""
        if previous == 0:
            return "→ N/A" if current == 0 else "↑ New"
        
        growth = ((current - previous) / previous) * 100
        
        if growth > 0:
            return f"↑ {growth:.1f}%"
        elif growth < 0:
            return f"↓ {abs(growth):.1f}%"
        else:
            return "→ 0%"
    
    def _update_top_technicians(self):
        """Update top technicians list"""
        # Clear existing
        while self.tech_list_layout.count():
            child = self.tech_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        
        # Get technician performance
        tech_performance = self.ticket_service.get_technician_performance(
            self.analytics_start_date, self.analytics_end_date,
            branch_id=self.current_branch_id
        )
        
        # Add top 5
        for idx, tech in enumerate(tech_performance[:5], 1):
            self._add_technician_row(
                idx,
                tech.get('technician_name', 'Unknown'),
                tech.get('tickets_completed', 0),
                tech.get('total_revenue', 0)
            )
        
        if not tech_performance:
            no_data = QLabel(self.lm.get("Reports.no_data", "No data available"))
            no_data.setObjectName("metricLabel")
            no_data.setAlignment(Qt.AlignCenter)
            self.tech_list_layout.addWidget(no_data)
    
    def _update_quick_stats(self, stats, status_dist):
        """Update quick stats list"""
        # Clear existing
        while self.stats_list_layout.count():
            child = self.stats_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        
        # Add stats
        completion_rate = (stats['completed'] / stats['total_tickets'] * 100) if stats['total_tickets'] > 0 else 0
        self._add_stat_row(self.lm.get("Reports.completion_rate", "Completion Rate"), f"{completion_rate:.1f}%", "#10B981")
        
        open_tickets = status_dist.get('open', 0)
        self._add_stat_row(self.lm.get("Reports.open_tickets", "Open Tickets"), open_tickets, "#F59E0B")
        
        diagnosed = status_dist.get('diagnosed', 0)
        self._add_stat_row(self.lm.get("Reports.diagnosed", "Diagnosed"), diagnosed, "#3B82F6")
        
        awaiting_parts = status_dist.get('awaiting_parts', 0)
        self._add_stat_row(self.lm.get("Reports.awaiting_parts", "Awaiting Parts"), awaiting_parts, "#8B5CF6")
        
        unrepairable = status_dist.get('unrepairable', 0)
        self._add_stat_row(self.lm.get("Reports.unrepairable", "Unrepairable"), unrepairable, "#EF4444")
    
    def _clear_layout(self, layout):
        """Clear all items from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
    
    def _create_performance_tab(self):
        """Create performance analysis tab"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(self.lm.get("Reports.technician_performance", "Technician Performance"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Technician Performance Table
        perf_card = QFrame()
        perf_card.setObjectName("cardFrame")
        perf_layout = QVBoxLayout(perf_card)
        perf_layout.setSpacing(8)
        perf_layout.setContentsMargins(12, 12, 12, 12)
        
        perf_title = QLabel(self.lm.get("Reports.technician_performance", "Technician Performance"))
        perf_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        perf_layout.addWidget(perf_title)
        
        self.perf_table = QTableWidget()
        self.perf_table.setColumnCount(6)
        self.perf_table.setHorizontalHeaderLabels([
            self.lm.get("Reports.technician", "Technician"),
            self.lm.get("Reports.tickets_completed", "Tickets Completed"),
            self.lm.get("Reports.avg_time_hrs", "Avg Time (hrs)"),
            self.lm.get("Reports.revenue_generated", "Revenue Generated"),
            self.lm.get("Reports.success_rate", "Success Rate"),
            self.lm.get("Reports.rating", "Rating")
        ])
        self.perf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.perf_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.perf_table.setAlternatingRowColors(True)
        self.perf_table.setObjectName("reportTable")
        
        perf_layout.addWidget(self.perf_table)
        main_layout.addWidget(perf_card)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Load performance data
        self._load_performance_data()
        
        return scroll
    
    def _load_performance_data(self):
        """Load technician performance data"""
        try:
            tech_performance = self.ticket_service.get_technician_performance(
                datetime.now().date() - timedelta(days=30),
                datetime.now().date(),
                branch_id=self.current_branch_id
            )
            
            self.perf_table.setRowCount(len(tech_performance))
            
            for row, tech in enumerate(tech_performance):
                # Technician name
                self.perf_table.setItem(row, 0, QTableWidgetItem(tech.get('technician_name', 'Unknown')))
                
                # Tickets completed
                self.perf_table.setItem(row, 1, QTableWidgetItem(str(tech.get('tickets_completed', 0))))
                
                # Avg time
                avg_time = tech.get('avg_completion_time', 0)
                self.perf_table.setItem(row, 2, QTableWidgetItem(f"{avg_time:.1f}"))
                
                # Revenue
                revenue = tech.get('total_revenue', 0)
                self.perf_table.setItem(row, 3, QTableWidgetItem(self.cf.format(revenue)))
                
                # Success rate
                success_rate = tech.get('success_rate', 0)
                self.perf_table.setItem(row, 4, QTableWidgetItem(f"{success_rate:.1f}%"))
                
                # Rating (placeholder)
                self.perf_table.setItem(row, 5, QTableWidgetItem("⭐⭐⭐⭐⭐"))
                
        except Exception as e:
            print(f"Error loading performance data: {e}")
    
    def _create_reports_tab(self):
        """Create reports tab with clean design"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(self.lm.get("Reports.reports", "Reports"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Report controls card
        controls_card = QFrame()
        controls_card.setObjectName("cardFrame")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        
        # Report type selection
        type_layout = QHBoxLayout()
        type_label = QLabel(f"{self.lm.get('Reports.report_type', 'Report Type')}:")
        type_label.setObjectName("metricLabel")
        type_label.setStyleSheet("font-weight: 600;")
        type_layout.addWidget(type_label)
        
        self.report_type = QComboBox()
        self.report_type.addItems([
            # Phase 1 Reports
            self.lm.get("Reports.daily_ticket_summary", "Daily Ticket Summary"),
            self.lm.get("Reports.technician_performance", "Technician Performance"),
            self.lm.get("Reports.revenue_summary", "Revenue Summary"),
            self.lm.get("Reports.invoice_report", "Invoice Report"),
            self.lm.get("Reports.stock_level_report", "Stock Level Report"),
            # Phase 2 Reports
            self.lm.get("Reports.customer_activity", "Customer Activity"),
            self.lm.get("Reports.work_log_summary", "Work Log Summary"),
            self.lm.get("Reports.inventory_movement", "Inventory Movement"),
            self.lm.get("Reports.supplier_performance", "Supplier Performance"),
            self.lm.get("Reports.outstanding_payments", "Outstanding Payments")
        ])
        self.report_type.currentIndexChanged.connect(self._on_report_type_changed)
        type_layout.addWidget(self.report_type, 1)
        controls_layout.addLayout(type_layout)
        
        # Date range selection
        date_layout = QHBoxLayout()
        date_label = QLabel(f"{self.lm.get('Reports.date_range', 'Date Range')}:")
        date_label.setObjectName("metricLabel")
        date_label.setStyleSheet("font-weight: 600;")
        date_layout.addWidget(date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel(self.lm.get("Reports.to", "to")))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        date_layout.addStretch()
        controls_layout.addLayout(date_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton(f"📊 {self.lm.get('Reports.generate_report', 'Generate Report')}")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.generate_btn.clicked.connect(self._generate_report)
        btn_layout.addWidget(self.generate_btn)
        
        self.export_pdf_btn = QPushButton(f"📄 {self.lm.get('Reports.export_pdf', 'Export PDF')}")
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        btn_layout.addWidget(self.export_pdf_btn)
        
        self.export_csv_btn = QPushButton(f"📊 {self.lm.get('Reports.export_csv', 'Export CSV')}")
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.export_csv_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(self.export_csv_btn)
        
        btn_layout.addStretch()
        controls_layout.addLayout(btn_layout)
        
        main_layout.addWidget(controls_card)
        
        # Report display card
        report_card = QFrame()
        report_card.setObjectName("cardFrame")
        report_layout = QVBoxLayout(report_card)
        report_layout.setSpacing(8)
        report_layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        report_title = QLabel(self.lm.get("Reports.report_preview", "Report Preview"))
        report_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        report_layout.addWidget(report_title)
        
        # Table
        self.report_display = QTableWidget()
        self.report_display.setColumnCount(6)
        self.report_display.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_display.setEditTriggers(QTableWidget.NoEditTriggers)
        self.report_display.setAlternatingRowColors(True)
        self.report_display.setObjectName("reportTable")
        
        # Initialize with first report type headers
        self._on_report_type_changed(0)
        
        report_layout.addWidget(self.report_display)
        main_layout.addWidget(report_card)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        return scroll
    
    def _on_report_type_changed(self, index):
        """Handle report type change"""
        # Update table headers based on report type
        report_types = {
            # Phase 1
            0: [
                self.lm.get("Reports.date", "Date"),
                self.lm.get("Reports.new_tickets", "New Tickets"),
                self.lm.get("Reports.completed", "Completed"),
                self.lm.get("Reports.in_progress", "In Progress"),
                self.lm.get("Reports.revenue", "Revenue"),
                self.lm.get("Reports.parts_used", "Parts Used")
            ],
            1: [
                self.lm.get("Reports.technician", "Technician"),
                self.lm.get("Reports.total_tickets_col", "Total Tickets"),
                self.lm.get("Reports.completed", "Completed"),
                self.lm.get("Reports.avg_time_hrs", "Avg Time (hrs)"),
                self.lm.get("Reports.revenue", "Revenue"),
                self.lm.get("Reports.success_rate", "Success Rate"),
                self.lm.get("Reports.estimated_bonus", "Est. Bonus")
            ],
            2: [
                self.lm.get("Reports.metric", "Metric"),
                self.lm.get("Reports.value", "Value"),
                "", "", "", ""
            ],
            3: [
                self.lm.get("Reports.invoice_num", "Invoice #"),
                self.lm.get("Reports.customer", "Customer"),
                self.lm.get("Reports.amount", "Amount"),
                self.lm.get("Reports.status", "Status"),
                self.lm.get("Reports.due_date", "Due Date"),
                self.lm.get("Reports.days_overdue", "Days Overdue")
            ],
            4: [
                self.lm.get("Reports.sku", "SKU"),
                self.lm.get("Reports.part_name", "Part Name"),
                self.lm.get("Reports.quantity", "Quantity"),
                self.lm.get("Reports.min_stock", "Min Stock"),
                self.lm.get("Reports.status", "Status"),
                self.lm.get("Reports.total_value", "Total Value")
            ],
            # Phase 2
            5: [
                self.lm.get("Reports.customer", "Customer"),
                self.lm.get("Reports.total_tickets_col", "Total Tickets"),
                self.lm.get("Reports.total_spent", "Total Spent"),
                self.lm.get("Reports.last_visit", "Last Visit"),
                self.lm.get("Reports.status", "Status"),
                self.lm.get("Reports.avg_value", "Avg Value")
            ],
            6: [
                self.lm.get("Reports.technician", "Technician"),
                self.lm.get("Reports.sessions", "Sessions"),
                self.lm.get("Reports.total_hours", "Total Hours"),
                self.lm.get("Reports.avg_ticket", "Avg/Ticket"),
                self.lm.get("Reports.billable", "Billable"),
                self.lm.get("Reports.efficiency", "Efficiency")
            ],
            7: [
                self.lm.get("Reports.part", "Part"),
                self.lm.get("Reports.stock_in", "Stock In"),
                self.lm.get("Reports.stock_out", "Stock Out"),
                self.lm.get("Reports.current", "Current"),
                self.lm.get("Reports.net_change", "Net Change"),
                self.lm.get("Reports.value", "Value")
            ],
            8: [
                self.lm.get("Reports.supplier", "Supplier"),
                self.lm.get("Reports.orders", "Orders"),
                self.lm.get("Reports.total_value", "Total Value"),
                self.lm.get("Reports.avg_delivery", "Avg Delivery"),
                self.lm.get("Reports.on_time_pct", "On-Time %"),
                self.lm.get("Reports.issues", "Issues")
            ],
            9: [
                self.lm.get("Reports.invoice_num", "Invoice #"),
                self.lm.get("Reports.customer", "Customer"),
                self.lm.get("Reports.amount_due", "Amount Due"),
                self.lm.get("Reports.due_date", "Due Date"),
                self.lm.get("Reports.days_overdue", "Days Overdue"),
                self.lm.get("Reports.aging", "Aging")
            ]
        }
        
        headers = report_types.get(index, ["Col 1", "Col 2", "Col 3", "Col 4", "Col 5", "Col 6"])
        self.report_display.setColumnCount(len(headers))
        self.report_display.setHorizontalHeaderLabels(headers)
    
    def _generate_report(self):
        """Generate the selected report with real data"""
        report_type = self.report_type.currentText()
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        try:
            # Phase 1 Reports
            if report_type == self.lm.get("Reports.daily_ticket_summary", "Daily Ticket Summary"):
                self._display_daily_ticket_summary(start_date, end_date)
            elif report_type == self.lm.get("Reports.technician_performance", "Technician Performance"):
                self._display_technician_performance(start_date, end_date)
            elif report_type == self.lm.get("Reports.revenue_summary", "Revenue Summary"):
                self._display_revenue_summary(start_date, end_date)
            elif report_type == self.lm.get("Reports.invoice_report", "Invoice Report"):
                self._display_invoice_report(start_date, end_date)
            elif report_type == self.lm.get("Reports.stock_level_report", "Stock Level Report"):
                self._display_stock_level_report()
            # Phase 2 Reports
            elif report_type == self.lm.get("Reports.customer_activity", "Customer Activity"):
                self._display_customer_activity(start_date, end_date)
            elif report_type == self.lm.get("Reports.work_log_summary", "Work Log Summary"):
                self._display_work_log_summary(start_date, end_date)
            elif report_type == self.lm.get("Reports.inventory_movement", "Inventory Movement"):
                self._display_inventory_movement(start_date, end_date)
            elif report_type == self.lm.get("Reports.supplier_performance", "Supplier Performance"):
                self._display_supplier_performance(start_date, end_date)
            elif report_type == self.lm.get("Reports.outstanding_payments", "Outstanding Payments"):
                self._display_outstanding_payments()
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"Failed to generate report:\\n{str(e)}")
    
    def _display_daily_ticket_summary(self, start_date, end_date):
        """Display daily ticket summary report"""
        data = self.report_service.get_daily_ticket_summary(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['date']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['new_tickets'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(str(item['completed'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(str(item['in_progress'])))
            self.report_display.setItem(row, 4, QTableWidgetItem(self.cf.format(item['total_revenue'])))
            self.report_display.setItem(row, 5, QTableWidgetItem(str(item['parts_used'])))    
    def _display_technician_performance(self, start_date, end_date):
        """Display technician performance report"""
        data = self.report_service.get_technician_performance(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['technician_name']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['total_tickets'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(str(item['tickets_completed'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(f"{item['avg_completion_time']:.1f}"))
            self.report_display.setItem(row, 4, QTableWidgetItem(self.cf.format(item['total_revenue'])))
            self.report_display.setItem(row, 5, QTableWidgetItem(f"{item['success_rate']:.1f}%"))
            self.report_display.setItem(row, 6, QTableWidgetItem(self.cf.format(item.get('estimated_bonus', 0))))
    
    def _display_revenue_summary(self, start_date, end_date):
        """Display revenue summary report"""
        data = self.report_service.get_revenue_summary(start_date, end_date, branch_id=self.current_branch_id)
        
        # Display as key-value pairs
        summary_items = [
            ('Total Revenue', self.cf.format(data['total_revenue'])),
            ('Total Cost (Parts)', self.cf.format(data.get('total_cost', 0))),
            ('Gross Profit', self.cf.format(data.get('gross_profit', 0))),
            ('Profit Margin', f"{data.get('profit_margin', 0):.1f}%"),
            ('Ticket Count', str(data['ticket_count'])),
            ('Avg Revenue/Ticket', self.cf.format(data['avg_revenue_per_ticket'])),
            ('Previous Period', self.cf.format(data['previous_period_revenue'])),
            ('Growth', f"{data['growth_percentage']:.1f}%"),
        ]
        
        self.report_display.setRowCount(len(summary_items))
        
        for row, (metric, value) in enumerate(summary_items):
            self.report_display.setItem(row, 0, QTableWidgetItem(metric))
            self.report_display.setItem(row, 1, QTableWidgetItem(value))
    
    def _display_invoice_report(self, start_date, end_date):
        """Display invoice report"""
        data = self.report_service.get_invoice_report(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['invoice_number']))
            self.report_display.setItem(row, 1, QTableWidgetItem(item['customer_name']))
            self.report_display.setItem(row, 2, QTableWidgetItem(self.cf.format(item['total_amount'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(item['status']))
            self.report_display.setItem(row, 4, QTableWidgetItem(item['due_date']))
            self.report_display.setItem(row, 5, QTableWidgetItem(str(item['days_overdue'])))
    
    def _display_stock_level_report(self):
        """Display stock level report"""
        data = self.report_service.get_stock_level_report(branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['sku']))
            self.report_display.setItem(row, 1, QTableWidgetItem(item['name']))
            self.report_display.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(str(item['min_stock_level'])))
            self.report_display.setItem(row, 4, QTableWidgetItem(item['status']))
            self.report_display.setItem(row, 5, QTableWidgetItem(self.cf.format(item['total_value'])))
    
    def _display_customer_activity(self, start_date, end_date):
        """Display customer activity report"""
        data = self.report_service.get_customer_activity(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['customer_name']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['total_tickets'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(self.cf.format(item['total_spent'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(item['last_visit']))
            self.report_display.setItem(row, 4, QTableWidgetItem(item['status']))
            self.report_display.setItem(row, 5, QTableWidgetItem(self.cf.format(item['avg_value'])))
    
    def _display_work_log_summary(self, start_date, end_date):
        """Display work log summary report"""
        data = self.report_service.get_work_log_summary(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['technician_name']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['sessions'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(f"{item['total_hours']:.1f}"))
            self.report_display.setItem(row, 3, QTableWidgetItem(f"{item['avg_per_ticket']:.1f}"))
            self.report_display.setItem(row, 4, QTableWidgetItem(f"{item['billable_hours']:.1f}"))
            self.report_display.setItem(row, 5, QTableWidgetItem(item['efficiency']))
    
    def _display_inventory_movement(self, start_date, end_date):
        """Display inventory movement report"""
        data = self.report_service.get_inventory_movement(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['part_name']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['stock_in'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(str(item['stock_out'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(str(item['current_stock'])))
            self.report_display.setItem(row, 4, QTableWidgetItem(str(item['net_change'])))
            self.report_display.setItem(row, 5, QTableWidgetItem(self.cf.format(item['movement_value'])))
    
    def _display_supplier_performance(self, start_date, end_date):
        """Display supplier performance report"""
        data = self.report_service.get_supplier_performance(start_date, end_date, branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['supplier_name']))
            self.report_display.setItem(row, 1, QTableWidgetItem(str(item['total_orders'])))
            self.report_display.setItem(row, 2, QTableWidgetItem(self.cf.format(item['total_value'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(f"{item['avg_delivery_days']:.1f}"))
            self.report_display.setItem(row, 4, QTableWidgetItem(f"{item['on_time_rate']:.1f}%"))
            self.report_display.setItem(row, 5, QTableWidgetItem(str(item['quality_issues'])))
    
    def _display_outstanding_payments(self):
        """Display outstanding payments report"""
        data = self.report_service.get_outstanding_payments(branch_id=self.current_branch_id)
        
        self.report_display.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.report_display.setItem(row, 0, QTableWidgetItem(item['invoice_number']))
            self.report_display.setItem(row, 1, QTableWidgetItem(item['customer_name']))
            self.report_display.setItem(row, 2, QTableWidgetItem(self.cf.format(item['amount_due'])))
            self.report_display.setItem(row, 3, QTableWidgetItem(item['due_date']))
            self.report_display.setItem(row, 4, QTableWidgetItem(str(item['days_overdue'])))
            self.report_display.setItem(row, 5, QTableWidgetItem(item['aging_bucket']))
    
    def _export_pdf(self):
        """Export current report to PDF"""
        QMessageBox.information(self, self.lm.get("Common.info", "Info"), "PDF export functionality coming soon!")
    
    def _export_csv(self):
        """Export current report to CSV"""
        if self.report_display.rowCount() == 0:
            QMessageBox.warning(self, self.lm.get("Common.warning", "Warning"), "No data to export. Please generate a report first.")
            return
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.lm.get("Reports.export_csv", "Export CSV"),
            "",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = []
                for col in range(self.report_display.columnCount()):
                    headers.append(self.report_display.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.report_display.rowCount()):
                    row_data = []
                    for col in range(self.report_display.columnCount()):
                        item = self.report_display.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), f"Report exported successfully to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"Failed to export CSV:\n{str(e)}")
