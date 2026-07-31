"""Tests for analytics forecasting module."""

import unittest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    get_connection,
    add_sale,
    DB_PATH,
)
from analytics.forecasting import (
    forecast_sales_units,
    forecast_revenue,
    forecast_inventory_turnover,
    forecast_seasonal_impact,
)


class TestForecastSalesUnits(unittest.TestCase):
    """Tests for forecast_sales_units function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_forecast_units.db')

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
        """Clear sales table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM sales')
        conn.commit()
        conn.close()

    def test_forecast_sales_units_no_sales(self):
        """Test forecast returns 0 when no sales data exists."""
        forecast = forecast_sales_units(30)
        self.assertEqual(forecast, 0)

    def test_forecast_sales_units_basic(self):
        """Test basic sales units forecast calculation."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 90 sales over last 90 days (1 per day) = 90 total units
        for i in range(90):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # Forecast for 30 days: (90 units / 90 days) * 30 days = 30 units
        forecast = forecast_sales_units(30)
        self.assertEqual(forecast, 30)

    def test_forecast_sales_units_multiple_units(self):
        """Test forecast with items having multiple units."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 10 sales with 5 units each over 10 days = 50 total units over 10 days
        for i in range(10):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=5,
                category='Electronics',
                sale_price=100.00,
            )

        # Average daily: 50 units / 90 days = 0.556 units/day
        # 30 day forecast: 0.556 * 30 = 16.67 ≈ 17 units
        forecast = forecast_sales_units(30)
        self.assertGreaterEqual(forecast, 16)
        self.assertLessEqual(forecast, 18)

    def test_forecast_sales_units_custom_period(self):
        """Test forecast with custom period (60 days instead of 30)."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 90 sales = 90 total units
        for i in range(90):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # 60 day forecast: (90 / 90) * 60 = 60 units
        forecast = forecast_sales_units(60)
        self.assertEqual(forecast, 60)

    def test_forecast_sales_units_filters_current_year_only(self):
        """Test that forecast only includes current year sales."""
        current_year = datetime.now().year
        past_year = current_year - 1
        today = datetime.now().date()

        # Add 90 current year sales
        for i in range(90):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Current {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # Manually add 90 past year sales (would double forecast if included)
        conn = get_connection()
        c = conn.cursor()
        for i in range(90):
            past_date = (datetime(past_year, 7, 1).date() - timedelta(days=i)).isoformat()
            c.execute('''
                INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (past_year, 7, 'eBay', past_date, f'Past {i}', 1, 'Electronics', 100.00))
        conn.commit()
        conn.close()

        # Forecast should only use current year (30 units, not 60)
        forecast = forecast_sales_units(30)
        self.assertEqual(forecast, 30)

    def test_forecast_sales_units_only_last_90_days(self):
        """Test that forecast only uses last 90 days, not older sales."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 50 sales from last 90 days = 50 total units
        for i in range(50):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Recent {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # Add 40 sales from 91+ days ago (should be ignored)
        for i in range(91, 131):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Old {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # Forecast based on 50 units only: (50 / 90) * 30 ≈ 17
        forecast = forecast_sales_units(30)
        self.assertGreaterEqual(forecast, 16)
        self.assertLessEqual(forecast, 18)


class TestForecastRevenue(unittest.TestCase):
    """Tests for forecast_revenue function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_forecast_revenue.db')

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

    def test_forecast_revenue_no_sales(self):
        """Test forecast returns 0.0 when no sales data exists."""
        forecast = forecast_revenue(30)
        self.assertAlmostEqual(forecast, 0.0, places=2)

    def test_forecast_revenue_basic(self):
        """Test basic revenue forecast calculation."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 30 sales of $100 each over last 90 days
        # Average revenue per sale = $100
        # Average daily sales = 30/90 = 0.33 per day
        # 30 day forecast = 0.33 * 30 = 10 sales expected
        # Forecast revenue = $100 * 10 = $1000
        for i in range(30):
            sale_date = (today - timedelta(days=i*3)).isoformat()  # Every 3 days
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
                shipping_collected=0.00,
            )

        forecast = forecast_revenue(30)
        # Should be approximately 1000
        self.assertGreater(forecast, 900)
        self.assertLess(forecast, 1100)

    def test_forecast_revenue_includes_shipping(self):
        """Test revenue forecast includes shipping collected."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 10 sales: $100 price + $10 shipping
        # Average revenue per sale = $110
        for i in range(10):
            sale_date = (today - timedelta(days=i*9)).isoformat()  # Spread over 90 days
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
                shipping_collected=10.00,
            )

        # Average daily: 10/90 = 0.11 per day
        # 30 day forecast: 0.11 * 30 = 3.3 units ≈ 3 units (rounded)
        # Forecast revenue: $110 * 3 = $330
        forecast = forecast_revenue(30)
        self.assertGreater(forecast, 300)
        self.assertLess(forecast, 350)

    def test_forecast_revenue_custom_period(self):
        """Test revenue forecast with custom period."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 30 sales of $100 each
        for i in range(30):
            sale_date = (today - timedelta(days=i*3)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # 60 day forecast should be roughly 2x the 30 day forecast
        forecast_30 = forecast_revenue(30)
        forecast_60 = forecast_revenue(60)

        self.assertGreater(forecast_60, forecast_30)

    def test_forecast_revenue_filters_current_year_only(self):
        """Test that revenue forecast only includes current year sales."""
        current_year = datetime.now().year
        past_year = current_year - 1
        today = datetime.now().date()

        # Add 30 current year sales of $100 each
        for i in range(30):
            sale_date = (today - timedelta(days=i*3)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Current {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
            )

        # Manually add 30 past year sales (would double forecast if included)
        conn = get_connection()
        c = conn.cursor()
        for i in range(30):
            past_date = (datetime(past_year, 7, 1).date() - timedelta(days=i*3)).isoformat()
            c.execute('''
                INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (past_year, 7, 'eBay', past_date, f'Past {i}', 1, 'Electronics', 100.00))
        conn.commit()
        conn.close()

        # Get forecast based on current year only
        forecast = forecast_revenue(30)

        # Should not be doubled by past year data
        self.assertLess(forecast, 1500)


class TestForecastInventoryTurnover(unittest.TestCase):
    """Tests for forecast_inventory_turnover function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_forecast_turnover.db')

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

    def test_inventory_turnover_no_sales(self):
        """Test turnover returns 0.0 when no sales exist."""
        turnover = forecast_inventory_turnover('Electronics')
        self.assertAlmostEqual(turnover, 0.0, places=1)

    def test_inventory_turnover_single_sale(self):
        """Test turnover calculation with single sale."""
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
            days_to_sell=10,
        )

        turnover = forecast_inventory_turnover('Electronics')
        self.assertAlmostEqual(turnover, 10.0, places=1)

    def test_inventory_turnover_multiple_sales(self):
        """Test turnover averages multiple sales."""
        current_year = datetime.now().year

        # Sale with 10 days to sell
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Item 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
            days_to_sell=10,
        )

        # Sale with 20 days to sell
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-25',
            item_title='Item 2',
            units=1,
            category='Electronics',
            sale_price=100.00,
            days_to_sell=20,
        )

        # Average = (10 + 20) / 2 = 15
        turnover = forecast_inventory_turnover('Electronics')
        self.assertAlmostEqual(turnover, 15.0, places=1)

    def test_inventory_turnover_different_categories(self):
        """Test turnover correctly filters by category."""
        current_year = datetime.now().year

        # Electronics: 10 days
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Electronics Item',
            units=1,
            category='Electronics',
            sale_price=100.00,
            days_to_sell=10,
        )

        # Clothing: 20 days
        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-25',
            item_title='Clothing Item',
            units=1,
            category='Clothing',
            sale_price=50.00,
            days_to_sell=20,
        )

        electronics_turnover = forecast_inventory_turnover('Electronics')
        clothing_turnover = forecast_inventory_turnover('Clothing')

        self.assertAlmostEqual(electronics_turnover, 10.0, places=1)
        self.assertAlmostEqual(clothing_turnover, 20.0, places=1)

    def test_inventory_turnover_filters_current_year_only(self):
        """Test that turnover only includes current year sales."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Current year: 10 days
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Current Year',
            units=1,
            category='Electronics',
            sale_price=100.00,
            days_to_sell=10,
        )

        # Past year: 30 days (should be ignored)
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, days_to_sell)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-20', 'Past Year', 1, 'Electronics', 100.00, 30))
        conn.commit()
        conn.close()

        turnover = forecast_inventory_turnover('Electronics')

        # Should only include current year (10, not 20)
        self.assertAlmostEqual(turnover, 10.0, places=1)

    def test_inventory_turnover_last_180_days(self):
        """Test that turnover only uses last 180 days."""
        current_year = datetime.now().year
        today = datetime.now().date()

        # Add 5 sales from last 180 days: average 15 days
        for i in range(5):
            sale_date = (today - timedelta(days=i*30)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Recent {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
                days_to_sell=15,
            )

        # Add 3 sales from 181+ days ago (should be ignored)
        for i in range(181, 271, 30):
            sale_date = (today - timedelta(days=i)).isoformat()
            add_sale(
                year=current_year,
                month=datetime.fromisoformat(sale_date).month,
                platform='eBay',
                sold_date=sale_date,
                item_title=f'Old {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
                days_to_sell=5,
            )

        turnover = forecast_inventory_turnover('Electronics')

        # Should only average recent sales (15 days, not mixed)
        self.assertAlmostEqual(turnover, 15.0, places=1)


class TestForecastSeasonalImpact(unittest.TestCase):
    """Tests for forecast_seasonal_impact function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_forecast_seasonal.db')

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

    def test_seasonal_impact_no_sales(self):
        """Test seasonal impact returns empty dict when no sales exist."""
        impact = forecast_seasonal_impact(7)
        self.assertEqual(impact, {})

    def test_seasonal_impact_single_month(self):
        """Test seasonal impact with single month of sales."""
        current_year = datetime.now().year

        # Add 3 sales in July: $100, $200, $300 (avg revenue = $600)
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-10',
            item_title='Item 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
            shipping_collected=0.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Item 2',
            units=1,
            category='Clothing',
            sale_price=200.00,
            shipping_collected=0.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-20',
            item_title='Item 3',
            units=1,
            category='Electronics',
            sale_price=300.00,
            shipping_collected=0.00,
        )

        impact = forecast_seasonal_impact(7)

        self.assertEqual(impact['month'], 7)
        self.assertEqual(impact['month_name'], 'July')
        self.assertEqual(impact['avg_sales'], 3)
        self.assertAlmostEqual(impact['avg_revenue'], 600.0, places=2)
        self.assertIsNotNone(impact['best_category'])
        self.assertGreater(impact['best_category_revenue'], 0)

    def test_seasonal_impact_best_category(self):
        """Test that seasonal impact correctly identifies best category."""
        current_year = datetime.now().year

        # Electronics: $100 + $100 = $200
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-10',
            item_title='Electronics 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-11',
            item_title='Electronics 2',
            units=1,
            category='Electronics',
            sale_price=100.00,
        )

        # Clothing: $500 (best category)
        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-15',
            item_title='Clothing 1',
            units=1,
            category='Clothing',
            sale_price=500.00,
        )

        impact = forecast_seasonal_impact(7)

        self.assertEqual(impact['best_category'], 'Clothing')
        self.assertAlmostEqual(impact['best_category_revenue'], 500.0, places=2)

    def test_seasonal_impact_different_months(self):
        """Test seasonal impact for different months."""
        current_year = datetime.now().year

        # July: 2 sales, $300 total
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-10',
            item_title='July 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='July 2',
            units=1,
            category='Electronics',
            sale_price=200.00,
        )

        # August: 1 sale, $150 total
        add_sale(
            year=current_year,
            month=8,
            platform='eBay',
            sold_date='2026-08-10',
            item_title='August 1',
            units=1,
            category='Clothing',
            sale_price=150.00,
        )

        july_impact = forecast_seasonal_impact(7)
        august_impact = forecast_seasonal_impact(8)

        self.assertEqual(july_impact['avg_sales'], 2)
        self.assertAlmostEqual(july_impact['avg_revenue'], 300.0, places=2)

        self.assertEqual(august_impact['avg_sales'], 1)
        self.assertAlmostEqual(august_impact['avg_revenue'], 150.0, places=2)

    def test_seasonal_impact_invalid_month(self):
        """Test seasonal impact raises error for invalid month."""
        with self.assertRaises(ValueError):
            forecast_seasonal_impact(0)

        with self.assertRaises(ValueError):
            forecast_seasonal_impact(13)

    def test_seasonal_impact_includes_shipping(self):
        """Test seasonal impact includes shipping in revenue calculation."""
        current_year = datetime.now().year

        # Sale: $100 price + $10 shipping = $110 total
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-10',
            item_title='Item with Shipping',
            units=1,
            category='Electronics',
            sale_price=100.00,
            shipping_collected=10.00,
        )

        impact = forecast_seasonal_impact(7)

        self.assertAlmostEqual(impact['avg_revenue'], 110.0, places=2)

    def test_seasonal_impact_filters_current_year_only(self):
        """Test that seasonal impact only includes current year sales."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Current year: 2 sales, $300 total
        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-10',
            item_title='Current 1',
            units=1,
            category='Electronics',
            sale_price=100.00,
        )

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='Current 2',
            units=1,
            category='Electronics',
            sale_price=200.00,
        )

        # Past year: 3 sales, $600 total (should be ignored)
        conn = get_connection()
        c = conn.cursor()
        for i, price in enumerate([100, 200, 300]):
            c.execute('''
                INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (past_year, 7, 'eBay', f'2025-07-{10+i*5}', f'Past {i}', 1, 'Electronics', price))
        conn.commit()
        conn.close()

        impact = forecast_seasonal_impact(7)

        # Should only include current year (2 sales, $300)
        self.assertEqual(impact['avg_sales'], 2)
        self.assertAlmostEqual(impact['avg_revenue'], 300.0, places=2)


if __name__ == '__main__':
    unittest.main()
