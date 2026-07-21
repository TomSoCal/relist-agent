"""
License Key Validation for Relist Agent
Validates against remote used_keys.json on thetrashedpanda.com
Also validates checksum for auto-registration of new keys

IMPORTANT: Internet connection is required for license activation and validation.
- First launch: Connects to server to validate and register license key
- Subsequent launches: Validates cached license (works offline)
- App-specific enforcement: Requires server connection to prevent multi-app key sharing
"""

import json
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, messagebox
import urllib.request
import urllib.error
import hashlib
import os
import sys

# Get the correct directory (frozen EXE or script)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    BASE_DIR = Path(__file__).parent

CONFIG_FILE = BASE_DIR / "config.json"
# Store logs in hidden folder (not in root)
DATA_DIR = BASE_DIR / ".ebay_relist_agent_data"
DATA_DIR.mkdir(exist_ok=True)
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetFileAttributesW(str(DATA_DIR), 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
LOG_FILE = DATA_DIR / "license_debug.log"
LICENSE_DB_URL = "https://thetrashedpanda.com/license/used_keys.json"
LICENSE_UPDATE_URL = "https://thetrashedpanda.com/license/api/update-key.php"
LICENSE_API_KEY = "8RT39EA0IT4XCAXYRY0T9QDT1155P10I"
LICENSE_SECRET = 'relist-agent-secret'  # Must match keygen.py
APP_ID = "relist-agent"  # Unique identifier for this app

def log_debug(msg):
    """Write debug message to both console and file"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass


def load_license_db():
    """Load the license database from remote URL"""
    # Try Python urllib first
    try:
        req = urllib.request.Request(
            LICENSE_DB_URL,
            headers={
                'User-Agent': 'Relist-Agent/1.5.0',
                'Cache-Control': 'no-cache'
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            db = json.loads(data)
            log_debug(f"[LICENSE] Successfully loaded {len(db)} licenses from {LICENSE_DB_URL}")
            return db
    except urllib.error.HTTPError as e:
        log_debug(f"[LICENSE] HTTP Error {e.code} - Trying fallback method...")
    except Exception as e:
        log_debug(f"[LICENSE] urllib failed: {e} - Trying PowerShell fallback...")

    # Fallback: Use PowerShell (works on Windows)
    try:
        import subprocess
        ps_cmd = f'(Invoke-WebRequest -Uri "{LICENSE_DB_URL}" -UseBasicParsing).Content'
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            db = json.loads(result.stdout)
            log_debug(f"[LICENSE] Successfully loaded {len(db)} licenses (via PowerShell)")
            return db
        else:
            log_debug(f"[LICENSE] PowerShell error: {result.stderr}")
    except Exception as e:
        log_debug(f"[LICENSE] PowerShell fallback failed: {e}")

    return {}


def get_computer_identifier():
    """Get a unique identifier for this computer"""
    try:
        import socket
        return socket.gethostname()
    except:
        return "unknown"


def register_key_on_server(license_key, computer):
    """Register the license key + computer on the server to prevent sharing

    Returns: (success, error_message)
        success: True if registered, False otherwise
        error_message: None if success, error string if failed
    """
    try:
        log_debug(f"[LICENSE] APP_ID value: '{APP_ID}' (type: {type(APP_ID).__name__})")
        log_debug(f"[LICENSE] Registering key on server: {license_key[:20]}... on {computer} for app={APP_ID}")
        log_debug(f"[LICENSE] Endpoint: {LICENSE_UPDATE_URL}")
        log_debug(f"[LICENSE] API Key: {LICENSE_API_KEY[:10]}...")

        # Get customer name from config (eBay store name - should be set by check_license_on_startup)
        customer_name = "User"
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    store_name = config.get("store_name", "").strip()
                    customer_name = store_name if store_name else "User"
        except:
            pass

        log_debug(f"[LICENSE] Using customer_name: {customer_name}")

        payload = {
            "api_key": LICENSE_API_KEY,
            "license_key": license_key,
            "computer": computer,
            "app": APP_ID,
            "customer_name": customer_name
        }

        log_debug(f"[LICENSE] Keys in payload: {list(payload.keys())}")
        log_debug(f"[LICENSE] Payload: {json.dumps(payload)}")

        req = urllib.request.Request(
            LICENSE_UPDATE_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'close'
            }
        )

        log_debug(f"[LICENSE] Sending POST request...")
        response = urllib.request.urlopen(req, timeout=5)
        response_text = response.read().decode('utf-8')
        log_debug(f"[LICENSE] Response: {response_text}")

        result = json.loads(response_text)

        if result.get('success'):
            log_debug(f"[LICENSE] Key registered on server successfully")
            return True, None
        else:
            error_msg = result.get('error', 'Unknown error')
            log_debug(f"[LICENSE] Server registration failed: {error_msg}")
            return False, error_msg

    except urllib.error.HTTPError as e:
        error_response = e.read().decode('utf-8')
        log_debug(f"[LICENSE] HTTP Error {e.code}: {error_response}")
        try:
            err = json.loads(error_response)
            return False, err.get('error', f'HTTP {e.code}')
        except:
            return False, f'HTTP {e.code}'
    except Exception as e:
        log_debug(f"[LICENSE] Error registering key on server: {type(e).__name__}: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return False, str(e)


def validate_key_checksum(key):
    """
    Validate that a key has a valid checksum (was generated by keygen).
    Format: RA-XX-XXXXXXXX-XXXXXXXX

    Returns: True if checksum is valid, False otherwise
    """
    try:
        parts = key.split('-')
        if len(parts) != 4 or parts[0] != 'RA':
            return False

        order_id = parts[1]
        random_part = parts[2]
        provided_checksum = parts[3]

        # Recalculate checksum
        base_key = f"RA-{order_id}-{random_part}"
        checksum_input = base_key + LICENSE_SECRET
        calculated_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:8].upper()

        is_valid = calculated_checksum == provided_checksum
        log_debug(f"[LICENSE] Checksum validation: {is_valid} (calc: {calculated_checksum}, provided: {provided_checksum})")
        return is_valid
    except Exception as e:
        log_debug(f"[LICENSE] Checksum validation error: {e}")
        return False


def validate_license_key(key):
    """
    Validate a license key.

    1. First checks database (for registered keys)
    2. Then validates checksum (for auto-registration of generated keys)
    Only you have keygen, so valid checksums = legitimate keys

    Returns:
        (is_valid, message, customer_name)
    """
    licenses = load_license_db()

    # Check if key is in database
    if key in licenses:
        info = licenses[key]
        status = info.get("status", "unknown")
        customer = info.get("customer_name", "User")
        assigned_computer = info.get("computer", None)
        assigned_app = info.get("app", None)
        current_computer = get_computer_identifier()

        if status == "active":
            # Check if license is for a different app
            if assigned_app and assigned_app != APP_ID:
                return False, f"This license is registered for {assigned_app}. Each app requires its own license.", customer
            # Check if license is already in use on a different computer
            if assigned_computer and assigned_computer != current_computer:
                reset_msg = (
                    "This license is already in use on another computer.\n\n"
                    "If you are trying to use an old license on a new computer, "
                    "please email support@thetrashedpanda.com to reset your license.\n\n"
                    "You are allowed 1 license reset per purchase."
                )
                return False, reset_msg, customer
            # License is valid and available
            return True, f"License valid for {customer}", customer
        elif status == "unused":
            return False, "License exists but not activated in system. Contact support.", customer
        else:
            return False, "Please enter a valid license", customer

    # Key not in database - validate checksum for auto-registration
    # Since only you have keygen, valid checksum = legitimate key
    if validate_key_checksum(key):
        log_debug(f"[LICENSE] Valid generated key: {key}")
        return True, "License valid", "User"
    else:
        return False, "Please enter a valid license", None


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
    Check if app has a valid license by validating against remote server.
    Always fetches from server - no shortcuts.

    Returns:
        True if valid license exists, False if user cancelled
    """
    # FORCE WRITE - DEBUG v2.0.0
    try:
        with open("C:\\temp\\license_check_startup_v2.txt", "a") as f:
            f.write(f"check_license_on_startup CALLED from v2.0.0\n")
    except:
        pass

    # Clear old log and start fresh
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"[LICENSE] check_license_on_startup() CALLED\n")
    except:
        pass

    log_debug(f"[LICENSE] CONFIG_FILE: {CONFIG_FILE}")
    log_debug(f"[LICENSE] Config exists: {CONFIG_FILE.exists()}")

    # Load config
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        log_debug(f"[LICENSE] Config loaded successfully")

    license_key = config.get("license_key", "").strip()
    log_debug(f"[LICENSE] License key from config: {'[PRESENT]' if license_key else '[MISSING]'}")
    log_debug(f"[LICENSE] Key length: {len(license_key) if license_key else 0}")

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

    # ALWAYS validate against server - fetch fresh data each time
    log_debug(f"[LICENSE] Validating key: {license_key[:20]}...")
    is_valid, message, customer = validate_license_key(license_key)
    log_debug(f"[LICENSE] Validation result: is_valid={is_valid}, message={message}, customer={customer}")

    if not is_valid:
        log_debug(f"[LICENSE] Validation failed, showing error dialog")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Please enter a valid license", message)
        root.destroy()
        return False

    log_debug(f"[LICENSE] Validation passed!")

    # License is valid
    log_debug(f"[LICENSE] License validated successfully for {customer}")

    # Prompt for eBay store name
    store_name = config.get("store_name", "").strip()
    if not store_name:
        root = tk.Tk()
        root.withdraw()
        store_name = simpledialog.askstring(
            "eBay Store Name",
            "Enter your eBay store name:\n\n(This helps identify your account in our records)",
            parent=root
        )
        root.destroy()

        if not store_name:
            store_name = "User"
        else:
            store_name = store_name.strip()

    log_debug(f"[LICENSE] Store name: {store_name}")

    # Try to save it to config, but don't fail if save fails
    try:
        config["license_key"] = license_key
        config["store_name"] = store_name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        log_debug(f"[LICENSE] License and store name saved to config.json")
    except Exception as e:
        log_debug(f"[LICENSE] Warning: Could not save to config: {e}")
        # Don't return False - license is valid, just can't persist it

    # Register the key on the server (locks it to this computer)
    log_debug(f"[LICENSE] Attempting to register key on server...")
    computer_name = get_computer_identifier()
    success, error_msg = register_key_on_server(license_key, computer_name)

    if success:
        log_debug(f"[LICENSE] Key registered on server successfully")
    else:
        # Check if error is due to app mismatch
        if error_msg and "registered for" in error_msg.lower():
            log_debug(f"[LICENSE] REJECTION: {error_msg}")
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("License Error", error_msg)
            root.destroy()
            return False
        else:
            log_debug(f"[LICENSE] Warning: Could not register key on server (but license still valid locally)")

    return True


def get_license_key_from_config():
    """Get the stored license key from config.json"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("license_key")
    except:
        pass
    return None


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
