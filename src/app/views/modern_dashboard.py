# src/app/views/modern_dashboard.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QScrollArea, QGridLayout, QPushButton,
                              QComboBox, QDateEdit)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QCursor
from views.components.new_dashboard_widgets import WaveChart, MetricCard, DashboardCard, is_dark_theme
from datetime import datetime, timedelta
# Matplotlib removed
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
        
        # Flag to track if data has been loaded
        self._data_loaded = False
        
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
        self._connect_theme_signal()
        
    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)
                
                # Initial propagation
                self._on_theme_changed(self.container.theme_controller.current_theme)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        # Determine strict theme mode
        current = str(theme_name).lower().strip()
        is_dark = (current == 'dark')
        # print(f"DEBUG: ModernDashboardTab._on_theme_changed propagation -> theme={theme_name} -> is_dark={is_dark}")

        # Propagate to all theme-aware widgets
        for widget in self.findChildren(DashboardCard):
            widget.set_theme_mode(is_dark)
            
        for chart in self.findChildren(WaveChart):
            chart.set_theme_mode(is_dark)

        # MetricCards are re-created in refresh_data(), so they handle themselves via the init arg
        self.refresh_data()
    
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
        
        # Chart & Lists row
        chart_row = QHBoxLayout()
        chart_row.setSpacing(12)
        
        # Left column - Revenue, Techs
        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        
        # 1. Revenue Chart
        chart_card = self._create_revenue_chart_card()
        left_column.addWidget(chart_card)
        
        # 2. Technician Performance
        tech_perf_card = self._create_technician_performance_card()
        left_column.addWidget(tech_perf_card)
        
        chart_row.addLayout(left_column, 7) # 70% width
        
        # Right column - Status, Recent Activity
        right_column = QVBoxLayout()
        right_column.setSpacing(12)
        
        # 1. Status Breakdown
        self.quick_stats_card = self._create_quick_stats_card()
        right_column.addWidget(self.quick_stats_card)
        
        # 2. Recent tickets
        recent_tickets_card = self._create_recent_tickets_card()
        right_column.addWidget(recent_tickets_card)
        
        chart_row.addLayout(right_column, 3) # 30% width
        
        main_layout.addLayout(chart_row)
        
        # We need to remove the old creation calls from further down if they exist or just ensure _setup_ui matches this flow
        # In the original file, create_quick_stats_card etc were called later. I need to make sure I don't double add or leave orphans.
        # The previous code had chart_row with left/right columns. I've restructured it.
        
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
        
        # Mobile App button
        mobile_app_btn = QPushButton(f"📱 {self.lm.get('Dashboard.mobile_app', 'Mobile App')}")
        mobile_app_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: black;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        mobile_app_btn.clicked.connect(self._on_mobile_pairing)
        layout.addWidget(mobile_app_btn)
        
        layout.addStretch()
        
        return layout
    
    def _create_revenue_chart_card(self):
        """Create revenue chart card"""
        card = DashboardCard()
        # card.setMinimumHeight(400) # Let the chart decide height
        # dashboard card handles style dynamically
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5) # Reduced from 20
        layout.setContentsMargins(20, 15, 20, 10) # Reduced from 25s
        
        # Card header row
        header = QHBoxLayout()
        title = QLabel(self.lm.get("Dashboard.revenue_overview", "Revenue Trend"))
        title.setStyleSheet("font-size: 16px; font-weight: bold; border: none; background: transparent;") # Reduced font slightly
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Wave Chart
        self.wave_chart = WaveChart()
        self.wave_chart.setMinimumHeight(300)
        self.wave_chart.set_formatter(lambda x: self.cf.format(x))
        layout.addWidget(self.wave_chart)
        
        return card
    
    def _create_recent_tickets_card(self):
        """Create recent tickets list card"""
        card = DashboardCard() # Use generic theme aware card
        
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
        """Create quick stats card (Vertical List)"""
        card = DashboardCard()
        # card.setMinimumHeight(100)
        # card.setMaximumHeight(60) # Removed fixed height constraint
        # style handled by class
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel(self.lm.get("Dashboard.status_breakdown", "Status Breakdown"))
        title.setStyleSheet("font-size: 14px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(title)
        
        # Stats container - Vertical
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(0)
        layout.addLayout(self.stats_layout)
        
        # Remove stretch if we want it compact at top
        # layout.addStretch() 
        
        return card
    
    def _create_technician_performance_card(self):
        """Create technician performance card"""
        card = DashboardCard()
        # card.setObjectName("chartCard") # Handled by DashboardCard
        
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
    
    def _on_mobile_pairing(self):
        """Handle mobile app pairing button."""
        from views.mobile_pairing_dialog import MobilePairingDialog
        dialog = MobilePairingDialog(self)
        dialog.exec()
    
    def _on_view_all_tickets(self):
        """Navigate to tickets tab"""
        # Get parent main window and switch to tickets tab
        main_window = self.window()
        if hasattr(main_window, 'stacked_widget'):
            main_window.stacked_widget.setCurrentIndex(1)  # Tickets tab index
    
    def refresh_data(self):
        """Refresh dashboard data"""
        try:
            # Get stats
            stats = self.ticket_service.get_dashboard_stats_range(self.start_date, self.end_date, self.current_branch_id)
            avg_time = self.ticket_service.get_average_completion_time(self.start_date, self.end_date, self.current_branch_id)
            
            # Update all sections
            self._update_metric_cards(stats, avg_time)
            self._update_revenue_chart(self.start_date, self.end_date)
            try:
                self._update_recent_tickets()
            except Exception as e:
                print(f"Error updating recent tickets: {e}")
                
            self._update_quick_stats(stats)
            self._update_technician_performance(self.start_date, self.end_date)
        except Exception as e:
            print(f"Error refreshing dashboard data: {e}")
            import traceback
            traceback.print_exc()

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
        # Title, Value, Subtext, Color, ShowDonut, DonutValue
        cards_data = [
            (self.lm.get("Dashboard.active_tickets", "Total Tickets"), str(total_tickets), tickets_growth, "#1F2937", True, 0.75),
            (self.lm.get("Dashboard.total_revenue", "Revenue"), self.cf.format(current_revenue), revenue_growth, "#1F2937", True, 0.60),
            (self.lm.get("Dashboard.pending_invoices", "Pending"), str(current_pending), pending_growth, "#1F2937", False, 0.0),
            (self.lm.get("Reports.completion_rate", "Completion Rate"), f"{current_completion_rate}%", completion_growth, "#1F2937", True, current_completion_rate / 100.0 if current_completion_rate else 0.0),
        ]
        
        # Determine theme mode
        is_dark = True
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            current = str(self.container.theme_controller.current_theme).lower().strip()
            is_dark = (current == 'dark')
            print(f"DEBUG: ModernDashboardTab detected theme from controller: '{self.container.theme_controller.current_theme}' -> cleaned='{current}' -> is_dark={is_dark}")
        else:
            is_dark = is_dark_theme(self)
            print(f"DEBUG: ModernDashboardTab detected theme from utils -> is_dark={is_dark}")

        for title, value, subtext, color, show_donut, donut_val in cards_data:
            card = MetricCard(title, value, subtext, color, show_donut, donut_val, is_dark_mode=is_dark)
            self.metrics_layout.addWidget(card)
    
    def _update_revenue_chart(self, start_date, end_date):
        """Update revenue trend chart"""
        # Get revenue trend data
        trend_data = self.ticket_service.get_revenue_trend(start_date, end_date, self.current_branch_id)
        
        # Convert to dictionary for easy lookup
        trend_map = {item['date']: item['revenue'] for item in trend_data}
        
        days = []
        revenues = []
        
        # Calculate number of days
        delta = (end_date - start_date).days
        
        # Determine grouping strategy (same as before)
        if delta <= 7:
            # Daily view
            date_format = "%a"  # Mon, Tue
            for i in range(delta + 1):
                day = start_date + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                
                days.append(day.strftime(date_format))
                revenues.append(float(trend_map.get(day_str, 0.0)))
        else:
            # Weekly grouping or coarse daily if < 30 etc.
            # For simplicity, stick to Daily if < 14, else Weekly
             # Weekly grouping
            weekly_data = {}
            week_order = []
            
            for i in range(delta + 1):
                day = start_date + timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                revenue = float(trend_map.get(day_str, 0.0))
                
                # Get week start date (Monday)
                week_start = day - timedelta(days=day.weekday())
                week_label = week_start.strftime("%b %d")
                
                if week_label not in weekly_data:
                    weekly_data[week_label] = 0.0
                    week_order.append(week_label)
                
                weekly_data[week_label] += revenue
            
            days = week_order
            revenues = [weekly_data[lbl] for lbl in days]
            
        # Update Wave Chart
        self.wave_chart.set_data(revenues, days)
    
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
        """Update quick stats (Vertical List)"""
        # Clear existing
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        try:
            # Status breakdown
            statuses = [
                (self.lm.get("Tickets.new_ticket", "New"), stats.get('new_jobs', 0), "#3B82F6"),
                (self.lm.get("Common.in_progress", "In Progress"), stats.get('in_progress', 0), "#F59E0B"),
                (self.lm.get("Common.completed", "Completed"), stats.get('completed', 0), "#10B981"),
            ]
            
            for status_name, count, color in statuses:
                # Create a compact container for each status item
                stat_widget = QWidget()
                stat_widget.setMinimumHeight(30) # Ensure visibility
                stat_widget.setStyleSheet("background-color: transparent;")
                
                # Use QHBoxLayout: Label -> Stretch -> Value
                stat_layout = QHBoxLayout(stat_widget)
                stat_layout.setContentsMargins(10, 5, 10, 5)
                stat_layout.setSpacing(10)
                
                # Ensure status_name is string
                status_str = str(status_name) if status_name else "Status"
                
                label = QLabel(status_str)
                label.setObjectName("metricLabel")
                label.setStyleSheet("font-size: 13px; color: #9CA3AF; border: none; font-weight: 500;")
                stat_layout.addWidget(label)
                
                stat_layout.addStretch()
                
                value = QLabel(str(count))
                value.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; border: none;")
                stat_layout.addWidget(value)
                
                self.stats_layout.addWidget(stat_widget)
                
                # Add separator lines
                if status_name != statuses[-1][0]:
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    line.setFrameShadow(QFrame.Sunken)
                    line.setStyleSheet("background-color: #374151; border: none; max-height: 1px;")
                    self.stats_layout.addWidget(line)
        except Exception as e:
            print(f"Error updating quick stats: {e}")
    
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
