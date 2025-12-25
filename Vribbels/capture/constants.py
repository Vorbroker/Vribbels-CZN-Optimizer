"""
Capture system constants for CZN data interception.
"""

from pathlib import Path

# Network configuration
GAME_HOSTS = ["live-g-czn-gamemjc2n1x.game.playstove.com"]
GAME_PORT = 13701
PROXY_PORT = 13701

# File system paths
OUTPUT_DIR = Path(__file__).parent.parent / "snapshots"
HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
