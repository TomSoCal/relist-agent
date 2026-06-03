#!/usr/bin/env python3
"""
Relist previously failed items using the fixed delist-first logic
"""
import json
import time
from datetime import date, datetime
from pathlib import Path

from auth import get_access_token, load_config
from ebay_api import add_item, end_item, get_item

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "relist_log.json"
CONFIG_FILE = BASE_DIR / "config.json"

# Items that failed with duplicate policy errors
FAILED_ITEMS = [
    "287310763184",  # Dyson Vacuum Flexible Extendable Crevice Tool
    "287310763185",  # Dyson Vacuum Combination Tool Attachment
    "287310763188",  # Shark Vacuum Upholstery Fabric Tool
]


def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")


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


def main():
    log("=== Relisting Failed Items (using fixed delist-first logic) ===")

    cfg = load_config()
    if not cfg.get("app_id"):
        log("ERROR: Config not found. Run setup first.")
        return

    token = get_access_token(cfg)
    today = date.today().isoformat()
    log_entries = []
    relisted = []
    failed = []

    for item_id in FAILED_ITEMS:
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log(f"\nProcessing: {item_id}")

        # Step 1: Get item details
        try:
            item_data = get_item(cfg, token, item_id)
            title = item_data.get("title", "Unknown")
            log(f"  [OK] Got item details: {title}")
        except Exception as e:
            log(f"  [FAIL] GetItem failed: {e}")
            failed.append({"item_id": item_id, "reason": str(e)})
            continue

        # Step 2: Try to end old listing (may already be closed)
        try:
            end_item(cfg, token, item_id)
            log(f"  [OK] Delisted old item")
            time.sleep(2)  # Wait for deletion to process
        except Exception as e:
            if "already been closed" in str(e) or "has been closed" in str(e):
                log(f"  [INFO] Item already closed, skipping delist")
                time.sleep(1)
            else:
                log(f"  [WARN] EndItem: {e}")
                # Continue anyway - try to relist

        # Step 4: Create new listing
        try:
            new_id = add_item(cfg, token, item_data)
            log(f"  [OK] Relisted as: {new_id}")
            relisted.append({"old_id": item_id, "new_id": new_id, "title": title})

            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entries.append({
                "date": today,
                "start_time": start_time,
                "end_time": end_time,
                "old_item_id": item_id,
                "new_item_id": new_id,
                "title": title,
                "status": "relisted",
                "note": "recovered - failed item relisted successfully"
            })
        except Exception as e:
            log(f"  [FAIL] AddItem failed: {e}")
            log(f"  [INFO] Waiting 5s before retry...")
            time.sleep(5)

            # Retry once
            try:
                new_id = add_item(cfg, token, item_data)
                log(f"  [OK] Relisted as: {new_id} (retry succeeded)")
                relisted.append({"old_id": item_id, "new_id": new_id, "title": title})

                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_entries.append({
                    "date": today,
                    "start_time": start_time,
                    "end_time": end_time,
                    "old_item_id": item_id,
                    "new_item_id": new_id,
                    "title": title,
                    "status": "relisted",
                    "note": "recovered - failed item relisted on retry"
                })
            except Exception as e2:
                log(f"  [FAIL] Retry failed: {e2}")
                failed.append({"item_id": item_id, "reason": str(e2)})

    # Log results
    if log_entries:
        append_log(log_entries)

    log(f"\n=== Results ===")
    log(f"[SUCCESS] Relisted: {len(relisted)}")
    for item in relisted:
        log(f"  {item['old_id']} -> {item['new_id']}")

    if failed:
        log(f"[FAILED] Failed: {len(failed)}")
        for item in failed:
            log(f"  {item['item_id']}: {item['reason']}")
    else:
        log(f"[SUCCESS] All items relisted successfully!")


if __name__ == "__main__":
    main()
