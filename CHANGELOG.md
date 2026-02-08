# Changelog

All notable changes to Vribbels CZN Optimizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-02-07

### Added
- **Live Monitoring** — Keep capture running and see changes in real-time
  - Equip, unequip, swap, and upgrade memory fragments without restarting capture
  - Capture log shows human-readable [LIVE] messages for each change
  - Inventory, Combatants, and Materials tabs auto-refresh on every change
  - Data auto-loads on initial capture — no need to stop capture and manually load
- **WebSocket Debug Logger** (hidden, developer tool) for inspecting raw game traffic

### Changed
- Capture tab instructions updated to reflect live monitoring workflow
- Removed post-stop "Load data?" prompt — data is already loaded automatically
- Filtered noisy mitmproxy WebSocket flow messages from capture log

### Fixed
- Handled JSON array WebSocket messages that caused `'list' object has no attribute 'get'` errors

## [1.6.0] - 2026-02-07

### Added
- **New Memory Fragment Sets**
  - **Beast's Yearning** (4-piece, set_id 24): +30% Justice and Order Attack Cards (max 5 per turn)
  - **Glory's Reign** (4-piece, set_id 25): +5% ally DMG on Exhaust card create/use (max 15%)

### Changed
- **UI Improvements**
  - Application window widened from 1450 to 1550 for better layout
  - Optimizer tab: 4-piece set checkboxes now use 4 columns
  - Optimizer tab: Selected Build section uses grid layout to reliably show all 6 gear slots
  - Optimizer tab: Stats Comparison and Results column layout improvements

### Fixed
- Update checker now re-notifies on launch from cached data when 24h API throttle is active
- Manual "Check for Updates" uses Yes/No dialog instead of showinfo (X no longer opens browser)
- Update notification dialog X button properly dismisses via WM_DELETE_WINDOW handler

## [1.5.1] - 2026-02-06

### Added
- **New Characters**
  - **Nine** - 5-star character
- **New Partner Cards**
  - **Alcea** partner card

## [1.5.0] - 2026-01-16

### Added
- **Zstd Dictionary Decompression** for compressed game WebSocket data
- `find_mitmdump()` utility to locate mitmdump in various installation paths
- Bundled `zstd_dictionary.bin` for compressed data decompression

### Changed
- Cleaned up capture logging to reduce verbosity

## [1.4.1] - 2026-01-15

### Added
- **New Characters**
  - **Narja** (res_id 1052) - 5-star Instinct Controller with DEF%/CRate potential nodes
- **New Partner Cards**
  - **Gaya** (res_id 20002) - 5-star Controller with Defense-based damage passive for Instinct cards

## [1.4.0] - 2025-12-26

### Added
- **Automatic Update Checking**
  - Checks GitHub releases for new versions once per 24 hours
  - Modal dialog at startup when update is available
  - "About" tab with version info and manual update check
  - Skip version capability to ignore specific releases
  - Graceful offline behavior with cached update info
  - Background threading for non-blocking checks

### Technical Details
- New `version.py` module as single source of truth for version
- New `update_checker.py` module for GitHub API integration
- New `AboutTab` following BaseTab pattern
- Uses `packaging` library for semantic version comparison
- Metadata persisted in `%APPDATA%/Vribbels/update_check.json`

## [1.3.1] - 2025-12-26

### Fixed
- **Bundled Exe Capture Issues**
  - Fixed addon script generation error in bundled executables
    - Replaced `inspect.getsource()` with embedded template string
    - Resolves "could not get source code" error when running from exe
  - Fixed black console window appearing during capture
    - Added Windows STARTUPINFO configuration to hide mitmproxy console window
    - Improves user experience - no more distracting black windows
  - Fixed snapshots folder created in wrong location
    - Detects PyInstaller frozen state and uses exe directory
    - Snapshots now properly created next to the exe instead of in AppData temp folder
  - Fixed auto-load not working after capture
    - Corrected `load_data_callback` to point to proper `load_data` method
    - "Load captured data now?" dialog now works correctly

### Notes
- All capture features now work correctly in the bundled exe
- Snapshots folder will be created in the same directory as the exe
- After capture completes, users will be prompted to auto-load the data

## [1.3.0] - 2025-12-26

### Changed
- **Major Refactoring: 92% Code Reduction**
  - Main GUI file reduced from ~3,900 lines to just 296 lines
  - Complete modularization of the codebase

### Added
- **Complete UI Modularization** - All 7 tabs extracted to `ui/tabs/` module (~2,441 lines):
  - Phase 1: MaterialsTab, SetupTab, CaptureTab (~478 lines)
  - Phase 2: InventoryTab, OptimizerTab (~1,243 lines)
  - Phase 3: HeroesTab, ScoringTab (~918 lines)
- **Design Patterns**:
  - BaseTab pattern with dependency injection
  - AppContext for cross-component communication
  - Main GUI now acts purely as coordinator and lifecycle manager
- **Solia Partner Card** (res_id: 1058)
  - 5-star Ranger with Spacetime Warp passive
  - Unconditional: +20-40% Extra Attack damage
  - Conditional: +10-20% Attack Card Damage on first draw per turn
  - Ego Skill: Spacetime Rift (cost 3, 250% Damage + Mark 1)

### Fixed
- Corrected potential stat values to 5 levels
- Fixed CRate scaling (2%/level, not 0.6%/level)
- Fixed CDmg potential values (2.4%/level, not 1.2%/level)

### Technical Details
- All original functionality preserved
- Zero breaking changes to user experience
- Each component independently maintainable and testable
- Clear separation of concerns throughout the codebase

## [1.1.0] - 2025-12-24

### Added
- **New Characters**
  - **Sereniel** - 5-star Instinct Hunter (res_id 30075)
    - Level 60 stats: 491 ATK, 155 DEF, 329 HP
    - Potential nodes: Crit Rate (50), Crit Damage (60)
- **New Partner Cards**
  - **Peko** - 5-star Hunter partner card (res_id 30076)
    - Passive: Peko's Multi-Purpose Kit (ATK boost, Repairs Complete mechanic)
    - EGO: Overclock Beacon (cost 3)

### Changed
- **UI/UX Improvements**
  - Improved selection contrast - darker blue (#3b6ea5) for better readability
  - Fixed checkbox hover states - proper dark background with light text
  - Enhanced Treeview heading hovers - readable text when hovering over table headers
  - Better combatant selection visibility - dark blue background instead of light blue
  - Overall contrast improvements across all selection and hover states

### Refactored
- Game data split into separate modules (characters, partners, sets, constants)
- Improved code organization and maintainability

## [1.0.0] - 2025-12-12

### Added
- Initial release of Vribbels CZN Optimizer
- Memory Fragment (gear) management and optimization
- Data capture via mitmproxy integration
- Character and partner card database
- Optimization algorithm with configurable priorities
- Set bonus calculations
- Potential node support
- GUI with multiple tabs:
  - Optimizer tab for gear optimization
  - Memory Fragments inventory view
  - Materials tracking
  - Combatants (heroes) view
  - Capture tab for data extraction
  - Setup tab for prerequisites
  - Scoring tab for custom weights

---

[1.7.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.1.0...v1.3.0
[1.1.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/releases/tag/v1.0.0
