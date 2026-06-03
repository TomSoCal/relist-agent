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

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "relist_log.json"
BACKUP_FILE = BASE_DIR / "item_backups.json"
ERROR_LOG_FILE = BASE_DIR / "error_log.txt"


def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{ts}] {msg}"
    print(formatted)
    try:
        with open(BASE_DIR / "run.log", "a", encoding="utf-8") as f:
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

    for item in to_relist:
        iid = item["item_id"]
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            fields = get_item(cfg, token, iid)
        except Exception as e:
            log(f"  ERROR GetItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"GetItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        # CRITICAL: End old listing FIRST, before creating new one (prevents duplicate policy violation)
        try:
            end_item(cfg, token, iid)
            log(f"  Delisted: {iid}")
        except Exception as e:
            log(f"  ERROR EndItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"EndItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({"date": today, "start_time": start_time, "end_time": end_time, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        # Wait for eBay to process the delisting (prevents duplicate policy errors)
        time.sleep(2)

        try:
            new_id = add_item(cfg, token, fields)
        except Exception as e:
            log(f"  ERROR AddItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"AddItem failed: {e}"})
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

        log(f"  Relisted: {iid} -> {new_id} — {item['title']}")
        relisted_report.append({"old_id": iid, "new_id": new_id, "title": item["title"]})

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
