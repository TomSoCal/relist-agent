"""
License key validation for Relist Agent with checksum verification
Format: RA-{ORDER_ID}-{RANDOM_8_CHAR}-{CHECKSUM}
Example: RA-50-7872742F-X7K9M2W4
"""

import hashlib
import json
from pathlib import Path

LICENSE_SECRET = 'relist-agent-secret'  # Must match website


def validate_license_key(license_key: str) -> tuple:
    """
    Validate license key with checksum verification

    Args:
        license_key: Key in format RA-{ORDER_ID}-{RANDOM_8_CHAR}-{CHECKSUM}

    Returns:
        (is_valid: bool, message: str)
    """
    if not license_key:
        return False, "No license key provided"

    # Check format
    parts = license_key.split('-')
    if len(parts) != 4:
        return False, "Invalid key format (expected RA-XX-XXXXXXXX-XXXXXXXX)"

    # Extract parts
    prefix = parts[0]  # RA
    order_id = parts[1]  # 50
    random_part = parts[2]  # 7872742F
    provided_checksum = parts[3]  # X7K9M2W4

    # Validate prefix
    if prefix != 'RA':
        return False, "Invalid key prefix (must be RA)"

    # Reconstruct base key for checksum calculation
    base_key = f"{prefix}-{order_id}-{random_part}"

    # Recalculate checksum
    checksum_input = base_key + LICENSE_SECRET
    calculated_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:8].upper()

    # Compare checksums
    if provided_checksum.upper() != calculated_checksum:
        return False, "Invalid key (checksum verification failed)"

    # Key is valid!
    return True, "License key is valid"


def get_license_key_from_config(config_file: str = None) -> str:
    """
    Load license key from config.json

    Args:
        config_file: Path to config.json (uses current dir if not provided)

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
    if not license_key:
        return False

    is_valid, _ = validate_license_key(license_key)
    return is_valid
