#!/usr/bin/env python3
"""
eBay Listing Refresh Agent

Daily: ends the 10 oldest fixed-price active listings and re-creates them fresh.
Also ends any zero-quantity listings without relisting them.
Emails a report to tomnissley@gmail.com after each run.

First run:  python ebay_relist_agent.py --setup
Ongoing:    python ebay_relist_agent.py
"""

import argparse
import json
import os
import sys
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

# Handle PyInstaller bundled paths
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "relist_log.json"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


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


def run() -> None:
    today = date.today().isoformat()
    log(f"=== eBay Relist Agent starting ({today}) ===")

    cfg = load_config()
    token = get_access_token(cfg)

    log("Fetching all active listings...")
    all_items = fetch_all_active_listings(cfg, token)
    log(f"  {len(all_items)} active listings found")

    zero_qty, eligible = partition_listings(all_items)
    per_run = cfg.get("listings_per_run", 10)
    to_relist = select_oldest(eligible, n=per_run)
    log(f"  {len(zero_qty)} zero-qty | {len(eligible)} eligible | {len(to_relist)} to relist (limit: {per_run})")

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

    PROGRESS_FILE = BASE_DIR / "progress.json"
    total_items = len(to_relist)
    completed = 0

    for idx, item in enumerate(to_relist, start=1):
        iid = item["item_id"]
        start_time = datetime.now().isoformat()

        # Stage 1: Getting listing
        with open(PROGRESS_FILE, "w") as f:
            json.dump({
                "completed": completed,
                "total": total_items,
                "item_id": iid,
                "title": item["title"],
                "stage": "Getting listing"
            }, f)

        try:
            fields = get_item(cfg, token, iid)
        except Exception as e:
            log(f"  ERROR GetItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"GetItem failed: {e}"})
            end_time = datetime.now().isoformat()
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        # Stage 2: Delisting old
        with open(PROGRESS_FILE, "w") as f:
            json.dump({
                "completed": completed,
                "total": total_items,
                "item_id": iid,
                "title": item["title"],
                "stage": "Delisting old"
            }, f)

        try:
            end_item(cfg, token, iid)
        except Exception as e:
            log(f"  WARNING EndItem {iid} failed: {e}")

        # Stage 3: Verifying deletion
        with open(PROGRESS_FILE, "w") as f:
            json.dump({
                "completed": completed,
                "total": total_items,
                "item_id": iid,
                "title": item["title"],
                "stage": "Verifying deletion"
            }, f)

        # Wait for deletion confirmation before relisting
        import time
        time.sleep(5)  # Wait 5 seconds for eBay to process deletion

        # Stage 4: Creating new listing
        with open(PROGRESS_FILE, "w") as f:
            json.dump({
                "completed": completed,
                "total": total_items,
                "item_id": iid,
                "title": item["title"],
                "stage": "Creating new listing"
            }, f)

        try:
            new_id = add_item(cfg, token, fields)
        except Exception as e:
            log(f"  ERROR AddItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"AddItem failed: {e}"})
            end_time = datetime.now().isoformat()
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        # KFF process sanity check — free via Ollama
        kff_result = kff_check(
            "process",
            agent="ebay-relist-agent",
            step="relist",
            context=f"Relisted item {iid} as {new_id}: title='{item['title']}'"
        )
        if kff_result.get("status") == "flag":
            log(f"  KFF flagged relist {iid} -> {new_id}: {kff_result.get('suggestion', '')}")

        end_time = datetime.now().isoformat()
        log(f"  Relisted: {iid} -> {new_id} — {item['title']}")
        relisted_report.append({"old_id": iid, "new_id": new_id, "title": item["title"]})
        log_entries.append({
            "date": today, "start_time": start_time, "end_time": end_time, "old_item_id": iid, "new_item_id": new_id,
            "title": item["title"], "status": "relisted",
        })
        completed += 1

    append_log(log_entries)

    # Write final progress state before cleanup
    with open(PROGRESS_FILE, "w") as f:
        json.dump({
            "completed": completed,
            "total": total_items,
            "stage": "Completed"
        }, f)

    # Clean up progress file
    try:
        PROGRESS_FILE.unlink()
    except:
        pass

    body = format_report(relisted_report, ended_zero_qty_report, failures_report)
    subject = format_subject(today)
    try:
        send_email(
            password=cfg["gmail_app_password"],
            subject=subject,
            body=body,
            sender=cfg["gmail_email"],
            recipient=cfg["report_email"],
            smtp_host=cfg.get("smtp_server", "smtp.gmail.com"),
            smtp_port=cfg.get("smtp_port", 465)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eBay Listing Refresh Agent")
    parser.add_argument("--setup", action="store_true", help="Interactive first-time setup")
    args = parser.parse_args()
    if args.setup:
        interactive_setup()
    else:
        run()
