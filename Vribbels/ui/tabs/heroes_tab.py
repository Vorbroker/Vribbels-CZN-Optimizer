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

    def setup_ui(self):
        """Setup the Heroes tab UI."""
        # User info frame at top
        user_frame = ttk.Frame(self.frame)
        user_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.user_info_label = tk.Label(
            user_frame,
            text="No data loaded",
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            anchor="w"
        )
        self.user_info_label.pack(side=tk.LEFT)

        # Main content: hero list on left, details on right
        content_pane = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        content_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Left: Hero list
        hero_list_container = ttk.Frame(content_pane)
        content_pane.add(hero_list_container, weight=1)

        # Hero list header
        hero_header_frame = tk.Frame(hero_list_container, bg=self.colors["bg_dark"])
        hero_header_frame.pack(fill=tk.X)

        # Header columns with sort functionality
        hero_cols = [
            ("name", "Name", 20),
            ("attr", "Attr", 8),
            ("class", "Class", 10),
            ("grade", "★", 3),
            ("level", "Lv", 3),
            ("asc", "Asc", 3),
            ("lb", "LB", 3),
            ("ego", "Ego", 3),
            ("gs", "GS", 6),
        ]

        self.hero_col_char_widths = {col[0]: col[2] for col in hero_cols}
        self.hero_header_labels = []

        for col_id, col_name, width in hero_cols:
            lbl = tk.Label(
                hero_header_frame,
                text=col_name,
                bg=self.colors["bg_dark"],
                fg=self.colors["fg_dim"],
                font=("Consolas", 9, "bold"),
                width=width,
                anchor="w" if col_id == "name" else "center",
                cursor="hand2"
            )
            lbl.pack(side=tk.LEFT, padx=2, pady=2)
            lbl.bind("<Button-1>", lambda e, c=col_id: self.sort_heroes(c))
            self.hero_header_labels.append(lbl)

        # Scrollable hero list
        hero_canvas_frame = ttk.Frame(hero_list_container)
        hero_canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.hero_canvas = tk.Canvas(
            hero_canvas_frame,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        hero_vsb = ttk.Scrollbar(hero_canvas_frame, orient=tk.VERTICAL, command=self.hero_canvas.yview)
        self.hero_canvas.configure(yscrollcommand=hero_vsb.set)

        self.hero_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hero_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.hero_list_frame = tk.Frame(self.hero_canvas, bg=self.colors["bg"])
        self.hero_canvas_window = self.hero_canvas.create_window(
            (0, 0),
            window=self.hero_list_frame,
            anchor="nw"
        )

        self.hero_canvas.bind("<Configure>", self._on_hero_canvas_configure)
        self.hero_list_frame.bind("<Configure>", lambda e: self._update_hero_scrollregion())

        # Right: Hero details
        hero_detail_container = ttk.Frame(content_pane)
        content_pane.add(hero_detail_container, weight=2)

        # Hero name/title
        self.hero_detail_name = tk.Label(
            hero_detail_container,
            text="Select a hero",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            anchor="w"
        )
        self.hero_detail_name.pack(fill=tk.X, padx=5, pady=(5, 10))

        # Character info
        char_info_frame = tk.Frame(hero_detail_container, bg=self.colors["bg_dark"], relief=tk.RIDGE, bd=1)
        char_info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        char_info_label = tk.Label(
            char_info_frame,
            text="Character Info",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["purple"],
            anchor="w"
        )
        char_info_label.pack(fill=tk.X, padx=5, pady=(3, 0))

        self.hero_char_info = tk.Label(
            char_info_frame,
            text="",
            font=("Consolas", 9),
            bg=self.colors["bg_dark"],
            fg=self.colors["fg"],
            anchor="w",
            justify=tk.LEFT
        )
        self.hero_char_info.pack(fill=tk.X, padx=5, pady=(2, 5))

        # Partner card info
        partner_frame = tk.Frame(hero_detail_container, bg=self.colors["bg_dark"], relief=tk.RIDGE, bd=1)
        partner_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        partner_label = tk.Label(
            partner_frame,
            text="Partner Card",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["purple"],
            anchor="w"
        )
        partner_label.pack(fill=tk.X, padx=5, pady=(3, 0))

        self.hero_partner_text = tk.Label(
            partner_frame,
            text="",
            font=("Consolas", 9),
            bg=self.colors["bg_dark"],
            fg=self.colors["fg"],
            anchor="w",
            justify=tk.LEFT
        )
        self.hero_partner_text.pack(fill=tk.X, padx=5, pady=(2, 5))

        # Stats section
        stats_frame = tk.Frame(hero_detail_container, bg=self.colors["bg_dark"], relief=tk.RIDGE, bd=1)
        stats_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        stats_label = tk.Label(
            stats_frame,
            text="Total Stats",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["purple"],
            anchor="w"
        )
        stats_label.pack(fill=tk.X, padx=5, pady=(3, 0))

        self.hero_stats_label = tk.Label(
            stats_frame,
            text="",
            font=("Consolas", 9),
            bg=self.colors["bg_dark"],
            fg=self.colors["fg"],
            anchor="w",
            justify=tk.LEFT
        )
        self.hero_stats_label.pack(fill=tk.X, padx=5, pady=(2, 5))

        # Gear section
        gear_container = tk.Frame(hero_detail_container, bg=self.colors["bg"])
        gear_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        gear_title = tk.Label(
            gear_container,
            text="Equipped Memory Fragments",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["purple"],
            anchor="w"
        )
        gear_title.pack(fill=tk.X, pady=(0, 5))

        # 6 gear slots in 2 rows
        gear_grid = tk.Frame(gear_container, bg=self.colors["bg"])
        gear_grid.pack(fill=tk.BOTH, expand=True)

        for slot_num, slot_name in EQUIPMENT_SLOTS.items():
            row = (slot_num - 1) // 3
            col = (slot_num - 1) % 3

            slot_frame = tk.Frame(gear_grid, bg=self.colors["bg_dark"], relief=tk.RIDGE, bd=1)
            slot_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

            slot_header = tk.Label(
                slot_frame,
                text=f"Slot {slot_num}: {slot_name}",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["bg_dark"],
                fg=self.colors["fg_dim"],
                anchor="w"
            )
            slot_header.pack(fill=tk.X, padx=3, pady=(2, 0))

            slot_content = tk.Label(
                slot_frame,
                text="Empty",
                font=("Consolas", 8),
                bg=self.colors["bg_dark"],
                fg=self.colors["fg_dim"],
                anchor="nw",
                justify=tk.LEFT
            )
            slot_content.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0, 3))

            self.gear_frames[slot_num] = slot_frame
            self.gear_labels[slot_num] = slot_content

        # Configure grid weights for equal columns
        for i in range(3):
            gear_grid.columnconfigure(i, weight=1)
        for i in range(2):
            gear_grid.rowconfigure(i, weight=1)

    # Public API
    def refresh_heroes(self):
        """Refresh the heroes list."""
        # Clear existing rows
        for widget in self.hero_row_widgets:
            widget.destroy()
        self.hero_row_widgets.clear()
        self.hero_data_list.clear()
        self.selected_hero_index = -1

        # Update user info
        if self.optimizer.user_info:
            ui = self.optimizer.user_info
            self.user_info_label.config(
                text=f"User: {ui.name}  |  Server: {ui.server}  |  UID: {ui.user_id}  |  Data: {self.optimizer.capture_time}"
            )
        else:
            self.user_info_label.config(text="No data loaded")

        # Prepare hero data
        for char_name, char_info in self.optimizer.character_info.items():
            if not char_info:
                continue

            char_def = get_character_by_name(char_name)
            if not char_def:
                continue

            # Calculate gear score
            equipped = self.optimizer.characters.get(char_name, [])
            gear_score = sum(g.gear_score for g in equipped)

            # Add to data list
            self.hero_data_list.append({
                "name": char_name,
                "attr": char_def.get("attribute", "?"),
                "class": char_def.get("class", "?"),
                "grade": char_def.get("grade", 0),
                "level": char_info.level,
                "asc": char_info.ascension,
                "lb": char_info.limit_break,
                "ego": char_info.ego_level,
                "gs": gear_score
            })

        # Sort heroes
        sort_key_map = {
            "name": lambda x: x["name"],
            "attr": lambda x: x["attr"],
            "class": lambda x: x["class"],
            "grade": lambda x: x["grade"],
            "level": lambda x: x["level"],
            "asc": lambda x: x["asc"],
            "lb": lambda x: x["lb"],
            "ego": lambda x: x["ego"],
            "gs": lambda x: x["gs"]
        }

        sort_fn = sort_key_map.get(self.hero_sort_col, lambda x: x["name"])
        self.hero_data_list.sort(key=sort_fn, reverse=self.hero_sort_reverse)

        # Highlight sort header
        for lbl in self.hero_header_labels:
            lbl.config(fg=self.colors["fg_dim"])
        # Find the sorted column and highlight it
        for i, (col_id, _, _) in enumerate([
            ("name", "Name", 20),
            ("attr", "Attr", 8),
            ("class", "Class", 10),
            ("grade", "★", 3),
            ("level", "Lv", 3),
            ("asc", "Asc", 3),
            ("lb", "LB", 3),
            ("ego", "Ego", 3),
            ("gs", "GS", 6),
        ]):
            if col_id == self.hero_sort_col:
                arrow = " ▼" if self.hero_sort_reverse else " ▲"
                self.hero_header_labels[i].config(fg=self.colors["purple"], text=f"{['Name','Attr','Class','★','Lv','Asc','LB','Ego','GS'][i]}{arrow}")
                break

        # Display rows
        for idx, hero_data in enumerate(self.hero_data_list):
            row_frame = tk.Frame(self.hero_list_frame, bg=self.colors["bg"])
            row_frame.pack(fill=tk.X, pady=1)

            # Name
            name_lbl = tk.Label(
                row_frame,
                text=hero_data["name"][:self.hero_col_char_widths["name"]],
                bg=self.colors["bg"],
                fg=ATTRIBUTE_COLORS.get(hero_data["attr"], self.colors["fg"]),
                font=("Consolas", 9),
                width=self.hero_col_char_widths["name"],
                anchor="w",
                cursor="hand2"
            )
            name_lbl.pack(side=tk.LEFT, padx=2)
            name_lbl.bind("<Button-1>", lambda e, i=idx: self.select_hero_row(i))

            # Other columns
            for key in ["attr", "class", "grade", "level", "asc", "lb", "ego", "gs"]:
                val = hero_data[key]
                lbl = tk.Label(
                    row_frame,
                    text=str(val),
                    bg=self.colors["bg"],
                    fg=self.colors["fg"],
                    font=("Consolas", 9),
                    width=self.hero_col_char_widths[key],
                    anchor="center",
                    cursor="hand2"
                )
                lbl.pack(side=tk.LEFT, padx=2)
                lbl.bind("<Button-1>", lambda e, i=idx: self.select_hero_row(i))

            self.hero_row_widgets.append(row_frame)

        self._update_hero_scrollregion()

    # Sorting and display
    def sort_heroes(self, col: str):
        """Sort heroes list by column"""
        if col == self.hero_sort_col:
            self.hero_sort_reverse = not self.hero_sort_reverse
        else:
            self.hero_sort_col = col
            self.hero_sort_reverse = col in ["gs", "grade", "ego"]

        self.refresh_heroes()

    def select_hero_row(self, index: int):
        """Select a hero row."""
        pass  # Implement in later task

    def show_hero_details(self, hero_name: str):
        """Show hero details."""
        pass  # Implement in later task

    # Helper methods
    def _update_hero_scrollregion(self):
        """Update scroll region and ensure content stays at top when it fits"""
        self.hero_canvas.configure(scrollregion=self.hero_canvas.bbox("all"))
        # If content fits in view, reset to top
        if self.hero_canvas.bbox("all"):
            content_height = self.hero_canvas.bbox("all")[3]
            visible_height = self.hero_canvas.winfo_height()
            if content_height <= visible_height:
                self.hero_canvas.yview_moveto(0)

    def _on_hero_canvas_configure(self, event):
        """Handle canvas resize - update width and check scrolling"""
        self.hero_canvas.itemconfig(self.hero_canvas_window, width=event.width)
        # Check if we need to reset scroll position
        if self.hero_canvas.bbox("all"):
            content_height = self.hero_canvas.bbox("all")[3]
            if content_height <= event.height:
                self.hero_canvas.yview_moveto(0)

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
