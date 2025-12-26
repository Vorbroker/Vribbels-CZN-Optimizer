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
        """Select a hero row and show details"""
        # Deselect previous
        if 0 <= self.selected_hero_index < len(self.hero_row_widgets):
            prev_frame = self.hero_row_widgets[self.selected_hero_index]
            prev_frame.config(bg=self.colors["bg"])
            for child in prev_frame.winfo_children():
                child.config(bg=self.colors["bg"])

        # Select new
        self.selected_hero_index = index
        if 0 <= index < len(self.hero_row_widgets):
            sel_frame = self.hero_row_widgets[index]
            sel_frame.config(bg=self.colors["bg_highlight"])
            for child in sel_frame.winfo_children():
                child.config(bg=self.colors["bg_highlight"])

            # Show details
            hero_data = self.hero_data_list[index]
            self.show_hero_details(hero_data["name"])
        else:
            # Clear details
            self.hero_detail_name.config(text="Select a hero")
            self.hero_char_info.config(text="")
            self.hero_partner_text.config(text="")
            self.hero_stats_label.config(text="")
            for slot_num in range(1, 7):
                self.gear_labels[slot_num].config(text="Empty", fg=self.colors["fg_dim"])
                self.gear_frames[slot_num].config(bg=self.colors["bg_dark"])

    def show_hero_details(self, hero_name: str):
        """Show detailed hero information including gear"""
        char_info = self.optimizer.character_info.get(hero_name)
        if not char_info:
            return

        char_def = get_character_by_name(hero_name)
        if not char_def:
            return

        # Update title with attribute color
        attr = char_def.get("attribute", "")
        attr_color = ATTRIBUTE_COLORS.get(attr, self.colors["fg"])
        self.hero_detail_name.config(text=hero_name, fg=attr_color)

        # Character info section
        char_text_lines = [
            f"Grade: {'★' * char_def.get('grade', 0)}  |  Attribute: {attr}  |  Class: {char_def.get('class', '?')}",
            f"Level: {char_info.level}  |  Ascension: {char_info.ascension}  |  Limit Break: {char_info.limit_break}  |  Ego: {char_info.ego_level}",
        ]

        # Potential nodes
        potential_lines = []
        if char_info.potential_50_unlocked:
            node_50_stat = char_def.get("node_50", "Unknown")
            bonus_50 = get_potential_stat_bonus(node_50_stat, 50)
            potential_lines.append(f"  Node 50: {node_50_stat} +{bonus_50}")
        if char_info.potential_60_unlocked:
            node_60_stat = char_def.get("node_60", "Unknown")
            bonus_60 = get_potential_stat_bonus(node_60_stat, 60)
            potential_lines.append(f"  Node 60: {node_60_stat} +{bonus_60}")

        if potential_lines:
            char_text_lines.append("Potential Nodes:")
            char_text_lines.extend(potential_lines)

        self.hero_char_info.config(text="\n".join(char_text_lines))

        # Partner card info
        if char_info.partner_res_id:
            partner_info = get_partner(char_info.partner_res_id)
            if partner_info:
                partner_name = partner_info.get("name", f"Partner {char_info.partner_res_id}")
                partner_lines = [f"Name: {partner_name}  |  Level: {char_info.partner_level}"]

                # Partner stats
                partner_stats = get_partner_stats(char_info.partner_res_id, char_info.partner_level)
                if partner_stats:
                    partner_lines.append(
                        f"Stats: ATK +{partner_stats['atk']:.0f}  DEF +{partner_stats['def']:.0f}  HP +{partner_stats['hp']:.0f}"
                    )

                # Partner passive
                passive_info = get_partner_passive_info(char_info.partner_res_id, char_info.partner_passive_level)
                if passive_info:
                    partner_lines.append(f"Passive (Lv.{char_info.partner_passive_level}): {passive_info}")

                # Friendship level
                if char_info.friendship_level > 0:
                    partner_lines.append(f"Friendship: Level {char_info.friendship_level}")

                self.hero_partner_text.config(text="\n".join(partner_lines))
            else:
                self.hero_partner_text.config(text=f"Partner ID: {char_info.partner_res_id} (Unknown)")
        else:
            self.hero_partner_text.config(text="No partner equipped")

        # Calculate and display stats
        equipped = self.optimizer.characters.get(hero_name, [])
        stats = self.optimizer.calculate_build_stats(equipped, char_info)

        stats_lines = [
            f"ATK: {stats['final_atk']:.0f}  |  DEF: {stats['final_def']:.0f}  |  HP: {stats['final_hp']:.0f}",
            f"CRate: {stats['final_crit_rate']:.1f}%  |  CDmg: {stats['final_crit_dmg']:.1f}%",
            f"Speed: {stats.get('final_speed', 0):.0f}  |  Hit: {stats.get('final_hit', 0):.1f}%  |  Res: {stats.get('final_res', 0):.1f}%"
        ]
        self.hero_stats_label.config(text="\n".join(stats_lines))

        # Display gear
        equipped_by_slot = {g.slot: g for g in equipped}

        for slot_num in range(1, 7):
            gear = equipped_by_slot.get(slot_num)
            if not gear:
                self.gear_labels[slot_num].config(text="Empty", fg=self.colors["fg_dim"])
                self.gear_frames[slot_num].config(bg=self.colors["bg_dark"])
                continue

            # Set background color by rarity
            rarity_bg = RARITY_BG_COLORS.get(gear.rarity, self.colors["bg_dark"])
            self.gear_frames[slot_num].config(bg=rarity_bg)

            # Gear name and level
            gear_name = f"{SETS.get(gear.set_id, ('Unknown Set',))[0]} +{gear.enhance_level}"
            rarity_color = RARITY_COLORS.get(gear.rarity, self.colors["fg"])

            # Main stat
            main_stat_line = f"{gear.main_stat.name}: {gear.main_stat.format_value()}"

            # Substats with colored rolls
            substat_lines = []
            for sub in gear.substats:
                stat_name = sub.name
                # Get colored parts for this substat
                colored_parts = self.format_roll_with_color(sub, self.gear_frames[slot_num], rarity_bg)

                if sub.roll_count > 1 and sub.rolls:
                    # Multi-roll format: "StatName +total (parts)"
                    total_val = sub.format_value()
                    parts_str = ",".join([part[0] for part in colored_parts])
                    substat_lines.append((f"{stat_name} +{total_val} ({parts_str})", colored_parts))
                else:
                    # Single roll: just "StatName +value"
                    substat_lines.append((f"{stat_name} +{colored_parts[0][0]}", colored_parts))

            # Build final text with basic formatting (we'll use a Frame with Labels for true color support)
            # For now, use plain text with color hints
            text_parts = [gear_name, main_stat_line]
            for substat_line, colored_parts in substat_lines:
                # For Label widget, we can't mix colors easily, so use the first color
                # (This is a simplification - full implementation would need Text widget or multiple Labels)
                text_parts.append(substat_line.split("(")[0].strip())  # Just the "StatName +total" part

            # Clear previous content and rebuild with colored labels
            self.gear_labels[slot_num].destroy()

            # Create a frame to hold multiple labels for color support
            content_frame = tk.Frame(self.gear_frames[slot_num], bg=rarity_bg)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0, 3))

            # Gear name in rarity color
            name_label = tk.Label(
                content_frame,
                text=gear_name,
                font=("Consolas", 8, "bold"),
                bg=rarity_bg,
                fg=rarity_color,
                anchor="nw",
                justify=tk.LEFT
            )
            name_label.pack(fill=tk.X)

            # Main stat
            main_label = tk.Label(
                content_frame,
                text=main_stat_line,
                font=("Consolas", 8),
                bg=rarity_bg,
                fg=self.colors["fg"],
                anchor="nw",
                justify=tk.LEFT
            )
            main_label.pack(fill=tk.X)

            # Substats with individual roll coloring
            for sub in gear.substats:
                stat_name = sub.name
                colored_parts = self.format_roll_with_color(sub, self.gear_frames[slot_num], rarity_bg)

                # Create a frame for this substat line to hold inline colored labels
                substat_frame = tk.Frame(content_frame, bg=rarity_bg)
                substat_frame.pack(fill=tk.X, anchor="nw")

                # Stat name
                name_part = tk.Label(
                    substat_frame,
                    text=f"{stat_name} +",
                    font=("Consolas", 8),
                    bg=rarity_bg,
                    fg=self.colors["fg"],
                    anchor="w"
                )
                name_part.pack(side=tk.LEFT)

                if sub.roll_count > 1 and sub.rolls:
                    # Multi-roll: show total + (parts)
                    total_val = sub.format_value()
                    total_label = tk.Label(
                        substat_frame,
                        text=f"{total_val} (",
                        font=("Consolas", 8),
                        bg=rarity_bg,
                        fg=self.colors["fg"],
                        anchor="w"
                    )
                    total_label.pack(side=tk.LEFT)

                    # Individual rolls with color
                    for idx, (part_text, part_color) in enumerate(colored_parts):
                        part_label = tk.Label(
                            substat_frame,
                            text=part_text,
                            font=("Consolas", 8),
                            bg=rarity_bg,
                            fg=part_color,
                            anchor="w"
                        )
                        part_label.pack(side=tk.LEFT)

                        # Add comma separator if not last
                        if idx < len(colored_parts) - 1:
                            comma_label = tk.Label(
                                substat_frame,
                                text=",",
                                font=("Consolas", 8),
                                bg=rarity_bg,
                                fg=self.colors["fg"],
                                anchor="w"
                            )
                            comma_label.pack(side=tk.LEFT)

                    # Closing parenthesis
                    close_label = tk.Label(
                        substat_frame,
                        text=")",
                        font=("Consolas", 8),
                        bg=rarity_bg,
                        fg=self.colors["fg"],
                        anchor="w"
                    )
                    close_label.pack(side=tk.LEFT)
                else:
                    # Single roll - just show the value with color
                    if colored_parts:
                        val_label = tk.Label(
                            substat_frame,
                            text=colored_parts[0][0],
                            font=("Consolas", 8),
                            bg=rarity_bg,
                            fg=colored_parts[0][1],
                            anchor="w"
                        )
                        val_label.pack(side=tk.LEFT)

            # Store reference to content frame (for future updates)
            self.gear_labels[slot_num] = content_frame

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
