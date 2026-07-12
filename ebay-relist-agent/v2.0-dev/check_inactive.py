#!/usr/bin/env python3
import xml.etree.ElementTree as ET

from auth import get_access_token, load_config
from ebay_api import trading_call, _t

cfg = load_config()
token = get_access_token(cfg)

# Fetch inactive listings
body = """
  <InactiveList>
    <Include>true</Include>
    <Pagination><EntriesPerPage>200</EntriesPerPage><PageNumber>1</PageNumber></Pagination>
  </InactiveList>"""

root = trading_call(cfg, token, "GetMyeBaySelling", body)
inactive_list = root.find(_t("InactiveList"))
item_array = inactive_list.find(_t("ItemArray")) if inactive_list is not None else None

print(f"Found {len(item_array or [])} inactive items\n")

# Get the 8 items that were relisted today from run.log
relisted_ids = [
    "287293965539", "287293965546", "287296271469", "287296271478",
    "287296271481", "287296271488", "287310763167", "287310763168"
]

recently_ended = []
for item in (item_array.findall(_t("Item")) if item_array is not None else []):
    item_id = item.findtext(_t("ItemID")) or ""
    title = item.findtext(_t("Title")) or ""

    if item_id in relisted_ids:
        print(f"✓ {item_id} — {title[:70]}")
    else:
        recently_ended.append((item_id, title))
        print(f"✗ {item_id} — {title[:70]}")

print(f"\n=== {len(recently_ended)} items ENDED but NOT RELISTED ===")
for iid, title in recently_ended[:10]:
    print(f"\n  ID: {iid}")
    print(f"  Title: {title}")
