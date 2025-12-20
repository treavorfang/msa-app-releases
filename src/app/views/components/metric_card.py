# src/app/views/components/metric_card.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class MetricCard(QFrame):
    """Modern metric card widget with background color like invoice cards"""
    
    def __init__(self, icon: str, value: str, label: str, growth: str = None, color: str = "#3B82F6", parent=None):
        super().__init__(parent)
        self.color = color
        self.setObjectName("metricCard")
        self._setup_ui(icon, value, label, growth)
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply card styling with background color"""
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: {self.color};
                border-radius: 8px;
            }}
        """)
    
    def _adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness by a factor"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Adjust brightness
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _setup_ui(self, icon: str, value: str, label: str, growth: str):
        """Setup the card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header: Icon + Label
        header = QHBoxLayout()
        layout.addLayout(header) # Add to parent layout first
        header.setSpacing(8)
        header.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; color: white; background: transparent; border: none;")
        header.addWidget(icon_label)
        
        # Label
        self.label_label = QLabel(label)
        self.label_label.setObjectName("metricLabel")
        self.label_label.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.9); font-weight: bold; background: transparent; border: none;")
        header.addWidget(self.label_label)
        
        header.addStretch()
        
        # Value and Growth on same line
        value_row = QHBoxLayout()
        layout.addLayout(value_row) # Add to parent layout first
        value_row.setSpacing(8)
        value_row.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setStyleSheet("font-size: 22px; color: white; font-weight: bold; background: transparent; border: none;")
        value_row.addWidget(self.value_label)
        
        value_row.addStretch()  # Push growth to the right
        
        # Growth indicator (if provided) - on same line as value
        if growth:
            self.growth_label = QLabel(growth)
            self.growth_label.setObjectName("metricGrowth")
            
            # Determine color based on growth direction
            if growth.startswith("↑") or growth.startswith("+"):
                growth_color = "#FDE047"  # Bright yellow
            elif growth.startswith("↓") or growth.startswith("-"):
                growth_color = "#FCA5A5"  # Light red/pink
            else:
                growth_color = "rgba(255, 255, 255, 0.9)"
            
            self.growth_label.setStyleSheet(f"color: {growth_color}; font-weight: 700; font-size: 12px; background: transparent; border: none;")
            value_row.addWidget(self.growth_label)
            
    def update_value(self, value: str):
        """Update the metric value"""
        self.value_label.setText(value)
    
    def update_growth(self, growth: str):
        """Update the growth indicator"""
        if hasattr(self, 'growth_label'):
            self.growth_label.setText(growth)
            
            # Update color
            if growth.startswith("↑") or growth.startswith("+"):
                growth_color = "#FDE047"  # Bright yellow
            elif growth.startswith("↓") or growth.startswith("-"):
                growth_color = "#FCA5A5"  # Light red/pink
            else:
                growth_color = "rgba(255, 255, 255, 0.9)"
            
            self.growth_label.setStyleSheet(f"color: {growth_color}; font-weight: 700; font-size: 12px; background: transparent; border: none;")
    def update_label(self, label: str):
        """Update the metric label"""
        if hasattr(self, 'label_label'):
            self.label_label.setText(label)
        elif hasattr(self, 't_label'): # Fallback for other MetricCard implementations if mixed
            self.t_label.setText(label)
