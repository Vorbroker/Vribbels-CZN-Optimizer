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
