"""
Application configuration and user preferences management.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """Application configuration and user preferences."""
    server_region: str = "global"  # Default to global server


CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> AppConfig:
    """Load configuration from file, or return defaults if not found."""
    if not CONFIG_FILE.exists():
        return AppConfig()

    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
        return AppConfig(**data)
    except Exception:
        # If config is corrupted, return defaults
        return AppConfig()


def save_config(config: AppConfig):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    except Exception:
        pass  # Silently fail if can't save
