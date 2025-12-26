"""
Capture system constants for CZN data interception.
"""

import sys
from pathlib import Path

# Network configuration
GAME_HOSTS = ["live-g-czn-gamemjc2n1x.game.playstove.com"]
GAME_PORT = 13701
PROXY_PORT = 13701

# File system paths
# When running from PyInstaller bundle, use exe directory
# When running from source, use script directory
if getattr(sys, 'frozen', False):
    # Running from bundled exe - use exe directory
    BASE_DIR = Path(sys.executable).parent
else:
    # Running from source - use script directory
    BASE_DIR = Path(__file__).parent.parent

OUTPUT_DIR = BASE_DIR / "snapshots"
HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
