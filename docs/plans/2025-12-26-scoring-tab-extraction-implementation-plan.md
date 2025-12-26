# ScoringTab Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans OR superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Extract ScoringTab from main GUI into modular ui/tabs/scoring_tab.py, completing the UI refactoring

**Architecture:** BaseTab + AppContext pattern with cross-tab refresh capabilities via AppContext.inventory_tab and AppContext.heroes_tab

**Tech Stack:** Python, Tkinter, ttk, scrolledtext

---

## Task 1: Extend AppContext with Tab Instance Fields

**Files:**
- Modify: `Vribbels/ui/context.py:1-20`

**Step 1: Add tab instance fields to AppContext**

Open `Vribbels/ui/context.py` and add two new optional fields after `refresh_callback`:

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
    # Tab instance references for cross-tab refresh
    inventory_tab: Optional['InventoryTab'] = None
    heroes_tab: Optional['HeroesTab'] = None
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/context.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/context.py
git commit -m "feat: add inventory_tab and heroes_tab fields to AppContext for cross-tab refresh"
```

---

## Task 2: Create ScoringTab Skeleton

**Files:**
- Create: `Vribbels/ui/tabs/scoring_tab.py`

**Step 1: Create file with imports and class skeleton**

Create `Vribbels/ui/tabs/scoring_tab.py`:

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

    def __init__(self, parent: tk.Widget, context: AppContext):
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()

    def _init_state(self):
        """Initialize state variables."""
        pass

    def setup_ui(self):
        """Setup the Scoring configuration tab UI."""
        pass

    def reset_weights(self):
        """Reset all stat weights to 1.0."""
        pass

    def preset_dps_weights(self):
        """Set weights for DPS-focused scoring."""
        pass

    def preset_tank_weights(self):
        """Set weights for tank-focused scoring."""
        pass

    def apply_custom_weights(self):
        """Apply custom weights and recalculate all gear scores."""
        pass
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: create ScoringTab skeleton with method stubs"
```

---

## Task 3: Implement _init_state()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:26-28`

**Step 1: Implement state variable initialization**

Replace the `_init_state()` method:

```python
    def _init_state(self):
        """Initialize state variables."""
        # Widget references (set in setup_ui)
        self.stat_weight_vars = {}      # Dict[str, tk.DoubleVar] - 16 stat weights
        self.weight_status = None       # ttk.Label - status message
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab._init_state() with 2 state variables"
```

---

## Task 4: Implement setup_ui()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:30-32`

**Step 1: Implement complete UI setup**

Replace the `setup_ui()` method with the complete UI construction code from czn_optimizer_gui.py lines 189-303:

```python
    def setup_ui(self):
        """Setup the Scoring configuration tab UI."""
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main_frame, text="Gear Score Calculation", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(main_frame, text="Configure how gear scores are calculated",
                  foreground=self.colors["fg_dim"]).pack(anchor=tk.W, pady=(0, 10))

        # Split into left (explanation) and right (config)
        content = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True)

        # Left side - Explanation
        explain_frame = ttk.LabelFrame(content, text="How Gear Score Works", padding=10)
        content.add(explain_frame, weight=1)

        explanation = """GEAR SCORE (GS) CALCULATION

The Gear Score measures how well a piece of gear rolled relative to its maximum potential.

FORMULA:
For each substat:
  1. Calculate roll quality = actual_value / (max_roll * num_rolls)
  2. Multiply by number of rolls
  3. Sum all substats and multiply by 10

EXAMPLE:
A substat with 2 rolls that got:
  - Roll 1: 7 (max is 8) = 87.5% quality
  - Roll 2: 6 (max is 8) = 75% quality
  - Total: 13 out of possible 16
  - Contribution: (13/16) * 2 * 10 = 16.25 GS

STAT MAX ROLLS:
These are the maximum values each stat can roll:
  - ATK%/DEF%/HP%: 1.3%
  - Flat ATK: 8
  - Flat DEF: 5
  - Flat HP: 12
  - CRate: 2.0%
  - CDmg: 4.0%
  - Ego: 5
  - Extra DMG%/DoT%: 3.4%
  - Element DMG%: 3.5%

WEIGHTED SCORE:
You can configure custom weights below to emphasize stats you care about. A weight of 1.0 means normal contribution. A weight of 2.0 means that stat contributes double to the score.

POTENTIAL:
Shows the range of possible final GS based on remaining upgrades. Low assumes minimum rolls, high assumes maximum rolls."""

        explain_text = scrolledtext.ScrolledText(explain_frame, height=20, wrap=tk.WORD,
                                                  bg=self.colors["bg_light"], fg=self.colors["fg"],
                                                  font=("Consolas", 9))
        explain_text.insert("1.0", explanation)
        explain_text.config(state=tk.DISABLED)
        explain_text.pack(fill=tk.BOTH, expand=True)

        # Right side - Configuration
        config_frame = ttk.LabelFrame(content, text="Stat Weight Configuration", padding=10)
        content.add(config_frame, weight=1)

        ttk.Label(config_frame, text="Adjust weights for custom scoring (1.0 = normal)",
                  foreground=self.colors["fg_dim"]).pack(anchor=tk.W, pady=(0, 10))

        # Weight configuration
        weights_inner = ttk.Frame(config_frame)
        weights_inner.pack(fill=tk.X)

        stat_display_names = [
            ("Flat ATK", "Flat ATK"), ("ATK%", "ATK%"),
            ("Flat DEF", "Flat DEF"), ("DEF%", "DEF%"),
            ("Flat HP", "Flat HP"), ("HP%", "HP%"),
            ("CRate", "Crit Rate"), ("CDmg", "Crit Damage"),
            ("Ego", "Ego"), ("Extra DMG%", "Extra DMG%"),
            ("DoT%", "DoT%"), ("Passion DMG%", "Passion"),
            ("Order DMG%", "Order"), ("Justice DMG%", "Justice"),
            ("Void DMG%", "Void"), ("Instinct DMG%", "Instinct"),
        ]

        for i, (stat_key, display_name) in enumerate(stat_display_names):
            row = i // 2
            col = i % 2
            frame = ttk.Frame(weights_inner)
            frame.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)

            ttk.Label(frame, text=f"{display_name}:", width=12).pack(side=tk.LEFT)
            var = tk.DoubleVar(value=1.0)
            self.stat_weight_vars[stat_key] = var
            # Use tk.Spinbox with dark theme colors
            spinbox = tk.Spinbox(frame, from_=0.0, to=5.0, increment=0.1, width=5,
                                 textvariable=var, format="%.1f",
                                 bg=self.colors["bg_light"], fg=self.colors["fg"],
                                 buttonbackground=self.colors["bg_lighter"],
                                 insertbackground=self.colors["fg"],
                                 selectbackground=self.colors["select"],
                                 selectforeground=self.colors["fg"],
                                 relief=tk.FLAT, bd=1)
            spinbox.pack(side=tk.LEFT, padx=2)

        # Preset buttons
        preset_frame = ttk.Frame(config_frame)
        preset_frame.pack(fill=tk.X, pady=(15, 5))

        ttk.Label(preset_frame, text="Presets:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(preset_frame, text="Reset All", command=self.reset_weights).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="DPS Focus", command=self.preset_dps_weights).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Tank Focus", command=self.preset_tank_weights).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Apply Weights", command=self.apply_custom_weights).pack(side=tk.LEFT, padx=5)

        # Status
        self.weight_status = ttk.Label(config_frame, text="Using default weights (all 1.0)",
                                        foreground=self.colors["fg_dim"])
        self.weight_status.pack(anchor=tk.W, pady=(10, 0))
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab.setup_ui() with two-pane layout (explanation + config)"
```

---

## Task 5: Implement reset_weights()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:34-36`

**Step 1: Implement reset weights method**

Replace the `reset_weights()` method:

```python
    def reset_weights(self):
        """Reset all stat weights to 1.0."""
        for var in self.stat_weight_vars.values():
            var.set(1.0)
        self.weight_status.config(text="Weights reset to default (all 1.0)")
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab.reset_weights() method"
```

---

## Task 6: Implement preset_dps_weights()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:38-40`

**Step 1: Implement DPS preset method**

Replace the `preset_dps_weights()` method:

```python
    def preset_dps_weights(self):
        """Set weights for DPS-focused scoring."""
        presets = {
            "ATK%": 2.0, "Flat ATK": 1.5, "CRate": 2.0, "CDmg": 2.0,
            "Extra DMG%": 1.5, "DoT%": 1.0,
            "DEF%": 0.5, "Flat DEF": 0.3, "HP%": 0.5, "Flat HP": 0.3,
            "Ego": 1.0,
        }
        for stat, var in self.stat_weight_vars.items():
            var.set(presets.get(stat, 1.0))
        self.weight_status.config(text="Applied DPS preset weights")
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab.preset_dps_weights() method"
```

---

## Task 7: Implement preset_tank_weights()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:42-44`

**Step 1: Implement Tank preset method**

Replace the `preset_tank_weights()` method:

```python
    def preset_tank_weights(self):
        """Set weights for tank-focused scoring."""
        presets = {
            "DEF%": 2.0, "Flat DEF": 1.5, "HP%": 2.0, "Flat HP": 1.5,
            "ATK%": 0.5, "Flat ATK": 0.3, "CRate": 0.5, "CDmg": 0.5,
            "Extra DMG%": 0.3, "DoT%": 0.3, "Ego": 1.0,
        }
        for stat, var in self.stat_weight_vars.items():
            var.set(presets.get(stat, 1.0))
        self.weight_status.config(text="Applied Tank preset weights")
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab.preset_tank_weights() method"
```

---

## Task 8: Implement apply_custom_weights()

**Files:**
- Modify: `Vribbels/ui/tabs/scoring_tab.py:46-48`

**Step 1: Implement apply weights with cross-tab refresh**

Replace the `apply_custom_weights()` method:

```python
    def apply_custom_weights(self):
        """Apply custom weights and recalculate all gear scores."""
        weights = {stat: var.get() for stat, var in self.stat_weight_vars.items()}

        # Recalculate gear scores with custom weights
        for fragment in self.optimizer.fragments:
            weighted_score = 0.0
            for sub in fragment.substats:
                stat_info = STATS.get(sub.raw_name, (sub.name, sub.name, sub.is_percentage, 1.0, 0.5))
                max_roll = stat_info[3]
                normalized = sub.value / (max_roll * sub.roll_count) if max_roll > 0 else 0
                weight = weights.get(sub.name, 1.0)
                weighted_score += normalized * sub.roll_count * weight
            fragment.gear_score = round(weighted_score * 10, 1)
            fragment.calculate_potential()

        # Refresh other tabs via AppContext
        self.context.inventory_tab.refresh_inventory()
        self.context.heroes_tab.refresh_heroes()

        # Update status
        self.weight_status.config(text="Custom weights applied - scores recalculated",
                                   foreground=self.colors["green"])
```

**Step 2: Verify syntax**

Run: `python -m py_compile Vribbels/ui/tabs/scoring_tab.py`
Expected: No errors

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/scoring_tab.py
git commit -m "feat: implement ScoringTab.apply_custom_weights() with cross-tab refresh"
```

---

## Task 9: Add Module Exports

**Files:**
- Modify: `Vribbels/ui/tabs/__init__.py`
- Modify: `Vribbels/ui/__init__.py`

**Step 1: Export ScoringTab from ui/tabs/__init__.py**

Add import and update __all__:

```python
from .materials_tab import MaterialsTab
from .setup_tab import SetupTab
from .capture_tab import CaptureTab
from .inventory_tab import InventoryTab
from .optimizer_tab import OptimizerTab
from .heroes_tab import HeroesTab
from .scoring_tab import ScoringTab

__all__ = ['MaterialsTab', 'SetupTab', 'CaptureTab', 'InventoryTab', 'OptimizerTab', 'HeroesTab', 'ScoringTab']
```

**Step 2: Export ScoringTab from ui/__init__.py**

Update the import:

```python
from .tabs import MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab, ScoringTab

__all__ = [
    'BaseTab',
    'AppContext',
    'MaterialsTab',
    'SetupTab',
    'CaptureTab',
    'InventoryTab',
    'OptimizerTab',
    'HeroesTab',
    'ScoringTab',
]
```

**Step 3: Verify imports**

Run: `python -c "from ui import ScoringTab; print('Import successful')"`
Expected: "Import successful"

**Step 4: Commit**

```bash
git add Vribbels/ui/tabs/__init__.py Vribbels/ui/__init__.py
git commit -m "feat: add ScoringTab to module exports"
```

---

## Task 10: Integrate ScoringTab into Main GUI

**Files:**
- Modify: `Vribbels/czn_optimizer_gui.py:33`
- Modify: `Vribbels/czn_optimizer_gui.py:175-181`

**Step 1: Update import statement**

Change line 33 to import ScoringTab:

```python
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab, ScoringTab
```

**Step 2: Set tab instance references in AppContext**

After creating the heroes_tab_instance (around line 175), add:

```python
        # Set tab instance references for cross-tab refresh
        self.app_context.inventory_tab = self.inventory_tab_instance
        self.app_context.heroes_tab = self.heroes_tab_instance
```

**Step 3: Create ScoringTab instance**

Replace lines 179-181 (old frame creation and setup call) with:

```python
        self.scoring_tab_instance = ScoringTab(self.notebook, self.app_context)
        self.scoring_tab = self.scoring_tab_instance.get_frame()
        self.notebook.add(self.scoring_tab, text="Scoring")
```

**Step 4: Verify application starts**

Run: `python Vribbels/czn_optimizer_gui.py`
Expected: Application window opens with Scoring tab visible

**Step 5: Commit**

```bash
git add Vribbels/czn_optimizer_gui.py
git commit -m "feat: integrate ScoringTab instance into main GUI"
```

---

## Task 11: Remove Old Code from Main GUI

**Files:**
- Modify: `Vribbels/czn_optimizer_gui.py:187-355`

**Step 1: Remove setup_scoring_tab method**

Delete lines 187-303 (entire setup_scoring_tab method)

**Step 2: Remove reset_weights method**

Delete lines 305-309 (entire reset_weights method)

**Step 3: Remove preset_dps_weights method**

Delete lines 311-321 (entire preset_dps_weights method)

**Step 4: Remove preset_tank_weights method**

Delete lines 323-332 (entire preset_tank_weights method)

**Step 5: Remove apply_custom_weights method**

Delete lines 334-355 (entire apply_custom_weights method)

**Step 6: Verify application still works**

Run: `python Vribbels/czn_optimizer_gui.py`
Expected: Application starts, Scoring tab works

**Step 7: Commit**

```bash
git add Vribbels/czn_optimizer_gui.py
git commit -m "refactor: remove old ScoringTab code from main GUI (~169 lines)"
```

---

## Task 12: Functional Validation

**Files:**
- N/A (manual testing)

**Step 1: Basic UI validation**

Run: `python Vribbels/czn_optimizer_gui.py`

Test:
1. ✅ Scoring tab appears in notebook
2. ✅ Left pane shows gear score explanation text
3. ✅ Right pane shows 16 stat weight spinboxes
4. ✅ All spinboxes default to 1.0
5. ✅ Status shows "Using default weights (all 1.0)"

**Step 2: Preset validation**

Test:
1. ✅ Click "Reset All" → All spinboxes return to 1.0, status updates
2. ✅ Click "DPS Focus" → Weights change (ATK% 2.0, CRate 2.0, CDmg 2.0, DEF% 0.5)
3. ✅ Click "Tank Focus" → Weights change (HP% 2.0, DEF% 2.0, ATK% 0.5)
4. ✅ Manually modify a spinbox → Value updates correctly

**Step 3: Cross-tab integration validation**

Test:
1. ✅ Load test data file
2. ✅ Note gear scores in Inventory tab
3. ✅ Go to Scoring tab, click "Apply Weights"
4. ✅ Status shows "Custom weights applied - scores recalculated" (green)
5. ✅ Return to Inventory tab → Verify scores unchanged (weights all 1.0)
6. ✅ Go to Scoring tab, click "DPS Focus" then "Apply Weights"
7. ✅ Return to Inventory tab → Verify scores changed
8. ✅ Check Heroes tab → Verify gear scores match
9. ✅ Reset weights and apply → Verify scores return to original

**Step 4: Document completion**

Expected: All validation tests pass

**Step 5: Final commit**

```bash
git commit --allow-empty -m "test: manual functional validation complete - all scoring features working"
```

---

## Summary

**Total Tasks:** 12
**Estimated Time:** 2-3 hours
**Files Created:** 1 (scoring_tab.py)
**Files Modified:** 5 (context.py, 2x __init__.py, czn_optimizer_gui.py)
**Lines Extracted:** ~170
**Main GUI Reduction:** 461 → ~290 lines (37% reduction)
**Total Project Reduction:** 3,900 → ~290 lines (93% total!)

**Completion Criteria:**
- ✅ ScoringTab extracted to modular file
- ✅ All 5 methods implemented
- ✅ AppContext extended for cross-tab refresh
- ✅ Main GUI updated to use ScoringTab instance
- ✅ Old code removed from main GUI
- ✅ All functional validation tests pass
- ✅ UI refactoring 100% complete!
