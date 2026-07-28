# PandaSuite Shared API Configuration - Implementation Guide

**Version:** 1.0  
**Date:** 2026-07-27  
**For:** Panda Print, Panda Profit, and future PandaSuite apps

---

## Overview

All PandaSuite applications share eBay API credentials and OAuth tokens via a centralized configuration in Windows `%appdata%`. Each app maintains its own license key (not shared).

### Directory Structure

```
C:\Users\tom\AppData\Roaming\PandaSuite\
├── ebay/                           # eBay platform (shared by ALL apps)
│   ├── config.json                 # app_id, dev_id, cert_id
│   └── tokens.json                 # access_token, refresh_token, expires_at
├── amazon/                         # (future platform)
│   ├── config.json
│   └── tokens.json
├── etsy/                           # (future platform)
│   ├── config.json
│   └── tokens.json
├── relist-agent/                   # (app-specific license)
│   └── license.json
├── panda-print/                    # (app-specific license)
│   └── license.json
└── panda-profit/                   # (app-specific license)
    └── license.json
```

---

## Key Principle

- **Platform folders** (ebay/, amazon/, etc.) = **SHARED** across all apps
- **App folders** (relist-agent/, panda-print/, etc.) = **App-specific** (license only)
- **Each app can read** platform credentials but **only writes** to its own license folder

---

## Implementation Steps

### Step 1: Copy Shared Module

Copy `panda_suite_api.py` into your app's root directory:

```bash
# For Panda Print
cp shared-api-config/panda_suite_api.py panda-print-show-mode/

# For Panda Profit
cp shared-api-config/panda_suite_api.py panda-profit/
```

### Step 2: Update Auth Module

Update your app's auth/config loading code to use PandaSuite paths.

#### Example: Panda Print (Custom Auth)

If Panda Print has custom auth:

```python
from pathlib import Path
import os
import json

# Use PandaSuite for eBay credentials
PANDA_SUITE_PATH = Path(os.environ['APPDATA']) / 'PandaSuite' / 'ebay'
PANDA_SUITE_PATH.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = PANDA_SUITE_PATH / "config.json"
TOKEN_FILE = PANDA_SUITE_PATH / "tokens.json"

def load_ebay_config():
    """Load eBay API config from PandaSuite"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"eBay config not found. Run setup first.")
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_ebay_tokens():
    """Load eBay OAuth tokens from PandaSuite"""
    if not TOKEN_FILE.exists():
        return {}
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_ebay_tokens(tokens):
    """Save eBay OAuth tokens to PandaSuite"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
```

### Step 3: Integrate panda_suite_api Module

In your main app file:

```python
from panda_suite_api import PandaSuiteAPI

# Initialize
suite = PandaSuiteAPI()

# On app startup
if suite.platform_configured('ebay'):
    # Load existing credentials
    config = suite.load_config('ebay')
    token = suite.get_access_token('ebay')  # Auto-refreshes if expired
else:
    # First time setup - run OAuth flow
    run_ebay_setup_flow()
    # After getting tokens:
    suite.save_config('ebay', config)
    suite.save_tokens('ebay', tokens)
```

### Step 4: Handle App License (App-Specific)

License keys stay **app-specific** (not shared):

```python
from panda_suite_api import PandaSuiteAPI
from pathlib import Path
import os
import json

suite = PandaSuiteAPI()

# Get app-specific license path
LICENSE_PATH = Path(os.environ['APPDATA']) / 'PandaSuite' / 'panda-print'  # Use app name
LICENSE_PATH.mkdir(parents=True, exist_ok=True)
LICENSE_FILE = LICENSE_PATH / 'license.json'

def load_license():
    """Load app-specific license"""
    if not LICENSE_FILE.exists():
        return None
    with open(LICENSE_FILE) as f:
        return json.load(f)

def save_license(license_data):
    """Save app-specific license"""
    with open(LICENSE_FILE, 'w') as f:
        json.dump(license_data, f, indent=2)

# License validation includes APP_ID
def validate_license():
    lic = load_license()
    if not lic:
        raise RuntimeError("License not found. Run setup.")
    
    # Check APP_ID matches
    if lic.get('app_id') != APP_ID:
        raise RuntimeError("License registered for different app. Invalid.")
    
    # Check key validity with server
    verify_with_server(lic['key'])
    return True
```

### Step 5: Installer Configuration (MSI)

Update your MSI installer to:

1. **Skip local credential storage** during install
2. **Point to %appdata%\PandaSuite** for credentials
3. **Create app-specific folder** (panda-print/, panda-profit/) for license

Example in installer:
```ini
; PandaSuite paths
PandaSuitePath = %appdata%\PandaSuite
PlatformPath = %appdata%\PandaSuite\ebay
AppLicensePath = %appdata%\PandaSuite\[APP_NAME]
```

### Step 6: First-Run Setup Flow

When app launches:

```python
from panda_suite_api import PandaSuiteAPI

suite = PandaSuiteAPI()
APP_ID = "panda-print"  # or "panda-profit"

# Check if eBay is configured
if not suite.platform_configured('ebay'):
    print("First-time setup required...")
    
    # Option A: User already set up via another app
    if input("Do you have eBay API credentials? (y/n): ").lower() == 'y':
        # Prompt for setup
        app_id = input("Enter app_id: ")
        dev_id = input("Enter dev_id: ")
        cert_id = input("Enter cert_id: ")
        
        config = {
            'app_id': app_id,
            'dev_id': dev_id,
            'cert_id': cert_id
        }
        suite.save_config('ebay', config)
        
        # Run OAuth flow
        tokens = run_oauth_flow(config)
        suite.save_tokens('ebay', tokens)

# Check license
lic = load_license()
if not lic:
    print("License setup required...")
    license_key = input("Enter license key: ")
    verify_license_with_server(license_key, APP_ID)
    save_license({
        'key': license_key,
        'app_id': APP_ID,
        'registered_date': datetime.now().isoformat()
    })
```

---

## File Formats

### config.json (Shared eBay Credentials)

```json
{
  "app_id": "YOUR_eBay_APP_ID",
  "dev_id": "YOUR_eBay_DEV_ID",
  "cert_id": "YOUR_eBay_CERT_ID"
}
```

### tokens.json (Shared OAuth Tokens)

```json
{
  "access_token": "v^1.1#i^1#r^0#p^3#f^0#I^3#t^H4sIAAAAAAAA/+1Ze2w...",
  "refresh_token": "v^1.1#i^1#f^0#I^3#r^1#p^3#t^Ul4xMF85OjgyN0QzMDU3...",
  "expires_at": "2026-08-27T12:34:56.000000+00:00"
}
```

### license.json (App-Specific License)

```json
{
  "key": "XXXXX-XXXXX-XXXXX-XXXXX",
  "app_id": "panda-print",
  "registered_date": "2026-07-27T10:00:00",
  "customer_name": "Your Store Name"
}
```

---

## Important Notes

### Token Refresh (Automatic)

```python
# This automatically refreshes if token is expired
token = suite.get_access_token('ebay')

# Token is valid and ready to use
# If it was refreshed, it's automatically saved to tokens.json
```

### License Isolation

- **Relist Agent license** in `%appdata%\PandaSuite\relist-agent\license.json`
- **Panda Print license** in `%appdata%\PandaSuite\panda-print\license.json`
- **Panda Profit license** in `%appdata%\PandaSuite\panda-profit\license.json`
- App ID check ensures key can't be used across apps

### Backward Compatibility

For existing apps (Relist Agent):
- App checks local config first
- If found, migrates to PandaSuite on first run
- Existing users don't lose credentials

---

## Testing Checklist

- [ ] App starts, finds eBay credentials in PandaSuite
- [ ] Token is loaded and valid
- [ ] App-specific license loads from app folder
- [ ] License validation includes APP_ID check
- [ ] Token auto-refresh works (expires_at check)
- [ ] New app can use same eBay credentials (run 2nd app, check)
- [ ] License from App A fails when used in App B
- [ ] Installer creates PandaSuite folder structure
- [ ] Uninstall doesn't delete shared credentials

---

## Troubleshooting

**"eBay config not found"**
- First app needs to run setup: `python app.py --setup`
- Or manually create: `C:\Users\tom\AppData\Roaming\PandaSuite\ebay\config.json`

**"License registered for different app"**
- License key is app-specific
- Each app needs its own license key
- Contact support for key reassignment

**"Token refresh failed"**
- Credentials may be invalid
- Re-run setup: `python app.py --setup`
- Or delete tokens.json and let app refresh

**Second app can't find eBay creds**
- Verify first app saved to PandaSuite correctly
- Check: `C:\Users\tom\AppData\Roaming\PandaSuite\ebay\`
- Both config.json and tokens.json should exist

---

## Migration from Local Config

If moving from app-local config to PandaSuite:

```python
# Old way
LOCAL_CONFIG = Path(__file__).parent / "config.json"

# New way
SHARED_CONFIG = Path(os.environ['APPDATA']) / 'PandaSuite' / 'ebay' / 'config.json'

# Migration code
if LOCAL_CONFIG.exists() and not SHARED_CONFIG.exists():
    # Copy local config to shared location
    shutil.copy(LOCAL_CONFIG, SHARED_CONFIG)
    print(f"Migrated config to {SHARED_CONFIG}")
```

---

## References

- `panda_suite_api.py` — Main module (in each app folder)
- `README.md` — Quick start guide
- Location: `C:\Users\tom\agents\shared-api-config\`

---

## Questions?

Refer to existing implementations:
- **Relist Agent** — `auth.py` (updated to use PandaSuite)
- **Sales Analyzer** — `sales_analyzer.py` (uses panda_suite_api)

