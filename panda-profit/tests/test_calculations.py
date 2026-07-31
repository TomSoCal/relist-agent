"""Tests for analytics calculations module."""

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
    add_sale,
    DB_PATH,
)
from analytics.calculations import (
    calculate_profit,
    calculate_roi_by_category,
    calculate_turnover_rate,
    calculate_platform_impact,
)


class TestCalculateProfit(unittest.TestCase):
    """Tests for calculate_profit function."""

    def test_calculate_profit_basic(self):
        """Test basic profit calculation."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': 10.00,
            'cost_of_goods': 30.00,
            'shipping_cost': 5.00,
            'platform_fee': 5.00,
            'transaction_fee': 3.00,
            'promoted_fee': 0.00,
        }
        profit = calculate_profit(sale)
        # (100 + 10) - (30 + 5 + 5 + 3 + 0) = 110 - 43 = 67
        self.assertAlmostEqual(profit, 67.00, places=2)

    def test_calculate_profit_with_loss(self):
        """Test profit calculation resulting in loss."""
        sale = {
            'sale_price': 50.00,
            'shipping_collected': 5.00,
            'cost_of_goods': 40.00,
            'shipping_cost': 10.00,
            'platform_fee': 5.00,
            'transaction_fee': 3.00,
            'promoted_fee': 2.00,
        }
        profit = calculate_profit(sale)
        # (50 + 5) - (40 + 10 + 5 + 3 + 2) = 55 - 60 = -5
        self.assertAlmostEqual(profit, -5.00, places=2)

    def test_calculate_profit_with_zero_fees(self):
        """Test profit calculation with no fees."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 30.00,
            'shipping_cost': 0.00,
            'platform_fee': 0.00,
            'transaction_fee': 0.00,
            'promoted_fee': 0.00,
        }
        profit = calculate_profit(sale)
        # 100 - 30 = 70
        self.assertAlmostEqual(profit, 70.00, places=2)

    def test_calculate_profit_with_none_values(self):
        """Test profit calculation handles None values gracefully."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': None,
            'cost_of_goods': 30.00,
            'shipping_cost': None,
            'platform_fee': 5.00,
            'transaction_fee': None,
            'promoted_fee': 0.00,
        }
        profit = calculate_profit(sale)
        # (100 + 0) - (30 + 0 + 5 + 0 + 0) = 100 - 35 = 65
        self.assertAlmostEqual(profit, 65.00, places=2)

    def test_calculate_profit_high_fees(self):
        """Test profit calculation with high fees."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': 10.00,
            'cost_of_goods': 20.00,
            'shipping_cost': 5.00,
            'platform_fee': 20.00,
            'transaction_fee': 5.00,
            'promoted_fee': 15.00,
        }
        profit = calculate_profit(sale)
        # (100 + 10) - (20 + 5 + 20 + 5 + 15) = 110 - 65 = 45
        self.assertAlmostEqual(profit, 45.00, places=2)


class TestROIByCategory(unittest.TestCase):
    """Tests for calculate_roi_by_category function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_roi.db')

        # Remove old test database if it exists
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        # Patch the DB_PATH in the database and calculations modules
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
        """Clear sales table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM sales')
        conn.commit()
        conn.close()

    def test_roi_by_category_single_category(self):
        """Test ROI calculation for single category."""
        current_year = datetime.now().year

        # Add a profitable sale
        add_sale(
            year=current_year,
            month=7,
            days_to_sell=5,
            platform='eBay',
            sold_date='2026-07-15',
            listed_date='2026-07-10',
            item_title='Test Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            shipping_collected=10.00,
            cost_of_goods=30.00,
            shipping_cost=5.00,
            platform_fee=5.00,
            transaction_fee=3.00,
        )

        results = calculate_roi_by_category('2026-07-01', '2026-07-31')

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['category'], 'Electronics')
        self.assertEqual(result['cost'], 30.00)
        # Profit = (100 + 10) - (30 + 5 + 5 + 3) = 67
        self.assertAlmostEqual(result['profit'], 67.00, places=2)
        # ROI = 67/30 * 100 = 223.33%
        self.assertAlmostEqual(result['roi_pct'], 223.33, places=1)

    def test_roi_by_category_multiple_categories(self):
        """Test ROI calculation with multiple categories."""
        current_year = datetime.now().year

        # Add sales for Category A
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Item A1',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            shipping_cost=5.00,
            platform_fee=5.00,
            transaction_fee=3.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-16',
            item_title='Item A2',
            units=1,
            category='Electronics',
            sale_price=50.00,
            cost_of_goods=20.00,
            shipping_cost=2.00,
            platform_fee=2.00,
            transaction_fee=1.50,
        )

        # Add sales for Category B
        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-20',
            item_title='Item B1',
            units=1,
            category='Clothing',
            sale_price=80.00,
            cost_of_goods=20.00,
            platform_fee=16.00,  # 20% commission on Poshmark
        )

        results = calculate_roi_by_category('2026-07-01', '2026-07-31')

        self.assertEqual(len(results), 2)

        # Verify categories are present
        categories = [r['category'] for r in results]
        self.assertIn('Electronics', categories)
        self.assertIn('Clothing', categories)

    def test_roi_by_category_zero_cost(self):
        """Test ROI calculation handles zero cost (ROI should be 0 or high value)."""
        current_year = datetime.now().year

        # Add a sale with zero cost
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Free Item',
            units=1,
            category='Giveaway',
            sale_price=50.00,
            cost_of_goods=0.00,  # No cost
            platform_fee=2.00,
        )

        results = calculate_roi_by_category('2026-07-01', '2026-07-31')

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['cost'], 0.00)
        # When cost is 0, ROI should be 0 per function specification
        self.assertEqual(result['roi_pct'], 0)

    def test_roi_by_category_sorted_by_roi(self):
        """Test that results are sorted by ROI descending."""
        current_year = datetime.now().year

        # High ROI sale
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='High ROI',
            units=1,
            category='HighROI',
            sale_price=100.00,
            cost_of_goods=10.00,
            platform_fee=1.00,
        )

        # Low ROI sale
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-16',
            item_title='Low ROI',
            units=1,
            category='LowROI',
            sale_price=50.00,
            cost_of_goods=40.00,
            platform_fee=2.00,
        )

        results = calculate_roi_by_category('2026-07-01', '2026-07-31')

        self.assertEqual(len(results), 2)
        # First should be higher ROI
        self.assertGreater(results[0]['roi_pct'], results[1]['roi_pct'])

    def test_roi_by_category_filters_current_year_only(self):
        """Test that ROI calculation filters to current year only."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Add sale from current year
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Current Year',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
        )

        # Manually add sale from past year (bypass add_sale validation)
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-15', 'Past Year', 1, 'Electronics', 200.00, 50.00))
        conn.commit()
        conn.close()

        results = calculate_roi_by_category('2026-07-01', '2026-07-31')

        # Should only include current year sales (100 cost, not 150)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['cost'], 30.00)

    def test_roi_by_category_respects_year_parameter(self):
        """Test that ROI calculation respects the year parameter for historical data."""
        current_year = datetime.now().year
        past_year = 2024

        # Add sale from 2024
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2024-07-15', 'Past Year Sale', 1, 'Electronics', 100.00, 30.00))
        conn.commit()
        conn.close()

        # Add sale from current year
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Current Year Sale',
            units=1,
            category='Electronics',
            sale_price=200.00,
            cost_of_goods=50.00,
        )

        # Query 2024 data explicitly
        results_2024 = calculate_roi_by_category('2024-07-01', '2024-07-31', year=2024)
        # Query current year data
        results_current = calculate_roi_by_category('2026-07-01', '2026-07-31', year=current_year)

        # 2024 should only have the 2024 sale
        self.assertEqual(len(results_2024), 1)
        self.assertAlmostEqual(results_2024[0]['cost'], 30.00, places=2)

        # Current year should only have the current year sale
        self.assertEqual(len(results_current), 1)
        self.assertAlmostEqual(results_current[0]['cost'], 50.00, places=2)


class TestTurnoverRate(unittest.TestCase):
    """Tests for calculate_turnover_rate function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_turnover.db')

        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

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
        """Clear sales table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM sales')
        conn.commit()
        conn.close()

    def test_turnover_rate_single_sale(self):
        """Test turnover rate calculation with single sale."""
        current_year = datetime.now().year

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            listed_date='2026-07-10',
            item_title='Test Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=10,
        )

        rate = calculate_turnover_rate('Electronics', '2026-07-01', '2026-07-31')
        self.assertAlmostEqual(rate, 10.0, places=1)

    def test_turnover_rate_multiple_sales(self):
        """Test turnover rate with multiple sales (should average)."""
        current_year = datetime.now().year

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Item 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=10,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-25',
            item_title='Item 2',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=20,
        )

        rate = calculate_turnover_rate('Electronics', '2026-07-01', '2026-07-31')
        # Average of 10 and 20 = 15
        self.assertAlmostEqual(rate, 15.0, places=1)

    def test_turnover_rate_no_sales(self):
        """Test turnover rate returns 0 when no sales found."""
        rate = calculate_turnover_rate('Nonexistent', '2026-07-01', '2026-07-31')
        self.assertEqual(rate, 0.0)

    def test_turnover_rate_different_categories(self):
        """Test turnover rate correctly filters by category."""
        current_year = datetime.now().year

        # Electronics with 10 day turnover
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Electronics Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=10,
        )

        # Clothing with 20 day turnover
        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-25',
            item_title='Clothing Item',
            units=1,
            category='Clothing',
            sale_price=50.00,
            cost_of_goods=10.00,
            days_to_sell=20,
        )

        electronics_rate = calculate_turnover_rate('Electronics', '2026-07-01', '2026-07-31')
        clothing_rate = calculate_turnover_rate('Clothing', '2026-07-01', '2026-07-31')

        self.assertAlmostEqual(electronics_rate, 10.0, places=1)
        self.assertAlmostEqual(clothing_rate, 20.0, places=1)

    def test_turnover_rate_filters_current_year_only(self):
        """Test that turnover calculation filters to current year only."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Add sale from current year with 10 days
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Current Year',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=10,
        )

        # Manually add sale from past year with 30 days
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods, days_to_sell)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-20', 'Past Year', 1, 'Electronics', 100.00, 30.00, 30))
        conn.commit()
        conn.close()

        rate = calculate_turnover_rate('Electronics', '2026-07-01', '2026-07-31')

        # Should only average current year (10, not (10+30)/2=20)
        self.assertAlmostEqual(rate, 10.0, places=1)

    def test_turnover_rate_respects_year_parameter(self):
        """Test that turnover calculation respects the year parameter for historical data."""
        current_year = datetime.now().year
        past_year = 2024

        # Add sale from 2024 with 10 days
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods, days_to_sell)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2024-07-20', 'Past Year Sale', 1, 'Electronics', 100.00, 30.00, 10))
        conn.commit()
        conn.close()

        # Add sale from current year with 20 days
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Current Year Sale',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            days_to_sell=20,
        )

        # Query 2024 data explicitly
        rate_2024 = calculate_turnover_rate('Electronics', '2024-07-01', '2024-07-31', year=2024)
        # Query current year data
        rate_current = calculate_turnover_rate('Electronics', '2026-07-01', '2026-07-31', year=current_year)

        # 2024 should only include 2024 sales (10 days)
        self.assertAlmostEqual(rate_2024, 10.0, places=1)

        # Current year should only include current year sales (20 days)
        self.assertAlmostEqual(rate_current, 20.0, places=1)


class TestPlatformImpact(unittest.TestCase):
    """Tests for calculate_platform_impact function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_platform.db')

        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

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
        """Clear sales table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM sales')
        conn.commit()
        conn.close()

    def test_platform_impact_single_sale(self):
        """Test platform impact calculation with single sale."""
        current_year = datetime.now().year

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Test Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            shipping_collected=10.00,
            cost_of_goods=30.00,
            shipping_cost=5.00,
            platform_fee=5.00,
            transaction_fee=3.00,
            promoted_fee=0.00,
        )

        impact = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31')

        self.assertEqual(impact['platform'], 'eBay')
        self.assertEqual(impact['sales_count'], 1)
        self.assertAlmostEqual(impact['total_revenue'], 110.00, places=2)  # 100 + 10
        self.assertAlmostEqual(impact['total_fees'], 8.00, places=2)  # 5 + 3 + 0
        self.assertAlmostEqual(impact['total_cost'], 30.00, places=2)
        # net_profit = 110 - 8 - 30 = 72
        self.assertAlmostEqual(impact['net_profit'], 72.00, places=2)
        # fee_pct = 8/110 * 100 = 7.27%
        self.assertAlmostEqual(impact['fee_percentage'], 7.27, places=2)

    def test_platform_impact_multiple_sales(self):
        """Test platform impact with multiple sales (should aggregate)."""
        current_year = datetime.now().year

        # Sale 1
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Item 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            platform_fee=5.00,
            transaction_fee=3.00,
        )

        # Sale 2
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Item 2',
            units=1,
            category='Electronics',
            sale_price=50.00,
            cost_of_goods=20.00,
            platform_fee=2.00,
            transaction_fee=1.50,
        )

        impact = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31')

        self.assertEqual(impact['sales_count'], 2)
        self.assertAlmostEqual(impact['total_revenue'], 150.00, places=2)  # 100 + 50
        self.assertAlmostEqual(impact['total_fees'], 11.50, places=2)  # (5+3) + (2+1.5)
        self.assertAlmostEqual(impact['total_cost'], 50.00, places=2)  # 30 + 20

    def test_platform_impact_no_sales(self):
        """Test platform impact returns empty dict when no sales found."""
        impact = calculate_platform_impact('NonexistentPlatform', '2026-07-01', '2026-07-31')
        self.assertEqual(impact, {})

    def test_platform_impact_different_platforms(self):
        """Test platform impact correctly filters by platform."""
        current_year = datetime.now().year

        # eBay sale
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='eBay Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            platform_fee=5.00,
            transaction_fee=3.00,
        )

        # Poshmark sale
        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-20',
            item_title='Poshmark Item',
            units=1,
            category='Clothing',
            sale_price=80.00,
            cost_of_goods=20.00,
            platform_fee=16.00,  # 20% on Poshmark
        )

        ebay_impact = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31')
        poshmark_impact = calculate_platform_impact('Poshmark', '2026-07-01', '2026-07-31')

        self.assertEqual(ebay_impact['sales_count'], 1)
        self.assertEqual(poshmark_impact['sales_count'], 1)
        self.assertNotEqual(ebay_impact['total_fees'], poshmark_impact['total_fees'])

    def test_platform_impact_zero_revenue(self):
        """Test platform impact handles zero revenue (fee percentage should be 0)."""
        current_year = datetime.now().year

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='No Price',
            units=1,
            category='Electronics',
            sale_price=0.00,
            shipping_collected=0.00,
            cost_of_goods=30.00,
            platform_fee=0.00,
            transaction_fee=0.00,
        )

        impact = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31')

        self.assertAlmostEqual(impact['total_revenue'], 0.00, places=2)
        self.assertEqual(impact['fee_percentage'], 0)

    def test_platform_impact_filters_current_year_only(self):
        """Test that platform impact filters to current year only."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Add sale from current year
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Current Year',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
            platform_fee=5.00,
        )

        # Manually add sale from past year
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods, platform_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-15', 'Past Year', 1, 'Electronics', 200.00, 50.00, 10.00))
        conn.commit()
        conn.close()

        impact = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31')

        # Should only include current year sales (100 revenue, not 300)
        self.assertEqual(impact['sales_count'], 1)
        self.assertAlmostEqual(impact['total_revenue'], 100.00, places=2)

    def test_platform_impact_respects_year_parameter(self):
        """Test that platform impact respects the year parameter for historical data."""
        current_year = datetime.now().year
        past_year = 2024

        # Add sale from 2024
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods, platform_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2024-07-15', 'Past Year Sale', 1, 'Electronics', 100.00, 30.00, 5.00))
        conn.commit()
        conn.close()

        # Add sale from current year
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Current Year Sale',
            units=1,
            category='Electronics',
            sale_price=200.00,
            cost_of_goods=50.00,
            platform_fee=10.00,
        )

        # Query 2024 data explicitly
        impact_2024 = calculate_platform_impact('eBay', '2024-07-01', '2024-07-31', year=2024)
        # Query current year data
        impact_current = calculate_platform_impact('eBay', '2026-07-01', '2026-07-31', year=current_year)

        # 2024 should only include 2024 sales
        self.assertEqual(impact_2024['sales_count'], 1)
        self.assertAlmostEqual(impact_2024['total_revenue'], 100.00, places=2)

        # Current year should only include current year sales
        self.assertEqual(impact_current['sales_count'], 1)
        self.assertAlmostEqual(impact_current['total_revenue'], 200.00, places=2)


if __name__ == '__main__':
    unittest.main()
