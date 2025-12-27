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

### Latest Release: v1.1.0

- 🍎 **macOS**: [Download MSA-Installer.zip](https://github.com/treavorfang/msa-app-releases/releases/download/v1.1.0/MSA-Installer.zip)
- 🪟 **Windows**: [Download MSA_Setup_v1.1.0.exe](https://github.com/treavorfang/msa-app-releases/releases/download/v1.1.0/MSA_Setup_v1.1.0.exe)

### Installation Steps

#### macOS

1. **Download** the DMG file.
2. **Open** `MSA-Installer.zip`.
3. **Drag** MSA to Applications.
4. **Launch** from Applications.

#### Windows

1. **Download** the EXE file.
2. **Run** `MSA_Setup_v1.1.0.exe`.
3. **Follow** the setup wizard.
4. **Launch** from Start Menu or Desktop.

### System Requirements

#### macOS

- **OS**: macOS 10.13 (High Sierra) or later
- **Processor**: Apple Silicon (M1/M2/M3) or Intel
- **Memory**: 4GB RAM minimum
- **Display**: 1280x800 minimum

#### Windows

- **OS**: Windows 10 or Windows 11
- **Processor**: 64-bit Intel/AMD
- **Memory**: 4GB RAM minimum
- **Disk**: 500MB available space

---

## 🚀 What's New in v1.1.0

### Added

- **Urgent Ticket Priority**: Tickets due today or within 24 hours now automatically float to the top of the Active list.
- **Financial Indicators**: Added clear Credit/Debit indicators on the Client Profile.
- **Unpaid Alert**: Added red border visual cue for unpaid tickets.

### Changed

- **Premium Mobile UI**: Complete visual overhaul with styled Language Selector, themed financial cards, and refined typography.
- **Performance Access**: "Performance" button is now visible to Technicians but hidden for Staff/Admins on mobile profile.

### Fixed

- **Printing Accuracy**: Fixed missing IMEI, Color, and Condition fields on printed thermal tickets.
- **Navigation Stability**: Fixed flickering issues and optimized the "Create" FAB visibility logic.

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

**Version**: 1.1.0  
**Build**: 1038  
**Release Date**: December 27, 2025
