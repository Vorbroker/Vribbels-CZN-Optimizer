"""Inventory tab for viewing and filtering Memory Fragments."""

import tkinter as tk
from tkinter import ttk
from game_data import EQUIPMENT_SLOTS, RARITY_COLORS
from ..base_tab import BaseTab


class InventoryTab(BaseTab):
    """
    Inventory tab displays all Memory Fragments with filtering options.

    Provides filters by slot, set, rarity, and equipped status.
    Updates automatically when data is loaded via populate_set_filters().
    """

    def __init__(self, parent, context):
        super().__init__(parent, context)

        # Filter state
        self.inv_slot_vars = {}
        self.inv_set_vars = {}
        self.inv_unequipped_var = None
        self.inv_include_uncommon_var = None

        # Inventory display state
        self.inv_tree = None
        self.inv_sort_col = "gs"
        self.inv_sort_reverse = True
        self.inv_filtered_data = []

        # Frame for set checkboxes (populated dynamically)
        self.inv_set_frame_inner = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the Inventory tab UI."""
        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # Slot checkboxes with two columns: left (3,2,1) right (4,5,6), buttons at bottom
        slot_frame = ttk.LabelFrame(filter_frame, text="Slots", padding=3)
        slot_frame.pack(side=tk.LEFT, padx=(0, 10), anchor=tk.N)

        slot_inner = ttk.Frame(slot_frame)
        slot_inner.pack()

        # Left column: slots 3, 2, 1 (top to bottom) - matches Roman numerals III, II, I
        # Right column: slots 4, 5, 6 (top to bottom) - matches Roman numerals IV, V, VI
        left_slots = [3, 2, 1]   # III, II, I Denial, Suppression, Shock
        right_slots = [4, 5, 6]  # IV, V, VI  Ideal, Desire, Imagination

        for row, (left_slot, right_slot) in enumerate(zip(left_slots, right_slots)):
            # Left column
            left_name = EQUIPMENT_SLOTS[left_slot]
            left_var = tk.BooleanVar(value=True)
            self.inv_slot_vars[left_slot] = left_var
            ttk.Checkbutton(slot_inner, text=left_name, variable=left_var,
                           command=self.refresh_inventory).grid(row=row, column=0, sticky=tk.W, padx=2)

            # Right column
            right_name = EQUIPMENT_SLOTS[right_slot]
            right_var = tk.BooleanVar(value=True)
            self.inv_slot_vars[right_slot] = right_var
            ttk.Checkbutton(slot_inner, text=right_name, variable=right_var,
                           command=self.refresh_inventory).grid(row=row, column=1, sticky=tk.W, padx=2)

        # Slot buttons at bottom
        slot_btn_frame = ttk.Frame(slot_frame)
        slot_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(slot_btn_frame, text="All", width=5,
                   command=self.select_all_slots).pack(side=tk.LEFT, padx=1)
        ttk.Button(slot_btn_frame, text="None", width=5,
                   command=self.select_no_slots).pack(side=tk.LEFT, padx=1)

        # Set checkboxes with buttons at bottom
        set_frame = ttk.LabelFrame(filter_frame, text="Sets", padding=3)
        set_frame.pack(side=tk.LEFT, padx=(0, 10), anchor=tk.N)

        self.inv_set_frame_inner = ttk.Frame(set_frame)
        self.inv_set_frame_inner.pack()

        # Set buttons at bottom
        set_btn_frame = ttk.Frame(set_frame)
        set_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(set_btn_frame, text="All", width=5,
                   command=self.select_all_sets).pack(side=tk.LEFT, padx=1)
        ttk.Button(set_btn_frame, text="None", width=5,
                   command=self.select_no_sets).pack(side=tk.LEFT, padx=1)

        # Options
        opt_frame = ttk.Frame(filter_frame)
        opt_frame.pack(side=tk.LEFT, padx=(0, 10))

        self.inv_unequipped_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Unequipped Only", variable=self.inv_unequipped_var,
                        command=self.refresh_inventory).pack(anchor=tk.W)

        self.inv_include_uncommon_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Include Uncommon", variable=self.inv_include_uncommon_var,
                        command=self.refresh_inventory).pack(anchor=tk.W)

        ttk.Button(opt_frame, text="Refresh", command=self.refresh_inventory).pack(anchor=tk.W, pady=(5, 0))

        # Treeview for inventory display
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        inv_cols = ("slot", "set", "lvl", "main", "sub1", "sub2", "sub3", "sub4", "gs", "potential", "equipped")
        self.inv_tree = ttk.Treeview(tree_frame, columns=inv_cols, show="headings", height=25)

        for col, txt, w in [("slot", "Slot", 100), ("set", "Set", 150), ("lvl", "+Lv", 35),
                            ("main", "Main", 110), ("sub1", "Sub1", 100), ("sub2", "Sub2", 100),
                            ("sub3", "Sub3", 100), ("sub4", "Sub4", 100), ("gs", "GS", 40),
                            ("potential", "Potential", 75), ("equipped", "Equipped", 80)]:
            self.inv_tree.heading(col, text=txt, command=lambda c=col.lower(): self.sort_inventory(c))
            self.inv_tree.column(col, width=w, anchor=tk.W if col in ["slot", "set", "main", "equipped"] else tk.CENTER)

        inv_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=inv_scroll.set)
        self.inv_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inv_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def select_all_slots(self):
        """Select all slot checkboxes in inventory filter."""
        for var in self.inv_slot_vars.values():
            var.set(True)
        self.refresh_inventory()

    def select_no_slots(self):
        """Deselect all slot checkboxes in inventory filter."""
        for var in self.inv_slot_vars.values():
            var.set(False)
        self.refresh_inventory()

    def select_all_sets(self):
        """Select all set checkboxes in inventory filter."""
        for var in self.inv_set_vars.values():
            var.set(True)
        self.refresh_inventory()

    def select_no_sets(self):
        """Deselect all set checkboxes in inventory filter."""
        for var in self.inv_set_vars.values():
            var.set(False)
        self.refresh_inventory()

    def populate_set_filters(self):
        """
        Populate set filter checkboxes based on loaded fragments.

        Called automatically after data loads.
        """
        # Clear existing set checkboxes
        for widget in self.inv_set_frame_inner.winfo_children():
            widget.destroy()
        self.inv_set_vars.clear()

        # Get unique set names from fragments
        sets = sorted(set(f.set_name for f in self.optimizer.fragments))
        for i, set_name in enumerate(sets):
            var = tk.BooleanVar(value=True)
            self.inv_set_vars[set_name] = var
            row = i // 3
            col = i % 3
            ttk.Checkbutton(self.inv_set_frame_inner, text=set_name, variable=var,
                           command=self.refresh_inventory).grid(row=row, column=col, sticky=tk.W, padx=2)

    def refresh_inventory(self):
        """Refresh inventory display based on current filter settings."""
        self.inv_tree.delete(*self.inv_tree.get_children())

        # Get checkbox filter values
        uneq_only = self.inv_unequipped_var.get()
        include_uncommon = self.inv_include_uncommon_var.get()

        # Determine minimum rarity
        min_rarity = 2 if include_uncommon else 3

        # Get selected slots from checkboxes
        slot_nums = set()
        for slot_num, var in self.inv_slot_vars.items():
            if var.get():
                slot_nums.add(slot_num)

        # Get selected sets from checkboxes
        set_names = set()
        all_selected = True
        for set_name, var in self.inv_set_vars.items():
            if var.get():
                set_names.add(set_name)
            else:
                all_selected = False

        # If all sets selected or none, don't filter by set
        if all_selected or not set_names:
            set_names = None

        filtered = [f for f in self.optimizer.fragments if f.rarity_num >= min_rarity]
        filtered = [f for f in filtered if f.slot_num in slot_nums]
        if set_names:
            filtered = [f for f in filtered if f.set_name in set_names]
        if uneq_only:
            filtered = [f for f in filtered if not f.equipped_to]

        self.inv_filtered_data = filtered
        self._display_inventory_sorted()

    def _display_inventory_sorted(self):
        """Display filtered inventory with current sort settings."""
        self.inv_tree.delete(*self.inv_tree.get_children())

        if not hasattr(self, 'inv_filtered_data'):
            return

        filtered = self.inv_filtered_data

        sort_key_map = {
            "slot": lambda f: f.slot_num,
            "set": lambda f: f.set_name,
            "lvl": lambda f: f.level,
            "main": lambda f: f.main_stat.name if f.main_stat else "",
            "gs": lambda f: f.gear_score,
            "potential": lambda f: f.potential_high,
            "equipped": lambda f: f.equipped_to or "",
        }

        key_func = sort_key_map.get(self.inv_sort_col, lambda f: f.gear_score)
        filtered_sorted = sorted(filtered, key=key_func, reverse=self.inv_sort_reverse)

        for f in filtered_sorted[:500]:
            # Use full stat names for inventory
            subs = []
            for s in f.substats[:4]:
                subs.append(f"{s.name}:{s.format_value()}")
            while len(subs) < 4:
                subs.append("-")

            main_str = f"{f.main_stat.name}:{f.main_stat.format_value()}" if f.main_stat else "-"
            pot = f"{f.potential_low:.0f}-{f.potential_high:.0f}" if f.potential_low != f.potential_high else "-"

            # Include set size in set name
            set_pieces = f.get_set_pieces()
            set_display = f"{f.set_name} ({set_pieces})"

            self.inv_tree.insert("", tk.END, values=(
                f.slot_name, set_display, f"+{f.level}",
                main_str, *subs, f"{f.gear_score:.0f}", pot, f.equipped_to or ""
            ), tags=(f"r{f.rarity_num}",))

        self.inv_tree.tag_configure("r4", foreground=RARITY_COLORS[4])
        self.inv_tree.tag_configure("r3", foreground=RARITY_COLORS[3])
        self.inv_tree.tag_configure("r2", foreground=RARITY_COLORS[2])

    def sort_inventory(self, col: str):
        """Sort inventory by specified column."""
        if col == self.inv_sort_col:
            self.inv_sort_reverse = not self.inv_sort_reverse
        else:
            self.inv_sort_col = col
            self.inv_sort_reverse = col in ["gs", "lvl", "potential"]

        self._display_inventory_sorted()
