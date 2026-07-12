# v1.0.4 Remaining Tasks

## Critical Features
- [ ] **Check for Updates Button** — Add to GUI (About section?). URL: Pending (user will provide website directory path)
  - Code exists: `update_checker.py` (ready to use)
  - Needs: Website directory URL from user, button in About section
  - Status: PENDING URL from user, then integration

- [x] **License Key System** — Restored and integrated
  - Code exists: `license_check.py`, `keygen.py`, `keygen_gui.py`
  - Format: RA-XX-XXXXXXXX-XXXXXXXX (validated via checksum)
  - Database: used_keys.json (remote at https://thetrashedpanda.com/license/)
  - Integration done:
    - [x] Call check_license_on_startup() in gui_app.py before main window
    - [x] Add license_key to config.json blank template
    - [x] Invalid license message: "Please enter a valid license"
    - [x] License reset instruction in error message (email support@)
    - [ ] Add "License Info" button to Settings/About (TODO)
    - [ ] Add FAQ entry: "License reset policy - 1 reset per purchase" (TODO)
  - Status: INTEGRATED, needs UI button + FAQ

- [ ] **Window Instance Limiting** — Max 1 of each window type
  - Prevent multiple Inventory windows
  - Prevent multiple Exclude windows
  - Other windows (Settings, About, etc) can only have 1 open
  - Error message when user tries to open duplicate
  - Status: NEEDS IMPLEMENTATION

- [ ] **Window Icons** — Use ERA_Icon.ico on all windows
  - Current: Only MainApp uses ERA_Icon.png (as .png)
  - Need: Change to ERA_Icon.ico, apply to:
    - [ ] MainApp (main window)
    - [ ] InventoryWindow
    - [ ] ExclusionsWindow
    - [ ] SettingsWindow
    - [ ] Any dialog/popup windows
  - Status: NEEDS IMPLEMENTATION

## Bug Fixes
- [ ] **Retry Relist** — Currently non-functional (can be removed if not critical)
  - Purpose: Re-run relisting on items that failed during previous run
  - Find code location in GUI / ebay_relist_agent.py
  - Debug/fix OR remove UI element if deprecated
  - Status: NEEDS DIAGNOSIS

## UI/UX Updates
- [ ] **About Popup** — Out of date
  - Check current content
  - Update version, credits, links
  - Status: NEEDS REVIEW

- [ ] **In-App Instructions** — Update all help text
  - Explain new exclusion system
  - Document file upload feature
  - Document license key system (once re-added)
  - Status: TO BE DONE LAST (per user)

## Documentation
- [ ] **INSTALL_INSTRUCTIONS.txt** — Review and update
  - Check if matches current setup flow
  - Add license key info (once working)
  - Status: PENDING REVIEW

- [ ] **UPDATE_INSTRUCTIONS.txt** — Review and update
  - Document update process
  - Check for update button instructions
  - Status: PENDING REVIEW

## Follow-Up Items
- [ ] Identify any additional missing features (user said "im sure there is more")

---

## Notes
- Baseline saved: v1.0.4-baseline-2026-06-12
- Config file: Has personal credentials (remove before release ZIP)
- All work isolated in v1.0.4 directory
