"""
ScoringTab - Gear scoring configuration interface.

This tab provides controls for configuring how Memory Fragments are scored:
- Custom stat priority weights (0-100 sliders for each stat)
- Preset configurations (DPS-focused, Tank-focused)
- Weight reset functionality
- Real-time score recalculation and inventory refresh

The scoring system affects:
- Gear score calculation for each Memory Fragment
- Filtering during optimization (top X% selection)
- Inventory display rankings
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from ..base_tab import BaseTab
from ..context import AppContext
from game_data import STATS


class ScoringTab(BaseTab):
    """Tab for configuring gear scoring weights and presets."""

    def __init__(self, parent: tk.Widget, context: AppContext):
        """
        Initialize the ScoringTab.

        Args:
            parent: Parent widget (typically the notebook)
            context: Application context with shared dependencies
        """
        super().__init__(parent, context)
        self._init_state()
        self.setup_ui()

    def _init_state(self):
        """Initialize state variables."""
        # Widget references (set in setup_ui)
        self.stat_weight_vars = {}      # Dict[str, tk.DoubleVar] - 16 stat weights
        self.weight_status = None       # ttk.Label - status message

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

    def reset_weights(self):
        """Reset all stat priority weights to default values (0)."""
        # TODO: Set all priority_vars to 0
        # TODO: Update optimizer.priorities
        # TODO: Recalculate scores and refresh inventory
        pass

    def preset_dps_weights(self):
        """Apply DPS-focused preset weights (ATK%, CRate, CDmg prioritized)."""
        # TODO: Set ATK%, CRate, CDmg to high values
        # TODO: Update optimizer.priorities
        # TODO: Recalculate scores and refresh inventory
        pass

    def preset_tank_weights(self):
        """Apply Tank-focused preset weights (HP%, DEF% prioritized)."""
        # TODO: Set HP%, DEF% to high values
        # TODO: Update optimizer.priorities
        # TODO: Recalculate scores and refresh inventory
        pass

    def apply_custom_weights(self):
        """Apply current slider values as custom weights."""
        # TODO: Read all priority_vars
        # TODO: Update optimizer.priorities
        # TODO: Recalculate scores
        # TODO: Refresh inventory display
        # TODO: Log action to console
        pass
