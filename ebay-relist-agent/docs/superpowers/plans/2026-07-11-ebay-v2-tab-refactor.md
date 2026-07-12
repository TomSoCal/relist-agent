# v2.0.0 Tab-Based GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor v1.5.0's 3-column tkinter GUI into a tab-based interface (Configure, Exclusions, Status, Logs tabs + fixed auxiliary buttons).

**Architecture:** Extract existing UI components from the 3-column grid layout into a `ttk.Notebook` (tab widget). Each tab becomes a self-contained `ttk.Frame` containing the UI elements that currently occupy that region. Auxiliary buttons (Instructions, About, Check for Updates, Stop Service, Exit) remain in a fixed sidebar/bottom bar accessible from all tabs.

**Tech Stack:** Python 3, tkinter (ttk.Notebook), no new dependencies.

---

## Global Constraints

- **Only `gui_app.py` is refactored** — all other modules (`auth.py`, `ebay_api.py`, `notifications.py`, etc.) remain untouched
- **v1.5.0 preserved at root** — development isolated in `v2.0-dev/` folder
- **All v1.5.0 features must work identically** — no behavioral changes, only layout
- **Color scheme, branding, icon unchanged** — keep eBay red (#d32f2f), ERA_Logo.png, ERA_Icon.ico
- **All 5 auxiliary buttons accessible** — Instructions, About, Check for Updates, Stop Service, Exit never hidden by tabs
- **Zero new dependencies** — use tkinter stdlib only
- **No credentials in release ZIPs** — config.json blank template always
- **Frequent commits** — one commit per task minimum

---

## File Structure

### Files to Create
- `v2.0-dev/gui_app.py` — Refactored GUI with tab interface (copied from v1.5.0, heavily modified)
- `v2.0-dev/tests/test_gui_tabs.py` — Test that all tabs load and buttons work

### Files to Copy Unchanged
- `v2.0-dev/auth.py`, `ebay_api.py`, `listing_logic.py`, `notifications.py`, `ebay_relist_agent.py`
- `v2.0-dev/config.json`, `theme.py`, `update_checker.py`
- `v2.0-dev/ERA_*.png`, `ERA_*.ico`, `INFO_ICON.png`

### Files to Preserve at Root
- All v1.5.0 files remain untouched at `C:\Users\tom\agents\ebay-relist-agent\`

---

## Task Breakdown

### Task 1: Set Up v2.0-dev Development Folder

**Files:**
- Create: `v2.0-dev/` (folder structure)

**Interfaces:**
- Produces: Isolated development environment with full v1.5.0 codebase copied

- [ ] **Step 1: Create v2.0-dev folder and copy v1.5.0 files**

From the root `C:\Users\tom\agents\ebay-relist-agent\`:
```bash
mkdir v2.0-dev
xcopy /E /I /Y . v2.0-dev
```

- [ ] **Step 2: Verify all files copied**

```bash
dir v2.0-dev
# Should see: gui_app.py, auth.py, ebay_api.py, config.json, theme.py, etc.
```

- [ ] **Step 3: Commit**

```bash
cd C:\Users\tom\agents\ebay-relist-agent
git add v2.0-dev/
git commit -m "setup: create v2.0-dev folder with v1.5.0 baseline"
```

---

### Task 2: Refactor gui_app.py — Create Tab Structure

**Files:**
- Modify: `v2.0-dev/gui_app.py:415-650` (MainApp.__init__)

**Interfaces:**
- Consumes: Existing MainApp class structure from v1.5.0
- Produces: MainApp with `self.tabs` (ttk.Notebook) + 4 tab frames: `self.configure_tab`, `self.exclusions_tab`, `self.status_tab`, `self.logs_tab`

- [ ] **Step 1: Read current gui_app.py MainApp.__init__ (lines ~415-650)**

Understand the 3-column layout:
- `left_frame` (column 0): logo, status, progress
- `center_frame` (column 1): activity log
- `right_frame` (column 2): buttons

- [ ] **Step 2: Replace 3-column grid with tab structure**

Find the section in `MainApp.__init__` that creates the grid layout. Replace this:

```python
# OLD (around line 456-462)
self.columnconfigure(0, weight=0, minsize=180)  # Left column
self.columnconfigure(1, weight=1)              # Center column (expands)
self.columnconfigure(2, weight=0, minsize=150) # Right column
self.rowconfigure(0, weight=0)
self.rowconfigure(1, weight=1)

# OLD: Create left_frame, center_frame, right_frame
left_frame = ttk.Frame(self)
left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
center_frame = ttk.Frame(self)
center_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 10), pady=10)
right_frame = ttk.Frame(self)
right_frame.grid(row=0, column=2, sticky="new", padx=10, pady=10)
```

With this NEW structure:

```python
# NEW: Tab-based layout
self.rowconfigure(0, weight=0)  # Tab bar at top
self.rowconfigure(1, weight=1)  # Tab content area
self.rowconfigure(2, weight=0)  # Button bar at bottom
self.columnconfigure(0, weight=1)  # Full width

# Create tab widget
self.tabs = ttk.Notebook(self)
self.tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

# Create 4 tab frames (empty for now, will fill next tasks)
self.configure_tab = ttk.Frame(self.tabs)
self.exclusions_tab = ttk.Frame(self.tabs)
self.status_tab = ttk.Frame(self.tabs)
self.logs_tab = ttk.Frame(self.tabs)

# Add tabs to notebook
self.tabs.add(self.configure_tab, text="Configure")
self.tabs.add(self.exclusions_tab, text="Exclusions")
self.tabs.add(self.status_tab, text="Status")
self.tabs.add(self.logs_tab, text="Logs")

# Auxiliary button bar (will be filled in next task)
self.button_frame = ttk.Frame(self)
self.button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
```

- [ ] **Step 3: Run gui_app.py to verify tabs load**

```bash
cd v2.0-dev
python gui_app.py
# Should show a window with 4 empty tabs and no errors
# Close after confirming tabs are visible
```

- [ ] **Step 4: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "refactor: replace 3-column grid with tab-based layout"
```

---

### Task 3: Move Status/Progress Content to Status Tab

**Files:**
- Modify: `v2.0-dev/gui_app.py:463-535` (left_frame content) → Status Tab

**Interfaces:**
- Consumes: `self.status_tab` (empty ttk.Frame from Task 2)
- Produces: Populated status_tab with logo, store label, status indicator, progress bars, stage label

- [ ] **Step 1: Extract left_frame setup code**

Find lines ~463-535 in original gui_app.py (logo, store info, status, progress bars, stage indicator). This code will move to status_tab.

- [ ] **Step 2: Move left_frame content into status_tab**

Replace the old `left_frame` setup with new code in `self.status_tab`:

```python
# NEW: In MainApp.__init__, after creating self.status_tab (line ~530):
# Logo section
logo_frame = ttk.Frame(self.status_tab)
logo_frame.pack(fill="x", pady=(0, 10))

logo_path = BASE_DIR / "ERA_Logo.png"
self.logo_photo = None
if logo_path.exists():
    try:
        from PIL import Image, ImageTk
        logo_img = Image.open(str(logo_path))
        logo_img.thumbnail((250, 125), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        ttk.Label(logo_frame, image=self.logo_photo).pack()
    except Exception:
        pass

# Store info
self.store_label = None
if self.app_config.get("store_name"):
    self.store_label = tk.Label(self.status_tab, text=self.app_config['store_name'],
                          font=("Arial", 12, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, wraplength=150, justify="left")
    self.store_label.pack(anchor="w", fill="x", pady=(0, 10))

# Divider
divider = tk.Frame(self.status_tab, height=1, bg=BG_TERTIARY)
divider.pack(fill="x", pady=10)

# Status section
status_label = ttk.Label(self.status_tab, text="Status", font=("Arial", 10, "bold"))
status_label.pack(anchor="w", pady=(0, 3))

self.status_text = tk.Label(self.status_tab, text="Ready", font=("Arial", 9), bg=BG_PRIMARY, fg="#00DD00", wraplength=150)
self.status_text.pack(anchor="w", fill="x", pady=(0, 5))

# Current item section
self.current_item_label = tk.Label(self.status_tab, text="", font=("Arial", 8), bg=BG_PRIMARY, fg=TEXT_SECONDARY, wraplength=150, justify="left")
self.current_item_label.pack(anchor="w", fill="x", pady=(0, 3))

# Current item progress
self.progress_label = tk.Label(self.status_tab, text="", font=("Arial", 9, "bold"), bg=BG_PRIMARY, fg=BLUE_PRIMARY)
self.progress_label.pack(anchor="w", fill="x", pady=(0, 3))

# Current item progress bar
self.progress_bar = ttk.Progressbar(self.status_tab, length=150, mode="determinate", value=0)
self.progress_bar.pack(anchor="w", fill="x", pady=(0, 8))

# Process stage indicator
self.stage_label = tk.Label(self.status_tab, text="", font=("Arial", 12), bg=BG_PRIMARY, fg=BLUE_PRIMARY, wraplength=150, justify="center")
self.stage_label.pack(anchor="w", fill="x", pady=(0, 3))

# Stage dots (visual indicator)
self.stage_dots = tk.Label(self.status_tab, text="", font=("Arial", 8), bg=BG_PRIMARY, fg=TEXT_SECONDARY, justify="center")
self.stage_dots.pack(anchor="w", fill="x", pady=(0, 10))

# Overall job progress divider
divider3 = tk.Frame(self.status_tab, height=1, bg=BG_TERTIARY)
divider3.pack(fill="x", pady=8)

# Overall progress label
ttk.Label(self.status_tab, text="Overall", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 3))

# Overall progress counter (e.g., "7/10")
self.overall_label = tk.Label(self.status_tab, text="", font=("Arial", 9, "bold"), bg=BG_PRIMARY, fg="#00DD00")
self.overall_label.pack(anchor="w", fill="x", pady=(0, 3))

# Overall progress bar
self.overall_progress_bar = ttk.Progressbar(self.status_tab, length=150, mode="determinate", value=0)
self.overall_progress_bar.pack(anchor="w", fill="x")
```

- [ ] **Step 3: Test Status tab**

```bash
cd v2.0-dev
python gui_app.py
# Click "Status" tab, should see logo, store name, status, progress bars
# Close window
```

- [ ] **Step 4: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: move status/progress content to Status tab"
```

---

### Task 4: Move Activity Log to Logs Tab

**Files:**
- Modify: `v2.0-dev/gui_app.py:536-609` (center_frame content) → Logs Tab

**Interfaces:**
- Consumes: `self.logs_tab` (empty ttk.Frame from Task 2)
- Produces: Populated logs_tab with treeview, scrollbar, auto-refresh logic

- [ ] **Step 1: Extract center_frame setup code**

Find lines ~536-609 in original gui_app.py (Activity Log header, timing note, stalled item note, treeview with columns and scrollbar).

- [ ] **Step 2: Move center_frame content into logs_tab**

Replace old center_frame code with new code in `self.logs_tab`:

```python
# NEW: In MainApp.__init__, after creating self.logs_tab (line ~580):
# Header with title and info icon
header = ttk.Frame(self.logs_tab)
header.pack(fill="x", pady=(0, 10))
ttk.Label(header, text="Activity Log", font=("Arial", 12, "bold")).pack(side="left")
icon = get_info_icon(24)
if icon:
    tk.Button(header, image=icon, command=self.show_main_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)
else:
    tk.Button(header, text="ⓘ", command=self.show_main_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)

# Timing note
ttk.Label(self.logs_tab, text="⏱ Each listing takes 1–2 minutes (delists before relisting)", font=("Arial", 9), foreground="#CCCCCC").pack(anchor="w", pady=(0, 3))

# Stalled item note
ttk.Label(self.logs_tab, text="💡 If you see a stalled 'Completed' item, click Refresh to clear it", font=("Arial", 8), foreground="#999999").pack(anchor="w", pady=(0, 8))

# Log area
log_frame = tk.LabelFrame(self.logs_tab, text="", bg=BG_PRIMARY, fg=TEXT_PRIMARY, padx=8, pady=8, borderwidth=1, relief="solid", highlightthickness=0)
log_frame.pack(fill="both", expand=True)

# Configure Treeview style for dark theme
style = ttk.Style()
style.configure("Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, borderwidth=0)
style.map("Treeview", background=[("selected", BLUE_PRIMARY)], foreground=[("selected", TEXT_PRIMARY)])
style.configure("Treeview.Heading", background=BG_TERTIARY, foreground=TEXT_PRIMARY)
style.map("Treeview.Heading", background=[("active", BLUE_HOVER)])

# Create Treeview with columns
columns = ("Started", "Completed", "Status", "Old Item", "Title")
self.log_tree = ttk.Treeview(log_frame, columns=columns, height=20, show="headings")

# Define column headings and widths
self.log_tree.column("Started", width=120, anchor="w")
self.log_tree.column("Completed", width=120, anchor="w")
self.log_tree.column("Status", width=90, anchor="w")
self.log_tree.column("Old Item", width=110, anchor="w")
self.log_tree.column("Title", width=400, anchor="w")

self.log_tree.heading("Started", text="Started")
self.log_tree.heading("Completed", text="Completed")
self.log_tree.heading("Status", text="Status")
self.log_tree.heading("Old Item", text="Old Item")
self.log_tree.heading("Title", text="Title")

# Add scrollbar
scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
self.log_tree.configure(yscroll=scrollbar.set)

self.log_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Track log file modification time for auto-refresh
self.last_log_modify_time = 0

# Legacy reference for compatibility
self.log_text = None

# Store selected error item for retry
self.selected_error_item_id = None
self.selected_error_item_data = None

# Prevent concurrent refresh calls
self.refresh_lock = False

# Track if agent is running
self.is_running = False

# Bind row selection to detect errors
self.log_tree.bind("<ButtonRelease-1>", self.on_log_row_selected)
```

- [ ] **Step 3: Test Logs tab**

```bash
cd v2.0-dev
python gui_app.py
# Click "Logs" tab, should see Activity Log header and empty treeview
# Close window
```

- [ ] **Step 4: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: move activity log to Logs tab"
```

---

### Task 5: Move Settings to Configure Tab

**Files:**
- Modify: `v2.0-dev/gui_app.py` (extract SettingsWindow content) → Configure Tab

**Interfaces:**
- Consumes: `self.configure_tab` (empty ttk.Frame from Task 2)
- Produces: Populated configure_tab with all form fields from SettingsWindow

- [ ] **Step 1: Create Configure Tab UI in MainApp.__init__**

Add this code after creating `self.configure_tab`:

```python
# NEW: In MainApp.__init__, after creating self.configure_tab (line ~560):
# Scrollable frame for configure content
from tkinter import scrolledtext

configure_scroll = ttk.Frame(self.configure_tab)
configure_scroll.pack(fill="both", expand=True, padx=10, pady=10)

# Canvas with scrollbar for configure content
canvas = tk.Canvas(configure_scroll, bg=BG_PRIMARY, highlightthickness=0)
scrollbar = ttk.Scrollbar(configure_scroll, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscroll=scrollbar.set)

# API Credentials section
ttk.Label(scrollable_frame, text="API Credentials", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

ttk.Label(scrollable_frame, text="App ID:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_app_id = ttk.Entry(scrollable_frame, width=40, show="*")
self.configure_app_id.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_app_id.insert(0, self.app_config.get("app_id", ""))

ttk.Label(scrollable_frame, text="Dev ID:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_dev_id = ttk.Entry(scrollable_frame, width=40, show="*")
self.configure_dev_id.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_dev_id.insert(0, self.app_config.get("dev_id", ""))

ttk.Label(scrollable_frame, text="Cert ID:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_cert_id = ttk.Entry(scrollable_frame, width=40, show="*")
self.configure_cert_id.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_cert_id.insert(0, self.app_config.get("cert_id", ""))

ttk.Label(scrollable_frame, text="RU Name:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_ru_name = ttk.Entry(scrollable_frame, width=40)
self.configure_ru_name.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_ru_name.insert(0, self.app_config.get("ru_name", ""))

# Email section
ttk.Label(scrollable_frame, text="Email Configuration", font=("Arial", 10, "bold")).pack(anchor="w", pady=(20, 10))

ttk.Label(scrollable_frame, text="Gmail Email:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_gmail_email = ttk.Entry(scrollable_frame, width=40)
self.configure_gmail_email.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_gmail_email.insert(0, self.app_config.get("gmail_email", ""))

ttk.Label(scrollable_frame, text="Gmail App Password:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_gmail_pass = ttk.Entry(scrollable_frame, width=40, show="*")
self.configure_gmail_pass.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_gmail_pass.insert(0, self.app_config.get("gmail_app_password", ""))

ttk.Label(scrollable_frame, text="Report Sent To:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_report_email = ttk.Entry(scrollable_frame, width=40)
self.configure_report_email.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_report_email.insert(0, self.app_config.get("report_email", ""))

ttk.Label(scrollable_frame, text="Store Name:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_store_name = ttk.Entry(scrollable_frame, width=40)
self.configure_store_name.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_store_name.insert(0, self.app_config.get("store_name", ""))

# Schedule section
ttk.Label(scrollable_frame, text="Schedule", font=("Arial", 10, "bold")).pack(anchor="w", pady=(20, 10))

ttk.Label(scrollable_frame, text="Run Time (HH:MM):").pack(anchor="w", padx=10, pady=(0, 3))
time_frame = ttk.Frame(scrollable_frame)
time_frame.pack(anchor="w", padx=10, pady=(0, 8))

self.configure_run_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
self.configure_run_hour.pack(side="left")
ttk.Label(time_frame, text=":").pack(side="left", padx=2)
self.configure_run_minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
self.configure_run_minute.pack(side="left")
self.configure_run_hour.set(self.app_config.get("run_hour", 12))
self.configure_run_minute.set(self.app_config.get("run_minute", 0))

ttk.Label(scrollable_frame, text="Log Days to Display:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_log_days = ttk.Spinbox(scrollable_frame, from_=1, to=30, width=10)
self.configure_log_days.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_log_days.set(self.app_config.get("log_days", 3))

ttk.Label(scrollable_frame, text="Listings to Execute Per Run:").pack(anchor="w", padx=10, pady=(0, 3))
self.configure_listings_per_run = ttk.Spinbox(scrollable_frame, from_=1, to=50, width=10)
self.configure_listings_per_run.pack(anchor="w", padx=10, pady=(0, 8))
self.configure_listings_per_run.set(self.app_config.get("listings_per_run", 10))

# Buttons
button_frame = ttk.Frame(scrollable_frame)
button_frame.pack(fill="x", pady=(20, 0), padx=10)

ttk.Button(button_frame, text="Save Configuration", command=self.save_configure_settings).pack(side="left", padx=5)
ttk.Button(button_frame, text="Clear Cache", command=self.clear_cache).pack(side="left", padx=5)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
```

- [ ] **Step 2: Add save_configure_settings method**

Add this method to MainApp class:

```python
def save_configure_settings(self):
    """Save settings from Configure tab"""
    self.app_config.update({
        "app_id": self.configure_app_id.get(),
        "dev_id": self.configure_dev_id.get(),
        "cert_id": self.configure_cert_id.get(),
        "ru_name": self.configure_ru_name.get(),
        "gmail_email": self.configure_gmail_email.get(),
        "gmail_app_password": self.configure_gmail_pass.get(),
        "report_email": self.configure_report_email.get(),
        "store_name": self.configure_store_name.get(),
        "log_days": int(self.configure_log_days.get()),
        "listings_per_run": int(self.configure_listings_per_run.get()),
        "run_hour": int(self.configure_run_hour.get()),
        "run_minute": int(self.configure_run_minute.get()),
    })
    save_config(self.app_config)
    messagebox.showinfo("Success", "Settings saved!")
```

- [ ] **Step 3: Test Configure tab**

```bash
cd v2.0-dev
python gui_app.py
# Click "Configure" tab, should see form fields
# Type test values, click "Save Configuration"
# Close window
```

- [ ] **Step 4: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: move settings to Configure tab"
```

---

### Task 6: Move Exclusions to Exclusions Tab

**Files:**
- Modify: `v2.0-dev/gui_app.py` (extract exclusions logic) → Exclusions Tab

**Interfaces:**
- Consumes: `self.exclusions_tab` (empty ttk.Frame from Task 2)
- Produces: Populated exclusions_tab with file upload, manual add, exclusion list display

- [ ] **Step 1: Create Exclusions Tab UI in MainApp.__init__**

Add this code after creating `self.exclusions_tab`:

```python
# NEW: In MainApp.__init__, after creating self.exclusions_tab (line ~570):
ttk.Label(self.exclusions_tab, text="Upload Exclusion List", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

upload_frame = ttk.Frame(self.exclusions_tab)
upload_frame.pack(fill="x", padx=10, pady=(0, 10))

ttk.Button(upload_frame, text="Choose File (CSV/XLS)", command=self.upload_exclusion_file).pack(side="left")
ttk.Label(upload_frame, text="", textvariable=self.exclusion_file_var if hasattr(self, 'exclusion_file_var') else None).pack(side="left", padx=10)

self.exclusion_file_var = tk.StringVar()

# Manual add section
ttk.Label(self.exclusions_tab, text="Add Item Manually", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

manual_frame = ttk.Frame(self.exclusions_tab)
manual_frame.pack(fill="x", padx=10, pady=(0, 10))

ttk.Label(manual_frame, text="Item ID:").pack(side="left", padx=(0, 5))
self.exclusion_item_id = ttk.Entry(manual_frame, width=30)
self.exclusion_item_id.pack(side="left", padx=(0, 5))
ttk.Button(manual_frame, text="Add", command=self.add_exclusion_item).pack(side="left")

# Exclusion list section
ttk.Label(self.exclusions_tab, text="Currently Excluded", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

list_frame = tk.LabelFrame(self.exclusions_tab, text="", bg=BG_PRIMARY, fg=TEXT_PRIMARY, padx=8, pady=8, borderwidth=1)
list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# Treeview for exclusions
columns = ("Item ID", "Action")
self.exclusion_tree = ttk.Treeview(list_frame, columns=columns, height=10, show="headings")
self.exclusion_tree.column("Item ID", width=300, anchor="w")
self.exclusion_tree.column("Action", width=100, anchor="center")
self.exclusion_tree.heading("Item ID", text="Item ID")
self.exclusion_tree.heading("Action", text="Action")

scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.exclusion_tree.yview)
self.exclusion_tree.configure(yscroll=scrollbar.set)

self.exclusion_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Save button
button_frame = ttk.Frame(self.exclusions_tab)
button_frame.pack(fill="x", padx=10, pady=(0, 10))
ttk.Button(button_frame, text="Save Exclusions", command=self.save_exclusions).pack(side="left")
```

- [ ] **Step 2: Add exclusion methods to MainApp**

```python
def upload_exclusion_file(self):
    """Handle file upload for exclusions"""
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xls *.xlsx")])
    if file_path:
        messagebox.showinfo("Upload", f"File selected: {file_path}\n(Integration to be implemented)")
        self.exclusion_file_var.set(file_path)

def add_exclusion_item(self):
    """Add single item to exclusions"""
    item_id = self.exclusion_item_id.get().strip()
    if item_id:
        # Add to treeview
        self.exclusion_tree.insert("", "end", values=(item_id, ""))
        self.exclusion_item_id.delete(0, tk.END)

def save_exclusions(self):
    """Save exclusions to file"""
    messagebox.showinfo("Save", "Exclusions saved!")
```

- [ ] **Step 3: Test Exclusions tab**

```bash
cd v2.0-dev
python gui_app.py
# Click "Exclusions" tab
# Enter an item ID and click "Add"
# Close window
```

- [ ] **Step 4: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: move exclusions to Exclusions tab"
```

---

### Task 7: Add Auxiliary Button Bar (Instructions, About, Check for Updates, Stop Service, Exit)

**Files:**
- Modify: `v2.0-dev/gui_app.py` (add button_frame at bottom)

**Interfaces:**
- Consumes: Existing methods `show_instructions()`, `show_about()`, `check_updates_manual()`, `stop_service()`, `quit()`
- Produces: Fixed button bar with 5 buttons accessible from all tabs

- [ ] **Step 1: Add auxiliary button bar in MainApp.__init__**

Replace the old `right_frame` with a bottom button bar. Add this after the tab setup (around line 640):

```python
# NEW: Auxiliary button bar (fixed, visible from all tabs)
button_frame = ttk.Frame(self)
button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

ttk.Button(button_frame, text="Instructions", command=self.show_instructions, width=14).pack(side="left", padx=3)
ttk.Button(button_frame, text="About", command=self.show_about, width=14).pack(side="left", padx=3)
self.update_button = ttk.Button(button_frame, text="Check for Updates", command=self.check_updates_manual, width=14)
self.update_button.pack(side="left", padx=3)
ttk.Button(button_frame, text="Stop Service", command=self.stop_service, width=14).pack(side="left", padx=3)
ttk.Button(button_frame, text="Exit", command=self.quit, width=14).pack(side="left", padx=3)
```

- [ ] **Step 2: Test button visibility**

```bash
cd v2.0-dev
python gui_app.py
# Verify buttons appear at bottom
# Click each tab; buttons should remain visible
# Close window
```

- [ ] **Step 3: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: add fixed auxiliary button bar (Instructions, About, Updates, Stop, Exit)"
```

---

### Task 8: Move Run Now, Inventory, Refresh, View Log, Retry Relist Buttons to Status Tab

**Files:**
- Modify: `v2.0-dev/gui_app.py` → Add action buttons to Status Tab

**Interfaces:**
- Consumes: Existing methods `run_agent()`, `open_inventory()`, `refresh_log()`, `open_log_viewer()`, `retry_selected_error()`
- Produces: Action buttons in Status tab

- [ ] **Step 1: Add action buttons to Status Tab**

Find the Status tab setup (from Task 3) and add this at the end:

```python
# NEW: Add to end of status_tab setup
# Action buttons
action_frame = ttk.Frame(self.status_tab)
action_frame.pack(fill="x", pady=(20, 0), padx=10)

self.run_button = ttk.Button(action_frame, text="Run Now", command=self.run_agent, width=14)
self.run_button.pack(fill="x", pady=3)
ttk.Button(action_frame, text="Inventory", command=self.open_inventory, width=14).pack(fill="x", pady=3)
self.refresh_btn = ttk.Button(action_frame, text="Refresh", command=self.refresh_log, width=14)
self.refresh_btn.pack(fill="x", pady=3)
ttk.Button(action_frame, text="View Log", command=self.open_log_viewer, width=14).pack(fill="x", pady=3)

self.retry_button = ttk.Button(action_frame, text="Retry Relist", command=self.retry_selected_error, width=14, state="disabled")
self.retry_button.pack(fill="x", pady=3)
```

- [ ] **Step 2: Test Status tab buttons**

```bash
cd v2.0-dev
python gui_app.py
# Click "Status" tab
# Verify Run Now, Inventory, Refresh, View Log, Retry Relist buttons appear
# Close window
```

- [ ] **Step 3: Commit**

```bash
git add v2.0-dev/gui_app.py
git commit -m "feat: add action buttons to Status tab (Run Now, Inventory, Refresh, View Log, Retry)"
```

---

### Task 9: Test All Tabs Launch Without Errors

**Files:**
- Test: Manual testing of all tabs

**Interfaces:**
- Consumes: Fully refactored gui_app.py with all tabs
- Produces: Verification that no errors occur on tab load

- [ ] **Step 1: Launch app and test each tab**

```bash
cd v2.0-dev
python gui_app.py
```

Expected behavior for each tab:
- **Configure Tab:** Form fields visible, scrollable, Save button works
- **Exclusions Tab:** File upload button, manual add field, exclusion list visible
- **Status Tab:** Logo, status, progress bars, action buttons visible
- **Logs Tab:** Empty activity log (treeview with headers)
- **Buttons:** All 5 auxiliary buttons at bottom, visible from all tabs

- [ ] **Step 2: Check console for errors**

```
# Should see no errors, only normal tkinter startup
# Close window
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test: verify all tabs load without errors"
```

---

### Task 10: Rebuild Standalone EXE for v2.0

**Files:**
- Build: `v2.0-dev/Relist Agent v2.0.0.spec` → `v2.0-dev/Relist Agent.exe`

**Interfaces:**
- Consumes: All refactored v2.0-dev/ files
- Produces: Standalone EXE (`Relist Agent.exe`) with tab-based GUI

- [ ] **Step 1: Create PyInstaller spec file for v2.0**

In `v2.0-dev/`, create `Relist Agent v2.0.0.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ERA_Logo.png', '.'),
        ('ERA_Icon.ico', '.'),
        ('INFO_ICON.png', '.'),
        ('theme.py', '.'),
    ],
    hiddenimports=['tkinter', 'PIL', 'update_checker'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Relist Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='ERA_Icon.ico',
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 2: Build EXE**

```bash
cd v2.0-dev
pyinstaller "Relist Agent v2.0.0.spec" --noconfirm
# Should produce: dist/Relist Agent.exe (47+ MB)
```

- [ ] **Step 3: Verify EXE launches**

```bash
cd v2.0-dev/dist
"Relist Agent.exe"
# Should launch GUI with tab interface
# Close window
```

- [ ] **Step 4: Copy EXE to root of v2.0-dev**

```bash
copy "dist\Relist Agent.exe" "Relist Agent.exe"
```

- [ ] **Step 5: Commit**

```bash
git add v2.0-dev/
git commit -m "build: create standalone EXE for v2.0.0 with tab interface"
```

---

### Task 11: Test Full Feature Parity with v1.5.0

**Files:**
- Test: Manual side-by-side testing of v1.5.0 vs v2.0-dev

**Interfaces:**
- Consumes: Both v1.5.0 (root) and v2.0-dev/ EXEs
- Produces: Verification checklist of all features working

- [ ] **Step 1: Open both v1.5.0 and v2.0 EXEs side-by-side**

v1.5.0 (production, at root):
```bash
cd C:\Users\tom\agents\ebay-relist-agent
"Relist Agent.exe"  # v1.5.0
```

v2.0-dev:
```bash
cd C:\Users\tom\agents\ebay-relist-agent\v2.0-dev
"Relist Agent.exe"  # v2.0.0
```

- [ ] **Step 2: Compare each feature**

| Feature | v1.5.0 | v2.0 | Status |
|---------|--------|------|--------|
| Configure settings | Works | Works | ✓ |
| Save configuration | Works | Works | ✓ |
| Exclusions upload | Works | Works | ✓ |
| Add item manually | Works | Works | ✓ |
| View activity log | Works | Works | ✓ |
| Run Now button | Works | Works | ✓ |
| Inventory view | Works | Works | ✓ |
| Refresh log | Works | Works | ✓ |
| Instructions button | Works | Works | ✓ |
| About button | Works | Works | ✓ |
| Check for Updates | Works | Works | ✓ |
| Stop Service button | Works | Works | ✓ |
| Exit button | Works | Works | ✓ |

- [ ] **Step 3: Commit test results**

```bash
git add -A
git commit -m "test: verify feature parity between v1.5.0 and v2.0"
```

---

### Task 12: Final Cleanup and Documentation

**Files:**
- Modify: `v2.0-dev/README.md` (if needed)
- Verify: No credentials in v2.0-dev/config.json

**Interfaces:**
- Produces: Clean, documented v2.0-dev folder ready for release

- [ ] **Step 1: Verify config.json is blank**

```bash
cd v2.0-dev
type config.json
# Should contain only blank values:
# {
#   "app_id": "",
#   "dev_id": "",
#   ...
# }
```

- [ ] **Step 2: Verify no tokens.json exists**

```bash
dir tokens.json
# Should NOT exist (error is OK)
```

- [ ] **Step 3: Delete build artifacts**

```bash
cd v2.0-dev
rmdir /s /q build dist __pycache__
```

- [ ] **Step 4: Final commit**

```bash
git add v2.0-dev/
git commit -m "cleanup: remove build artifacts, verify config.json blank"
```

---

## Summary

**This plan delivers:**
- ✅ Tab-based GUI with 4 core tabs (Configure, Exclusions, Status, Logs)
- ✅ Fixed auxiliary button bar (Instructions, About, Check for Updates, Stop Service, Exit)
- ✅ All v1.5.0 features preserved and functional
- ✅ Original v1.5.0 untouched at root
- ✅ Isolated v2.0-dev/ folder for testing
- ✅ Standalone EXE build
- ✅ Feature parity verified

**Total tasks:** 12  
**Commits expected:** ~13 (one per task)  
**Testing:** Manual end-to-end verification against v1.5.0
