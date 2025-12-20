from PySide6.QtWidgets import QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QColor, QFont, QPainter, QLinearGradient, QPen, QPainterPath, QPalette

from PySide6.QtCore import QSettings
from config.config import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION, THEME_SETTING_KEY


def is_dark_theme(widget):
    """Check if the current theme is dark based on QSettings."""
    try:
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        theme = settings.value(THEME_SETTING_KEY, "dark") # Default to dark
        # print(f"DEBUG: is_dark_theme check. Theme value: {theme}")
        # Handle potential string wrapping or type issues
        if isinstance(theme, str):
             theme = theme.lower().strip('"').strip("'")
        
        is_dark = (theme == "dark")
        # print(f"DEBUG: is_dark_theme result: {is_dark}")
        return is_dark
    except Exception:
        return True # Default to dark on error




# --- CUSTOM WAVE CHART WIDGET ---
class WaveChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        # Default Data
        self.data_points = [0.4, 0.3, 0.6, 0.5, 0.9, 0.6, 0.8] 
        self.labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.currency_formatter = lambda x: f"${x/1000:.1f}k"
        self.max_value = 1000.0
        self._forced_dark_mode = None

    def set_theme_mode(self, is_dark):
        """Force a specific theme mode"""
        self._forced_dark_mode = is_dark
        self.update()

    def set_data(self, data_points, labels, max_val=None):
        """
        Set data for the chart.
        data_points: list of float values (absolute values)
        labels: list of strings
        """
        self.data_points = data_points
        self.labels = labels
        if max_val:
            self.max_value = max_val
        elif data_points:
            self.max_value = max(data_points) * 1.2 # Add headroom
            if self.max_value == 0: self.max_value = 1.0
        
        self.update()

    def set_formatter(self, formatter):
        self.currency_formatter = formatter

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Theme Colors
        # Check forced mode first
        if getattr(self, '_forced_dark_mode', None) is not None:
             dark_mode = self._forced_dark_mode
        else:
             dark_mode = is_dark_theme(self)
        
        if dark_mode:
            grid_color = QColor(255, 255, 255, 20)
            text_color = QColor(156, 163, 175) # Gray 400
            dot_bg = QColor(17, 24, 39) # Gray 900
            tooltip_bg = QColor(55, 65, 81) # Gray 700
            tooltip_text = QColor(255, 255, 255)
            highlight_dot = QColor(255, 255, 255)
        else:
            grid_color = QColor(0, 0, 0, 20)
            text_color = QColor(75, 85, 99) # Gray 600
            dot_bg = QColor(255, 255, 255) # White
            tooltip_bg = QColor(229, 231, 235) # Gray 200
            tooltip_text = QColor(17, 24, 39) # Gray 900
            highlight_dot = QColor(37, 99, 235) # Blue 600

        # Dimensions
        w = self.width()
        h = self.height()
        padding_btm = 30
        padding_left = 50
        padding_right = 20
        padding_top = 20
        
        graph_w = w - padding_left - padding_right
        graph_h = h - padding_top - padding_btm
        
        # Normalize data to 0.0 - 1.0
        normalized_data = []
        if self.max_value > 0:
            normalized_data = [min(1.0, max(0.0, val / self.max_value)) for val in self.data_points]
        else:
            normalized_data = [0.0] * len(self.data_points)

        # 1. Draw Grid Lines & Y-Axis Labels
        painter.setPen(QPen(grid_color, 1, Qt.SolidLine))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        num_grid_lines = 5
        for i in range(num_grid_lines + 1):
            y_ratio = i / num_grid_lines
            y = padding_top + (y_ratio * graph_h)
            
            # Grid Line
            painter.drawLine(padding_left, int(y), w - padding_right, int(y))
            
            # Label
            val = self.max_value * (1.0 - y_ratio)
            label_text = self.currency_formatter(val)
            painter.setPen(text_color)
            painter.drawText(0, int(y) - 10, padding_left - 5, 20, Qt.AlignRight | Qt.AlignVCenter, label_text)
            painter.setPen(QPen(grid_color, 1, Qt.SolidLine)) # Reset pen for grid

        if not normalized_data:
            return

        # 2. Prepare Path Points
        if len(normalized_data) > 1:
            step_x = graph_w / (len(normalized_data) - 1)
        else:
            step_x = graph_w

        points = []
        for i, val in enumerate(normalized_data):
            px = padding_left + (i * step_x)
            # Invert Y because 0 is top
            # 1.0 val means top (padding_top), 0.0 means bottom (h - padding_btm)
            py = (h - padding_btm) - (val * graph_h)
            points.append(QPointF(px, py))
            
        # 3. Create Smooth Curve (Cubic Spline)
        path = QPainterPath()
        if points:
            path.moveTo(points[0])
            
            # Simple smoothing algorithm
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                
                # Control points for smooth curve
                ctrl1_x = p1.x() + step_x * 0.5
                ctrl1_y = p1.y()
                ctrl2_x = p2.x() - step_x * 0.5
                ctrl2_y = p2.y()
                
                path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, p2.x(), p2.y())
            
            # 4. Draw Gradient Area (Under the curve)
            fill_path = QPainterPath(path)
            # Close the path to bottom corners
            fill_path.lineTo(points[-1].x(), h - padding_btm)
            fill_path.lineTo(points[0].x(), h - padding_btm)
            fill_path.closeSubpath()
            
            grad = QLinearGradient(0, padding_top, 0, h - padding_btm)
            grad.setColorAt(0, QColor(59, 130, 246, 120)) # Blue top
            grad.setColorAt(1, QColor(59, 130, 246, 0))   # Transparent bottom
            
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawPath(fill_path)
            
            # 5. Draw Line Stroke
            stroke_pen = QPen(QColor(96, 165, 250), 3) # Blue 400
            stroke_pen.setCapStyle(Qt.RoundCap)
            painter.strokePath(path, stroke_pen)
            
            # 6. Draw Points & Tooltips
            # Find index of max value for highlighting
            max_idx = -1
            max_val_in_data = -1
            if self.data_points:
                max_val_in_data = max(self.data_points)
                if max_val_in_data > 0:
                    max_idx = self.data_points.index(max_val_in_data)

            for i, p in enumerate(points):
                # Draw X-Axis Label
                if i < len(self.labels):
                    painter.setPen(text_color)
                    painter.drawText(int(p.x()) - 30, h - padding_btm + 5, 60, 20, Qt.AlignCenter, self.labels[i])
                
                # Draw Dot
                painter.setPen(QPen(QColor(96, 165, 250), 2))
                painter.setBrush(dot_bg)
                
                # Highlight max value
                if i == max_idx:
                    # Glow effect / Bigger dot
                    painter.setBrush(highlight_dot)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(p, 6, 6)
                    
                    # Draw Label
                    label_text = self.currency_formatter(self.data_points[i])
                    
                    # Label Box
                    tip_rect_w = 70
                    tip_rect_h = 25
                    tip_x = int(p.x()) - tip_rect_w // 2
                    tip_y = int(p.y()) - 35
                    
                    # Ensure label stays within bounds (horizontal)
                    if tip_x < 0: tip_x = 0
                    if tip_x + tip_rect_w > w: tip_x = w - tip_rect_w
                    
                    painter.setBrush(tooltip_bg)
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(tip_x, tip_y, tip_rect_w, tip_rect_h, 4, 4)
                    
                    painter.setPen(tooltip_text)
                    painter.drawText(tip_x, tip_y, tip_rect_w, tip_rect_h, Qt.AlignCenter, label_text)
                else:
                    painter.setPen(QPen(QColor(96, 165, 250), 2)) # Restore pen ring
                    painter.drawEllipse(p, 4, 4)

class DonutWidget(QWidget):
    def __init__(self, value, color="#3B82F6"):
        super().__init__()
        self.value = value # 0.75 for 75%
        self.active_color = QColor(color)
        self.setStyleSheet("background: transparent;")
        self._forced_dark_mode = None
        
    def set_theme_mode(self, is_dark):
        """Force a specific theme mode"""
        self._forced_dark_mode = is_dark
        self.update()

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(4, 4, -4, -4)
        
        # Determine background ring color based on theme
        if getattr(self, '_forced_dark_mode', None) is not None:
             dark_mode = self._forced_dark_mode
        else:
             dark_mode = is_dark_theme(self)
        
        bg_ring_color = QColor(55, 65, 81) if dark_mode else QColor(229, 231, 235) # Gray 700 vs Gray 200
        
        # Draw Background Circle (Gray)
        pen_bg = QPen(bg_ring_color, 8)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)
        
        # Draw Value Arc
        pen_val = QPen(self.active_color, 8)
        pen_val.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_val)
        
        # Qt Angles are 1/16th of a degree. Start at 90 (top) which is 90*16
        start_angle = 90 * 16
        span_angle = - (self.value * 360 * 16) # Negative for clockwise
        
        painter.drawArc(rect, start_angle, int(span_angle))

# --- GENERIC DASHBOARD CARD ---
class DashboardCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chartCard")
        self._last_mode = None
        self._forced_dark_mode = None
        self.update_style()
        
    def set_theme_mode(self, is_dark):
        """Force a specific theme mode"""
        self._forced_dark_mode = is_dark
        self.update_style()

    def changeEvent(self, event):
        """Handle theme changes"""
        if event.type() == QEvent.PaletteChange:
            self.update_style()
        super().changeEvent(event)

    def update_style(self):
        """Update styles based on current theme"""
        # Prevent recursion and unnecessary updates
        if getattr(self, '_forced_dark_mode', None) is not None:
             dark_mode = self._forced_dark_mode
        else:
             dark_mode = is_dark_theme(self)
             
        if getattr(self, '_last_mode', None) == dark_mode:
            return
        self._last_mode = dark_mode
        
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        text_color = "white" if dark_mode else "#111827"
        
        self.setStyleSheet(f"""
            QFrame#chartCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
            QLabel {{
                color: {text_color};
                border: none;
                background: transparent;
            }}
        """)

# --- METRIC CARD WIDGET ---
class MetricCard(QFrame):
    def __init__(self, title, value, subtext, color="#1F2937", show_donut=False, donut_value=0.0, is_dark_mode=None):
        super().__init__()
        self.setObjectName("metricCard")
        self._last_mode = None
        self._forced_dark_mode = is_dark_mode
        # Store params for updates
        self.show_donut = show_donut
        self.donut_value = donut_value 
        self.donut_color_hex = "#3B82F6" # Default
        if "Completed" in title or "Rate" in title: self.donut_color_hex = "#8B5CF6" 
        elif "Revenue" in title: self.donut_color_hex = "#10B981" 
        
        # Setup UI
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Left Text Container
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(text_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        self.t_label = QLabel(title)
        self.v_label = QLabel(value)
        self.s_label = QLabel(subtext)
        
        layout.addWidget(self.t_label)
        layout.addWidget(self.v_label)
        layout.addWidget(self.s_label)
        layout.addStretch()
        
        main_layout.addWidget(text_container)
        
        # Donut Chart (Right Side)
        self.donut = None
        if self.show_donut:
            self.donut = DonutWidget(self.donut_value, color=self.donut_color_hex)
            self.donut.setFixedSize(70, 70)
            main_layout.addWidget(self.donut)

        # Initial style update
        self.update_style()

    def changeEvent(self, event):
        """Handle theme changes"""
        if event.type() == QEvent.PaletteChange:
            self.update_style()
        super().changeEvent(event)

    def update_style(self):
        """Update styles based on current theme"""
        # Force fresh check logic
        if self._forced_dark_mode is not None:
            dark_mode = self._forced_dark_mode
        else:
            dark_mode = is_dark_theme(self)
        
        # Still utilize cache to prevent flickering if called repeatedly
        if getattr(self, '_last_mode', None) == dark_mode:
            return
        self._last_mode = dark_mode
        
        # Propagate to children
        if self.donut:
            self.donut.set_theme_mode(dark_mode)
        
        # Colors
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        title_color = "#9CA3AF" if dark_mode else "#6B7280"
        value_color = "white" if dark_mode else "#111827"
        
        # print(f"DEBUG: MetricCard.update_style (forced={self._forced_dark_mode}) -> dark_mode={dark_mode}, bg={bg_color}")

        # Apply style to self (QFrame) directly without ID selector to ensure application
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: {bg_color} !important;
                border-radius: 16px;
                border: 1px solid {border_color};
            }}
        """)
        
        # Update labels (force specific colors to override generic QFrame color)
        self.t_label.setStyleSheet(f"color: {title_color}; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        self.v_label.setStyleSheet(f"color: {value_color}; font-size: 24px; font-weight: bold; border: none; margin-top: 5px; background: transparent;")
        
        # Re-apply subtext color
        subtext = self.s_label.text()
        s_color = "#10B981" if "↑" in subtext or "+" in subtext else "#F59E0B" if "—" in subtext else "#EF4444" 
        self.s_label.setStyleSheet(f"color: {s_color}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        
        # Update donut if exists
        if self.donut:
            self.donut.update()

            
    def update_data(self, value, subtext, donut_val=None):
        self.v_label.setText(value)
        self.s_label.setText(subtext)
        
        # Update color based on new subtext
        s_color = "#10B981" if "↑" in subtext or "+" in subtext else "#F59E0B" if "—" in subtext else "#EF4444" 
        self.s_label.setStyleSheet(f"color: {s_color}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        
        if self.donut and donut_val is not None:
            self.donut.set_value(donut_val)
