import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db, add_inventory, add_sale, archive_sold_inventory_for_year,
    get_archived_inventory, copy_archived_to_active, get_inventory_by_id,
    get_all_inventory, delete_inventory, DB_PATH, check_and_archive_year_transition,
    get_setting, set_setting
)


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Create a test database for each test"""
    import database
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_archive.db')

    # Remove existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Patch DB_PATH
    monkeypatch.setattr(database, 'DB_PATH', test_db_path)
    monkeypatch.setattr('database.DB_PATH', test_db_path)

    init_db()

    yield test_db_path

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


class TestArchiveFunctions:

    def test_archive_sold_inventory_marks_units_zero_as_archived(self, test_db):
        """Inventory with units=0 should be marked archived=1"""
        # Add inventory with units=1, then sell it (units becomes 0)
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Test Item',
            units=1,
            sku='TEST-01',
            category='Test',
            cost=10.0
        )

        # Simulate sale by manually updating units to 0 (normally done via UI)
        from database import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE inventory SET units = 0 WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        conn.close()

        # Archive year 2026
        archive_sold_inventory_for_year(2026)

        # Verify archived=1
        item = get_inventory_by_id(item_id)
        assert item['archived'] == 1

    def test_archive_does_not_mark_unsold_inventory_archived(self, test_db):
        """Inventory with units > 0 should remain archived=0"""
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Unsold Item',
            units=5,
            sku='UNSOLD-01',
            category='Test',
            cost=10.0
        )

        # Archive year 2026
        archive_sold_inventory_for_year(2026)

        # Verify archived=0
        item = get_inventory_by_id(item_id)
        assert item['archived'] == 0

    def test_get_archived_inventory_returns_only_archived_items(self, test_db):
        """get_archived_inventory should return only archived=1 items"""
        # Add and archive one item
        item1_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Archived Item',
            units=0,
            sku='ARCH-01',
            category='Test',
            cost=10.0
        )

        # Add unsold item (never archived)
        item2_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Active Item',
            units=3,
            sku='ACTIVE-01',
            category='Test',
            cost=10.0
        )

        # Mark first item archived
        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1, units = 0 WHERE id = ?", (item1_id,))
        conn.commit()
        conn.close()

        # Query archived
        archived = get_archived_inventory(year=2026)
        archived_skus = [a['sku'] for a in archived]

        assert 'ARCH-01' in archived_skus
        assert 'ACTIVE-01' not in archived_skus

    def test_get_archived_inventory_search_by_sku(self, test_db):
        """Search should filter by SKU"""
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Searchable Item',
            units=0,
            sku='SEARCH-123',
            category='Test',
            cost=10.0
        )

        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        # Search for SKU
        results = get_archived_inventory(search_query='SEARCH')

        assert len(results) > 0
        assert any(r['sku'] == 'SEARCH-123' for r in results)

    def test_copy_archived_to_active_creates_new_inventory(self, test_db):
        """copy_archived_to_active should create new row with new SKU"""
        # Create and archive original item
        orig_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Original Item',
            units=0,
            sku='ORIG-01',
            category='Electronics',
            brand='TestBrand',
            cost=25.0
        )

        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (orig_id,))
        conn.commit()
        conn.close()

        # Copy to active with new SKU
        new_id = copy_archived_to_active(orig_id, new_sku='RESTOCK-01', copy_details=True)

        # Verify new item exists with new SKU
        new_item = get_inventory_by_id(new_id)
        assert new_item['sku'] == 'RESTOCK-01'
        assert new_item['item_title'] == 'Original Item'
        assert new_item['category'] == 'Electronics'
        assert new_item['brand'] == 'TestBrand'
        assert new_item['cost'] == 25.0
        assert new_item['archived'] == 0  # Active
        assert new_item['units'] == 1  # Default

    def test_copy_archived_without_copy_details_creates_minimal_item(self, test_db):
        """With copy_details=False, should create item with only SKU and units"""
        orig_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Original Item',
            units=0,
            sku='ORIG-02',
            category='Test',
            cost=10.0
        )

        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (orig_id,))
        conn.commit()
        conn.close()

        new_id = copy_archived_to_active(orig_id, new_sku='RESTOCK-02', copy_details=False)

        new_item = get_inventory_by_id(new_id)
        assert new_item['sku'] == 'RESTOCK-02'
        assert new_item['units'] == 1
        assert new_item['archived'] == 0
        # Other fields may be empty/defaults

    def test_check_and_archive_year_transition_archives_on_year_change(self, test_db, monkeypatch):
        """Year transition should trigger archival and update last_app_year setting"""
        # Mock datetime to simulate new year
        class MockDatetime:
            @staticmethod
            def now():
                class Now:
                    year = 2027
                return Now()

        monkeypatch.setattr('database.datetime', MockDatetime)

        # Set last year to 2026
        set_setting('last_app_year', '2026')

        # Create sold item from 2026
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='2026 Item',
            units=0,
            sku='YEAR-26',
            category='Test',
            cost=10.0,
            created_at='2026-01-01'
        )

        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET created_at = '2026-01-01T00:00:00' WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        # Run year check
        result = check_and_archive_year_transition()

        # Verify archival happened
        assert result == True
        assert get_setting('last_app_year') == '2027'

        item = get_inventory_by_id(item_id)
        assert item['archived'] == 1

    def test_complete_workflow_sell_archive_restock(self, test_db):
        """Full workflow: create → sell → archive → search → restock"""
        # 1. Create inventory item
        item_id = add_inventory(
            listed_date='2026-01-15',
            item_title='Premium Widget',
            units=1,
            sku='WIDGET-001',
            category='Electronics',
            brand='WidgetCorp',
            cost=50.0
        )

        # Verify active
        item = get_inventory_by_id(item_id)
        assert item['archived'] == 0
        assert item['units'] == 1

        # 2. Sell the item (simulate sale)
        sale_id = add_sale(
            sold_date='2026-02-01',
            listed_date='2026-01-15',
            item_title='Premium Widget',
            platform='eBay',
            units=1,
            sku='WIDGET-001',
            category='Electronics',
            sale_price=100.0,
            shipping_collected=0.0,
            cost_of_goods=50.0,
            shipping_cost=5.0,
            platform_fee=12.00,
            transaction_fee=2.90,
            promoted_fee=0.0
        )

        # Mark inventory as sold
        from database import get_connection
        conn = get_connection()
        conn.execute("UPDATE inventory SET units = 0 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        # 3. Archive at year boundary
        archive_sold_inventory_for_year(2026)

        # Verify archived
        item = get_inventory_by_id(item_id)
        assert item['archived'] == 1

        # 4. Search archived inventory
        archived = get_archived_inventory(year=2026, search_query='WIDGET')
        assert len(archived) > 0
        found_item = [a for a in archived if a['sku'] == 'WIDGET-001'][0]
        assert found_item['item_title'] == 'Premium Widget'
        assert found_item['units_sold_total'] == 1

        # 5. Restock with new SKU
        new_item_id = copy_archived_to_active(
            item_id,
            new_sku='WIDGET-002',
            copy_details=True
        )

        # Verify new item is active with copied details
        new_item = get_inventory_by_id(new_item_id)
        assert new_item['sku'] == 'WIDGET-002'
        assert new_item['item_title'] == 'Premium Widget'
        assert new_item['category'] == 'Electronics'
        assert new_item['brand'] == 'WidgetCorp'
        assert new_item['cost'] == 50.0
        assert new_item['archived'] == 0
        assert new_item['units'] == 1
