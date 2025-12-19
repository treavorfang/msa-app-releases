

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout)
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QLinearGradient, QPen, QPainterPath, QBrush

# --- CUSTOM WAVE CHART WIDGET ---
class WaveChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        # Simulated Data: 7 Days (Mon-Sun)
        # Values between 0.0 and 1.0 representing height percentage
        self.data_points = [0.4, 0.3, 0.6, 0.5, 0.9, 0.6, 0.8] 
        self.labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        w = self.width()
        h = self.height()
        padding_btm = 30
        padding_left = 40
        padding_right = 20
        padding_top = 20
        
        graph_w = w - padding_left - padding_right
        graph_h = h - padding_top - padding_btm
        
        # 1. Draw Grid Lines & Y-Axis Labels
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1, Qt.SolidLine))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        num_grid_lines = 5
        for i in range(num_grid_lines + 1):
            y_ratio = i / num_grid_lines
            y = padding_top + (y_ratio * graph_h)
            
            # Grid Line
            painter.drawLine(padding_left, int(y), w - padding_right, int(y))
            
            # Label ($250k, $200k...)
            val = int(300 - (300 * y_ratio)) # Mock scale 0-300k
            label_text = f"${val}k"
            painter.drawText(0, int(y) - 5, padding_left - 5, 20, Qt.AlignRight | Qt.AlignVCenter, label_text)

        # 2. Prepare Path Points
        step_x = graph_w / (len(self.data_points) - 1)
        points = []
        for i, val in enumerate(self.data_points):
            px = padding_left + (i * step_x)
            # Invert Y because 0 is top
            # 1.0 val means top (padding_top), 0.0 means bottom (h - padding_btm)
            py = (h - padding_btm) - (val * graph_h)
            points.append(QPointF(px, py))
            
        # 3. Create Smooth Curve (Cubic Spline)
        path = QPainterPath()
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
        painter.setBrush(QColor(17, 24, 39)) # Back ground color for circle center
        painter.setPen(QPen(QColor(96, 165, 250), 2))
        
        for i, p in enumerate(points):
            # Draw X-Axis Label
            painter.setPen(QColor(156, 163, 175))
            painter.drawText(int(p.x()) - 20, h - padding_btm + 5, 40, 20, Qt.AlignCenter, self.labels[i])
            
            # Draw Dot
            painter.setPen(QPen(QColor(96, 165, 250), 2))
            painter.setBrush(QColor(17, 24, 39))
            painter.drawEllipse(p, 4, 4)
            
            # Draw "Active" point highlight (fake, say index 4)
            if i == 4:
                # Glow effect
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(p, 6, 6)
                
                # Draw Tooltip
                tip_rect_w = 60
                tip_rect_h = 25
                tip_x = int(p.x()) - tip_rect_w // 2
                tip_y = int(p.y()) - 35
                
                painter.setBrush(QColor(55, 65, 81)) # Gray 700
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tip_x, tip_y, tip_rect_w, tip_rect_h, 4, 4)
                
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(tip_x, tip_y, tip_rect_w, tip_rect_h, Qt.AlignCenter, "$250k")


# --- METRIC CARD WIDGET ---
class MetricCard(QFrame):
    def __init__(self, title, value, subtext, color="#1F2937", show_donut=False, donut_value=0.7):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 16px;
                border: 1px solid #374151;
            }}
        """)
        self.show_donut = show_donut
        self.donut_value = donut_value # 0.0 to 1.0
        
        # Horizontal Layout to support Donut on the right
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Left Text Container
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(text_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #9CA3AF; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        
        v_label = QLabel(value)
        v_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; border: none; margin-top: 5px; background: transparent;")
        
        s_label = QLabel(subtext)
        s_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold; border: none; background: transparent;") # Green text
        
        layout.addWidget(t_label)
        layout.addWidget(v_label)
        layout.addWidget(s_label)
        layout.addStretch()
        
        main_layout.addWidget(text_container)
        
        # Donut Chart (Right Side)
        if self.show_donut:
            donut = DonutWidget(self.donut_value)
            donut.setFixedSize(80, 80)
            main_layout.addWidget(donut)
            
class DonutWidget(QWidget):
    def __init__(self, value):
        super().__init__()
        self.value = value # 0.75 for 75%
        self.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(4, 4, -4, -4)
        
        # Draw Background Circle (Gray)
        pen_bg = QPen(QColor(55, 65, 81), 8)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)
        
        # Draw Value Arc (Blue)
        pen_val = QPen(QColor(59, 130, 246), 8)
        pen_val.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_val)
        
        # Qt Angles are 1/16th of a degree. Start at 90 (top) which is 90*16
        start_angle = 90 * 16
        span_angle = - (self.value * 360 * 16) # Negative for clockwise
        
        painter.drawArc(rect, start_angle, span_angle)

# --- SIDEBAR BUTTON ---
class SidebarButton(QPushButton):
    def __init__(self, text, icon_name="home", active=False):
        super().__init__(text)
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        
        base_style = """
            QPushButton {
                text-align: left;
                padding-left: 20px;
                background-color: transparent;
                color: #9CA3AF;
                border-radius: 10px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #374151;
                color: white;
            }
        """
        
        active_style = """
            QPushButton:checked {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
            }
        """
        self.setStyleSheet(base_style + active_style)

# --- MODERN DASHBOARD WINDOW ---
class ModernDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSA Modern Dashboard")
        self.resize(1200, 800)
        
        # Main Container (Window Background)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: #111827;") # Very Dark Slate
        self.setCentralWidget(self.central_widget)
        
        # Root Layout (Sidebar | Main)
        root_layout = QHBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # === 1. SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #1F2937; border-right: 1px solid #374151;")
        
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(20, 30, 20, 30)
        side_layout.setSpacing(10)
        
        # Logo
        logo = QLabel("MSA")
        logo.setStyleSheet("color: #3B82F6; font-size: 28px; font-weight: 800; border: none; font-family: 'Arial'; background: transparent;")
        side_layout.addWidget(logo)
        side_layout.addSpacing(30)
        
        # Nav Items
        nav_items = ["Dashboard", "Tickets", "Invoices", "Reports", "Customers", "Technicians", "Settings"]
        for idx, item in enumerate(nav_items):
            btn = SidebarButton(item, active=(idx==0))
            side_layout.addWidget(btn)
            
        side_layout.addStretch()
        
        # User Profile at Bottom
        user_row = QHBoxLayout()
        avatar = QLabel("AD") # Avatar placeholder
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 16px; font-weight: bold; font-size: 12px;")
        
        uname = QLabel("Admin User")
        uname.setStyleSheet("color: white; font-size: 14px; border: none; background: transparent;")
        
        user_row.addWidget(avatar)
        user_row.addWidget(uname)
        user_row.addStretch()
        
        side_layout.addLayout(user_row)
        
        root_layout.addWidget(sidebar)
        
        # === 2. MAIN CONTENT ===
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #111827;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # -- Header --
        header_row = QHBoxLayout()
        title = QLabel("Dashboard Overview")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        
        # Notif Icon
        notif = QPushButton("🔔")
        notif.setFixedSize(40, 40)
        notif.setStyleSheet("""
            QPushButton { background-color: #1F2937; border-radius: 20px; border: 1px solid #374151; font-size: 18px; color: white; }
            QPushButton:hover { background-color: #374151; }
        """)
        
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(notif)
        
        main_layout.addLayout(header_row)
        
        # -- Top Metrics Row --
        metrics_grid = QHBoxLayout()
        metrics_grid.setSpacing(20)
        
        c1 = MetricCard("Total Revenue", "$1,245,000", "+8.5% from last month")
        c2 = MetricCard("Active Tickets", "42", "+12 New today", show_donut=True, donut_value=0.65)
        c3 = MetricCard("Technicians", "15", "12 Active now")
        
        metrics_grid.addWidget(c1)
        metrics_grid.addWidget(c2)
        metrics_grid.addWidget(c3)
        
        main_layout.addLayout(metrics_grid)
        
        # -- Chart Section --
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border-radius: 20px;
                border: 1px solid #374151;
            }
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(25, 25, 25, 25)
        
        chart_header = QHBoxLayout()
        c_title = QLabel("Weekly Sales")
        c_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        
        c_dropdown = QPushButton("This Week ▼")
        c_dropdown.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #9CA3AF;
                padding: 5px 15px;
                border-radius: 8px;
                border: 1px solid #374151;
                font-size: 12px;
            }
        """)
        
        chart_header.addWidget(c_title)
        chart_header.addStretch()
        chart_header.addWidget(c_dropdown)
        
        # INSERT CUSTOM CHART HERE
        chart_widget = WaveChart()
        chart_widget.setMinimumHeight(400)
        
        chart_layout.addLayout(chart_header)
        chart_layout.addSpacing(20)
        chart_layout.addWidget(chart_widget)
        
        main_layout.addWidget(chart_frame)
        main_layout.addStretch()
        
        root_layout.addWidget(main_content)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernDashboard()
    window.show()
    sys.exit(app.exec())
