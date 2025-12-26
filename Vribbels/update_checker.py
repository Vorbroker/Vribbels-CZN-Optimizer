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

    def check_for_updates(self) -> UpdateInfo:
        """
        Check GitHub API for latest release.

        Makes API call, compares versions, updates metadata.
        Never raises exceptions - errors are returned in UpdateInfo.error.

        Returns:
            UpdateInfo object with check results
        """
        metadata = self._read_metadata()

        try:
            # Make API request with 5 second timeout
            response = requests.get(self.api_url, timeout=5)
            response.raise_for_status()

            # Parse response
            release_data = response.json()
            tag_name = release_data.get('tag_name', '')

            # Strip 'v' prefix if present
            latest_version = tag_name.lstrip('v')

            # Validate version string before parsing
            if not latest_version:
                raise ValueError("Empty version string from GitHub")

            download_url = release_data.get('html_url') or self.releases_url

            # Compare versions using packaging library
            current = pkg_version.parse(self.current_version)
            latest = pkg_version.parse(latest_version)
            update_available = latest > current

            # Update metadata
            metadata['last_check_timestamp'] = datetime.now().isoformat()
            metadata['last_known_latest'] = latest_version
            metadata['last_error'] = None
            self._write_metadata(metadata)

            return UpdateInfo(
                current_version=self.current_version,
                latest_version=latest_version,
                update_available=update_available,
                download_url=download_url,
                error=None
            )

        except requests.exceptions.Timeout:
            error_msg = "Network timeout"
        except requests.exceptions.ConnectionError:
            error_msg = "No internet connection"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                error_msg = "GitHub API rate limit exceeded"
            else:
                error_msg = f"GitHub API error: {e.response.status_code}"
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            error_msg = "Invalid response from GitHub"
        except Exception as e:
            error_msg = "Unexpected error"

        # On error, return cached info if available
        metadata['last_error'] = error_msg
        self._write_metadata(metadata)

        cached_latest = metadata.get('last_known_latest', self.current_version)

        return UpdateInfo(
            current_version=self.current_version,
            latest_version=cached_latest,
            update_available=False,  # Don't show update on error
            download_url=self.releases_url,
            error=error_msg
        )

    def skip_version(self, version: str) -> None:
        """
        Mark a version as skipped (don't prompt again for this version).

        Args:
            version: Version string to skip (e.g., "1.4.0")
        """
        metadata = self._read_metadata()
        skipped = metadata.get('skipped_versions', [])

        if version not in skipped:
            skipped.append(version)
            metadata['skipped_versions'] = skipped
            self._write_metadata(metadata)

    def is_version_skipped(self, version: str) -> bool:
        """
        Check if a version has been marked as skipped.

        Args:
            version: Version string to check

        Returns:
            True if version is in skipped list
        """
        metadata = self._read_metadata()
        return version in metadata.get('skipped_versions', [])

    def get_cached_info(self) -> dict:
        """
        Get last known update information from cache.

        Used for displaying update status when offline.

        Returns:
            Dict with current_version, latest_version, last_check, error
        """
        metadata = self._read_metadata()

        return {
            'current_version': self.current_version,
            'latest_version': metadata.get('last_known_latest', self.current_version),
            'last_check_timestamp': metadata.get('last_check_timestamp'),
            'last_error': metadata.get('last_error')
        }

    def open_releases_page(self) -> None:
        """Open the GitHub releases page in default browser."""
        webbrowser.open(self.releases_url)
