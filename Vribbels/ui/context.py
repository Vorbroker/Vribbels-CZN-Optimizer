"""
Application context for dependency injection across UI tabs.

Provides shared state and services to all tabs without tight coupling.
"""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from optimizer import GearOptimizer
    from capture import CaptureManager
    from ui.tabs import InventoryTab, HeroesTab


@dataclass
class AppContext:
    """
    Application context providing shared state and services to all tabs.

    This acts as a dependency injection container, allowing tabs to access
    shared resources without tight coupling to the main GUI class.

    Attributes:
        root: Main Tk window
        notebook: Main ttk.Notebook containing all tabs
        optimizer: GearOptimizer instance for data and optimization
        capture_manager: CaptureManager for capture operations
        colors: Color palette dictionary
        style: ttk.Style instance for theming

        # Callbacks for cross-tab communication
        load_data_callback: Callback to load data file (filepath: str) -> None
        switch_tab_callback: Callback to switch to a tab (tab_frame: tk.Widget) -> None
        refresh_callback: Optional callback to refresh displays after data load
        inventory_tab: Optional reference to InventoryTab for cross-tab refresh
        heroes_tab: Optional reference to HeroesTab for cross-tab refresh
    """

    # Core widgets
    root: tk.Tk
    notebook: ttk.Notebook

    # Services
    optimizer: 'GearOptimizer'
    capture_manager: 'CaptureManager'

    # Styling
    colors: dict
    style: ttk.Style

    # Callbacks
    load_data_callback: Callable[[str], None]
    switch_tab_callback: Callable[[tk.Widget], None]
    refresh_callback: Optional[Callable[[], None]] = None
    inventory_tab: Optional['InventoryTab'] = None
    heroes_tab: Optional['HeroesTab'] = None
