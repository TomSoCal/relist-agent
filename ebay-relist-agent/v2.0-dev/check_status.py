#!/usr/bin/env python3
import json
from pathlib import Path
from auth import get_access_token, load_config
from ebay_api import fetch_all_active_listings

cfg = load_config()
token = get_access_token(cfg)

print("Fetching all active listings...")
all_items = fetch_all_active_listings(cfg, token)
print(f"Total active: {len(all_items)}\n")

# Items relisted today (from run.log)
relisted_today = {
    "287293965539", "287293965546", "287296271469", "287296271478",
    "287296271481", "287296271488", "287310763167", "287310763168"
}

# New listings added today (mapping old -> new from run.log)
relisted_map = {
    "287293965539": "287369962147",
    "287293965546": "287369963008",
    "287296271469": "287369963771",
    "287296271478": "287369964752",
    "287296271481": "287369968283",
    "287296271488": "287369973441",
    "287310763167": "287369974494",
    "287310763168": "287369976017",
}

print("Checking if relisted items are still in active...")
for old_id, new_id in relisted_map.items():
    old_found = any(item["item_id"] == old_id for item in all_items)
    new_found = any(item["item_id"] == new_id for item in all_items)
    status = f"  Old {old_id}: {'ACTIVE' if old_found else 'ENDED'} -> New {new_id}: {'ACTIVE' if new_found else 'PENDING'}"
    print(status)

print(f"\nLooking for which 2 items were NOT processed...")
# Fetch the list of items that should have been relisted
# The script selects the 10 oldest eligible items
print("\nNeed more info: which 10 items were candidates for relisting?")
