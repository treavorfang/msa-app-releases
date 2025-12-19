# src/app/utils/performance_charts.py
"""
Performance Charts Utility

Creates visual charts for technician performance using matplotlib.
"""

import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt backend for PySide6 integration
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout
from datetime import datetime
from decimal import Decimal


class PerformanceChartWidget(QWidget):
    """Widget for displaying performance charts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6), facecolor='#1F2937')
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Set dark theme for charts
        plt.style.use('dark_background')
    
    def plot_tickets_trend(self, performance_history):
        """Plot tickets completed trend over time"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not performance_history:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='#9CA3AF')
            self.canvas.draw()
            return
        
        # Extract data
        months = [p.month.strftime('%b %Y') for p in reversed(performance_history)]
        tickets = [p.tickets_completed for p in reversed(performance_history)]
        
        # Create bar chart
        bars = ax.bar(months, tickets, color='#3B82F6', alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10, color='white')
        
        ax.set_xlabel('Month', fontsize=12, color='#E5E7EB')
        ax.set_ylabel('Tickets Completed', fontsize=12, color='#E5E7EB')
        ax.set_title('Tickets Completed Trend', fontsize=14, fontweight='bold', color='#F9FAFB')
        ax.tick_params(colors='#9CA3AF')
        ax.grid(True, alpha=0.2)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_revenue_trend(self, performance_history):
        """Plot revenue trend over time"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not performance_history:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='#9CA3AF')
            self.canvas.draw()
            return
        
        # Extract data
        months = [p.month.strftime('%b %Y') for p in reversed(performance_history)]
        revenue = [float(p.revenue_generated) for p in reversed(performance_history)]
        commission = [float(p.commission_earned) for p in reversed(performance_history)]
        
        # Create line chart
        ax.plot(months, revenue, marker='o', linewidth=2, markersize=8, 
               color='#10B981', label='Revenue')
        ax.plot(months, commission, marker='s', linewidth=2, markersize=8, 
               color='#8B5CF6', label='Commission')
        
        ax.set_xlabel('Month', fontsize=12, color='#E5E7EB')
        ax.set_ylabel('Amount ($)', fontsize=12, color='#E5E7EB')
        ax.set_title('Revenue & Commission Trend', fontsize=14, fontweight='bold', color='#F9FAFB')
        ax.tick_params(colors='#9CA3AF')
        ax.grid(True, alpha=0.2)
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_efficiency_trend(self, performance_history):
        """Plot efficiency score trend"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not performance_history:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='#9CA3AF')
            self.canvas.draw()
            return
        
        # Extract data
        months = [p.month.strftime('%b %Y') for p in reversed(performance_history)]
        efficiency = [float(p.efficiency_score) for p in reversed(performance_history)]
        avg_days = [float(p.avg_completion_days) for p in reversed(performance_history)]
        
        # Create dual-axis chart
        ax2 = ax.twinx()
        
        line1 = ax.plot(months, efficiency, marker='o', linewidth=2, markersize=8, 
                       color='#F59E0B', label='Efficiency Score')
        line2 = ax2.plot(months, avg_days, marker='s', linewidth=2, markersize=8, 
                        color='#EF4444', label='Avg Completion Days')
        
        ax.set_xlabel('Month', fontsize=12, color='#E5E7EB')
        ax.set_ylabel('Efficiency Score', fontsize=12, color='#F59E0B')
        ax2.set_ylabel('Avg Days', fontsize=12, color='#EF4444')
        ax.set_title('Efficiency Metrics', fontsize=14, fontweight='bold', color='#F9FAFB')
        
        ax.tick_params(colors='#9CA3AF')
        ax2.tick_params(colors='#9CA3AF')
        ax.grid(True, alpha=0.2)
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left', framealpha=0.9)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_compensation_breakdown(self, performance_data, base_salary):
        """Plot compensation breakdown pie chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not performance_data:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='#9CA3AF')
            self.canvas.draw()
            return
        
        # Calculate totals
        base = float(base_salary)
        commission = float(performance_data.commission_earned)
        bonuses = float(performance_data.bonuses_earned)
        
        # Create pie chart
        sizes = [base, commission, bonuses]
        labels = ['Base Salary', 'Commission', 'Bonuses']
        colors = ['#3B82F6', '#8B5CF6', '#F59E0B']
        explode = (0.05, 0.05, 0.05)
        
        # Filter out zero values
        filtered_data = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
        if filtered_data:
            sizes, labels, colors = zip(*filtered_data)
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90,
                                          explode=explode[:len(sizes)],
                                          textprops={'color': 'white', 'fontsize': 11})
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        ax.set_title('Compensation Breakdown', fontsize=14, fontweight='bold', color='#F9FAFB')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_team_comparison(self, comparison_data):
        """Plot team comparison horizontal bar chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not comparison_data:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14, color='#9CA3AF')
            self.canvas.draw()
            return
        
        # Extract top 10
        top_10 = comparison_data[:10]
        
        names = [d['technician_name'][:20] for d in top_10]  # Truncate long names
        tickets = [d['tickets_completed'] for d in top_10]
        
        # Create horizontal bar chart
        y_pos = range(len(names))
        bars = ax.barh(y_pos, tickets, color='#10B981', alpha=0.8)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{int(width)}',
                   ha='left', va='center', fontsize=10, color='white', 
                   fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()  # Top performer at top
        ax.set_xlabel('Tickets Completed', fontsize=12, color='#E5E7EB')
        ax.set_title('Team Performance Ranking', fontsize=14, fontweight='bold', color='#F9FAFB')
        ax.tick_params(colors='#9CA3AF')
        ax.grid(True, alpha=0.2, axis='x')
        
        self.figure.tight_layout()
        self.canvas.draw()
