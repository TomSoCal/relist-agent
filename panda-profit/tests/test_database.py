import unittest
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    get_connection,
    add_expense_category,
    get_all_expense_categories,
    delete_expense_category,
    add_platform_fee,
    get_platform_fee,
    get_all_platform_fees,
    update_platform_fee,
    DB_PATH
)


class TestExpenseCategories(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        # Use a test database
        global DB_PATH
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit.db')

        # Patch the DB_PATH in the database module
        import database
        database.DB_PATH = cls.test_db_path
        global DB_PATH
        DB_PATH = cls.test_db_path

        init_db()

    @classmethod
    def tearDownClass(cls):
        """Remove test database after all tests."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        """Clear expense_categories table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM expense_categories')
        conn.commit()
        conn.close()

    def test_add_expense_category(self):
        """Test adding a new expense category."""
        category_id = add_expense_category('Packaging', 'supplies')
        self.assertIsNotNone(category_id)
        self.assertIsInstance(category_id, int)

    def test_get_all_expense_categories(self):
        """Test retrieving all expense categories."""
        add_expense_category('Packaging', 'supplies')
        add_expense_category('Shipping', 'shipping')

        categories = get_all_expense_categories()
        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0]['name'], 'Packaging')
        self.assertEqual(categories[1]['name'], 'Shipping')

    def test_delete_expense_category(self):
        """Test deleting an expense category."""
        category_id = add_expense_category('Packaging', 'supplies')
        delete_expense_category(category_id)

        categories = get_all_expense_categories()
        self.assertEqual(len(categories), 0)

    def test_category_has_required_fields(self):
        """Test that category has all required fields."""
        add_expense_category('Packaging', 'supplies')

        categories = get_all_expense_categories()
        category = categories[0]

        self.assertIn('id', category)
        self.assertIn('name', category)
        self.assertIn('category_type', category)
        self.assertIn('created_at', category)
        self.assertIn('updated_at', category)

    def test_default_categories_created(self):
        """Test that default categories are created during init."""
        # Reinitialize to populate defaults
        init_db()

        categories = get_all_expense_categories()
        # Should have at least some default categories
        self.assertGreater(len(categories), 0)


class TestPlatformFees(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_fees.db')

        # Remove old test database if it exists
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        # Patch the DB_PATH in the database module
        import database
        database.DB_PATH = cls.test_db_path
        global DB_PATH
        DB_PATH = cls.test_db_path

        init_db()

    @classmethod
    def tearDownClass(cls):
        """Remove test database after all tests."""
        import time
        # Give connections time to close
        time.sleep(0.5)
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        """Clear test-added platform_fees before each test (preserve defaults)."""
        import time
        import gc

        # Force garbage collection to close any lingering connections
        gc.collect()
        time.sleep(0.2)

        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = get_connection()
                try:
                    c = conn.cursor()
                    # Only delete non-default platforms added by tests
                    test_platforms = [
                        'TestPlatform',
                        'AmazonTest',
                        'ShopifyTest',
                        'EtsyTest',
                        'AlibabaTest'
                    ]
                    placeholders = ','.join(['?' for _ in test_platforms])
                    c.execute(f'DELETE FROM platform_fees WHERE platform IN ({placeholders})', test_platforms)
                    conn.commit()
                finally:
                    conn.close()
                break
            except sqlite3.OperationalError as e:
                if attempt < max_retries - 1:
                    time.sleep(1.0)
                else:
                    raise

    def test_add_platform_fee(self):
        """Test adding a new platform fee."""
        fee_id = add_platform_fee('AmazonTest', 0.50, 15.0, 5.0, 2.5, 'Test notes')
        self.assertIsNotNone(fee_id)
        self.assertIsInstance(fee_id, int)

    def test_get_platform_fee_by_name(self):
        """Test retrieving a platform fee by platform name."""
        # Test with existing default platform
        fee = get_platform_fee('eBay')
        self.assertIsNotNone(fee)
        self.assertEqual(fee['platform'], 'eBay')
        self.assertEqual(fee['listing_fee'], 0.30)
        self.assertEqual(fee['transaction_fee_pct'], 12.9)
        self.assertEqual(fee['payment_fee_pct'], 2.2)

    def test_get_all_platform_fees(self):
        """Test retrieving all platform fees."""
        fees = get_all_platform_fees()
        # Should have at least the 5 default platforms
        self.assertGreaterEqual(len(fees), 5)
        # Check that expected platforms exist
        platform_names = [f['platform'] for f in fees]
        self.assertIn('eBay', platform_names)
        self.assertIn('Poshmark', platform_names)
        self.assertIn('Mercari', platform_names)

    def test_update_platform_fee(self):
        """Test updating a platform fee."""
        # Create a test platform to update
        add_platform_fee('ShopifyTest', 0.30, 12.9, 0, 2.2, 'Test')

        # Update it
        update_platform_fee('ShopifyTest', listing_fee=0.35, transaction_fee_pct=13.5)

        fee = get_platform_fee('ShopifyTest')
        self.assertEqual(fee['listing_fee'], 0.35)
        self.assertEqual(fee['transaction_fee_pct'], 13.5)

    def test_platform_fee_has_required_fields(self):
        """Test that platform fee has all required fields."""
        add_platform_fee('EtsyTest', 0.30, 12.9, 0, 2.2, None)

        fee = get_platform_fee('EtsyTest')
        self.assertIn('id', fee)
        self.assertIn('platform', fee)
        self.assertIn('listing_fee', fee)
        self.assertIn('transaction_fee_pct', fee)
        self.assertIn('shipping_fee_pct', fee)
        self.assertIn('payment_fee_pct', fee)
        self.assertIn('notes', fee)
        self.assertIn('created_at', fee)
        self.assertIn('updated_at', fee)

    def test_default_platforms_created(self):
        """Test that default platforms are created during init."""
        # The defaults were already created in setUpClass via init_db()
        # Just query to verify they exist
        fees = get_all_platform_fees()
        # Should have 5 default platforms
        self.assertEqual(len(fees), 5)

        # Check that expected platforms exist
        platform_names = [fee['platform'] for fee in fees]
        self.assertIn('eBay', platform_names)
        self.assertIn('Poshmark', platform_names)
        self.assertIn('Facebook Marketplace', platform_names)
        self.assertIn('Mercari', platform_names)
        self.assertIn('Whatnot', platform_names)

    def test_platform_unique_constraint(self):
        """Test that platform name is unique."""
        add_platform_fee('AlibabaTest', 0.30, 12.9, 0, 2.2, None)

        # Attempting to add duplicate should raise an exception
        with self.assertRaises(sqlite3.IntegrityError):
            add_platform_fee('AlibabaTest', 0.35, 13.5, 0, 2.5, None)


if __name__ == '__main__':
    unittest.main()
