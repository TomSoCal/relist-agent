#!/usr/bin/env python3
"""
eBay Listing Refresh Agent

Daily: ends the 10 oldest fixed-price active listings and re-creates them fresh.
Also ends any zero-quantity listings without relisting them.
Emails a report after each run (configured in settings).

First run:  python ebay_relist_agent.py --setup
Ongoing:    python ebay_relist_agent.py
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

from auth import get_access_token, interactive_setup, load_config
from ebay_api import add_item, end_item, fetch_all_active_listings, get_item
from listing_logic import partition_listings, select_oldest
from notifications import format_report, format_subject, notify_toast, send_email

sys.path.insert(0, r"C:\Users\tom\agents")
try:
    from shared.kff_client import kff_check
except ImportError:
    def kff_check(*args, **kwargs):
        return {"status": "approve", "suggestion": ""}

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / ".ebay_relist_agent_data"
DATA_DIR.mkdir(exist_ok=True)  # Create hidden folder if it doesn't exist
# Make folder hidden on Windows
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetFileAttributesW(str(DATA_DIR), 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
LOG_FILE = DATA_DIR / "relist_log.json"
BACKUP_FILE = DATA_DIR / "item_backups.json"
ERROR_LOG_FILE = DATA_DIR / "error_log.txt"
PROGRESS_FILE = DATA_DIR / "progress.json"


def update_progress(stage: str, item_id: str = "", title: str = "", completed: int = 0, total: int = 0) -> None:
    """Write real-time progress to progress.json for GUI to read"""
    try:
        progress_data = {
            "stage": stage,
            "item_id": item_id,
            "title": title[:50],
            "completed": completed,
            "total": total,
            "timestamp": datetime.now().isoformat()
        }
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress_data, f)
    except:
        pass


def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{ts}] {msg}"
    try:
        # Print with error handling for emoji/unicode characters
        print(formatted, end="\n", flush=True)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        safe_msg = formatted.encode("utf-8", errors="replace").decode("utf-8")
        print(safe_msg, end="\n", flush=True)
    except:
        pass

    try:
        with open(DATA_DIR / "run.log", "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except:
        pass


def append_log(entries: list[dict]) -> None:
    existing = []
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                pass
    existing.extend(entries)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def verify_item_delisted(cfg: dict, token: str, item_id: str, max_retries: int = 5) -> bool:
    """Verify that an item has been successfully delisted by checking eBay"""
    for attempt in range(max_retries):
        try:
            get_item(cfg, token, item_id)
            # If we get here, item is still active, wait and retry
            if attempt < max_retries - 1:
                log(f"    [Verify] Item still active, retry {attempt + 1}/{max_retries - 1}...")
                time.sleep(5)  # Wait 5 seconds for eBay to process deletion
        except Exception as e:
            # Item not found means it's successfully delisted
            if "no longer available" in str(e).lower() or "item not found" in str(e).lower():
                log(f"    [Verify] Item confirmed delisted")
                return True

    log(f"    [Verify] WARNING: Item may still be active after {max_retries} checks")
    return False


def backup_listing(item_id: str, fields: dict) -> dict:
    backup_data = {
        "item_id": item_id,
        "date": date.today().isoformat(),
        "title": fields.get("title"),
        "description": fields.get("description"),
        "pictures": fields.get("pictures", []),
        "start_price": fields.get("start_price"),
        "quantity": fields.get("quantity"),
        "primary_category_id": fields.get("primary_category_id"),
        "secondary_category_id": fields.get("secondary_category_id"),
        "condition_id": fields.get("condition_id"),
        "condition_description": fields.get("condition_description"),
        "listing_duration": fields.get("listing_duration"),
        "sku": fields.get("sku"),
        "shipping_profile_id": fields.get("shipping_profile_id"),
        "return_profile_id": fields.get("return_profile_id"),
        "payment_profile_id": fields.get("payment_profile_id"),
        "currency": fields.get("currency"),
        "country": fields.get("country"),
    }

    # Append to separate backup file
    backups = []
    if BACKUP_FILE.exists():
        with open(BACKUP_FILE, encoding="utf-8") as f:
            try:
                backups = json.load(f)
            except json.JSONDecodeError:
                pass
    backups.append(backup_data)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(backups, f, indent=2)

    return backup_data


def run() -> None:
    today = date.today().isoformat()
    log(f"=== eBay Relist Agent starting ({today}) ===")

    cfg = load_config()
    token = get_access_token(cfg)

    log("Fetching all active listings...")
    all_items = fetch_all_active_listings(cfg, token)
    log(f"  {len(all_items)} active listings found")

    zero_qty, eligible = partition_listings(all_items)
    listings_per_run = cfg.get("listings_per_run", 10)
    to_relist = select_oldest(eligible, n=listings_per_run)
    log(f"  {len(zero_qty)} zero-qty | {len(eligible)} eligible | {len(to_relist)} to relist")

    log_entries = []
    ended_zero_qty_report = []
    relisted_report = []
    failures_report = []

    for item in zero_qty:
        iid = item["item_id"]
        try:
            end_item(cfg, token, iid)
            log(f"  Ended zero-qty: {iid} — {item['title']}")
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "ended-zero-qty"})
            ended_zero_qty_report.append({"item_id": iid, "title": item["title"]})
        except Exception as e:
            log(f"  ERROR ending zero-qty {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": str(e)})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})

    for idx, item in enumerate(to_relist, 1):
        iid = item["item_id"]
        title = item["title"]
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Stage 1: Get item details
        update_progress("Getting listing", iid, title, idx - 1, len(to_relist))
        try:
            fields = get_item(cfg, token, iid)
        except Exception as e:
            log(f"  ERROR GetItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": title, "reason": f"GetItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": title, "status": "error", "reason": str(e)})
            continue

        # Stage 2: Delete old listing
        update_progress("Delisting old", iid, title, idx - 1, len(to_relist))
        try:
            end_item(cfg, token, iid)
            log(f"  Delisted: {iid}")
        except Exception as e:
            log(f"  ERROR EndItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": title, "reason": f"EndItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": title, "status": "error", "reason": str(e)})
            continue

        # Stage 3: Verify deletion
        update_progress("Verifying deletion", iid, title, idx - 1, len(to_relist))
        if not verify_item_delisted(cfg, token, iid):
            log(f"  WARNING: {iid} may still be active, attempting relist anyway...")

        # Stage 4: Create new listing
        update_progress("Creating new listing", iid, title, idx - 1, len(to_relist))
        try:
            new_id = add_item(cfg, token, fields)
        except Exception as e:
            log(f"  ERROR AddItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": title, "reason": f"AddItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": title, "status": "error", "reason": str(e)})
            continue

        # KFF process sanity check — free via Ollama
        kff_result = kff_check(
            "process",
            agent="ebay-relist-agent",
            step="relist",
            context=f"Relisted item {iid} as {new_id}: title='{title}'"
        )
        if kff_result.get("status") == "flag":
            log(f"  KFF flagged relist {iid} -> {new_id}: {kff_result.get('suggestion', '')}")

        update_progress("Completed", iid, title, idx, len(to_relist))
        log(f"  Relisted: {iid} -> {new_id} — {title}")
        relisted_report.append({"old_id": iid, "new_id": new_id, "title": title})

        # Create backup of listing details
        backup = backup_listing(iid, fields)

        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entries.append({
            "date": today, "start_time": start_time, "end_time": end_time,
            "old_item_id": iid, "new_item_id": new_id,
            "title": item["title"], "status": "relisted",
            "backup": backup,
        })

    append_log(log_entries)

    body = format_report(relisted_report, ended_zero_qty_report, failures_report)
    subject = format_subject(today)
    try:
        send_email(
            cfg["gmail_app_password"],
            subject,
            body,
            sender=cfg.get("gmail_email"),
            recipient=cfg.get("report_email")
        )
        log("Email report sent.")
    except Exception as e:
        log(f"WARNING: Email failed: {e}")

    if failures_report:
        toast_body = f"Relisted {len(relisted_report)}/10 — {len(failures_report)} failed"
    else:
        toast_body = f"Cycled {len(relisted_report)} | Ended {len(ended_zero_qty_report)} zero-qty"
    notify_toast("eBay Relist Agent", toast_body)

    log(f"=== Done — {len(relisted_report)} relisted, {len(ended_zero_qty_report)} zero-qty ended, {len(failures_report)} errors ===")

    # Clear progress.json so completed items don't show as "Completed" in the GUI
    try:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            log("Cleared progress.json")
    except Exception as e:
        log(f"WARNING: Could not delete progress.json: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eBay Listing Refresh Agent")
    parser.add_argument("--setup", action="store_true", help="Interactive first-time setup")
    args = parser.parse_args()
    if args.setup:
        interactive_setup()
    else:
        try:
            run()
        except Exception as e:
            import traceback
            msg = f"FATAL ERROR: {e}\n{traceback.format_exc()}"
            log(msg)
            with open(ERROR_LOG_FILE, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] {msg}\n")
            sys.exit(1)
