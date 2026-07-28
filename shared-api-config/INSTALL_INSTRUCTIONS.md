# PandaSuite Application Installation Guide

**A PandaSuite Application by The Trashed Panda**

---

## What is PandaSuite?

PandaSuite is a suite of interconnected e-commerce automation applications. The key benefit: **Setup once, use everywhere.**

**Current Apps:**
- **Relist Agent** — eBay automation
- **Panda Print** — Print & label management
- **Panda Profit** — Analytics & reporting

**Future:** PandaSuite will expand to support multiple selling platforms (Amazon, Etsy, and more).

**Key Benefits:**
- Install 1 app, 2 apps, or all 3 apps
- **You only need to configure platform API credentials ONCE per selling platform**
  - Setup eBay credentials once → all eBay apps use them
  - Setup Amazon credentials once → all Amazon apps use them
  - Setup Etsy credentials once → all Etsy apps use them
- All apps automatically share platform credentials
- Streamlined, efficient, no duplication
- Scalable for future platforms

---

## Before You Install

### Requirements
- Windows 10 or later
- Selling platform account(s) with API credentials (eBay, Amazon, Etsy, etc.)
- Valid license key for each app (if purchased separately)

### You'll Need (One Time Setup)
- Platform API credentials (varies by platform)
  - **eBay:** App ID, Dev ID, Cert ID
  - **Amazon:** (credentials in future setup)
  - **Etsy:** (credentials in future setup)

---

## Installation Steps

### Step 1: Run the MSI Installer

```
Relist Agent v2.0.1 Setup.exe
OR
Panda Print v1.0.0 Setup.exe
OR
Panda Profit v1.0.0 Setup.exe
```

Click **Next** to proceed.

### Step 2: Accept Terms & Choose Install Location

- Default location: `C:\Program Files\PandaSuite\[App Name]\`
- App will automatically use shared credentials in `%appdata%\PandaSuite\`

### Step 3: Complete Installation

The app is installed. Next: **Initial Setup**

---

## First-Time Setup (One Time Only)

### First App You Install

When you launch the app for the first time:

```
┌─────────────────────────────────────┐
│  Setup Required                     │
│                                     │
│  eBay API Configuration             │
│  ─────────────────────────────       │
│  This is your first PandaSuite      │
│  app. Please enter your eBay        │
│  API credentials.                   │
│                                     │
│  [Next to Setup] [Skip for Later]   │
└─────────────────────────────────────┘
```

**Enter your credentials:**
- App ID: `[Your eBay App ID]`
- Dev ID: `[Your eBay Dev ID]`
- Cert ID: `[Your eBay Cert ID]`

The app will save these to:
```
C:\Users\[YourName]\AppData\Roaming\PandaSuite\ebay\
```

**This folder is now shared by all PandaSuite apps.**

### License Activation

```
┌─────────────────────────────────────┐
│  License Key                        │
│                                     │
│  Enter your license key to activate │
│  [App Name]                         │
│                                     │
│  License Key: [Enter here]          │
│                                     │
│  [Activate] [Trial Mode]            │
└─────────────────────────────────────┘
```

Enter your license key. Your license is specific to this app only.

---

## Installing a Second PandaSuite App

### You've Already Installed Relist Agent. Now Installing Panda Print?

**The app will automatically detect your existing eBay credentials.**

```
┌─────────────────────────────────────┐
│  Setup Complete!                    │
│                                     │
│  ✓ eBay credentials found           │
│    (Shared from Relist Agent)       │
│                                     │
│  Now activate your Panda Print      │
│  license:                           │
│                                     │
│  License Key: [Enter here]          │
│                                     │
│  [Activate] [Trial Mode]            │
└─────────────────────────────────────┘
```

**That's it!** No need to re-enter API credentials.

---

## Installing a Third App (Panda Profit)

Same process:

1. Run installer
2. App launches
3. Detects eBay credentials (shared)
4. Asks for license key (app-specific)
5. Ready to use

**No API setup required.**

---

## The Benefit: One Setup Per Platform, All Apps Use It

### Without PandaSuite
```
Install Relist Agent (eBay)     → Setup eBay credentials
Install Panda Print (eBay)      → Setup eBay credentials AGAIN
Install Panda Profit (eBay)     → Setup eBay credentials AGAIN
Future: Amazon Seller App       → Setup Amazon credentials
Total: 4 credential setups, wasted time
```

### With PandaSuite
```
Install Relist Agent (eBay)     → Setup eBay credentials (ONCE)
Install Panda Print (eBay)      → Credentials auto-detected ✓
Install Panda Profit (eBay)     → Credentials auto-detected ✓
Future: Amazon Seller App       → Setup Amazon credentials (ONCE)
All Amazon apps                 → Credentials auto-detected ✓
Total: 2 credential setups, streamlined
```

**Each platform's credentials are configured once, then shared by all apps using that platform.**

---

## Shared Credentials Folder

All apps use this folder for eBay API credentials:

```
C:\Users\[YourName]\AppData\Roaming\PandaSuite\ebay\
```

You can see it (if you enable showing hidden folders in Windows):
- `config.json` — Your eBay API credentials
- `tokens.json` — OAuth tokens (auto-refreshes)

**Do not edit these files manually.** Apps manage them automatically.

---

## License Keys (Per-App)

Each app has its own license folder:

```
C:\Users\[YourName]\AppData\Roaming\PandaSuite\
├── relist-agent/
│   └── license.json
├── panda-print/
│   └── license.json
└── panda-profit/
    └── license.json
```

**Important:** A license key for Relist Agent cannot be used to activate Panda Print. Each app requires its own license.

---

## Troubleshooting

### "Credentials not found" on second app install

**Solution:** Verify first app saved credentials:
1. Make sure first app completed setup successfully
2. Check: `C:\Users\[YourName]\AppData\Roaming\PandaSuite\ebay\`
3. Both `config.json` and `tokens.json` should exist
4. If not, run first app setup again

### "License key already used"

**This is expected.** If you enter a license key from another app:
```
Error: This license is registered for Relist Agent.
Cannot activate Panda Print with this key.

Please enter a Panda Print license key.
```

**Solution:** Use the license key for the correct app.

### "eBay API not working"

**Likely cause:** Credentials expired or incorrect.

**Solution:**
1. Right-click app → Run as Administrator
2. Look for setup/settings option
3. Re-enter eBay credentials
4. Credentials will auto-share with other apps

---

## Updating Apps

When you update an app (e.g., Relist Agent v2.0.0 → v2.0.1):

```
Run installer → Select "Upgrade"
```

**All credentials and settings are preserved.**

The PandaSuite shared folder is never removed during uninstall.

---

## Uninstalling Apps

### Uninstalling One App

```
Control Panel → Programs → Uninstall → Panda Print → Uninstall
```

**Your eBay credentials stay in PandaSuite** (other apps still need them).

### Uninstalling All PandaSuite Apps

After uninstalling the last app, you can manually delete:

```
C:\Users\[YourName]\AppData\Roaming\PandaSuite\
```

(This is optional - it doesn't hurt to leave it there.)

---

## What Gets Installed

### Program Files
```
C:\Program Files\PandaSuite\Relist Agent\
├── Relist Agent.exe
├── Supporting files
└── (Uninstallable via Control Panel)
```

### Shared Credentials (AppData)
```
C:\Users\[YourName]\AppData\Roaming\PandaSuite\
├── ebay/                 (Shared by all apps)
├── relist-agent/         (Specific to Relist Agent)
├── panda-print/          (Specific to Panda Print)
└── panda-profit/         (Specific to Panda Profit)
```

---

## Questions?

**"Why share API credentials but not licenses?"**
- API credentials are platform-level (eBay API)
- Licenses are app-level (Relist Agent, Panda Print, Panda Profit)
- This ensures you pay for each app but don't repeat setup

**"Can I use one Relist Agent license in Panda Print?"**
- No. Each app requires its own license
- This prevents key sharing between apps
- Each app has separate functionality

**"What if I uninstall an app?"**
- Your credentials stay (other apps may need them)
- Your license for that app is removed
- You can reinstall and reactivate anytime

---

## Summary

✅ **Install any PandaSuite app**  
✅ **Setup eBay credentials once** (first app only)  
✅ **Other apps auto-detect credentials**  
✅ **Each app needs its own license** (per-app)  
✅ **Streamlined, efficient, no duplication**  

**Powered by PandaSuite by The Trashed Panda**

