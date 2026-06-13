#!/usr/bin/env python3
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import scrolledtext
from pathlib import Path
import threading
import webbrowser
import sys
import os
import urllib.request
from theme import *
from PIL import Image, ImageTk
from update_checker import check_for_updates

# Try to use curl_cffi for WAF bypass (TLS fingerprint spoofing)
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

# Handle both source and compiled EXE paths
if getattr(sys, 'frozen', False):
    # Running as compiled EXE - use directory of the running executable
    BASE_DIR = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    # Running as .py script - use script directory
    BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / ".ebay_relist_agent_data"
DATA_DIR.mkdir(exist_ok=True)  # Create hidden folder if it doesn't exist
# Make folder hidden on Windows
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetFileAttributesW(str(DATA_DIR), 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
LOG_FILE = DATA_DIR / "relist_log.json"

# Cache for info icon
_info_icon_cache = None

def get_info_icon(size=24):
    global _info_icon_cache
    if _info_icon_cache is not None:
        return _info_icon_cache

    icon_path = BASE_DIR / "INFO_ICON.png"
    if icon_path.exists():
        try:
            img = Image.open(str(icon_path))
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            _info_icon_cache = ImageTk.PhotoImage(img)
            return _info_icon_cache
        except Exception:
            return None
    return None


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


def is_admin():
    """Check if running with admin privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def restart_as_admin():
    """Restart the application with admin privileges"""
    try:
        import ctypes
        import sys
        import os

        # Get the path to the current script
        script_path = os.path.abspath(__file__)

        # Use ShellExecuteW to restart as admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)

        # Exit current process
        import sys
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error", f"Could not restart as admin:\n{e}")


def check_admin_on_startup():
    """Check if admin is needed and show popup if necessary"""
    if not is_admin():
        result = messagebox.askyesno(
            "Admin Setup Required",
            "eBay Relist Agent needs admin privileges to configure\n"
            "Windows Task Scheduler for automatic runs.\n\n"
            "Restart the app as admin? (one-time only)\n\n"
            "After restart, settings changes will update automatically.",
            icon=messagebox.QUESTION
        )
        if result:
            restart_as_admin()
        else:
            messagebox.showinfo(
                "Limited Functionality",
                "The app will run, but you won't be able to\n"
                "configure automatic scheduling.\n\n"
                "You can still use 'Run Now' manually."
            )


_icon_photo = None

def set_window_icon(window):
    """Set ERA icon on window using iconphoto"""
    global _icon_photo
    try:
        ico_path = BASE_DIR / "ERA_Icon.ico"
        if ico_path.exists():
            window.iconbitmap(str(ico_path))
    except Exception as e:
        pass


class QuickGuideWindow(tk.Toplevel):
    instance = None

    def __init__(self, parent, title, guide_text):
        if QuickGuideWindow.instance is not None:
            try:
                QuickGuideWindow.instance.lift()
                QuickGuideWindow.instance.focus()
                return
            except:
                QuickGuideWindow.instance = None

        super().__init__(parent)
        QuickGuideWindow.instance = self
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title(f"Quick Guide - {title}")
        self.geometry("600x500")
        self.config(bg=BG_PRIMARY)

        text_widget = scrolledtext.ScrolledText(self, height=25, width=70, wrap="word", font=("Arial", 10),
                                                bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=BLUE_PRIMARY)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("end", guide_text)
        text_widget.config(state="disabled")

    def _on_close(self):
        QuickGuideWindow.instance = None
        self.destroy()


class SettingsWindow(tk.Toplevel):
    instance = None

    def __init__(self, parent, config, on_save):
        if SettingsWindow.instance is not None:
            try:
                SettingsWindow.instance.lift()
                SettingsWindow.instance.focus()
                return
            except:
                SettingsWindow.instance = None

        super().__init__(parent)
        SettingsWindow.instance = self
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title("Settings")
        self.geometry("550x700")
        self.config_dict = config
        self.on_save = on_save
        self.config(bg=BG_PRIMARY)

        # Configure custom ttk style
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY, font=("Arial", 10))
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Vertical.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Horizontal.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.map('TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Vertical.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Horizontal.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])

        # Header with title and info icon
        header = ttk.Frame(self, style='TFrame')
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Settings", font=("Arial", 12, "bold")).pack(side="left")
        icon = get_info_icon(24)
        if icon:
            tk.Button(header, image=icon, command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)
        else:
            tk.Button(header, text="ⓘ", command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)

        # Form container
        form_frame = ttk.Frame(self)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # API Credentials
        ttk.Label(form_frame, text="App ID:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.app_id = ttk.Entry(form_frame, width=40, show="*")
        self.app_id.grid(row=0, column=1, padx=10, pady=5)
        self.app_id.insert(0, config.get("app_id", ""))

        ttk.Label(form_frame, text="Dev ID:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.dev_id = ttk.Entry(form_frame, width=40, show="*")
        self.dev_id.grid(row=1, column=1, padx=10, pady=5)
        self.dev_id.insert(0, config.get("dev_id", ""))

        ttk.Label(form_frame, text="Cert ID:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cert_id = ttk.Entry(form_frame, width=40, show="*")
        self.cert_id.grid(row=2, column=1, padx=10, pady=5)
        self.cert_id.insert(0, config.get("cert_id", ""))

        ttk.Label(form_frame, text="RU Name:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.ru_name = ttk.Entry(form_frame, width=40)
        self.ru_name.grid(row=3, column=1, padx=10, pady=5)
        self.ru_name.insert(0, config.get("ru_name", ""))

        # Gmail
        ttk.Label(form_frame, text="Gmail Email:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.gmail_email = ttk.Entry(form_frame, width=40)
        self.gmail_email.grid(row=4, column=1, padx=10, pady=5)
        self.gmail_email.insert(0, config.get("gmail_email", ""))

        ttk.Label(form_frame, text="Gmail App Password:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.gmail_pass = ttk.Entry(form_frame, width=40, show="*")
        self.gmail_pass.grid(row=5, column=1, padx=10, pady=5)
        self.gmail_pass.insert(0, config.get("gmail_app_password", ""))

        ttk.Label(form_frame, text="Report Sent To:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.report_email = ttk.Entry(form_frame, width=40)
        self.report_email.grid(row=6, column=1, padx=10, pady=5)
        self.report_email.insert(0, config.get("report_email", ""))

        # Store Name
        ttk.Label(form_frame, text="Store Name:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.store_name = ttk.Entry(form_frame, width=40)
        self.store_name.grid(row=7, column=1, padx=10, pady=5)
        self.store_name.insert(0, config.get("store_name", ""))

        # Log Days
        ttk.Label(form_frame, text="Log Days to Display:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.log_days = ttk.Spinbox(form_frame, from_=1, to=30, width=10)
        self.log_days.grid(row=8, column=1, sticky="w", padx=10, pady=5)
        self.log_days.set(config.get("log_days", 3))

        # Listings to Execute
        ttk.Label(form_frame, text="Listings to Execute Per Run:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.listings_per_run = ttk.Spinbox(form_frame, from_=1, to=50, width=10)
        self.listings_per_run.grid(row=9, column=1, sticky="w", padx=10, pady=5)
        self.listings_per_run.set(config.get("listings_per_run", 10))

        # Schedule Frame
        schedule_frame = tk.LabelFrame(form_frame, text="Schedule", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=("Arial", 10, "bold"), padx=10, pady=10, borderwidth=2, relief="solid", highlightthickness=0)
        schedule_frame.grid(row=10, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

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
        days_frame = tk.Frame(schedule_frame, bg=BG_PRIMARY)
        days_frame.grid(row=1, column=1, sticky="w", padx=5)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        run_days = config.get("run_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

        self.day_vars = {}
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=day in run_days)
            self.day_vars[day] = var
            cb = tk.Checkbutton(days_frame, text=day, variable=var, bg=BG_PRIMARY, fg=TEXT_PRIMARY,
                               activebackground="black", activeforeground=TEXT_PRIMARY, selectcolor=BLUE_PRIMARY,
                               font=("Arial", 10), relief="flat", borderwidth=0)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=5, pady=3)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=20)
        ttk.Button(btn_frame, text="Save", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Authorize Now", command=self.do_oauth_auth).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear Cache", command=self.clear_progress_cache).pack(side="left", padx=5)
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
            "ru_name": self.ru_name.get(),
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
        self._on_close()

    def apply_schedule(self, run_time, run_days):
        """Apply the schedule to Windows Task Scheduler via inline PowerShell"""
        import subprocess
        import sys

        messagebox.showinfo(
            "Schedule Updated",
            f"✓ Schedule configured:\n\n"
            f"⏰ Run Time: {run_time}\n"
            f"📅 Days: {', '.join(run_days)}\n\n"
            f"Changes take effect immediately."
        )

        try:
            script_path = str(BASE_DIR / "ebay_relist_agent.py")
            script_dir = str(BASE_DIR)
            python_exe = sys.executable

            # Build PowerShell command inline (no external files)
            ps_cmd = f"""
$taskName = 'eBayRelistAgent'
$pythonExe = '{python_exe}'
$script = '{script_path}'
$scriptDir = '{script_dir}'

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $script -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -Daily -At '{run_time}'
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
"""

            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                timeout=10,
                text=True
            )

            if result.returncode != 0:
                messagebox.showwarning("Warning", f"Schedule update had issues:\n{result.stderr}")
            else:
                print(f"[SETTINGS] Schedule updated: {run_time} on {', '.join(run_days)}")

        except Exception as e:
            messagebox.showwarning("Error", f"Failed to update schedule:\n{e}")

    def _cleanup_batch_file(self, batch_file):
        """Clean up temporary batch file"""
        try:
            if batch_file.exists():
                batch_file.unlink()
        except:
            pass

    def show_manual_schedule_command(self, run_time, run_days):
        """Show user the manual command to run as admin if auto-update fails"""
        script_path = BASE_DIR / "update_schedule.ps1"
        days_str = "', '".join(run_days)

        command = f"& '{script_path}' -Time '{run_time}' -Days @('{days_str}')"

        msg = f"""Schedule auto-update requires admin privileges.

Please run this command in PowerShell as Administrator:

{command}

Or copy this and paste it in an admin PowerShell window.

After running, the task will be scheduled for {run_time} on: {', '.join(run_days)}"""

        messagebox.showinfo("Manual Schedule Update Required", msg)

    def clear_progress_cache(self):
        """Clear the progress.json file to remove stale progress data"""
        from pathlib import Path
        progress_file = BASE_DIR / "progress.json"

        try:
            if progress_file.exists():
                progress_file.unlink()
                messagebox.showinfo("Success", "Progress cache cleared.\n\nStale progress data has been removed.")
            else:
                messagebox.showinfo("Info", "No cache to clear.\n\nProgress cache is already empty.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear cache: {e}")

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

CLEAR CACHE
• Clears stale progress data from the system
• Use this if progress shows stuck or duplicate entries
• One-click cleanup without restarting the application
• Shows confirmation when complete

SAVE & APPLY
Click Save to store all settings and automatically update the
Windows Task Scheduler with your new schedule.
"""
        QuickGuideWindow(self, "Settings", guide_text)

    def do_oauth_auth(self):
        """OAuth authorization - exactly mirrors interactive_setup() flow from auth.py"""
        try:
            from tkinter import simpledialog as sd
            import webbrowser
            import urllib.parse
            import requests
            import base64
            from datetime import datetime, timezone, timedelta
            from auth import save_tokens, OAUTH_AUTH_URL, OAUTH_TOKEN_URL, SCOPES

            # Verify all required credentials are present
            required = ["app_id", "cert_id", "dev_id", "ru_name"]
            missing = [f for f in required if not self.config_dict.get(f)]
            if missing:
                messagebox.showerror("Missing Credentials", f"Please fill in all required fields:\n{', '.join(missing)}")
                return

            # Build OAuth URL (exactly as _do_oauth() does in auth.py)
            auth_url = (
                f"{OAUTH_AUTH_URL}?client_id={urllib.parse.quote(self.config_dict['app_id'])}"
                f"&response_type=code"
                f"&redirect_uri={urllib.parse.quote(self.config_dict['ru_name'])}"
                f"&scope={urllib.parse.quote(SCOPES)}"
            )

            # Open browser
            messagebox.showinfo(
                "OAuth Authorization",
                "A browser window will open for eBay authorization.\n\n"
                "After you authorize the app, your browser will redirect to a page that fails to load.\n"
                "Copy the full URL from the address bar and paste it in the next dialog."
            )
            webbrowser.open(auth_url)

            # Ask user to paste redirect URL
            raw = sd.askstring(
                "Paste Authorization URL",
                "Copy the full URL from your browser's address bar and paste it below:"
            )
            if not raw:
                messagebox.showwarning("Cancelled", "OAuth authorization was cancelled.")
                return

            # Extract authorization code
            params = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
            if "code" not in params:
                messagebox.showerror("Error", "No 'code' found in the URL.\nMake sure you copied the entire URL from the address bar.")
                return
            code = params["code"][0]

            # Exchange code for tokens (exactly as _do_oauth() does)
            creds = base64.b64encode(f"{self.config_dict['app_id']}:{self.config_dict['cert_id']}".encode()).decode()
            resp = requests.post(
                OAUTH_TOKEN_URL,
                headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "authorization_code", "code": code, "redirect_uri": self.config_dict["ru_name"]},
                timeout=30,
            )
            if not resp.ok:
                messagebox.showerror("Error", f"Token exchange failed ({resp.status_code}):\n{resp.text}")
                return

            data = resp.json()
            if not data.get("refresh_token"):
                messagebox.showerror("Error", "eBay did not return a refresh token.\nCheck your app credentials and OAuth scopes are correct.")
                return

            # Save tokens (exactly as _do_oauth() does)
            now = datetime.now(timezone.utc)
            save_tokens({
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_at": (now + timedelta(seconds=data["expires_in"])).isoformat(),
            })

            messagebox.showinfo("Success", "✓ Authorization complete!\n\nTokens saved. You're ready to use the app.")

        except Exception as e:
            messagebox.showerror("Error", f"OAuth failed: {str(e)}")

    def _on_close(self):
        SettingsWindow.instance = None
        self.destroy()


class ExclusionsWindow(tk.Toplevel):
    instance = None

    def __init__(self, parent, config_dict, on_save=None, refresh_inventory_callback=None):
        if ExclusionsWindow.instance is not None:
            try:
                ExclusionsWindow.instance.lift()
                ExclusionsWindow.instance.focus()
                return
            except:
                ExclusionsWindow.instance = None

        super().__init__(parent)
        ExclusionsWindow.instance = self
        set_window_icon(self)
        self.title("Exclude from Relist")
        self.geometry("1000x700")
        self.config_dict = config_dict
        self.on_save = on_save
        self.refresh_inventory_callback = refresh_inventory_callback
        self.resizable(False, False)
        self.config(bg=BG_PRIMARY)
        self.sku_display_map = {}  # Map display text to SKU
        self.excluded_skus_set = set()  # Keep a reliable set of excluded SKUs in memory
        self.has_unsaved_changes = False

        # Warn if closing with unsaved changes
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Exclude from Relist", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(header, text="Save", command=self.save_exclusions).pack(side="right", padx=2)
        ttk.Button(header, text="Upload CSV/XLS", command=self.upload_exclusion_file).pack(side="right", padx=5)
        ttk.Button(header, text="Refresh Data", command=self.refresh_data).pack(side="right", padx=5)

        # Description
        desc = tk.Label(self, text="Upload a CSV/XLS file with SKUs, or manually select from the list below. Excel template: columns 'SKU' and 'Notes (optional)'.",
                       bg="#1a1a1a", fg=TEXT_PRIMARY, font=("Arial", 9), justify="left", wraplength=900)
        desc.pack(anchor="w", padx=20, pady=(0, 10))

        # Progress bar
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=300, value=0)
        self.progress_bar.pack(side="left", padx=5, fill="x", expand=True)
        self.progress_text = ttk.Label(progress_frame, text="Ready")
        self.progress_text.pack(side="left", padx=5)

        # Main content - SKUs only
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== SKU SECTION =====
        sku_section = tk.LabelFrame(main_frame, text="SKUs", bg=BG_PRIMARY, fg=TEXT_PRIMARY,
                                    font=("Arial", 10, "bold"), padx=10, pady=10, borderwidth=2, relief="solid",
                                    highlightthickness=0)
        sku_section.pack(fill="both", expand=True)

        sku_frame = ttk.Frame(sku_section)
        sku_frame.pack(fill="both", expand=True)

        # Available SKUs (left)
        left_sku_frame = tk.LabelFrame(sku_frame, text="Available", bg=BG_PRIMARY, fg=TEXT_PRIMARY,
                                       font=("Arial", 9, "bold"), padx=5, pady=5, borderwidth=1)
        left_sku_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Search field
        ttk.Label(left_sku_frame, text="Search:").pack(anchor="w")
        self.sku_search = ttk.Entry(left_sku_frame, width=20)
        self.sku_search.pack(anchor="w", pady=(0, 5))
        self.sku_search.bind("<KeyRelease>", self.filter_available_skus)

        sku_scrollbar_left = ttk.Scrollbar(left_sku_frame)
        sku_scrollbar_left.pack(side="right", fill="y")

        self.available_skus = tk.Listbox(left_sku_frame, bg=BG_SECONDARY, fg=TEXT_PRIMARY,
                                         yscrollcommand=sku_scrollbar_left.set, height=12)
        self.available_skus.pack(side="left", fill="both", expand=True)
        sku_scrollbar_left.config(command=self.available_skus.yview)

        # Buttons in middle
        middle_sku_frame = ttk.Frame(sku_frame)
        middle_sku_frame.pack(side="left", padx=5)
        ttk.Button(middle_sku_frame, text="Select All\nExcluded", command=self.select_all_excluded, width=10).pack(fill="x", pady=3)
        ttk.Button(middle_sku_frame, text="← Include", command=self.include_sku).pack(fill="x", pady=3)
        ttk.Button(middle_sku_frame, text="→ Exclude", command=self.exclude_sku).pack(fill="x", pady=3)
        ttk.Button(middle_sku_frame, text="Select All\nAvailable", command=self.select_all_skus, width=10).pack(fill="x", pady=3)

        # Excluded SKUs (right)
        right_sku_frame = tk.LabelFrame(sku_frame, text="Excluded", bg=BG_PRIMARY, fg=TEXT_PRIMARY,
                                        font=("Arial", 9, "bold"), padx=5, pady=5, borderwidth=1)
        right_sku_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        sku_scrollbar_right = ttk.Scrollbar(right_sku_frame)
        sku_scrollbar_right.pack(side="right", fill="y")

        self.excluded_skus = tk.Listbox(right_sku_frame, bg=BG_SECONDARY, fg=TEXT_PRIMARY,
                                        yscrollcommand=sku_scrollbar_right.set, height=12)
        self.excluded_skus.pack(side="left", fill="both", expand=True)
        sku_scrollbar_right.config(command=self.excluded_skus.yview)

        # Load initial data (load excluded first so they're excluded from available list)
        self.load_excluded_from_config()  # Load previously saved exclusions
        self.load_skus_from_store()
        self.has_unsaved_changes = False  # Track if user has made changes without saving

    def _on_closing(self):
        """Handle window close - warn if unsaved changes"""
        if self.has_unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Close without saving?"):
                ExclusionsWindow.instance = None
                self.destroy()
        else:
            ExclusionsWindow.instance = None
            self.destroy()

    def refresh_data(self):
        """Refresh data from store (with or without Inventory window)"""
        self.progress_bar.config(value=0)
        self.progress_text.config(text="Refreshing...")
        self.update_idletasks()
        try:
            if self.refresh_inventory_callback:
                # Use callback if Inventory window is open (for efficiency)
                self.refresh_inventory_callback(force_refresh=True)
            else:
                # Fetch inventory directly if Inventory window not open
                from auth import get_access_token, load_config
                from ebay_api import fetch_all_active_listings
                cfg = load_config()
                token = get_access_token(cfg)
                self.progress_text.config(text="Fetching inventory...")
                self.update_idletasks()
                items = fetch_all_active_listings(cfg, token)
                # Save full items with title for display
                cache_file = self._get_cache_file()
                cache_data = {"items": items}
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)

            # Reload from cache after refresh
            self.load_skus_from_store()
            self.refresh_excluded_titles()  # Also refresh titles for excluded items
            self.progress_bar.config(value=100)
            self.progress_text.config(text="Done")
            messagebox.showinfo("Success", "Data refreshed from store")
        except Exception as e:
            self.progress_bar.config(value=0)
            self.progress_text.config(text="Ready")
            messagebox.showerror("Error", f"Refresh failed: {str(e)}")

    def _get_cache_file(self):
        return DATA_DIR / "available_for_exclusions.json"

    def refresh_excluded_titles(self):
        """Update excluded items display with titles from refreshed cache"""
        try:
            cache = self._load_cache()
            items = cache.get("items", [])

            # Build SKU -> Title map from cache
            sku_to_title = {}
            for item in items:
                sku = item.get("sku", "").strip()
                if sku:
                    sku_to_title[sku] = item.get("title", "").strip()[:60]

            # Update excluded items display with titles
            excluded_count = self.excluded_skus.size()
            new_items = []
            for idx in range(excluded_count):
                display_text = self.excluded_skus.get(idx)
                sku = display_text.split(" - ")[0] if " - " in display_text else display_text

                # Try to get title from cache
                title = sku_to_title.get(sku, "")
                if title:
                    new_display = f"{sku} - {title}"
                else:
                    new_display = sku

                new_items.append(new_display)
                self.sku_display_map[new_display] = sku

            # Rebuild excluded list with new titles
            self.excluded_skus.delete(0, tk.END)
            for item in new_items:
                self.excluded_skus.insert(tk.END, item)
        except:
            pass  # Graceful failure if cache doesn't have items

    def _write_debug_log(self, log_lines):
        """Write debug logs to file"""
        try:
            debug_file = DATA_DIR / "exclusions_debug.log"
            with open(debug_file, "a", encoding="utf-8") as f:
                import datetime
                f.write(f"\n=== {datetime.datetime.now().isoformat()} ===\n")
                for line in log_lines:
                    f.write(line + "\n")
        except:
            pass

    def _load_cache(self):
        """Load cached items (SKU + Title)"""
        cache_file = self._get_cache_file()
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"items": []}

    def select_all_skus(self):
        """Select all available SKUs"""
        self.available_skus.select_set(0, tk.END)

    def select_all_excluded(self):
        """Select all excluded SKUs"""
        self.excluded_skus.select_set(0, tk.END)

    def upload_exclusion_file(self):
        """Upload CSV or XLS file with SKUs to exclude"""
        from tkinter import filedialog
        file = filedialog.askopenfile(
            title="Select CSV or XLS file with SKUs",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not file:
            return

        try:
            skus_to_add = []
            filename = file.name
            file.close()

            if filename.endswith('.csv'):
                import csv
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sku = row.get('SKU', row.get('sku', '')).strip()
                        title = row.get('Title', row.get('title', '')).strip()
                        if sku:
                            display_text = f"{sku} - {title}" if title else sku
                            skus_to_add.append((sku, display_text))
            else:  # XLS/XLSX
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(filename)
                    ws = wb.active
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        sku = str(row[0] or '').strip()
                        title = str(row[1] or '').strip() if len(row) > 1 else ''
                        if sku and sku.lower() != 'sku':
                            display_text = f"{sku} - {title}" if title else sku
                            skus_to_add.append((sku, display_text))
                except ImportError:
                    messagebox.showerror("Error", "openpyxl not installed. Please use CSV format instead.")
                    return

            # Add to excluded list
            for sku, display_text in skus_to_add:
                if sku not in [s.split(" - ")[0] if " - " in s else s for s in self.excluded_skus.get(0, tk.END)]:
                    self.excluded_skus.insert(tk.END, display_text)

            messagebox.showinfo("Success", f"Added {len(skus_to_add)} SKUs from file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")

    def load_skus_from_store(self):
        """Load SKUs with titles from cache"""
        debug_log = []
        cache = self._load_cache()
        items = cache.get("items", [])
        debug_log.append(f"load_skus_from_store: Found {len(items)} items in cache")

        # Use in-memory excluded SKUs set instead of extracting from display text
        excluded_skus = getattr(self, 'excluded_skus_set', set())
        debug_log.append(f"load_skus_from_store: Using in-memory excluded set with {len(excluded_skus)} SKUs")
        debug_log.append(f"  Excluded SKUs in memory: {list(excluded_skus)[:5]}")

        self.available_skus.delete(0, tk.END)
        self.sku_display_map = {}  # Map display text back to SKU

        added_count = 0
        excluded_count = 0
        for item in items:
            sku = item.get("sku", "").strip()
            title = item.get("title", "").strip()[:60]  # Truncate long titles
            if sku:
                display_text = f"{sku} - {title}" if title else sku
                if sku not in excluded_skus:
                    self.available_skus.insert(tk.END, display_text)
                    self.sku_display_map[display_text] = sku
                    added_count += 1
                else:
                    excluded_count += 1

        debug_log.append(f"load_skus_from_store: Added {added_count} to available, excluded {excluded_count}")
        self._write_debug_log(debug_log)

        if not items:
            self.available_skus.insert(tk.END, "(No SKUs found in store)")

    def load_excluded_from_config(self):
        """Load previously saved excluded items from persistent file (with titles)"""
        debug_log = []
        try:
            # First try to load from excluded_items.json (has titles)
            excluded_items_file = DATA_DIR / "excluded_items.json"
            excluded_display_texts = []

            if excluded_items_file.exists():
                try:
                    with open(excluded_items_file, "r", encoding="utf-8") as f:
                        excluded_data = json.load(f)
                        excluded_display_texts = excluded_data.get("items", [])
                    debug_log.append(f"load_excluded_from_config: Loaded {len(excluded_display_texts)} items from excluded_items.json")
                except:
                    debug_log.append("load_excluded_from_config: Failed to load excluded_items.json, falling back to config")

            # If excluded_items.json doesn't exist, fall back to config (SKU only)
            if not excluded_display_texts:
                from auth import load_config
                cfg = load_config()
                excluded_skus_list = cfg.get("excluded_skus", [])
                excluded_display_texts = excluded_skus_list
                debug_log.append(f"load_excluded_from_config: Loaded {len(excluded_display_texts)} SKUs from config (no titles)")

            # Populate excluded_skus listbox with saved exclusions
            self.excluded_skus.delete(0, tk.END)
            self.sku_display_map = getattr(self, 'sku_display_map', {})
            self.excluded_skus_set = set()  # Clear and rebuild the in-memory set

            loaded_count = 0
            for display_text in excluded_display_texts:
                self.excluded_skus.insert(tk.END, display_text)
                # Extract SKU and add to set
                sku = display_text.split(" - ")[0] if " - " in display_text else display_text
                self.sku_display_map[display_text] = sku
                self.excluded_skus_set.add(sku)
                loaded_count += 1
            debug_log.append(f"load_excluded_from_config: Loaded {loaded_count} items into UI and memory set")

            # Write logs to file
            self._write_debug_log(debug_log)
        except Exception as e:
            debug_log.append(f"load_excluded_from_config ERROR: {e}")
            import traceback
            debug_log.append(traceback.format_exc())
            self._write_debug_log(debug_log)

    def refresh_skus_cache(self):
        """Trigger complete refresh (inventory + exclusions cache)"""
        self.progress_bar.config(value=0)
        self.progress_text.config(text="Loading...")
        self.update_idletasks()

        if self.refresh_inventory_callback:
            try:
                self.refresh_inventory_callback(force_refresh=True)
                self.load_categories_from_store()
                self.load_skus_from_store()
                self.progress_bar.config(value=0)
                self.progress_text.config(text="Ready")
                messagebox.showinfo("Success", "Refreshed all data: Inventory, Categories, and SKUs")
            except Exception as e:
                self.progress_bar.config(value=0)
                self.progress_text.config(text="Ready")
                messagebox.showerror("Error", f"Refresh failed: {str(e)[:100]}")
        else:
            # Fallback: fetch directly without updating inventory
            try:
                categories, skus = self._fetch_from_store()
                self._save_cache(categories, skus)
                self.load_categories_from_store()
                self.load_skus_from_store()
                self.progress_bar.config(value=0)
                self.progress_text.config(text="Ready")
                messagebox.showinfo("Success", f"Loaded {len(categories)} categories and {len(skus)} SKUs\n(Open Inventory for full sync)")
            except Exception as e:
                self.progress_bar.config(value=0)
                self.progress_text.config(text="Ready")
                messagebox.showerror("Error", f"Fetch failed: {str(e)[:100]}")

    def filter_available_skus(self, event=None):
        """Filter SKUs based on search (SKU or title)"""
        search_term = self.sku_search.get().lower()
        cache = self._load_cache()
        items = cache.get("items", [])
        excluded_skus = set(self.excluded_skus.get(0, tk.END))

        self.available_skus.delete(0, tk.END)
        self.sku_display_map = {}

        for item in items:
            sku = item.get("sku", "").strip()
            title = item.get("title", "").strip()[:60]
            if sku and sku not in excluded_skus:
                if search_term in sku.lower() or search_term in title.lower():
                    display_text = f"{sku} - {title}" if title else sku
                    self.available_skus.insert(tk.END, display_text)
                    self.sku_display_map[display_text] = sku

        if not self.available_skus.get(0, tk.END):
            self.available_skus.insert(tk.END, "(No matches)")

    def exclude_sku(self):
        """Move selected SKUs from available to excluded"""
        selection = self.available_skus.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a SKU to exclude.")
            return
        # Process in reverse order to avoid index shifting
        for idx in reversed(selection):
            display_text = self.available_skus.get(idx)
            if display_text.startswith("Error") or display_text.startswith("("):
                continue
            # Extract actual SKU from display text
            sku = self.sku_display_map.get(display_text, display_text.split(" - ")[0])
            self.available_skus.delete(idx)
            if sku not in self.excluded_skus.get(0, tk.END):
                # Display with title in excluded list too
                title_part = display_text.split(" - ", 1)[1] if " - " in display_text else ""
                excluded_display = f"{sku} - {title_part}" if title_part else sku
                self.excluded_skus.insert(tk.END, excluded_display)
                self.excluded_skus_set.add(sku)  # Add to in-memory set
        self.has_unsaved_changes = True

    def include_sku(self):
        """Move selected SKUs from excluded to available"""
        selection = self.excluded_skus.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a SKU to include.")
            return
        # Process in reverse order to avoid index shifting
        for idx in reversed(selection):
            excluded_display = self.excluded_skus.get(idx)
            # Extract SKU from display text
            sku = excluded_display.split(" - ")[0] if " - " in excluded_display else excluded_display
            self.excluded_skus.delete(idx)
            self.excluded_skus_set.discard(sku)  # Remove from in-memory set
            # Add back to available list with title if present
            if sku not in self.available_skus.get(0, tk.END):
                self.available_skus.insert(tk.END, excluded_display)
                self.sku_display_map[excluded_display] = sku
        self.has_unsaved_changes = True

    def save_exclusions(self):
        """Save exclusions with confirmation"""
        excluded_displays = list(self.excluded_skus.get(0, tk.END))
        excluded_displays = [s for s in excluded_displays if not s.startswith("Error") and not s.startswith("(No")]

        # Extract SKUs from display text
        excluded_skus = []
        for display in excluded_displays:
            sku = display.split(" - ")[0] if " - " in display else display
            excluded_skus.append(sku)

        # DEBUG: Log what we're about to save
        debug_info = [
            f"SAVE_EXCLUSIONS - Listbox has {self.excluded_skus.size()} items",
            f"  Displays to save: {excluded_displays}",
            f"  SKUs to save: {excluded_skus}",
            f"  excluded_skus_set in memory: {self.excluded_skus_set}"
        ]
        self._write_debug_log(debug_info)

        # Show confirmation
        msg = f"""Save these exclusions?

SKUs to exclude ({len(excluded_skus)}):
{', '.join(excluded_skus[:5])}{'...' if len(excluded_skus) > 5 else ''}
"""
        if messagebox.askyesno("Confirm Exclusions", msg):
            self.config_dict.update({
                "excluded_skus": sorted(set(excluded_skus)),
            })
            save_config(self.config_dict)

            # Also save the display format (SKU - Title) to persistent file
            # This way titles load without needing to refresh data from store
            try:
                excluded_items_file = DATA_DIR / "excluded_items.json"
                with open(excluded_items_file, "w", encoding="utf-8") as f:
                    json.dump({"items": excluded_displays}, f, indent=2)
                self._write_debug_log([f"  Saved to {excluded_items_file.name}: {len(excluded_displays)} items"])
            except Exception as e:
                self._write_debug_log([f"  ERROR saving to {excluded_items_file.name}: {e}"])

            messagebox.showinfo("Success", "Exclusion settings saved!")
            self.has_unsaved_changes = False
            if self.on_save:
                self.on_save()
            ExclusionsWindow.instance = None
            self.destroy()


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        set_window_icon(self)
        self.title("Relist Agent")

        # Bring window to front after admin dialog - call multiple times to overcome UAC
        self.after(500, self.bring_to_front)
        self.after(1000, self.bring_to_front)
        self.after(1500, self.bring_to_front)
        self.geometry("700x500")
        self.app_config = load_config()

        # Configure window background
        tk.Tk.config(self, bg=BG_PRIMARY)

        # Configure global ttk style
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY, bordercolor=BG_TERTIARY, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TCheckbutton', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Vertical.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Horizontal.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.map('TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Vertical.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Horizontal.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])

        # Set window icon
        icon_path = BASE_DIR / "ERA_Icon.png"
        if icon_path.exists():
            try:
                self.iconphoto(False, tk.PhotoImage(file=str(icon_path)))
            except Exception:
                pass

        # Configure grid layout
        self.columnconfigure(0, weight=0, minsize=180)  # Left column
        self.columnconfigure(1, weight=1)              # Center column (expands)
        self.columnconfigure(2, weight=0, minsize=150) # Right column
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        # ===== LEFT COLUMN =====
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Logo section
        logo_frame = ttk.Frame(left_frame)
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
            self.store_label = tk.Label(left_frame, text=self.app_config['store_name'],
                                  font=("Arial", 12, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, wraplength=150, justify="left")
            self.store_label.pack(anchor="w", fill="x", pady=(0, 10))

        # Divider
        divider = tk.Frame(left_frame, height=1, bg=BG_TERTIARY)
        divider.pack(fill="x", pady=10)

        # Status section
        status_label = ttk.Label(left_frame, text="Status", font=("Arial", 10, "bold"))
        status_label.pack(anchor="w", pady=(0, 3))

        self.status_text = tk.Label(left_frame, text="Ready", font=("Arial", 9), bg=BG_PRIMARY, fg="#00DD00", wraplength=150)
        self.status_text.pack(anchor="w", fill="x", pady=(0, 5))

        # Current item section
        self.current_item_label = tk.Label(left_frame, text="", font=("Arial", 8), bg=BG_PRIMARY, fg=TEXT_SECONDARY, wraplength=150, justify="left")
        self.current_item_label.pack(anchor="w", fill="x", pady=(0, 3))

        # Current item progress
        self.progress_label = tk.Label(left_frame, text="", font=("Arial", 9, "bold"), bg=BG_PRIMARY, fg=BLUE_PRIMARY)
        self.progress_label.pack(anchor="w", fill="x", pady=(0, 3))

        # Current item progress bar
        self.progress_bar = ttk.Progressbar(left_frame, length=150, mode="determinate", value=0)
        self.progress_bar.pack(anchor="w", fill="x", pady=(0, 8))

        # Process stage indicator
        self.stage_label = tk.Label(left_frame, text="", font=("Arial", 12), bg=BG_PRIMARY, fg=BLUE_PRIMARY, wraplength=150, justify="center")
        self.stage_label.pack(anchor="w", fill="x", pady=(0, 3))

        # Stage dots (visual indicator)
        self.stage_dots = tk.Label(left_frame, text="", font=("Arial", 8), bg=BG_PRIMARY, fg=TEXT_SECONDARY, justify="center")
        self.stage_dots.pack(anchor="w", fill="x", pady=(0, 10))

        # Overall job progress divider
        divider3 = tk.Frame(left_frame, height=1, bg=BG_TERTIARY)
        divider3.pack(fill="x", pady=8)

        # Overall progress label
        ttk.Label(left_frame, text="Overall", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 3))

        # Overall progress counter (e.g., "7/10")
        self.overall_label = tk.Label(left_frame, text="", font=("Arial", 9, "bold"), bg=BG_PRIMARY, fg="#00DD00")
        self.overall_label.pack(anchor="w", fill="x", pady=(0, 3))

        # Overall progress bar
        self.overall_progress_bar = ttk.Progressbar(left_frame, length=150, mode="determinate", value=0)
        self.overall_progress_bar.pack(anchor="w", fill="x")

        # ===== CENTER COLUMN =====
        center_frame = ttk.Frame(self)
        center_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 10), pady=10)

        # Header with title and info icon
        header = ttk.Frame(center_frame)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Activity Log", font=("Arial", 12, "bold")).pack(side="left")
        icon = get_info_icon(24)
        if icon:
            tk.Button(header, image=icon, command=self.show_main_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)
        else:
            tk.Button(header, text="ⓘ", command=self.show_main_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)

        # Timing note
        ttk.Label(center_frame, text="⏱ Each listing takes 1–2 minutes (delists before relisting)", font=("Arial", 9), foreground="#CCCCCC").pack(anchor="w", pady=(0, 3))

        # Stalled item note
        ttk.Label(center_frame, text="💡 If you see a stalled 'Completed' item, click Refresh to clear it", font=("Arial", 8), foreground="#999999").pack(anchor="w", pady=(0, 8))

        # Log area
        log_frame = tk.LabelFrame(center_frame, text="", bg=BG_PRIMARY, fg=TEXT_PRIMARY, padx=8, pady=8, borderwidth=1, relief="solid", highlightthickness=0)
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

        # Prevent concurrent refresh calls
        self.refresh_lock = False

        # Track if agent is running
        self.is_running = False

        # Bind row selection to detect errors
        # log_tree selection binding removed (retry feature removed)

        # ===== RIGHT COLUMN =====
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=2, sticky="new", padx=10, pady=10)

        # Quick actions label
        ttk.Label(right_frame, text="Quick Actions", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Action buttons (vertical stack)
        self.run_button = ttk.Button(right_frame, text="Run Now", command=self.run_agent, width=14)
        self.run_button.pack(fill="x", pady=3)
        ttk.Button(right_frame, text="Inventory", command=self.open_inventory, width=14).pack(fill="x", pady=3)
        self.refresh_btn = ttk.Button(right_frame, text="Refresh", command=self.refresh_log, width=14)
        self.refresh_btn.pack(fill="x", pady=3)
        ttk.Button(right_frame, text="View Log", command=self.open_log_viewer, width=14).pack(fill="x", pady=3)

        # Divider
        divider2 = tk.Frame(right_frame, height=1, bg=BG_TERTIARY)
        divider2.pack(fill="x", pady=10)

        # Settings section
        ttk.Label(right_frame, text="Settings", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Button(right_frame, text="Configure", command=self.open_settings, width=14).pack(fill="x", pady=3)
        ttk.Button(right_frame, text="Exclude from Relist", command=self.open_exclusions, width=14).pack(fill="x", pady=3)
        ttk.Button(right_frame, text="Instructions", command=self.show_instructions, width=14).pack(fill="x", pady=3)
        ttk.Button(right_frame, text="About", command=self.show_about, width=14).pack(fill="x", pady=3)

        # Update status button
        self.update_button = ttk.Button(right_frame, text="Check for Updates", command=self.check_updates_manual, width=14)
        self.update_button.pack(fill="x", pady=3)

        ttk.Button(right_frame, text="Exit", command=self.quit, width=14).pack(fill="x", pady=3)
        ttk.Button(right_frame, text="Stop Service", command=self.stop_service, width=14).pack(fill="x", pady=3)

        # Version label
        ttk.Label(right_frame, text="v1.0.4", font=("Arial", 9), foreground="gray").pack(pady=(10, 0))

        # Bottom action buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        # Placeholder for potential bottom-level controls

        # Load log and check error items in background thread
        threading.Thread(target=self.startup_check, daemon=True).start()

        # Check for updates on startup
        self.check_updates_startup()

        # Start auto-refresh polling
        self.auto_refresh_activity_log()

    def bring_to_front(self):
        """Bring window to foreground after admin dialog"""
        try:
            import ctypes
            # Get this window's handle
            hwnd = self.winfo_id()

            # BringWindowToTop is more forceful than SetWindowPos
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)

            # Make permanently topmost until user interacts
            self.attributes('-topmost', True)

            # Release topmost on first user interaction
            def on_focus_in(event):
                try:
                    self.attributes('-topmost', False)
                    self.unbind("<FocusIn>")
                except:
                    pass

            self.bind("<FocusIn>", on_focus_in)
        except:
            pass

    def refresh_log(self):
        # Prevent overlapping refresh calls
        if self.refresh_lock:
            print("[REFRESH] Already refreshing, skipping duplicate call")
            return

        self.refresh_lock = True
        print("[REFRESH] Starting refresh_log()")

        try:
            # Show feedback
            self.refresh_btn.config(text="Refreshing...")
            self.update()
            print("[REFRESH] Button updated to 'Refreshing...'")
        except Exception as e:
            print(f"[REFRESH ERROR] Failed to update button: {e}")

        try:
            # Clear existing items
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)

            from datetime import datetime, timedelta
            from pathlib import Path

            PROGRESS_FILE = DATA_DIR / "progress.json"
            all_entries = []

            # Check for current running item from progress.json
            running_entry = None
            if PROGRESS_FILE.exists():
                try:
                    with open(PROGRESS_FILE, encoding="utf-8") as f:
                        progress_data = json.load(f)
                        stage = progress_data.get("stage", "")
                        item_id = progress_data.get("item_id", "")
                        title = progress_data.get("title", "")
                        timestamp = progress_data.get("timestamp", "")

                        # Extract time from ISO timestamp
                        if timestamp and "T" in timestamp:
                            start_time = timestamp.split("T")[1][:8]  # HH:MM:SS
                        else:
                            start_time = "..."

                        if stage and item_id:
                            running_entry = (start_time, "", f"▶ {stage}", item_id, title, "running")
                except:
                    pass

            if LOG_FILE.exists():
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    entries = json.load(f)

                # Filter by log_days setting
                log_days = self.app_config.get("log_days", 3)
                cutoff_date = (datetime.now() - timedelta(days=log_days)).date()

                filtered_entries = [
                    e for e in entries
                    if e.get("date") and e.get("date") >= cutoff_date.isoformat()
                ]

                # Convert entries to tuple format with extracted times
                for entry in filtered_entries:
                    start_time = entry.get("start_time", "?")
                    end_time = entry.get("end_time", "?")
                    status = entry.get("status", "?")
                    old_id = entry.get("old_item_id") or entry.get("item_id", "?")
                    title = entry.get("title", "")
                    reason = entry.get("reason", "")

                    # Extract just the time portion if it's a full datetime
                    if start_time and " " in start_time:
                        start_time = start_time.split(" ")[1]
                    if end_time and " " in end_time:
                        end_time = end_time.split(" ")[1]

                    # Determine tag based on status
                    if status == "relisted":
                        tag = "success"
                    elif status == "error":
                        tag = "error"
                    else:
                        tag = ""

                    # Add entry with sort key (date + time)
                    sort_key = (entry.get("date", ""), start_time)
                    all_entries.append((sort_key, (start_time, end_time, status, old_id, title, tag)))

                    # Track error reasons and status
                    if reason and status == "error":
                        error_msg = f"Error: {reason}"
                        all_entries.append((sort_key, ("", "", "", "", error_msg, "error_detail")))

                    # Add status indicator for error items
                    if status == "error":
                        is_active = entry.get("_is_active", None)
                        if is_active is True:
                            status_line = f"[ACTIVE] Item still active - can retry"
                            all_entries.append((sort_key, ("", "", "", "", status_line, "error_active")))
                        elif is_active is False:
                            status_line = f"[CLOSED] Item already closed - cannot retry"
                            all_entries.append((sort_key, ("", "", "", "", status_line, "error_closed")))

            # Sort by time (newest first)
            all_entries.sort(key=lambda x: x[0], reverse=True)

            # Insert running item first if it exists
            if running_entry:
                self.log_tree.insert("", "end", values=running_entry[:-1], tags=(running_entry[-1],))

            # Insert historical entries in sorted order
            for sort_key, (start_time, end_time, status, old_id, title, tag) in all_entries:
                values = (start_time, end_time, status, old_id, title)
                self.log_tree.insert("", "end", values=values, tags=(tag,))

            # Configure row tags for styling
            self.log_tree.tag_configure("success", foreground="#00DD00")
            self.log_tree.tag_configure("error", foreground="#FF4444")
            self.log_tree.tag_configure("error_detail", foreground="#FF8888")
            self.log_tree.tag_configure("error_active", foreground="#00CC88")  # Green - can retry
            self.log_tree.tag_configure("error_closed", foreground="#888888")  # Gray - cannot retry
            self.log_tree.tag_configure("running", foreground=YELLOW_PRIMARY)

            # Reset button feedback
            self.refresh_btn.config(text="Refresh")
            print("[REFRESH] Completed successfully")

        except Exception as e:
            # Reset button even on error
            self.refresh_btn.config(text="Refresh")
            print(f"[REFRESH ERROR] {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())

        finally:
            # Always unlock when done
            self.refresh_lock = False
            print("[REFRESH] Lock released")

    def cleanup_old_logs(self, keep_days=30):
        """Delete log entries older than keep_days (default 30 days)"""
        try:
            if not LOG_FILE.exists():
                return

            with open(LOG_FILE, "r", encoding="utf-8") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    return

            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=keep_days)).date()

            # Separate old and new entries
            old_entries = []
            new_entries = []

            for entry in entries:
                entry_date_str = entry.get("date", "")
                if entry_date_str:
                    try:
                        entry_date = datetime.fromisoformat(entry_date_str).date()
                        if entry_date < cutoff_date:
                            old_entries.append(entry)
                        else:
                            new_entries.append(entry)
                    except (ValueError, TypeError):
                        # If date parsing fails, keep the entry
                        new_entries.append(entry)
                else:
                    new_entries.append(entry)

            # Only update if there are old entries to remove
            if old_entries:
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_entries, f, indent=2)

                print(f"[DEBUG] Log cleanup: removed {len(old_entries)} entries older than {keep_days} days")
                print(f"[DEBUG] Kept {len(new_entries)} recent entries")
            else:
                print(f"[DEBUG] Log cleanup: no entries older than {keep_days} days to remove")

        except Exception as e:
            print(f"[DEBUG] Log cleanup error: {e}")

    def startup_check(self):
        """Check error items against active listings on startup"""
        try:
            # First clean up old logs (keep last 30 days)
            self.cleanup_old_logs()

            # Then load the log
            self.refresh_log()

            # Then check error items status
            self.check_error_items_status()
        except Exception as e:
            print(f"[DEBUG] Startup check error: {e}")

    def check_error_items_status(self):
        """Check which error items are still active vs already closed"""
        try:
            from ebay_api import fetch_all_active_listings
            from auth import get_access_token, load_config

            config = load_config()
            token = get_access_token(config)

            # Fetch active listings
            print("[DEBUG] Checking error items against active listings...")
            active_items = fetch_all_active_listings(config, token)
            active_ids = {item["item_id"] for item in active_items}
            print(f"[DEBUG] Found {len(active_ids)} active listings")

            # Check each error entry in log
            if LOG_FILE.exists():
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    try:
                        entries = json.load(f)
                    except json.JSONDecodeError:
                        return

                # Find error entries and check status
                for entry in entries:
                    if entry.get("status") == "error":
                        item_id = entry.get("old_item_id") or entry.get("item_id", "")
                        if item_id:
                            is_active = item_id in active_ids
                            entry["_is_active"] = is_active
                            status_text = "[ACTIVE] Can retry" if is_active else "[CLOSED] Already ended"
                            print(f"[DEBUG] {item_id}: {status_text}")

                # Save updated entries with status info
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2)

            # Refresh display
            self.after(0, self.refresh_log)

        except Exception as e:
            print(f"[DEBUG] Error checking status: {e}")
            import traceback
            traceback.print_exc()

    def update_log(self, text):
        # Clear tree and add a status message
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        if text and text.strip():
            self.log_tree.insert("", 0, values=("", "", text, "", ""))

    def auto_refresh_activity_log(self):
        """Auto-refresh activity log and status if file has been modified or task is running"""
        try:
            # Check if progress.json exists (task running)
            progress_file = BASE_DIR / "progress.json"
            if progress_file.exists():
                # Update both the log AND the left panel status
                self.refresh_log()
                self.update_status_from_progress()
            # Or check if relist_log.json changed (task completed)
            elif LOG_FILE.exists():
                current_modify_time = LOG_FILE.stat().st_mtime
                if current_modify_time > self.last_log_modify_time:
                    self.last_log_modify_time = current_modify_time
                    self.refresh_log()
        except:
            pass

        # Schedule next check in 2 seconds
        self.after(2000, self.auto_refresh_activity_log)

    def update_status_from_progress(self):
        """Update left panel status from progress.json (for scheduled tasks)"""
        try:
            progress_file = BASE_DIR / "progress.json"
            if progress_file.exists():
                with open(progress_file, encoding="utf-8") as f:
                    progress = json.load(f)

                    stage = progress.get("stage", "")
                    item_id = progress.get("item_id", "")
                    title = progress.get("title", "")
                    completed = progress.get("completed", 0)
                    total = progress.get("total", 10)

                    # Update status
                    self.status_text.config(text="Running...", fg="#FFFF00")

                    # Update current item
                    self.current_item_label.config(text=f"Item: {item_id}\n{title[:40]}")

                    # Update progress (cap at total)
                    current = min(completed + 1, total)
                    self.progress_label.config(text=f"Current: {current}/{total} items")
                    self.progress_bar.config(value=(current * 100) // max(total, 1))

                    # Update stage
                    stage_display = stage.replace("_", " ").title()
                    self.stage_label.config(text=f"⊙ {stage_display}")
        except:
            pass

    def open_settings(self):
        SettingsWindow(self, self.app_config, self.refresh_after_settings_save)

    def open_exclusions(self):
        try:
            # Only pass callback if Inventory window is already open
            inventory_window = None
            for widget in self.winfo_children():
                if isinstance(widget, InventoryWindow):
                    inventory_window = widget
                    break

            refresh_callback = inventory_window.load_items if inventory_window else None
            ExclusionsWindow(self, self.app_config, on_save=self.refresh_after_settings_save, refresh_inventory_callback=refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Exclude window:\n{str(e)}")

    def refresh_after_settings_save(self):
        """Refresh UI after settings are saved"""
        # Reload config from disk
        from auth import load_config
        self.app_config = load_config()

        # Update store name label
        if self.store_label:
            store_name = self.app_config.get("store_name", "")
            if store_name:
                self.store_label.config(text=store_name)
                if not self.store_label.winfo_viewable():
                    self.store_label.pack(anchor="w", fill="x", pady=(0, 10))
            else:
                self.store_label.pack_forget()

        # Refresh the activity log
        self.refresh_log()

    def run_agent(self):
        threading.Thread(target=self._run_agent_thread, daemon=True).start()

    def _run_agent_thread(self):
        try:
            self.status_text.config(text="Running...", fg="#FFFF00")
            self.progress_bar.config(value=0)
            self.progress_label.config(text="Current: 0/10 items")
            self.overall_progress_bar.config(value=0)
            self.overall_label.config(text="0/10 total")
            self.stage_label.config(text="")
            self.stage_dots.config(text="")
            self.current_item_label.config(text="")
            self.monitor_progress()  # Start monitoring
            self.update_log("Running agent...\n")

            # Import and call agent directly
            from ebay_relist_agent import run
            run()

            self.progress_bar.config(value=100)
            self.overall_progress_bar.config(value=100)
            self.status_text.config(text="Complete\n✓", fg="#00DD00")
            self.update_log("Agent completed successfully!\n\nRefreshing log...")
            self.after(1000, self.refresh_log)
        except Exception as e:
            self.status_text.config(text="Failed\n✗", fg="#FF4444")
            self.update_log(f"Agent failed:\n{str(e)}")
            self.progress_bar.config(value=0)
            self.overall_progress_bar.config(value=0)

    def update_progress_display(self):
        """Update progress bar and current item display"""
        try:
            from datetime import datetime, timedelta
            from pathlib import Path

            PROGRESS_FILE = DATA_DIR / "progress.json"

            # Get total items to process from config
            total_items = self.app_config.get("listings_per_run", 10)

            # Read real-time progress from progress.json
            stage = ""
            current_title = ""
            completed = 0
            current_step = 0  # 0=Getting, 1=Delisting, 2=Verifying, 3=Creating

            if PROGRESS_FILE.exists():
                try:
                    with open(PROGRESS_FILE, encoding="utf-8") as f:
                        progress_data = json.load(f)
                        stage = progress_data.get("stage", "")
                        current_title = progress_data.get("title", "")[:40]
                        completed = progress_data.get("completed", 0)
                except:
                    pass

            # Map stage to step number (for 4-step progress)
            stage_to_step = {
                "Getting listing": 0,
                "Delisting old": 1,
                "Verifying deletion": 2,
                "Creating new listing": 3,
                "Completed": 4,
            }
            current_step = stage_to_step.get(stage, 0)

            # Current item progress (25% per step, 4 steps total)
            item_percentage = int((current_step / 4) * 100) if stage else 0
            self.progress_bar.config(value=item_percentage)
            self.progress_label.config(text=f"Current: {completed}/{total_items} items")

            # Overall progress: account for 4 steps per item
            # Total steps = total_items * 4, Completed steps = completed * 4 + current_step
            total_steps = total_items * 4
            completed_steps = completed * 4 + current_step
            overall_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

            self.overall_progress_bar.config(value=overall_percentage)
            self.overall_label.config(text=f"{completed}/{total_items} total")

            # Update stage indicator
            stage_symbols = {
                "Getting listing": "1️⃣",
                "Delisting old": "2️⃣",
                "Verifying deletion": "3️⃣",
                "Creating new listing": "4️⃣",
                "Completed": "✓",
            }

            # Visual stage indicator (dots)
            stages = ["Getting listing", "Delisting old", "Verifying deletion", "Creating new listing"]
            stage_status = []
            for s in stages:
                if stage == s:
                    stage_status.append("●")  # Current stage
                elif stages.index(s) < stages.index(stage) if stage in stages else -1:
                    stage_status.append("✓")  # Completed stage
                else:
                    stage_status.append("○")  # Pending stage

            self.stage_label.config(text=stage if stage else "Idle")
            self.stage_dots.config(text=" ".join(stage_status))

            if current_title:
                self.current_item_label.config(text=f"Processing:\n{current_title}")
            else:
                self.current_item_label.config(text="")

        except Exception as e:
            pass

    def monitor_progress(self):
        """Continuously monitor and update progress while agent runs"""
        self.update_progress_display()
        self.after(1000, self.monitor_progress)  # Update every 1 second

    def open_log_viewer(self):
        LogViewerWindow(self)

    def show_about(self):
        store_name = self.app_config.get("store_name", "")
        licensed_to = f"Licensed to: {store_name}" if store_name else ""

        about_text = """eBay Relist Agent v1.0.4

Automatically relist your items daily from your eBay store.

KEY FEATURES:
• Schedule automatic relisting (daily or custom days)
• Track relisted items in activity log
• Manage inventory with exclusions
• License-protected (one key per computer)
• OAuth 2.0 for secure eBay authentication

QUICK START:
1. Configure your eBay API credentials
2. Set schedule and run time
3. Click "Run Now" to test or let it run automatically

SUPPORT:
For issues or feature requests:
support@thetrashedpanda.com

""" + licensed_to
        messagebox.showinfo("About Relist Agent", about_text)

    def check_updates_manual(self):
        """Check for updates and download if available"""
        from tkinter import filedialog
        has_update, latest_version = check_for_updates()
        if has_update:
            # Ask user where to save the file
            filename = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
                initialfile=f"Relist-Agent-{latest_version}.zip"
            )
            if filename:
                self._download_update(latest_version, filename)
        else:
            messagebox.showinfo("No Update", "You are using the latest version.")

    def _download_update(self, version, filepath):
        """Download update file"""
        try:
            url = f"https://thetrashedpanda.com/updates/{version}/Relist-Agent-{version}.zip"
            messagebox.showinfo("Downloading", f"Downloading {version}...\n\nSaving to:\n{filepath}")

            # Try curl_cffi first (WAF bypass via TLS fingerprint)
            if HAS_CURL_CFFI:
                try:
                    response = cffi_requests.get(url, impersonate="chrome", timeout=30)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        messagebox.showinfo("Downloaded", f"Update downloaded successfully!\n\n{filepath}\n\nExtract and run the new version.")
                        return
                except Exception as e:
                    pass  # Fall back to urllib

            # Fallback: urllib with browser headers
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            urllib.request.urlretrieve(url, filepath)
            messagebox.showinfo("Downloaded", f"Update downloaded successfully!\n\n{filepath}\n\nExtract and run the new version.")
        except Exception as e:
            messagebox.showerror("Download Failed", f"Failed to download update:\n{str(e)}")

    def check_updates_startup(self):
        """Check for updates on startup in background"""
        def _check():
            try:
                has_update, latest_version = check_for_updates()
                if has_update:
                    self.after(0, self._flash_update_button)
            except Exception as e:
                print(f"[UPDATE] Startup check failed: {e}")
        threading.Thread(target=_check, daemon=True).start()

    def _flash_update_button(self):
        """Flash update button red to indicate new version available"""
        self.update_button.config(text="⚠ UPDATE AVAILABLE")
        self.update_button.config(foreground="red")

    def stop_service(self):
        """Remove the scheduled task from Windows Task Scheduler"""
        if not messagebox.askyesno("Stop Service", "Remove the scheduled task? The agent will no longer run automatically."):
            return

        try:
            import subprocess
            # Unregister the scheduled task
            subprocess.run(
                ["powershell", "-Command", "Unregister-ScheduledTask -TaskName 'eBayRelistAgent' -Confirm:$false"],
                check=True,
                capture_output=True
            )
            messagebox.showinfo("Success", "Scheduled task removed. The agent will no longer run automatically.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove task: {str(e)}")

    def show_instructions(self):
        instructions_text = """RELIST AGENT - COMPLETE INSTRUCTIONS

═══════════════════════════════════════════════════════════════

GETTING STARTED

1. CONFIGURE SETTINGS
   • Click Settings → Configure button
   • Enter your eBay API credentials (App ID, Dev ID, Cert ID)
   • Set up Gmail for email reports (Gmail Email + App Password)
   • Enter Report Email (where daily reports are sent)
   • Set Store Name (displays in dashboard)
   • Click Save to apply changes

2. SCHEDULE SETUP
   • In Settings, set Run Time (HH:MM format, e.g., 10:30)
   • Select which days of the week to run automatically
   • Choose how many items to relist per run (1-50)
   • Set how many days of logs to display (1-30)
   • Save your schedule

═══════════════════════════════════════════════════════════════

UNDERSTANDING THE DASHBOARD

LEFT PANEL - Status & Progress
• Logo and Store Name at top
• Status (Ready / Running / Complete / Failed)
• Current Item: Shows which item is being processed
• Current Progress: Stage within current item (4 stages = 100%)
• Overall Progress: Total items completed in this run

CENTER PANEL - Activity Log
• All relist activity in time order (newest first)
• Started: When the operation began
• Completed: When it finished
• Status: Current stage (if running) or result (relisted/error)
• Old Item: The item ID being relisted
• Title: Item title for identification

RIGHT PANEL - Quick Actions
• Run Now: Execute the agent immediately
• Inventory: Browse all your items
• Refresh: Reload the activity log
• View Log: Detailed log viewer with filtering
• Configure: Change settings
• Instructions: This page
• About: App information
• Exit: Close the application

═══════════════════════════════════════════════════════════════

ACTIVITY LOG STATUS MEANINGS

CURRENT ITEM IN PROGRESS (Yellow ▶)
• Getting listing: Fetching item details from eBay
• Delisting old: Removing the old listing
• Verifying deletion: Confirming item is delisted
• Creating new listing: Uploading the new listing

COMPLETED ITEMS (In Log)
• relisted (Green): Successfully relisted ✓
• error (Red): Failed to relist ✗

═══════════════════════════════════════════════════════════════

TIMING & WHY ITEMS TAKE TIME

⏱ EACH LISTING: 1–2 MINUTES

Why the delay?
The agent DELISTS the old listing BEFORE creating a new one. This
prevents eBay's duplicate listing policy errors, which would block
relisting.

What happens:
1. Get listing details from eBay (~15 seconds)
2. Delete the old listing (~15 seconds)
3. Verify it's really deleted (~30-60 seconds, with retries)
4. Create the new listing with same details (~15 seconds)
────────────────────────────────────
Total: 1–2 minutes per item (depends on eBay API response times)

Example: 10 items = 10-20 minutes total runtime

The verification step is critical—without it, eBay might still see the
old listing active, triggering the "item already exists" error.

═══════════════════════════════════════════════════════════════

PROGRESS BARS

Current Item Progress
• Shows progress through 4 stages
• Each stage = 25%
• Getting (0-25%) → Delisting (25-50%) → Verifying (50-75%)
  → Creating (75-100%)

Overall Job Progress
• Shows total items completed
• Accounts for all items × 4 stages
• Example: 10 items = 40 total stages
  • 1 item done + 2 stages on item 2 = 6/40 stages = 15%

═══════════════════════════════════════════════════════════════

INVENTORY WINDOW

Browse all active items in your store with powerful search.

COLUMNS:
• Actions: Delist (❌) or Relist (♻️) buttons for each item
• Item ID: Unique eBay item number
• SKU: Your custom SKU/product code
• Title: Product description
• Date Listed: When the listing was created

SEARCH:
• Type in the search box to filter by:
  → Product description (title)
  → Custom SKU code
• Examples: search by product name or SKU
• Real-time filtering as you type

QUICK ACTIONS:
• ❌ Delist: End the listing
• ♻️ Relist: End old listing and create new one
• 🔗 Link: Click the link icon next to Item ID to open on eBay
• Refresh Data: Reload all items (first load takes ~1 min per 100)
• Find Duplicates: View all items with same SKU (review only, no action)
• Auto-Delist Dupes: Automatically remove true duplicates (matching title+SKU, keeps newest)

═══════════════════════════════════════════════════════════════

MANAGING DUPLICATE LISTINGS

Duplicates can happen when the agent relists items or manual errors occur.

FINDING DUPLICATES:
• Click "Find Duplicates" button to scan inventory
• Shows all items with same SKU (not all are true duplicates)
• Review the report to identify which need removal

REMOVING TRUE DUPLICATES:
A "true duplicate" has:
• Exact same SKU
• Matching product title
• Created by accident (extra copy of same listing)

Click "Auto-Delist Dupes" to:
1. Find all true duplicates (matching title + SKU)
2. Keep the newest item (latest listing)
3. Mark older copies for deletion
4. Show confirmation list before delisting
5. Perform bulk removal with error handling

EXAMPLE:
If you have two identical "Funko Pop Batman #141" listings with same SKU,
the older item ID will be deleted automatically (keeping the newer one).

═══════════════════════════════════════════════════════════════

RECOVERING FAILED ITEMS

If an item fails to relist (marked with "error" in red):

1. Click the error row in the Activity Log
   → The "Retry Relist" button will activate

2. Click "Retry Relist"
   → System will attempt to relist the item again
   → Fetches latest item details
   → Delists old listing
   → Creates new listing

3. View the result popup:
   ✅ Success: Old ID, New ID, and Title shown
   ❌ Failed: Error message explains what happened

COMMON FAILURE REASONS:
• Duplicate Listing Policy (wait 24-48 hours or change SKU)
• API errors (usually temporary - retry in a few minutes)
• Missing item details (item may have been manually ended)

TIPS FOR RETRY:
• Try again immediately for API errors
• Wait 24-48 hours for duplicate policy blocks
• Modify the SKU before retrying if it's a duplicate
• Check email report for detailed error messages

═══════════════════════════════════════════════════════════════

TROUBLESHOOTING

Stuck Progress / Double Entries
→ Click Configure → Clear Cache
→ Removes stale progress data
→ Try again next run

Items Not Loading
→ Click Refresh Data in Inventory
→ First load may take 1-2 minutes

Email Reports Not Arriving
→ Check Gmail settings in Configure
→ Verify App Password is correct (16 chars)
→ Check Report Email address

Schedule Not Running
→ Verify at least one day is selected
→ Check Run Time is set correctly
→ Settings are saved (must click Save)

═══════════════════════════════════════════════════════════════

TIPS & BEST PRACTICES

1. Run Offline Safely
   Agent runs on Windows Task Scheduler
   You can close the GUI and tasks still run

2. Monitor First Runs
   Watch the first 2-3 runs before going fully automatic
   Check activity log to see what's being relisted

3. Use View Log for Details
   Full log viewer has filtering by date/status/keywords
   Great for finding specific items or troubleshooting

4. Verify Inventory Regularly
   Check Inventory window weekly
   Catch any issues early

5. Test with Run Now
   Use Run Now button to test settings
   Runs outside the schedule

6. Email Reports
   Daily reports show what relisted/what failed
   Check for patterns in errors

═══════════════════════════════════════════════════════════════

QUICK REFERENCE

BUTTONS BY LOCATION

Dashboard Right Panel:
• Run Now → Execute agent now
• Inventory → Browse items
• Refresh → Reload log
• View Log → Detailed viewer
• Configure → Settings
• Instructions → This page
• About → App info
• Exit → Close app

Settings Window:
• Save → Apply changes
• Clear Cache → Remove stale data
• Cancel → Discard changes

Inventory Window:
• ❌ Delist → End listing
• ♻️ Relist → Delist & create new
• Refresh Data → Reload items

═══════════════════════════════════════════════════════════════
"""
        QuickGuideWindow(self, "Instructions", instructions_text)

    def show_main_guide(self):
        guide_text = """DASHBOARD QUICK GUIDE

ACTIVITY LOG
Shows your most recent relist activity. Displays:
• Started: Time when the relist began
• Completed: Time when the relist finished
• Status: Current stage or result
• Old Item: The item ID that was ended
• Title: The listing title

ACTIVITY STATUS DESCRIPTIONS

CURRENT ITEM IN PROGRESS (Yellow ▶)
  ▶ Getting listing - Fetching item details from eBay
  ▶ Delisting old - Removing the old listing
  ▶ Verifying deletion - Confirming item is delisted
  ▶ Creating new listing - Uploading the new listing

COMPLETED ITEMS (Logged in Activity Log)
  relisted (Green) - Successfully relisted item
  error (Red) - Failed to relist (duplicate policy, API error, etc)

FAILED ITEMS
  • Failed items are logged with error details
  • Check email report for detailed error messages
  • Manually relist using the Inventory window if needed

PROGRESS BARS
  Current: Shows progress through current item (4 stages = 100%)
    • Each stage = 25% (Getting → Delisting → Verifying → Creating)
  Overall: Shows total progress across all items in this run
    • Accounts for all items × 4 stages per item

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
        InventoryWindow(self, self.app_config)


class InventoryWindow(tk.Toplevel):
    instance = None

    def __init__(self, parent, config):
        if InventoryWindow.instance is not None:
            try:
                InventoryWindow.instance.lift()
                InventoryWindow.instance.focus()
                return
            except:
                InventoryWindow.instance = None

        print("[INVENTORY] InventoryWindow.__init__ starting")
        super().__init__(parent)
        InventoryWindow.instance = self
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title("Store Inventory")
        self.geometry("1200x700")
        tk.Toplevel.config(self, bg=BG_PRIMARY)
        self.app_config = config
        self.all_items = []
        print("[INVENTORY] Basic init complete")

        # Configure ttk style for this window
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY, bordercolor=BG_TERTIARY, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('Treeview', background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, borderwidth=1)
        style.configure('Treeview.Heading', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('Treeview.Heading', background=[('active', BLUE_HOVER)])
        style.configure('TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Vertical.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Horizontal.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.map('TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Vertical.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Horizontal.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])

        # Header with title and guide icon
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Store Inventory", font=("Arial", 12, "bold")).pack(side="left")
        icon = get_info_icon(24)
        if icon:
            tk.Button(header, image=icon, command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)
        else:
            tk.Button(header, text="ⓘ", command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)

        # Button guide
        guide_frame = tk.Frame(self, bg=BG_PRIMARY, relief="solid", borderwidth=1)
        guide_frame.pack(fill="x", padx=0, pady=0)

        tk.Label(guide_frame, text="Action Buttons:", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        tk.Label(guide_frame, text="❌ = End listing  |  ♻️ = Delist & Relist", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=("Arial", 9)).pack(side="left", padx=10, pady=5)

        # Info note
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(info_frame, text="[INFO] First load fetches all item details (~1 min per 100 items). Future loads will be much faster thanks to caching.",
                  font=("Arial", 9), foreground=TEXT_SECONDARY).pack(anchor="w")
        ttk.Label(info_frame, text="[SEARCH] Find items by product description OR custom SKU",
                  font=("Arial", 9), foreground=TEXT_SECONDARY).pack(anchor="w")
        ttk.Label(info_frame, text="[DUPLICATES] 'Find Duplicates' shows all items with same SKU | 'Auto-Delist Dupes' removes true duplicates (matching title+SKU, keeps newest)",
                  font=("Arial", 9), foreground=TEXT_SECONDARY).pack(anchor="w")

        # Search and controls frame
        print("[INVENTORY] Creating search frame...")
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=10)
        print("[INVENTORY] Search frame packed")

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._debounce_filter)
        self.search_timer = None
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)

        ttk.Button(search_frame, text="Refresh Data", command=self.refresh_data).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Find Duplicates", command=self.find_duplicate_skus).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Auto-Delist Dupes", command=self.auto_delist_duplicates).pack(side="left", padx=5)

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

        # Table frame with custom scrollable list
        table_frame = tk.Frame(self, bg=BG_PRIMARY)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header + scrollable content container
        content_frame = tk.Frame(table_frame, bg=BG_PRIMARY)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        # Header row using grid
        header_frame = tk.Frame(content_frame, bg=BG_PRIMARY, height=30)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 5))
        header_frame.columnconfigure(2, weight=1)  # Title column expands
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="Actions", font=("Arial", 10, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        tk.Label(header_frame, text="Item ID", font=("Arial", 10, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        tk.Label(header_frame, text="SKU", font=("Arial", 10, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        tk.Label(header_frame, text="Title", font=("Arial", 10, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        tk.Label(header_frame, text="Date Listed", font=("Arial", 10, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=4, sticky="ew", padx=2, pady=2)

        # Set column widths (in pixels)
        header_frame.columnconfigure(0, minsize=90)   # Actions
        header_frame.columnconfigure(1, minsize=100)  # Item ID
        header_frame.columnconfigure(2, minsize=80)   # SKU
        header_frame.columnconfigure(3, weight=1)     # Title (expands)
        header_frame.columnconfigure(4, minsize=160)  # Date Listed

        # Canvas with scrollbar for items (below header)
        list_container = tk.Frame(content_frame, bg=BG_PRIMARY)
        list_container.grid(row=1, column=0, sticky="nsew")
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(list_container, bg=BG_SECONDARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.items_frame = tk.Frame(self.canvas, bg=BG_SECONDARY)

        self.items_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree = None  # Keep for compatibility

        # Load items in background
        threading.Thread(target=self.load_items, daemon=True).start()

    def load_items(self, force_refresh=False):
        print(f"[DEBUG] load_items() called with force_refresh={force_refresh}")
        try:
            from datetime import datetime, timedelta
            from auth import get_access_token
            from ebay_api import fetch_all_active_listings

            print("[DEBUG] Imports successful")
            cache_file = DATA_DIR / "inventory_cache.json"
            cache_valid_hours = 6

            # Try to load from cache first (unless force refresh)
            cached_items = {}
            cached_item_ids = set()
            print(f"[DEBUG] force_refresh={force_refresh}, cache_file={cache_file.exists()}")

            if not force_refresh and cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                        cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
                        if datetime.now() - cache_time < timedelta(hours=cache_valid_hours):
                            cached_items = {item.get("item_id"): item for item in cache_data.get("items", []) if item.get("item_id")}
                            cached_item_ids = set(cached_items.keys())

                            self.all_items = list(cached_items.values())
                            self.progress.config(value=100)
                            self.progress_text.config(text="Loaded from cache")
                            self.item_count.config(text=f"Loaded {len(self.all_items)} items (cached)")
                            self.filter_items()
                            return
                except Exception:
                    pass  # Cache load failed, fetch fresh

            # Fetch fresh data from eBay
            self.progress.config(maximum=100, value=50)
            self.progress_text.config(text="Fetching from eBay...")
            self.item_count.config(text="Loading...")
            self.update()

            token = get_access_token(self.app_config)
            fresh_items = fetch_all_active_listings(self.app_config, token)
            fresh_item_ids = {item.get("item_id") for item in fresh_items if item.get("item_id")}

            # Smart cache: detect new and deleted items
            new_item_ids = fresh_item_ids - cached_item_ids
            deleted_item_ids = cached_item_ids - fresh_item_ids

            if new_item_ids or deleted_item_ids:
                self.progress.config(value=75)
                if new_item_ids:
                    self.progress_text.config(text=f"Found {len(new_item_ids)} new items, {len(deleted_item_ids)} deleted")
                else:
                    self.progress_text.config(text=f"Found {len(deleted_item_ids)} deleted items")
                self.update()

            # Combine cached and fresh items
            self.all_items = [item for item in fresh_items if item.get("item_id") in fresh_item_ids]

            # Save to cache
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "items": self.all_items,
                "new_count": len(new_item_ids),
                "deleted_count": len(deleted_item_ids)
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            # OPTIMIZATION: Also update exclusions cache (avoid redundant API calls)
            try:
                from ebay_api import get_store_categories
                categories, category_mapping = get_store_categories(self.app_config, token)

                # Extract SKUs from fresh items
                skus = set()
                for item in fresh_items:
                    sku = item.get("sku")
                    if sku:
                        skus.add(sku)

                # Save to exclusions cache (in hidden folder)
                exclusions_cache_file = DATA_DIR / "exclusions_cache.json"
                with open(exclusions_cache_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "categories": sorted(categories),
                        "skus": sorted(skus),
                        "category_mapping": category_mapping
                    }, f, indent=2)
                print(f"[INVENTORY] Updated exclusions cache: {len(categories)} cats, {len(skus)} skus")

                # ALSO update the Exclude window's separate cache (available_for_exclusions.json)
                # This keeps the Exclude window's display in sync without losing exclusions
                available_for_exclusions_file = DATA_DIR / "available_for_exclusions.json"
                with open(available_for_exclusions_file, "w", encoding="utf-8") as f:
                    json.dump({"items": fresh_items}, f, indent=2)
                print(f"[INVENTORY] Updated available_for_exclusions cache: {len(fresh_items)} items")
            except Exception as e:
                print(f"[INVENTORY] Couldn't update exclusions cache: {e}")

            self.progress.config(value=90)
            self.progress_text.config(text="Rendering items...")
            self.update()

            self.filter_items()

            self.progress.config(value=100)
            self.progress_text.config(text="Done")
            status_msg = f"Loaded {len(self.all_items)} items"
            if new_item_ids or deleted_item_ids:
                status_msg += f" ({len(new_item_ids)} new, {len(deleted_item_ids)} deleted)"
            self.item_count.config(text=status_msg)
        except Exception as e:
            import traceback
            self.progress.config(value=0)
            self.progress_text.config(text="")
            error_msg = f"Error: {str(e)}"
            self.item_count.config(text=error_msg)
            print(f"[DEBUG] Load items error: {traceback.format_exc()}")

    def _debounce_filter(self, *args):
        """Debounce search input to avoid lag - wait 300ms after user stops typing"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.filter_items)

    def _preformat_item_dates(self):
        """Pre-format all item dates once to avoid re-parsing during filtering"""
        from datetime import datetime
        for item in self.all_items:
            date_str = item.get("start_time", "")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    item["_formatted_date"] = dt.strftime("%m/%d/%Y %I:%M %p")
                except:
                    item["_formatted_date"] = date_str
            else:
                item["_formatted_date"] = ""

    def filter_items(self, *args):
        search_term = self.search_var.get().lower()

        # Clear existing items
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        # Filter by title and SKU
        filtered = [
            item for item in self.all_items
            if search_term in item.get("title", "").lower() or
               search_term in item.get("sku", "").lower()
        ]

        for idx, item in enumerate(filtered):
            # Use pre-formatted date
            formatted_date = item.get("_formatted_date", "")

            item_id = item.get("item_id", "")
            sku = item.get("sku", "")
            title = item.get("title", "")

            # Alternate row colors
            row_bg = BG_SECONDARY if idx % 2 == 0 else BG_TERTIARY

            # Create row frame using grid
            row = tk.Frame(self.items_frame, bg=row_bg, height=30)
            row.pack(fill="x", padx=0, pady=0)
            row.columnconfigure(3, weight=1)  # Title expands

            # Action buttons
            btn_frame = tk.Frame(row, bg=row_bg)
            btn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
            tk.Button(btn_frame, text="❌", width=2, height=1, bg=RED_PRIMARY, fg=TEXT_PRIMARY, command=lambda iid=item_id, t=title: self.delist_item(iid, t), relief="flat", border=1).pack(side="left", padx=1)
            tk.Button(btn_frame, text="♻️", width=2, height=1, bg=YELLOW_PRIMARY, fg="#000000", command=lambda iid=item_id, t=title: self.relist_item(iid, t), relief="flat", border=1).pack(side="left", padx=1)
            tk.Button(btn_frame, text="🔗", width=2, height=1, bg=TEXT_PRIMARY, fg=BG_PRIMARY, command=lambda iid=item_id: webbrowser.open(f"https://www.ebay.com/itm/{iid}"), relief="flat", border=1).pack(side="left", padx=1)

            # Item ID label
            tk.Label(row, text=item_id, font=("Arial", 9), bg=row_bg, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=1, sticky="ew", padx=2, pady=0)

            # SKU
            tk.Label(row, text=sku, font=("Arial", 9), bg=row_bg, fg=TEXT_SECONDARY, anchor="w").grid(row=0, column=2, sticky="ew", padx=2, pady=0)

            # Title (truncate long titles)
            title_display = (title[:50] + "...") if len(title) > 50 else title
            tk.Label(row, text=title_display, font=("Arial", 9), bg=row_bg, fg=TEXT_PRIMARY, anchor="w").grid(row=0, column=3, sticky="ew", padx=2, pady=0)

            # Date
            tk.Label(row, text=formatted_date, font=("Arial", 9), bg=row_bg, fg=TEXT_SECONDARY, anchor="w").grid(row=0, column=4, sticky="ew", padx=2, pady=0)

            # Match header column widths
            row.columnconfigure(0, minsize=90)   # Actions
            row.columnconfigure(1, minsize=100)  # Item ID
            row.columnconfigure(2, minsize=80)   # SKU
            row.columnconfigure(4, minsize=160)  # Date Listed

        # Update canvas scroll region
        self.items_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.item_count.config(text=f"{len(filtered)} of {len(self.all_items)} items")

    def _on_frame_configure(self, event=None):
        """Update scroll region and canvas window width"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Match canvas window width to canvas width
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(3, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-3, "units")

    def refresh_data(self):
        """Refresh inventory from eBay (force fresh fetch)"""
        result = messagebox.askyesno(
            "Refresh Data",
            "Force refresh from eBay? (This will skip cache and fetch fresh data)\n\nThis may take 1-2 minutes for large inventories.",
            parent=self
        )
        if result:
            print("[DEBUG] Refreshing inventory from eBay...")

            # Clear items frame
            for widget in self.items_frame.winfo_children():
                widget.destroy()

            # Reload with force_refresh=True
            self.all_items = []
            self.progress["value"] = 0
            self.progress_text.config(text="Connecting to eBay...")
            self.item_count.config(text="Loading...")

            threading.Thread(target=lambda: self.load_items(force_refresh=True), daemon=True).start()

    def find_duplicate_skus(self):
        """Find and display all duplicate SKUs in inventory"""
        if not self.all_items:
            messagebox.showwarning("No Items", "Load inventory first")
            return

        # Build SKU -> items map
        sku_map = {}
        for item in self.all_items:
            sku = item.get("sku", "").strip()
            if sku:
                if sku not in sku_map:
                    sku_map[sku] = []
                sku_map[sku].append(item)

        # Find duplicates
        duplicates = {sku: items for sku, items in sku_map.items() if len(items) > 1}

        if not duplicates:
            messagebox.showinfo("No Duplicates", "All SKUs are unique!")
            return

        # Build report
        report = f"Found {len(duplicates)} duplicate SKUs:\n\n"
        for sku, items in sorted(duplicates.items()):
            report += f"SKU: {sku} ({len(items)} items)\n"
            for item in items:
                report += f"  • {item.get('item_id')} - {item.get('title', 'N/A')[:40]}\n"
            report += "\n"

        # Show in a text window
        info_window = tk.Toplevel(self)
        info_window.title("Duplicate SKUs Found")
        info_window.geometry("600x400")
        info_window.config(bg=BG_PRIMARY)

        text_widget = tk.Text(info_window, bg=BG_SECONDARY, fg=TEXT_PRIMARY, wrap="word", padx=10, pady=10)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", report)
        text_widget.config(state="disabled")

        scrollbar = ttk.Scrollbar(text_widget, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        close_btn = ttk.Button(info_window, text="Close", command=info_window.destroy)
        close_btn.pack(pady=10)

    def auto_delist_duplicates(self):
        """Find true duplicates (matching title+SKU) and delist oldest"""
        if not self.all_items:
            messagebox.showwarning("No Items", "Load inventory first")
            return

        # Normalize titles for comparison (first 50 chars, lowercase)
        def normalize_title(title):
            return (title or "")[:50].lower().strip()

        # Build SKU -> items map
        sku_map = {}
        for item in self.all_items:
            sku = item.get("sku", "").strip()
            if sku:
                if sku not in sku_map:
                    sku_map[sku] = []
                sku_map[sku].append(item)

        # Find true duplicates (matching title + SKU)
        to_delist = []
        for sku, items in sku_map.items():
            if len(items) <= 1:
                continue

            # Group by normalized title
            title_groups = {}
            for item in items:
                norm_title = normalize_title(item.get("title", ""))
                if norm_title:
                    if norm_title not in title_groups:
                        title_groups[norm_title] = []
                    title_groups[norm_title].append(item)

            # For each title group, keep newest, mark others for deletion
            for norm_title, title_items in title_groups.items():
                if len(title_items) > 1:
                    # Sort by item ID (ascending = oldest first)
                    sorted_items = sorted(title_items, key=lambda x: int(x.get("item_id", 0)))
                    # Keep newest (last), delist rest
                    for item in sorted_items[:-1]:
                        to_delist.append(item)

        if not to_delist:
            messagebox.showinfo("No True Duplicates", "No items found with matching title AND SKU")
            return

        # Build confirmation message
        msg = f"Found {len(to_delist)} true duplicates to remove (keeping newest):\n\n"
        for item in to_delist:
            msg += f"ID: {item['item_id']} | SKU: {item.get('sku', 'N/A')} | {item.get('title', 'N/A')[:40]}\n"

        confirm = messagebox.askyesno("Confirm Auto-Delist", msg + f"\n\nDelist {len(to_delist)} items?")

        if confirm:
            self.perform_bulk_delist(to_delist)

    def perform_bulk_delist(self, items_to_delete):
        """Delist multiple items and show progress"""
        from auth import get_access_token
        from ebay_api import end_item

        success_count = 0
        failed_items = []

        progress = messagebox.showinfo(
            "Delisting",
            f"Delisting {len(items_to_delete)} duplicate items...\n\nThis may take a minute."
        )

        try:
            token = get_access_token(self.app_config)

            for idx, item in enumerate(items_to_delete):
                try:
                    item_id = item['item_id']
                    end_item(self.app_config, token, item_id)
                    success_count += 1
                    print(f"[INFO] Delisted {item_id} ({idx+1}/{len(items_to_delete)})")
                except Exception as e:
                    failed_items.append((item['item_id'], str(e)))
                    print(f"[ERROR] Failed to delist {item['item_id']}: {e}")

            # Show results
            result_msg = f"Delisted {success_count}/{len(items_to_delete)} items"
            if failed_items:
                result_msg += f"\n\nFailed ({len(failed_items)}):\n"
                for item_id, error in failed_items[:5]:
                    result_msg += f"  • {item_id}: {error}\n"
                if len(failed_items) > 5:
                    result_msg += f"  ... and {len(failed_items)-5} more"

            messagebox.showinfo("Bulk Delist Complete", result_msg)

            # Reload inventory
            self.all_items = []
            self.filter_items()
            threading.Thread(target=self.load_items, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Bulk delist failed: {e}")

    def delist_item(self, item_id, title):
        """Delist a single item by ID"""
        confirm = messagebox.askyesno(
            "Confirm Delist",
            f"End listing: {title}?\n\nItem ID: {item_id}"
        )

        if confirm:
            try:
                from auth import get_access_token
                from ebay_api import end_item

                token = get_access_token(self.app_config)
                end_item(self.app_config, token, item_id)
                messagebox.showinfo("Success", f"Item {item_id} delisted successfully")
                # Reload inventory
                self.all_items = []
                self.filter_items()
                threading.Thread(target=self.load_items, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delist: {e}")

    def relist_item(self, item_id, title):
        """Relist a single item (delist old, create new)"""
        confirm = messagebox.askyesno(
            "Confirm Relist",
            f"Relist: {title}?\n\nItem ID: {item_id}\n\nThis will end the current listing and create a new one with the same details"
        )

        if confirm:
            try:
                from auth import get_access_token
                from ebay_api import get_item, add_item, end_item

                token = get_access_token(self.app_config)

                # Get full item details FIRST (before delisting)
                details = get_item(self.app_config, token, item_id)

                # Delist the old item
                end_item(self.app_config, token, item_id)

                # Create new listing with same details
                new_item_id = add_item(self.app_config, token, details)

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
• Search by product title OR custom SKU
• Type to filter in real-time
• Case-insensitive search
• Examples:
  - Search "Plant" finds "Plant Pots Set of 3"
  - Search by product name to find items
  - Search by SKU code to find items

COLUMNS

Item ID
• Unique eBay identifier
• Click the 🔗 button to open the item on eBay.com in your browser

SKU
• Your custom product SKU/code
• Use this to quickly find items you're looking for

Title
• The listing title

Date Listed
• When the item was originally listed
• Format: MM/DD/YYYY HH:MM AM/PM

ACTIONS (Row Action Buttons)

Row buttons appear on the left of each item:

❌ DELIST SELECTED
• Select an item in the list
• Click the ❌ button to end/delete the listing
• Requires confirmation before delisting

♻️ RELIST SELECTED
• Select an item in the list
• Click the ♻️ button to automatically delist and relist with same details
• Uses current price, description, condition, shipping, etc.
• Old listing ends, new listing is created seamlessly

🔗 OPEN ON EBAY
• Click the 🔗 button next to the Item ID
• Opens the eBay listing in your web browser
• Allows you to view, edit, or manage the listing directly on eBay
• No selection required - button appears for every item

REFRESH DATA
Click to reload the inventory from eBay.

Item count shows: "X of Y items" where X is currently visible
after search filtering, and Y is total items in your store.

DUPLICATE SEARCH OPTIONS

FIND DUPLICATES
Purpose: Review and identify potential duplicates
• Scans inventory for items with the same SKU
• Shows ALL items with matching SKU (grouped by SKU)
• Includes items that may NOT be true duplicates
• No action taken - this is VIEW ONLY
• Use this to manually inspect and decide what to remove
• Good for: Understanding your inventory, finding variations of same product

AUTO-DELIST DUPES
Purpose: Automatically remove true duplicates
• Scans for items with BOTH matching title AND SKU
• Only targets true duplicates (identical product + SKU)
• Automatically keeps the NEWEST listing
• Delists OLDER copies of the same item
• Requires your confirmation before delisting
• Shows success/failure report
• Use this when you have exact duplicate listings
• Good for: Cleaning up accidental duplicate listings from relisting or manual errors

WHEN TO USE EACH:
1. Use "Find Duplicates" first to review potential issues
2. Use "Auto-Delist Dupes" to safely remove confirmed true duplicates
   (matching both title AND SKU)
"""
        QuickGuideWindow(self, "Inventory", guide_text)

    def open_activity_log(self):
        """Open the activity log viewer"""
        LogViewerWindow(self)

    def _on_close(self):
        InventoryWindow.instance = None
        self.destroy()


class LogViewerWindow(tk.Toplevel):
    instance = None

    def __init__(self, parent):
        if LogViewerWindow.instance is not None:
            try:
                LogViewerWindow.instance.lift()
                LogViewerWindow.instance.focus()
                return
            except:
                LogViewerWindow.instance = None

        super().__init__(parent)
        LogViewerWindow.instance = self
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title("Log Viewer - All Runs")
        self.geometry("900x600")
        tk.Toplevel.config(self, bg=BG_PRIMARY)

        # Configure ttk style for this window
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.configure('TButton', background=BLUE_PRIMARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TLabelFrame', background=BG_PRIMARY, foreground=TEXT_PRIMARY, bordercolor=BG_TERTIARY, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY)
        style.configure('TLabelFrame.Label', background=BG_PRIMARY, foreground=TEXT_PRIMARY)
        style.map('TButton', background=[('active', BLUE_HOVER)])
        style.configure('TEntry', fieldbackground=BG_SECONDARY, foreground=TEXT_PRIMARY, borderwidth=1)
        style.configure('TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Vertical.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.configure('Horizontal.TScrollbar', background=SCROLLBAR_BG, troughcolor=SCROLLBAR_TROUGH, lightcolor=BG_TERTIARY, darkcolor=BG_TERTIARY, borderwidth=1)
        style.map('TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Vertical.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])
        style.map('Horizontal.TScrollbar', background=[('active', SCROLLBAR_ACTIVE)])

        # Header with title and guide icon
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="Log Viewer", font=("Arial", 12, "bold")).pack(side="left")
        icon = get_info_icon(24)
        if icon:
            tk.Button(header, image=icon, command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)
        else:
            tk.Button(header, text="ⓘ", command=self.show_guide, bg=BG_PRIMARY, activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY, border=0, highlightthickness=0, relief="flat").pack(side="left", padx=5)

        # Filter frame
        filter_frame = tk.LabelFrame(self, text="Filter", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=("Arial", 10, "bold"), padx=10, pady=10, borderwidth=2, relief="solid", highlightthickness=0)
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
        ttk.Button(filter_frame, text="🔄 Refresh", command=self.refresh_log).grid(row=0, column=9, padx=5)

        # Table frame
        table_frame = tk.LabelFrame(self, text="History", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=("Arial", 10, "bold"), padx=10, pady=10, borderwidth=2, relief="solid", highlightthickness=0)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Text widget for log (with built-in scrollbars)
        self.log_display = scrolledtext.ScrolledText(table_frame, height=20, width=100, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=BLUE_PRIMARY)
        self.log_display.pack(fill="both", expand=True)

        # Load all data
        self.all_entries = []
        self.last_modify_time = 0
        self.load_all_entries()
        self.apply_filter()

        # Auto-refresh log every 2 seconds
        self.auto_refresh_log()

    def load_all_entries(self):
        try:
            if not LOG_FILE.exists():
                return
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                self.all_entries = json.load(f)
        except Exception as e:
            self.log_display.insert("end", f"Error loading log: {e}\n")

    def refresh_log(self):
        """Reload log entries and reapply filters"""
        self.load_all_entries()
        self.apply_filter()

    def auto_refresh_log(self):
        """Auto-refresh log if file has been modified"""
        try:
            if LOG_FILE.exists():
                current_modify_time = LOG_FILE.stat().st_mtime
                if current_modify_time > self.last_modify_time:
                    self.last_modify_time = current_modify_time
                    self.load_all_entries()
                    self.apply_filter()
        except:
            pass

        # Schedule next refresh in 2 seconds
        if self.winfo_exists():
            self.after(2000, self.auto_refresh_log)

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

    def _on_close(self):
        LogViewerWindow.instance = None
        self.destroy()


def main():
    """Main entry point for the application"""
    try:
        # Write to file to confirm main() was called
        with open("main_called.log", "w") as f:
            f.write("Main called\n")
    except:
        pass

    try:
        # Check license key FIRST (before admin check)
        from license_check import check_license_on_startup
        if not check_license_on_startup():
            sys.exit(1)

        # Check if admin is needed
        check_admin_on_startup()

        # Create and run the app
        app = MainApp()
        app.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"STARTUP ERROR: {e}\n{traceback.format_exc()}"
        print(error_msg)
        # Try to write to a log file
        try:
            with open("startup_error.log", "w") as f:
                f.write(error_msg)
        except:
            pass
        sys.exit(1)


# Call main directly at module level so it always runs (not in __main__ block)
if __name__ == "__main__" or True:  # Always run, even if imported
    main()
