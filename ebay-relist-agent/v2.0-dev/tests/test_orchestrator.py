import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

CFG = {"app_id": "a", "cert_id": "c", "dev_id": "d", "ru_name": "r", "gmail_app_password": "pw"}

MOCK_FIELDS = {
    "title": "Normal", "description": "", "primary_category_id": "1",
    "secondary_category_id": "", "store_category_id": "", "store_category2_id": "",
    "start_price": "9.99", "quantity": "2", "listing_duration": "GTC",
    "listing_type": "FixedPriceItem", "condition_id": "1000", "condition_description": "",
    "pictures": [], "item_specifics": [], "sku": "SKU1",
    "shipping_xml": "", "ship_to_locations": [], "return_policy_xml": "",
    "dispatch_time_max": "1",
}


def test_run_ends_zero_qty_and_relists_eligible():
    from ebay_relist_agent import run
    all_items = [
        {"item_id": "ZZ1", "title": "Zero", "listing_type": "FixedPriceItem", "quantity": 0, "start_time": "2026-01-01T00:00:00Z"},
        {"item_id": "A01", "title": "Normal", "listing_type": "FixedPriceItem", "quantity": 2, "start_time": "2026-01-02T00:00:00Z"},
    ]
    with patch("ebay_relist_agent.load_config", return_value=CFG), \
         patch("ebay_relist_agent.get_access_token", return_value="tok"), \
         patch("ebay_relist_agent.fetch_all_active_listings", return_value=all_items), \
         patch("ebay_relist_agent.get_item", return_value=MOCK_FIELDS), \
         patch("ebay_relist_agent.add_item", return_value="NEW01"), \
         patch("ebay_relist_agent.end_item") as mock_end, \
         patch("ebay_relist_agent.send_email"), \
         patch("ebay_relist_agent.notify_toast"), \
         patch("ebay_relist_agent.append_log"), \
         patch("ebay_relist_agent.kff_check", return_value={"status": "approve", "suggestion": ""}):
        run()
    ended_ids = [c.args[2] for c in mock_end.call_args_list]
    assert "ZZ1" in ended_ids
    assert "A01" in ended_ids


def test_run_does_not_end_item_when_add_item_fails():
    from ebay_relist_agent import run
    all_items = [
        {"item_id": "F01", "title": "Fail", "listing_type": "FixedPriceItem", "quantity": 1, "start_time": "2026-01-01T00:00:00Z"},
    ]
    with patch("ebay_relist_agent.load_config", return_value=CFG), \
         patch("ebay_relist_agent.get_access_token", return_value="tok"), \
         patch("ebay_relist_agent.fetch_all_active_listings", return_value=all_items), \
         patch("ebay_relist_agent.get_item", return_value=MOCK_FIELDS), \
         patch("ebay_relist_agent.add_item", side_effect=RuntimeError("API error")), \
         patch("ebay_relist_agent.end_item") as mock_end, \
         patch("ebay_relist_agent.send_email"), \
         patch("ebay_relist_agent.notify_toast"), \
         patch("ebay_relist_agent.append_log"), \
         patch("ebay_relist_agent.kff_check", return_value={"status": "approve", "suggestion": ""}):
        run()
    ended_ids = [c.args[2] for c in mock_end.call_args_list]
    assert "F01" not in ended_ids
