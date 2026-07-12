# Relist Agent — License Key System

## Overview

License keys are generated per customer and required to run the app. Each key is:
- **Unique** — One key per customer
- **One-time activation** — Stored in user's `config.json` after first entry
- **Offline validated** — No server required for ongoing checks

---

## Workflow: Purchase → Email → Activation

```
Customer Purchases
    ↓
You Generate License Key
    ↓
Email Key to Customer
    ↓
Customer Enters Key on First Run
    ↓
App Validates & Stores Key
    ↓
App Unlocked Forever
```

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

## Checklist Before Building EXE

- [ ] Review this guide
- [ ] Test license_generator.py locally
- [ ] Generate a test key
- [ ] Test entering key in app
- [ ] Verify key gets stored in config.json
- [ ] Make sure licenses.json is included in EXE bundle
- [ ] Document your license pricing

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
