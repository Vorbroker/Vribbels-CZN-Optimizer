#!/usr/bin/env python3
"""
Vribbels - CZN Memory Fragment Tool
A Fribbels-inspired gear management and optimization tool for Chaos Zero Nightmare
Includes integrated data capture and setup functionality.
"""

import json
import os
import sys
import itertools
import socket
import subprocess
import shutil
import ctypes
import re
import webbrowser
from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont

# === GAME DATA IMPORTS ===
from game_data import *
from models import *
from capture import *
from optimizer import GearOptimizer
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab


class MultiSelectListbox(tk.Frame):
    """A frame containing a listbox with multi-select capability"""
    def __init__(self, parent, items, height=4, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=height,
                                  exportselection=False, bg="#363650", fg="#cdd6f4",
                                  selectbackground="#3b6ea5", selectforeground="#cdd6f4",
                                  highlightthickness=0)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        for item in items:
            self.listbox.insert(tk.END, item)
    
    def get_selected(self) -> list[str]:
        indices = self.listbox.curselection()
        return [self.listbox.get(i) for i in indices]
    
    def select_items(self, items: list[str]):
        self.listbox.selection_clear(0, tk.END)
        for i in range(self.listbox.size()):
            if self.listbox.get(i) in items:
                self.listbox.selection_set(i)


class OptimizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vribbels - CZN Memory Fragment Optimizer")
        self.root.geometry("1450x1000")
        self.root.minsize(1200, 800)

        self.colors = {
            "bg": "#1e1e2e", "bg_light": "#2a2a3e", "bg_lighter": "#363650",
            "fg": "#cdd6f4", "fg_dim": "#6c7086", "accent": "#89b4fa",
            "green": "#a6e3a1", "red": "#f38ba8", "yellow": "#f9e2af", "purple": "#cba6f7",
            "orange": "#FF8C00", "select": "#3b6ea5",
        }

        self.root.configure(bg=self.colors["bg"])
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.optimizer = GearOptimizer()
        self.selected_character = tk.StringVar()
        self.priority_vars: dict[str, tk.IntVar] = {}
        self.priority_labels: dict[str, ttk.Label] = {}
        self.main_stat_vars: dict[int, dict[str, tk.BooleanVar]] = {}
        self.four_piece_vars: dict[str, tk.BooleanVar] = {}  # Multi-select for 4-piece
        self.two_piece_vars: dict[str, tk.BooleanVar] = {}  # Changed to dict of checkboxes
        self.top_percent_var = tk.IntVar(value=50)
        self.include_equipped_var = tk.BooleanVar(value=True)
        
        self.optimization_results: list = []
        self.result_queue = queue.Queue()
        self.cancel_flag = [False]
        self.exclude_hero_vars: dict[str, tk.BooleanVar] = {}
        self.inv_sort_col = "gs"
        self.inv_sort_reverse = True
        self.inv_filtered_data: list = []
        self.result_sort_col = "score"
        self.result_sort_reverse = False
        self.hero_sort_col = "name"
        self.hero_sort_reverse = False
        
        # Inventory multi-select state
        self.inv_slot_selections: set = set()
        self.inv_set_selections: set = set()

        # Initialize capture manager
        self.capture_manager = CaptureManager(
            output_folder=OUTPUT_DIR,
            log_callback=lambda msg, tag=None: self.capture_tab_instance.capture_log_msg(msg, tag) if hasattr(self, 'capture_tab_instance') else None,
            status_callback=lambda status: self.capture_tab_instance.capture_status_label.config(text=status) if hasattr(self, 'capture_tab_instance') else None
        )

        # Create AppContext for UI tabs
        self.app_context = AppContext(
            root=self.root,
            notebook=None,  # Set after notebook created in setup_ui
            optimizer=self.optimizer,
            capture_manager=self.capture_manager,
            colors=self.colors,
            style=self.style,
            load_data_callback=self.load_data,
            switch_tab_callback=self._switch_to_tab
        )

        self.setup_ui()
        self.auto_load()
        self.root.after(100, self.check_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_styles(self):
        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"])
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        self.style.configure("TButton", background=self.colors["bg_light"], foreground=self.colors["fg"], padding=5)
        self.style.map("TButton", background=[("active", self.colors["bg_lighter"])])
        self.style.configure("TCombobox", fieldbackground=self.colors["bg_lighter"], background=self.colors["bg_lighter"],
                             foreground=self.colors["fg"], selectbackground=self.colors["select"],
                             selectforeground=self.colors["fg"])
        self.style.map("TCombobox", fieldbackground=[("readonly", self.colors["bg_lighter"])], 
                       foreground=[("readonly", self.colors["fg"])])
        self.style.configure("TCheckbutton", background=self.colors["bg"], foreground=self.colors["fg"])
        self.style.map("TCheckbutton", background=[("active", self.colors["bg_lighter"])],
                       foreground=[("active", self.colors["fg"])])
        self.style.configure("TLabelframe", background=self.colors["bg"])
        self.style.configure("TLabelframe.Label", background=self.colors["bg"], foreground=self.colors["accent"])
        self.style.configure("TScale", background=self.colors["bg"], troughcolor=self.colors["bg_light"])
        self.style.configure("TNotebook", background=self.colors["bg"])
        self.style.configure("TNotebook.Tab", background=self.colors["bg_light"], foreground=self.colors["fg"], padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", self.colors["bg_lighter"])])
        self.style.configure("Treeview", background=self.colors["bg_light"], foreground=self.colors["fg"],
                             fieldbackground=self.colors["bg_light"], rowheight=24)
        self.style.configure("Treeview.Heading", background=self.colors["bg_lighter"], foreground=self.colors["fg"])
        self.style.map("Treeview.Heading", background=[("active", self.colors["select"])],
                       foreground=[("active", self.colors["fg"])])
        self.style.map("Treeview", background=[("selected", self.colors["select"])],
                       foreground=[("selected", self.colors["fg"])])

    def setup_ui(self):
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        kofi_btn = tk.Button(top_bar, text="Support on Ko-Fi", 
                            command=lambda: webbrowser.open("https://ko-fi.com/H2H21PHYKW"),
                            bg="#72a4f2", fg="white", font=("Segoe UI", 9, "bold"),
                            relief=tk.FLAT, padx=10, pady=3, cursor="hand2")
        kofi_btn.pack(side=tk.RIGHT, padx=5)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Update AppContext with notebook reference
        self.app_context.notebook = self.notebook

        self.optimizer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.optimizer_tab, text="Optimizer")
        self.setup_optimizer_tab()

        self.inventory_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_tab, text="Memory Fragments")
        self.setup_inventory_tab()

        # Materials tab - using UI module
        self.materials_tab_instance = MaterialsTab(self.notebook, self.app_context)
        self.materials_tab = self.materials_tab_instance.get_frame()
        self.notebook.add(self.materials_tab, text="Materials")

        self.heroes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.heroes_tab, text="Combatants")
        self.setup_heroes_tab()

        # Capture tab - using UI module
        self.capture_tab_instance = CaptureTab(self.notebook, self.app_context)
        self.capture_tab = self.capture_tab_instance.get_frame()
        self.notebook.add(self.capture_tab, text="Capture")
        
        # Setup tab - using UI module
        self.setup_tab_instance = SetupTab(self.notebook, self.app_context)
        self.setup_tab = self.setup_tab_instance.get_frame()
        self.notebook.add(self.setup_tab, text="Setup")
        
        self.scoring_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scoring_tab, text="Scoring")
        self.setup_scoring_tab()

    def setup_optimizer_tab(self):
        toolbar = ttk.Frame(self.optimizer_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Load Data", command=self.load_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Combatant:").pack(side=tk.LEFT, padx=(15, 5))
        self.hero_combo = ttk.Combobox(toolbar, textvariable=self.selected_character, width=12, state="readonly")
        self.hero_combo.pack(side=tk.LEFT)
        self.hero_combo.bind("<<ComboboxSelected>>", self.on_hero_select)

        ttk.Button(toolbar, text="Start", command=self.run_optimization).pack(side=tk.LEFT, padx=(15, 2))
        ttk.Button(toolbar, text="Stop", command=self.cancel_optimization).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset_settings).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(toolbar, text="No data loaded", foreground=self.colors["fg_dim"])
        self.status_label.pack(side=tk.RIGHT, padx=10)

        main_pane = ttk.PanedWindow(self.optimizer_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.LabelFrame(main_pane, text="Stats Comparison", padding=5)
        main_pane.add(left_frame, weight=1)

        self.stats_tree = ttk.Treeview(left_frame, columns=("stat", "current", "new", "diff"), show="headings", height=22)
        self.stats_tree.heading("stat", text="Stat")
        self.stats_tree.heading("current", text="Current")
        self.stats_tree.heading("new", text="New")
        self.stats_tree.heading("diff", text="+/-")
        self.stats_tree.column("stat", width=90)
        self.stats_tree.column("current", width=65, anchor=tk.E)
        self.stats_tree.column("new", width=65, anchor=tk.E)
        self.stats_tree.column("diff", width=55, anchor=tk.E)
        self.stats_tree.pack(fill=tk.BOTH, expand=True)

        middle_frame = ttk.Frame(main_pane)
        main_pane.add(middle_frame, weight=1)

        priority_frame = ttk.LabelFrame(middle_frame, text="Stat Priority (-1 to 3)", padding=5)
        priority_frame.pack(fill=tk.X, pady=(0, 5))

        priority_stats = ["ATK%", "Flat ATK", "DEF%", "Flat DEF", "HP%", "Flat HP", 
                          "CRate", "CDmg", "Ego", "Extra DMG%", "DoT%"]
        
        for i, stat_name in enumerate(priority_stats):
            row = i // 2
            col = i % 2
            frame = ttk.Frame(priority_frame)
            frame.grid(row=row, column=col, sticky=tk.W, padx=3, pady=1)
            
            ttk.Label(frame, text=f"{stat_name}:", width=10, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            var = tk.IntVar(value=0)
            self.priority_vars[stat_name] = var
            
            scale = ttk.Scale(frame, from_=-1, to=3, variable=var, orient=tk.HORIZONTAL, length=70,
                              command=lambda v, s=stat_name: self.on_priority_change(s))
            scale.pack(side=tk.LEFT, padx=2)
            
            label = ttk.Label(frame, text="0", width=2, font=("Segoe UI", 9, "bold"))
            label.pack(side=tk.LEFT)
            self.priority_labels[stat_name] = label

        top_frame = ttk.Frame(priority_frame)
        top_frame.grid(row=(len(priority_stats) + 1) // 2, column=0, columnspan=2, pady=(8, 0), sticky=tk.W)
        ttk.Label(top_frame, text="Top % Filter:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        ttk.Scale(top_frame, from_=10, to=100, variable=self.top_percent_var, orient=tk.HORIZONTAL, length=90).pack(side=tk.LEFT, padx=5)
        self.top_pct_label = ttk.Label(top_frame, text="50%", font=("Segoe UI", 9, "bold"))
        self.top_pct_label.pack(side=tk.LEFT)
        self.top_percent_var.trace_add("write", lambda *a: self.top_pct_label.config(text=f"{self.top_percent_var.get()}%"))

        main_stat_frame = ttk.LabelFrame(middle_frame, text="Main Stats (Slots IV/V/VI)", padding=5)
        main_stat_frame.pack(fill=tk.X, pady=(0, 5))

        for slot_num, slot_name in [(4, "IV"), (5, "V"), (6, "VI")]:
            slot_frame = ttk.Frame(main_stat_frame)
            slot_frame.pack(fill=tk.X, pady=1)
            ttk.Label(slot_frame, text=f"{slot_name}:", width=3, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            
            self.main_stat_vars[slot_num] = {}
            possible_mains = SLOT_MAIN_STATS[slot_num]
            
            for main in possible_mains[:8]:
                var = tk.BooleanVar(value=False)
                self.main_stat_vars[slot_num][main] = var
                # Truncate display but keep full name in var
                short_name = main.replace("%", "").replace(" DMG", "").replace("Flat ", "F.")[:8]
                ttk.Checkbutton(slot_frame, text=short_name, variable=var, width=8).pack(side=tk.LEFT)

        set_frame = ttk.LabelFrame(middle_frame, text="Set Configuration", padding=5)
        set_frame.pack(fill=tk.X, pady=(0, 5))

        # 4-piece multi-select with checkboxes - use grid layout for full names
        four_pc_frame = ttk.Frame(set_frame)
        four_pc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(four_pc_frame, text="4-Piece Sets:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        
        four_pc_inner = ttk.Frame(four_pc_frame)
        four_pc_inner.pack(fill=tk.X, padx=5)
        for i, sid in enumerate(FOUR_PIECE_SETS):
            name = SETS[sid]["name"]
            var = tk.BooleanVar(value=False)
            self.four_piece_vars[name] = var
            row = i // 2
            col = i % 2
            ttk.Checkbutton(four_pc_inner, text=name, variable=var).grid(row=row, column=col, sticky=tk.W, padx=5)

        # 2-piece sets - checkboxes like 4-piece
        two_pc_frame = ttk.Frame(set_frame)
        two_pc_frame.pack(fill=tk.X, pady=(5, 2))
        ttk.Label(two_pc_frame, text="2-Piece Sets:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        
        two_pc_inner = ttk.Frame(two_pc_frame)
        two_pc_inner.pack(fill=tk.X, padx=5)
        for i, sid in enumerate(TWO_PIECE_SETS):
            name = SETS[sid]["name"]
            var = tk.BooleanVar(value=False)
            self.two_piece_vars[name] = var
            row = i // 3
            col = i % 3
            ttk.Checkbutton(two_pc_inner, text=name, variable=var).grid(row=row, column=col, sticky=tk.W, padx=5)

        opt_frame = ttk.Frame(set_frame)
        opt_frame.pack(fill=tk.X, pady=3)
        ttk.Checkbutton(opt_frame, text="Include Equipped Items", variable=self.include_equipped_var).pack(anchor=tk.W)

        exclude_frame = ttk.LabelFrame(middle_frame, text="Exclude Combatant's Gear", padding=5)
        exclude_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.exclude_hero_vars: dict[str, tk.BooleanVar] = {}
        exclude_inner = ttk.Frame(exclude_frame)
        exclude_inner.pack(fill=tk.X)
        self.exclude_heroes_frame = exclude_inner

        right_frame = ttk.LabelFrame(main_pane, text="Results", padding=5)
        main_pane.add(right_frame, weight=2)

        self.progress_label = ttk.Label(right_frame, text="Ready to optimize", foreground=self.colors["fg_dim"])
        self.progress_label.pack(anchor=tk.W)

        result_cols = ("rank", "score", "sets", "atk", "hp", "def", "crate", "cdmg", "extra")
        self.result_tree = ttk.Treeview(right_frame, columns=result_cols, show="headings", height=12)
        self.result_tree.heading("rank", text="#", command=lambda: self.sort_results("rank"))
        self.result_tree.heading("score", text="Score", command=lambda: self.sort_results("score"))
        self.result_tree.heading("sets", text="Sets", command=lambda: self.sort_results("sets"))
        self.result_tree.heading("atk", text="ATK", command=lambda: self.sort_results("atk"))
        self.result_tree.heading("hp", text="HP", command=lambda: self.sort_results("hp"))
        self.result_tree.heading("def", text="DEF", command=lambda: self.sort_results("def"))
        self.result_tree.heading("crate", text="CRate", command=lambda: self.sort_results("crate"))
        self.result_tree.heading("cdmg", text="CDmg", command=lambda: self.sort_results("cdmg"))
        self.result_tree.heading("extra", text="ExDMG", command=lambda: self.sort_results("extra"))

        self.result_tree.column("rank", width=28, anchor=tk.CENTER)
        self.result_tree.column("score", width=45, anchor=tk.CENTER)
        self.result_tree.column("sets", width=160)
        self.result_tree.column("atk", width=50, anchor=tk.CENTER)
        self.result_tree.column("hp", width=50, anchor=tk.CENTER)
        self.result_tree.column("def", width=50, anchor=tk.CENTER)
        self.result_tree.column("crate", width=50, anchor=tk.CENTER)
        self.result_tree.column("cdmg", width=55, anchor=tk.CENTER)
        self.result_tree.column("extra", width=50, anchor=tk.CENTER)

        result_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=result_scroll.set)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        detail_frame = ttk.LabelFrame(self.optimizer_tab, text="Selected Build", padding=5)
        detail_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        detail_cols = ("slot", "set", "main", "sub1", "sub2", "sub3", "sub4", "gs", "potential", "owner")
        self.detail_tree = ttk.Treeview(detail_frame, columns=detail_cols, show="headings", height=6)
        for col, txt, w in [("slot","Slot",110),("set","Set",130),("main","Main",100),
                            ("sub1","Sub1",95),("sub2","Sub2",95),("sub3","Sub3",95),("sub4","Sub4",95),
                            ("gs","GS",40),("potential","Potential",75),("owner","Owner",80)]:
            self.detail_tree.heading(col, text=txt)
            self.detail_tree.column(col, width=w, anchor=tk.W if col in ["slot","set","main","owner"] else tk.CENTER)
        self.detail_tree.pack(fill=tk.X)

    def setup_inventory_tab(self):
        filter_frame = ttk.Frame(self.inventory_tab)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # Slot checkboxes with two columns: left (3,2,1) right (4,5,6), buttons at bottom
        slot_frame = ttk.LabelFrame(filter_frame, text="Slots", padding=3)
        slot_frame.pack(side=tk.LEFT, padx=(0, 10), anchor=tk.N)
        
        self.inv_slot_vars = {}
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
        
        self.inv_set_vars = {}
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
        
        ttk.Button(opt_frame, text="Refresh", command=self.refresh_inventory).pack(anchor=tk.W, pady=(5,0))

        tree_frame = ttk.Frame(self.inventory_tab)
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

    def setup_heroes_tab(self):
        user_frame = ttk.Frame(self.heroes_tab)
        user_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.user_info_label = ttk.Label(user_frame, text="No user data available", font=("Segoe UI", 10))
        self.user_info_label.pack(anchor=tk.W)
        
        content_frame = ttk.PanedWindow(self.heroes_tab, orient=tk.HORIZONTAL)
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

    def sort_heroes(self, col: str):
        """Sort heroes list by column"""
        if col == self.hero_sort_col:
            self.hero_sort_reverse = not self.hero_sort_reverse
        else:
            self.hero_sort_col = col
            self.hero_sort_reverse = col in ["gs", "grade", "ego"]
        
        self.refresh_heroes()
    
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

    def on_hero_detail_select(self, event=None):
        # Legacy method - now handled by select_hero_row
        pass

    def format_roll_with_color(self, sub: Stat, parent_frame: tk.Frame, bg_color: str) -> str:
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

    def show_hero_details(self, hero_name: str):
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

    def setup_scoring_tab(self):
        """Setup the Scoring configuration tab"""
        main_frame = ttk.Frame(self.scoring_tab)
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
        self.stat_weight_vars = {}
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

    def reset_weights(self):
        """Reset all stat weights to 1.0"""
        for var in self.stat_weight_vars.values():
            var.set(1.0)
        self.weight_status.config(text="Weights reset to default (all 1.0)")

    def preset_dps_weights(self):
        """Set weights for DPS-focused scoring"""
        presets = {
            "ATK%": 2.0, "Flat ATK": 1.5, "CRate": 2.0, "CDmg": 2.0,
            "Extra DMG%": 1.5, "DoT%": 1.0,
            "DEF%": 0.5, "Flat DEF": 0.3, "HP%": 0.5, "Flat HP": 0.3,
            "Ego": 1.0,
        }
        for stat, var in self.stat_weight_vars.items():
            var.set(presets.get(stat, 1.0))
        self.weight_status.config(text="Applied DPS preset weights")

    def preset_tank_weights(self):
        """Set weights for tank-focused scoring"""
        presets = {
            "DEF%": 2.0, "Flat DEF": 1.5, "HP%": 2.0, "Flat HP": 1.5,
            "ATK%": 0.5, "Flat ATK": 0.3, "CRate": 0.5, "CDmg": 0.5,
            "Extra DMG%": 0.3, "DoT%": 0.3, "Ego": 1.0,
        }
        for stat, var in self.stat_weight_vars.items():
            var.set(presets.get(stat, 1.0))
        self.weight_status.config(text="Applied Tank preset weights")

    def apply_custom_weights(self):
        """Apply custom weights and recalculate all gear scores"""
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
        
        # Refresh displays
        self.refresh_inventory()
        self.refresh_heroes()
        
        self.weight_status.config(text="Custom weights applied - scores recalculated", 
                                   foreground=self.colors["green"])

    def install_mitmproxy(self):
        """Install mitmproxy using capture module."""
        def install_thread():
            try:
                success = install_mitmproxy()
                self.root.after(0, lambda: self.setup_tab_instance.check_status())
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", "mitmproxy installed successfully!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Installation failed: {e}"))

        messagebox.showinfo("Installing", "Installing mitmproxy... This may take a minute.")
        threading.Thread(target=install_thread, daemon=True).start()

    def on_close(self):
        """Handle window close event."""
        if self.capture_manager.is_capturing():
            if messagebox.askyesno("Confirm Exit", "Capture is still running. Stop and exit?"):
                self.capture_tab_instance.stop_capture()
            else:
                return
        self.root.destroy()

    def auto_load(self):
        for dir_path in ["snapshots", ".", str(Path.home() / "snapshots")]:
            snapshots = Path(dir_path)
            if snapshots.exists():
                files = list(snapshots.glob("memory_fragments_*.json"))
                if files:
                    latest = str(max(files, key=lambda f: f.stat().st_mtime))
                    self.load_data(latest)
                    return

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Memory Fragment Snapshot",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="snapshots"
        )
        if filepath:
            self.load_data(filepath)

    def load_data(self, filepath: str):
        try:
            self.optimizer.load_data(filepath)
            self.status_label.config(text=f"Loaded {len(self.optimizer.fragments)} fragments", foreground=self.colors["green"])
            
            all_heroes = set(self.optimizer.characters.keys()) | set(self.optimizer.character_info.keys())
            self.hero_combo["values"] = sorted(all_heroes)
            
            # Update set checkboxes with full names
            for widget in self.inv_set_frame_inner.winfo_children():
                widget.destroy()
            self.inv_set_vars.clear()
            
            sets = sorted(set(f.set_name for f in self.optimizer.fragments))
            for i, set_name in enumerate(sets):
                var = tk.BooleanVar(value=True)
                self.inv_set_vars[set_name] = var
                row = i // 3
                col = i % 3
                ttk.Checkbutton(self.inv_set_frame_inner, text=set_name, variable=var,
                               command=self.refresh_inventory).grid(row=row, column=col, sticky=tk.W, padx=2)
            
            # Update exclude combatants with 6 columns and colored names
            for widget in self.exclude_heroes_frame.winfo_children():
                widget.destroy()
            self.exclude_hero_vars.clear()
            
            heroes = sorted(self.optimizer.characters.keys())
            for i, hero in enumerate(heroes):
                var = tk.BooleanVar(value=False)
                self.exclude_hero_vars[hero] = var
                row = i // 6
                col = i % 6
                # Get attribute color for this hero
                hero_data = get_character_by_name(hero)
                attribute = hero_data.get("attribute", "Unknown")
                fg_color = ATTRIBUTE_COLORS.get(attribute, self.colors["fg"])
                # Create checkbutton with colored text
                cb = tk.Checkbutton(self.exclude_heroes_frame, text=hero, variable=var,
                                   bg=self.colors["bg"], fg=fg_color, selectcolor=self.colors["bg_light"],
                                   activebackground=self.colors["bg"], activeforeground=fg_color,
                                   font=("Segoe UI", 9), anchor=tk.W, width=9)
                cb.grid(row=row, column=col, sticky=tk.W)

            self.refresh_inventory()
            self.refresh_heroes()
            self.materials_tab_instance.refresh_materials()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
            import traceback
            traceback.print_exc()

    def on_hero_select(self, event=None):
        char = self.selected_character.get()
        if char in self.optimizer.characters:
            self.show_current_stats(char)

    def show_current_stats(self, char_name: str):
        gear = self.optimizer.characters.get(char_name, [])
        stats = self.optimizer.calculate_build_stats(gear, char_name)
        self.stats_tree.delete(*self.stats_tree.get_children())
        
        stat_order = [
            ("- Totals -", None),
            ("ATK", 0), ("DEF", 0), ("HP", 0), ("CRate", 1), ("CDmg", 1),
            ("- Substats -", None),
            ("ATK%", 1), ("DEF%", 1), ("HP%", 1), ("Ego", 0), ("Extra DMG%", 1), ("DoT%", 1),
            ("- Calculated -", None),
            ("EHP", 0), ("Avg DMG", 0), ("Max CD", 0), ("Bruiser", 0),
        ]
        
        for stat_name, decimals in stat_order:
            if decimals is None:
                self.stats_tree.insert("", tk.END, values=(stat_name, "", "", ""), tags=("header",))
                continue
            
            val = stats.get(stat_name, 0)
            if val == 0:
                continue
            fmt = f"{val:.0f}" if decimals == 0 else f"{val:.1f}"
            self.stats_tree.insert("", tk.END, values=(stat_name, fmt, "-", "-"))
        
        self.stats_tree.tag_configure("header", foreground=self.colors["fg_dim"])

    def on_priority_change(self, stat_name: str):
        for name, var in self.priority_vars.items():
            self.optimizer.priorities[name] = var.get()
            self.priority_labels[name].config(text=str(var.get()))
        self.optimizer.recalculate_scores()

    def reset_settings(self):
        for var in self.priority_vars.values():
            var.set(0)
        for lbl in self.priority_labels.values():
            lbl.config(text="0")
        for var in self.four_piece_vars.values():
            var.set(False)
        for var in self.two_piece_vars.values():
            var.set(False)
        for slot_vars in self.main_stat_vars.values():
            for var in slot_vars.values():
                var.set(False)
        self.top_percent_var.set(50)
        self.include_equipped_var.set(True)
        for var in self.exclude_hero_vars.values():
            var.set(False)

    def cancel_optimization(self):
        self.cancel_flag[0] = True
        self.progress_label.config(text="Cancelling...")

    def run_optimization(self):
        char_name = self.selected_character.get()
        if not char_name:
            messagebox.showwarning("Warning", "Please select a hero")
            return

        has_any_main_selected = False
        for slot_num in [4, 5, 6]:
            slot_vars = self.main_stat_vars.get(slot_num, {})
            if any(v.get() for v in slot_vars.values()):
                has_any_main_selected = True
                break
        
        if not has_any_main_selected:
            messagebox.showwarning("Warning", "Please select at least one main stat option for slots IV, V, or VI")
            return

        self.cancel_flag[0] = False
        
        # Get selected 4-piece sets (multi-select)
        selected_4pc = []
        for name, var in self.four_piece_vars.items():
            if var.get():
                for sid, sinfo in SETS.items():
                    if sinfo["name"] == name:
                        selected_4pc.append(sid)
                        break
        
        settings = {
            "four_piece_sets": selected_4pc,  # Now a list
            "two_piece_sets": [],
            "main_stat_4": [n for n, v in self.main_stat_vars.get(4, {}).items() if v.get()],
            "main_stat_5": [n for n, v in self.main_stat_vars.get(5, {}).items() if v.get()],
            "main_stat_6": [n for n, v in self.main_stat_vars.get(6, {}).items() if v.get()],
            "top_percent": self.top_percent_var.get(),
            "include_equipped": self.include_equipped_var.get(),
            "excluded_heroes": [h for h, v in self.exclude_hero_vars.items() if v.get()],
            "max_results": 100,
        }

        # Get selected 2-piece sets from checkboxes
        for name, var in self.two_piece_vars.items():
            if var.get():
                for sid, sinfo in SETS.items():
                    if sinfo["name"] == name:
                        settings["two_piece_sets"].append(sid)
                        break

        for name, var in self.priority_vars.items():
            self.optimizer.priorities[name] = var.get()
        self.optimizer.recalculate_scores()

        self.progress_label.config(text="Starting...")
        self.result_tree.delete(*self.result_tree.get_children())

        def optimize_thread():
            def progress_cb(checked, total, found):
                self.result_queue.put(("progress", checked, total, found))
            results = self.optimizer.optimize(char_name, settings, progress_cb, self.cancel_flag)
            self.result_queue.put(("done", results))

        threading.Thread(target=optimize_thread, daemon=True).start()

    def check_queue(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                if msg[0] == "progress":
                    _, checked, total, found = msg
                    pct = (checked / total * 100) if total > 0 else 0
                    self.progress_label.config(text=f"Checked {checked:,} ({pct:.1f}%) - Found {found}")
                elif msg[0] == "done":
                    results = msg[1]
                    self.optimization_results = results
                    self.display_results(results)
                    self.progress_label.config(text=f"Done! {len(results)} builds found")
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def display_results(self, results: list):
        self.result_tree.delete(*self.result_tree.get_children())
        for i, (gear, score, stats) in enumerate(results[:100]):
            set_counts = {}
            for p in gear:
                set_counts[p.set_name] = set_counts.get(p.set_name, 0) + 1
            sets_str = " + ".join(f"{c}x{n[:10]}" for n, c in set_counts.items() if c >= 2)

            atk = stats.get("ATK", 0)
            hp = stats.get("HP", 0)
            def_stat = stats.get("DEF", 0)
            crit_rate = stats.get("CRate", 0)
            crit_dmg = stats.get("CDmg", 0)
            extra_dmg = stats.get("Extra DMG%", 0)

            self.result_tree.insert("", tk.END, values=(
                i+1, f"{score:.0f}", sets_str,
                f"{atk:.0f}", f"{hp:.0f}", f"{def_stat:.0f}",
                f"{crit_rate:.1f}", f"{crit_dmg:.1f}", f"{extra_dmg:.1f}"
            ), iid=str(i))

    def sort_results(self, col: str):
        if not self.optimization_results:
            return
        
        if col == self.result_sort_col:
            self.result_sort_reverse = not self.result_sort_reverse
        else:
            self.result_sort_col = col
            self.result_sort_reverse = False
        
        col_map = {
            "rank": lambda x: x[0],
            "score": lambda x: x[1],
            "sets": lambda x: "",
            "atk": lambda x: x[2].get("ATK", 0),
            "hp": lambda x: x[2].get("HP", 0),
            "def": lambda x: x[2].get("DEF", 0),
            "crate": lambda x: x[2].get("CRate", 0),
            "cdmg": lambda x: x[2].get("CDmg", 0),
            "extra": lambda x: x[2].get("Extra DMG%", 0),
        }
        
        key_func = col_map.get(col, lambda x: x[1])
        indexed_results = [(i, gear, score, stats) for i, (gear, score, stats) in enumerate(self.optimization_results)]
        indexed_results.sort(key=lambda x: key_func((x[0], x[2], x[3])), reverse=not self.result_sort_reverse)
        
        self.result_tree.delete(*self.result_tree.get_children())
        for rank, (orig_idx, gear, score, stats) in enumerate(indexed_results[:100]):
            set_counts = {}
            for p in gear:
                set_counts[p.set_name] = set_counts.get(p.set_name, 0) + 1
            sets_str = " + ".join(f"{c}x{n[:10]}" for n, c in set_counts.items() if c >= 2)
            
            self.result_tree.insert("", tk.END, values=(
                rank+1, f"{score:.0f}", sets_str,
                f"{stats.get('ATK', 0):.0f}", f"{stats.get('HP', 0):.0f}", f"{stats.get('DEF', 0):.0f}",
                f"{stats.get('CRate', 0):.1f}", f"{stats.get('CDmg', 0):.1f}", f"{stats.get('Extra DMG%', 0):.1f}"
            ), iid=str(orig_idx))

    def on_result_select(self, event):
        sel = self.result_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self.optimization_results):
            return

        gear, score, new_stats = self.optimization_results[idx]
        char = self.selected_character.get()
        current_gear = self.optimizer.characters.get(char, [])
        current_stats = self.optimizer.calculate_build_stats(current_gear, char)

        self.stats_tree.delete(*self.stats_tree.get_children())
        
        stat_order = [
            ("- Totals -", None),
            ("ATK", 0), ("DEF", 0), ("HP", 0), ("CRate", 1), ("CDmg", 1),
            ("- Substats -", None),
            ("ATK%", 1), ("DEF%", 1), ("HP%", 1), ("Ego", 0), ("Extra DMG%", 1), ("DoT%", 1),
            ("- Calculated -", None),
            ("EHP", 0), ("Avg DMG", 0), ("Max CD", 0), ("Bruiser", 0),
        ]
        
        for stat_name, decimals in stat_order:
            if decimals is None:
                self.stats_tree.insert("", tk.END, values=(stat_name, "", "", ""), tags=("header",))
                continue
                
            curr = current_stats.get(stat_name, 0)
            new = new_stats.get(stat_name, 0)
            diff = new - curr
            
            if decimals == 0:
                curr_fmt = f"{curr:.0f}"
                new_fmt = f"{new:.0f}"
                diff_fmt = f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}"
            else:
                curr_fmt = f"{curr:.1f}"
                new_fmt = f"{new:.1f}"
                diff_fmt = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
            
            if curr == 0 and new == 0:
                continue
                
            tag = "pos" if diff > 0.1 else "neg" if diff < -0.1 else ""
            self.stats_tree.insert("", tk.END, values=(stat_name, curr_fmt, new_fmt, diff_fmt), tags=(tag,))

        self.stats_tree.tag_configure("pos", foreground=self.colors["green"])
        self.stats_tree.tag_configure("neg", foreground=self.colors["red"])
        self.stats_tree.tag_configure("header", foreground=self.colors["fg_dim"])

        self.detail_tree.delete(*self.detail_tree.get_children())
        for p in sorted(gear, key=lambda x: x.slot_num):
            subs = []
            for s in p.substats[:4]:
                subs.append(f"{s.name}:{s.format_value()}")
            while len(subs) < 4:
                subs.append("-")
            
            main_str = f"{p.main_stat.name}:{p.main_stat.format_value()}" if p.main_stat else "-"
            pot = f"{p.potential_low:.0f}-{p.potential_high:.0f}" if p.potential_low != p.potential_high else "-"
            owner = p.equipped_to or ""
            
            self.detail_tree.insert("", tk.END, values=(
                f"+{p.level} {p.slot_name}",
                p.set_name, main_str, *subs, f"{p.gear_score:.0f}", pot, owner
            ), tags=(f"r{p.rarity_num}",))

        self.detail_tree.tag_configure("r4", foreground=RARITY_COLORS[4])
        self.detail_tree.tag_configure("r3", foreground=RARITY_COLORS[3])

    def select_all_slots(self):
        """Select all slot checkboxes in inventory filter"""
        for var in self.inv_slot_vars.values():
            var.set(True)
        self.refresh_inventory()
    
    def select_no_slots(self):
        """Deselect all slot checkboxes in inventory filter"""
        for var in self.inv_slot_vars.values():
            var.set(False)
        self.refresh_inventory()
    
    def select_all_sets(self):
        """Select all set checkboxes in inventory filter"""
        for var in self.inv_set_vars.values():
            var.set(True)
        self.refresh_inventory()
    
    def select_no_sets(self):
        """Deselect all set checkboxes in inventory filter"""
        for var in self.inv_set_vars.values():
            var.set(False)
        self.refresh_inventory()

    def refresh_inventory(self):
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
        if col == self.inv_sort_col:
            self.inv_sort_reverse = not self.inv_sort_reverse
        else:
            self.inv_sort_col = col
            self.inv_sort_reverse = col in ["gs", "lvl", "potential"]
        
        self._display_inventory_sorted()

    def refresh_heroes(self):
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

    def _switch_to_tab(self, tab_frame: tk.Widget):
        """Switch notebook to the specified tab frame."""
        self.notebook.select(tab_frame)

    def run(self):
        self.root.mainloop()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    if sys.platform != "win32":
        return False
    
    try:
        if getattr(sys, 'frozen', False):
            script = sys.executable
            params = " ".join(sys.argv[1:])
        else:
            script = sys.executable
            params = f'"{sys.argv[0]}"'
            if len(sys.argv) > 1:
                params += " " + " ".join(sys.argv[1:])
        
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)
        return ret > 32
    except Exception as e:
        print(f"Failed to elevate: {e}")
        return False


def main():
    if sys.platform == "win32" and not is_admin():
        temp_root = tk.Tk()
        temp_root.withdraw()
        
        response = messagebox.askyesno(
            "Administrator Required",
            "This application needs Administrator privileges for the capture feature.\n\n"
            "Do you want to restart with elevated permissions?\n\n"
            "(Click 'No' to continue without capture functionality)"
        )
        
        temp_root.destroy()
        
        if response:
            if run_as_admin():
                sys.exit(0)
            else:
                temp_root2 = tk.Tk()
                temp_root2.withdraw()
                messagebox.showwarning("Elevation Failed", "Could not get administrator privileges.")
                temp_root2.destroy()
    
    app = OptimizerGUI()
    app.run()


if __name__ == "__main__":
    main()