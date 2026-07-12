#!/usr/bin/env python3
"""
License Key Generator for Relist Agent
Run this script to generate license keys for customers
"""

import secrets
import string
import json
from datetime import datetime
from pathlib import Path

LICENSE_FILE = Path("licenses.json")


def generate_license_key():
    """Generate a license key in format: RELIST-XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    key = "RELIST-"
    key += "-".join("".join(secrets.choice(chars) for _ in range(4)) for _ in range(4))
    return key


def load_licenses():
    """Load existing licenses from file"""
    if LICENSE_FILE.exists():
        with open(LICENSE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_licenses(licenses):
    """Save licenses to file"""
    with open(LICENSE_FILE, "w") as f:
        json.dump(licenses, f, indent=2)


def add_license(email, customer_name=None):
    """
    Generate and add a new license key

    Args:
        email: Customer email address
        customer_name: Optional customer name for reference

    Returns:
        Generated license key
    """
    licenses = load_licenses()

    # Generate unique key
    while True:
        key = generate_license_key()
        if key not in licenses:
            break

    # Store license info
    licenses[key] = {
        "email": email,
        "customer_name": customer_name or "Unknown",
        "generated": datetime.now().isoformat(),
        "activated": None,
        "status": "unused"
    }

    save_licenses(licenses)
    return key


def activate_license(key):
    """Mark a license as activated"""
    licenses = load_licenses()

    if key in licenses:
        licenses[key]["activated"] = datetime.now().isoformat()
        licenses[key]["status"] = "active"
        save_licenses(licenses)
        return True
    return False


def list_licenses():
    """Display all licenses"""
    licenses = load_licenses()

    if not licenses:
        print("No licenses generated yet.")
        return

    print("\n" + "="*80)
    print("LICENSE KEY INVENTORY")
    print("="*80)
    print(f"{'License Key':<25} {'Email':<30} {'Status':<10} {'Generated':<20}")
    print("-"*80)

    for key, info in sorted(licenses.items()):
        status = info.get("status", "unknown")
        generated = info.get("generated", "unknown")[:10]
        print(f"{key:<25} {info['email']:<30} {status:<10} {generated:<20}")

    print("-"*80)
    unused = sum(1 for info in licenses.values() if info.get("status") == "unused")
    active = sum(1 for info in licenses.values() if info.get("status") == "active")
    print(f"Total: {len(licenses)} | Unused: {unused} | Active: {active}")
    print("="*80 + "\n")


def validate_license(key):
    """Check if a license key is valid and active"""
    licenses = load_licenses()

    if key not in licenses:
        return False, "License key not found"

    info = licenses[key]
    if info.get("status") == "active":
        return True, f"License activated for {info.get('customer_name')}"
    elif info.get("status") == "unused":
        return False, "License not yet activated"
    else:
        return False, "License inactive"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Relist Agent - License Key Generator")
        print("\nUsage:")
        print("  python license_generator.py generate <email> [customer_name]")
        print("  python license_generator.py list")
        print("  python license_generator.py validate <key>")
        print("\nExamples:")
        print("  python license_generator.py generate john@example.com 'John Doe'")
        print("  python license_generator.py list")
        print("  python license_generator.py validate RELIST-A7K2-9M5Q-3TW8-7HX4")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "generate":
        if len(sys.argv) < 3:
            print("Error: Email required")
            sys.exit(1)

        email = sys.argv[2]
        customer_name = sys.argv[3] if len(sys.argv) > 3 else None

        key = add_license(email, customer_name)
        print(f"\n✓ License generated successfully!")
        print(f"\nLicense Key: {key}")
        print(f"Email: {email}")
        print(f"Customer: {customer_name or 'Unknown'}")
        print(f"\nReady to email to customer.")

    elif command == "list":
        list_licenses()

    elif command == "validate":
        if len(sys.argv) < 3:
            print("Error: License key required")
            sys.exit(1)

        key = sys.argv[2]
        valid, message = validate_license(key)

        if valid:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
