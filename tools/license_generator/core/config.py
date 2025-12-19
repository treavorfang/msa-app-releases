"""
Configuration and path management for License Generator
"""
import sys
import os
import platform

# Determine paths
if getattr(sys, 'frozen', False):
    # Running in a bundle
    BASE_EXEC_DIR = os.path.dirname(sys.executable)
    
    # Determine RESOURCE_DIR (read-only bundled assets)
    if hasattr(sys, '_MEIPASS'):
        # Onefile mode
        RESOURCE_DIR = sys._MEIPASS # type: ignore
    else:
        # Onedir mode
        RESOURCE_DIR = BASE_EXEC_DIR
        # Check for _internal directory (PyInstaller v6+)
        if os.path.exists(os.path.join(BASE_EXEC_DIR, '_internal')):
            RESOURCE_DIR = os.path.join(BASE_EXEC_DIR, '_internal')
            
    # Determine PERSISTENT_DIR (writeable user data)
    APP_NAME = "MSALicenseMonitor"
    if platform.system() == 'Darwin':
        PERSISTENT_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    elif platform.system() == 'Windows':
        PERSISTENT_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser("~")), APP_NAME)
    else:
        PERSISTENT_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME)
    
    if not os.path.exists(PERSISTENT_DIR):
        os.makedirs(PERSISTENT_DIR, exist_ok=True)
        
    # Alias SCRIPT_DIR to BASE_EXEC_DIR for compatibility
    SCRIPT_DIR = BASE_EXEC_DIR

else:
    # Running from source
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PERSISTENT_DIR = SCRIPT_DIR
    RESOURCE_DIR = SCRIPT_DIR
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# App Name (Global)
APP_NAME = "MSA License Monitor"



# Logo might be bundled
LOGO_PATH = os.path.join(RESOURCE_DIR, "ui", "logo.png") 

# Fallback for Dev Environment (Logo)
if not os.path.exists(LOGO_PATH) and not getattr(sys, 'frozen', False):
    dev_logo_path = os.path.join(PROJECT_ROOT, "src", "app", "static", "icons", "logo.png")
    if os.path.exists(dev_logo_path):
        LOGO_PATH = dev_logo_path


# License duration options (in days)
DURATION_OPTIONS = [
    ("1 Month", 30),
    ("3 Months", 90),
    ("6 Months", 180),
    ("1 Year", 365),
    ("Lifetime", -1),  # -1 indicates lifetime
]

# Default duration index
DEFAULT_DURATION_INDEX = 3  # 1 Year

# Pricing Configuration
# USD Base: $5/mo
# MMK Base: 20,000 Ks/mo (at 1 USD = 4000 MMK)

CURRENCY_OPTIONS = ["MMK", "USD"]

PRICING_MAP_MMK = {
    "1 Month": 20000,
    "3 Months": 60000,
    "6 Months": 120000,
    "1 Year": 200000,       # Discounted
    "Lifetime": 600000
}

PRICING_MAP_USD = {
    "1 Month": 5,
    "3 Months": 15,
    "6 Months": 30,
    "1 Year": 50,           # Discounted (save $10)
    "Lifetime": 150
}

# Lifetime expiry date
LIFETIME_EXPIRY = "9999-12-31"

# Expiring soon threshold (days)
EXPIRING_SOON_DAYS = 30

# Payment status options
PAYMENT_STATUS_OPTIONS = [
    "Paid",
    "Pending",
    "Partial",
    "Refunded",
]

# Payment method options
PAYMENT_METHOD_OPTIONS = [
    "Cash",
    "Bank Transfer",
    "Credit Card",
    "PayPal",
    "Cryptocurrency",
    "Other",
]


# Company Information (Used in Invoices)
COMPANY_NAME = "World Lock Inc"
COMPANY_SUBTITLE = "Mobile Service POS System"
COMPANY_CONTACT_PHONE = "📱 +959259282400 | +95968098642"
COMPANY_CONTACT_SOCIAL = "💬 WhatsApp/Telegram: +959259282400"

# Version Info
APP_VERSION = "1.0.0"
BUILD_DATE = "2025-12-15"
DEVELOPER_NAME = "Sai Hleng"
