# WiX Installer Templates for PandaSuite Apps

**Ready-to-use templates for Relist Agent, Panda Print, and Panda Profit**

---

## What You Have

Three complete WiX installer templates (`.wxs` files):

| File | App | Purpose |
|------|-----|---------|
| `RELIST_AGENT_PRODUCT.wxs` | Relist Agent v2.0.1 | eBay automation |
| `PANDA_PRINT_PRODUCT.wxs` | Panda Print v1.0.0 | Print management |
| `PANDA_PROFIT_PRODUCT.wxs` | Panda Profit v1.0.0 | Analytics + SQLite DB |

---

## Quick Start

### 1. Create Project Folder

```bash
mkdir C:\MyProjects\Relist-Agent-Installer
cd C:\MyProjects\Relist-Agent-Installer

# Create subdirectories
mkdir Source
mkdir Installer
mkdir Output
```

### 2. Copy Files

```bash
# Copy app executable and dependencies to Source/
cp C:\Users\tom\agents\ebay-master\ebay-relist-agent\*.exe Source\
cp C:\Users\tom\agents\ebay-master\ebay-relist-agent\*.py Source\
cp C:\Users\tom\agents\ebay-master\ebay-relist-agent\Relist Agent.ico Source\
# ... copy all required files
```

### 3. Copy Template

```bash
cp RELIST_AGENT_PRODUCT.wxs Installer\Product.wxs
```

### 4. Edit Template (if needed)

**Key GUIDs to update:**
- ProductCode (generate new GUID)
- UpgradeCode (same across versions)
- Component GUIDs (generate new GUIDs)

**Command to generate GUID:**
```powershell
[guid]::NewGuid()
```

### 5. Build MSI

**Option A: Command Line**
```bash
cd Installer
candle.exe Product.wxs -o obj\ -dSourceDir=..\Source
light.exe obj\Product.wixobj -o ..\Output\Relist-Agent-v2.0.1.msi
```

**Option B: Visual Studio**
```bash
# Create Visual Studio project, add Product.wxs, Build
```

**Option C: WiX Studio**
```bash
# Open Product.wxs in WiX Studio, click Build
```

### 6. Test MSI

```bash
msiexec /i Output\Relist-Agent-v2.0.1.msi
```

**Verify:**
- Desktop shortcut created ✓
- `C:\Program Files\PandaSuite\Relist Agent\` populated ✓
- Start Menu shortcut created ✓
- Registry entries added ✓

---

## Customization per App

### App Name
```xml
<!-- Old -->
<Product Name="Relist Agent" ...>

<!-- New (for Panda Print) -->
<Product Name="Panda Print" ...>
```

### Version
```xml
<!-- For Panda Print v1.0.0 -->
Version="1.0.0.0"

<!-- For future Panda Print v1.0.1 -->
Version="1.0.1.0"
```

### Executable Name
```xml
<!-- Relist Agent -->
<File Source="$(var.SourceDir)\Relist Agent.exe" />

<!-- Panda Print -->
<File Source="$(var.SourceDir)\Panda Print.exe" />
```

### Icon File
```xml
<!-- Relist Agent -->
<File Source="$(var.SourceDir)\Relist Agent.ico" />

<!-- Panda Print -->
<File Source="$(var.SourceDir)\Panda Print.ico" />
```

### Install Path
```xml
<!-- Relist Agent -->
<Directory Id="APPFOLDER" Name="Relist Agent" />

<!-- Panda Print -->
<Directory Id="APPFOLDER" Name="Panda Print" />
```

### Registry Paths
```xml
<!-- Relist Agent -->
<RegistryKey Root="HKLM" Key="Software\The Trashed Panda\Relist Agent" ...>

<!-- Panda Print -->
<RegistryKey Root="HKLM" Key="Software\The Trashed Panda\Panda Print" ...>
```

### GUIDs (IMPORTANT)

**Generate new GUIDs for each app/version:**

```powershell
# Generate 3 GUIDs for each app
[guid]::NewGuid()  # ProductCode (unique per version)
[guid]::NewGuid()  # UpgradeCode (same across versions)
[guid]::NewGuid()  # Component GUID
[guid]::NewGuid()  # Component GUID
[guid]::NewGuid()  # Component GUID
```

**Update in template:**
```xml
<Product Id="*" UpgradeCode="UNIQUE-GUID-HERE-1234">
  ...
  <Component Id="MainExecutable" Guid="UNIQUE-GUID-HERE-5678">
  <Component Id="DesktopShortcut" Guid="UNIQUE-GUID-HERE-9999">
```

---

## Special: Panda Profit with SQLite

Panda Profit uses SQLite database stored in `%appdata%\PandaSuite\panda-profit\database.db`.

**The template includes:**
```xml
<RegistryValue Type="string" Name="DatabasePath" 
  Value="%appdata%\PandaSuite\panda-profit\database.db" />
```

**Note:** SQLite database is NOT included in installer. App creates it on first run:
```python
DB_PATH = Path(os.environ['APPDATA']) / 'PandaSuite' / 'panda-profit' / 'database.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
# App creates database here
```

---

## Required Source Files

### Relist Agent
```
Source/
├── Relist Agent.exe          (compiled from py via PyInstaller)
├── Relist Agent.ico          (app icon)
├── config.json               (template config)
├── auth.py
├── ebay_api.py
├── panda_suite_api.py
├── [other dependencies]
└── [all required files]
```

### Panda Print
```
Source/
├── Panda Print.exe
├── Panda Print.ico
├── config.json
├── panda_suite_api.py
├── [other dependencies]
└── [all required files]
```

### Panda Profit
```
Source/
├── Panda Profit.exe
├── Panda Profit.ico
├── config.json
├── panda_suite_api.py
├── [other dependencies]
└── [all required files]
```

---

## Common Issues & Fixes

### "Unable to find Source files"
- Verify `Source/` folder has all files
- Check relative paths in .wxs file
- Use absolute path if needed: `C:\full\path\to\source\file.exe`

### "ProductCode already exists"
- ProductCode must be unique per VERSION
- Generate new GUID for each release
- Example:
  - v1.0.0 → ProductCode=AAAA...
  - v1.0.1 → ProductCode=BBBB... (different)

### "Icon not found"
- Verify `.ico` file exists in `Source/`
- Use correct filename in template
- Icon must be in `SourceFile` attribute

### MSI won't install
- Check Windows Event Viewer for error
- Run: `msiexec /i installer.msi /l*v install.log`
- Review log for specific error

---

## Build Process

### Before Building
- [ ] All source files copied to `Source/`
- [ ] `.wxs` template copied to `Installer/`
- [ ] Template customized for your app
- [ ] GUIDs generated and updated
- [ ] File paths verified

### Building
- [ ] Run WiX compiler (candle.exe)
- [ ] Run WiX linker (light.exe)
- [ ] MSI generated in `Output/`

### After Building
- [ ] Test install on clean Windows
- [ ] Verify shortcuts created
- [ ] Verify program files installed
- [ ] Verify registry entries
- [ ] Test uninstall
- [ ] Verify uninstall cleanup

---

## Releasing

Once MSI is built and tested:

1. **Name:** `[App]-v[VERSION].msi`
   - Example: `Relist-Agent-v2.0.1.msi`

2. **Upload to website**
   - Folder: `https://thetrashedpanda.com/downloads/`
   - File: `Relist-Agent-v2.0.1.msi`

3. **Update version checker**
   - File: `LATEST_VERSION.txt`
   - Upload to: `https://thetrashedpanda.com/updates/ebay/`

4. **Create release notes**
   - File: `RELEASE-NOTES-v2.0.1.txt`
   - Upload to: `https://thetrashedpanda.com/updates/ebay/`

---

## Support Files

Also provided in this directory:

- `MSI_BUILD_GUIDE.md` — Detailed step-by-step build instructions
- `MSI_INSTALLER_CONFIG.md` — Configuration options and customization
- `INSTALL_INSTRUCTIONS.md` — End-user installation guide

---

## Questions?

Refer to:
- WiX Documentation: https://wixtoolset.org/docs/
- MSI_BUILD_GUIDE.md (in this directory)
- Template comments (in .wxs files)

