#!/usr/bin/env python3
from auth import get_access_token, load_config
from ebay_api import fetch_all_active_listings

cfg = load_config()
token = get_access_token(cfg)

print("Checking for item 287310763170...")
all_items = fetch_all_active_listings(cfg, token)
target = next((item for item in all_items if item["item_id"] == "287310763170"), None)

if target:
    print(f"\nFOUND - Item is STILL ACTIVE (needs to be relisted)")
    print(f"  Item ID: 287310763170")
    print(f"  Title: {target['title']}")
    print(f"  Start Time: {target['start_time']}")
else:
    print(f"\nNOT FOUND - Item either relisted or manually ended")
    print(f"Check eBay directly for item 287310763170")
