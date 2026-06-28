import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

_config = None


def load_config() -> dict:
    global _config
    if _config is not None:
        return _config

    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"config.yaml not found at {CONFIG_PATH}")

    with open(CONFIG_PATH) as f:
        _config = yaml.safe_load(f)

    return _config


def get(section: str, key: str, fallback=None):
    """Get a config value by section and key."""
    try:
        return load_config()[section][key]
    except (KeyError, TypeError):
        return fallback
