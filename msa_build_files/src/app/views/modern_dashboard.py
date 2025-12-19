# src/app/views/modern_dashboard.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QScrollArea, QGridLayout, QPushButton,
                              QComboBox, QDateEdit)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QCursor
from views.components.metric_card import MetricCard
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('QtAgg')  # Use Qt6-compatible backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter
from core.event_bus import EventBus
from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
    TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent,
    InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent,
    CustomerCreatedEvent, CustomerUpdatedEvent, CustomerDeletedEvent,
    TechnicianCreatedEvent, TechnicianUpdatedEvent, TechnicianDeactivatedEvent,
    BranchContextChangedEvent
)

class ModernDashboardTab(QWidget):
    """Modern analytics dashboard with clean card-based design"""
    
    def __init__(
        self,
        ticket_service,
        ticket_controller,
        customer_controller,
        technician_controller,
        repair_part_controller,
        work_log_controller,
        business_settings_service,
        part_service,
        technician_repository,
        user,
        container=None
    ):
        """
        Initialize the dashboard tab.
        
        Args:
            ticket_service: Service for ticket operations
            ticket_controller: Controller for ticket actions
            customer_controller: Controller for customer actions
            technician_controller: Controller for technician actions
            repair_part_controller: Controller for repair parts
            work_log_controller: Controller for work logs
            business_settings_service: Service for business settings
            part_service: Service for parts
            technician_repository: Repository for technicians
            user: Current user
            container: Legacy dependency container (optional)
        """
        super().__init__()
        self.container = container
        self.user = user
        
        # Explicit dependencies
        self.ticket_service = ticket_service
        self.ticket_controller = ticket_controller
        self.customer_controller = customer_controller
        self.technician_controller = technician_controller
        self.repair_part_controller = repair_part_controller
        self.work_log_controller = work_log_controller
        self.business_settings_service = business_settings_service
        self.part_service = part_service
        self.technician_repository = technician_repository
        
        self.lm = language_manager
        self.cf = currency_formatter
        
        # Default date range (last 30 days)
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=30)

        
        self.current_branch_id = None
        
        self._setup_ui()
        self._subscribe_to_events()
        
        # Flag to track if data has been loaded
        self._data_loaded = False
        
        # We don't load data here anymore. 
        # It will be loaded in showEvent calling refresh_data()
        # self.refresh_data()
    
    def _setup_ui(self):
        """Setup the modern dashboard UI"""
        # Main scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(10)  # Reduced from 14
        main_layout.setContentsMargins(12, 12, 12, 12)  # Reduced from 14
        
        # Header with date range selector
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)
        
        # Quick actions row
        actions_layout = self._create_quick_actions()
        main_layout.addLayout(actions_layout)
        
        # Metric cards row
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(12)
        main_layout.addLayout(self.metrics_layout)
        
        # Chart row - Revenue chart and Status breakdown side by side
        chart_row = QHBoxLayout()
        chart_row.setSpacing(10)  # Reduced from 12
        
        # Left column - Revenue chart above Recent tickets
        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        chart_card = self._create_revenue_chart_card()
        left_column.addWidget(chart_card)
        recent_tickets_card = self._create_recent_tickets_card()
        left_column.addWidget(recent_tickets_card)
        
        # Right column - Status breakdown above Top Technicians
        right_column = QVBoxLayout()
        right_column.setSpacing(12)
        quick_stats_card = self._create_quick_stats_card()
        right_column.addWidget(quick_stats_card)
        tech_perf_card = self._create_technician_performance_card()
        right_column.addWidget(tech_perf_card)
        
        # Add both columns to the row
        chart_row.addLayout(left_column, 1)
        chart_row.addLayout(right_column, 1)
        
        main_layout.addLayout(chart_row)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Set scroll area as main layout
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
    
    def _create_header(self):
        """Create dashboard header with date range selector"""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("Dashboard.dashboard_title", "Analytics Overview"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Date range selector
        range_label = QLabel(f"{self.lm.get('Common.period', 'Period')}:")
        range_label.setObjectName("metricLabel")
        layout.addWidget(range_label)
        
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            self.lm.get("Common.last_7_days", "Last 7 Days"),
            self.lm.get("Common.last_30_days", "Last 30 Days"),
            self.lm.get("Common.last_90_days", "Last 90 Days"),
            self.lm.get("Common.this_month", "This Month"),
            self.lm.get("Common.this_year", "This Year")
        ])
        self.date_range_combo.setCurrentIndex(1)  # Default to Last 30 Days
        self.date_range_combo.currentIndexChanged.connect(self._on_date_range_changed)
        layout.addWidget(self.date_range_combo)
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet("padding: 6px 12px;")
        layout.addWidget(refresh_btn)
        
        return layout
    
    def _create_quick_actions(self):
        """Create quick action buttons"""
        layout = QHBoxLayout()
        
        # New Ticket button
        new_ticket_btn = QPushButton(f"➕ {self.lm.get('Tickets.new_ticket', 'New Ticket')}")
        new_ticket_btn.setStyleSheet("""
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
        new_ticket_btn.clicked.connect(self._on_new_ticket)
        layout.addWidget(new_ticket_btn)
        
        # New Customer button
        new_customer_btn = QPushButton(f"➕ {self.lm.get('Customers.new_customer', 'New Customer')}")
        new_customer_btn.setStyleSheet("""
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
        new_customer_btn.clicked.connect(self._on_new_customer)
        layout.addWidget(new_customer_btn)
        
        layout.addStretch()
        
        return layout
    
    def _create_revenue_chart_card(self):
        """Create revenue chart card"""
        card = QFrame()
        card.setObjectName("chartCard")
        card.setMinimumHeight(200)  # Increased from 160
        card.setMaximumHeight(200)  # Fixed height
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)  # Reduced from 12
        
        # Card title
        title = QLabel(self.lm.get("Dashboard.revenue_overview", "Revenue Trend"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Chart canvas
        self.revenue_figure = Figure(figsize=(10, 2), facecolor='none')  # Reduced height from 3 to 2
        self.revenue_canvas = FigureCanvas(self.revenue_figure)
        self.revenue_canvas.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.revenue_canvas)
        
        return card
    
    def _create_recent_tickets_card(self):
        """Create recent tickets list card"""
        card = QFrame()
        card.setObjectName("chartCard")
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        # Card title
        title_layout = QHBoxLayout()
        title = QLabel(self.lm.get("Dashboard.recent_activity", "Recent Tickets"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # View all button
        view_all_btn = QPushButton(f"{self.lm.get('Common.view_all', 'View All')} →")
        view_all_btn.setStyleSheet("border: none; color: #3B82F6; font-weight: 600;")
        view_all_btn.setCursor(QCursor(Qt.PointingHandCursor))
        view_all_btn.clicked.connect(self._on_view_all_tickets)
        title_layout.addWidget(view_all_btn)
        
        layout.addLayout(title_layout)
        
        # Tickets list container
        self.tickets_list_layout = QVBoxLayout()
        self.tickets_list_layout.setSpacing(8)
        layout.addLayout(self.tickets_list_layout)
        
        layout.addStretch()
        
        return card
    
    def _create_quick_stats_card(self):
        """Create quick stats card"""
        card = QFrame()
        card.setObjectName("chartCard")
        card.setMinimumHeight(200)  # Increased from 160
        card.setMaximumHeight(200)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        # Card title
        title = QLabel(self.lm.get("Dashboard.status_breakdown", "Status Breakdown"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Stats container
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(12)
        layout.addLayout(self.stats_layout)
        
        layout.addStretch()
        
        return card
    
    def _create_technician_performance_card(self):
        """Create technician performance card"""
        card = QFrame()
        card.setObjectName("chartCard")
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        # Card title
        title = QLabel(self.lm.get("Dashboard.technician_performance", "Top Technicians"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Performance grid
        self.tech_perf_layout = QGridLayout()
        self.tech_perf_layout.setSpacing(12)
        layout.addLayout(self.tech_perf_layout)
        
        layout.addStretch()
        
        return card
    
    def _on_date_range_changed(self, index):
        """Handle date range change"""
        today = datetime.now().date()
        
        if index == 0:  # Last 7 Days
            self.start_date = today - timedelta(days=7)
            self.end_date = today
        elif index == 1:  # Last 30 Days
            self.start_date = today - timedelta(days=30)
            self.end_date = today
        elif index == 2:  # Last 90 Days
            self.start_date = today - timedelta(days=90)
            self.end_date = today
        elif index == 3:  # This Month
            self.start_date = today.replace(day=1)
            self.end_date = today
        elif index == 4:  # This Year
            self.start_date = today.replace(month=1, day=1)
            self.end_date = today
        
        self.refresh_data()
    
    def _on_new_ticket(self):
        """Handle new ticket button"""
        self.ticket_controller.show_new_ticket_receipt(
            user_id=self.user.id,
            parent=self
        )
    
    def _on_new_customer(self):
        """Handle new customer button"""
        self.customer_controller.show_new_customer_form(
            user_id=self.user.id,
            parent=self
        )
    
    def _on_view_all_tickets(self):
        """Navigate to tickets tab"""
        # Get parent main window and switch to tickets tab
        main_window = self.window()
        if hasattr(main_window, 'stacked_widget'):
            main_window.stacked_widget.setCurrentIndex(1)  # Tickets tab index
    
    def refresh_data(self):
        """Refresh dashboard data"""
        # Get stats
        stats = self.ticket_service.get_dashboard_stats_range(self.start_date, self.end_date, self.current_branch_id)
        avg_time = self.ticket_service.get_average_completion_time(self.start_date, self.end_date, self.current_branch_id)
        
        # Update all sections
        self._update_metric_cards(stats, avg_time)
        self._update_revenue_chart(self.start_date, self.end_date)
        self._update_recent_tickets()
        self._update_quick_stats(stats)
        self._update_technician_performance(self.start_date, self.end_date)
    
    def _update_metric_cards(self, stats, avg_time):
        """Update the top metric cards"""
        # Clear existing cards
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Calculate totals for current period
        total_tickets = stats.get('total_tickets', 0)
        current_revenue = stats.get('revenue', 0)
        
        # Pending = devices that haven't been returned yet (more accurate)
        from models.device import Device
        from datetime import datetime
        start_datetime = datetime.combine(self.start_date, datetime.min.time())
        end_datetime = datetime.combine(self.end_date, datetime.max.time())
        
        current_pending = Device.select().where(
            (Device.status != 'returned') &
            (Device.received_at >= start_datetime) &
            (Device.received_at <= end_datetime) &
            (Device.is_deleted == False)
        ).count()
        
        current_completion_rate = stats.get('completion_rate', 0)
        
        # Calculate previous period dates
        period_length = (self.end_date - self.start_date).days
        prev_end_date = self.start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_length)
        prev_start_datetime = datetime.combine(prev_start_date, datetime.min.time())
        prev_end_datetime = datetime.combine(prev_end_date, datetime.max.time())
        
        # Get previous period stats
        prev_stats = self.ticket_service.get_dashboard_stats_range(prev_start_date, prev_end_date)
        prev_total_tickets = prev_stats.get('total_tickets', 0)
        prev_revenue = prev_stats.get('revenue', 0)
        
        prev_pending = Device.select().where(
            (Device.status != 'returned') &
            (Device.received_at >= prev_start_datetime) &
            (Device.received_at <= prev_end_datetime) &
            (Device.is_deleted == False)
        ).count()
        
        prev_completion_rate = prev_stats.get('completion_rate', 0)
        
        # Calculate growth percentages
        def calculate_growth(current, previous):
            """Calculate percentage growth and format with arrow"""
            if previous == 0:
                if current > 0:
                    return f"↑ {self.lm.get('Common.new', 'New')}"
                else:
                    return "—"
            
            change = ((current - previous) / previous) * 100
            
            if change > 0:
                return f"↑ {abs(change):.1f}%"
            elif change < 0:
                return f"↓ {abs(change):.1f}%"
            else:
                return "— 0%"
        
        tickets_growth = calculate_growth(total_tickets, prev_total_tickets)
        revenue_growth = calculate_growth(current_revenue, prev_revenue)
        pending_growth = calculate_growth(current_pending, prev_pending)
        completion_growth = calculate_growth(current_completion_rate, prev_completion_rate)
        
        # Create metric cards with different colors and real growth data
        cards_data = [
            ("🎫", str(total_tickets), self.lm.get("Dashboard.active_tickets", "Total Tickets"), tickets_growth, "#3B82F6"),  # Blue
            ("💰", self.cf.format(current_revenue), self.lm.get("Dashboard.total_revenue", "Revenue"), revenue_growth, "#10B981"),  # Green
            ("⏳", str(current_pending), self.lm.get("Dashboard.pending_invoices", "Pending"), pending_growth, "#F59E0B"),  # Orange
            ("✅", f"{current_completion_rate}%", self.lm.get("Reports.completion_rate", "Completion Rate"), completion_growth, "#8B5CF6"),  # Purple
        ]
        
        for icon, value, label, growth, color in cards_data:
            card = MetricCard(icon, value, label, growth, color)
            self.metrics_layout.addWidget(card)
    
    def _update_revenue_chart(self, start_date, end_date):
        """Update revenue trend chart"""
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
        
        # Get revenue trend data
        trend_data = self.ticket_service.get_revenue_trend(start_date, end_date, self.current_branch_id)
        
        # Debug: Print revenue trend data
        print(f"DEBUG Revenue Trend: start={start_date}, end={end_date}, branch={self.current_branch_id}")
        print(f"DEBUG Revenue Trend Data: {trend_data}")
        print(f"DEBUG Revenue Trend Count: {len(trend_data)} days")
        
        # Convert to dictionary for easy lookup
        trend_map = {item['date']: item['revenue'] for item in trend_data}
        
        days = []
        revenues = []
        
        # Calculate number of days
        delta = (end_date - start_date).days
        
        # Determine grouping strategy
        if delta <= 7:
            # Daily view
            date_format = "%a"  # Mon, Tue
            
            for i in range(delta + 1):
                day = start_date + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                
                days.append(day.strftime(date_format))
                revenues.append(trend_map.get(day_str, 0.0))
        else:
            # Weekly grouping
            weekly_data = {}
            week_order = []
            
            for i in range(delta + 1):
                day = start_date + timedelta(days=i)
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
        
        # Plot line chart with red color like the screenshot
        x_indices = range(len(days))
        
        if revenues:
            ax.plot(x_indices, revenues, color='#EF4444', linewidth=2.5, marker='o', 
                   markersize=4, markerfacecolor='#EF4444', markeredgecolor='#EF4444')
            
            # Add average line (dotted)
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            ax.axhline(y=avg_revenue, color='#EF4444', linestyle='--', 
                      linewidth=1, alpha=0.5)
        
        # Styling - match screenshot
        ax.set_facecolor(bg_color)
        ax.set_ylim(bottom=0)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(grid_color)
        ax.spines['bottom'].set_color(grid_color)
        
        # Grid styling - match screenshot with dashed lines
        ax.grid(True, alpha=0.3, color=grid_color, linestyle='--', linewidth=0.8)
        ax.set_axisbelow(True)  # Grid behind data
        
        # Set x-axis ticks
        ax.set_xticks(x_indices)
        ax.set_xticklabels(days)
        
        # Tick styling
        ax.tick_params(colors=text_color, labelsize=9)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: self.cf.format(x)))
        
        self.revenue_figure.tight_layout()
        self.revenue_canvas.draw()
    
    def _update_recent_tickets(self):
        """Update recent tickets list"""
        # Clear existing
        while self.tickets_list_layout.count():
            item = self.tickets_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Get recent tickets
        recent_tickets = self.ticket_service.get_recent_tickets(5, self.current_branch_id)
        
        for ticket in recent_tickets:
            ticket_item = self._create_ticket_item(ticket)
            self.tickets_list_layout.addWidget(ticket_item)
    
    def _create_ticket_item(self, ticket):
        """Create a clickable ticket list item"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom: 1px solid #e5e7eb;
                padding: 8px 0px;
            }
            QFrame:hover {
                background-color: rgba(59, 130, 246, 0.05);
                border-radius: 6px;
            }
        """)
        item.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Store ticket ID for click handling
        item.ticket_id = ticket.id
        item.mousePressEvent = lambda event: self._on_ticket_clicked(ticket.id)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 4, 8, 4)  # Reduced vertical padding
        
        # Ticket number
        ticket_num = QLabel(ticket.ticket_number)
        ticket_num.setStyleSheet("font-weight: bold; font-size: 11px;")  # Reduced from 12px
        ticket_num.setFixedWidth(80)  # Reduced from 90
        layout.addWidget(ticket_num)
        
        # Customer name
        customer_name = ticket.customer.name if hasattr(ticket, 'customer') and ticket.customer else self.lm.get("Common.unknown", "Unknown")
        # Truncate if too long
        if len(customer_name) > 12:
            customer_name = customer_name[:12] + "..."
        customer_label = QLabel(customer_name)
        customer_label.setObjectName("metricLabel")
        customer_label.setStyleSheet("font-size: 10px;")  # Smaller font
        customer_label.setFixedWidth(90)  # Reduced from 120
        layout.addWidget(customer_label)
        
        # Device info
        device_info = f"{ticket.device.brand} {ticket.device.model}" if ticket.device else self.lm.get("Common.no_device", "No Device")
        # Truncate if too long
        if len(device_info) > 15:
            device_info = device_info[:15] + "..."
        device_label = QLabel(device_info)
        device_label.setObjectName("metricLabel")
        device_label.setStyleSheet("font-size: 10px;")  # Smaller font
        device_label.setFixedWidth(100)  # Reduced from 120
        layout.addWidget(device_label)
        
        # Issue (truncated)
        issue = ticket.error[:20] + "..." if ticket.error and len(ticket.error) > 20 else (ticket.error or self.lm.get("Common.no_issue", "No issue"))
        issue_label = QLabel(issue)
        issue_label.setObjectName("metricLabel")
        issue_label.setStyleSheet("font-size: 10px; color: #6B7280;")  # Smaller font
        layout.addWidget(issue_label)
        
        layout.addStretch()
        
        # Status badge
        status_text = ticket.status.replace('_', ' ').title()
        # Translate status if possible
        status_key = f"Common.{ticket.status}"
        status_text = self.lm.get(status_key, status_text)
        
        status_badge = QLabel(status_text)
        status_badge.setStyleSheet("""
            padding: 3px 10px;
            border-radius: 10px;
            background-color: #3B82F6;
            color: white;
            font-size: 10px;
            font-weight: 600;
        """)
        layout.addWidget(status_badge)
        
        return item
    
    def _on_ticket_clicked(self, ticket_id):
        """Handle ticket click"""
        # Open ticket details dialog
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        ticket = self.ticket_service.get_ticket(ticket_id)
        if ticket:
            dialog = TicketDetailsDialog(
                ticket=ticket,
                ticket_service=self.ticket_service,
                ticket_controller=self.ticket_controller,
                technician_controller=self.technician_controller,
                repair_part_controller=self.repair_part_controller,
                work_log_controller=self.work_log_controller,
                business_settings_service=self.business_settings_service,
                part_service=self.part_service,
                technician_repository=self.technician_repository,
                user=self.user,
                container=self.container,
                parent=self
            )
            dialog.exec()
    
    def _update_quick_stats(self, stats):
        """Update quick stats"""
        # Clear existing
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Status breakdown
        statuses = [
            (self.lm.get("Tickets.new_ticket", "New"), stats.get('new_jobs', 0), "#3B82F6"),
            (self.lm.get("Common.in_progress", "In Progress"), stats.get('in_progress', 0), "#F59E0B"),
            (self.lm.get("Common.completed", "Completed"), stats.get('completed', 0), "#10B981"),
        ]
        
        for status_name, count, color in statuses:
            # Create a container widget for each status item
            stat_widget = QWidget()
            stat_widget.setStyleSheet("background-color: transparent;")  # Transparent background
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 6, 0, 6)
            stat_layout.setSpacing(0)
            
            label = QLabel(status_name)
            label.setObjectName("metricLabel")
            stat_layout.addWidget(label)
            
            stat_layout.addStretch()
            
            value = QLabel(str(count))
            value.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            stat_layout.addWidget(value)
            
            self.stats_layout.addWidget(stat_widget)
    
    def _update_technician_performance(self, start_date, end_date):
        """Update technician performance"""
        # Clear existing
        for i in reversed(range(self.tech_perf_layout.count())): 
            self.tech_perf_layout.itemAt(i).widget().setParent(None)
        
        # Get technician data
        tech_data = self.ticket_service.get_technician_performance(start_date, end_date, self.current_branch_id)
        
        # Headers
        headers = [
            self.lm.get("Tickets.technician", "Technician"),
            self.lm.get("Tickets.assignment", "assignment"),
            self.lm.get("Common.completed", "Completed"),
            self.lm.get("Reports.revenue", "Revenue"),
            self.lm.get("Reports.completion_rate", "Rate")
        ]
        for col, header in enumerate(headers):
            header_label = QLabel(header)
            header_label.setStyleSheet("font-weight: bold; color: #6B7280;")
            self.tech_perf_layout.addWidget(header_label, 0, col)
        
        # Data rows
        for row, tech in enumerate(tech_data[:5], start=1):  # Show top 5
            # Name
            name_label = QLabel(tech['technician_name'])
            self.tech_perf_layout.addWidget(name_label, row, 0)
            
            # Assigned
            assigned_label = QLabel(str(tech['total_assigned']))
            self.tech_perf_layout.addWidget(assigned_label, row, 1)
            
            # Completed
            completed_label = QLabel(str(tech['tickets_completed']))
            self.tech_perf_layout.addWidget(completed_label, row, 2)
            
            # Revenue
            revenue_label = QLabel(self.cf.format(tech['total_revenue']))
            self.tech_perf_layout.addWidget(revenue_label, row, 3)
            
            # Completion rate
            rate = (tech['tickets_completed'] / tech['total_assigned'] * 100) if tech['total_assigned'] > 0 else 0
            rate_label = QLabel(f"{rate:.1f}%")
            rate_label.setStyleSheet("font-weight: bold; color: #10B981;")
            self.tech_perf_layout.addWidget(rate_label, row, 4)

    def _subscribe_to_events(self):
        """Subscribe to domain events"""
        events = [
            TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
            TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent,
            InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent,
            CustomerCreatedEvent, CustomerUpdatedEvent, CustomerDeletedEvent,
            TechnicianCreatedEvent, TechnicianUpdatedEvent, TechnicianDeactivatedEvent,
            BranchContextChangedEvent
        ]
        for event_type in events:
            EventBus.subscribe(event_type, self._handle_domain_event)

    def _handle_domain_event(self, event):
        """Handle domain events by refreshing data"""
        if isinstance(event, BranchContextChangedEvent):
            self.current_branch_id = event.branch_id
            
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.refresh_data)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # Load data after a short delay to allow UI to render
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.refresh_data)
            self._data_loaded = True
        else:
            # If already loaded, just refresh quickly to be safe
            self.refresh_data()
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.refresh_data)
            self._data_loaded = True

    def closeEvent(self, event):
        """Clean up resources"""
        self._unsubscribe_from_events()
        super().closeEvent(event)

    def _unsubscribe_from_events(self):
        """Unsubscribe from domain events"""
        events = [
            TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
            TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent,
            InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent,
            CustomerCreatedEvent, CustomerUpdatedEvent, CustomerDeletedEvent,
            TechnicianCreatedEvent, TechnicianUpdatedEvent, TechnicianDeactivatedEvent,
            BranchContextChangedEvent
        ]
        for event_type in events:
            EventBus.unsubscribe(event_type, self._handle_domain_event)
