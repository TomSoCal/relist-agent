#!/usr/bin/env python3
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
from pathlib import Path
import threading
from theme import *

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "relist_log.json"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "app_id": "",
        "dev_id": "",
        "cert_id": "",
        "gmail_app_password": "",
        "store_name": "",
    }


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


class QuickGuideWindow(tk.Toplevel):
    def __init__(self, parent, title, guide_text):
        super().__init__(parent)
        self.title(f"Quick Guide - {title}")
        self.geometry("600x500")
        self.config(bg=BG_PRIMARY)

        text_widget = scrolledtext.ScrolledText(self, height=25, width=70, wrap="word", font=("Arial", 10),
                                                bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=BLUE_PRIMARY)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("end", guide_text)
        text_widget.config(state="disabled")


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("550x700")
        self.config_dict = config
        self.on_save = on_save
        self.config(bg=BG_PRIMARY)

        # Configure custom ttk style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY, font=("Arial", 10))
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])

        # Header with title and info icon
        header = ttk.Frame(self, style='TFrame')
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Settings", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(header, text="ⓘ", width=3, command=self.show_guide).pack(side="left", padx=5)

        # Form container
        form_frame = ttk.Frame(self)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # API Credentials
        ttk.Label(form_frame, text="App ID:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.app_id = ttk.Entry(form_frame, width=40)
        self.app_id.grid(row=0, column=1, padx=10, pady=5)
        self.app_id.insert(0, config.get("app_id", ""))

        ttk.Label(form_frame, text="Dev ID:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.dev_id = ttk.Entry(form_frame, width=40)
        self.dev_id.grid(row=1, column=1, padx=10, pady=5)
        self.dev_id.insert(0, config.get("dev_id", ""))

        ttk.Label(form_frame, text="Cert ID:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cert_id = ttk.Entry(form_frame, width=40)
        self.cert_id.grid(row=2, column=1, padx=10, pady=5)
        self.cert_id.insert(0, config.get("cert_id", ""))

        # Gmail
        ttk.Label(form_frame, text="Gmail Email:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.gmail_email = ttk.Entry(form_frame, width=40)
        self.gmail_email.grid(row=3, column=1, padx=10, pady=5)
        self.gmail_email.insert(0, config.get("gmail_email", ""))

        ttk.Label(form_frame, text="Gmail App Password:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.gmail_pass = ttk.Entry(form_frame, width=40, show="*")
        self.gmail_pass.grid(row=4, column=1, padx=10, pady=5)
        self.gmail_pass.insert(0, config.get("gmail_app_password", ""))

        ttk.Label(form_frame, text="Report Sent To:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.report_email = ttk.Entry(form_frame, width=40)
        self.report_email.grid(row=5, column=1, padx=10, pady=5)
        self.report_email.insert(0, config.get("report_email", ""))

        # Store Name
        ttk.Label(form_frame, text="Store Name:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.store_name = ttk.Entry(form_frame, width=40)
        self.store_name.grid(row=6, column=1, padx=10, pady=5)
        self.store_name.insert(0, config.get("store_name", ""))

        # Log Days
        ttk.Label(form_frame, text="Log Days to Display:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.log_days = ttk.Spinbox(form_frame, from_=1, to=30, width=10)
        self.log_days.grid(row=7, column=1, sticky="w", padx=10, pady=5)
        self.log_days.set(config.get("log_days", 3))

        # Listings to Execute
        ttk.Label(form_frame, text="Listings to Execute Per Run:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.listings_per_run = ttk.Spinbox(form_frame, from_=1, to=50, width=10)
        self.listings_per_run.grid(row=8, column=1, sticky="w", padx=10, pady=5)
        self.listings_per_run.set(config.get("listings_per_run", 10))

        # Schedule Frame
        schedule_frame = ttk.LabelFrame(form_frame, text="Schedule", padding=10)
        schedule_frame.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Time
        ttk.Label(schedule_frame, text="Run Time (HH:MM):").grid(row=0, column=0, sticky="w")
        time_frame = ttk.Frame(schedule_frame)
        time_frame.grid(row=0, column=1, sticky="w", padx=5)

        self.run_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.run_hour.pack(side="left")
        ttk.Label(time_frame, text=":").pack(side="left", padx=2)
        self.run_minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.run_minute.pack(side="left")

        time_str = config.get("run_time", "10:30")
        hour, minute = time_str.split(":")
        self.run_hour.set(int(hour))
        self.run_minute.set(int(minute))

        # Days of week
        ttk.Label(schedule_frame, text="Days to Run:").grid(row=1, column=0, sticky="nw", pady=5)
        days_frame = ttk.Frame(schedule_frame)
        days_frame.grid(row=1, column=1, sticky="w", padx=5)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        run_days = config.get("run_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

        self.day_vars = {}
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=day in run_days)
            self.day_vars[day] = var
            cb = ttk.Checkbutton(days_frame, text=day, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=5)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=20)
        ttk.Button(btn_frame, text="Save", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def save_settings(self):
        # Get selected days
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        if not selected_days:
            messagebox.showwarning("Warning", "Please select at least one day to run.")
            return

        run_time = f"{int(self.run_hour.get()):02d}:{int(self.run_minute.get()):02d}"

        self.config_dict.update({
            "app_id": self.app_id.get(),
            "dev_id": self.dev_id.get(),
            "cert_id": self.cert_id.get(),
            "gmail_email": self.gmail_email.get(),
            "gmail_app_password": self.gmail_pass.get(),
            "report_email": self.report_email.get(),
            "store_name": self.store_name.get(),
            "log_days": int(self.log_days.get()),
            "listings_per_run": int(self.listings_per_run.get()),
            "run_time": run_time,
            "run_days": selected_days,
        })
        save_config(self.config_dict)

        # Apply schedule to Windows Task Scheduler
        self.apply_schedule(run_time, selected_days)

        messagebox.showinfo("Success", "Settings saved and schedule updated!")
        self.on_save()
        self.destroy()

    def apply_schedule(self, run_time, run_days):
        """Apply the schedule to Windows Task Scheduler"""
        import subprocess
        import os

        script_path = BASE_DIR / "update_schedule.ps1"
        if not script_path.exists():
            messagebox.showwarning("Warning", "Schedule update script not found.")
            return

        try:
            # Build PowerShell command with admin elevation
            days_str = "', '".join(run_days)
            ps_cmd = f"""
            $script = '{script_path}'
            Start-Process powershell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $script, '-Time', '{run_time}', '-Days', @('{days_str}')) -Verb RunAs -WindowStyle Hidden -Wait
            """

            # Hide the PowerShell window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                timeout=10,
                startupinfo=startupinfo
            )
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not auto-update schedule: {e}\nYou may need to run with admin privileges.")

    def show_guide(self):
        guide_text = """SETTINGS QUICK GUIDE

API CREDENTIALS
• App ID, Dev ID, Cert ID: Obtain from eBay API account
  https://developer.ebay.com/
• These authenticate your relisting requests

EMAIL SETTINGS
• Gmail Email: Your Gmail account address
• Gmail App Password: 16-character password from Google Account
  (Settings → Security → App Passwords)
• Report Sent To: Email address to receive daily reports

STORE INFORMATION
• Store Name: Your eBay store name (displays in dashboard)

SCHEDULE SETTINGS
• Log Days to Display: How many days of activity logs to show
  on the main dashboard (default: 3 days)
• Listings to Execute Per Run: How many items to relist each
  time the agent runs (default: 10 items)
• Run Time: What time each day to automatically relist (HH:MM)
• Days to Run: Which days of the week the agent should run

SAVE & APPLY
Click Save to store all settings and automatically update the
Windows Task Scheduler with your new schedule.
"""
        QuickGuideWindow(self, "Settings", guide_text)


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Relist Agent")
        self.geometry("700x500")
        self.config = load_config()

        # Configure window background
        self.config(bg=BG_PRIMARY)

        # Configure global ttk style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TCheckbutton', background=BG_PRIMARY, foreground=TEXT_PRIMARY)

        # Set window icon
        icon_path = BASE_DIR / "ERA_Icon.png"
        if icon_path.exists():
            try:
                self.iconphoto(False, tk.PhotoImage(file=str(icon_path)))
            except Exception:
                pass

        # Header with logo
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)

        # Add logo if it exists
        logo_path = BASE_DIR / "ERA_Logo.png"
        self.logo_photo = None
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                logo_img = Image.open(str(logo_path))
                logo_img.thumbnail((120, 60), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                ttk.Label(header, image=self.logo_photo).pack(side="left", padx=10)
            except Exception:
                pass

        # Title and store info
        info_frame = ttk.Frame(header)
        info_frame.pack(side="left", fill="both", expand=True, padx=10)

        title_frame = ttk.Frame(info_frame)
        title_frame.pack(anchor="w")
        ttk.Label(title_frame, text="Relist Agent", font=("Arial", 14, "bold")).pack(side="left")
        ttk.Button(title_frame, text="ⓘ", width=3, command=self.show_main_guide).pack(side="left", padx=5)

        if self.config.get("store_name"):
            ttk.Label(info_frame, text=f"Store: {self.config['store_name']}", font=("Arial", 10)).pack(anchor="w")

        # Log area
        log_frame = ttk.LabelFrame(self, text="Activity Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=BLUE_PRIMARY)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert("end", "Loading...\n")
        self.log_text.config(state="disabled")

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Settings", command=self.open_settings).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="View Log", command=self.open_log_viewer).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_log).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Run Now", command=self.run_agent).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Inventory", command=self.open_inventory).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="About", command=self.show_about).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.quit).pack(side="left", padx=5)

        # Load log in background thread
        threading.Thread(target=self.refresh_log, daemon=True).start()

    def refresh_log(self):
        try:
            if not LOG_FILE.exists():
                self.update_log("No activity yet.")
                return

            with open(LOG_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)

            # Filter by log_days setting
            from datetime import datetime, timedelta
            log_days = self.config.get("log_days", 3)
            cutoff_date = (datetime.now() - timedelta(days=log_days)).date()

            filtered_entries = [
                e for e in entries
                if e.get("date") and e.get("date") >= cutoff_date.isoformat()
            ]

            self.log_text.config(state="normal")
            self.log_text.delete(1.0, "end")

            if not filtered_entries:
                self.log_text.insert("end", f"No activity in the last {log_days} days.")
                self.log_text.config(state="disabled")
                return

            # Header
            self.log_text.insert("end", f"{'Started':<20} {'Completed':<20} {'Status':<10} {'Old Item':<15} {'Title':<35}\n")
            self.log_text.insert("end", "=" * 110 + "\n")

            # Entries (sorted newest first)
            sorted_entries = sorted(filtered_entries, key=lambda x: (x.get("date", ""), x.get("start_time", "")), reverse=True)

            for entry in sorted_entries:
                start_time = entry.get("start_time", "?")
                end_time = entry.get("end_time", "?")
                status = entry.get("status", "?")
                old_id = entry.get("old_item_id") or entry.get("item_id", "?")
                title = entry.get("title", "")[:33]
                reason = entry.get("reason", "")

                if status == "relisted":
                    self.log_text.insert("end", f"{start_time:<20} {end_time:<20} {status:<10} {old_id:<15} {title:<35}\n")
                else:
                    self.log_text.insert("end", f"{start_time:<20} {end_time:<20} {status:<10} {old_id:<15} {title:<35}\n")
                    if reason:
                        self.log_text.insert("end", f"{'':40} Error: {reason}\n")

            self.log_text.config(state="disabled")
        except Exception as e:
            self.update_log(f"Error loading log: {e}")

    def update_log(self, text):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.insert("end", text)
        self.log_text.config(state="disabled")

    def open_settings(self):
        SettingsWindow(self, self.config, self.refresh_log)

    def run_agent(self):
        threading.Thread(target=self._run_agent_thread, daemon=True).start()

    def _run_agent_thread(self):
        try:
            self.update_log("Running agent...\n")
            result = subprocess.run(
                ["python", str(BASE_DIR / "ebay_relist_agent.py")],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode == 0:
                self.update_log("Agent completed successfully!\n\nRefreshing log...")
                self.after(1000, self.refresh_log)
            else:
                self.update_log(f"Agent error:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            self.update_log("Agent timeout")
        except Exception as e:
            self.update_log(f"Error: {e}")

    def open_log_viewer(self):
        LogViewerWindow(self)

    def show_about(self):
        messagebox.showinfo("About", "Relist Agent\n\nAutomatically relist your items daily.\n\nVersion 1.0\n\nSchedule your relists, track your activity, and manage your inventory with ease.")

    def show_main_guide(self):
        guide_text = """DASHBOARD QUICK GUIDE

ACTIVITY LOG
Shows your most recent relist activity. Displays:
• Started: Time when the relist began
• Completed: Time when the relist finished
• Status: Relisted (success) or Error (failed)
• Old Item: The item ID that was ended
• Title: The listing title

DASHBOARD BUTTONS

SETTINGS - Configure API credentials, email, schedule, and more

VIEW LOG - Open detailed log viewer to filter and search all
  historical relist activity by date, status, or keywords

REFRESH - Reload the activity log to see latest runs

RUN NOW - Execute the relist agent immediately (useful for
  testing or running outside the scheduled time)

INVENTORY - Browse all items in your store

ABOUT - View application information

EXIT - Close the application

TYPICAL WORKFLOW
1. Configure Settings with your eBay API credentials
2. Set your preferred run schedule
3. Agent will automatically run at scheduled times
4. Check Dashboard for activity and results
5. Use Inventory to browse your store
"""
        QuickGuideWindow(self, "Dashboard", guide_text)

    def open_inventory(self):
        InventoryWindow(self, self.config)


class InventoryWindow(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Store Inventory")
        self.geometry("1200x700")
        self.config(bg=BG_PRIMARY)
        self.config = config
        self.all_items = []

        # Configure ttk style for this window
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('Treeview', background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY)
        style.configure('Treeview.Heading', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('Treeview.Heading', background=[('active', BLUE_HOVER)])

        # Header with title and guide icon
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Store Inventory", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(header, text="ⓘ", width=3, command=self.show_guide).pack(side="left", padx=5)

        # Feature banner
        banner_frame = tk.Frame(self, bg=BANNER_BG, relief="solid", borderwidth=2, highlightthickness=0, bd=0)
        banner_frame.pack(fill="x", padx=0, pady=0)
        banner_frame.config(highlightbackground=BANNER_BORDER, highlightthickness=1)
        banner_label = tk.Label(
            banner_frame,
            text="✨ NEW: Click ❌ Delist or ♻️ Relist below to manually manage your listings",
            bg=BANNER_BG,
            fg=BANNER_FG,
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        )
        banner_label.pack(fill="x")

        # Info note
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(info_frame, text="ℹ️ First load fetches all item details (~1 min per 100 items). Future loads will be much faster thanks to caching.",
                  font=("Arial", 9), foreground=TEXT_SECONDARY).pack(anchor="w")
        ttk.Label(info_frame, text="💡 Double-click Item ID to open",
                  font=("Arial", 9), foreground=TEXT_SECONDARY).pack(anchor="w")

        # Search and controls frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_items)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)

        ttk.Button(search_frame, text="🔄 Refresh Data", command=self.refresh_data).pack(side="left", padx=5)

        ttk.Label(search_frame, text="Items:").pack(side="left", padx=20)
        self.item_count = ttk.Label(search_frame, text="Loading...")
        self.item_count.pack(side="left", padx=5)

        # Progress bar
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", padx=10, pady=5)
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", length=300)
        self.progress.pack(side="left", padx=5, fill="x", expand=True)
        self.progress_text = ttk.Label(progress_frame, text="")
        self.progress_text.pack(side="left", padx=5)

        # Table frame
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview with columns
        columns = ("Item ID", "Title", "Date Listed")
        self.tree = ttk.Treeview(table_frame, columns=columns, height=25)
        self.tree.column("#0", width=0, stretch="no")
        self.tree.column("Item ID", anchor="w", width=120)
        self.tree.column("Title", anchor="w", width=500)
        self.tree.column("Date Listed", anchor="center", width=180)

        for col in columns:
            self.tree.heading(col, text=col)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Bind double-click to open item
        self.tree.bind("<Double-1>", self.open_item)

        # Action buttons
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(action_frame, text="❌ Delist Selected", command=self.delist_selected).pack(side="left", padx=5)
        ttk.Button(action_frame, text="♻️ Relist Selected", command=self.relist_selected).pack(side="left", padx=5)

        # Load items in background
        threading.Thread(target=self.load_items, daemon=True).start()

    def load_items(self):
        try:
            from auth import get_access_token
            from ebay_api import fetch_all_active_listings

            token = get_access_token(self.config)

            # Load active listings
            self.all_items = fetch_all_active_listings(self.config, token)

            self.progress.config(maximum=1)
            self.progress["value"] = 0


            self.progress.config(value=0)
            self.progress_text.config(text="")
            self.filter_items()
            self.item_count.config(text=f"Loaded {len(self.all_items)} items")
        except Exception as e:
            self.item_count.config(text=f"Error loading items: {e}")

    def filter_items(self, *args):
        search_term = self.search_var.get().lower()

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter by title and SKU
        filtered = [
            item for item in self.all_items
            if search_term in item.get("title", "").lower() or
               search_term in item.get("sku", "").lower()
        ]

        for item in filtered:
            # Format date from ISO format to 12-hour time
            date_str = item.get("start_time", "")
            if date_str:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
                except:
                    formatted_date = date_str
            else:
                formatted_date = ""

            self.tree.insert("", "end", values=(
                item.get("item_id", ""),
                item.get("title", ""),
                formatted_date
            ))

        self.item_count.config(text=f"{len(filtered)} of {len(self.all_items)} items")

    def refresh_data(self):
        """Refresh inventory from eBay"""
        result = messagebox.askyesno(
            "Refresh Data",
            "Reload the inventory from eBay?"
        )
        if result:
            # Clear table
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Reload
            self.all_items = []
            self.progress["value"] = 0
            self.item_count.config(text="Loading...")
            threading.Thread(target=self.load_items, daemon=True).start()

    def open_item(self, event):
        import webbrowser
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            item_id = item["values"][0]
            url = f"https://www.ebay.com/itm/{item_id}"
            webbrowser.open(url)

    def delist_selected(self):
        """End the selected listing"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to delist")
            return

        item = self.tree.item(selection[0])
        item_id = item["values"][0]
        title = item["values"][1]

        confirm = messagebox.askyesno(
            "Confirm Delist",
            f"End listing: {title}?\n\nItem ID: {item_id}"
        )

        if confirm:
            try:
                from auth import get_access_token
                from ebay_api import end_item

                token = get_access_token(self.config)
                end_item(self.config, token, item_id)
                messagebox.showinfo("Success", f"Item {item_id} delisted successfully")
                # Reload inventory
                self.all_items = []
                self.filter_items()
                threading.Thread(target=self.load_items, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delist: {e}")

    def relist_selected(self):
        """Relist the selected item (delist old, create new)"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to relist")
            return

        item = self.tree.item(selection[0])
        item_id = item["values"][0]
        title = item["values"][1]

        confirm = messagebox.askyesno(
            "Confirm Relist",
            f"Relist: {title}?\n\nItem ID: {item_id}\n\nThis will end the current listing and create a new one with the same details"
        )

        if confirm:
            try:
                from auth import get_access_token
                from ebay_api import get_item, add_item, end_item

                token = get_access_token(self.config)

                # Get full item details FIRST (before delisting)
                details = get_item(self.config, token, item_id)

                # Delist the old item
                end_item(self.config, token, item_id)

                # Create new listing with same details
                new_item_id = add_item(self.config, token, details)

                messagebox.showinfo("Success", f"Listing refreshed!\n\nOld: {item_id}\nNew: {new_item_id}")

                # Reload inventory
                self.all_items = []
                self.filter_items()
                threading.Thread(target=self.load_items, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to relist: {e}")

    def show_guide(self):
        guide_text = """INVENTORY QUICK GUIDE

YOUR STORE ITEMS
Browse all active listings in your eBay store. Load is instant
since it uses eBay's basic listing data.

SEARCH
• Search by title
• Type to filter in real-time
• Case-insensitive search
• Example: search "Plant" finds "Plant Pots Set of 3"

COLUMNS

Item ID
• Unique eBay identifier
• Double-click to open the item on eBay.com in your browser

Title
• The listing title

Date Listed
• When the item was originally listed
• Format: MM/DD/YYYY HH:MM AM/PM

ACTIONS

❌ DELIST SELECTED
• Select an item in the list
• Click to end/delete the listing
• Requires confirmation before delisting

♻️ RELIST SELECTED
• Select an item in the list
• Click to automatically delist and relist with same details
• Uses current price, description, condition, shipping, etc.
• Old listing ends, new listing is created seamlessly

REFRESH DATA
Click to reload the inventory from eBay.

Item count shows: "X of Y items" where X is currently visible
after search filtering, and Y is total items in your store.
"""
        QuickGuideWindow(self, "Inventory", guide_text)


class LogViewerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Log Viewer - All Runs")
        self.geometry("900x600")
        self.config(bg=BG_PRIMARY)

        # Configure ttk style for this window
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY)

        # Header with title and guide icon
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Log Viewer", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(header, text="ⓘ", width=3, command=self.show_guide).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.LabelFrame(self, text="Filter", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(filter_frame, text="From Date:").grid(row=0, column=0, sticky="w")
        self.from_date = ttk.Entry(filter_frame, width=15)
        self.from_date.grid(row=0, column=1, sticky="w", padx=5)
        self.from_date.insert(0, "2026-01-01")

        ttk.Label(filter_frame, text="To Date:").grid(row=0, column=2, sticky="w")
        self.to_date = ttk.Entry(filter_frame, width=15)
        self.to_date.grid(row=0, column=3, sticky="w", padx=5)
        self.to_date.insert(0, "2099-12-31")

        ttk.Label(filter_frame, text="Status:").grid(row=0, column=4, sticky="w")
        self.status_var = tk.StringVar(value="All")
        status_box = ttk.Combobox(filter_frame, textvariable=self.status_var, values=["All", "Relisted", "Error"], width=10)
        status_box.grid(row=0, column=5, sticky="w", padx=5)

        ttk.Label(filter_frame, text="Search:").grid(row=0, column=6, sticky="w")
        self.search = ttk.Entry(filter_frame, width=20)
        self.search.grid(row=0, column=7, sticky="w", padx=5)

        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_filter).grid(row=0, column=8, padx=5)

        # Table frame
        table_frame = ttk.LabelFrame(self, text="History", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Text widget for log (with built-in scrollbars)
        self.log_display = scrolledtext.ScrolledText(table_frame, height=20, width=100, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=BLUE_PRIMARY)
        self.log_display.pack(fill="both", expand=True)

        # Load all data
        self.all_entries = []
        self.load_all_entries()
        self.apply_filter()

    def load_all_entries(self):
        try:
            if not LOG_FILE.exists():
                return
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                self.all_entries = json.load(f)
        except Exception as e:
            self.log_display.insert("end", f"Error loading log: {e}\n")

    def apply_filter(self):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        status = self.status_var.get()
        search = self.search.get().lower()

        self.log_display.config(state="normal")
        self.log_display.delete(1.0, "end")

        filtered = [
            e for e in self.all_entries
            if (from_date <= e.get("date", "") <= to_date) and
               (status == "All" or e.get("status", "").capitalize() == status) and
               (search == "" or search in str(e.get("title", "")).lower() or
                search in str(e.get("item_id", "")).lower() or
                search in str(e.get("old_item_id", "")).lower())
        ]

        if not filtered:
            self.log_display.insert("end", "No matching entries.\n")
            self.log_display.config(state="disabled")
            return

        # Header
        self.log_display.insert("end", f"{'Started':<20} {'Completed':<20} {'Status':<10} {'Old Item':<15} {'Title':<35}\n")
        self.log_display.insert("end", "=" * 110 + "\n")

        # Entries (sorted newest first)
        sorted_entries = sorted(filtered, key=lambda x: (x.get("date", ""), x.get("start_time", "")), reverse=True)

        for entry in sorted_entries:
            start_time = entry.get("start_time", "?")
            end_time = entry.get("end_time", "?")
            status = entry.get("status", "?")
            old_id = entry.get("old_item_id") or entry.get("item_id", "?")
            title = entry.get("title", "")[:33]
            reason = entry.get("reason", "")

            if status == "relisted":
                self.log_display.insert("end", f"{start_time:<20} {end_time:<20} {status:<10} {old_id:<15} {title:<35}\n")
            else:
                self.log_display.insert("end", f"{start_time:<20} {end_time:<20} {status:<10} {old_id:<15} {title:<35}\n")
                if reason:
                    self.log_display.insert("end", f"{'':40} Error: {reason}\n")

        self.log_display.config(state="disabled")

    def show_guide(self):
        guide_text = """LOG VIEWER QUICK GUIDE

FILTERING YOUR LOGS
Find specific relist activity using these filters:

FROM DATE / TO DATE
• Enter dates in YYYY-MM-DD format (e.g., 2026-06-01)
• Filters logs within the date range
• Default: 2026-01-01 to 2099-12-31 (all dates)

STATUS
• All: Shows all entries regardless of status
• Relisted: Only successful relists
• Error: Only failed attempts
• Helps identify problem items quickly

SEARCH
• Search by title, item ID, or old item ID
• Case-insensitive
• Enter partial text (e.g., "Plant" will find "Plant Pot")

APPLY FILTER
Click this button to filter the log based on your criteria.

READING THE LOG
Each entry shows:
• Started: Time the relist process began
• Completed: Time the relist process finished
• Status: relisted (success) or error (failed)
• Old Item: The item ID that was ended
• Title: The first 33 characters of the listing title

ERROR DETAILS
If an entry shows Error status, additional error details are
displayed on the next line explaining what went wrong.

SORTING
Logs are always sorted by newest first (most recent at the top).
"""
        QuickGuideWindow(self, "Log Viewer", guide_text)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
