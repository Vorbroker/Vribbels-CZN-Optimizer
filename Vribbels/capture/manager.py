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
from .setup import find_mitmdump


class CaptureError(Exception):
    """Raised when capture operations fail."""
    pass


# Addon template embedded as string constant (works in bundled executables)
ADDON_TEMPLATE = '''"""
mitmproxy Addon for intercepting CZN game WebSocket traffic.
Extracts Memory Fragment inventory and character data from game API responses.
"""

import json
import gzip
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


class Addon:
    """mitmproxy addon that intercepts WebSocket messages and extracts game data."""

    def __init__(
        self,
        output_dir: Path,
        dict_path: Optional[Path] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the capture addon.

        Args:
            output_dir: Directory to save captured JSON files
            dict_path: Optional path to zstd dictionary file
            log_callback: Optional callback for logging messages (defaults to print)
        """
        self.output_dir = output_dir
        self.log_callback = log_callback or print
        self.inventory_data = None
        self.character_data = None
        self.saved_path = None
        self.zstd_dict = None
        self.zstd_dctx = None

        # Load zstd dictionary if available
        if dict_path and dict_path.exists() and HAS_ZSTD:
            try:
                with open(dict_path, 'rb') as f:
                    dict_data = f.read()
                self.zstd_dict = zstd.ZstdCompressionDict(dict_data)
                self.zstd_dctx = zstd.ZstdDecompressor(dict_data=self.zstd_dict)
            except Exception as e:
                self.log_callback(f"Warning: Failed to load zstd dictionary: {e}")

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

    def _try_decode_binary(self, raw_bytes):
        """
        Try to decode binary data - may be compressed or plain JSON.
        Returns decoded string or None if unable to decode.
        """
        size = len(raw_bytes)

        # Try plain UTF-8 first
        try:
            return raw_bytes.decode('utf-8')
        except:
            pass

        # Check for Zstandard magic number (0x28 0xB5 0x2F 0xFD)
        ZSTD_MAGIC = bytes([0x28, 0xB5, 0x2F, 0xFD])
        is_zstd = len(raw_bytes) >= 4 and raw_bytes[:4] == ZSTD_MAGIC

        if is_zstd:
            if HAS_ZSTD:
                # Try with dictionary first (required for CZN game data)
                if self.zstd_dctx:
                    try:
                        decompressed = self.zstd_dctx.decompress(raw_bytes)
                        return decompressed.decode('utf-8')
                    except:
                        pass

                # Try without dictionary as fallback
                try:
                    dctx = zstd.ZstdDecompressor()
                    decompressed = dctx.decompress(raw_bytes)
                    return decompressed.decode('utf-8')
                except:
                    pass
            else:
                self.log_callback("ERROR: zstandard module not installed!")

        # Try zstd anyway (in case magic check failed)
        if HAS_ZSTD and not is_zstd:
            # Try with dictionary first
            if self.zstd_dctx:
                try:
                    decompressed = self.zstd_dctx.decompress(raw_bytes)
                    return decompressed.decode('utf-8')
                except:
                    pass
            # Try without dictionary
            try:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(raw_bytes)
                return decompressed.decode('utf-8')
            except:
                pass

        # Try gzip decompression
        try:
            decompressed = gzip.decompress(raw_bytes)
            return decompressed.decode('utf-8')
        except:
            pass

        # Try zlib decompression (with and without header)
        for wbits in [15, -15, 31, 47]:
            try:
                decompressed = zlib.decompress(raw_bytes, wbits)
                return decompressed.decode('utf-8')
            except:
                pass

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
            # Handle both text and binary WebSocket frames
            if msg.is_text:
                content = msg.text
            else:
                # Binary frame - try to decode/decompress
                content = self._try_decode_binary(msg.content)
                if content is None:
                    return

            data = json.loads(content)
            if data.get("res") != "ok":
                return

            # Check for 'info' structure (new API format)
            if "info" in data:
                info = data.get("info", {})

                # Check for item data in new format
                if isinstance(info, dict) and "item" in info:
                    item_info = info.get("item", {})

                    # Check for piece (Memory Fragment) data
                    if "piece" in item_info:
                        piece_info = item_info.get("piece", {})
                        # Store this as inventory data (new format)
                        if not self.inventory_data:
                            self.inventory_data = {}
                        self.inventory_data["info_item_piece"] = piece_info
                        self._save_data()

                # Check for character data in new format
                if isinstance(info, dict) and "character" in info:
                    char_info = info.get("character", {})
                    if not self.character_data:
                        self.character_data = {}
                    self.character_data["info_character"] = char_info
                    self._save_data()

            # Capture inventory data (Memory Fragments)
            if "piece_items" in data:
                self.inventory_data = data
                self._save_data()

            # Capture character data
            has_characters = "characters" in data and isinstance(data.get("characters"), list)
            has_user = "user" in data

            if has_characters or has_user:
                self.character_data = data
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
        char_count = len(self.character_data.get("characters", [])) if self.character_data else 0
        self.log_callback(
            f"Saved: {count} Memory Fragments, {char_count} characters -> {self.saved_path.name}"
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

    def _find_dictionary_path(self) -> Optional[Path]:
        """
        Find the zstd dictionary file.
        Searches in order: output_folder, Vribbels folder, bundled location.
        If found in bundled location, copies to output_folder for addon script access.

        Returns:
            Path to dictionary file if found, None otherwise
        """
        import shutil
        dict_name = "zstd_dictionary.bin"

        # Check output folder first (always accessible by addon script)
        dict_path = self.output_folder / dict_name
        if dict_path.exists():
            return dict_path

        # Check Vribbels folder (development mode)
        vribbels_folder = Path(__file__).parent.parent
        source_path = vribbels_folder / dict_name
        if source_path.exists():
            return source_path

        # Check if running from PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            bundled_path = Path(sys._MEIPASS) / dict_name
            if bundled_path.exists():
                # Copy to output folder so addon script can access it
                # (addon runs as separate process without _MEIPASS access)
                try:
                    dest_path = self.output_folder / dict_name
                    shutil.copy2(bundled_path, dest_path)
                    return dest_path
                except Exception:
                    # Return bundled path as fallback
                    return bundled_path

        return None

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

            # Find dictionary path
            dict_path = self._find_dictionary_path()
            dict_path_str = f'Path(r"{dict_path}")' if dict_path else "None"

            if not dict_path:
                self.log_callback("Warning: zstd dictionary not found", "warning")

            # Generate standalone script using embedded template
            addon_code = f'''{ADDON_TEMPLATE}

OUTPUT_DIR = Path(r"{self.output_folder.absolute()}")
DICT_PATH = {dict_path_str}

addons = [Addon(OUTPUT_DIR, dict_path=DICT_PATH)]
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

        # Patterns to filter out (verbose mitmproxy messages)
        skip_patterns = [
            "Loading script",
            "client connect",
            "client disconnect",
            "server connect",
            "server disconnect",
            "HTTP/2 connection",
            "CONNECT",
            "<<",
            ">>",
        ]

        try:
            for line in self.proxy_process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Skip verbose mitmproxy messages
                if any(pattern.lower() in line.lower() for pattern in skip_patterns):
                    continue

                self.log_callback(f"[proxy] {line}", None)

                # Update status when data is saved
                if "Saved:" in line and "Memory Fragments" in line:
                    if self.status_callback:
                        self.status_callback("[OK] Data Captured!")

            # Check exit code when process ends
            if self.proxy_process:
                exit_code = self.proxy_process.poll()
                if exit_code is not None and exit_code != 0:
                    self.log_callback(f"[proxy] Process exited with code {exit_code}", "error")
        except Exception as e:
            self.log_callback(f"[proxy] Output reader error: {e}", "error")

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

        self.log_callback("Starting capture...", None)

        # Resolve game servers for current region
        # (Always re-resolve to ensure we use the correct region's servers)
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

        # Find mitmdump executable
        mitmdump_path = find_mitmdump()
        if not mitmdump_path:
            self.restore_hosts_file()
            raise CaptureError(
                "mitmdump not found.\n\n"
                "Please ensure mitmproxy is installed and accessible.\n"
                "Run 'pip install mitmproxy' in a terminal, or check the Setup tab."
            )

        # Build mitmdump command
        # Note: -q (quiet) removed to allow seeing errors and addon output
        cmd = [
            mitmdump_path,
            "--mode", f"reverse:https://{real_ip}:{GAME_PORT}/",
            "--listen-port", str(PROXY_PORT),
            "--ssl-insecure",
            "--set", "upstream_cert=false",
            "--set", "keep_host_header=true",
            "--set", "connection_strategy=lazy",
            "-s", str(addon_script),
        ]

        # Start proxy process
        try:
            # Hide console window on Windows
            startupinfo = None
            creationflags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                # CREATE_NO_WINDOW flag to prevent console window
                creationflags = subprocess.CREATE_NO_WINDOW

            self.proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            threading.Thread(target=self._read_proxy_output, daemon=True).start()
        except Exception as e:
            self.log_callback(f"[X] Failed to start proxy: {e}", "error")
            self.restore_hosts_file()
            raise CaptureError(f"Failed to start proxy: {e}")

        self.capturing = True

        if self.status_callback:
            self.status_callback("Capturing...")

        self.log_callback("Capture started! Launch the game and load into the main menu.", "success")

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

        # Stop proxy
        if self.proxy_process:
            self.proxy_process.terminate()
            try:
                self.proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()
            self.proxy_process = None

        # Restore hosts file
        self.restore_hosts_file()

        self.capturing = False

        if self.status_callback:
            self.status_callback("[O] Stopped")

        # Get latest capture file
        latest = self.get_latest_capture()
        if latest:
            detected = self._read_detected_region(latest)
            self.log_callback(f"Capture stopped. File: {latest.name}", "success")
            return (latest, detected)

        self.log_callback("Capture stopped. No data captured.", None)
        return None
