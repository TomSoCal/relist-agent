# MSI Installer Build Guide

**A PandaSuite Application by The Trashed Panda**

---

## Step-by-Step: Build MSI Installers

Complete guide to build `.msi` files for Relist Agent, Panda Print, and Panda Profit.

---

## Prerequisites

### Software Required
1. **WiX Toolset 3.11+** (Free)
   - Download: https://github.com/wixtoolset/wix3/releases
   - Or use WiX v4 (newer)

2. **Visual Studio 2019+** (Community edition is free)
   - Required for WiX project support
   - Or use **WiX Studio** (standalone, free)

3. **.NET Framework 3.5+**
   - Usually included with Windows
   - Required by WiX

### Files You'll Have
- App executable: `[App Name].exe`
- App icon: `[App Name].ico`
- Support files (DLLs, config files, etc.)
- WiX project template: `Product.wxs` (provided below)

---

## Setup: Visual Studio + WiX

### Option 1: Visual Studio with WiX Extension

1. **Install Visual Studio 2019+ Community Edition**
   - Download: https://visualstudio.microsoft.com/downloads/
   - Select: Desktop development with C++

2. **Install WiX Toolset**
   - Download: https://github.com/wixtoolset/wix3/releases
   - Run: `wix311.exe` (or latest version)

3. **Install WiX Visual Studio Extension**
   - In Visual Studio: Extensions → Manage Extensions
   - Search: "WiX"
   - Install: WiX Toolset (by WiX Project)

### Option 2: WiX Studio (Standalone, Easier)

1. **Download WiX Studio**
   - https://github.com/wixtoolset/wix/releases
   - Latest version (v4+)

2. **Install WiX Studio**
   - Run installer
   - No VS required
   - Graphical UI for building MSI

---

## Project Structure

Create folder for each app:

```
C:\MyProjects\Relist-Agent-Installer\
├── Source\
│   ├── Relist Agent.exe
│   ├── Relist Agent.ico
│   ├── config.json (template)
│   ├── auth.py
│   ├── ebay_api.py
│   ├── ... (other files)
├── Installer\
│   ├── Product.wxs (main installer config)
│   ├── Banner.bmp (optional)
│   ├── Dialog.bmp (optional)
└── Output\
    └── Relist-Agent-v2.0.1.msi (generated)
```

---

## Build Steps

### Step 1: Prepare Source Files

Copy all app files to `Source/` folder:
- Executable (.exe)
- DLLs and dependencies
- Config files
- Icon file
- Documentation

### Step 2: Create WiX Project

Create file: `Installer/Product.wxs`

Use template below (customize for your app).

### Step 3: Configure Installer Settings

Edit `Product.wxs`:
- Set version: `Version="2.0.1.0"`
- Set app name: `ProductName="Relist Agent"`
- Set manufacturer: `Manufacturer="The Trashed Panda"`
- Set install path: `ProgramFilesFolder`

### Step 4: Build MSI

**Via Command Line:**
```bash
cd Installer
candle.exe Product.wxs -o obj\
light.exe obj\Product.wixobj -o output\Relist-Agent-v2.0.1.msi
```

**Via Visual Studio:**
1. Open `.wixproj` file
2. Right-click → Build
3. MSI appears in `bin\Release\`

**Via WiX Studio:**
1. Open `.wxs` file
2. Click "Build"
3. MSI appears in output folder

### Step 5: Test MSI

```bash
# Install
msiexec /i Relist-Agent-v2.0.1.msi

# Uninstall
msiexec /x Relist-Agent-v2.0.1.msi

# Verify:
# - Desktop shortcut created
# - Program Files folder contains files
# - Start Menu folder created
# - %appdata%\PandaSuite folder created (on first app run)
```

---

## WiX Template: Product.wxs

See `RELIST_AGENT_PRODUCT.wxs` (below) for complete template.

**Key customizations per app:**

| Setting | Relist Agent | Panda Print | Panda Profit |
|---------|--------------|-------------|--------------|
| ProductName | Relist Agent | Panda Print | Panda Profit |
| Version | 2.0.1.0 | 1.0.0.0 | 1.0.0.0 |
| ProductCode | {unique-guid} | {unique-guid} | {unique-guid} |
| UpgradeCode | {unique-guid} | {unique-guid} | {unique-guid} |
| Icon | relist-agent.ico | panda-print.ico | panda-profit.ico |
| Exe Name | Relist Agent.exe | Panda Print.exe | Panda Profit.exe |
| Install Folder | PandaSuite\Relist Agent | PandaSuite\Panda Print | PandaSuite\Panda Profit |

---

## Generate GUIDs

Each installer needs **unique GUIDs**:

```powershell
# In PowerShell:
[guid]::NewGuid()
```

Or use online generator: https://www.guidgenerator.com/

You need:
- ProductCode (unique per version)
- UpgradeCode (same for all versions of same product)

---

## Build Output

When build succeeds:
```
✓ Relist-Agent-v2.0.1.msi (44 MB, example size)
```

Test by:
1. Running on clean Windows machine
2. Verifying all files install
3. Checking desktop shortcut
4. Verifying %appdata%\PandaSuite created on first run
5. Testing uninstall

---

## Signing MSI (Optional but Recommended)

Professional installers are code-signed.

```bash
signtool sign /f certificate.pfx /p password Relist-Agent-v2.0.1.msi
```

---

## Troubleshooting

### "candle.exe not found"
- Add WiX to PATH: `C:\Program Files (x86)\WiX Toolset v3.11\bin`
- Or use full path: `"C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe"`

### "Product code already exists"
- ProductCode must be unique per version
- Generate new GUID for each release

### "Icon file not found"
- Verify icon path in .wxs file
- Icon should be in Source/ folder
- Path should be relative or absolute

### MSI won't install
- Check Windows Event Viewer for error details
- Try: `msiexec /i installer.msi /l*v install.log`
- Review log file for specific error

---

## Distribution

Once MSI is built:

1. **Name format:** `[App]-v[VERSION].msi`
   - Example: `Relist-Agent-v2.0.1.msi`

2. **Host on website**
   - Upload to: `https://thetrashedpanda.com/downloads/`
   - Include version in filename

3. **Create release notes**
   - File: `RELEASE-NOTES-v2.0.1.txt`
   - Upload alongside MSI

4. **Update version checker**
   - File: `LATEST_VERSION.txt`
   - Content: `2.0.1`
   - Upload to: `%appdata%\PandaSuite\updates/`

---

## Release Checklist

Before releasing MSI:

- [ ] All source files in Source/ folder
- [ ] .wxs file configured for app (ProductName, Version, Icon, etc.)
- [ ] WiX project builds without errors
- [ ] MSI generated successfully
- [ ] Test install on clean Windows
- [ ] Desktop shortcut created
- [ ] Program Files folder populated
- [ ] Uninstall removes files (preserves PandaSuite folder)
- [ ] First app run creates %appdata%\PandaSuite
- [ ] License key setup works
- [ ] Version checker updated (LATEST_VERSION.txt)
- [ ] Release notes created
- [ ] MSI uploaded to website
- [ ] Download link tested

---

## Next Steps

1. Get the `RELIST_AGENT_PRODUCT.wxs` template (below)
2. Create project folder structure
3. Copy app files
4. Edit WiX file for your app
5. Build MSI
6. Test thoroughly
7. Release

---

## Questions?

Refer to:
- **WiX Documentation:** https://wixtoolset.org/docs/
- **WiX Studio Docs:** https://wixtoolset.org/docs/wix3/
- **Common Tasks:** See examples in `RELIST_AGENT_PRODUCT.wxs`

