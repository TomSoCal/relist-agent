"""
License key validation for Relist Agent with checksum verification + one-time use
Format: RA-{ORDER_ID}-{RANDOM_8_CHAR}-{CHECKSUM}
Example: RA-50-7872742F-X7K9M2W4

One-time use: Each key can only be activated once. Used keys are tracked in used_keys.json
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime

LICENSE_SECRET = 'relist-agent-secret'  # Must match website


def get_used_keys_file() -> Path:
    """Get path to used_keys.json tracking file"""
    return Path(__file__).parent / "used_keys.json"


def load_used_keys() -> dict:
    """Load tracking of used keys"""
    used_file = get_used_keys_file()
    if used_file.exists():
        try:
            with open(used_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def is_key_already_used(license_key: str) -> bool:
    """Check if key has already been activated"""
    used_keys = load_used_keys()
    return license_key in used_keys


def mark_key_as_used(license_key: str) -> None:
    """Mark a key as used with activation timestamp"""
    used_keys = load_used_keys()
    used_keys[license_key] = {
        'activated_at': datetime.now().isoformat(),
        'machine_id': _get_machine_id()
    }

    used_file = get_used_keys_file()
    with open(used_file, 'w', encoding='utf-8') as f:
        json.dump(used_keys, f, indent=2)


def _get_machine_id() -> str:
    """Get unique machine identifier"""
    import socket
    import hashlib
    hostname = socket.gethostname()
    return hashlib.md5(hostname.encode()).hexdigest()[:8]


def validate_license_key(license_key: str) -> tuple:
    """
    Validate license key with checksum verification (one-time use)

    Args:
        license_key: Key in format RA-{ORDER_ID}-{RANDOM_8_CHAR}-{CHECKSUM}

    Returns:
        (is_valid: bool, message: str)
    """
    if not license_key:
        return False, "No license key provided"

    # Check if already used
    if is_key_already_used(license_key):
        return False, "This license key has already been activated"

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

    # Key is valid - mark as used
    try:
        mark_key_as_used(license_key)
    except:
        pass  # Non-fatal - key still activates even if tracking fails

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
