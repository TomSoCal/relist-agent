# PandaSuite Shared Configuration & App Standards

**Master reference for all PandaSuite app developers**

## 🚀 START HERE

New app? **[Read APP_STANDARDS.md](APP_STANDARDS.md)** — Master checklist for licensing, MSI installer, app creation, and release.

Existing app? Jump to your task:
- **Building an installer?** → [MSI_BUILD_GUIDE.md](MSI_BUILD_GUIDE.md)
- **Adding licensing?** → [LICENSING_SYSTEM.md](LICENSING_SYSTEM.md)
- **Using API credentials?** → Keep reading (below) or see [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **Releasing a new version?** → [VERSION_SYNC_CHECKLIST.md](VERSION_SYNC_CHECKLIST.md)
- **End-user help?** → [INSTALL_INSTRUCTIONS.md](INSTALL_INSTRUCTIONS.md)

---

## Centralized API Credential Management

Centralized API credential management for all PandaSuite applications.

## Directory Structure

```
C:\Users\tom\AppData\Roaming\PandaSuite\
├── ebay/
│   ├── config.json          # app_id, dev_id, cert_id
│   └── tokens.json          # access_token, refresh_token, expires_at
├── amazon/                  # (future)
├── etsy/                     # (future)
└── platform-index.json      # (optional) metadata
```

## How Apps Use This

### 1. Import the module
```python
from panda_suite_api import PandaSuiteAPI

suite = PandaSuiteAPI()
```

### 2. Check if platform is configured
```python
if suite.platform_configured('ebay'):
    # Use existing credentials
    token = suite.get_access_token('ebay')
else:
    # Run setup flow
    setup_ebay_credentials()
```

### 3. Get access token (auto-refreshes if expired)
```python
token = suite.get_access_token('ebay')
# Token is valid and ready to use
```

### 4. Load config (app credentials)
```python
config = suite.load_config('ebay')
app_id = config['app_id']
dev_id = config['dev_id']
cert_id = config['cert_id']
```

### 5. Save new credentials (during setup)
```python
config = {
    'app_id': 'YOUR_APP_ID',
    'dev_id': 'YOUR_DEV_ID',
    'cert_id': 'YOUR_CERT_ID'
}
suite.save_config('ebay', config)

tokens = {
    'access_token': 'token_here',
    'refresh_token': 'refresh_here',
    'expires_at': '2026-08-27T12:00:00+00:00'
}
suite.save_tokens('ebay', tokens)
```

## eBay config.json Format
```json
{
  "app_id": "YOUR_APP_ID",
  "dev_id": "YOUR_DEV_ID",
  "cert_id": "YOUR_CERT_ID"
}
```

## eBay tokens.json Format
```json
{
  "access_token": "v^1.1#i^1#r^0#p^3#...",
  "refresh_token": "v^1.1#i^1#f^0#I^3#...",
  "expires_at": "2026-08-27T12:34:56.000000+00:00"
}
```

## Setup Flow for Apps

1. **App starts**
2. **Check:** `suite.platform_configured('ebay')`
3. **If no:**
   - Prompt user for eBay API setup
   - Get credentials from user
   - Call `suite.save_config('ebay', config)`
   - Handle OAuth flow, get tokens
   - Call `suite.save_tokens('ebay', tokens)`
4. **If yes:**
   - Get token: `suite.get_access_token('ebay')`
   - Use for all API calls
   - Token auto-refreshes when needed

## Location

- **Path:** `C:\Users\tom\AppData\Roaming\PandaSuite\`
- **Reason:** Standard Windows %appdata% location for installed apps
- **Roaming:** If user has roaming profiles, credentials follow them

## Benefits

✅ Setup once, use everywhere  
✅ Credentials shared across all apps  
✅ Token refresh happens centrally  
✅ Easy to add new platforms  
✅ Professional structure for distributed apps  

## Files in This Directory

- `panda_suite_api.py` — Main module (use in all apps)
- `README.md` — This file
- `setup_template.py` — Example setup flow (coming soon)
