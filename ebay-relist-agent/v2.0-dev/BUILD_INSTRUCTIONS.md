# Building Relist Agent — Windows EXE & Mac DMG

## Prerequisites

### For Both Platforms:
```bash
# Install Python 3.11+
# Install PyInstaller
pip install pyinstaller

# Install dependencies
pip install -r requirements.txt
```

**Icon:** ERA_Icon.png (Relist Agent branding)

---

## Build for Windows (.EXE)

**Run on Windows PC:**

```bash
cd C:\Users\tom\agents\ebay-master\ebay-relist-agent

# Single-file executable with ERA icon
pyinstaller --windowed --onefile ^
  --name "Relist Agent" ^
  --icon ERA_Icon.png ^
  --hidden-import=tkinter ^
  --hidden-import=PIL ^
  --hidden-import=gspread ^
  --hidden-import=google ^
  --hidden-import=firecrawl ^
  --hidden-import=playwright ^
  gui_app.py
```

**Output:** `dist\Relist Agent.exe`

✓ **Already built and ready in:** `DISTRIBUTION/Relist Agent.exe`

### Optional: Create Windows Installer

Install NSIS (Nullsoft Scriptable Install System):
```bash
pip install pyinstaller-hooks-contrib
# Then use NSIS to wrap the .exe with an installer
```

---

## Build for Mac (.DMG)

**Run on Mac:**

```bash
cd /path/to/ebay-relist-agent

# Single-file app bundle with ERA icon
pyinstaller --windowed --onefile \
  --name "Relist Agent" \
  --icon ERA_Icon.png \
  --hidden-import=tkinter \
  --hidden-import=PIL \
  --hidden-import=gspread \
  --hidden-import=google \
  --hidden-import=firecrawl \
  --hidden-import=playwright \
  gui_app.py
```

**Output:** `dist/Relist Agent.app`

### Convert to DMG:

```bash
# Create DMG from app bundle
hdiutil create -volname "Relist Agent" \
  -srcfolder dist \
  -ov -format UDBZ \
  "Relist Agent.dmg"
```

---

## Automated Builds with GitHub Actions

**Option: Skip manual builds and use GitHub Actions for automatic cross-platform builds**

1. Push code to GitHub
2. GitHub Actions automatically builds on Windows and Mac runners
3. Download both `.exe` and `.dmg` from releases

See `GITHUB_ACTIONS_SETUP.md` for configuration.

---

## Build Settings Explained

| Flag | Purpose |
|------|---------|
| `--windowed` | No console window (GUI only) |
| `--onefile` | Single executable file (vs. folder with many files) |
| `--name "Relist Agent"` | Output filename |
| `--icon INFO_ICON.png` | Icon for the app |
| `--hidden-import=...` | Force include hidden imports |
| `gui_app.py` | Main entry point |

---

## Testing the Build

### Windows:
```bash
# Test the .exe
"dist\Relist Agent.exe"
```

### Mac:
```bash
# Test the .app
open "dist/Relist Agent.app"
```

---

## Troubleshooting

**"Missing module X" error:**
- Add `--hidden-import=X` to the build command

**App won't start:**
- Check that `config.json` exists (it should be created on first run)
- Try running from Command Prompt (Windows) or Terminal (Mac) to see error messages

**Size too large:**
- Windows: ~120-150 MB (normal for Python + dependencies)
- Mac: ~150-180 MB (normal, includes Python + dependencies)

**App crashes on startup:**
- Ensure all API credentials are valid in `config.json`
- Check system requirements (Windows 10+, Mac 10.14+)

---

## Distribution

1. **Windows:** Distribute `dist/Relist Agent.exe`
2. **Mac:** Distribute `Relist Agent.dmg`
3. **Optional:** Create a GitHub release with both files attached

---

## Next Steps

1. **Windows:** Run the Windows build command on your PC
2. **Mac:** Either:
   - Use a Mac to build (friend, MacStadium cloud, or VM)
   - Or use GitHub Actions for automated builds
3. Test both versions thoroughly before distributing

---

## Questions?

Refer to:
- PyInstaller docs: https://pyinstaller.org/
- GitHub Actions: https://github.com/features/actions
