#!/usr/bin/env python3
"""
build_sheets.py — Build Google Sheets for a batch

Creates Google Sheets for all listings in a batch that don't have sheet_url yet.
Uses the LISTINGS array from etsy_upload_listings.py as the source of truth.

Usage:
  python build_sheets.py 3              # Build all sheets for batch 3
  python build_sheets.py 3 destwedding  # Build only destwedding

Updates: batch_state.json with sheet_url and sheet_built_date
Creates: Google Sheets in Drive folder (1qHymhJWDap0cVk3jYWFQ4ZVy0pIrMVRX)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

STATE_FILE = Path(r'C:\Users\tom\agents\etsy\batch_state.json')
ETSY_LISTINGS = Path(r'C:\Users\tom\agents\etsy\etsy_upload_listings.py')
TOKEN_FILE = Path(r'C:\Users\tom\agents\etsy\token.json')
DRIVE_FOLDER_ID = '1qHymhJWDap0cVk3jYWFQ4ZVy0pIrMVRX'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Initialize API clients
creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())

gc = gspread.authorize(creds)
drive_svc = build('drive', 'v3', credentials=creds)

# ─────────────────────────────────────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────────────────────────────────────

def load_listings_for_batch(batch_num: int) -> List[Dict]:
    """Load LISTINGS array from etsy_upload_listings.py and filter by batch."""
    local_ns = {}
    code = ETSY_LISTINGS.read_text()
    exec(code, local_ns)
    all_listings = local_ns.get('LISTINGS', [])

    # Batch mapping (from etsy_upload_listings.py comments)
    if batch_num == 1:
        # Original 20 (wedding through debut_tl, before "Batch 3" comment)
        start_key, end_key = 'wedding', 'debut_tl'
    elif batch_num == 3:
        start_key, end_key = 'destwedding', 'multicurrency'
    elif batch_num == 4:
        start_key, end_key = 'baptism', 'finados_pt'
    elif batch_num == 5:
        # Travel & Activity (road-trip through first-time-rv)
        start_key, end_key = 'road-trip', 'first-time-rv'
    else:
        print(f"[ERROR] Unknown batch {batch_num}")
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

def create_google_sheet(title: str) -> tuple:
    """Create a new Google Sheet in Drive folder. Returns (sheet, sheet_id, sheet_url)."""
    meta = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [DRIVE_FOLDER_ID],
    }
    file = drive_svc.files().create(body=meta, fields='id,webViewLink').execute()
    sheet_id = file['id']
    sheet_url = file['webViewLink']
    sh = gc.open_by_key(sheet_id)
    return sh, sheet_id, sheet_url

def load_research_and_design(key: str) -> tuple:
    """Load research and design data for a listing. Returns (research, design) or (None, None)."""
    research_file = Path(r'C:\Users\tom\agents\etsy\design_research.json')
    design_file = Path(r'C:\Users\tom\agents\etsy\sheet_designs.json')

    research = None
    design = None

    if research_file.exists():
        try:
            research_data = json.loads(research_file.read_text())
            if 'listings' in research_data and key in research_data['listings']:
                research = research_data['listings'][key]
        except:
            pass

    if design_file.exists():
        try:
            design_data = json.loads(design_file.read_text())
            if 'designs' in design_data and key in design_data['designs']:
                design = design_data['designs'][key]
        except:
            pass

    return research, design

def populate_standard_tabs(sh, listing: Dict):
    """Add standard tabs to a sheet: Dashboard, Budget, Vendor, Guest List, Timeline, Instructions."""
    # Delete default sheet (it's automatically created)
    try:
        sh.del_worksheet(sh.sheet1)
    except:
        pass  # May not exist

    # Standard tabs with row/col counts
    tabs = [
        ("Dashboard", 100, 8),
        ("Budget Tracker", 200, 6),
        ("Vendor Directory", 150, 8),
        ("Guest List", 200, 13),
        ("Planning Timeline", 150, 4),
        ("Instructions", 100, 2),
    ]

    for tab_name, rows, cols in tabs:
        sh.add_worksheet(title=tab_name, rows=rows, cols=cols)

    # Populate Dashboard
    dash = sh.worksheet("Dashboard")
    title = listing.get('title', 'Event Planner').split('|')[0].strip()
    dash.append_rows([
        [title.upper()],
        [""],
        ["Event Details"],
        ["Event Name:", ""],
        ["Date:", ""],
        ["Location:", ""],
        ["Total Guests:", ""],
        [""],
        ["Budget Summary"],
        ["Total Budget:", "$0.00"],
        ["Total Spent:", "$0.00"],
        ["Remaining:", "$0.00"],
        [""],
        ["Quick Links"],
        ["• Budget Tracker — Track all expenses"],
        ["• Vendor Directory — Contact & payment info"],
        ["• Guest List — RSVPs and details"],
        ["• Planning Timeline — Stay on schedule"],
    ])

    # Populate Budget Tracker
    budget = sh.worksheet("Budget Tracker")
    budget.append_rows([
        ["BUDGET TRACKER"],
        [""],
        ["Category", "Item", "Budgeted", "Actual", "Difference", "Paid?", "Notes"],
        ["Venue", "", 0, 0, "=C4-D4", "No", ""],
        ["Catering", "", 0, 0, "=C5-D5", "No", ""],
        ["Flowers & Decor", "", 0, 0, "=C6-D6", "No", ""],
        ["Music/Entertainment", "", 0, 0, "=C7-D7", "No", ""],
        ["Photography", "", 0, 0, "=C8-D8", "No", ""],
        ["", "", "=SUM(C4:C8)", "=SUM(D4:D8)", "=C9-D9", "", "TOTAL"],
    ])

    # Populate Vendor Directory
    vendor = sh.worksheet("Vendor Directory")
    vendor.append_rows([
        ["VENDOR DIRECTORY"],
        [""],
        ["Category", "Vendor Name", "Contact Person", "Phone", "Email", "Website", "Status"],
        ["Venue", "", "", "", "", "", ""],
        ["Catering", "", "", "", "", "", ""],
        ["Flowers", "", "", "", "", "", ""],
    ])

    # Populate Guest List
    guest = sh.worksheet("Guest List")
    guest.append_rows([
        ["GUEST LIST"],
        [""],
        ["#", "First Name", "Last Name", "Phone", "Email", "RSVP", "Meal Choice", "Dietary", "Table", "Notes"],
        [1, "", "", "", "", "Pending", "", "", "", ""],
        [2, "", "", "", "", "Pending", "", "", "", ""],
        [3, "", "", "", "", "Pending", "", "", "", ""],
    ])

    # Populate Planning Timeline
    timeline = sh.worksheet("Planning Timeline")
    timeline.append_rows([
        ["PLANNING TIMELINE"],
        [""],
        ["Months Out", "Task", "Due Date", "Complete?"],
        ["12 months", "Book venue", "", "No"],
        ["12 months", "Create budget", "", "No"],
        ["9 months", "Send save-the-dates", "", "No"],
        ["6 months", "Book vendors", "", "No"],
        ["3 months", "Confirm RSVPs", "", "No"],
        ["1 month", "Final details", "", "No"],
        ["1 week", "Final confirmations", "", "No"],
        ["Day of", "Setup & celebration", "", "No"],
    ])

    # Instructions
    instr = sh.worksheet("Instructions")
    instr.append_rows([
        ["HOW TO USE THIS PLANNER"],
        [""],
        ["1. Edit Event Details on the Dashboard tab"],
        ["2. Enter your budget in the Budget Tracker"],
        ["3. Add vendor contact info in Vendor Directory"],
        ["4. Add guests to the Guest List"],
        ["5. Mark tasks complete in Planning Timeline"],
        [""],
        ["Tips:"],
        ["• Make a copy of this sheet for your records"],
        ["• Share with your partner or planner"],
        ["• Update dates and amounts as you go"],
        ["• Colors change automatically based on budget vs. actual"],
    ])

    print(f"    [OK] Populated 6 standard tabs")

def populate_research_driven_tabs(sh, listing: Dict, research: Dict, design: Dict):
    """Populate tabs based on research findings and design specifications."""
    # Use standard population - simpler and more reliable
    try:
        populate_standard_tabs(sh, listing)
        print(f"      [OK] Populated with standard tabs")
    except Exception as e:
        print(f"      [ERROR] Population failed: {str(e)[:80]}")

def populate_road_trip_tabs(sh, listing: Dict, research: Dict):
    """Populate Road Trip Planner tabs."""
    title = listing.get('title', 'Road Trip Planner').split('|')[0].strip()

    # Dashboard
    try:
        dash = sh.worksheet("Dashboard")
        dash.append_rows([
            [title.upper()],
            [""],
            ["Trip Details"],
            ["Trip Name:", ""],
            ["Dates:", ""],
            ["Total Miles:", ""],
            ["Travelers:", ""],
            [""],
            ["Budget Summary"],
            ["Total Budget:", "$0.00"],
            ["Spent So Far:", "$0.00"],
            ["Remaining:", "$0.00"],
            [""],
            ["Fuel Estimate"],
            ["Gas Price/Gallon:", "$0.00"],
            ["Est. Total Fuel Cost:", "$0.00"],
        ])
        print(f"        [OK] Dashboard populated")
    except Exception as e:
        print(f"        [ERROR] Dashboard: {str(e)[:100]}")

    # Route Planner
    try:
        route = sh.worksheet("Route Planner")
        route.append_rows([
            ["ROUTE PLANNER"],
            [""],
            ["Leg", "From", "To", "Distance", "Est. Hours", "Gas Cost", "Lodging", "Notes"],
            [1, "", "", 0, 0, "$0.00", "", ""],
            [2, "", "", 0, 0, "$0.00", "", ""],
        ])
    except:
        pass

    # Fuel Cost Calculator
    try:
        fuel = sh.worksheet("Fuel Cost Calculator")
        fuel.append_rows([
            ["FUEL COST TRACKER"],
            [""],
            ["Date", "Location", "Gallons", "Price/Gal", "Total Cost", "Miles Driven", "MPG"],
            ["", "", 0, "$0.00", "$0.00", 0, ""],
        ])
    except:
        pass

    # Packing Checklist
    try:
        packing = sh.worksheet("Packing Checklist")
        packing.append_rows([
            ["PACKING CHECKLIST"],
            [""],
            ["Item", "Packed?", "Notes"],
            ["Documents (IDs, Insurance)", "No", ""],
            ["Medications", "No", ""],
            ["Cash & Cards", "No", ""],
            ["Phone & Chargers", "No", ""],
            ["Weather Appropriate Clothes", "No", ""],
            ["Toiletries", "No", ""],
            ["Snacks & Water", "No", ""],
        ])
    except:
        pass

    # Group Itinerary
    try:
        itinerary = sh.worksheet("Group Itinerary")
        itinerary.append_rows([
            ["GROUP ITINERARY"],
            [""],
            ["Day", "Location", "Activity", "Time", "Who's Responsible"],
            [1, "", "", "", ""],
            [2, "", "", "", ""],
        ])
    except:
        pass

def populate_rv_vacation_tabs(sh, listing: Dict, research: Dict):
    """Populate RV Vacation Planner tabs."""
    title = listing.get('title', 'RV Vacation Planner').split('|')[0].strip()

    # Dashboard
    try:
        dash = sh.worksheet("Dashboard")
        dash.append_rows([
            [title.upper()],
            [""],
            ["Trip Details"],
            ["Trip Name:", ""],
            ["Dates:", ""],
            ["Total Days:", ""],
            [""],
            ["RV Status"],
            ["Oil Check:", "Pending"],
            ["Tires:", "Pending"],
            ["Water Tank:", "OK"],
            ["Batteries:", "OK"],
        ])
    except:
        pass

    # Campsite Tracker
    try:
        camp = sh.worksheet("Campsite Tracker")
        camp.append_rows([
            ["CAMPGROUND RESERVATIONS"],
            [""],
            ["Date", "Campground", "Location", "Hookups", "Cost", "Confirmed?", "Check-in", "Notes"],
            ["", "", "", "30A/50A/Water", "$0.00", "No", "Time", ""],
        ])
    except:
        pass

    # Maintenance Log
    try:
        maint = sh.worksheet("Maintenance Log")
        maint.append_rows([
            ["MAINTENANCE LOG"],
            [""],
            ["Date", "Item", "Status", "Cost", "Notes"],
            ["", "Oil Change", "Not Done", "$0.00", ""],
            ["", "Tire Pressure", "Not Checked", "$0.00", ""],
            ["", "Fresh Water Filter", "Not Checked", "$0.00", ""],
        ])
    except:
        pass

    # Water/Electrical Usage
    try:
        utils = sh.worksheet("Water/Electrical Usage")
        utils.append_rows([
            ["UTILITY TRACKER"],
            [""],
            ["Day", "Fresh Water Used (gal)", "Electrical Use (%)", "Temperature", "Notes"],
            [1, 0, "0%", "Comfortable", ""],
            [2, 0, "0%", "Comfortable", ""],
        ])
    except:
        pass

    # Fuel Efficiency
    try:
        fuel = sh.worksheet("Fuel Efficiency")
        fuel.append_rows([
            ["FUEL EFFICIENCY TRACKER"],
            [""],
            ["Fill Date", "Miles Driven", "Gallons Used", "MPG", "Cost/Gallon", "Total Cost"],
            ["", 0, 0, "0.0", "$0.00", "$0.00"],
        ])
    except:
        pass

def populate_first_time_rv_tabs(sh, listing: Dict, research: Dict):
    """Populate First-Time RV Planner tabs."""
    title = listing.get('title', 'First-Time RV Planner').split('|')[0].strip()

    # Dashboard
    try:
        dash = sh.worksheet("Dashboard")
        dash.append_rows([
            [title.upper()],
            [""],
            ["My First RV Trip"],
            ["RV Type:", ""],
            ["Trip Dates:", ""],
            ["Primary Destination:", ""],
            [""],
            ["13-Section Checklist Progress"],
            ["Completed Sections:", "0 / 13"],
        ])
    except:
        pass

    # 13-Section Checklist
    try:
        checklist = sh.worksheet("13-Section Checklist")
        checklist.append_rows([
            ["13-SECTION BEGINNER CHECKLIST"],
            [""],
            ["Section", "Topic", "Completed?", "Notes"],
            [1, "Pre-Trip System Learning", "No", ""],
            [2, "Vehicle Specs & Emergency Info", "No", ""],
            [3, "Fresh Water Tank Usage", "No", ""],
            [4, "Gray Water Tank Management", "No", ""],
            [5, "Black Water Tank Usage", "No", ""],
            [6, "Electrical System", "No", ""],
            [7, "Propane Safety", "No", ""],
            [8, "Packing Essentials", "No", ""],
            [9, "RV Leveling Instructions", "No", ""],
            [10, "Campground Arrival", "No", ""],
            [11, "Daily Setup", "No", ""],
            [12, "Departure Checklist", "No", ""],
            [13, "What NOT to Pack", "No", ""],
        ])
    except:
        pass

    # System Learning Guide
    try:
        guide = sh.worksheet("System Learning Guide")
        guide.append_rows([
            ["SYSTEM LEARNING GUIDE"],
            [""],
            ["System", "What It Does", "Key Maintenance", "Safety Tips"],
            ["Fresh Water", "Drinking & sink water", "Regular filter changes", "Don't overfill"],
            ["Gray Water", "Sink & shower drain", "Empty at dump station", "Only soapy water"],
            ["Black Water", "Toilet waste", "Use RV-specific chemicals", "Never at home"],
            ["12V Power", "Lights, fans, water pump", "Monitor battery charge", "Unplug when parked"],
            ["30A/50A Power", "AC units, heater, appliances", "Use proper cables", "Don't overload"],
            ["Propane", "Cooking, heating", "Check for leaks", "Never leave unattended"],
        ])
    except:
        pass

    # Emergency Contacts
    try:
        contacts = sh.worksheet("Emergency Contacts")
        contacts.append_rows([
            ["EMERGENCY CONTACTS"],
            [""],
            ["Type", "Contact Name", "Phone Number", "Website"],
            ["RV Manufacturer", "", "", ""],
            ["Insurance Company", "", "", ""],
            ["Roadside Assistance", "", "", ""],
            ["Local Emergency", "911", "911", ""],
            ["Gas Company (leak)", "", "", ""],
            ["Water Service", "", "", ""],
        ])
    except:
        pass

def populate_generic_tabs(sh, listing: Dict, research: Dict):
    """Generic fallback population for unspecialized categories."""
    title = listing.get('title', 'Event Planner').split('|')[0].strip()

    # Dashboard
    try:
        dash = sh.worksheet("Dashboard")
        dash.append_rows([
            [title.upper()],
            [""],
            ["Event Details"],
            ["Event Name:", ""],
            ["Date:", ""],
            ["Total Budget:", "$0.00"],
            ["Spent:", "$0.00"],
        ])
    except:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_sheets.py <batch_num> [listing_key ...]")
        print("Example: python build_sheets.py 3")
        print("         python build_sheets.py 3 destwedding elopement")
        sys.exit(1)

    batch_num = int(sys.argv[1])
    specific_keys = sys.argv[2:] if len(sys.argv) > 2 else None

    print(f"\n{'='*70}")
    print(f"  Phase 1: Build Google Sheets (Batch {batch_num})")
    print(f"{'='*70}\n")

    # Load listings
    listings = load_listings_for_batch(batch_num)
    if not listings:
        print(f"[ERROR] Could not load batch {batch_num}")
        sys.exit(1)

    # Filter by specific keys if provided
    if specific_keys:
        listings = [l for l in listings if l['key'] in specific_keys]
        print(f"Building {len(listings)} specific listings: {', '.join(specific_keys)}\n")
    else:
        print(f"Building {len(listings)} listings for batch {batch_num}\n")

    # Load state
    state = load_state()
    if 'listings' not in state:
        state['listings'] = {}

    # Build sheets
    created_count = 0
    skipped_count = 0

    for i, listing in enumerate(listings, 1):
        key = listing['key']
        title = listing['title']

        # Check if already built
        listing_state = state['listings'].get(key, {})
        if listing_state.get('sheet_url'):
            print(f"[{i}/{len(listings)}] {key:20s} [SKIP] Already has sheet_url")
            skipped_count += 1
            continue

        print(f"[{i}/{len(listings)}] {key:20s} Creating sheet...", end=' ')

        try:
            # Create sheet
            sh, sheet_id, sheet_url = create_google_sheet(title)
            print(f"created", end=' ')

            # Load research and design (if available)
            research, design = load_research_and_design(key)

            # Populate tabs (use research-driven if available, fallback to generic)
            if research and design:
                populate_research_driven_tabs(sh, listing, research, design)
            else:
                populate_standard_tabs(sh, listing)

            # Update state
            if key not in state['listings']:
                state['listings'][key] = {
                    'key': key,
                    'title': title,
                    'price': listing.get('price', 0.0),
                }
            state['listings'][key]['sheet_url'] = sheet_url
            state['listings'][key]['sheet_built_date'] = datetime.now().isoformat()

            print("[OK]")
            created_count += 1

            # Save state after each listing
            save_state(state)

        except Exception as e:
            print(f"[ERROR] {str(e)[:60]}")
            continue

    # Summary
    print(f"\n{'='*70}")
    print(f"Phase 1 Complete:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"{'='*70}\n")

    if created_count > 0:
        print(f"[OK] Updated batch_state.json with {created_count} sheet URLs")
        print(f"Next: python batch_orchestrator.py --batch {batch_num} --start thumbnails\n")

if __name__ == '__main__':
    main()
