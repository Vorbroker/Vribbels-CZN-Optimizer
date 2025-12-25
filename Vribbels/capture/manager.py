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
import inspect
from pathlib import Path
from typing import Optional, Callable

from .constants import PROXY_PORT, GAME_PORT, GAME_HOSTS, HOSTS_PATH
from .addon import Addon


class CaptureError(Exception):
    """Raised when capture operations fail."""
    pass


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

    def open_snapshots_folder(self):
        """Open snapshots folder in file explorer."""
        self.output_folder.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.output_folder)
        else:
            subprocess.run(["xdg-open", str(self.output_folder)])

    def resolve_game_server(self):
        """
        Resolve game server hostnames to IP addresses.
        Stores results in self.game_server_ips.
        """
        self.game_server_ips = {}
        for host in GAME_HOSTS:
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
            entries = ["\n# CZN-CAPTURE-START"]
            for host in GAME_HOSTS:
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
            # Get Addon class source code
            addon_source = inspect.getsource(Addon)

            addon_script = self.output_folder / "_capture_addon.py"

            # Generate standalone script
            addon_code = f'''
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

OUTPUT_DIR = Path(r"{self.output_folder.absolute()}")

{addon_source}

addons = [Addon(OUTPUT_DIR)]
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

        # Get first resolved IP
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
            self.proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
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

    def stop_capture(self) -> Optional[Path]:
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
            self.log_callback(f"[OK] Latest capture: {latest.name}", "success")

        self.log_callback("="*50, None)

        return latest
