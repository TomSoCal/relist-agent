# eBay Relist Agent v2.0.0 — Single-Window Tab Interface Design

**Date:** 2026-07-11  
**Status:** Approved  
**Author:** Claude Code  

---

## Overview

Refactor v1.5.0's single-window tkinter GUI to use a tab-based interface for better organization. All features, functionality, and branding from v1.5.0 are preserved exactly — only the UI layout changes from a 3-column grid to tabbed sections.

**Current v1.5.0 layout:** 3-column tkinter window (left: status/progress, center: activity log, right: buttons)  
**v2.0 layout:** Single window with 4 tabs (Configure, Exclusions, Status, Logs) + fixed auxiliary buttons (Instructions, About, Check for Updates, Stop Service, Exit)

**Scope:** UI refactoring of `gui_app.py` only. No changes to core relisting logic, API calls, scheduling, email reports, or any supporting modules.

---

## Goals

- **Tab-based organization** — Reorganize v1.5.0's single window from 3-column grid to 4-tab interface for cleaner UX
- **All features preserved** — Every button, form, and workflow from v1.5.0 remains unchanged and accessible
- **Preserve branding** — Keep eBay red accent (#d32f2f), ERA icon, color scheme, and styling intact
- **Keep auxiliary controls visible** — Instructions, About, Check for Updates, Stop Service, Exit remain accessible (not hidden by tabs)
- **Minimal code changes** — Only `gui_app.py` is refactored; all other modules remain untouched
- **Safe development** — v1.5.0 stays intact at root; v2.0-dev folder for testing

---

## Non-Goals

- Redesign the UI beyond consolidation
- Add new features
- Refactor supporting modules (auth, API, notifications, etc.)
- Change functionality of any existing feature

---

## Architecture

### Tab Structure

The main window contains a `QTabWidget` with exactly 4 core tabs:

1. **Configure Tab**
   - eBay API credentials (App ID, Dev ID, Cert ID, RU Name)
   - Email configuration (Gmail email, app password, report recipient)
   - Store name
   - Schedule settings (run time, days, items per run, log days)
   - Buttons: Save Configuration, Clear Cache

2. **Exclusions Tab**
   - File upload (CSV/XLS) for bulk exclusion list
   - Manual item ID entry + Add button
   - List of currently excluded items with Remove buttons
   - Button: Save Exclusions

3. **Status Tab**
   - Real-time progress (current item, stage, progress bar)
   - Today's run statistics (relisted count, skipped count, errors, time)
   - Active listing count and rotation estimate
   - Next scheduled run info
   - Buttons: Run Now, Inventory, Refresh, View Log, Retry Relist

4. **Logs Tab**
   - Activity history (success/skip/error entries with timestamps)
   - Status badges (Success, Skipped, Error, Retry)
   - Item IDs, old→new ID mapping, operation details
   - Buttons: Export Logs, Clear Logs

### Auxiliary Buttons (Right-side panel or bottom bar)

These buttons remain accessible from any tab (not hidden by tab switching):

- **Instructions** — Opens Quick Guide window with setup/usage instructions
- **About** — Displays app version, license info, credits
- **Check for Updates** — Launches update_checker.py to detect new versions
- **Stop Service** — Halts the scheduled task and stops current run
- **Exit** — Closes the application gracefully

### Folder Structure

```
C:\Users\tom\agents\ebay-relist-agent\
├── v1.5.0/                    # Original v1.5.0 (untouched backup)
│   ├── ebay_relist_agent.py
│   ├── gui_app.py
│   ├── auth.py
│   ├── ebay_api.py
│   ├── listing_logic.py
│   ├── notifications.py
│   ├── config.json
│   └── [other v1.5.0 files]
│
├── v2.0-dev/                  # v2.0 development folder
│   ├── ebay_relist_agent.py   (copy, minimal changes)
│   ├── gui_app.py             (refactored for tabs)
│   ├── auth.py                (unchanged)
│   ├── ebay_api.py            (unchanged)
│   ├── listing_logic.py       (unchanged)
│   ├── notifications.py       (unchanged)
│   ├── config.json            (template)
│   └── [other v2.0 files]
│
├── ebay_relist_agent.py       (v1.5.0 at root, active)
├── gui_app.py                 (v1.5.0 at root, active)
├── auth.py                    (v1.5.0 at root, active)
├── ebay_api.py                (v1.5.0 at root, active)
└── [other root files]
```

**Key:** v1.5.0 remains at root (untouched). v2.0-dev is isolated for testing.

### Code Organization

**Files that change:**
- `v2.0-dev/gui_app.py` — MAJOR refactoring (see Implementation Approach below)

**Files that remain unchanged:**
- `ebay_relist_agent.py` — Entry point, no changes
- `auth.py` — OAuth and credential management
- `ebay_api.py` — eBay API calls
- `listing_logic.py` — Relisting core logic
- `notifications.py` — Email formatting and sending
- All other modules and supporting files

### Branding & Styling

**Preserved from v1.5.0:**
- Color scheme: eBay red (#d32f2f) accents, Windows system colors
- ERA icon: No changes
- Window title: "eBay Relist Agent"
- Font sizes, spacing, button styles
- All dark mode / light mode compatibility

---

## Implementation Approach

### Refactoring Strategy: Minimal Code Changes

**Current v1.5.0 structure (simplified):**
```python
class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI setup, signals, slots

class ExclusionsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI setup, signals, slots

class StatusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI setup, signals, slots

class LogsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI setup, signals, slots

# Main app
class EbayRelistApp(QApplication):
    def run(self):
        self.config_window = ConfigWindow()
        self.exclusions_window = ExclusionsWindow()
        self.status_window = StatusWindow()
        self.logs_window = LogsWindow()
        # Each window launches independently
```

**v2.0 refactored structure:**
```python
class ConfigTab(QWidget):  # Changed from QMainWindow
    def __init__(self):
        super().__init__()
        # Same UI code as ConfigWindow (no logic changes)
        # All signals and slots remain identical

class ExclusionsTab(QWidget):
    def __init__(self):
        super().__init__()
        # Same UI code as ExclusionsWindow

class StatusTab(QWidget):
    def __init__(self):
        super().__init__()
        # Same UI code as StatusWindow

class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        # Same UI code as LogsWindow

# Main window with tabs
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("eBay Relist Agent")
        self.setWindowIcon(QIcon("ERA_Icon.png"))  # Same icon
        
        tabs = QTabWidget()
        tabs.addTab(ConfigTab(), "Configure")
        tabs.addTab(ExclusionsTab(), "Exclusions")
        tabs.addTab(StatusTab(), "Status")
        tabs.addTab(LogsTab(), "Logs")
        
        self.setCentralWidget(tabs)
        self.show()

# Main app
class EbayRelistApp(QApplication):
    def run(self):
        self.main_window = MainWindow()
        # Single window handles all tabs
```

### No Changes to Logic

- Button click handlers remain unchanged
- Data flow (API calls, file uploads, email sending) unchanged
- State management unchanged
- All signals and slots work identically
- Configuration save/load unchanged
- Email report generation unchanged
- Scheduled task execution unchanged

---

## Data Flow (Unchanged from v1.5.0)

```
User clicks "Configure" tab
  → ConfigTab loads (no API calls yet)
  → User enters settings
  → Clicks "Save Configuration"
  → Same save_config() function as v1.5.0
  → config.json updated

User clicks "Status" tab
  → StatusTab loads
  → refresh_status() called (same function)
  → Fetches active listing count from API
  → Displays stats

User clicks "Run Now"
  → Calls do_relist() (unchanged)
  → Gets 10 oldest listings
  → AddItem / EndItem / GetItem API calls
  → Logs to Logs tab (same logging)
  → Sends email report (same format)
```

---

## Testing Strategy

### Phase 1: Setup & Launch
- [ ] Copy v1.5.0 files to v2.0-dev/
- [ ] Refactor gui_app.py to tab structure
- [ ] Verify app launches without errors
- [ ] Verify window title and icon display

### Phase 2: UI Functionality
- [ ] Configure tab: All form fields work (run time, item count, email)
- [ ] Configure tab: Save button saves to config.json
- [ ] Configure tab: Test Email button sends test email
- [ ] Exclusions tab: File upload accepts CSV/XLS
- [ ] Exclusions tab: Add Item ID button works
- [ ] Exclusions tab: Remove button deletes from list
- [ ] Exclusions tab: Save button persists exclusions
- [ ] Status tab: Displays current stats
- [ ] Status tab: Run Now button triggers relisting
- [ ] Logs tab: Shows activity history
- [ ] Logs tab: Export and Clear buttons work
- [ ] All tabs: Tab switching is smooth

### Phase 3: Feature Parity
- [ ] Configure: Settings save and load correctly
- [ ] Exclusions: Items are actually excluded from relisting
- [ ] Status: Real-time stats update after Run Now
- [ ] Logs: All operations logged correctly
- [ ] Scheduled task still triggers daily run
- [ ] Email reports sent with same format/content

### Phase 4: Comparison Test
- [ ] Run v1.5.0 and v2.0-dev side-by-side
- [ ] Verify identical behavior for all features
- [ ] Confirm no regressions

### Phase 5: Edge Cases
- [ ] Close app mid-operation (graceful shutdown)
- [ ] Resize window, verify tabs scale properly
- [ ] Dark mode / light mode both work
- [ ] Multiple rapid tab switches (no crashes)

---

## Success Criteria

- ✅ Single window launches with 4 visible tabs
- ✅ All v1.5.0 features present and functional
- ✅ No features removed or changed
- ✅ Color scheme and branding intact
- ✅ v1.5.0 remains untouched at root
- ✅ Zero errors/crashes during testing
- ✅ All buttons, forms, and workflows work identically to v1.5.0

---

## Constraints

- **No refactoring beyond tabs** — Do not rename functions, reorganize modules, or improve code
- **Preserve all signals/slots** — Button handlers and data flow unchanged
- **Keep v1.5.0 safe** — Development in v2.0-dev/ only
- **No new features** — Only consolidate existing features into tabs
- **Maintain branding** — Color scheme, icon, styling exactly as v1.5.0

---

## Rollback Plan

If issues arise during v2.0 development:
1. v1.5.0 remains at root — no impact
2. Delete v2.0-dev/ folder
3. Root version continues to work
4. No data loss, no user impact

---

## Timeline

- **Phase 1 (Setup):** 1-2 hours
- **Phase 2 (UI Testing):** 2-3 hours
- **Phase 3 (Feature Testing):** 2-3 hours
- **Phase 4 (Comparison):** 1-2 hours
- **Phase 5 (Edge Cases):** 1-2 hours
- **Total:** ~8-12 hours development + testing

---

## Next Steps

1. Write implementation plan (writing-plans skill)
2. Copy v1.5.0 to v2.0-dev/
3. Refactor gui_app.py to tab structure
4. Run through testing phases
5. Build standalone EXE for v2.0
6. Release to GitHub

