# src/app/views/components/dashboard_charts.py
"""
Dashboard chart components using matplotlib integrated with PySide6.
Provides reusable chart widgets for visualizing ticket and revenue data.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import Dict, List
import numpy as np


class StatusDistributionChart(QWidget):
    """Interactive donut chart with clickable segments"""
    
    segment_clicked = Signal(str, int, float)  # status, count, percentage
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 7), dpi=100, facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Status colors - vibrant and modern
        self.status_colors = {
            'open': '#3B82F6',           # Bright Blue
            'diagnosed': '#A855F7',      # Purple
            'in_progress': '#F59E0B',    # Orange
            'awaiting_parts': '#EF4444', # Red
            'completed': '#10B981',      # Green
            'cancelled': '#EC4899',      # Pink
            'unrepairable': '#6B7280'    # Gray
        }
        
        
        # Status icons - using text abbreviations instead of emojis to avoid font issues
        self.status_icons = {
            'open': 'NEW',
            'diagnosed': 'DIA',
            'in_progress': 'WIP',
            'awaiting_parts': 'WAIT',
            'completed': 'DONE',
            'cancelled': 'CANC',
            'unrepairable': 'UNRP'
        }
        
        # Track data and selection
        self.distribution = {}
        self.total = 0
        self.selected_index = None
        self.wedges = []
        self.labels_data = []
        
        # Connect click event
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)
    
    def wheelEvent(self, event):
        """Pass wheel events to parent to enable scrolling over chart"""
        if self.parent():
            self.parent().wheelEvent(event)
        else:
            super().wheelEvent(event)
        
    def update_chart(self, distribution: Dict[str, int]):
        """Update the donut chart with new data"""
        self.distribution = distribution
        self.total = sum(distribution.values())
        self.selected_index = None
        
        self.figure.clear()
        
        if not distribution or self.total == 0:
            # Show empty state
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='white')
            ax.axis('off')
            ax.set_facecolor('none')
            self.canvas.draw()
            return
        
        # Prepare data
        labels = []
        sizes = []
        colors = []
        self.labels_data = []
        
        for status, count in distribution.items():
            if count > 0:
                label = status.replace('_', ' ').title()
                labels.append(label)
                sizes.append(count)
                colors.append(self.status_colors.get(status, '#6B7280'))
                self.labels_data.append({
                    'status': status,
                    'label': label,
                    'count': count,
                    'percentage': (count / self.total) * 100,
                    'color': self.status_colors.get(status, '#6B7280'),
                    'icon': self.status_icons.get(status, '📊')
                })
        
        # Create donut chart
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')
        
        # Create the donut
        self.wedges, texts = ax.pie(
            sizes,
            labels=None,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.35, edgecolor='#1e293b', linewidth=1.5)
        )
        
        # Display total by default
        self._update_center_text(ax, None)
        
        # Equal aspect ratio
        ax.axis('equal')
        
        self.figure.patch.set_alpha(0.0)
        self.figure.tight_layout()
        
        self.canvas.draw()
    
    def _update_center_text(self, ax, index):
        """Update the center text based on selection"""
        # Clear previous text
        for txt in ax.texts:
            txt.remove()
        
        if index is None:
            # Show total
            ax.text(0, 0.15, 'Total', ha='center', va='center', 
                   fontsize=13, color='#9CA3AF', fontweight='normal')
            ax.text(0, -0.15, f'{self.total:,}', ha='center', va='center', 
                   fontsize=28, color='white', fontweight='bold')
        else:
            # Show selected segment
            data = self.labels_data[index]
            
            # Status abbreviation (styled as badge)
            ax.text(0, 0.25, data['icon'], ha='center', va='center', 
                   fontsize=16, color='white', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=data['color'], 
                            edgecolor='none', alpha=0.9))
            
            # Label and percentage
            ax.text(0, 0.05, f"{data['label']} {data['percentage']:.1f}%", 
                   ha='center', va='center', 
                   fontsize=12, color='#9CA3AF', fontweight='normal')
            
            # Count
            ax.text(0, -0.20, f"{data['count']:,}", ha='center', va='center', 
                   fontsize=28, color=data['color'], fontweight='bold')
    
    def _on_click(self, event):
        """Handle click on chart segments"""
        if event.inaxes is None:
            return
        
        # Check if click is on a wedge
        for i, wedge in enumerate(self.wedges):
            if wedge.contains_point([event.x, event.y]):
                # Toggle selection
                if self.selected_index == i:
                    self.selected_index = None
                else:
                    self.selected_index = i
                
                self._highlight_segment()
                
                # Emit signal
                if self.selected_index is not None:
                    data = self.labels_data[self.selected_index]
                    self.segment_clicked.emit(data['status'], data['count'], data['percentage'])
                
                break
    
    def _on_hover(self, event):
        """Handle hover over segments"""
        if event.inaxes is None:
            return
        
        # Change cursor on hover
        for wedge in self.wedges:
            if wedge.contains_point([event.x, event.y]):
                self.canvas.setCursor(Qt.PointingHandCursor)
                return
        
        self.canvas.setCursor(Qt.ArrowCursor)
    
    def _highlight_segment(self):
        """Highlight the selected segment with animation"""
        ax = self.figure.axes[0]
        
        # Reset all wedges
        for i, wedge in enumerate(self.wedges):
            if i == self.selected_index:
                # Explode selected segment
                wedge.set_radius(1.05)
                wedge.set_linewidth(2)
                wedge.set_edgecolor('#ffffff')
            else:
                # Normal state
                wedge.set_radius(1.0)
                wedge.set_linewidth(1.5)
                wedge.set_edgecolor('#1e293b')
        
        # Update center text
        self._update_center_text(ax, self.selected_index)
        
        self.canvas.draw()



class RevenueTrendChart(QWidget):
    """Line chart showing revenue trend with dynamic coloring"""
    
    def __init__(self, currency_formatter=None, parent=None):
        super().__init__(parent)
        self.cf = currency_formatter
        self.figure = Figure(figsize=(8, 5), dpi=100, facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def wheelEvent(self, event):
        """Pass wheel events to parent to enable scrolling over chart"""
        if self.parent():
            self.parent().wheelEvent(event)
        else:
            super().wheelEvent(event)
    
    def update_chart(self, trend_data: List[Dict]):
        """Update the chart with new data
        
        Args:
            trend_data: List of dicts with 'date', 'revenue', 'count' keys
        """
        self.figure.clear()
        
        if not trend_data:
            # Show empty state
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No revenue data available', 
                   ha='center', va='center', fontsize=12, color='white')
            ax.axis('off')
            ax.set_facecolor('none')
            self.canvas.draw()
            return
        
        # Prepare data
        dates = [item['date'] for item in trend_data]
        revenues = [item['revenue'] for item in trend_data]
        
        # Determine trend color (compare first and last values)
        if len(revenues) >= 2:
            start_value = revenues[0]
            end_value = revenues[-1]
            
            if end_value > start_value:
                # Growing trend - Green
                line_color = '#10B981'
                fill_color = '#10B981'
            else:
                # Declining trend - Red
                line_color = '#EF4444'
                fill_color = '#EF4444'
        else:
            line_color = '#10B981'
            fill_color = '#10B981'
        
        # Calculate statistics
        max_revenue = max(revenues)
        min_revenue = min(revenues)
        avg_revenue = sum(revenues) / len(revenues)
        
        # Create line chart
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')
        
        # Plot line
        x_values = list(range(len(dates)))
        line = ax.plot(x_values, revenues, linewidth=2, 
                      color=line_color, zorder=3)
        
        # Fill area under the line with gradient effect
        ax.fill_between(x_values, revenues, alpha=0.2, color=fill_color, zorder=1)
        
        # Add horizontal average line (dotted)
        ax.axhline(y=avg_revenue, color='#6B7280', linestyle='--', 
                  linewidth=1, alpha=0.5, zorder=2)
        
        # Format currency using currency formatter if available
        def format_currency(value):
            if self.cf:
                return self.cf.format(value)
            return f'${value:,.0f}'
        
        # Add average label with tooltip style
        ax.text(len(dates) * 0.1, avg_revenue, f'  Average: {format_currency(avg_revenue)}', 
               fontsize=9, color='#9CA3AF', va='center',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#374151', 
                        edgecolor='none', alpha=0.8))
        
        # Add max and min labels
        max_idx = revenues.index(max_revenue)
        ax.text(max_idx, max_revenue, format_currency(max_revenue), 
               fontsize=9, color='white', ha='center', va='bottom',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#374151', 
                        edgecolor=line_color, alpha=0.9))
        
        min_idx = revenues.index(min_revenue)
        ax.text(min_idx, min_revenue, format_currency(min_revenue), 
               fontsize=9, color='white', ha='center', va='top',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#374151', 
                        edgecolor=line_color, alpha=0.9))
        
        # Styling
        ax.set_xlabel('Date', fontsize=9, color='#9CA3AF')
        ax.set_ylabel('Revenue', fontsize=9, color='#9CA3AF')
        ax.grid(True, alpha=0.1, linestyle='-', color='gray', zorder=0)
        
        # Format dates for display (remove time if present)
        from datetime import datetime as dt
        formatted_dates = []
        for date_str in dates:
            try:
                # Try to parse as datetime and format as date only
                if 'T' in date_str or ' ' in date_str:
                    # Has time component
                    date_obj = dt.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_dates.append(date_obj.strftime('%b %d'))
                else:
                    # Already just a date
                    date_obj = dt.strptime(date_str, '%Y-%m-%d')
                    formatted_dates.append(date_obj.strftime('%b %d'))
            except:
                # Fallback to original string
                formatted_dates.append(date_str)
        
        # Set x-axis labels
        if len(dates) <= 10:
            ax.set_xticks(x_values)
            ax.set_xticklabels(formatted_dates)
        else:
            # Show fewer labels for many data points
            step = max(1, len(dates) // 8)
            tick_positions = x_values[::step]
            tick_labels = formatted_dates[::step]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels)

        
        ax.tick_params(axis='x', labelsize=7, colors='#9CA3AF')
        ax.tick_params(axis='y', labelsize=8, colors='#9CA3AF')

        
        # Format y-axis with currency formatter
        if self.cf:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: self.cf.format(x)))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Set spine colors
        for spine in ax.spines.values():
            spine.set_color('#374151')
            spine.set_alpha(0.3)
        
        # Add padding to y-axis
        y_range = max_revenue - min_revenue
        if y_range > 0:
            ax.set_ylim(min_revenue - y_range * 0.1, max_revenue + y_range * 0.15)
        else:
            # If all values are the same, add a small buffer
            ax.set_ylim(max(0, min_revenue - 10), min_revenue + 10)
        
        # Tight layout with padding to prevent label cutoff
        self.figure.patch.set_alpha(0.0)
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.15)
        
        self.canvas.draw()
