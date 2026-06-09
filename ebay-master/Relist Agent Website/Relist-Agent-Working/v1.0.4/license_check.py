"""
License key validation for Relist Agent
Validates keys in format: RA-50-7872742F (RA-NN-XXXXXXXX)
"""

import re
from pathlib import Path
import json


def validate_license_key(key: str) -> bool:
    """
    Validate license key format: RA-XX-XXXXXXXX

    Args:
        key: License key string to validate

    Returns:
        True if valid format, False otherwise
    """
    if not key:
        return False

    # Pattern: RA-<2 digits>-<8 hex characters>
    pattern = r'^RA-\d{2}-[0-9A-F]{8}$'
    return bool(re.match(pattern, key, re.IGNORECASE))


def get_license_key_from_config(config_file: str = None) -> str:
    """
    Load license key from config.json

    Args:
        config_file: Path to config.json (uses BASE_DIR if not provided)

    Returns:
        License key string or empty string if not found
    """
    if config_file is None:
        config_file = Path(__file__).parent / "config.json"
    else:
        config_file = Path(config_file)

    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('license_key', '')
    except Exception:
        pass

    return ''


def check_license() -> bool:
    """
    Check if app has valid license key in config

    Returns:
        True if license is valid, False otherwise
    """
    license_key = get_license_key_from_config()
    return validate_license_key(license_key)
