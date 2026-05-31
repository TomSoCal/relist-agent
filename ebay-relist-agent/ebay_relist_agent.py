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
    to_relist = select_oldest(eligible, n=10)
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
        try:
            fields = get_item(cfg, token, iid)
        except Exception as e:
            log(f"  ERROR GetItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"GetItem failed: {e}"})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        try:
            end_item(cfg, token, iid)
        except Exception as e:
            log(f"  WARNING EndItem {iid} failed: {e}")

        try:
            new_id = add_item(cfg, token, fields)
        except Exception as e:
            log(f"  ERROR AddItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"AddItem failed: {e}"})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
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
        log_entries.append({
            "date": today, "old_item_id": iid, "new_item_id": new_id,
            "title": item["title"], "status": "relisted",
        })

    append_log(log_entries)

    body = format_report(relisted_report, ended_zero_qty_report, failures_report)
    subject = format_subject(today)
    try:
        send_email(cfg["gmail_app_password"], subject, body)
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
