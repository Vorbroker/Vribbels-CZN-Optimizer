"""
mitmproxy Addon for intercepting CZN game WebSocket traffic.
Extracts Memory Fragment inventory and character data from game API responses.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable


class Addon:
    """mitmproxy addon that intercepts WebSocket messages and extracts game data."""

    def __init__(
        self,
        output_dir: Path,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the capture addon.

        Args:
            output_dir: Directory to save captured JSON files
            log_callback: Optional callback for logging messages (defaults to print)
        """
        self.output_dir = output_dir
        self.log_callback = log_callback or print
        self.inventory_data = None
        self.character_data = None
        self.saved_path = None

    def websocket_message(self, flow):
        """
        Handle WebSocket messages from the game server.
        Extracts piece_items (inventory) and characters data.

        Args:
            flow: mitmproxy flow object containing WebSocket messages
        """
        msg = flow.websocket.messages[-1]
        if msg.from_client:
            return

        try:
            data = json.loads(msg.text)
            if data.get("res") != "ok":
                return

            keys = list(data.keys())
            self.log_callback(f">>> API response keys: {keys}")

            # Capture inventory data (Memory Fragments)
            if "piece_items" in data:
                self.inventory_data = data
                count = len(data.get('piece_items', []))
                self.log_callback(f">>> Captured inventory: {count} pieces")
                self._save_data()

            # Capture character data
            has_characters = "characters" in data and isinstance(data.get("characters"), list)
            has_user = "user" in data

            if has_characters or has_user:
                self.character_data = data
                char_count = len(data.get("characters", []))
                self.log_callback(f">>> Captured character data: {char_count} chars")
                self._save_data()

        except Exception as e:
            self.log_callback(f"Error: {e}")

    def _save_data(self):
        """
        Save captured data to JSON file.
        Only saves when inventory data is available.
        Combines inventory and character data into single file.
        """
        if not self.inventory_data:
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not self.saved_path:
            self.saved_path = self.output_dir / f"memory_fragments_{ts}.json"

        save_data = {
            "capture_time": datetime.now().isoformat(),
            "inventory": self.inventory_data,
            "characters": self.character_data,
        }

        with open(self.saved_path, "w") as f:
            json.dump(save_data, f, indent=2)

        count = len(self.inventory_data.get("piece_items", []))
        has_chars = "Yes" if self.character_data else "No"
        self.log_callback(
            f">>> SAVED {count} Memory Fragments (char data: {has_chars}) to {self.saved_path.name}"
        )
