# Relist Agent — License Key System (v2.0.0+)

## Overview

License keys are generated per customer and required to run the app. Each key is:
- **Unique** — One key per customer
- **App-specific** — Each app (Relist Agent, Panda Print, etc.) requires its own key
- **Computer-locked** — One key per computer; licenses cannot be shared across machines
- **Server-validated** — First activation registers key with server to prevent cross-app sharing
- **Offline capable** — After first activation, app works offline using cached validation

## ⚠️ IMPORTANT: App-Specific Licensing (New in v2.0.0)

Relist Agent now enforces **app-specific licensing**. This means:

1. **Each app gets its own APP_ID**
   - Relist Agent: `APP_ID = "relist-agent"`
   - Panda Print: `APP_ID = "panda-print"`
   - Future apps will have their own IDs

2. **Same key cannot be used in multiple apps**
   - If user tries to use a Panda Print key in Relist Agent → ERROR
   - If user tries to use a Relist Agent key in Panda Print → ERROR
   - Each app requires its own purchased license

3. **Multiple versions of same app CAN share licenses**
   - Relist Agent v2.0.0 and v2.1.0 both use `APP_ID = "relist-agent"`
   - Same key works in both versions on same computer
   - This is correct behavior (not a bug)

4. **Server enforces the restriction**
   - When key is registered, server records which app it belongs to
   - If different app tries to use the same key, server rejects with error
   - Error message shows: "This license is already registered to user '[store_name]' using the app [App Name]"

---

## Workflow: Purchase → Email → Activation

```
Customer Purchases
    ↓
You Generate License Key (format: RA-XX-XXXXXXXX-XXXXXXXX)
    ↓
Email Key to Customer
    ↓
Customer Runs App for First Time
    ↓
Customer Enters License Key
    ↓
App Prompts for eBay Store Name
    ↓
App Registers Key with Server (+ app ID + store name)
    ↓
Server Checks: Is this key already used by another app?
    ├─ YES → Server REJECTS with error message (app doesn't start)
    └─ NO → Server ACCEPTS, key is now locked to "relist-agent" on this computer
    ↓
App Stores Key in config.json
    ↓
App Unlocked (works offline after this)
```

## Technical Details: How Registration Works

### Initial Validation (First Launch)

1. User runs app → `check_license_on_startup()` is called
2. App loads the key from `config.json` (or prompts for it)
3. App connects to server: `register_key_on_server(license_key, computer_id, store_name)`
4. Server receives POST with:
   ```json
   {
       "api_key": "8RT39EA0IT4XCAXYRY0T9QDT1155P10I",
       "license_key": "RA-90-21E4F537-20C900F2",
       "computer": "MyComputer-Hostname",
       "app": "relist-agent",
       "customer_name": "MyStore"
   }
   ```
5. Server checks: Is this key already registered to a different app?
   - If YES: Return HTTP 400 with error message → app rejects and exits
   - If NO: Accept the registration → key is locked to "relist-agent" + "MyComputer"
6. App saves key to local `config.json`

### Subsequent Launches (Offline Mode)

1. App finds key in `config.json`
2. App loads license database (used_keys.json from server)
3. App validates locally: Is this key still associated with "relist-agent"?
4. App runs (even if server unreachable)

### Why Server-Side Validation Matters

Without server validation, users could:
1. Generate a new key in one app
2. Use the same key in a different app
3. No enforcement possible on client side

With server validation:
1. First registration "claims" the key for that app
2. Second app's registration attempt is rejected
3. User must purchase a separate key for the second app

### The Dual User-Agent Pattern (Cloudflare Bypass)

The server uses Cloudflare DDoS protection, which blocks automated POST requests.
To work around this:

- **GET requests** (read data): Use app-specific User-Agent
  ```python
  User-Agent: 'Relist-Agent/1.5.0'
  ```
  This proves we're a legitimate app client, not a bot

- **POST requests** (register key): Use Mozilla User-Agent
  ```python
  User-Agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
  ```
  This makes POST look like a browser request, bypassing Cloudflare

This dual approach allows:
- Secure app identity verification on GETs
- Cloudflare bypass on POST (registration)
- Enforcement of app-specific licensing

---

## Your Tasks (Step-by-Step)

### 1. Generate License Key

When a customer purchases, run:

```bash
python license_generator.py generate <email> "<customer_name>"
```

**Example:**
```bash
python license_generator.py generate john@example.com "John Doe"
```

**Output:**
```
✓ License generated successfully!

License Key: RELIST-A7K2-9M5Q-3TW8-7HX4
Email: john@example.com
Customer: John Doe

Ready to email to customer.
```

### 2. Email the Key to Customer

Use the **Email Template** below to send to customer.

### 3. Customer Enters Key

When they run the app:
1. First time → "License Required" dialog appears
2. They paste the key
3. App validates → Unlocked forever ✓

### 4. Track Your Licenses

**View all licenses:**
```bash
python license_generator.py list
```

**Output:**
```
================================================================================
LICENSE KEY INVENTORY
================================================================================
License Key              Email                          Status     Generated          
--------------------------------------------------------------------------------
RELIST-A7K2-9M5Q-3TW8-7HX4  john@example.com               unused     2026-06-04       
RELIST-B4L5-2K9T-8RX1-5QZ3  jane@example.com               active     2026-06-03       
...
Total: 2 | Unused: 1 | Active: 1
================================================================================
```

### 5. Validate a Key (if customer reports issues)

```bash
python license_generator.py validate RELIST-A7K2-9M5Q-3TW8-7HX4
```

---

## Email Template

**Copy and customize this for your emails:**

---

**Subject:** Your Relist Agent License Key

**Body:**

```
Hi [CUSTOMER_NAME],

Thank you for purchasing Relist Agent! 🎉

Your license key is:

    RELIST-A7K2-9M5Q-3TW8-7HX4

Installation & Activation:

1. Download Relist Agent (.exe for Windows or .dmg for Mac)
2. Run the installer
3. On first launch, you'll be prompted for a license key
4. Paste your key above → App unlocked!
5. Never need to enter it again

The license is tied to your account and installed on your machine.
One purchase = One machine. If you need to install on another computer, 
please let us know.

Support:
If you have any issues activating, email support@thetrashedpanda.com 
with your license key and I'll help you out.

Happy selling! 🚀

[YOUR NAME]
thetrashedpanda.com
```

---

## Technical Details (For Reference)

### How License Validation Works

1. **On App First Launch:**
   - App checks `config.json` for stored license key
   - If missing → Show dialog asking for key

2. **When User Enters Key:**
   - App reads `licenses.json` (local database)
   - Validates key exists in database
   - Stores key in `config.json` (never asks again)

3. **On Future Launches:**
   - App finds key in `config.json`
   - Silently loads → App runs

### Files Involved

- **`license_generator.py`** — Script for you to generate keys
- **`license_check.py`** — Library that validates keys in the app
- **`licenses.json`** — Database of all valid keys (keep this private!)
- **`config.json`** — User's personal config (includes their stored key)

---

## Security Notes

⚠️ **Keep `licenses.json` private!** 
- This file contains all valid keys
- Store it securely (don't commit to public GitHub)
- Include it in `.gitignore`

✓ **Each copy of the app has `licenses.json` baked in**
- When you distribute the EXE/DMG, include `licenses.json`
- Users can't modify it (it's read-only from app perspective)
- If you add new keys, users need a new version of the app OR you can host it online (advanced)

---

## Advanced: Updating Keys Without Releasing New Version

(Optional - only if you get comfortable with this)

Instead of embedding `licenses.json` in the app:
1. Host `licenses.json` on a simple server
2. App downloads it on startup (online validation)
3. New keys work immediately without app updates

For now, stick with embedded `licenses.json`.

---

## Troubleshooting

**Q: Customer lost their license key**
A: Check your license list output. Their email will be there. Re-send.

**Q: Customer trying to use same key on multiple machines**
A: That's a business policy decision. Currently, the app doesn't prevent it. 
You could:
- Use different keys per machine (generate multiple)
- Trust customers to follow your license agreement

**Q: Need to revoke a key?**
A: Currently, the app doesn't have a revocation system. You'd need to:
- Manually edit `licenses.json` (change status to "revoked")
- Distribute updated app

---

## For Developers: Key Files to Know

### License Validation Code
- **`license_check.py`** — Main licensing library
  - `APP_ID = "relist-agent"` — DO NOT CHANGE
  - `register_key_on_server()` — Registers key + validates app-specific enforcement
  - `validate_license_key()` — Checks if key is valid and belongs to this app
  - `check_license_on_startup()` — Entry point called on app start

### What NOT to Change
1. ❌ Never change `APP_ID` (it locks keys to this app)
2. ❌ Never remove the `"app"` field from registration payload
3. ❌ Never change the dual User-Agent pattern (GET = app-specific, POST = Mozilla)
4. ❌ Never allow offline use when error message contains "registered for" (app mismatch)

### What CAN Change
- ✅ The User-Agent version number (Relist-Agent/1.5.0 → Relist-Agent/2.0.0)
- ✅ The error message text (but keep "registered for" detection intact)
- ✅ The store name prompt (but keep it capturing the store name)
- ✅ Test cases and validation logic (but keep app-specific check)

### Testing the System
```python
# Test 1: Valid Relist Agent key
# Should: Accept registration

# Test 2: Use Panda Print key in Relist Agent
# Should: Get "registered for panda-print" error, app doesn't start

# Test 3: Same key used on second launch
# Should: Load from cache, work offline

# Test 4: Register key A, then try key B from different app
# Should: Reject key B with app mismatch error
```

## Checklist Before Building EXE

- [ ] Review this guide
- [ ] Verify APP_ID is set to "relist-agent" in license_check.py
- [ ] Verify registration payload includes "app" and "customer_name" fields
- [ ] Verify dual User-Agent pattern is implemented (GET + POST)
- [ ] Test with a key from Panda Print (should get rejected with app mismatch error)
- [ ] Test with a valid Relist Agent key (should register successfully)
- [ ] Verify error message shows customer store name
- [ ] Make sure server-side validation is working (thetrashedpanda.com responding)
- [ ] Build EXE with latest license_check.py
- [ ] Test EXE with both valid and invalid keys
- [ ] Document your license pricing
- [ ] Include licensing guide in user documentation

---

## Next Steps

1. **Test locally** with a generated key
2. **Build EXE/DMG** (includes licenses.json automatically)
3. **For each sale:**
   - Run: `python license_generator.py generate <email> "<name>"`
   - Copy key
   - Send via email using template above
   - Update your sales records
4. **Periodically check:** `python license_generator.py list`
