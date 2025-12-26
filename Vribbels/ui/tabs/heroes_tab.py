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

        # Hero list header - match original structure
        hero_header_frame = tk.Frame(hero_list_container, bg=self.colors["bg_lighter"])
        hero_header_frame.pack(fill=tk.X)

        # Use character widths for consistency between headers and data rows
        col_char_widths = [12, 6, 9, 10, 7, 5, 5]  # Character widths for each column
        col_names = ["Combatant", "Grade", "Attribute", "Class", "Level", "Ego", "GS"]
        col_keys = ["name", "grade", "attribute", "class", "level", "ego", "gs"]

        self.hero_header_labels = []
        for i, (name, char_width) in enumerate(zip(col_names, col_char_widths)):
            lbl = tk.Label(hero_header_frame, text=name, width=char_width,
                          bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                          font=("Segoe UI", 9, "bold"),
                          anchor=tk.W if i == 0 else tk.CENTER,
                          cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=1)
            lbl.bind("<Button-1>", lambda e, k=col_keys[i]: self.sort_heroes(k))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(fg=self.colors["accent"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(fg=self.colors["fg"]))
            self.hero_header_labels.append(lbl)

        self.hero_col_char_widths = col_char_widths  # Store character widths for data rows

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
        self.hero_detail_name = ttk.Label(hero_detail_container, text="Select a combatant", font=("Segoe UI", 14, "bold"))
        self.hero_detail_name.pack(anchor=tk.W, pady=(0, 5))

        # Info frame with Character and Partner Card
        # Character takes only needed space, Partner Card fills remaining with text wrapping
        info_frame = ttk.Frame(hero_detail_container)
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

        stats_frame = ttk.LabelFrame(hero_detail_container, text="Build Stats", padding=5)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.hero_stats_label = ttk.Label(stats_frame, text="", justify=tk.LEFT)
        self.hero_stats_label.pack(anchor=tk.W)

        gear_outer_frame = ttk.LabelFrame(hero_detail_container, text="Equipped Memory Fragments", padding=5)
        gear_outer_frame.pack(fill=tk.BOTH, expand=True)

        self.gear_frames = {}
        self.gear_labels = {}

        gear_grid = ttk.Frame(gear_outer_frame)
        gear_grid.pack(fill=tk.BOTH, expand=True)

        # Slot positions matching original: (slot_num, row, col)
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

    # Public API
    def refresh_heroes(self):
        """Refresh the heroes list."""
        # Clear existing rows
        for widget in self.hero_row_widgets:
            widget.destroy()
        self.hero_row_widgets.clear()
        self.hero_data_list.clear()
        self.selected_hero_index = -1

        # Update user info - match original format
        user = self.optimizer.user_info
        if user.nickname:
            user_text = (
                f"User: {user.nickname}  |  Level {user.level}  |  "
                f"Logins: {user.login_total}, Streak {user.login_continuous} (Best: {user.login_highest_continuous})"
            )
        else:
            user_text = "No user data available"
        self.user_info_label.config(text=user_text)

        # Get all heroes (from equipped gear or character info)
        all_heroes = set(self.optimizer.characters.keys()) | set(self.optimizer.character_info.keys())

        # Build hero data for sorting
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
                else:
                    lbl.config(fg=self.colors["fg"])

            self.show_hero_details(new_hero_data["name"])

    def show_hero_details(self, hero_name: str):
        """Show detailed hero information including gear - matches original exactly"""
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
