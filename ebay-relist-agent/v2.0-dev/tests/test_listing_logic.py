import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

ITEMS = [
    {"item_id": "1", "title": "Old Fixed",  "listing_type": "FixedPriceItem", "quantity": 2, "start_time": "2026-01-01T00:00:00.000Z"},
    {"item_id": "2", "title": "Auction",    "listing_type": "Chinese",        "quantity": 1, "start_time": "2026-01-02T00:00:00.000Z"},
    {"item_id": "3", "title": "Zero Qty",   "listing_type": "FixedPriceItem", "quantity": 0, "start_time": "2026-01-03T00:00:00.000Z"},
    {"item_id": "4", "title": "New Fixed",  "listing_type": "FixedPriceItem", "quantity": 5, "start_time": "2026-02-01T00:00:00.000Z"},
    {"item_id": "5", "title": "Mid Fixed",  "listing_type": "FixedPriceItem", "quantity": 1, "start_time": "2026-01-15T00:00:00.000Z"},
]


def test_partition_zero_qty_items():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    assert [i["item_id"] for i in zero_qty] == ["3"]


def test_partition_excludes_auctions_from_both_lists():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    all_ids = [i["item_id"] for i in zero_qty + eligible]
    assert "2" not in all_ids


def test_partition_eligible_contains_fixed_price_with_qty():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    ids = [i["item_id"] for i in eligible]
    assert "1" in ids and "4" in ids and "5" in ids


def test_select_oldest_returns_n_oldest_by_start_time():
    from listing_logic import select_oldest
    items = [
        {"item_id": "A", "start_time": "2026-01-03T00:00:00.000Z"},
        {"item_id": "B", "start_time": "2026-01-01T00:00:00.000Z"},
        {"item_id": "C", "start_time": "2026-01-02T00:00:00.000Z"},
    ]
    result = select_oldest(items, n=2)
    assert [i["item_id"] for i in result] == ["B", "C"]


def test_select_oldest_returns_all_if_fewer_than_n():
    from listing_logic import select_oldest
    items = [{"item_id": "X", "start_time": "2026-01-01T00:00:00.000Z"}]
    assert len(select_oldest(items, n=10)) == 1
