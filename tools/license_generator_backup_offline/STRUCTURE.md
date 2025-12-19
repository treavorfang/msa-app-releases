# License Generator - Modular Structure

## 📁 New File Structure

```
tools/license_generator/
├── main.py                      # Entry point (to be refactored)
├── run.py                       # Launcher script
├── core/                        # Business logic
│   ├── __init__.py
│   ├── config.py               # Configuration & paths
│   ├── generator.py            # License generation logic
│   └── history.py              # History management
├── ui/                          # User interface
│   ├── __init__.py
│   ├── styles.py               # UI styles & themes
│   ├── main_window.py          # Main generator window (to be created)
│   └── history_dialog.py       # License history dialog (to be created)
├── license_history.csv          # License database
└── README.md                    # Documentation
```

## 🎯 Module Responsibilities

### Core Modules

#### `core/config.py`

- All configuration constants
- Path management
- Duration options
- Expiry thresholds

#### `core/generator.py`

- `LicenseGeneratorCore` class
- License key generation
- Cryptographic operations
- Input validation

#### `core/history.py`

- `HistoryManager` class
- CSV file operations
- Statistics calculation
- License status determination

### UI Modules

#### `ui/styles.py`

- All QSS stylesheets
- Color constants
- Theme definitions

#### `ui/main_window.py` (to be created)

- Main application window
- Input forms
- Button handlers
- Uses `LicenseGeneratorCore`

#### `ui/history_dialog.py` (to be created)

- History viewing dialog
- Search & filter functionality
- Statistics display
- Uses `HistoryManager`

## ✅ Benefits

1. **Separation of Concerns**: Business logic separated from UI
2. **Testability**: Core logic can be tested without UI
3. **Maintainability**: Each module has a single responsibility
4. **Reusability**: Core modules can be used in other tools
5. **Scalability**: Easy to add new features

## 🔄 Next Steps

1. Refactor `main.py` into `ui/main_window.py`
2. Extract history dialog code into `ui/history_dialog.py`
3. Update `main.py` to be a simple entry point
4. Add unit tests for core modules

## 📝 Usage Example

```python
# Using the core modules directly
from core import LicenseGeneratorCore, HistoryManager

# Generate a license
generator = LicenseGeneratorCore()
license_data = generator.generate(
    customer_name="John Doe",
    hwid="ABC123",
    duration_days=365
)

# Save to history
history = HistoryManager()
history.save_license(license_data)

# Get statistics
data = history.load_history()
stats = history.calculate_statistics(data)
print(f"Total licenses: {stats['total']}")
```

## 🎨 Code Quality

- Type hints for better IDE support
- Docstrings for all public methods
- Error handling with specific exceptions
- Configuration centralized
- No hardcoded values
