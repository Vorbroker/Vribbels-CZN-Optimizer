"""
Update checking functionality for Vribbels CZN Optimizer.

Checks GitHub releases for new versions and manages update notifications.
"""

import os
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import requests
from packaging import version as pkg_version

from version import __version__


@dataclass
class UpdateInfo:
    """Information about an available update."""
    current_version: str
    latest_version: str
    update_available: bool
    download_url: str
    error: Optional[str] = None


class UpdateChecker:
    """
    Manages version checking against GitHub releases.

    Features:
    - Checks GitHub API for latest release
    - Compares semantic versions
    - Persists metadata (last check time, skipped versions)
    - Opens browser to releases page
    """

    def __init__(self):
        """Initialize the update checker."""
        self.github_repo = "Vorbroker/Vribbels-CZN-Optimizer"
        self.api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.releases_url = f"https://github.com/{self.github_repo}/releases"

        # Metadata file location in AppData
        appdata = os.getenv('APPDATA')
        if not appdata:
            appdata = os.path.expanduser("~")
        self.config_dir = Path(appdata) / 'Vribbels'
        self.config_file = self.config_dir / 'update_check.json'

        self.current_version = __version__

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
