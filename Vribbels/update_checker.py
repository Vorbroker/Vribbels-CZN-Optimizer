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

    @property
    def _default_metadata(self) -> dict:
        """Return default metadata structure."""
        return {
            "last_check_timestamp": None,
            "last_known_latest": None,
            "skipped_versions": [],
            "last_error": None
        }

    def _read_metadata(self) -> dict:
        """
        Read metadata from JSON file.

        Returns:
            Metadata dict with default values if file doesn't exist
        """
        if not self.config_file.exists():
            return self._default_metadata

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Return defaults if file is corrupted
            return self._default_metadata

    def _write_metadata(self, metadata: dict) -> None:
        """
        Write metadata to JSON file.

        Args:
            metadata: Metadata dictionary to save
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save update metadata: {e}")

    def should_check_now(self) -> bool:
        """
        Determine if we should check for updates now.

        Returns True if:
        - Never checked before (metadata doesn't exist)
        - Last check was >24 hours ago

        Returns:
            True if update check should be performed
        """
        metadata = self._read_metadata()
        last_check = metadata.get("last_check_timestamp")

        if not last_check:
            return True

        try:
            last_check_dt = datetime.fromisoformat(last_check)
            now = datetime.now()
            return (now - last_check_dt) > timedelta(hours=24)
        except (ValueError, TypeError):
            # If timestamp is invalid, check now
            return True
