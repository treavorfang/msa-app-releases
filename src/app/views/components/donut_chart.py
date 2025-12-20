"""
Donut Chart Widget - Custom QPainter implementation
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolTip, QPushButton
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QPoint, QRectF

from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class DonutChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.data = []  # List of dicts: {'name': str, 'value': float, 'color': str}
        self.total = 0.0
        self.hover_index = -1
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: transparent;")
        self.lm = language_manager

    def set_data(self, data, center_text="EXPENSES"):
        """
        Set data for the chart.
        data: List of dicts with keys 'name', 'amount', 'color'
        """
        self.data = data
        self.total = sum(d['amount'] for d in data)
        self.center_text = center_text
        self.update()
    
    def set_colors(self, hole_color, text_color):
        """Set colors for the chart elements"""
        self.hole_color = hole_color
        self.text_color = text_color
        self.update()

    def wheelEvent(self, event):
        """Pass wheel events to parent to enable scrolling over chart"""
        if self.parent():
            self.parent().wheelEvent(event)
        else:
            super().wheelEvent(event)

    def paintEvent(self, event):
        if not self.data or self.total == 0:
             painter = QPainter(self)
             text_color = getattr(self, 'text_color', "#808080")
             painter.setPen(QColor(text_color))
             text = self.lm.get("Financial.no_data", "No Data")
             painter.drawText(self.rect(), Qt.AlignCenter, text)
             return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Define chart area (square)
        side = min(width, height) - 20
        chart_rect = QRectF((width - side)/2, (height - side)/2, side, side)
        
        start_angle = 90 * 16 # Start at top
        
        for i, item in enumerate(self.data):
            value = item['amount']
            if value == 0: continue
            
            # Calculate span angle
            percent = value / self.total
            span_angle = -percent * 360 * 16
            
            # Setup Pen/Brush
            color = QColor(item['color'])
            if i == self.hover_index:
                color = color.lighter(120)
                
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            # Draw Pie Slice
            painter.drawPie(chart_rect, int(start_angle), int(span_angle))
            
            start_angle += span_angle
            
        # Draw Center Circle (to make it a Donut)
        center_hole_ratio = 0.6
        center_rect = QRectF(
            chart_rect.center().x() - (side * center_hole_ratio)/2,
            chart_rect.center().y() - (side * center_hole_ratio)/2,
            side * center_hole_ratio,
            side * center_hole_ratio
        )
        
        # Use configured hole color or default to match card background if known, else dark
        hole_color = getattr(self, 'hole_color', "#2D2D2D")
        painter.setBrush(QBrush(QColor(hole_color)))
        painter.drawEllipse(center_rect)
        
        # Draw Total in Center
        text_color = getattr(self, 'text_color', "white")
        painter.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        # Dynamic font size
        font.setPointSize(max(10, int(side * 0.08))) 
        painter.setFont(font)
        
        if hasattr(self, 'center_text'):
             painter.drawText(center_rect, Qt.AlignCenter, self.center_text)
        

class FinancialBreakdownCard(QWidget):
    """
    Composite widget with Donut Chart and Income/Expense Toggle
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardMain")
        self.setMinimumHeight(350) # Increased height for vertical layout
        
        self.expense_data = []
        self.income_data = []
        self.current_mode = "expense" # 'income' or 'expense'
        self.lm = language_manager
        self.cf = currency_formatter
        
        main_layout = QVBoxLayout(self)
        
        # --- Header with Toggle ---
        header_layout = QHBoxLayout()
        
        title_text = self.lm.get("Financial.breakdown", "Breakdown")
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        
        # Custom Toggle Buttons
        expense_text = self.lm.get("Financial.type_expense", "Expense")
        self.btn_expense = QPushButton(expense_text)
        self.btn_expense.setCheckable(True)
        self.btn_expense.setChecked(True)
        self.btn_expense.setCursor(Qt.PointingHandCursor)
        self.btn_expense.clicked.connect(self._show_expense)
        
        income_text = self.lm.get("Financial.type_income", "Income")
        self.btn_income = QPushButton(income_text)
        self.btn_income.setCheckable(True)
        self.btn_income.setCursor(Qt.PointingHandCursor)
        self.btn_income.clicked.connect(self._show_income)
        
        # Base Toggle Style
        self.toggle_style = """
            QPushButton {
                border: none;
                padding: 5px 12px;
                font-weight: bold;
            }
        """
        
        header_layout.addWidget(self.btn_expense)
        header_layout.addWidget(self.btn_income)
        
        main_layout.addLayout(header_layout)
        
        # Content Layout (Vertical now)
        content_layout = QVBoxLayout()
        
        # Chart
        self.chart = DonutChartWidget()
        content_layout.addWidget(self.chart, stretch=1)
        
        # Legend (Below chart)
        self.legend_container = QWidget()
        self.legend_layout = QVBoxLayout(self.legend_container)
        self.legend_layout.setContentsMargins(10, 0, 10, 10)
        self.legend_layout.setSpacing(8)
        content_layout.addWidget(self.legend_container)
        
        main_layout.addLayout(content_layout)
        
        # Initialize with Dark Theme (default)
        self.update_theme('dark')

    def set_data(self, expense_data, income_data):
        self.expense_data = expense_data
        self.income_data = income_data
        self._update_view()
    
    def wheelEvent(self, event):
        """Pass wheel events to parent to enable scrolling over chart"""
        if self.parent():
            self.parent().wheelEvent(event)
        else:
            super().wheelEvent(event)
        
    def _show_expense(self):
        self.current_mode = "expense"
        self.btn_expense.setChecked(True)
        self.btn_income.setChecked(False)
        self._update_view()
        
    def _show_income(self):
        self.current_mode = "income"
        self.btn_income.setChecked(True)
        self.btn_expense.setChecked(False)
        self._update_view()
        
    def update_theme(self, theme_name):
        """Update colors based on theme"""
        self.current_theme = theme_name
        
        if theme_name == 'dark':
            # Dark Theme Colors
            bg_color = "#2D2D2D"
            text_color = "white"
            subtext_color = "#A0A0A0"
            toggle_bg = "#374151"
            toggle_hover = "#4B5563"
            toggle_text = "#9CA3AF"
            
            # Chart colors
            self.chart.set_colors(bg_color, text_color)
            
        else:
            # Light Theme Colors
            bg_color = "#FFFFFF"
            text_color = "#1F2937"
            subtext_color = "#6B7280"
            toggle_bg = "#E5E7EB"
            toggle_hover = "#D1D5DB"
            toggle_text = "#6B7280"
            
            # Chart colors
            self.chart.set_colors(bg_color, text_color)
            
        # Apply Stylesheet
        self.setStyleSheet(f"""
            QWidget#cardMain {{ background-color: {bg_color}; border-radius: 12px; }}
            QLabel {{ color: {text_color}; border: none; }}
        """)
        
        # Update Toggle Buttons Style
        common_style = self.toggle_style + f"""
            QPushButton {{
                background-color: {toggle_bg};
                color: {toggle_text};
            }}
            QPushButton:hover {{
                background-color: {toggle_hover};
            }}
            QPushButton:checked {{
                color: white;
            }}
        """
        
        self.btn_expense.setStyleSheet(common_style + """
            QPushButton:checked { background-color: #EF4444; } 
            QPushButton { border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
        """)
        
        self.btn_income.setStyleSheet(common_style + """
            QPushButton:checked { background-color: #10B981; }
            QPushButton { border-top-right-radius: 6px; border-bottom-right-radius: 6px; margin-left: -1px; }
        """)
        
        # Store for legend updates
        self.subtext_color = subtext_color
        
        # Refresh Logic (re-render legend with new colors)
        self._update_view()

    def _update_view(self):
        data = self.expense_data if self.current_mode == "expense" else self.income_data
        
        # Localized Center Text
        if self.current_mode == "expense":
            center_text = self.lm.get("Financial.expense", "EXPENSES").upper()
        else:
            center_text = self.lm.get("Financial.income", "INCOME").upper()
            
        self.chart.set_data(data, center_text)
        
        # Clear legend
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    subchild = child.layout().takeAt(0)
                    if subchild.widget():
                        subchild.widget().deleteLater()
                
        # Populate Legend
        sorted_data = sorted(data, key=lambda x: x['amount'], reverse=True)[:5] # Top 5
        
        subtext_color = getattr(self, 'subtext_color', "#A0A0A0")
        
        for item in sorted_data:
            row = QHBoxLayout()
            
            color_lbl = QLabel()
            color_lbl.setFixedSize(12, 12)
            color_lbl.setStyleSheet(f"background-color: {item['color']}; border-radius: 6px;")
            
            # Truncate long names
            name = item['name']
            if len(name) > 20: name = name[:18] + ".."
            text_lbl = QLabel(name)
            # Inherits color from parent stylesheet (set in update_theme)
            text_lbl.setToolTip(item['name'])
            
            # Formatted Amount
            formatted_amt = self.cf.format(item['amount'])
            amt_lbl = QLabel(formatted_amt)
            amt_lbl.setStyleSheet(f"color: {subtext_color};")
            
            row.addWidget(color_lbl)
            row.addWidget(text_lbl)
            row.addStretch()
            row.addWidget(amt_lbl)
            
            self.legend_layout.addLayout(row)

# Backward compatibility alias
class ExpenseBreakdownCard(FinancialBreakdownCard):
    pass

