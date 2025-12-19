# MSA License Generator

A standalone tool for generating and managing MSA application licenses with a clean modular architecture.

## 📁 Project Structure

```
tools/license_generator/
├── main.py                  # Application entry point
├── run.py                   # Quick launcher
├── core/                    # Business logic layer
│   ├── __init__.py
│   ├── config.py           # Configuration & paths
│   ├── generator.py        # License generation logic
│   └── history.py          # History management
├── ui/                      # User interface layer
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── history_dialog.py   # License history dialog
│   └── styles.py           # UI styles & themes
├── license_history.csv      # License database
├── README.md               # This file
└── STRUCTURE.md            # Architecture documentation
```

## ✨ Features

### License Generation

- **Customer Information**: Name, Hardware ID (HWID)
- **Duration Options**:
  - 1 Month
  - 3 Months
  - 6 Months
  - 1 Year
  - Lifetime
- **Automatic Signing**: Uses Ed25519 cryptography
- **History Tracking**: All generated licenses saved to CSV

### License History Management

- **📊 Statistics Dashboard**: Real-time counts of total, active, expiring, expired, and lifetime licenses
- **🔍 Search**: Filter by customer name, HWID, or date
- **🔽 Filter**: Quick filters (All, Active, Expiring Soon, Expired, Lifetime)
- **↕️ Sortable Columns**: Click headers to sort
- **🎨 Color-Coded Status**: Visual indicators for license status
- **📋 Context Menu**: Right-click to copy license key, customer name, or HWID
- **📄 Details View**: Double-click for full license information
- **🗑️ Delete Entry**: Remove invalid or test licenses
- **💾 Export**: Save history to CSV file
- **🔄 Refresh**: Reload data from file

## 🚀 Usage

### Running the Tool

```bash
# From project root
python3 tools/license_generator/main.py

# Or using the launcher
python3 tools/license_generator/run.py
```

### Generating a License

1. Enter customer name
2. Paste the customer's Hardware ID (HWID)
3. Select license duration
4. Click "🔑 Generate License Key"
5. Copy the generated key and send to customer

### Viewing History

1. Click "📊 History" button
2. Use filters and search to find specific licenses
3. Double-click any row for detailed view
4. Right-click for quick actions

## 🏗️ Architecture

### Core Layer (`core/`)

- **Separation of Concerns**: Business logic separated from UI
- **Testability**: Core modules can be tested independently
- **Reusability**: Can be used in other tools or scripts

### UI Layer (`ui/`)

- **Clean Interface**: Modern, intuitive design
- **Responsive**: Adapts to different screen sizes
- **Themed**: Consistent dark theme throughout

### Benefits

- **Maintainability**: Each module has a single responsibility
- **Scalability**: Easy to add new features
- **Modularity**: Components can be updated independently

## 📋 Requirements

- Python 3.8+
- PySide6
- cryptography

## 🔐 Security

- Uses Ed25519 asymmetric cryptography
- Private key required (stored in project root: `private.pem`)
- Public key distributed with main application
- Hardware-locked licenses (HWID verification)

## 📊 License Status

- **🟢 Active**: Valid and not expiring soon
- **🟡 Expiring Soon**: Less than 30 days remaining
- **🔴 Expired**: Past expiry date
- **♾️ Lifetime**: Never expires (9999-12-31)

## 💡 Tips

- Keep `license_history.csv` backed up
- Export history regularly for safety
- Use descriptive customer names for easy searching
- Delete test licenses to keep history clean

## 🧪 Development

### Running Tests

```bash
# Unit tests (when implemented)
python3 -m pytest tests/
```

### Code Structure

See `STRUCTURE.md` for detailed architecture documentation.

## 📝 License

Part of the MSA (Mobile Service Application) project.
