# MSA - Mobile Service Accounting

**Professional Desktop Application for Mobile Device Repair Shops**

MSA is a comprehensive business management solution designed specifically for mobile phone repair shops. Built with modern technologies and a focus on efficiency, MSA helps you manage every aspect of your repair business from a single, elegant desktop application.

---

## 🌟 Key Features

### 📱 Ticket Management

- Complete repair workflow tracking from intake to completion
- Device lock pattern/passcode recording
- Photo documentation for before/after repairs
- Automatic work log generation
- Real-time status updates

### 👥 Customer Management

- Comprehensive customer database
- Device history tracking
- Quick search and lookup
- Customer communication tools

### 📦 Inventory Control

- Parts tracking and management
- Low stock alerts
- Supplier management
- Purchase order system
- Automatic inventory updates

### 💰 Financial Management

- Invoice generation and printing
- Payment tracking (cash, card, bank transfer)
- Revenue and expense reporting
- Profit/loss analysis
- Commission calculation for technicians

### 👨‍🔧 Technician Performance

- Individual performance tracking
- Commission-based compensation
- Work log history
- Bonus management

### 📱 Mobile Workbench

- Built-in mobile interface for technicians
- Access from any device on local network
- Real-time ticket updates
- Mobile-optimized UI
- QR code pairing

### 🌍 Multi-Language Support

- English and Burmese (Myanmar) languages
- Easy language switching
- Localized currency (MMK)

---

## 📥 Download & Installation

### Latest Release: v1.0.6

**[Download MSA-Installer.dmg](https://github.com/treavorfang/msa-app-releases/releases/latest)**

### Installation Steps

1. **Download** the DMG file from the latest release
2. **Open** the downloaded MSA-Installer.dmg
3. **Drag** MSA.app to your Applications folder
4. **Launch** MSA from Applications

### System Requirements

- **Operating System**: macOS 10.13 (High Sierra) or later
- **Processor**: Apple Silicon (M1/M2/M3) or Intel
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB available space
- **Display**: 1280x800 minimum resolution

---

## 🚀 What's New in v1.0.6

### Critical Fixes

- 🔧 **Automatic database migration** - Fixes schema issues from v1.0.5
- ✅ **Missing columns** - Adds user_id to technicians table
- ✅ **Missing table** - Creates ticket_photos table
- 📱 **Mobile UI fix** - Mobile interface now loads correctly via QR code
- 🛠️ **Error fixes** - Resolves "no such column", "no such table", and "Not Found" errors

### Mobile Access Now Working

- Scan QR code from desktop app
- Access mobile workbench from any device
- Real-time ticket updates
- Mobile-optimized interface

### For Existing Users

If you experienced database or mobile access errors with v1.0.5, this update will automatically fix them on first launch. Your data is completely safe.

---

## 💡 Why Choose MSA?

### 🎨 Modern, Beautiful Interface

Built with PySide6 (Qt), MSA features a sleek, professional interface that's both powerful and easy to use.

### 🔒 Secure & Private

All your data stays on your computer. No cloud dependencies, no data sharing, complete privacy.

### ⚡ Fast & Efficient

Optimized performance with lazy loading, smart caching, and efficient database operations.

### 🌐 Network Ready

Built-in mobile server allows technicians to access the system from their phones on your local network.

### 📊 Comprehensive Reporting

Generate detailed reports for revenue, expenses, inventory, and technician performance.

### 🎯 Purpose-Built

Designed specifically for mobile repair shops with features that matter to your business.

---

## 🛠️ Technical Highlights

- **Framework**: PySide6 (Qt for Python)
- **Database**: SQLAlchemy with SQLite
- **Architecture**: Clean MVC pattern with repository layer
- **Mobile UI**: Modern responsive web interface
- **API**: FastAPI backend for mobile access
- **Security**: Cython-compiled sensitive modules
- **Printing**: WeasyPrint for professional invoices and receipts

---

## 📖 Getting Started

### First Launch

1. **Create Admin Account**: Set up your administrator credentials
2. **Configure Business**: Enter your shop name and preferences
3. **Add Technicians**: Create user accounts for your team
4. **Set Up Inventory**: Add your parts and suppliers
5. **Start Taking Tickets**: Begin managing repairs!

### Mobile Access

1. Launch MSA on your Mac
2. Note the IP address and QR code shown in the Mobile Pairing dialog
3. On your mobile device, scan the QR code or navigate to `http://<IP>:8000`
4. Enter the daily PIN shown in the desktop app
5. Log in with your technician credentials

---

## 🌏 Language Support

MSA supports both English and Burmese (Myanmar) languages:

- **English**: Full interface translation
- **Burmese (ဗမာ)**: Complete localization including UI, reports, and receipts

Switch languages anytime from Settings → General.

---

## 📞 Support

For questions, issues, or feature requests, please visit the [Releases](https://github.com/treavorfang/msa-app-releases/releases) page.

---

## 📜 License

MSA is proprietary software. All rights reserved.

---

## 🎉 About

MSA is developed with ❤️ for mobile repair shop owners who want to streamline their business operations and focus on what matters most - serving their customers.

**Version**: 1.0.6  
**Build**: 930  
**Release Date**: December 25, 2025
