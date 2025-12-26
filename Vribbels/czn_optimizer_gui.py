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
from ui import AppContext, MaterialsTab, SetupTab, CaptureTab, InventoryTab, OptimizerTab, HeroesTab


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
            load_data_callback=self.load_file,
            switch_tab_callback=self._switch_to_tab
        )

        self.setup_ui()
        self.auto_load()
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

        # Create OptimizerTab instance
        self.optimizer_tab_instance = OptimizerTab(self.notebook, self.app_context)
        self.optimizer_tab = self.optimizer_tab_instance.get_frame()
        self.notebook.add(self.optimizer_tab, text="Optimizer")

        # Inventory tab - using UI module
        self.inventory_tab_instance = InventoryTab(self.notebook, self.app_context)
        self.inventory_tab = self.inventory_tab_instance.get_frame()
        self.notebook.add(self.inventory_tab, text="Memory Fragments")

        # Materials tab - using UI module
        self.materials_tab_instance = MaterialsTab(self.notebook, self.app_context)
        self.materials_tab = self.materials_tab_instance.get_frame()
        self.notebook.add(self.materials_tab, text="Materials")

        # Heroes tab - using UI module
        self.heroes_tab_instance = HeroesTab(self.notebook, self.app_context)
        self.heroes_tab = self.heroes_tab_instance.get_frame()
        self.notebook.add(self.heroes_tab, text="Combatants")

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

    def _switch_to_tab(self, tab_frame: tk.Widget):
        """Switch notebook to the specified tab frame."""
        self.notebook.select(tab_frame)

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
        self.inventory_tab_instance.refresh_inventory()
        self.heroes_tab_instance.refresh_heroes()

        self.weight_status.config(text="Custom weights applied - scores recalculated",
                                   foreground=self.colors["green"])

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

            # Update optimizer tab UI
            self.optimizer_tab_instance.refresh_after_load()

            # Update other tabs
            self.inventory_tab_instance.populate_set_filters()
            self.inventory_tab_instance.refresh_inventory()
            self.heroes_tab_instance.refresh_heroes()
            self.materials_tab_instance.refresh_materials()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
            import traceback
            traceback.print_exc()

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