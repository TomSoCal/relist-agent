#!/usr/bin/env python3
"""
research_event_categories.py — Research event categories to inform sheet design

Gathers information about each event type from etsy_upload_listings.py
to create category-specific sheet designs (not generic templates).

Usage:
  python research_event_categories.py              # All listings
  python research_event_categories.py 3           # Batch 3
  python research_event_categories.py wedding     # Single listing

Output: Creates design_research.json with category insights
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

RESEARCH_FILE = Path(r'C:\Users\tom\agents\etsy\design_research.json')
ETSY_LISTINGS = Path(r'C:\Users\tom\agents\etsy\etsy_upload_listings.py')

# Category Research Database
# Format: key → {description, typical_attendees, key_sections, budget_categories, ...}
CATEGORY_RESEARCH = {
    'wedding': {
        'description': 'Wedding Planning',
        'audience': 'Engaged couples, wedding planners',
        'timeline_months': 12,
        'typical_attendees': '50-300',
        'key_sections': ['Ceremony', 'Reception', 'Vendor Coordination', 'Guest Management', 'Timeline'],
        'budget_categories': ['Venue', 'Catering', 'Photography', 'Flowers & Decor', 'Music/DJ', 'Cake', 'Invitations', 'Attire', 'Transportation', 'Favors'],
        'unique_tabs': ['Seating Chart', 'Vendor Directory', 'Guest RSVP Tracker'],
        'complexity': 'high',
    },
    'babyshower': {
        'description': 'Baby Shower Planning',
        'audience': 'Expectant mothers, co-hosts',
        'timeline_months': 2,
        'typical_attendees': '15-50',
        'key_sections': ['Theme', 'Guest List', 'Games', 'Budget'],
        'budget_categories': ['Venue/Supplies', 'Decorations', 'Food & Drinks', 'Games & Activities', 'Favors', 'Cake'],
        'unique_tabs': ['Gift Registry', 'Games & Activities', 'Timeline'],
        'complexity': 'medium',
    },
    'quinceanera': {
        'description': 'Quinceañera Planning',
        'audience': 'Parents of 15-year-old girls, cultural event planners',
        'timeline_months': 6,
        'typical_attendees': '100-300',
        'key_sections': ['Court of Honor', 'Ceremony', 'Reception', 'Traditions', 'Guest List'],
        'budget_categories': ['Venue', 'Catering', 'Dress', 'Photography', 'Flowers', 'Music', 'Decorations'],
        'unique_tabs': ['Court of Honor Tracker', 'Dress & Attire', 'Traditional Elements'],
        'complexity': 'high',
    },
    'corporate': {
        'description': 'Corporate Event Planning',
        'audience': 'Event planners, HR professionals',
        'timeline_months': 3,
        'typical_attendees': '50-500',
        'key_sections': ['Objective', 'Budget', 'Vendors', 'Logistics', 'Staff Coordination'],
        'budget_categories': ['Venue', 'Catering', 'AV/Tech', 'Decorations', 'Entertainment', 'Materials', 'Staff'],
        'unique_tabs': ['Sponsor Tracker', 'Vendor Directory', 'Logistics Coordinator'],
        'complexity': 'high',
    },
    'graduation': {
        'description': 'Graduation Party Planning',
        'audience': 'Parents, students',
        'timeline_months': 2,
        'typical_attendees': '25-100',
        'key_sections': ['Celebration Theme', 'Guest List', 'Budget', 'Food & Entertainment'],
        'budget_categories': ['Venue', 'Decorations', 'Food & Drinks', 'Cake', 'Entertainment', 'Favors'],
        'unique_tabs': ['Guest List', 'Party Checklist', 'Timeline'],
        'complexity': 'medium',
    },
    'retirement': {
        'description': 'Retirement Party Planning',
        'audience': 'Family members, colleagues',
        'timeline_months': 1,
        'typical_attendees': '25-100',
        'key_sections': ['Guest Invitations', 'Budget', 'Tribute Planning', 'Memory Collection'],
        'budget_categories': ['Venue', 'Food & Drinks', 'Decorations', 'Entertainment', 'Cake', 'Gifts'],
        'unique_tabs': ['Guest List', 'Memory Tribute', 'Event Timeline'],
        'complexity': 'medium',
    },
    'bachelorette': {
        'description': 'Bachelorette Party Planning',
        'audience': 'Bridesmaids, friends of bride',
        'timeline_months': 2,
        'typical_attendees': '6-20',
        'key_sections': ['Guest List', 'Activity Planning', 'Budget', 'Timeline'],
        'budget_categories': ['Venue/Accommodations', 'Meals & Drinks', 'Activities', 'Decorations', 'Favors'],
        'unique_tabs': ['Activity Planner', 'Cost Split Tracker', 'Guest Preferences'],
        'complexity': 'medium',
    },
    'familyreunion': {
        'description': 'Family Reunion Planning',
        'audience': 'Family organizers',
        'timeline_months': 3,
        'typical_attendees': '50-200',
        'key_sections': ['Family Tree/Groups', 'Guest Coordination', 'Activities', 'Budget'],
        'budget_categories': ['Venue', 'Food & Drinks', 'Decorations', 'Activities/Games', 'Supplies'],
        'unique_tabs': ['Family Groups', 'Activities & Games', 'Guest List by Family'],
        'complexity': 'medium',
    },
    'destination_wedding': {
        'description': 'Destination Wedding Planning',
        'audience': 'Couples, wedding planners',
        'timeline_months': 12,
        'typical_attendees': '30-100',
        'key_sections': ['Travel Logistics', 'Accommodations', 'Ceremony & Reception', 'Guest Communication'],
        'budget_categories': ['Travel', 'Accommodations', 'Venue', 'Catering', 'Activities', 'Local Vendors'],
        'unique_tabs': ['Travel Planner', 'Accommodation Coordinator', 'Vendor Directory'],
        'complexity': 'high',
    },
    'hinduwedding': {
        'description': 'Hindu Wedding Planning',
        'audience': 'Hindu couples, families',
        'timeline_months': 12,
        'typical_attendees': '200-1000+',
        'key_sections': ['Multi-Day Events', 'Ceremony Details', 'Religious Elements', 'Guest Management'],
        'budget_categories': ['Venue(s)', 'Catering', 'Decorations', 'Clothing/Attire', 'Entertainment', 'Gifts'],
        'unique_tabs': ['Multi-Day Event Schedule', 'Ceremony Rituals', 'Vendor Directory'],
        'complexity': 'high',
    },
    'road_trip': {
        'description': 'Road Trip Planning',
        'audience': 'Budget-conscious travelers (ages 25-45)',
        'timeline_months': 1,
        'typical_attendees': '1-6',
        'key_sections': ['Route Planning', 'Budget Tracking', 'Itinerary', 'Emergency Contacts', 'Landmarks'],
        'budget_categories': ['Gas/Fuel', 'Food', 'Lodging', 'Activities', 'Parking/Tolls', 'Car Maintenance'],
        'unique_tabs': ['Route Planner', 'Fuel Cost Calculator', 'Packing Checklist', 'Group Itinerary'],
        'complexity': 'low',
    },
    'rv_vacation': {
        'description': 'RV Vacation Planning',
        'audience': 'RV owners with 1+ years experience (ages 30-60)',
        'timeline_months': 2,
        'typical_attendees': '1-8',
        'key_sections': ['Campsite Reservations', 'RV Maintenance', 'Utility Tracking', 'Local Activities'],
        'budget_categories': ['Campground Fees', 'Fuel/Gas', 'Maintenance', 'Activities', 'Supplies', 'Meals'],
        'unique_tabs': ['Campsite Tracker', 'Maintenance Log', 'Water/Electrical Usage', 'Fuel Efficiency'],
        'complexity': 'medium',
    },
    'first_time_rv': {
        'description': 'First-Time RV Planning',
        'audience': 'First-time RV owners (ages 25-45) with zero experience',
        'timeline_months': 1,
        'typical_attendees': '1-8',
        'key_sections': ['System Learning', 'Water Management', 'Electrical Systems', 'Propane Safety', 'Leveling'],
        'budget_categories': ['Campground Fees', 'Fuel', 'Supplies', 'Groceries', 'Activities'],
        'unique_tabs': ['13-Section Checklist', 'System Learning Guide', 'Emergency Contacts', 'Pre-Trip Checklist'],
        'complexity': 'high',
    },
}

def load_listings() -> Dict[str, Any]:
    """Load LISTINGS from etsy_upload_listings.py."""
    local_ns = {}
    code = ETSY_LISTINGS.read_text()
    exec(code, local_ns)
    return {l['key']: l for l in local_ns.get('LISTINGS', [])}

def get_research_for_listing(key: str, listing: Dict) -> Dict:
    """Get research data for a listing."""
    title = listing.get('title', '').lower()

    # Normalize key: replace hyphens with underscores for category matching
    normalized_key = key.lower().replace('-', '_')

    # Try to find matching category research
    for category_key, research in CATEGORY_RESEARCH.items():
        if category_key in normalized_key or category_key in title.replace(' ', '_'):
            return {
                'key': key,
                'category': category_key,
                'research': research,
                'source': 'CATEGORY_RESEARCH'
            }

    # Fallback: generic event planner
    return {
        'key': key,
        'category': 'generic_event',
        'research': {
            'description': 'Event Planning',
            'audience': 'Event planners, hosts',
            'timeline_months': 3,
            'typical_attendees': '20-200',
            'key_sections': ['Guest List', 'Budget', 'Timeline', 'Vendor Coordination'],
            'budget_categories': ['Venue', 'Catering', 'Decorations', 'Entertainment', 'Supplies'],
            'unique_tabs': ['Guest List', 'Budget Tracker', 'Vendor Directory'],
            'complexity': 'medium',
        },
        'source': 'FALLBACK'
    }

def create_design_research(batch_num: int = None, specific_keys: List[str] = None) -> Dict:
    """Create research data for sheet design."""
    listings = load_listings()

    # Filter by batch if provided
    if batch_num:
        if batch_num == 1:
            start_key, end_key = 'wedding', 'debut_tl'
        elif batch_num == 3:
            start_key, end_key = 'destwedding', 'multicurrency'
        elif batch_num == 4:
            start_key, end_key = 'baptism', 'finados_pt'
        elif batch_num == 5:
            start_key, end_key = 'road-trip', 'first-time-rv'
        else:
            return {}

        start_idx = next((i for i, l in enumerate(list(listings.values())) if l.get('key') == start_key), None)
        end_idx = next((i for i, l in enumerate(list(listings.values())) if l.get('key') == end_key), None)

        if start_idx is not None and end_idx is not None:
            listings = {k: v for k, v in list(listings.items())[start_idx:end_idx+1]}

    # Filter by specific keys if provided
    if specific_keys:
        listings = {k: v for k, v in listings.items() if k in specific_keys}

    # Build research data
    research_data = {
        'metadata': {
            'generated': __import__('datetime').datetime.now().isoformat(),
            'total_listings': len(listings),
            'batch': batch_num,
        },
        'listings': {}
    }

    for key, listing in listings.items():
        research = get_research_for_listing(key, listing)
        research_data['listings'][key] = research

    return research_data

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.isdigit():
            batch_num = int(arg)
            print(f"\nResearching Batch {batch_num}...")
            research = create_design_research(batch_num=batch_num)
        else:
            # Specific listing keys
            keys = sys.argv[1:]
            print(f"\nResearching {len(keys)} listings: {', '.join(keys)}")
            research = create_design_research(specific_keys=keys)
    else:
        print("\nResearching all listings...")
        research = create_design_research()

    # Save research
    RESEARCH_FILE.write_text(json.dumps(research, indent=2))

    print(f"[OK] Research saved: {RESEARCH_FILE}")
    print(f"     Total listings: {research['metadata']['total_listings']}")

    # Show sample
    if research['listings']:
        first_key = list(research['listings'].keys())[0]
        first = research['listings'][first_key]
        print(f"\n     Example - {first_key}:")
        print(f"       Category: {first['category']}")
        print(f"       Description: {first['research'].get('description')}")
        print(f"       Complexity: {first['research'].get('complexity')}")
        print(f"       Unique tabs: {', '.join(first['research'].get('unique_tabs', []))}")

if __name__ == '__main__':
    main()
