# Building Relist Agent as EXE

## Prerequisites
```bash
pip install pyinstaller pillow
```

Note: `pillow` is required for the logo display in the app. If not installed, the app will still work but the logo won't show.

## Build Command

Run this command in the agent directory:

```bash
pyinstaller --windowed --onefile --icon=ERA_Icon.png --name="Relist Agent" gui_app.py
```

## Options Explained
- `--windowed` - No console window (GUI only)
- `--onefile` - Single .exe file (not folder)
- `--icon=ERA_Icon.png` - Use the ERA icon for the .exe
- `--name="Relist Agent"` - Application name

## Output
The built `.exe` will be in `dist/` folder:
```
dist/Relist Agent.exe
```

## After Building
1. Copy `config.json` to the same folder as the .exe
2. Copy `ERA_Icon.png` and `ERA_Logo.png` to the same folder (for the app to use)
3. Double-click the .exe to run

## Creating Desktop Shortcut
Right-click `Relist Agent.exe` → Send To → Desktop (Create Shortcut)

## For Distribution
All required files in one folder:
```
Relist Agent.exe
config.json
ERA_Icon.png
ERA_Logo.png
```

User just needs to run the .exe. All settings/logs go to the same folder.
