import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from pathlib import Path
import sys
import base64
import requests
from datetime import datetime, timedelta, timezone
from ebay_api import fetch_sold_items_rest, fetch_all_active_listings

RELIST_AGENT_PATH = Path(r"C:\Users\tom\agents\ebay-master\ebay-relist-agent")
CONFIG_FILE = RELIST_AGENT_PATH / "config.json"
TOKEN_FILE = RELIST_AGENT_PATH / ".ebay_relist_agent_data" / "tokens.json"
OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPES = " ".join([
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
])


def load_config():
    """Load eBay API credentials from Relist Agent config"""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        return {
            "app_id": config.get("app_id"),
            "dev_id": config.get("dev_id"),
            "cert_id": config.get("cert_id"),
        }
    except Exception as e:
        messagebox.showerror("Config Error", f"Failed to load config: {e}")
        sys.exit(1)


def refresh_token_if_needed(cfg: dict, tokens: dict) -> str:
    """Refresh access token if expired"""
    try:
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(tokens.get("expires_at", "2000-01-01T00:00:00+00:00"))

        # If token still valid for 5+ minutes, use it
        if tokens.get("access_token") and expires_at > now + timedelta(minutes=5):
            return tokens["access_token"]

        # Need to refresh
        if not tokens.get("refresh_token"):
            raise RuntimeError(
                "No refresh token. Go to developer.ebay.com > User Tokens > "
                "Sign in to Production, copy the token, and re-run Relist Agent setup."
            )

        creds = base64.b64encode(f"{cfg['app_id']}:{cfg['cert_id']}".encode()).decode()
        resp = requests.post(
            OAUTH_TOKEN_URL,
            headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "scope": SCOPES},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        tokens["access_token"] = data["access_token"]
        tokens["expires_at"] = (now + timedelta(seconds=data["expires_in"])).isoformat()
        if "refresh_token" in data:
            tokens["refresh_token"] = data["refresh_token"]

        # Save updated tokens
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)

        return tokens["access_token"]
    except Exception as e:
        raise RuntimeError(f"Token refresh failed: {e}")


def load_auth_token():
    """Load eBay auth token from Relist Agent, refresh if needed"""
    try:
        if not TOKEN_FILE.exists():
            raise FileNotFoundError(f"Token file not found: {TOKEN_FILE}")

        cfg = load_config()
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)

        # Try to refresh token if needed
        return refresh_token_if_needed(cfg, tokens)
    except Exception as e:
        messagebox.showerror("Auth Error", f"Failed to load/refresh auth token: {e}")
        sys.exit(1)


def compare_listings(sold_items: list, active_items: list) -> list:
    """Compare sold items with active items by title. Aggregate by item."""
    active_by_title = {item["title"]: item for item in active_items}
    matches_dict = {}

    # Group by title and sum quantities
    for sold in sold_items:
        title = sold["title"]
        if title in active_by_title:
            if title not in matches_dict:
                active = active_by_title[title]
                matches_dict[title] = {
                    "title": title,
                    "sold_id": sold["item_id"],
                    "qty_sold": 0,
                    "last_sold_time": sold.get("sold_time", ""),
                    "active_id": active["item_id"],
                    "active_qty": active["quantity"],
                }
            # Add to total quantity sold
            try:
                matches_dict[title]["qty_sold"] += int(sold.get("quantity_sold", "1"))
            except (ValueError, TypeError):
                matches_dict[title]["qty_sold"] += 1
            # Update to most recent sale date
            matches_dict[title]["last_sold_time"] = sold.get("sold_time", "")

    # Convert to list and sort by title
    matches = list(matches_dict.values())
    matches.sort(key=lambda x: x["title"])
    return matches


class SalesAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Analyzer - Sold vs Active")
        self.root.geometry("1200x700")

        self.cfg = load_config()
        self.token = load_auth_token()

        self.sold_items = []
        self.active_items = []
        self.matches = []

        self.setup_ui()
        self.fetch_data()

    def setup_ui(self):
        """Build the GUI"""
        # Top frame: buttons
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(top_frame, text="Refresh Data", command=self.fetch_data).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export to CSV", command=self.export_csv).pack(side="left", padx=5)

        self.status_label = ttk.Label(top_frame, text="Loading...", foreground="blue")
        self.status_label.pack(side="left", padx=20)

        # Main content: two-column view
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left column: Sold items that have active listings
        left_frame = ttk.LabelFrame(content_frame, text="Sold Items (Still Active for Sale)", padding=5)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.sold_text = scrolledtext.ScrolledText(left_frame, height=30, width=50, font=("Courier", 9))
        self.sold_text.pack(fill="both", expand=True)

        # Right column: Corresponding active listings
        right_frame = ttk.LabelFrame(content_frame, text="Active Listing (Qty Available)", padding=5)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.active_text = scrolledtext.ScrolledText(right_frame, height=30, width=50, font=("Courier", 9))
        self.active_text.pack(fill="both", expand=True)

    def fetch_data(self):
        """Fetch sold and active items from eBay"""
        self.status_label.config(text="Fetching sold items...", foreground="blue")
        self.root.update()

        try:
            self.sold_items = fetch_sold_items_rest(self.cfg, self.token)
            print(f"DEBUG: Sold items fetched: {len(self.sold_items)}")

            self.status_label.config(text="Fetching active items...", foreground="blue")
            self.root.update()

            self.active_items = fetch_all_active_listings(self.cfg, self.token)
            print(f"DEBUG: Active items fetched: {len(self.active_items)}")

            self.matches = compare_listings(self.sold_items, self.active_items)
            print(f"DEBUG: Matches found: {len(self.matches)}")

            self.display_matches()
            self.status_label.config(
                text=f"Done. Sold: {len(self.sold_items)}, Active: {len(self.active_items)}, Matches: {len(self.matches)}",
                foreground="green"
            )
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", foreground="red")
            messagebox.showerror("Fetch Error", str(e))

    def display_matches(self):
        """Display side-by-side comparison"""
        self.sold_text.delete("1.0", "end")
        self.active_text.delete("1.0", "end")

        for match in self.matches:
            # Left: Sold item info (aggregated)
            sold_line = f"{match['title']}\n  Qty Sold (Total): {match['qty_sold']}\n  Last Sale: {match['last_sold_time']}\n\n"
            self.sold_text.insert("end", sold_line)

            # Right: Active listing info
            active_line = f"{match['title']}\n  ID: {match['active_id']}\n  Qty Available: {match['active_qty']}\n\n"
            self.active_text.insert("end", active_line)

        self.sold_text.config(state="disabled")
        self.active_text.config(state="disabled")

    def export_csv(self):
        """Export matches to CSV"""
        csv_path = Path.cwd() / "sales_analyzer_matches.csv"
        try:
            with open(csv_path, "w") as f:
                f.write("Sold Title,Sold ID,Sold Time,Active ID,Active Qty\n")
                for match in self.matches:
                    f.write(f'"{match["title"]}",{match["sold_id"]},"{match["sold_time"]}",{match["active_id"]},{match["active_qty"]}\n')
            messagebox.showinfo("Export", f"Exported {len(self.matches)} matches to {csv_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesAnalyzerApp(root)
    root.mainloop()
