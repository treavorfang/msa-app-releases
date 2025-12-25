from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from typing import List, Dict
from dtos.ticket_dto import TicketDTO
from views.tickets.ticket_base import TicketBaseWidget
from utils.language_manager import language_manager

class KanbanView(TicketBaseWidget):
    """
    Kanban board view for tickets
    """
    ticket_clicked = Signal(object, TicketDTO)  # card_widget, ticket_dto
    ticket_double_clicked = Signal(TicketDTO)
    context_menu_requested = Signal(object, TicketDTO)  # global_pos, ticket_dto
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kanban_columns = {}
        self.lm = language_manager  # Initialize language manager
        self.current_theme = 'dark' # Default theme
        self._setup_ui()
        
    def set_theme(self, theme_name):
        """Set the current theme"""
        self.current_theme = 'dark' if theme_name == 'dark' else 'light'
        self._update_all_styles()

    def _get_theme_colors(self):
        """Get colors based on current theme"""
        is_dark = self.current_theme == 'dark'
        return {
            'bg_primary': '#1F2937' if is_dark else '#FFFFFF',
            'bg_secondary': '#374151' if is_dark else '#F3F4F6',
            'bg_tertiary': '#4B5563' if is_dark else '#E5E7EB',
            'text_primary': 'white' if is_dark else '#111827',
            'text_secondary': '#9CA3AF' if is_dark else '#6B7280',
            'border': '#4B5563' if is_dark else '#E5E7EB',
            'border_hover': '#3B82F6', # Blue
            'border_selected': '#3B82F6',
            'card_bg': '#374151' if is_dark else '#FFFFFF',
            'card_bg_hover': '#4B5563' if is_dark else '#F9FAFB', # Slightly darker/lighter
            'count_bg': '#374151' if is_dark else '#E5E7EB',
            'count_text': 'white' if is_dark else '#374151'
        }

    def _update_all_styles(self):
        """Update styles for all elements"""
        colors = self._get_theme_colors()
        
        # Update columns
        for status_key, column in self.kanban_columns.items():
            # Update header title color
            header_layout = column.layout().itemAt(0).layout()
            title_label = header_layout.itemAt(0).widget()
            title_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: bold;
                color: {self.get_status_color(status_key)};
            """)
            
            # Update count label
            count_label = header_layout.itemAt(1).widget()
            count_label.setStyleSheet(f"""
                background-color: {colors['count_bg']};
                color: {colors['count_text']};
                padding: 2px 6px;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
            """)
            
            # Update cards in this column
            cards_container = column.findChild(QWidget, f"kanban_cards_{status_key}")
            if cards_container:
                layout = cards_container.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item.widget() and hasattr(item.widget(), 'ticket_dto'):
                        card = item.widget()
                        # Update card background/border
                        # We don't know is_selected easily, but we can check if border is blue?
                        # Or just assume false for now, parent handles selection refresh usually.
                        # Ideally, we should check existing style sheet? 
                        # Actually, better to check if ticket id is in parent.selected_tickets? 
                        # But we don't have access to parent.selected_tickets easily.
                        
                        # Workaround: Check object name or property?
                        # Let's just default to unselected style for immediate refresh, 
                        # or check if "border: 2px" is present in current stylesheet.
                        current_style = card.styleSheet()
                        is_selected = "border: 2px" in current_style
                        self.update_card_style(card, is_selected)
                        
                        # Update labels inside card
                        card_layout = card.layout()
                        if card_layout:
                            # 0: Ticket Num
                            ticket_num_item = card_layout.itemAt(0)
                            if ticket_num_item and ticket_num_item.widget():
                                ticket_num_item.widget().setStyleSheet(f"font-weight: bold; font-size: 12px; color: {colors['text_primary']};")
                            
                            # 1: Customer
                            cust_item = card_layout.itemAt(1)
                            if cust_item and cust_item.widget():
                                cust_item.widget().setStyleSheet(f"font-size: 11px; color: {colors['text_secondary']};")
                                
                            # 2: Issue
                            issue_item = card_layout.itemAt(2)
                            if issue_item and issue_item.widget():
                                issue_item.widget().setStyleSheet(f"font-size: 10px; color: {colors['text_secondary']};")
                            
                            # 3: Technician
                            tech_item = card_layout.itemAt(3)
                            if tech_item and tech_item.widget():
                                tech_item.widget().setStyleSheet(f"font-size: 10px; color: {colors['text_secondary']};")
        
    def _setup_ui(self):
        """Setup the Kanban UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.kanban_layout = QHBoxLayout(container)
        self.kanban_layout.setSpacing(12)
        self.kanban_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create columns for each status
        statuses = [
            ('open', self.lm.get('Common.open', 'Open')),
            ('diagnosed', self.lm.get('Common.diagnosed', 'Diagnosed')),
            ('in_progress', self.lm.get('Common.in_progress', 'In Progress')),
            ('awaiting_parts', self.lm.get('Common.awaiting_parts', 'Awaiting Parts')),
            ('completed', self.lm.get('Common.completed', 'Completed'))
        ]
        
        for status_key, status_label in statuses:
            column = self._create_kanban_column(status_key, status_label)
            self.kanban_columns[status_key] = column
            self.kanban_layout.addWidget(column)
        
        scroll.setWidget(container)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
    def _create_kanban_column(self, status_key, status_label):
        """Create a single Kanban column"""
        column = QFrame()
        column.setObjectName("kanbanColumn")
        column.setMinimumWidth(180)
        column.setMaximumWidth(250)
        
        layout = QVBoxLayout(column)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(status_label)
        colors = self._get_theme_colors()
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {self.get_status_color(status_key)};
        """)
        header.addWidget(title)
        
        count_label = QLabel("0")
        count_label.setObjectName(f"kanban_count_{status_key}")
        count_label.setStyleSheet(f"""
            background-color: {colors['count_bg']};
            color: {colors['count_text']};
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(count_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Cards container
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        cards_container = QWidget()
        cards_container.setObjectName(f"kanban_cards_{status_key}")
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setSpacing(8)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.addStretch()
        
        cards_scroll.setWidget(cards_container)
        layout.addWidget(cards_scroll)
        
        return column
    
    def populate(self, tickets: List[TicketDTO], selected_ticket_ids: List[int] = None):
        """Populate Kanban board view"""
        if selected_ticket_ids is None:
            selected_ticket_ids = []
            
        # Group tickets by status
        tickets_by_status = {}
        for ticket in tickets:
            status = ticket.status
            if status not in tickets_by_status:
                tickets_by_status[status] = []
            tickets_by_status[status].append(ticket)
        
        # Update each column
        for status_key, column in self.kanban_columns.items():
            # Get cards container
            cards_container = column.findChild(QWidget, f"kanban_cards_{status_key}")
            if not cards_container:
                continue
            
            # Clear existing cards
            layout = cards_container.layout()
            while layout.count() > 1:  # Keep the stretch
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add tickets for this status
            status_tickets = tickets_by_status.get(status_key, [])
            for ticket in status_tickets:
                is_selected = ticket.id in selected_ticket_ids
                card = self._create_kanban_card(ticket, is_selected)
                layout.insertWidget(layout.count() - 1, card)
            
            # Update count
            count_label = column.findChild(QLabel, f"kanban_count_{status_key}")
            if count_label:
                count_label.setText(str(len(status_tickets)))
                
    def _create_kanban_card(self, ticket: TicketDTO, is_selected: bool):
        """Create a Kanban card"""
        card = QFrame()
        card.setObjectName("kanbanCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.ticket_id = ticket.id
        
        # Store ticket for click handling
        card.ticket_dto = ticket
        
        # Custom click handling for kanban cards
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.ticket_clicked.emit(card, ticket)
                event.accept()
            elif event.button() == Qt.RightButton:
                try:
                    global_pos = event.globalPosition().toPoint()
                except AttributeError:
                    global_pos = event.globalPos()
                
                self.context_menu_requested.emit(global_pos, ticket)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self.ticket_double_clicked.emit(ticket)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Ticket number
        colors = self._get_theme_colors()
        ticket_num = QLabel(ticket.ticket_number)
        ticket_num.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {colors['text_primary']};")
        layout.addWidget(ticket_num)
        
        # Customer
        customer = QLabel(ticket.customer.name if ticket.customer else self.lm.get("Tickets.no_customer", "No Customer"))
        customer.setStyleSheet(f"font-size: 11px; color: {colors['text_secondary']};")
        layout.addWidget(customer)
        
        # Issue (truncated)
        issue = ticket.error[:40] + "..." if ticket.error and len(ticket.error) > 40 else (ticket.error or "")
        issue_label = QLabel(issue)
        issue_label.setStyleSheet(f"font-size: 10px; color: {colors['text_secondary']};")
        issue_label.setWordWrap(True)
        layout.addWidget(issue_label)
        
        # Technician
        tech_name = ticket.technician_name or self.lm.get("Tickets.not_assigned", "Unassigned")
        tech = QLabel(f"👤 {tech_name}")
        colors = self._get_theme_colors()
        tech.setStyleSheet(f"font-size: 10px; color: {colors['text_secondary']};")
        layout.addWidget(tech)
        
        # Customer
        # Update colors for customer and issue labels previously created
        # We need to recreate them or update them here to use variables
        # Wait, the lines above (192, 199) are inside this method. I need to be careful with chunks.
        # Let's replace the whole method content logic for labels below.
        
        # Actually, let's just update the specific text color lines in previous chunk if possible?
        # No, I am in `_create_kanban_card`.
        # I'll update `update_card_style` first.
        
        self.update_card_style(card, is_selected)
        
        # Update internal labels colors
        # We can't easily access them unless we stored them. 
        # But wait, I am CREATING them right now.
        
        # Let's rewrite the label creation to use dynamic colors.
        
        return card

    # We need to make sure we replace the label styles above.
    # I'll do a larger chunk replacement for `_create_kanban_card` to fix label colors.
        
    def update_card_style(self, card, is_selected):
        """Update card style based on selection"""
        colors = self._get_theme_colors()
        
        if is_selected:
            card.setStyleSheet(f"""
                QFrame#kanbanCard {{
                    background-color: {colors['card_bg']};
                    border: 2px solid {colors['border_selected']};
                    border-radius: 6px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame#kanbanCard {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                }}
                QFrame#kanbanCard:hover {{
                    border-color: {colors['border_hover']};
                    background-color: {colors['card_bg_hover']};
                }}
            """)