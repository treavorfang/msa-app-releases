# Changelog

## [1.0.5] - 2025-12-25

### Added

- **Technician Workbench Tabs**: New "Active", "Finished", and "Returned" sub-tabs on mobile dashboard with smooth, in-place transitions.
- **Modern Technician Login**: Completely redesigned mobile login UI with a premium "Nano Banana" aesthetic.
- **Device Status Guardrails**: Desktop app now restricts editing for tickets where the device has been returned.

### Changed

- **Financial Sync Logic**: Improved branch identification to ensure mobile transactions correctly sync with desktop views.
- **Font Loading Optimization**: Refactored font initialization to eliminate startup warnings and improve launch speed.
- **Mobile Localization**: Added Burmese translations across all new mobile dashboard components.

### Fixed

- **Branch ID Sync**: Resolved issue where mobile transactions were saved with `NULL` branch IDs, making them invisible on desktop.
- **Performance Tab Stability**: Fixed `TypeError` on mobile Performance tab when data was missing.
- **Database Migration**: Successfully migrated all legacy `NULL` branch records to the primary branch.

## [1.0.4] - 2025-12-20

### Added

- **Smart Window Sizing**: Application automatically adapts to screen resolution (optimizes for 720p vs 1080p).
- **Real-time Invoice Calculations**: Change due and remaining balance update instantly as you type.
- **Technician Bonuses**: Track and calculate performance-based bonuses.
- **Financial Module**: Enhanced financial management system.

### Changed

- **UI Revert**: Restored Activation and Login screens to the Classic Compact style with optimized spacing.
- **Localization**: Full localization support for Staff Login and Financial tabs.
- **Performance**: Improved startup stability on various display configurations.
- Updated build version to 1.0.4.
