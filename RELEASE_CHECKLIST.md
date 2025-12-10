# Release Checklist

## Files to Include in Release

When creating a GitHub release, include the following files/folders:

### Required Files
```
Vribbels/
├── czn_optimizer_gui.py          # Main application
├── captures/
│   └── _capture_addon.py         # Standalone capture addon
│   (no JSON files - captures folder otherwise empty)
└── images/                        # Growth stone icons (15 PNG files)
    ├── growth_stone_passion_common.png
    ├── growth_stone_passion_great.png
    ├── growth_stone_passion_premium.png
    ├── growth_stone_instinct_common.png
    ├── growth_stone_instinct_great.png
    ├── growth_stone_instinct_premium.png
    ├── growth_stone_void_common.png
    ├── growth_stone_void_great.png
    ├── growth_stone_void_premium.png
    ├── growth_stone_order_common.png
    ├── growth_stone_order_great.png
    ├── growth_stone_order_premium.png
    ├── growth_stone_justice_common.png
    ├── growth_stone_justice_great.png
    └── growth_stone_justice_premium.png

README.md                          # User documentation
```

### Files to EXCLUDE
- `.git/` folder
- `.gitignore`
- `.claude/` folder
- `CLAUDE.md`
- `RELEASE_CHECKLIST.md` (this file)
- `CZN Assets/` folder (if present)
- Any `memory_fragments_*.json` files in captures/
- `__pycache__/` folders
- `.vscode/`, `.idea/` folders

## Creating a Release on GitHub

1. Go to your repository: https://github.com/Vorbroker/Vribbels-CZN-Optimizer
2. Click on "Releases" in the right sidebar
3. Click "Draft a new release"
4. Create a new tag (e.g., `v1.0.0`)
5. Set release title (e.g., `Vribbels CZN Optimizer v1.0.0`)
6. Add release notes describing features
7. Attach a ZIP file containing only the files listed above
8. Mark as "Latest release"
9. Click "Publish release"

## Packaging the Release

**Option 1: Manual ZIP**
1. Create a new folder: `Vribbels-CZN-Optimizer-v1.0.0`
2. Copy only the required files listed above
3. ZIP the folder
4. Upload to GitHub release

**Option 2: Git Archive**
```bash
# This won't work perfectly due to images/ being in .gitignore
# Use manual method instead
```

## Sample Release Notes

```markdown
# Vribbels CZN Optimizer v1.0.0

A Fribbels-inspired gear optimizer for Chaos Zero Nightmare.

## Features
- Memory Fragment build optimization with stat priority weighting
- Materials tab with growth stone inventory tracking
- Data capture via integrated mitmproxy setup
- Support for 25+ combatants and 30+ partner cards
- Automatic dependency installation via Setup tab

## Installation
1. Download and extract the ZIP file
2. Ensure Python 3.8+ is installed
3. Run `czn_optimizer_gui.py`
4. Navigate to Setup tab and click "Install Dependencies"
5. Navigate to Capture tab to begin capturing your data

## Requirements
- Python 3.8 or higher
- Windows (for capture functionality)

Dependencies (auto-installed via Setup tab):
- Pillow (for image processing)
- mitmproxy (for data capture)
```
