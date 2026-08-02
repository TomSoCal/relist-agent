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
    add_expense_legacy,
    get_expenses_by_date_range_legacy,
    delete_expense_legacy,
    get_total_expenses_by_category_legacy,
    add_mileage_trip,
    get_mileage_by_date_range,
    delete_mileage_trip,
    get_total_mileage_for_period,
    add_brand,
    get_all_brands,
    delete_brand,
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


class TestExpenses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_expenses.db')

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
        time.sleep(0.5)
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        """Clear expenses table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM expenses')
        conn.commit()
        conn.close()

    def test_add_expense(self):
        """Test adding a new expense."""
        # Add an expense
        expense_id = add_expense_legacy('2026-07-30', 1, 50.00, 'Office supplies', '')
        self.assertIsNotNone(expense_id)
        self.assertIsInstance(expense_id, int)

    def test_add_expense_year_auto_populated(self):
        """Test that year is auto-populated when adding expense."""
        expense_id = add_expense_legacy('2026-07-30', 1, 50.00, 'Test expense', '')

        # Retrieve the expense
        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses), 1)

        expense = expenses[0]
        # Year should be current system year
        expected_year = datetime.now().year
        self.assertEqual(expense['year'], expected_year)

    def test_add_expense_with_default_fields(self):
        """Test adding expense with default values for optional fields."""
        expense_id = add_expense_legacy('2026-07-30', 1, 75.00)

        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses), 1)

        expense = expenses[0]
        self.assertEqual(expense['amount'], 75.00)
        self.assertEqual(expense['description'], '')
        self.assertEqual(expense['receipt_path'], '')

    def test_get_expenses_by_date_range(self):
        """Test retrieving expenses within a date range."""
        # Add multiple expenses
        add_expense_legacy('2026-07-15', 1, 50.00)
        add_expense_legacy('2026-07-20', 2, 100.00)
        add_expense_legacy('2026-07-25', 1, 75.00)

        # Get expenses in range
        expenses = get_expenses_by_date_range_legacy('2026-07-10', '2026-07-31')
        self.assertEqual(len(expenses), 3)

        # Verify order is DESC
        self.assertEqual(expenses[0]['expense_date'], '2026-07-25')
        self.assertEqual(expenses[1]['expense_date'], '2026-07-20')
        self.assertEqual(expenses[2]['expense_date'], '2026-07-15')


    def test_delete_expense(self):
        """Test deleting an expense."""
        expense_id = add_expense_legacy('2026-07-30', 1, 50.00)

        # Verify it exists
        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses), 1)

        # Delete it
        delete_expense_legacy(expense_id)

        # Verify it's deleted
        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses), 0)

    def test_expense_has_required_fields(self):
        """Test that expense has all required fields."""
        add_expense_legacy('2026-07-30', 1, 50.00, 'Test expense', '/path/to/receipt.pdf')

        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        expense = expenses[0]

        self.assertIn('id', expense)
        self.assertIn('year', expense)
        self.assertIn('expense_date', expense)
        self.assertIn('category_id', expense)
        self.assertIn('amount', expense)
        self.assertIn('description', expense)
        self.assertIn('receipt_path', expense)
        self.assertIn('created_at', expense)
        self.assertIn('updated_at', expense)

    def test_get_total_expenses_by_category(self):
        """Test getting total expenses grouped by category."""
        # Add expenses from multiple categories
        add_expense_legacy('2026-07-15', 1, 50.00)  # Category 1
        add_expense_legacy('2026-07-20', 1, 75.00)  # Category 1
        add_expense_legacy('2026-07-25', 2, 100.00)  # Category 2

        # Get totals by category
        totals = get_total_expenses_by_category_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(totals), 2)

        # Verify totals are calculated correctly
        # Should be ordered by total_amount DESC
        self.assertEqual(totals[0]['total_amount'], 125.00)
        self.assertEqual(totals[0]['count'], 2)
        self.assertEqual(totals[1]['total_amount'], 100.00)
        self.assertEqual(totals[1]['count'], 1)

    def test_add_expense_with_past_year_rejected(self):
        """Test that adding expense with past year is rejected (write protection)."""
        past_year = datetime.now().year - 1

        # Attempting to add expense with past year should raise ValueError
        with self.assertRaises(ValueError) as context:
            add_expense_legacy('2025-07-30', 1, 50.00, year=past_year)

        # Verify error message mentions current year
        self.assertIn(str(datetime.now().year), str(context.exception))

    def test_delete_expense_from_past_year_fails(self):
        """Test that deleting expense from past year fails (no rows match)."""
        # First, add an expense to current year
        expense_id = add_expense_legacy('2026-07-30', 1, 50.00)

        # Manually update the expense to have a past year
        conn = get_connection()
        c = conn.cursor()
        past_year = datetime.now().year - 1
        c.execute('UPDATE expenses SET year = ? WHERE id = ?', (past_year, expense_id))
        conn.commit()
        conn.close()

        # Now try to delete it - should fail (no rows match because WHERE includes year check)
        rows_deleted = delete_expense_legacy(expense_id)
        self.assertEqual(rows_deleted, 0)

    def test_get_expenses_by_date_range_with_explicit_year(self):
        """Test that querying with explicit year parameter works for read-only access."""
        # Add an expense to current year
        current_year = datetime.now().year
        add_expense_legacy('2026-07-30', 1, 50.00, year=current_year)

        # Add an expense to past year directly (simulating historical data)
        conn = get_connection()
        c = conn.cursor()
        past_year = current_year - 1
        c.execute('''
            INSERT INTO expenses (year, expense_date, category_id, amount, description, receipt_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (past_year, '2025-07-30', 1, 75.00, 'Past year expense', ''))
        conn.commit()
        conn.close()

        # Query current year (default)
        expenses_current = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses_current), 1)
        self.assertEqual(expenses_current[0]['amount'], 50.00)

        # Query past year explicitly
        expenses_past = get_expenses_by_date_range_legacy('2025-07-01', '2025-07-31', year=past_year)
        self.assertEqual(len(expenses_past), 1)
        self.assertEqual(expenses_past[0]['amount'], 75.00)

    def test_get_total_expenses_by_category_with_explicit_year(self):
        """Test that get_total_expenses_by_category_legacy works with explicit year for read-only access."""
        current_year = datetime.now().year

        # Add an expense to current year
        add_expense_legacy('2026-07-30', 1, 50.00, year=current_year)

        # Add an expense to past year directly
        conn = get_connection()
        c = conn.cursor()
        past_year = current_year - 1
        c.execute('''
            INSERT INTO expenses (year, expense_date, category_id, amount, description, receipt_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (past_year, '2025-07-30', 1, 100.00, 'Past year expense', ''))
        conn.commit()
        conn.close()

        # Query current year (default)
        totals_current = get_total_expenses_by_category_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(totals_current), 1)
        self.assertEqual(totals_current[0]['total_amount'], 50.00)

        # Query past year explicitly
        totals_past = get_total_expenses_by_category_legacy('2025-07-01', '2025-07-31', year=past_year)
        self.assertEqual(len(totals_past), 1)
        self.assertEqual(totals_past[0]['total_amount'], 100.00)

    def test_expense_foreign_key_reference(self):
        """Test that expense category_id references expense_categories."""
        # Add an expense with a valid category_id
        add_expense_legacy('2026-07-30', 1, 50.00)

        expenses = get_expenses_by_date_range_legacy('2026-07-01', '2026-07-31')
        self.assertEqual(len(expenses), 1)

        expense = expenses[0]
        # category_id should reference a valid category
        self.assertIsNotNone(expense['category_id'])


class TestMileage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_mileage.db')

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
        time.sleep(0.5)
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        """Clear mileage table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM mileage')
        conn.commit()
        conn.close()

    def test_add_mileage_trip(self):
        """Test adding a new mileage trip."""
        trip_id = add_mileage_trip('2026-07-30', 45.5, 'sourcing', 'Goodwill, Salvation Army', 'Found great deals')
        self.assertIsNotNone(trip_id)
        self.assertIsInstance(trip_id, int)

    def test_add_mileage_trip_year_auto_populated(self):
        """Test that year is auto-populated when adding mileage trip."""
        trip_id = add_mileage_trip('2026-07-30', 25.3)

        # Retrieve the trip
        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips), 1)

        trip = trips[0]
        # Year should be current system year
        expected_year = datetime.now().year
        self.assertEqual(trip['year'], expected_year)

    def test_add_mileage_trip_with_default_fields(self):
        """Test adding mileage trip with default values for optional fields."""
        trip_id = add_mileage_trip('2026-07-30', 30.0)

        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips), 1)

        trip = trips[0]
        self.assertEqual(trip['miles'], 30.0)
        self.assertEqual(trip['purpose'], 'sourcing')
        self.assertEqual(trip['stores_visited'], '')
        self.assertEqual(trip['notes'], '')
        self.assertEqual(trip['odometer_start'], 0)
        self.assertEqual(trip['odometer_end'], 0)

    def test_get_mileage_by_date_range(self):
        """Test retrieving mileage trips within a date range."""
        # Add multiple trips
        add_mileage_trip('2026-07-15', 25.0)
        add_mileage_trip('2026-07-20', 35.5)
        add_mileage_trip('2026-07-25', 40.0)

        # Get trips in range
        trips = get_mileage_by_date_range('2026-07-10', '2026-07-31')
        self.assertEqual(len(trips), 3)

        # Verify order is DESC
        self.assertEqual(trips[0]['trip_date'], '2026-07-25')
        self.assertEqual(trips[1]['trip_date'], '2026-07-20')
        self.assertEqual(trips[2]['trip_date'], '2026-07-15')


    def test_delete_mileage_trip(self):
        """Test deleting a mileage trip."""
        trip_id = add_mileage_trip('2026-07-30', 25.0)

        # Verify it exists
        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips), 1)

        # Delete it
        delete_mileage_trip(trip_id)

        # Verify it's deleted
        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips), 0)

    def test_mileage_trip_has_required_fields(self):
        """Test that mileage trip has all required fields."""
        add_mileage_trip('2026-07-30', 35.5, 'sourcing', 'Goodwill', 'Productive trip', 15000, 15035)

        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        trip = trips[0]

        self.assertIn('id', trip)
        self.assertIn('year', trip)
        self.assertIn('trip_date', trip)
        self.assertIn('odometer_start', trip)
        self.assertIn('odometer_end', trip)
        self.assertIn('miles', trip)
        self.assertIn('purpose', trip)
        self.assertIn('stores_visited', trip)
        self.assertIn('notes', trip)
        self.assertIn('created_at', trip)
        self.assertIn('updated_at', trip)

    def test_get_total_mileage_for_period(self):
        """Test getting total mileage and trip count for a period."""
        # Add multiple trips
        add_mileage_trip('2026-07-15', 25.0)
        add_mileage_trip('2026-07-20', 35.5)
        add_mileage_trip('2026-07-25', 40.0)

        # Get totals
        totals = get_total_mileage_for_period('2026-07-01', '2026-07-31')
        self.assertEqual(totals['total_miles'], 100.5)
        self.assertEqual(totals['trip_count'], 3)


    def test_get_total_mileage_empty_range(self):
        """Test getting total mileage for empty range returns zeros."""
        # Get totals for a range with no trips
        totals = get_total_mileage_for_period('2026-06-01', '2026-06-30')
        self.assertEqual(totals['total_miles'], 0)
        self.assertEqual(totals['trip_count'], 0)

    def test_mileage_trip_with_odometer_readings(self):
        """Test adding and retrieving trip with odometer start and end readings."""
        trip_id = add_mileage_trip('2026-07-30', 35.5, 'sourcing', 'Goodwill, Salvation Army', 'Found deals', 15000, 15035)

        trips = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips), 1)

        trip = trips[0]
        self.assertEqual(trip['odometer_start'], 15000)
        self.assertEqual(trip['odometer_end'], 15035)
        self.assertEqual(trip['miles'], 35.5)

    def test_add_mileage_trip_with_past_year_rejected(self):
        """Test that adding mileage trip with past year is rejected (write protection)."""
        past_year = datetime.now().year - 1

        # Attempting to add trip with past year should raise ValueError
        with self.assertRaises(ValueError) as context:
            add_mileage_trip('2025-07-30', 25.0, year=past_year)

        # Verify error message mentions current year
        self.assertIn(str(datetime.now().year), str(context.exception))

    def test_delete_mileage_trip_from_past_year_fails(self):
        """Test that deleting mileage trip from past year fails (no rows match)."""
        # First, add a trip to current year
        trip_id = add_mileage_trip('2026-07-30', 25.0)

        # Manually update the trip to have a past year
        conn = get_connection()
        c = conn.cursor()
        past_year = datetime.now().year - 1
        c.execute('UPDATE mileage SET year = ? WHERE id = ?', (past_year, trip_id))
        conn.commit()
        conn.close()

        # Now try to delete it - should fail (no rows match because WHERE includes year check)
        rows_deleted = delete_mileage_trip(trip_id)
        self.assertEqual(rows_deleted, 0)

    def test_get_mileage_by_date_range_with_explicit_year(self):
        """Test that querying with explicit year parameter works for read-only access."""
        # Add a trip to current year
        current_year = datetime.now().year
        add_mileage_trip('2026-07-30', 25.0, year=current_year)

        # Add a trip to past year directly (simulating historical data)
        conn = get_connection()
        c = conn.cursor()
        past_year = current_year - 1
        c.execute('''
            INSERT INTO mileage (year, trip_date, odometer_start, odometer_end, miles, purpose, stores_visited, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, '2025-07-30', 0, 0, 30.0, 'sourcing', '', ''))
        conn.commit()
        conn.close()

        # Query current year (default)
        trips_current = get_mileage_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(trips_current), 1)
        self.assertEqual(trips_current[0]['miles'], 25.0)

        # Query past year explicitly
        trips_past = get_mileage_by_date_range('2025-07-01', '2025-07-31', year=past_year)
        self.assertEqual(len(trips_past), 1)
        self.assertEqual(trips_past[0]['miles'], 30.0)

    def test_get_total_mileage_for_period_with_explicit_year(self):
        """Test that get_total_mileage_for_period works with explicit year for read-only access."""
        current_year = datetime.now().year

        # Add a trip to current year
        add_mileage_trip('2026-07-30', 25.0, year=current_year)

        # Add a trip to past year directly
        conn = get_connection()
        c = conn.cursor()
        past_year = current_year - 1
        c.execute('''
            INSERT INTO mileage (year, trip_date, odometer_start, odometer_end, miles, purpose, stores_visited, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, '2025-07-30', 0, 0, 40.0, 'sourcing', '', ''))
        conn.commit()
        conn.close()

        # Query current year (default)
        totals_current = get_total_mileage_for_period('2026-07-01', '2026-07-31')
        self.assertEqual(totals_current['total_miles'], 25.0)
        self.assertEqual(totals_current['trip_count'], 1)

        # Query past year explicitly
        totals_past = get_total_mileage_for_period('2025-07-01', '2025-07-31', year=past_year)
        self.assertEqual(totals_past['total_miles'], 40.0)
        self.assertEqual(totals_past['trip_count'], 1)


class TestBrands(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_brands.db')

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
        time.sleep(0.5)
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        """Clear brands table before each test."""
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
                    c.execute('DELETE FROM brands')
                    conn.commit()
                finally:
                    conn.close()
                break
            except sqlite3.OperationalError as e:
                if attempt < max_retries - 1:
                    time.sleep(1.0)
                else:
                    raise

    def test_add_brand(self):
        """Test adding a new brand."""
        brand_id = add_brand('Nike')
        self.assertIsNotNone(brand_id)
        self.assertIsInstance(brand_id, int)

    def test_get_all_brands(self):
        """Test retrieving all brands."""
        add_brand('Nike')
        add_brand('Adidas')
        add_brand('Puma')

        brands = get_all_brands()
        self.assertEqual(len(brands), 3)
        # Brands should be sorted by name (case-insensitive)
        brand_names = [b['name'] for b in brands]
        self.assertIn('Nike', brand_names)
        self.assertIn('Adidas', brand_names)
        self.assertIn('Puma', brand_names)

    def test_delete_brand(self):
        """Test deleting a brand."""
        brand_id = add_brand('Nike')
        delete_brand(brand_id)

        brands = get_all_brands()
        self.assertEqual(len(brands), 0)

    def test_brand_has_required_fields(self):
        """Test that brand has all required fields."""
        add_brand('Nike')

        brands = get_all_brands()
        brand = brands[0]

        self.assertIn('id', brand)
        self.assertIn('name', brand)
        self.assertIn('created_at', brand)

    def test_brand_unique_constraint(self):
        """Test that brand name is unique."""
        add_brand('Nike')

        # Attempting to add duplicate should raise an exception
        with self.assertRaises(sqlite3.IntegrityError):
            add_brand('Nike')

    def test_brand_names_case_insensitive_sort(self):
        """Test that brands are sorted case-insensitively."""
        add_brand('zebra')
        add_brand('Apple')
        add_brand('BANANA')

        brands = get_all_brands()
        brand_names = [b['name'] for b in brands]
        # Should be sorted: Apple, BANANA, zebra
        self.assertEqual(brand_names[0], 'Apple')
        self.assertEqual(brand_names[1], 'BANANA')
        self.assertEqual(brand_names[2], 'zebra')


if __name__ == '__main__':
    unittest.main()
