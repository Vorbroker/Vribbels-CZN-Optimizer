"""
Optimization configuration and execution tab.

Provides UI for configuring gear optimization parameters and viewing results.
Handles background optimization with progress updates and result display.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue

from ui.base_tab import BaseTab
from ui.context import AppContext
from game_data import (
    SETS, FOUR_PIECE_SETS, TWO_PIECE_SETS,
    SLOT_MAIN_STATS, RARITY_COLORS, ATTRIBUTE_COLORS,
    get_character_by_name
)


class OptimizerTab(BaseTab):
    """
    Main optimization tab for configuring and running gear optimizations.

    Features:
    - Stat priority configuration (sliders for 11 stats)
    - Main stat filters (slots IV/V/VI checkboxes)
    - Set requirements (4-piece and 2-piece multi-select)
    - Exclude hero filters (checkbox grid)
    - Background optimization with progress updates
    - Results display with sortable columns
    - Build comparison view (current vs new stats)
    """

    def __init__(self, parent: tk.Widget, context: AppContext):
        """Initialize OptimizerTab with parent and app context."""
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()
        # Start queue checking loop for background optimization
        self.root.after(100, self.check_queue)

    def _init_state(self):
        """Initialize all state variables and widget references."""
        # Character selection
        self.selected_character = tk.StringVar()

        # Priority sliders (11 stats: ATK%, Flat ATK, DEF%, etc.)
        self.priority_vars: dict[str, tk.IntVar] = {}
        self.priority_labels: dict[str, ttk.Label] = {}

        # Main stat filters for slots 4, 5, 6
        self.main_stat_vars: dict[int, dict[str, tk.BooleanVar]] = {}

        # Set filters (multi-select checkboxes)
        self.four_piece_vars: dict[str, tk.BooleanVar] = {}
        self.two_piece_vars: dict[str, tk.BooleanVar] = {}

        # Optimization options
        self.top_percent_var = tk.IntVar(value=50)
        self.include_equipped_var = tk.BooleanVar(value=True)
        self.exclude_hero_vars: dict[str, tk.BooleanVar] = {}

        # Results and threading state
        self.optimization_results: list = []
        self.result_queue = queue.Queue()
        self.cancel_flag = [False]  # Mutable list for thread safety

        # Sorting state
        self.result_sort_col = "score"
        self.result_sort_reverse = False

        # Widget references (set during setup_ui)
        self.hero_combo = None
        self.status_label = None
        self.stats_tree = None
        self.result_tree = None
        self.detail_tree = None
        self.progress_label = None
        self.top_pct_label = None
        self.exclude_heroes_frame = None

    def setup_ui(self):
        """Build the optimization tab UI."""
        # Toolbar with Load Data, hero selector, Start/Stop/Reset buttons
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Load Data",
                   command=self.context.load_data_callback).pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="Combatant:").pack(side=tk.LEFT, padx=(15, 5))
        self.hero_combo = ttk.Combobox(toolbar, textvariable=self.selected_character,
                                       width=12, state="readonly")
        self.hero_combo.pack(side=tk.LEFT)
        self.hero_combo.bind("<<ComboboxSelected>>", self.on_hero_select)

        ttk.Button(toolbar, text="Start",
                   command=self.run_optimization).pack(side=tk.LEFT, padx=(15, 2))
        ttk.Button(toolbar, text="Stop",
                   command=self.cancel_optimization).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset",
                   command=self.reset_settings).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(toolbar, text="No data loaded",
                                      foreground=self.colors["fg_dim"])
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Main 3-pane layout: Stats Comparison | Configuration | Results
        main_pane = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left pane: Stats Comparison
        left_frame = ttk.LabelFrame(main_pane, text="Stats Comparison", padding=5)
        main_pane.add(left_frame, weight=1)

        self.stats_tree = ttk.Treeview(left_frame,
                                       columns=("stat", "current", "new", "diff"),
                                       show="headings", height=22)
        self.stats_tree.heading("stat", text="Stat")
        self.stats_tree.heading("current", text="Current")
        self.stats_tree.heading("new", text="New")
        self.stats_tree.heading("diff", text="+/-")
        self.stats_tree.column("stat", width=90)
        self.stats_tree.column("current", width=65, anchor=tk.E)
        self.stats_tree.column("new", width=65, anchor=tk.E)
        self.stats_tree.column("diff", width=55, anchor=tk.E)
        self.stats_tree.pack(fill=tk.BOTH, expand=True)

        # Middle pane: Configuration (will be populated in next task)
        middle_frame = ttk.Frame(main_pane)
        main_pane.add(middle_frame, weight=1)

        # Right pane: Results (will be populated in later task)
        right_frame = ttk.LabelFrame(main_pane, text="Results", padding=5)
        main_pane.add(right_frame, weight=2)

    # === Public API (called by main GUI) ===

    def refresh_after_load(self):
        """Called after data loads to update UI components."""
        pass

    def refresh_hero_list(self):
        """Update hero combo dropdown with loaded heroes."""
        pass

    def refresh_exclude_heroes(self):
        """Populate exclude hero checkboxes with colored names."""
        pass

    # === Optimization Lifecycle ===

    def run_optimization(self):
        """Start optimization in background thread."""
        pass

    def cancel_optimization(self):
        """Cancel running optimization."""
        pass

    def check_queue(self):
        """Poll result queue for progress updates and completion."""
        pass

    # === Display Methods ===

    def display_results(self, results: list):
        """Display optimization results in tree."""
        pass

    def sort_results(self, col: str):
        """Sort results by column."""
        pass

    def on_result_select(self, event):
        """Show selected build details and stats comparison."""
        pass

    def show_current_stats(self, char_name: str):
        """Display current gear stats for character."""
        pass

    # === UI Event Handlers ===

    def on_hero_select(self, event=None):
        """Handle hero selection from dropdown."""
        pass

    def on_priority_change(self, stat_name: str):
        """Handle priority slider change."""
        pass

    def reset_settings(self):
        """Reset all settings to defaults."""
        pass
