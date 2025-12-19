
import os
import sys
from datetime import datetime

# Add src to path to import weasyprint if needed, or just import directly
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

import platform

# === MACOS WEASYPRINT FIX ===
# Ensure WeasyPrint can find the libraries installed by Homebrew
if platform.system() == 'Darwin':
    # Add common Homebrew paths to fallback library path
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

# Add src to path to import weasyprint if needed, or just import directly
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

try:
    from weasyprint import HTML, CSS
except ImportError:
    print("WeasyPrint is not installed. Please install it with: pip install weasyprint")
    sys.exit(1)

def generate_manual():
    print("Generating User Manual PDF...")
    
    # Define output path
    # Script is in tools/, so project root is ../
    output_dir = os.path.join(os.path.dirname(__file__), '../docs')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, 'MSA_User_Manual.pdf')
    
    # Current Date
    date_str = datetime.now().strftime("%B %Y")
    
    # CSS Styling
    css = """
    @page {
        size: A4;
        margin: 2.5cm;
        @bottom-center {
            content: "Page " counter(page);
            font-family: 'Helvetica', sans-serif;
            font-size: 9pt;
            color: #666;
        }
    }
    
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        line-height: 1.6;
        color: #333;
        font-size: 11pt;
    }
    
    h1, h2, h3 {
        color: #1F2937;
        font-weight: bold;
    }
    
    h1 {
        font-size: 28pt;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 10px;
        margin-top: 0;
    }
    
    h2 {
        font-size: 18pt;
        margin-top: 30px;
        border-bottom: 1px solid #E5E7EB;
        padding-bottom: 5px;
        color: #3B82F6;
    }
    
    h3 {
        font-size: 14pt;
        margin-top: 20px;
        color: #4B5563;
    }
    
    p {
        margin-bottom: 12px;
    }
    
    ul {
        margin-bottom: 12px;
    }
    
    li {
        margin-bottom: 5px;
    }
    
    .cover-page {
        text-align: center;
        padding-top: 300px;
        page-break-after: always;
    }
    
    .cover-title {
        font-size: 36pt;
        font-weight: bold;
        color: #1F2937;
        margin-bottom: 20px;
    }
    
    .cover-subtitle {
        font-size: 18pt;
        color: #6B7280;
        margin-bottom: 50px;
    }
    
    .cover-footer {
        font-size: 12pt;
        color: #9CA3AF;
        margin-top: 100px;
    }
    
    .note {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 10px 15px;
        margin: 15px 0;
        font-size: 10pt;
    }
    
    .warning {
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 10px 15px;
        margin: 15px 0;
        font-size: 10pt;
    }
    
    code {
        background-color: #F3F4F6;
        padding: 2px 5px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    
    .toc {
        page-break-after: always;
    }
    
    .toc-item {
        margin-bottom: 8px;
    }
    """
    
    # HTML Content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MSA User Manual</title>
        <style>{css}</style>
    </head>
    <body>
        
        <!-- Cover Page -->
        <div class="cover-page">
            <div class="cover-title">MSA</div>
            <div class="cover-subtitle">Mobile Service Accounting</div>
            <div style="font-size: 14pt; margin-bottom: 20px;">User Manual & Guide</div>
            <div class="cover-footer">
                Version 1.0.2<br>
                {date_str}
            </div>
        </div>
        
        <!-- Introduction -->
        <h1>1. Introduction</h1>
        <p>Welcome to <b>MSA (Mobile Service Accounting)</b>, the professional management solution designed specifically for mobile repair shops and service centers.</p>
        <p>This application simplifies your daily operations by combining ticket management, point-of-sale invoicing, inventory control, and customer relationship management into one unified, easy-to-use platform.</p>
        
        <h3>Key Features</h3>
        <ul>
            <li><b>Ticket Management:</b> Track repairs from intake to completion.</li>
            <li><b>Smart Invoicing:</b> Create professional invoices with thermal receipt support.</li>
            <li><b>Cloud Activation:</b> Secure, online license verification.</li>
            <li><b>Inventory Control:</b> Manage parts, devices, and stock levels.</li>
            <li><b>Customer CRM:</b> Keep track of customer history and devices.</li>
            <li><b>Reports:</b> Gain insights into your business performance.</li>
        </ul>
        
        <!-- Getting Started -->
        <h2>2. Getting Started</h2>
        
        <h3>Installation / Launch</h3>
        <p>MSA is provided as a standalone application. On macOS, simply copy the <code>MSA.app</code> to your Applications folder. On Windows, run the provided installer or executable.</p>
        
        <h3>Activation</h3>
        <p>When you first launch the application, you will be prompted to activate your license.</p>
        <ol>
            <li>Ensure you are connected to the internet.</li>
            <li>Enter your <b>Email</b> and <b>License Key</b> provided by your distributor.</li>
            <li>Click <b>Activate</b>. The system will verify your license with our cloud server.</li>
        </ol>
        <div class="note">
            <b>Note:</b> Your license is locked to your specific hardware. You cannot use the same license key on multiple computers simultaneously unless you have a multi-seat license.
        </div>
        
        <h3>Login</h3>
        <p>After activation, you will see the Staff Login screen.</p>
        <div style="text-align: center; margin: 20px 0;">
            <img src="../docs/images/login.png" width="400" style="border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        </div>
        <ul>
            <li><b>Default Admin User:</b> <code>admin</code></li>
            <li><b>Default Password:</b> <code>123456</code> (Please change this immediately in Settings)</li>
        </ul>
        <p>The "Remember Me" feature allows you to save your staff credentials for quick access, separate from your license activation credentials.</p>
        
        <!-- Interface Overview -->
        <h2>3. Interface Overview</h2>
        
        <h3>The Dashboard</h3>
        <p>The Dashboard is your command center. It provides an immediate snapshot of your business:</p>
        <div style="text-align: center; margin: 20px 0;">
            <img src="../docs/images/dashboard.png" width="500" style="border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        </div>
        <ul>
            <li><b>Key Metrics:</b> Total revenue, open tickets, and active technician count.</li>
            <li><b>Status Board:</b> A quick view of tickets categorized by status (New, In Progress, Completed).</li>
            <li><b>Recent Activity:</b> A log of the latest actions taken in the system.</li>
        </ul>
        
        <h3>Navigation</h3>
        <p>The sidebar on the left gives you access to all major modules:</p>
        <ul>
            <li><b>Tickets:</b> Manage repair jobs.</li>
            <li><b>Invoices:</b> Create and view sales records.</li>
            <li><b>Customers:</b> Manage client profiles and their devices.</li>
            <li><b>Inventory:</b> Manage parts and products.</li>
            <li><b>Technicians:</b> Manage staff profiles.</li>
            <li><b>Reports:</b> View financial data.</li>
            <li><b>Settings:</b> Configure application preferences.</li>
        </ul>
        
        <!-- Core Workflows -->
        <h2>4. Core Workflows</h2>
        
        <h3>Creating a New Ticket</h3>
        <ol>
            <li>Click <b>New Ticket</b> in the toolbar or press <code>Ctrl+N</code>.</li>
        </ol>
        <div style="text-align: center; margin: 20px 0;">
            <img src="../docs/images/ticket.png" width="400" style="border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        </div>
        <ol start="2">
            <li><b>Select Customer:</b> Search for an existing customer or click "+" to add a new one.</li>
            <li><b>Add Device:</b> Select the customer's device or add a new one (Model, Color, Serial/IMEI).</li>
            <li><b>Describe Issue:</b> Enter the problem description and any pattern/passcode.</li>
            <li><b>Assign Technician:</b> (Optional) Assign the job to a staff member.</li>
            <li>Click <b>Create Ticket</b>. You can now print a reception receipt for the customer.</li>
        </ol>
        
        <h3>Creating an Invoice</h3>
        <p>You can create an invoice directly or convert a ticket into an invoice.</p>
        <div style="text-align: center; margin: 20px 0;">
            <img src="../docs/images/invoice.png" width="500" style="border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        </div>
        <ol>
            <li>Go to the <b>Invoices</b> tab and click <b>New Invoice</b>.</li>
            <li>Select the Customer.</li>
            <li>Add <b>Line Items</b> (Parts, Service Charges). Prices are automatically populated from Inventory but can be overridden.</li>
            <li><b>Payments:</b> Record the amount paid. The system automatically calculates the balance.</li>
            <li>Click <b>Save & Print</b>.</li>
        </ol>
        <div class="note">
            <b>Burmese Font Support:</b> MSA automatically handles Pyidaungsu and other Myanmar fonts for correct rendering on receipts.
        </div>
        
        <h3>Managing Inventory</h3>
        <p>Go to the <b>Inventory</b> tab to track your stock.</p>
        <ul>
            <li><b>Parts:</b> Spare parts for repairs (screens, batteries).</li>
            <li><b>Reorder Alerts:</b> Items running low will be highlighted.</li>
        </ul>
        
        <!-- Settings -->
        <h2>5. Settings & Customization</h2>
        
        <h3>General Preferences</h3>
        <p>In the <b>Settings</b> tab, you can customize:</p>
        <ul>
            <li><b>Company Info:</b> Name, Address, Phone (appears on all receipts).</li>
            <li><b>Language:</b> Switch between English, Burmese, and other supported languages.</li>
            <li><b>Theme:</b> Toggle specialized Dark Mode or Light Mode.</li>
        </ul>
        
        <h3>Currency</h3>
        <p>You can set your preferred currency (e.g., USD, MMK). The system automatically formats numbers with commas (e.g., 10,000) for better readability.</p>
        
        <!-- Support -->
        <h2>6. Support</h2>
        <p>If you encounter any issues:</p>
        <ul>
            <li>Check the <b>About</b> dialog (Help > About) for your version number.</li>
            <li>Contact our support team at <b>support@worldlock.inc</b>.</li>
            <li>Please have your License Key ready when contacting support.</li>
        </ul>
        
        <br><br>
        <p style="text-align: center; color: #9CA3AF; font-size: 10pt;">
            © 2025 World Lock Inc. All rights reserved.
        </p>
    </body>
    </html>
    """
    
    # Generate PDF
    HTML(string=html_content).write_pdf(output_file, stylesheets=[CSS(string=css)])
    print(f"Success! Manual saved to: {output_file}")

if __name__ == "__main__":
    generate_manual()
