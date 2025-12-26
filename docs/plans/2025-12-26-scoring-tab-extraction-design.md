# ScoringTab Extraction Design

**Date:** 2025-12-26
**Status:** Approved
**Approach:** Simple extraction following established BaseTab pattern

## Overview

Extract the ScoringTab (Scoring configuration tab) from the main GUI file (~170 lines) into a modular `ui/tabs/scoring_tab.py` following the established BaseTab + AppContext pattern. This completes Phase 3 of the UI refactoring roadmap.

## Goals

- **Reduce main GUI file** from ~461 lines to ~290 lines (37% reduction)
- **Achieve 93% total reduction** from original 3,900 lines to ~290 lines
- **Maintain all functionality** - No breaking changes to user experience
- **Follow established pattern** - Use BaseTab + AppContext like other tabs
- **Enable independent testing** - ScoringTab can be tested in isolation
- **Complete UI refactoring** - Final tab extraction

## Architecture

### Pattern: BaseTab + AppContext

```python
class ScoringTab(BaseTab):
    def __init__(self, parent: tk.Widget, context: AppContext):
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()

    def _init_state(self):
        """Initialize state variables."""
        # Widget references (set in setup_ui)
        self.stat_weight_vars = {}      # Dict[str, tk.DoubleVar] - 16 stat weights
        self.weight_status = None       # ttk.Label - status message
```

### Key Architectural Decisions

1. **Self-contained widget management** - ScoringTab owns all 2 state variables
2. **Cross-tab refresh via AppContext** - Access inventory_tab and heroes_tab instances
3. **Preset weight configurations** - DPS and Tank presets built into tab
4. **Public API:** `apply_custom_weights()`, `reset_weights()`, `preset_dps_weights()`, `preset_tank_weights()`
5. **Extended AppContext** - Add `inventory_tab` and `heroes_tab` instance fields

## What We're Extracting

### From `czn_optimizer_gui.py`

**Lines to Extract (~170 total):**
- Frame creation (lines 179-180, ~2 lines)
- `setup_scoring_tab()` method (lines 187-303, ~117 lines)
- 4 scoring methods (lines 305-355, ~51 lines)
- State variable initialization (~2 lines from `__init__` if any)

**State Variables (2 variables):**
```python
self.stat_weight_vars = {}    # Dict[str, tk.DoubleVar]
self.weight_status = None     # ttk.Label
```

**Methods (5 methods):**
1. `setup_scoring_tab()` → `setup_ui()` - UI construction (~117 lines)
2. `reset_weights()` - Reset all weights to 1.0 (~5 lines)
3. `preset_dps_weights()` - DPS preset configuration (~13 lines)
4. `preset_tank_weights()` - Tank preset configuration (~13 lines)
5. `apply_custom_weights()` - Recalculate scores and refresh tabs (~22 lines)

## File Structure

### New File

```
Vribbels/ui/tabs/scoring_tab.py  (~170 lines)
```

**Structure:**
```python
"""
Scoring configuration tab.

Provides gear score weighting configuration with presets.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from ui.base_tab import BaseTab
from ui.context import AppContext
from game_data import STATS


class ScoringTab(BaseTab):
    """Gear score weighting configuration."""

    def __init__(self, parent, context):
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()

    def _init_state(self): ...
    def setup_ui(self): ...

    # Public API
    def reset_weights(self): ...
    def preset_dps_weights(self): ...
    def preset_tank_weights(self): ...
    def apply_custom_weights(self): ...
```

### Modified Files

**`ui/context.py`:**
```python
@dataclass
class AppContext:
    root: tk.Tk
    notebook: ttk.Notebook
    optimizer: 'GearOptimizer'
    capture_manager: 'CaptureManager'
    colors: dict
    style: ttk.Style
    load_data_callback: Callable[[str], None]
    switch_tab_callback: Callable[[tk.Widget], None]
    refresh_callback: Optional[Callable[[], None]] = None
    # NEW: Tab instance references for cross-tab refresh
    inventory_tab: Optional['InventoryTab'] = None
    heroes_tab: Optional['HeroesTab'] = None
```

**`ui/tabs/__init__.py`:**
```python
from .scoring_tab import ScoringTab

__all__ = ['MaterialsTab', 'SetupTab', 'CaptureTab', 'InventoryTab', 'OptimizerTab', 'HeroesTab', 'ScoringTab']
```

**`ui/__init__.py`:**
```python
from .tabs import MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab, ScoringTab
```

**`czn_optimizer_gui.py`:**
```python
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab, ScoringTab

# Set tab instances in AppContext after creating tabs (~line 175)
self.app_context.inventory_tab = self.inventory_tab_instance
self.app_context.heroes_tab = self.heroes_tab_instance

# Create ScoringTab instance (~line 178)
self.scoring_tab_instance = ScoringTab(self.notebook, self.app_context)
self.scoring_tab = self.scoring_tab_instance.get_frame()
self.notebook.add(self.scoring_tab, text="Scoring")

# Remove:
# - Lines 179-180 (old frame creation)
# - Lines 181 (setup_scoring_tab() call)
# - Lines 187-355 (setup_scoring_tab and 4 methods)
# - State variables from __init__ (if any)
```

## Integration Points

### Main GUI → ScoringTab

**Tab Creation:**
```python
# OptimizerGUI.__init__ creates instance:
self.scoring_tab_instance = ScoringTab(self.notebook, self.app_context)
```

**Cross-Tab Refresh:**
```python
def apply_custom_weights(self):
    # Collect weights from spinboxes
    weights = {stat: var.get() for stat, var in self.stat_weight_vars.items()}

    # Recalculate scores for all fragments
    for fragment in self.context.optimizer.fragments:
        weighted_score = 0.0
        for sub in fragment.substats:
            stat_info = STATS.get(sub.raw_name, ...)
            max_roll = stat_info[3]
            normalized = sub.value / (max_roll * sub.roll_count)
            weight = weights.get(sub.name, 1.0)
            weighted_score += normalized * sub.roll_count * weight
        fragment.gear_score = round(weighted_score * 10, 1)
        fragment.calculate_potential()

    # Refresh other tabs via AppContext
    self.context.inventory_tab.refresh_inventory()
    self.context.heroes_tab.refresh_heroes()

    # Update status
    self.weight_status.config(
        text="Custom weights applied - scores recalculated",
        foreground=self.colors["green"]
    )
```

**Preset Configurations:**

*DPS Focus:*
- High: ATK% (2.0), CRate (2.0), CDmg (2.0)
- Medium: Flat ATK (1.5), Extra DMG% (1.5)
- Low: DEF% (0.5), HP% (0.5), Flat DEF (0.3), Flat HP (0.3)

*Tank Focus:*
- High: HP% (2.0), DEF% (2.0)
- Medium: Flat HP (1.5), Flat DEF (1.5)
- Low: ATK% (0.5), CRate (0.5), CDmg (0.5), Extra DMG% (0.3), DoT% (0.3)

## Validation Checkpoints

### Checkpoint 1: Extraction Complete

**Actions:**
- Create `ui/tabs/scoring_tab.py` with ScoringTab class
- Migrate all 5 methods
- Move state variables to `_init_state()`
- Move UI code to `setup_ui()`
- Update `ui/context.py` with tab instance fields
- Add exports to `__init__.py` files

**Validation:**
```bash
python -m py_compile Vribbels/ui/tabs/scoring_tab.py
python -m py_compile Vribbels/ui/context.py
```
✅ Code compiles without syntax errors

### Checkpoint 2: Integration Complete

**Actions:**
- Update main GUI to import ScoringTab
- Create ScoringTab instance
- Set tab instances in AppContext
- Remove old methods from main GUI
- Remove old state variables

**Validation:**
```bash
python Vribbels/czn_optimizer_gui.py
```
✅ Application starts without errors
✅ Scoring tab appears in notebook

### Checkpoint 3: Functional Validation

**Test Workflow:**
1. ✅ Load test data → Scoring tab displays
2. ✅ Read explanation text → Left pane shows gear score formula
3. ✅ Check default weights → All spinboxes show 1.0
4. ✅ Click "Reset All" → All weights return to 1.0, status updates
5. ✅ Click "DPS Focus" → Weights change (ATK% 2.0, CRate 2.0, CDmg 2.0, DEF% 0.5, HP% 0.5)
6. ✅ Click "Tank Focus" → Weights change (HP% 2.0, DEF% 2.0, ATK% 0.5, CRate 0.5)
7. ✅ Modify individual weight → Spinbox updates correctly
8. ✅ Click "Apply Weights" → Status shows "Custom weights applied - scores recalculated" (green)
9. ✅ Switch to Inventory tab → Gear scores updated with new weights
10. ✅ Switch to Heroes tab → Gear scores updated in hero details
11. ✅ Apply weights again → Scores recalculate correctly

**Validation:** All scoring functionality works end-to-end

### Checkpoint 4: Cross-Tab Integration

**Test Cross-Tab:**
1. ✅ Load data with known gear
2. ✅ Note gear scores in Inventory tab
3. ✅ Apply DPS preset weights in Scoring tab
4. ✅ Return to Inventory → Verify scores changed
5. ✅ Check Heroes tab → Verify gear scores match
6. ✅ Reset weights → Verify scores return to original values

**Validation:** Cross-tab score updates work correctly

## Migration Strategy

### Phase 1: Extend AppContext
1. Update `ui/context.py` to add `inventory_tab` and `heroes_tab` fields
2. Compile to verify no syntax errors

### Phase 2: Create New Tab
1. Create `ui/tabs/scoring_tab.py`
2. Define `ScoringTab(BaseTab)` class
3. Copy `_init_state()` with state variables
4. Copy `setup_ui()` with all UI code (lines 187-303)
5. Copy all 5 methods (lines 305-355)
6. Update cross-tab refresh to use `self.context.inventory_tab` and `self.context.heroes_tab`
7. Add imports for game_data.STATS

### Phase 3: Update Main GUI
1. Import ScoringTab
2. Set tab instances in AppContext: `self.app_context.inventory_tab = self.inventory_tab_instance`
3. Create instance: `ScoringTab(notebook, app_context)`
4. Add to notebook

### Phase 4: Cleanup
1. Remove old frame creation (lines 179-180)
2. Remove `setup_scoring_tab()` call (line 181)
3. Remove `setup_scoring_tab()` method (lines 187-303)
4. Remove 4 scoring methods (lines 305-355)
5. Remove state variables from `__init__` (if any)

### Phase 5: Validate
1. Run through all 4 validation checkpoints
2. Fix any issues found
3. Confirm all functionality preserved

## Benefits

- ✅ Main GUI reduced from 461 → ~290 lines (37% reduction)
- ✅ ScoringTab is independently maintainable (~170 lines)
- ✅ Clear separation of concerns
- ✅ Follows established BaseTab pattern
- ✅ No breaking changes to user experience
- ✅ Phase 3 complete - ALL tabs extracted!
- ✅ Overall GUI reduction: 3,900 → ~290 lines (93% total!)

## Final State

After this extraction, the UI refactoring is **complete**:

**Extracted Tabs:**
- ✅ MaterialsTab (~118 lines)
- ✅ SetupTab (~175 lines)
- ✅ CaptureTab (~185 lines)
- ✅ InventoryTab (~280 lines)
- ✅ OptimizerTab (~765 lines)
- ✅ HeroesTab (~705 lines)
- ✅ ScoringTab (~170 lines)

**Total Extracted:** ~2,400 lines of tab code
**Main GUI:** ~290 lines (coordinator + lifecycle)
**Reduction:** 3,900 → 290 lines (93%)

## Implementation Plan

See: `PLAN.md` (generated by writing-plans skill)
