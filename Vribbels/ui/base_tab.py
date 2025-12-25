"""
Base tab class for all UI tabs in the CZN Optimizer.

Provides common infrastructure and enforces consistent tab interface.
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import AppContext


class BaseTab(ABC):
    """
    Abstract base class for all UI tabs.

    Provides common infrastructure and enforces consistent tab interface.
    Each tab receives an AppContext for accessing shared state and services.
    """

    def __init__(self, parent: tk.Widget, context: 'AppContext'):
        """
        Initialize the tab.

        Args:
            parent: Parent widget (typically a ttk.Notebook)
            context: Application context with shared state
        """
        self.parent = parent
        self.context = context
        self.frame = ttk.Frame(parent)

    @abstractmethod
    def setup_ui(self):
        """
        Setup the tab's UI components.

        Called once during initialization to build the tab's interface.
        Must be implemented by subclasses.
        """
        pass

    def get_frame(self) -> ttk.Frame:
        """Return the tab's root frame for adding to notebook."""
        return self.frame

    # Convenience properties for accessing shared resources
    @property
    def colors(self) -> dict:
        """Access color palette from context."""
        return self.context.colors

    @property
    def optimizer(self):
        """Access optimizer instance from context."""
        return self.context.optimizer

    @property
    def notebook(self) -> ttk.Notebook:
        """Access main notebook from context."""
        return self.context.notebook

    @property
    def root(self) -> tk.Tk:
        """Access root window from context."""
        return self.context.root
