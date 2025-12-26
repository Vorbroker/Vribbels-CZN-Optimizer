# HeroesTab Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract HeroesTab (~466 lines) from main GUI into modular `ui/tabs/heroes_tab.py` following BaseTab + AppContext pattern

**Architecture:** Self-contained HeroesTab class inheriting from BaseTab, managing 17 state variables, with public API `refresh_heroes()` called from load_data()

**Tech Stack:** Python 3.x, Tkinter, ttk, BaseTab pattern, AppContext dependency injection

---

## Task 1: Create HeroesTab File with Basic Structure

**Files:**
- Create: `Vribbels/ui/tabs/heroes_tab.py`

**Step 1: Create file with imports and class skeleton**

Create `Vribbels/ui/tabs/heroes_tab.py`:

```python
"""
Heroes/Combatants display tab.

Provides sortable list of heroes with detailed gear display.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ui.base_tab import BaseTab
from ui.context import AppContext
from game_data import (
    EQUIPMENT_SLOTS, SETS, STATS, RARITY_COLORS, RARITY_BG_COLORS,
    RARITY_STARTING_SUBSTATS, ATTRIBUTE_COLORS,
    get_character_by_name, get_partner, get_partner_stats,
    get_partner_passive_info, get_potential_stat_bonus
)
from models import Stat


class HeroesTab(BaseTab):
    """Heroes/Combatants list and detail display."""

    def __init__(self, parent: tk.Widget, context: AppContext):
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()

    def _init_state(self):
        """Initialize all state variables."""
        pass  # Implement in next task

    def setup_ui(self):
        """Setup the Heroes tab UI."""
        pass  # Implement in later task

    # Public API
    def refresh_heroes(self):
        """Refresh the heroes list."""
        pass  # Implement in later task

    # Sorting and display
    def sort_heroes(self, col: str):
        """Sort heroes by column."""
        pass  # Implement in later task

    def select_hero_row(self, index: int):
        """Select a hero row."""
        pass  # Implement in later task

    def show_hero_details(self, hero_name: str):
        """Show hero details."""
        pass  # Implement in later task

    # Helper methods
    def format_roll_with_color(self, sub: Stat, parent_frame: tk.Frame, bg_color: str):
        """Format substat roll with color."""
        pass  # Implement in later task

    def _update_hero_scrollregion(self):
        """Update scroll region."""
        pass  # Implement in later task

    def _on_hero_canvas_configure(self, event):
        """Handle canvas resize."""
        pass  # Implement in later task
```

**Step 2: Verify file compiles**

Run: `cd .worktrees/heroes-tab-extraction && python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
cd .worktrees/heroes-tab-extraction
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: create HeroesTab skeleton with method stubs"
```

---

## Task 2: Implement _init_state() Method

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:30-31`

**Step 1: Implement state variable initialization**

Replace the `_init_state()` method:

```python
    def _init_state(self):
        """Initialize all state variables."""
        # Sorting state
        self.hero_sort_col = "name"
        self.hero_sort_reverse = False

        # Canvas/List widgets (set in setup_ui)
        self.hero_canvas = None
        self.hero_list_frame = None
        self.hero_canvas_window = None
        self.hero_row_widgets = []
        self.hero_data_list = []
        self.hero_col_char_widths = None
        self.selected_hero_index = -1
        self.hero_header_labels = []

        # Detail widgets (set in setup_ui)
        self.user_info_label = None
        self.hero_detail_name = None
        self.hero_char_info = None
        self.hero_partner_text = None
        self.hero_stats_label = None
        self.gear_frames = {}
        self.gear_labels = {}
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab._init_state() with 17 state variables"
```

---

## Task 3: Implement Helper Methods

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:64-72`

**Step 1: Implement _update_hero_scrollregion()**

Replace the `_update_hero_scrollregion()` stub with:

```python
    def _update_hero_scrollregion(self):
        """Update scroll region and ensure content stays at top when it fits"""
        self.hero_canvas.configure(scrollregion=self.hero_canvas.bbox("all"))
        # If content fits in view, reset to top
        if self.hero_canvas.bbox("all"):
            content_height = self.hero_canvas.bbox("all")[3]
            visible_height = self.hero_canvas.winfo_height()
            if content_height <= visible_height:
                self.hero_canvas.yview_moveto(0)
```

**Step 2: Implement _on_hero_canvas_configure()**

Replace the `_on_hero_canvas_configure()` stub with:

```python
    def _on_hero_canvas_configure(self, event):
        """Handle canvas resize - update width and check scrolling"""
        self.hero_canvas.itemconfig(self.hero_canvas_window, width=event.width)
        # Check if we need to reset scroll position
        if self.hero_canvas.bbox("all"):
            content_height = self.hero_canvas.bbox("all")[3]
            if content_height <= event.height:
                self.hero_canvas.yview_moveto(0)
```

**Step 3: Implement format_roll_with_color()**

Replace the `format_roll_with_color()` stub with:

```python
    def format_roll_with_color(self, sub: Stat, parent_frame: tk.Frame, bg_color: str):
        """Format a substat roll string with individual roll coloring"""
        stat_info = STATS.get(sub.raw_name, (sub.name, sub.name, sub.is_percentage, 1.0, 0.5))
        max_roll = stat_info[3]
        min_roll = stat_info[4]

        # Build the display text with color info
        parts = []

        if sub.roll_count > 1 and sub.rolls:
            # Has upgrades - format: "Stat +total (base,+upg1,+upg2)"
            for roll in sub.rolls:
                if roll.stat_type in [1, 2]:  # Base or added stat
                    val_str = f"{roll.value:.0f}" if not sub.is_percentage else f"{roll.value:.1f}"
                    if roll.is_max_roll:
                        parts.append((val_str, self.colors["green"]))
                    elif roll.is_min_roll:
                        parts.append((val_str, self.colors["red"]))
                    else:
                        parts.append((val_str, self.colors["fg_dim"]))
                else:  # Upgrade roll (type 3)
                    val_str = f"+{roll.value:.0f}" if not sub.is_percentage else f"+{roll.value:.1f}"
                    is_min = abs(roll.value - min_roll) < 0.01
                    is_max = abs(roll.value - max_roll) < 0.01
                    if is_max:
                        parts.append((val_str, self.colors["green"]))
                    elif is_min:
                        parts.append((val_str, self.colors["red"]))
                    else:
                        parts.append((val_str, self.colors["fg_dim"]))

            return parts
        else:
            # Single roll - just color the total
            val_str = sub.format_value()
            if sub.rolls and len(sub.rolls) > 0:
                if sub.rolls[0].is_max_roll:
                    return [(val_str, self.colors["green"])]
                elif sub.rolls[0].is_min_roll:
                    return [(val_str, self.colors["red"])]
            return [(val_str, self.colors["fg"])]
```

**Step 4: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 5: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab helper methods (scroll, resize, format_roll)"
```

---

## Task 4: Implement sort_heroes() Method

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:46-49`

**Step 1: Implement sort_heroes()**

Replace the `sort_heroes()` stub with:

```python
    def sort_heroes(self, col: str):
        """Sort heroes list by column"""
        if col == self.hero_sort_col:
            self.hero_sort_reverse = not self.hero_sort_reverse
        else:
            self.hero_sort_col = col
            self.hero_sort_reverse = col in ["gs", "grade", "ego"]

        self.refresh_heroes()
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab.sort_heroes() method"
```

---

## Task 5: Implement setup_ui() Method (Part 1 - Structure)

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:33-35`

**Step 1: Implement setup_ui() - User info frame and layout**

Replace the `setup_ui()` stub with the beginning of the UI construction:

```python
    def setup_ui(self):
        """Setup the Heroes tab UI."""
        user_frame = ttk.Frame(self.frame)
        user_frame.pack(fill=tk.X, padx=10, pady=5)

        self.user_info_label = ttk.Label(user_frame, text="No user data available", font=("Segoe UI", 10))
        self.user_info_label.pack(anchor=tk.W)

        content_frame = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        list_frame = ttk.LabelFrame(content_frame, text="Combatants", padding=5)
        content_frame.add(list_frame, weight=1)

        # Continued in next step...
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: Syntax error - method incomplete
Note: Will fix in next step

---

## Task 6: Implement setup_ui() Method (Part 2 - Hero List)

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:33-35`

**Step 1: Complete setup_ui() with hero list and detail pane**

Replace the entire `setup_ui()` method with:

```python
    def setup_ui(self):
        """Setup the Heroes tab UI."""
        user_frame = ttk.Frame(self.frame)
        user_frame.pack(fill=tk.X, padx=10, pady=5)

        self.user_info_label = ttk.Label(user_frame, text="No user data available", font=("Segoe UI", 10))
        self.user_info_label.pack(anchor=tk.W)

        content_frame = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        list_frame = ttk.LabelFrame(content_frame, text="Combatants", padding=5)
        content_frame.add(list_frame, weight=1)

        # Custom scrollable list with per-cell coloring
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        # Header row - use Labels with click bindings for consistent alignment with data rows
        header_frame = tk.Frame(list_container, bg=self.colors["bg_lighter"])
        header_frame.pack(fill=tk.X)

        # Use character widths for consistency between headers and data rows
        col_char_widths = [12, 6, 9, 10, 7, 5, 5]  # Character widths for each column
        col_names = ["Combatant", "Grade", "Attribute", "Class", "Level", "Ego", "GS"]
        col_keys = ["name", "grade", "attribute", "class", "level", "ego", "gs"]

        self.hero_header_labels = []
        for i, (name, char_width) in enumerate(zip(col_names, col_char_widths)):
            lbl = tk.Label(header_frame, text=name, width=char_width,
                          bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                          font=("Segoe UI", 9, "bold"),
                          anchor=tk.W if i == 0 else tk.CENTER,
                          cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=1)
            lbl.bind("<Button-1>", lambda e, k=col_keys[i]: self.sort_heroes(k))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(fg=self.colors["accent"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(fg=self.colors["fg"]))
            self.hero_header_labels.append(lbl)

        # Scrollable canvas for hero rows
        canvas_frame = tk.Frame(list_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.hero_canvas = tk.Canvas(canvas_frame, bg=self.colors["bg"], highlightthickness=0)
        hero_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.hero_canvas.yview)
        self.hero_list_frame = tk.Frame(self.hero_canvas, bg=self.colors["bg"])

        self.hero_canvas.configure(yscrollcommand=hero_scroll.set)
        hero_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.hero_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hero_canvas_window = self.hero_canvas.create_window((0, 0), window=self.hero_list_frame, anchor=tk.NW)

        self.hero_list_frame.bind("<Configure>", lambda e: self._update_hero_scrollregion())
        self.hero_canvas.bind("<Configure>", lambda e: self._on_hero_canvas_configure(e))

        # Mouse wheel scrolling - only scroll when needed
        def on_mousewheel(event):
            # Only scroll if content is larger than visible area
            if self.hero_canvas.bbox("all"):
                content_height = self.hero_canvas.bbox("all")[3]
                visible_height = self.hero_canvas.winfo_height()
                if content_height > visible_height:
                    self.hero_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.hero_canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.hero_row_widgets = []  # Store row widgets for selection
        self.selected_hero_index = -1
        self.hero_col_char_widths = col_char_widths  # Store character widths for data rows
        self.hero_data_list = []  # Store hero data for selection lookup

        detail_frame = ttk.LabelFrame(content_frame, text="Combatant Details", padding=5)
        content_frame.add(detail_frame, weight=2)

        self.hero_detail_name = ttk.Label(detail_frame, text="Select a combatant", font=("Segoe UI", 14, "bold"))
        self.hero_detail_name.pack(anchor=tk.W, pady=(0, 5))

        # Info frame with Character and Partner Card
        # Character takes only needed space, Partner Card fills remaining with text wrapping
        info_frame = ttk.Frame(detail_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        char_frame = ttk.LabelFrame(info_frame, text="Character", padding=5)
        char_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.hero_char_info = ttk.Label(char_frame, text="", justify=tk.LEFT)
        self.hero_char_info.pack(anchor=tk.W)

        partner_frame = ttk.LabelFrame(info_frame, text="Partner Card", padding=5)
        partner_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        # Use a Text widget for Partner Card to allow proper wrapping
        self.hero_partner_text = tk.Text(partner_frame, wrap=tk.WORD, height=6,
                                         bg=self.colors["bg_light"], fg=self.colors["fg"],
                                         font=("Segoe UI", 9), bd=0, highlightthickness=0,
                                         padx=2, pady=2)
        self.hero_partner_text.pack(fill=tk.BOTH, expand=True)
        self.hero_partner_text.config(state=tk.DISABLED)

        stats_frame = ttk.LabelFrame(detail_frame, text="Build Stats", padding=5)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.hero_stats_label = ttk.Label(stats_frame, text="", justify=tk.LEFT)
        self.hero_stats_label.pack(anchor=tk.W)

        gear_outer_frame = ttk.LabelFrame(detail_frame, text="Equipped Memory Fragments", padding=5)
        gear_outer_frame.pack(fill=tk.BOTH, expand=True)

        self.gear_frames = {}
        self.gear_labels = {}

        gear_grid = ttk.Frame(gear_outer_frame)
        gear_grid.pack(fill=tk.BOTH, expand=True)

        slot_positions = [
            (3, 0, 0), (4, 0, 1),
            (2, 1, 0), (5, 1, 1),
            (1, 2, 0), (6, 2, 1),
        ]

        for slot_num, row, col in slot_positions:
            slot_name = EQUIPMENT_SLOTS.get(slot_num, f"Slot {slot_num}")

            frame = tk.Frame(gear_grid, bg=self.colors["bg_light"], relief=tk.RIDGE, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")

            header = tk.Label(frame, text=slot_name, font=("Segoe UI", 9, "bold"),
                            bg=self.colors["bg_light"], fg=self.colors["fg_dim"])
            header.pack(anchor=tk.W, padx=5, pady=(3, 0))

            main_stat = tk.Label(frame, text="", font=("Segoe UI", 9, "bold"),
                               bg=self.colors["bg_light"], fg=self.colors["orange"])
            main_stat.pack(anchor=tk.W, padx=5)

            sub_frames = []
            for i in range(4):
                sub_frame = tk.Frame(frame, bg=self.colors["bg_light"])
                sub_frame.pack(anchor=tk.W, padx=5, fill=tk.X)

                gs_contrib = tk.Label(sub_frame, text="", font=("Segoe UI", 7),
                                     bg=self.colors["bg_light"], fg=self.colors["accent"], width=3, anchor=tk.E)
                gs_contrib.pack(side=tk.LEFT)

                # Use Text widget for colored roll values
                sub_text = tk.Text(sub_frame, font=("Segoe UI", 8), height=1, width=40,
                                   bg=self.colors["bg_light"], fg=self.colors["fg"],
                                   bd=0, highlightthickness=0, padx=2, pady=0)
                sub_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
                # Configure tags for roll colors
                sub_text.tag_configure("max_roll", foreground=self.colors["green"])
                sub_text.tag_configure("min_roll", foreground=self.colors["red"])
                sub_text.tag_configure("normal", foreground=self.colors["yellow"])  # Mid-rolls in yellow
                sub_text.tag_configure("added", foreground=self.colors["fg"])  # Same as default
                sub_text.tag_configure("default", foreground=self.colors["fg"])
                sub_text.config(state=tk.DISABLED)

                sub_frames.append({"frame": sub_frame, "gs": gs_contrib, "text": sub_text})

            set_label = tk.Label(frame, text="", font=("Segoe UI", 8),
                               bg=self.colors["bg_light"], fg=self.colors["fg_dim"])
            set_label.pack(anchor=tk.W, padx=5, pady=(2, 0))

            # GS and Potential on same line
            gs_frame = tk.Frame(frame, bg=self.colors["bg_light"])
            gs_frame.pack(anchor=tk.W, padx=5, pady=(0, 3), fill=tk.X)

            gs_label = tk.Label(gs_frame, text="", font=("Segoe UI", 8, "bold"),
                               bg=self.colors["bg_light"], fg=self.colors["accent"])
            gs_label.pack(side=tk.LEFT)

            pot_label = tk.Label(gs_frame, text="", font=("Segoe UI", 8),
                                bg=self.colors["bg_light"], fg=self.colors["fg_dim"])
            pot_label.pack(side=tk.LEFT, padx=(10, 0))

            self.gear_frames[slot_num] = frame
            self.gear_labels[slot_num] = {
                "header": header,
                "main": main_stat,
                "subs": sub_frames,
                "set": set_label,
                "gs": gs_label,
                "potential": pot_label,
                "gs_frame": gs_frame
            }

        gear_grid.columnconfigure(0, weight=1)
        gear_grid.columnconfigure(1, weight=1)
        gear_grid.rowconfigure(0, weight=1)
        gear_grid.rowconfigure(1, weight=1)
        gear_grid.rowconfigure(2, weight=1)
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab.setup_ui() method (UI construction)"
```

---

## Task 7: Implement refresh_heroes() Method

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:39-42`

**Step 1: Implement refresh_heroes()**

Replace the `refresh_heroes()` stub with:

```python
    def refresh_heroes(self):
        """Refresh the heroes list."""
        # Clear existing rows
        for widget in self.hero_list_frame.winfo_children():
            widget.destroy()
        self.hero_row_widgets = []

        user = self.optimizer.user_info
        if user.nickname:
            user_text = (
                f"User: {user.nickname}  |  Level {user.level}  |  "
                f"Logins: {user.login_total}, Streak {user.login_continuous} (Best: {user.login_highest_continuous})"
            )
        else:
            user_text = "No user data available"
        self.user_info_label.config(text=user_text)

        all_heroes = set(self.optimizer.characters.keys()) | set(self.optimizer.character_info.keys())

        # Build hero data for sorting
        self.hero_data_list = []
        for hero in all_heroes:
            gear = self.optimizer.characters.get(hero, [])
            char_info = self.optimizer.character_info.get(hero)

            gs = sum(f.gear_score for f in gear)
            hero_data = get_character_by_name(hero)
            grade = hero_data.get("grade", 0)
            attribute = hero_data.get("attribute", "Unknown")
            hero_class = hero_data.get("class", "Unknown")

            if char_info:
                level = char_info.level
                max_level = char_info.max_level
                ego = char_info.limit_break
            else:
                level = 0
                max_level = 0
                ego = 0

            self.hero_data_list.append({
                "name": hero,
                "grade": grade,
                "attribute": attribute,
                "class": hero_class,
                "level": level,
                "max_level": max_level,
                "ego": ego,
                "gs": gs
            })

        # Sort heroes
        sort_key_map = {
            "name": lambda h: h["name"],
            "grade": lambda h: h["grade"],
            "attribute": lambda h: h["attribute"],
            "class": lambda h: h["class"],
            "level": lambda h: h["level"],
            "ego": lambda h: h["ego"],
            "gs": lambda h: h["gs"],
        }

        key_func = sort_key_map.get(self.hero_sort_col, lambda h: h["name"])
        self.hero_data_list.sort(key=key_func, reverse=self.hero_sort_reverse)

        # Create rows with individually colored cells
        for i, h in enumerate(self.hero_data_list):
            level_str = f"{h['level']}/{h['max_level']}" if h['max_level'] > 0 else "-"
            ego_str = f"E{h['ego']}" if h['max_level'] > 0 else "-"
            gs_str = f"{h['gs']:.0f}" if h['gs'] > 0 else "-"

            row_frame = tk.Frame(self.hero_list_frame, bg=self.colors["bg"])
            row_frame.pack(fill=tk.X)

            # Store reference to row data
            row_frame.hero_index = i
            row_frame.hero_name = h["name"]

            # Column values
            values = [h["name"], f"{h['grade']}*", h["attribute"], h["class"], level_str, ego_str, gs_str]

            labels = []
            for j, (val, char_width) in enumerate(zip(values, self.hero_col_char_widths)):
                # Determine color - only attribute column (index 2) gets colored
                if j == 2:  # Attribute column
                    fg_color = ATTRIBUTE_COLORS.get(h["attribute"], self.colors["fg"])
                else:
                    fg_color = self.colors["fg"]

                lbl = tk.Label(row_frame, text=val, width=char_width, anchor=tk.W if j == 0 else tk.CENTER,
                              bg=self.colors["bg"], fg=fg_color, font=("Segoe UI", 9))
                lbl.pack(side=tk.LEFT, padx=1)
                lbl.bind("<Button-1>", lambda e, idx=i: self.select_hero_row(idx))
                labels.append(lbl)

            row_frame.labels = labels
            row_frame.bind("<Button-1>", lambda e, idx=i: self.select_hero_row(idx))
            self.hero_row_widgets.append(row_frame)

        # Select first hero
        if self.hero_row_widgets:
            self.select_hero_row(0)
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab.refresh_heroes() method"
```

---

## Task 8: Implement select_hero_row() Method

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:51-54`

**Step 1: Implement select_hero_row()**

Replace the `select_hero_row()` stub with:

```python
    def select_hero_row(self, index: int):
        """Select a hero row and update display"""
        # Deselect previous - reset ALL labels to proper colors
        if 0 <= self.selected_hero_index < len(self.hero_row_widgets):
            old_row = self.hero_row_widgets[self.selected_hero_index]
            old_row.config(bg=self.colors["bg"])
            old_hero_data = self.hero_data_list[self.selected_hero_index]
            for j, lbl in enumerate(old_row.labels):
                lbl.config(bg=self.colors["bg"])
                # Restore attribute color for attribute column (index 2)
                if j == 2:
                    attr_color = ATTRIBUTE_COLORS.get(old_hero_data["attribute"], self.colors["fg"])
                    lbl.config(fg=attr_color)
                else:
                    lbl.config(fg=self.colors["fg"])

        # Select new
        self.selected_hero_index = index
        if 0 <= index < len(self.hero_row_widgets):
            new_row = self.hero_row_widgets[index]
            new_row.config(bg=self.colors["select"])
            new_hero_data = self.hero_data_list[index]
            for j, lbl in enumerate(new_row.labels):
                lbl.config(bg=self.colors["select"])
                # Keep attribute color for attribute column
                if j == 2:
                    attr_color = ATTRIBUTE_COLORS.get(new_hero_data["attribute"], self.colors["fg"])
                    lbl.config(fg=attr_color)

            # Trigger detail update
            hero_name = new_row.hero_name
            self.show_hero_details(hero_name)
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement HeroesTab.select_hero_row() method"
```

---

## Task 9: Implement show_hero_details() Method (Part 1)

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:56-59`

**Step 1: Implement show_hero_details() - Character and Partner info**

Replace the `show_hero_details()` stub with the first half:

```python
    def show_hero_details(self, hero_name: str):
        """Show hero details including character info, partner, stats, and gear"""
        self.hero_detail_name.config(text=hero_name)

        char_info = self.optimizer.character_info.get(hero_name)
        if char_info:
            fb = char_info.friendship_bonus
            hero_data = get_character_by_name(hero_name)
            grade = hero_data.get("grade", "?")
            attribute = hero_data.get("attribute", "Unknown")
            hero_class = hero_data.get("class", "Unknown")

            # Build potential info string
            potential_lines = []
            if char_info.potential_50_level > 0 or char_info.potential_60_level > 0:
                if char_info.potential_50_level > 0:
                    stat_type_50, bonus_50 = get_potential_stat_bonus(
                        char_info.res_id, 50, char_info.potential_50_level
                    )
                    if stat_type_50:
                        potential_lines.append(f"  Node 5: Lv{char_info.potential_50_level} ({stat_type_50} +{bonus_50:.1f}%)")

                if char_info.potential_60_level > 0:
                    stat_type_60, bonus_60 = get_potential_stat_bonus(
                        char_info.res_id, 60, char_info.potential_60_level
                    )
                    if stat_type_60:
                        potential_lines.append(f"  Node 6: Lv{char_info.potential_60_level} ({stat_type_60} +{bonus_60:.1f}%)")

            potential_str = "\n".join(potential_lines) if potential_lines else "  None"

            char_text = (
                f"Grade: {grade}*  |  {attribute}  |  {hero_class}\n"
                f"Level: {char_info.level}/{char_info.max_level}\n"
                f"Ego Manifestation: E{char_info.limit_break}\n"
                f"Friendship Lv: {char_info.friendship_index}\n"
                f"  Bonus: ATK+{fb[0]}, DEF+{fb[1]}, HP+{fb[2]}\n"
                f"Potential:\n{potential_str}"
            )
            self.hero_char_info.config(text=char_text)

            if char_info.partner_name:
                # Get partner stats
                partner_stats = get_partner_stats(char_info.partner_res_id, char_info.partner_level)

                # Get partner metadata (grade and class)
                partner_data = get_partner(char_info.partner_res_id)
                partner_grade = partner_data.get("grade", 3)
                partner_class = partner_data.get("class", "Unknown")

                # Get partner passive and ego skill info
                passive_info = get_partner_passive_info(
                    char_info.partner_res_id, char_info.partner_limit_break
                )

                partner_text = (
                    f"{char_info.partner_name}  ({partner_grade}* {partner_class})\n"
                    f"Level: {char_info.partner_level}/{char_info.partner_max_level}  |  Ego: E{char_info.partner_limit_break}\n"
                    f"Stats: ATK+{partner_stats['atk']}, DEF+{partner_stats['def']}, HP+{partner_stats['hp']}\n"
                    f"\n{passive_info['passive_name']}\n"
                    f"{passive_info['passive_desc']}\n"
                    f"\n{passive_info['ego_name']} - {passive_info['ego_cost']} EP\n"
                    f"{passive_info['ego_desc']}"
                )
            else:
                partner_text = "No partner equipped"
            # Update partner card Text widget
            self.hero_partner_text.config(state=tk.NORMAL)
            self.hero_partner_text.delete("1.0", tk.END)
            self.hero_partner_text.insert("1.0", partner_text)
            self.hero_partner_text.config(state=tk.DISABLED)
        else:
            self.hero_char_info.config(text="No character data available")
            # Update partner card Text widget
            self.hero_partner_text.config(state=tk.NORMAL)
            self.hero_partner_text.delete("1.0", tk.END)
            self.hero_partner_text.insert("1.0", "No partner data")
            self.hero_partner_text.config(state=tk.DISABLED)

        # Gear display will be added in next task
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: implement show_hero_details() part 1 (character/partner info)"
```

---

## Task 10: Implement show_hero_details() Method (Part 2 - Gear Display)

**Files:**
- Modify: `Vribbels/ui/tabs/heroes_tab.py:56-59`

**Step 1: Complete show_hero_details() with gear display**

Update `show_hero_details()` to add the gear display logic after the partner section:

Replace the comment `# Gear display will be added in next task` with:

```python
        gear = self.optimizer.characters.get(hero_name, [])
        gear_by_slot = {p.slot_num: p for p in gear}
        total_gs = 0

        for slot_num in range(1, 7):
            labels = self.gear_labels.get(slot_num)
            if not labels:
                continue

            piece = gear_by_slot.get(slot_num)

            if piece:
                total_gs += piece.gear_score
                rarity_color = RARITY_COLORS.get(piece.rarity_num, self.colors["fg"])
                bg_color = RARITY_BG_COLORS.get(piece.rarity_num, self.colors["bg_light"])

                # Update header to include gear level
                slot_name = EQUIPMENT_SLOTS.get(slot_num, f"Slot {slot_num}")
                labels["header"].config(text=f"{slot_name}  +{piece.level}", fg=rarity_color)

                if piece.main_stat:
                    main_text = f"{piece.main_stat.name}  +{piece.main_stat.format_value()}"
                    labels["main"].config(text=main_text, fg=rarity_color)
                else:
                    labels["main"].config(text="")

                num_starting = RARITY_STARTING_SUBSTATS.get(piece.rarity_num, 3)

                for i, sub_data in enumerate(labels["subs"]):
                    if i < len(piece.substats):
                        sub = piece.substats[i]

                        gs_contrib = sub.get_gs_contribution()
                        sub_data["gs"].config(text=f"{gs_contrib:.1f}")

                        # Get the Text widget
                        text_widget = sub_data["text"]

                        # Build stat name + total
                        stat_name = sub.name
                        total_val = sub.format_value()

                        # Get roll color info
                        roll_parts = self.format_roll_with_color(sub, sub_data["frame"], bg_color)

                        # Check if this is an added stat (type 2)
                        is_added = i >= num_starting

                        # Enable widget for editing
                        text_widget.config(state=tk.NORMAL)
                        text_widget.delete("1.0", tk.END)

                        # Determine base tag for stat name
                        base_tag = "added" if is_added else "default"

                        if sub.roll_count > 1:
                            # Format: "Stat +total (base | +upg1, +upg2)"
                            text_widget.insert(tk.END, f"{stat_name} +{total_val} (", base_tag)

                            base_shown = False
                            for idx, (roll_text, roll_color) in enumerate(roll_parts):
                                # Determine the tag based on color
                                if roll_color == self.colors["green"]:
                                    tag = "max_roll"
                                elif roll_color == self.colors["red"]:
                                    tag = "min_roll"
                                else:
                                    tag = "normal"

                                # First roll is base stat, rest are upgrades
                                if idx == 0:
                                    text_widget.insert(tk.END, roll_text, tag)
                                    base_shown = True
                                else:
                                    if idx == 1 and base_shown:
                                        text_widget.insert(tk.END, " | ", base_tag)
                                    elif idx > 1:
                                        text_widget.insert(tk.END, ", ", base_tag)
                                    text_widget.insert(tk.END, roll_text, tag)

                            text_widget.insert(tk.END, ")", base_tag)
                        else:
                            # Single roll - color the value if max/min
                            text_widget.insert(tk.END, f"{stat_name} +", base_tag)
                            if roll_parts and len(roll_parts) > 0:
                                roll_color = roll_parts[0][1]
                                if roll_color == self.colors["green"]:
                                    tag = "max_roll"
                                elif roll_color == self.colors["red"]:
                                    tag = "min_roll"
                                else:
                                    tag = base_tag
                                text_widget.insert(tk.END, total_val, tag)
                            else:
                                text_widget.insert(tk.END, total_val, base_tag)

                        # Disable widget and update background
                        text_widget.config(state=tk.DISABLED, bg=bg_color)

                        sub_data["frame"].config(bg=bg_color)
                        sub_data["gs"].config(bg=bg_color)
                    else:
                        text_widget = sub_data["text"]
                        text_widget.config(state=tk.NORMAL)
                        text_widget.delete("1.0", tk.END)
                        text_widget.config(state=tk.DISABLED, bg=bg_color)
                        sub_data["gs"].config(text="", bg=bg_color)
                        sub_data["frame"].config(bg=bg_color)

                set_pieces = piece.get_set_pieces()
                # Get bonus description from SETS
                set_info = SETS.get(piece.set_id)
                bonus_text = set_info.get("bonus", "") if set_info else ""
                labels["set"].config(text=f"{piece.set_name} ({set_pieces}) {bonus_text}")

                labels["gs"].config(text=f"GS: {piece.gear_score:.0f}")

                # Add potential display
                if piece.potential_low != piece.potential_high:
                    pot_text = f"Potential: {piece.potential_low:.0f}-{piece.potential_high:.0f}"
                else:
                    pot_text = ""
                labels["potential"].config(text=pot_text)

                self.gear_frames[slot_num].config(bg=bg_color)
                for widget in [labels["header"], labels["main"], labels["set"], labels["gs"], labels["potential"], labels["gs_frame"]]:
                    widget.config(bg=bg_color)
            else:
                bg_color = self.colors["bg_light"]
                # Reset header to just slot name
                slot_name = EQUIPMENT_SLOTS.get(slot_num, f"Slot {slot_num}")
                labels["header"].config(text=slot_name, fg=self.colors["fg_dim"])
                labels["main"].config(text="Empty", fg=self.colors["fg_dim"])
                for sub_data in labels["subs"]:
                    sub_data["gs"].config(text="", bg=bg_color)
                    # Clear Text widget properly
                    text_widget = sub_data["text"]
                    text_widget.config(state=tk.NORMAL)
                    text_widget.delete("1.0", tk.END)
                    text_widget.config(state=tk.DISABLED, bg=bg_color)
                    sub_data["frame"].config(bg=bg_color)
                labels["set"].config(text="")
                labels["gs"].config(text="")
                labels["potential"].config(text="")

                self.gear_frames[slot_num].config(bg=bg_color)
                for widget in [labels["header"], labels["main"], labels["set"], labels["gs"], labels["potential"], labels["gs_frame"]]:
                    widget.config(bg=bg_color)

        if gear:
            stats = self.optimizer.calculate_build_stats(gear, hero_name)
            set_counts = {}
            for f in gear:
                set_counts[f.set_name] = set_counts.get(f.set_name, 0) + 1
            sets_str = " + ".join(f"{c}x{n}" for n, c in set_counts.items() if c >= 2)

            stats_text = (
                f"Total GS: {total_gs:.0f}  |  Sets: {sets_str}\n"
                f"ATK: {stats.get('ATK', 0):.0f}  |  DEF: {stats.get('DEF', 0):.0f}  |  HP: {stats.get('HP', 0):.0f}\n"
                f"CRate: {stats.get('CRate', 0):.1f}%  |  CDmg: {stats.get('CDmg', 0):.1f}%"
            )
            self.hero_stats_label.config(text=stats_text)
        else:
            self.hero_stats_label.config(text="No gear equipped")
```

**Step 2: Verify file compiles**

Run: `python -m py_compile Vribbels/ui/tabs/heroes_tab.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add Vribbels/ui/tabs/heroes_tab.py
git commit -m "feat: complete show_hero_details() with gear display (part 2)"
```

---

## Task 11: Update Module Exports

**Files:**
- Modify: `Vribbels/ui/tabs/__init__.py`
- Modify: `Vribbels/ui/__init__.py`

**Step 1: Add HeroesTab to ui/tabs/__init__.py**

Add the import and export:

```python
from .heroes_tab import HeroesTab

__all__ = ['MaterialsTab', 'SetupTab', 'CaptureTab', 'InventoryTab', 'OptimizerTab', 'HeroesTab']
```

**Step 2: Add HeroesTab to ui/__init__.py**

Update the import line:

```python
from .tabs import MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab
```

Update the __all__ list:

```python
__all__ = [
    'BaseTab',
    'AppContext',
    'MaterialsTab',
    'SetupTab',
    'CaptureTab',
    'InventoryTab',
    'OptimizerTab',
    'HeroesTab',
]
```

**Step 3: Verify modules compile**

Run: `python -m py_compile Vribbels/ui/__init__.py Vribbels/ui/tabs/__init__.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add Vribbels/ui/__init__.py Vribbels/ui/tabs/__init__.py
git commit -m "feat: add HeroesTab to module exports"
```

---

## Task 12: Integrate HeroesTab into Main GUI

**Files:**
- Modify: `Vribbels/czn_optimizer_gui.py:166-169` (tab creation)
- Modify: `Vribbels/czn_optimizer_gui.py:913` (load_data call)

**Step 1: Add HeroesTab import**

Find the line:
```python
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab
```

Replace with:
```python
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab
```

**Step 2: Create HeroesTab instance**

Find the lines around line 166-169 where heroes_tab is created:
```python
        self.heroes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.heroes_tab, text="Combatants")
        self.setup_heroes_tab()
```

Replace with:
```python
        self.heroes_tab_instance = HeroesTab(self.notebook, self.app_context)
        self.heroes_tab = self.heroes_tab_instance.get_frame()
        self.notebook.add(self.heroes_tab, text="Combatants")
```

**Step 3: Update load_data() call**

Find line 913:
```python
            self.refresh_heroes()
```

Replace with:
```python
            self.heroes_tab_instance.refresh_heroes()
```

**Step 4: Verify file compiles**

Run: `python -m py_compile Vribbels/czn_optimizer_gui.py`
Expected: No output (success)

**Step 5: Commit**

```bash
git add Vribbels/czn_optimizer_gui.py
git commit -m "feat: integrate HeroesTab instance into main GUI"
```

---

## Task 13: Remove Old Code from Main GUI

**Files:**
- Modify: `Vribbels/czn_optimizer_gui.py:81-82` (state variables)
- Modify: `Vribbels/czn_optimizer_gui.py:184-372` (setup_heroes_tab method)
- Modify: `Vribbels/czn_optimizer_gui.py:373-1053` (8 hero methods)

**Step 1: Remove state variables from __init__**

Find lines 81-82:
```python
        self.hero_sort_col = "name"
        self.hero_sort_reverse = False
```

Delete both lines.

**Step 2: Remove setup_heroes_tab() method**

Find and delete the entire `setup_heroes_tab()` method (lines 184-372, approximately).

**Step 3: Remove sort_heroes() method**

Find and delete the entire `sort_heroes()` method (around line 373-381).

**Step 4: Remove _update_hero_scrollregion() method**

Find and delete the entire `_update_hero_scrollregion()` method (around line 383-392).

**Step 5: Remove _on_hero_canvas_configure() method**

Find and delete the entire `_on_hero_canvas_configure()` method (around line 393-401).

**Step 6: Remove on_hero_detail_select() method**

Find and delete the entire `on_hero_detail_select()` method (around line 402-404).

**Step 7: Remove format_roll_with_color() method**

Find and delete the entire `format_roll_with_color()` method (around line 406-447).

**Step 8: Remove show_hero_details() method**

Find and delete the entire `show_hero_details()` method (around line 448-690).

**Step 9: Remove refresh_heroes() method**

Find and delete the entire `refresh_heroes()` method (around line 920-1020).

**Step 10: Remove select_hero_row() method**

Find and delete the entire `select_hero_row()` method (around line 1022-1053).

**Step 11: Verify file compiles**

Run: `python -m py_compile Vribbels/czn_optimizer_gui.py`
Expected: No output (success)

**Step 12: Commit**

```bash
git add Vribbels/czn_optimizer_gui.py
git commit -m "refactor: remove old HeroesTab code from main GUI (~466 lines)"
```

---

## Task 14: Functional Validation

**Files:**
- Test: `Vribbels/czn_optimizer_gui.py` (running application)

**Step 1: Start the application**

Run: `cd .worktrees/heroes-tab-extraction && python Vribbels/czn_optimizer_gui.py`
Expected: Application starts without errors

**Step 2: Load test data**

Action: Click "Load Data" button and select a test snapshot file
Expected: Data loads successfully

**Step 3: Verify user info displays**

Check: User info label at top of Heroes tab
Expected: Shows nickname, level, login stats

**Step 4: Verify hero list populates**

Check: Hero list displays with columns (Name, Grade, Attribute, Class, Level, Ego, GS)
Expected: All heroes shown with colored attributes

**Step 5: Test column sorting**

Action: Click each column header (Name, Grade, Attribute, Class, Level, Ego, GS)
Expected: List re-sorts by that column, reverse sort on second click

**Step 6: Test hero row selection**

Action: Click different hero rows
Expected: Row highlights, details update on right side

**Step 7: Test canvas scrolling**

Action: Scroll hero list with mouse wheel
Expected: List scrolls smoothly (if content exceeds visible area)

**Step 8: Verify character info displays**

Check: Character info section on right
Expected: Shows grade, attribute, class, level, ego, friendship, potential nodes

**Step 9: Verify partner card displays**

Check: Partner Card section
Expected: Shows partner name, stats, passive, ego skill OR "No partner equipped"

**Step 10: Verify gear slots display**

Check: 6 gear slot frames
Expected: Each shows gear with colored rarity backgrounds, main stats, substats with colored rolls

**Step 11: Verify colored roll display**

Check: Substat rolls in gear slots
Expected: Green=max roll, Red=min roll, Yellow/normal=mid rolls

**Step 12: Verify GS contributions**

Check: Small numbers on left of each substat
Expected: Shows GS contribution value (e.g., "12.5")

**Step 13: Verify set bonus and total GS**

Check: Set name below substats, GS at bottom
Expected: Shows set name, piece count, bonus text, and total GS

**Step 14: Verify build stats**

Check: Build Stats section
Expected: Shows Total GS, Sets, ATK, DEF, HP, CRate, CDmg

**Step 15: Test cross-tab navigation**

Action: Switch to Optimizer tab, Inventory tab, Materials tab, then back to Heroes
Expected: All tabs work, data persists

**Step 16: Document any issues**

If any issues found: Create notes for fixes needed
If all working: Proceed to commit

**Step 17: Commit validation results**

```bash
git add -A
git commit -m "test: functional validation complete - all HeroesTab features working"
```

---

## Completion Checklist

After completing all tasks:

- ✅ HeroesTab extracted to `ui/tabs/heroes_tab.py` (~466 lines)
- ✅ All 17 state variables moved to `_init_state()`
- ✅ All 8 methods migrated (setup_ui, sort, refresh, select, show_details, helpers)
- ✅ Module exports updated (`ui/__init__.py`, `ui/tabs/__init__.py`)
- ✅ Main GUI integration complete
- ✅ Old code removed from main GUI (~466 lines removed)
- ✅ Compilation successful (all Python files compile)
- ✅ Functional validation complete (all features working)
- ✅ Main GUI reduced: ~1,118 → ~652 lines (42% reduction)
- ✅ Total reduction achieved: 3,900 → ~652 lines (83% overall!)

**Final Status:** HeroesTab extraction complete! Ready for code review and merge.
