"""
Capture orchestration manager for CZN game data interception.
Handles proxy lifecycle, hosts file modification, and data capture coordination.
"""

import subprocess
import threading
import socket
import re
import ctypes
import sys
import os
from pathlib import Path
from typing import Optional, Callable

from .constants import PROXY_PORT, GAME_PORT, HOSTS_PATH


class CaptureError(Exception):
    """Raised when capture operations fail."""
    pass


# Addon template embedded as string constant (works in bundled executables)
ADDON_TEMPLATE = '''"""
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
        log_callback: Optional[Callable[[str], None]] = None,
        server_hostname: Optional[str] = None
    ):
        """
        Initialize the capture addon.

        Args:
            output_dir: Directory to save captured JSON files
            log_callback: Optional callback for logging messages (defaults to print)
            server_hostname: Game server hostname for proper SNI (TLS Server Name Indication)
        """
        self.output_dir = output_dir
        self.log_callback = log_callback or print
        self.server_hostname = server_hostname
        self.inventory_data = None
        self.character_data = None
        self.saved_path = None

    def server_connect(self, data):
        """
        Hook called when mitmproxy connects to upstream server.
        Sets the correct SNI hostname for proper virtual hosting.
        """
        if self.server_hostname:
            # Override SNI to use game server hostname instead of IP
            data.server_conn.sni = self.server_hostname

    def _detect_region(self) -> Optional[str]:
        """Detect server region from world_id in character data."""
        if not self.character_data:
            return None

        # Check for world_id in user data
        user_data = self.character_data.get("user", {})
        world_id = user_data.get("world_id", "")

        # Map world_id to region
        if "world_live_global" in world_id:
            return "global"
        elif "world_live_asia" in world_id:
            return "asia"

        return None

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
            "detected_region": self._detect_region(),
        }

        with open(self.saved_path, "w") as f:
            json.dump(save_data, f, indent=2)

        count = len(self.inventory_data.get("piece_items", []))
        has_chars = "Yes" if self.character_data else "No"
        self.log_callback(
            f">>> SAVED {count} Memory Fragments (char data: {has_chars}) to {self.saved_path.name}"
        )
'''


class CaptureManager:
    """
    Manages the complete capture workflow:
    - Proxy server lifecycle
    - Hosts file modification/restoration
    - Game server resolution
    - Data capture coordination
    """

    def __init__(
        self,
        output_folder: Path,
        log_callback: Callable[[str, Optional[str]], None],
        status_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the capture manager.

        Args:
            output_folder: Directory to save captured JSON files
            log_callback: Function(message, tag) for logging (tag can be None, "success", "error", "warning", "info")
            status_callback: Optional function(status) for status updates
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.log_callback = log_callback
        self.status_callback = status_callback

        self.capturing = False
        self.proxy_process = None
        self.game_server_ips = {}
        self.original_hosts_content = None
        self.current_region = "global"  # Default region

    def is_capturing(self) -> bool:
        """Check if currently capturing."""
        return self.capturing

    def get_latest_capture(self) -> Optional[Path]:
        """
        Get path to most recent capture file.

        Returns:
            Path to latest capture file, or None if no snapshots exist
        """
        files = list(self.output_folder.glob("memory_fragments_*.json"))
        return max(files, key=lambda f: f.stat().st_mtime) if files else None

    def _read_detected_region(self, capture_file: Path) -> Optional[str]:
        """Read detected_region from capture file."""
        import json
        try:
            with open(capture_file, 'r') as f:
                data = json.load(f)
            return data.get("detected_region")
        except Exception:
            return None

    def open_snapshots_folder(self):
        """Open snapshots folder in file explorer."""
        self.output_folder.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.output_folder)
        else:
            subprocess.run(["xdg-open", str(self.output_folder)])

    def set_region(self, region_id: str):
        """Set the active server region for capture."""
        from .constants import SERVERS
        if region_id not in SERVERS:
            raise ValueError(f"Unknown region: {region_id}")
        self.current_region = region_id

    def resolve_game_server(self):
        """
        Resolve game server hostnames to IP addresses for current region.
        Stores results in self.game_server_ips.
        """
        from .constants import SERVERS
        server_config = SERVERS[self.current_region]
        self.game_server_ips = {}
        for host in server_config.hosts:
            try:
                ip = socket.gethostbyname(host)
                self.game_server_ips[host] = ip
            except socket.gaierror:
                pass

    def modify_hosts_file(self) -> str:
        """
        Modify Windows hosts file to redirect game traffic to local proxy.

        Returns:
            Original hosts file content (for restoration)

        Raises:
            CaptureError: If hosts file modification fails
        """
        try:
            with open(HOSTS_PATH, "r") as f:
                content = f.read()

            # Don't modify if already modified
            if "# CZN-CAPTURE-START" in content:
                return content

            # Add redirect entries
            from .constants import SERVERS
            server_config = SERVERS[self.current_region]
            entries = ["\n# CZN-CAPTURE-START"]
            for host in server_config.hosts:
                entries.append(f"127.0.0.1 {host}")
            entries.append("# CZN-CAPTURE-END\n")

            new_content = content + "\n".join(entries)

            with open(HOSTS_PATH, "w") as f:
                f.write(new_content)

            # Flush DNS cache
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)

            return content

        except Exception as e:
            raise CaptureError(f"Failed to modify hosts file: {e}")

    def restore_hosts_file(self):
        """
        Restore Windows hosts file to original state.
        Removes CZN-CAPTURE entries added by modify_hosts_file().
        """
        try:
            with open(HOSTS_PATH, "r") as f:
                content = f.read()

            # Remove our capture entries
            pattern = r'\n*# CZN-CAPTURE-START.*?# CZN-CAPTURE-END\n*'
            content = re.sub(pattern, '', content, flags=re.DOTALL)

            with open(HOSTS_PATH, "w") as f:
                f.write(content)

            # Flush DNS cache
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)

        except Exception as e:
            self.log_callback(f"Failed to restore hosts: {e}", "error")

    def _generate_addon_script(self) -> Path:
        """
        Generate temporary addon script with configured output directory.

        Returns:
            Path to generated addon script

        Raises:
            CaptureError: If script generation fails
        """
        try:
            addon_script = self.output_folder / "_capture_addon.py"

            # Get server hostname for proper SNI
            from .constants import SERVERS
            server_config = SERVERS[self.current_region]
            server_hostname = server_config.hosts[0]

            # Generate standalone script using embedded template
            addon_code = f'''{ADDON_TEMPLATE}

OUTPUT_DIR = Path(r"{self.output_folder.absolute()}")
SERVER_HOSTNAME = "{server_hostname}"

addons = [Addon(OUTPUT_DIR, server_hostname=SERVER_HOSTNAME)]
'''

            with open(addon_script, "w") as f:
                f.write(addon_code)

            return addon_script

        except Exception as e:
            raise CaptureError(f"Failed to generate addon script: {e}")

    def _read_proxy_output(self):
        """
        Read proxy process output and forward to log callback.
        Runs in background thread.
        """
        if not self.proxy_process:
            return

        try:
            for line in self.proxy_process.stdout:
                line = line.strip()
                if line:
                    self.log_callback(f"[proxy] {line}", None)
                    # Update status when data is saved
                    if "SAVED" in line and "Memory Fragments" in line:
                        if self.status_callback:
                            self.status_callback("[OK] Data Captured!")
        except Exception:
            pass

    def start_capture(self):
        """
        Start the capture process:
        1. Check admin privileges
        2. Resolve game servers
        3. Modify hosts file
        4. Generate addon script
        5. Start mitmproxy
        6. Start background thread for output reading

        Raises:
            CaptureError: If capture cannot be started
        """
        # Check admin privileges
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                raise CaptureError(
                    "Administrator privileges required.\n\n"
                    "Please restart as Administrator."
                )
        except AttributeError:
            # Not on Windows, skip admin check
            pass

        self.log_callback("="*50, None)
        self.log_callback("Starting capture...", None)

        # Resolve game servers
        if not self.game_server_ips:
            self.resolve_game_server()

        if not self.game_server_ips:
            raise CaptureError("Could not resolve game servers.")

        # Get first resolved IP for upstream connection
        # (Using IP avoids circular DNS lookup through modified hosts file)
        real_ip = list(self.game_server_ips.values())[0]

        # Modify hosts file
        try:
            self.modify_hosts_file()
            self.log_callback("Hosts file modified", "success")
        except CaptureError as e:
            raise CaptureError(f"Failed to modify hosts file: {e}")

        # Generate addon script
        try:
            addon_script = self._generate_addon_script()
        except CaptureError as e:
            self.restore_hosts_file()
            raise

        self.log_callback(f"Starting proxy on port {PROXY_PORT}...", None)

        # Build mitmdump command
        cmd = [
            "mitmdump",
            "--mode", f"reverse:https://{real_ip}:{GAME_PORT}/",
            "--listen-port", str(PROXY_PORT),
            "--ssl-insecure",
            "--set", "upstream_cert=false",
            "--set", "keep_host_header=true",
            "--set", "connection_strategy=lazy",
            "-s", str(addon_script),
            "-q",
        ]

        # Start proxy process
        try:
            # Hide console window on Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo
            )
            threading.Thread(target=self._read_proxy_output, daemon=True).start()
        except Exception as e:
            self.log_callback(f"[X] Failed to start proxy: {e}", "error")
            self.restore_hosts_file()
            raise CaptureError(f"Failed to start proxy: {e}")

        self.capturing = True

        if self.status_callback:
            self.status_callback("Capturing...")

        self.log_callback("="*50, None)
        self.log_callback("[OK] Capture started!", "success")
        self.log_callback("Now launch the game and load into the main menu.", None)

    def stop_capture(self) -> Optional[tuple[Path, Optional[str]]]:
        """
        Stop the capture process:
        1. Terminate proxy process
        2. Restore hosts file
        3. Return path to captured file

        Returns:
            Path to captured file if any, None otherwise
        """
        if not self.capturing:
            return None

        self.log_callback("Stopping capture...", None)

        # Stop proxy
        if self.proxy_process:
            self.proxy_process.terminate()
            try:
                self.proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()
            self.proxy_process = None
            self.log_callback("[OK] Proxy stopped", "success")

        # Restore hosts file
        self.restore_hosts_file()
        self.log_callback("[OK] Hosts file restored", "success")

        self.capturing = False

        if self.status_callback:
            self.status_callback("[O] Stopped")

        # Get latest capture file
        latest = self.get_latest_capture()
        if latest:
            detected = self._read_detected_region(latest)
            self.log_callback(f"[OK] Latest capture: {latest.name}", "success")
            return (latest, detected)

        self.log_callback("="*50, None)

        return None
