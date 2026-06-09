#!/usr/bin/env python3
"""
Relist Agent License Key Generator
Generates valid license keys for beta testers
Format: RA-{ORDER_ID}-{RANDOM_8_HEX}-{CHECKSUM}
"""

import hashlib
import secrets
import sys

LICENSE_SECRET = 'relist-agent-secret'  # Must match app validation


def generate_license_key(order_id: str = None) -> str:
    """
    Generate a valid license key

    Args:
        order_id: Order ID (2 digits). If None, generates random

    Returns:
        Valid license key in format RA-XX-XXXXXXXX-XXXXXXXX
    """
    # Generate or validate order ID
    if order_id is None:
        order_id = f"{secrets.randbelow(100):02d}"
    else:
        order_id = order_id.strip()
        if not order_id.isdigit() or len(order_id) > 2:
            order_id = f"{int(order_id):02d}" if order_id.isdigit() else f"{secrets.randbelow(100):02d}"

    # Generate random 8-char hex
    random_part = secrets.token_hex(4).upper()  # 8 hex chars

    # Calculate checksum
    base_key = f"RA-{order_id}-{random_part}"
    checksum_input = base_key + LICENSE_SECRET
    checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:8].upper()

    # Complete key
    license_key = f"{base_key}-{checksum}"
    return license_key


def main():
    """Generate license keys interactively or from command line"""
    if len(sys.argv) > 1:
        # Command line: python keygen.py [order_id]
        order_id = sys.argv[1]
        key = generate_license_key(order_id)
        print(key)
    else:
        # Interactive mode
        print("=" * 60)
        print("RELIST AGENT - LICENSE KEY GENERATOR (Beta Testers)")
        print("=" * 60)
        print()

        while True:
            print("Options:")
            print("  1. Generate with random Order ID")
            print("  2. Generate with specific Order ID")
            print("  3. Generate 10 keys at once")
            print("  4. Exit")
            print()

            choice = input("Choose (1-4): ").strip()

            if choice == "1":
                key = generate_license_key()
                print(f"\n✓ Generated: {key}\n")

            elif choice == "2":
                order_id = input("Enter Order ID (2 digits): ").strip()
                try:
                    oid = int(order_id) if order_id else secrets.randbelow(100)
                    key = generate_license_key(f"{oid:02d}")
                    print(f"\n✓ Generated: {key}\n")
                except ValueError:
                    print("\n✗ Invalid Order ID\n")

            elif choice == "3":
                print("\nGenerating 10 keys...\n")
                for i in range(10):
                    key = generate_license_key(f"{i+1:02d}")
                    print(f"{i+1:2d}. {key}")
                print()

            elif choice == "4":
                print("\nGoodbye!")
                break

            else:
                print("\n✗ Invalid choice\n")


if __name__ == "__main__":
    main()
