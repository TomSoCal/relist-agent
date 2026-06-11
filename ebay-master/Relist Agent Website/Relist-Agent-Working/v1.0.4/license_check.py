"""
License Key Validation for Relist Agent
"""

import json
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, messagebox


CONFIG_FILE = Path(__file__).parent / "config.json"
LICENSE_DB = Path(__file__).parent / "licenses.json"


def load_license_db():
    """Load the license database"""
    if LICENSE_DB.exists():
        with open(LICENSE_DB, "r") as f:
            return json.load(f)
    return {}


def validate_license_key(key):
    """
    Validate a license key

    Returns:
        (is_valid, message, customer_name)
    """
    licenses = load_license_db()

    if key not in licenses:
        return False, "License key not found", None

    info = licenses[key]
    status = info.get("status", "unknown")
    customer = info.get("customer_name", "User")

    if status == "active":
        return True, f"License valid for {customer}", customer
    elif status == "unused":
        return False, "License exists but not activated in system. Contact support.", customer
    else:
        return False, "License inactive or expired", customer


def prompt_for_license():
    """
    Show dialog asking user to enter license key

    Returns:
        License key or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()

    key = simpledialog.askstring(
        "License Required",
        "Enter your license key:\n\n(Format: RELIST-XXXX-XXXX-XXXX-XXXX)",
        show=None
    )

    root.destroy()
    return key


def check_license_on_startup():
    """
    Check if app has a valid license. If not, prompt for one.

    Returns:
        True if valid license exists, False if user cancelled
    """
    # Load config
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

    license_key = config.get("license_key")

    # If no license stored, ask for one
    if not license_key:
        root = tk.Tk()
        root.withdraw()

        result = messagebox.showinfo(
            "License Required",
            "Relist Agent requires a license key to run.\n\n"
            "If you don't have a license key, please purchase one at:\n"
            "https://www.thetrashedpanda.com/relist-agent\n\n"
            "Click OK to enter your license key."
        )

        root.destroy()

        # Prompt for key
        key = prompt_for_license()
        if not key:
            return False

        license_key = key

    # Validate the license
    is_valid, message, customer = validate_license_key(license_key)

    if not is_valid:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Invalid License", message)
        root.destroy()
        return False

    # License is valid - save it to config
    config["license_key"] = license_key
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    return True


def show_license_info():
    """Display current license information"""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

    license_key = config.get("license_key")

    if not license_key:
        info = "No license installed"
    else:
        is_valid, message, customer = validate_license_key(license_key)
        info = f"License: {license_key}\n\nStatus: {message}"

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("License Information", info)
    root.destroy()
