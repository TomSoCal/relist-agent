#!/usr/bin/env python3
import json
from pathlib import Path

LOG_FILE = Path("relist_log.json")

# Read existing log
with open(LOG_FILE, "r", encoding="utf-8") as f:
    entries = json.load(f)

# Add the 9 missing relists from the first run (10:30)
new_entries = [
    {"date": "2026-06-02", "old_item_id": "287293965539", "new_item_id": "287369962147", "title": "ECF3000 Filter Elkay EZH2O WaterSentry Plus Compatible Sealed", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287293965546", "new_item_id": "287369963008", "title": "Dept 56 Hard Rock Cafe Orlando Lighted Ornament Snow Village Boxed", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287296271469", "new_item_id": "287369963771", "title": "Ninja 4-Blade Food Chopper Replacement Blade Fits QB1005 QB900 Master Prep 5 Cup", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287296271478", "new_item_id": "287369964752", "title": "Ninja Master Prep Professional 6-Blade Replacement Assembly - Fits 48 oz Pitcher", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287296271481", "new_item_id": "287369968283", "title": "Ninja Master Prep 48 oz Pitcher with Lid - Replacement Blender Part QB900", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287296271488", "new_item_id": "287369973441", "title": "Ninja Master Prep Professional Blender Pitcher Blade - 16 oz Replacement Part", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287310763167", "new_item_id": "287369974494", "title": "Dyson Vacuum Mini Turbine Head Power Brush Tool 915034-02 Genuine", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287310763168", "new_item_id": "287369976017", "title": "Dyson Vacuum Telescoping Crevice Brush Tool 2-in-1 Attachment", "status": "relisted"},
    {"date": "2026-06-02", "old_item_id": "287310763169", "new_item_id": "287369978384", "title": "iRobot Roomba Front Wheel Caster Assembly Genuine Replacement e5 e6 i1 i3 i4 i6", "status": "relisted"},
]

entries.extend(new_entries)

# Write back
with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2)

print(f"Added 9 entries. Total entries now: {len(entries)}")
