# Changelog

All notable changes to Vribbels CZN Optimizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.3.1]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.1.0...v1.3.0
[1.1.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Vorbroker/Vribbels-CZN-Optimizer/releases/tag/v1.0.0
