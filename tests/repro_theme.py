
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/app')))

from PySide6.QtWidgets import QApplication
from views.components.new_dashboard_widgets import MetricCard

def test_metric_card_dark_mode():
    app = QApplication(sys.argv)
    
    # Test 1: Explicit Dark Mode
    print("Testing Explicit Dark Mode...")
    card_dark = MetricCard("Test", "123", "Growth", is_dark_mode=True)
    style_dark = card_dark.styleSheet()
    
    if "#1F2937" in style_dark:
        print("PASS: Dark mode background color found.")
    else:
        print(f"FAIL: Dark mode background color NOT found. Style: {style_dark}")

    # Test 2: Explicit Light Mode
    print("\nTesting Explicit Light Mode...")
    card_light = MetricCard("Test", "123", "Growth", is_dark_mode=False)
    style_light = card_light.styleSheet()
    
    if "#FFFFFF" in style_light:
        print("PASS: Light mode background color found.")
    else:
        print(f"FAIL: Light mode background color NOT found. Style: {style_light}")

if __name__ == "__main__":
    test_metric_card_dark_mode()
