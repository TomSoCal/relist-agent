#!/usr/bin/env python3
"""
generate_thumbnails.py — Screenshot Google Sheets for Etsy listings

Captures 5 high-quality PNG images from each sheet:
  1. Hero image (Dashboard tab)
  2. Budget Tracker tab
  3. Guest List tab
  4. Vendor Directory tab
  5. All tabs visible (shows comprehensiveness)

Usage:
  python generate_thumbnails.py 3              # All batch 3
  python generate_thumbnails.py 3 destwedding  # Specific listing

Updates: batch_state.json with thumbnails=true
Creates: PNG files in thumbnails/{key}/thumb_1_hero.png, etc.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from playwright.sync_api import sync_playwright

STATE_FILE = Path(r'C:\Users\tom\agents\etsy\batch_state.json')
ETSY_LISTINGS = Path(r'C:\Users\tom\agents\etsy\etsy_upload_listings.py')
THUMB_DIR = Path(r'C:\Users\tom\agents\etsy\thumbnails')

# ─────────────────────────────────────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────────────────────────────────────

def load_listings_for_batch(batch_num: int) -> List[Dict]:
    """Load LISTINGS from etsy_upload_listings.py and filter by batch."""
    local_ns = {}
    code = ETSY_LISTINGS.read_text()
    exec(code, local_ns)
    all_listings = local_ns.get('LISTINGS', [])

    if batch_num == 1:
        start_key, end_key = 'wedding', 'debut_tl'
    elif batch_num == 3:
        start_key, end_key = 'destwedding', 'multicurrency'
    elif batch_num == 4:
        start_key, end_key = 'baptism', 'finados_pt'
    elif batch_num == 5:
        start_key, end_key = 'road-trip', 'first-time-rv'
    else:
        return []

    start_idx = next((i for i, l in enumerate(all_listings) if l.get('key') == start_key), None)
    end_idx = next((i for i, l in enumerate(all_listings) if l.get('key') == end_key), None)

    if start_idx is not None and end_idx is not None:
        return all_listings[start_idx:end_idx+1]

    return []

def load_state() -> Dict:
    """Load batch_state.json."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'metadata': {}, 'listings': {}}

def save_state(state: Dict):
    """Save batch_state.json."""
    state['metadata']['last_updated'] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))

def screenshot_sheet(sheet_url: str, tab_name: str, output_path: Path) -> bool:
    """
    Take a screenshot of a specific sheet tab using Playwright.
    Returns True if successful.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1600, 'height': 1200})

            # Navigate to sheet
            page.goto(sheet_url, wait_until='networkidle')
            time.sleep(1)

            # Click on the tab if not the first one
            if tab_name != 'Dashboard':
                try:
                    # Find tab by text
                    tab_button = page.locator(f'text="{tab_name}"').first
                    if tab_button.is_visible():
                        tab_button.click()
                        time.sleep(0.5)
                except:
                    pass

            # Take screenshot
            page.screenshot(path=str(output_path))
            browser.close()

            return True

    except Exception as e:
        print(f"              [ERROR] Screenshot failed: {str(e)[:50]}")
        return False

def generate_thumbnails_for_listing(key: str, sheet_url: str, output_dir: Path) -> bool:
    """Generate 5 thumbnail images for a listing."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tabs = [
        ('Dashboard', 'thumb_1_hero.png'),
        ('Budget Tracker', 'thumb_2_budget.png'),
        ('Guest List', 'thumb_3_guests.png'),
        ('Vendor Directory', 'thumb_4_vendors.png'),
        ('Instructions', 'thumb_5_instructions.png'),
    ]

    success_count = 0
    for tab_name, filename in tabs:
        output_path = output_dir / filename
        if output_path.exists() and output_path.stat().st_size > 10000:
            # Skip if already exists and is large (good quality)
            success_count += 1
            continue

        if screenshot_sheet(sheet_url, tab_name, output_path):
            success_count += 1

    return success_count == len(tabs)

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_thumbnails.py <batch_num> [listing_key ...]")
        print("Example: python generate_thumbnails.py 3")
        print("         python generate_thumbnails.py 3 destwedding elopement")
        sys.exit(1)

    batch_num = int(sys.argv[1])
    specific_keys = sys.argv[2:] if len(sys.argv) > 2 else None

    print(f"\n{'='*70}")
    print(f"  Phase 2: Generate Thumbnails (Batch {batch_num})")
    print(f"{'='*70}\n")

    # Load listings
    listings = load_listings_for_batch(batch_num)
    if not listings:
        print(f"[ERROR] Could not load batch {batch_num}")
        sys.exit(1)

    # Filter by specific keys
    if specific_keys:
        listings = [l for l in listings if l['key'] in specific_keys]

    # Load state
    state = load_state()
    if 'listings' not in state:
        state['listings'] = {}

    # Generate thumbnails
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for i, listing in enumerate(listings, 1):
        key = listing['key']
        listing_state = state['listings'].get(key, {})
        sheet_url = listing_state.get('sheet_url')

        if not sheet_url:
            print(f"[{i}/{len(listings)}] {key:20s} [SKIP] No sheet_url (run build_sheets first)")
            skipped_count += 1
            continue

        print(f"[{i}/{len(listings)}] {key:20s} Screenshotting...", end=' ')

        # Check if already done
        thumb_dir = THUMB_DIR / key
        if listing_state.get('thumbnails'):
            if (thumb_dir / 'thumb_1_hero.png').exists():
                print("[SKIP] Already generated")
                skipped_count += 1
                continue

        # Generate thumbnails
        if generate_thumbnails_for_listing(key, sheet_url, thumb_dir):
            print("[OK]")
            success_count += 1

            # Update state
            if key not in state['listings']:
                state['listings'][key] = {'key': key}
            state['listings'][key]['thumbnails'] = True
            state['listings'][key]['thumbnails_date'] = datetime.now().isoformat()
            save_state(state)

        else:
            print("[FAIL]")
            failed_count += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"Phase 2 Complete:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed:  {failed_count}")
    print(f"{'='*70}\n")

    if failed_count == 0 and success_count > 0:
        print(f"[OK] Generated thumbnails for {success_count} listings")
        print(f"     Files saved to: {THUMB_DIR}")
        print(f"Next: python batch_orchestrator.py --batch {batch_num} --start video\n")

if __name__ == '__main__':
    main()
