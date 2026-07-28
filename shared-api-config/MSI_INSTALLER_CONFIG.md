# MSI Installer Configuration Guide

**A PandaSuite Application by The Trashed Panda**

---

## Desktop Shortcut Configuration

All PandaSuite apps should create a **desktop shortcut** during MSI installation.

### Shortcut Details

Each app gets:
- **Target:** `C:\Program Files\PandaSuite\[App Name]\[AppName].exe`
- **Icon:** App-specific icon (located in install folder)
- **Name:** `[App Name]` (e.g., "Relist Agent", "Panda Print", "Panda Profit")
- **Location:** User's Desktop

### WiX Installer Example

```xml
<!-- Desktop Shortcut -->
<Directory Id="DesktopFolder" Name="Desktop" />

<Feature Id="ProductFeature" Title="[ProductName]" Level="1">
  <ComponentRef Id="MainExecutable" />
  <ComponentRef Id="DesktopShortcut" />
</Feature>

<!-- Shortcut Component -->
<Component Id="DesktopShortcut" Directory="DesktopFolder">
  <Shortcut 
    Id="DesktopShortcut" 
    Name="[ProductName]"
    Target="[INSTALLFOLDER][AppName].exe"
    Icon="[AppIcon].ico"
    IconIndex="0" />
  <RemoveFolder Id="DesktopFolder" On="uninstall" />
  <RegistryValue 
    Root="HKCU" 
    Key="Software\[Manufacturer]\[ProductName]"
    Name="DesktopShortcut" 
    Value="1" 
    Type="integer" />
</Component>
```

### Visual Details

**Desktop Icon:**
- Relist Agent → Relist Agent icon
- Panda Print → Panda Print icon
- Panda Profit → Panda Profit icon

**Text below icon:** `[App Name]`

**Right-click properties:**
- Target: `C:\Program Files\PandaSuite\Relist Agent\Relist Agent.exe` (example)
- Start in: `C:\Program Files\PandaSuite\Relist Agent\`
- Run: Normal window

---

## Installation Flow

1. User downloads MSI installer
2. Runs installer
3. Installer copies files to: `C:\Program Files\PandaSuite\[App Name]\`
4. Creates desktop shortcut
5. Creates Start Menu shortcuts (optional)
6. Completes setup
7. Desktop shows new shortcut

---

## Uninstallation

When user uninstalls via Control Panel:
- ✓ Desktop shortcut is removed
- ✓ Program files are removed
- ✓ **PandaSuite shared folder is preserved** (other apps may need it)
- ✓ App-specific license folder removed
- ✓ App-specific registry entries removed

---

## Start Menu Shortcuts (Optional)

In addition to desktop shortcuts, consider adding to Start Menu:

```
Start Menu > PandaSuite > [App Name]
```

This creates an organized menu structure if multiple PandaSuite apps are installed.

---

## Installer Branding Elements

### File Associations (Optional)

Consider registering file types:
- Relist Agent: `.relist` files
- Panda Print: `.labels` files
- Panda Profit: `.report` files

### Context Menu (Optional)

Allow right-click from file explorer to open with app.

---

## Testing Checklist

- [ ] MSI installer creates desktop shortcut
- [ ] Shortcut launches app correctly
- [ ] Shortcut has correct icon (app-specific)
- [ ] Shortcut name is correct
- [ ] Uninstall removes desktop shortcut
- [ ] Uninstall preserves PandaSuite folder
- [ ] Multiple app installs each create their own shortcut

---

## Installer Information

**Installer Behavior:**
- Create desktop shortcut: **YES**
- Create Start Menu folder: **YES** (PandaSuite\[App Name])
- Create program files: **YES** (`C:\Program Files\PandaSuite\[App Name]\`)
- Create AppData folder: **NO** (created on first run)

**Tagline on Installer:**
"A PandaSuite Application by The Trashed Panda"

**Support Link:** (Optional) Include support/help links in installer

