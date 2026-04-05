"""
app/config.py
-------------
Loads and exposes the application configuration from config.json.
All modules import from here — never read config.json directly.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

# Resolve config.json relative to the project root (one level up from app/)
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

def load_config() -> dict:
    """Load and return the configuration dictionary from config.json."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("config.json not found at %s", _CONFIG_PATH)
        raise
    except json.JSONDecodeError as e:
        logger.error("config.json is malformed: %s", e)
        raise

# Module-level singleton — loaded once, shared everywhere
CONFIG = load_config()
