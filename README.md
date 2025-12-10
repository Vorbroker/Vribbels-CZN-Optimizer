# Vribbels - Chaos Zero Nightmare Optimizer

A Fribbels-inspired gear management and optimization tool for the mobile game **Chaos Zero Nightmare**. This tool helps you optimize your Memory Fragments to maximize your combatants' performance.

## Features

###  Memory Fragment Optimizer
- **Smart Build Optimization**: Automatically finds the best Memory Fragment combinations for your characters
- **Stat Priority Weighting**: Customize stat priorities to match your build goals
- **Set Bonus Support**: Filter by 2-piece and 4-piece set bonuses
- **Gear Score Calculation**: Evaluates fragments based on substats and potential
- **Top X% Filtering**: Reduce search space by focusing on your best fragments

###  Inventory Management
- **Memory Fragments Tab**: View and filter all your equipped and unequipped fragments
- **Materials Tab**: Track your growth stone inventory
- **Combatants Tab**: View all characters with levels, gear scores, and stats

###  Data Capture
- **Integrated mitmproxy Setup**: Built-in proxy configuration for capturing game data
- **Automatic Data Extraction**: Captures Memory Fragments, character data, and inventory
- **One-Click Capture**: Simple interface for extracting data from the game

###  Advanced Features
- **Potential Node Calculation**: Includes character progression bonuses
- **Partner Card Integration**: Calculates partner passive stat bonuses
- **Friendship Bonus Tracking**: Accounts for character friendship stats
- **Multi-Build Comparison**: Compare current vs. optimized builds side-by-side

## Installation

### Requirements
- Python 3.8 or higher
- Windows (for capture functionality)

### Quick Start

**Download Release (Recommended)**
1. Download the latest release from the [Releases page](https://github.com/Vorbroker/Vribbels-CZN-Optimizer/releases)
2. Extract the files
3. Run `czn_optimizer_gui.py`
4. Navigate to the **Setup** tab and click Install mitmproxy, then Generate & Install Cert

## Usage

### Capturing Game Data

1. Launch the application (run as Administrator on Windows for capture functionality)
2. Navigate to the **Capture** tab
3. Click **"Start Capture"**
4. Launch Chaos Zero Nightmare and navigate to the main menu
5. Click **"Stop Capture"**
6. Your data will be saved to `Vribbels/captures/memory_fragments_[timestamp].json`

### Optimizing Builds

1. Click **"Load Data"** and select your capture file
2. Select a combatant from the dropdown
3. Adjust **Stat Priorities** using the sliders (higher values = more important)
4. Select desired **Set Bonuses** (4-piece and/or 2-piece)
5. Choose **Main Stats** for slots 4, 5, and 6
6. Adjust **Top %** to control search space (lower = faster, fewer combinations)
7. Click **"Start"** to begin optimization
8. Review results showing stat improvements and required gear swaps

### Viewing Materials

Navigate to the **Materials** tab to see your growth stone inventory organized by attribute and quality level.

## How It Works

### Optimization Algorithm
1. Filters fragments by selected sets and main stats
2. Scores each fragment based on weighted stat priorities
3. Keeps only top X% of fragments per slot
4. Generates all valid 6-slot combinations
5. Validates set bonus requirements
6. Calculates final stats including:
   - Character base stats
   - Memory Fragment main stats
   - Memory Fragment substats
   - Set bonuses
   - Potential node bonuses
   - Partner bonuses
7. Ranks builds by priority-weighted score

### Gear Score Calculation
Each Memory Fragment receives a score based on:
- **Substat Quality**: Low/Med/High/Max rolls
- **Substat Rolls**: Number of enhancement upgrades
- **Potential**: Maximum achievable stats
- Combined into a 0-100 gear score

## Contributing

Contributions are welcome! Feel free to:
- Report bugs via GitHub Issues
- Submit character/partner data updates
- Suggest new features
- Improve documentation

## Credits

Inspired by [Fribbels Epic 7 Gear Optimizer](https://github.com/fribbels/Fribbels-Epic-7-Optimizer)

## Support

If you find this tool helpful, consider supporting development:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H21PHYKW)

## License

This project is for educational and personal use. Chaos Zero Nightmare and all related assets are property of their respective owners.

---

**Note**: This is a third-party tool and is not affiliated with or endorsed by the developers of Chaos Zero Nightmare.
