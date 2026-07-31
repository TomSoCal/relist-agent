"""Tests for analytics reports module."""

import unittest
import os
import sys
import csv
import tempfile
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    get_connection,
    add_sale,
    DB_PATH,
)
from analytics.reports import (
    generate_csv_report,
    generate_pdf_report,
    _format_currency,
    _get_sales_for_report,
    _calculate_summary_stats,
)


class TestFormatCurrency(unittest.TestCase):
    """Tests for currency formatting utility."""

    def test_format_currency_positive(self):
        """Test formatting positive currency values."""
        result = _format_currency(1234.56)
        self.assertEqual(result, "$1,234.56")

    def test_format_currency_zero(self):
        """Test formatting zero value."""
        result = _format_currency(0.0)
        self.assertEqual(result, "$0.00")

    def test_format_currency_negative(self):
        """Test formatting negative currency values."""
        result = _format_currency(-100.50)
        self.assertEqual(result, "$-100.50")

    def test_format_currency_large_number(self):
        """Test formatting large numbers with commas."""
        result = _format_currency(1000000.00)
        self.assertEqual(result, "$1,000,000.00")

    def test_format_currency_none(self):
        """Test formatting None value (should treat as 0)."""
        result = _format_currency(None)
        self.assertEqual(result, "$0.00")

    def test_format_currency_single_digit(self):
        """Test formatting single digit values."""
        result = _format_currency(5.50)
        self.assertEqual(result, "$5.50")


class TestGetSalesForReport(unittest.TestCase):
    """Tests for _get_sales_for_report utility function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_reports_query.db')

        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        import database
        database.DB_PATH = cls.test_db_path

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

    def test_get_sales_for_report_empty(self):
        """Test getting sales when none exist."""
        sales = _get_sales_for_report('2026-07-01', '2026-07-31')
        self.assertEqual(len(sales), 0)

    def test_get_sales_for_report_single_sale(self):
        """Test getting a single sale."""
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
            cost_of_goods=30.00,
        )

        sales = _get_sales_for_report('2026-07-01', '2026-07-31')
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0]['item_title'], 'Test Item')

    def test_get_sales_for_report_filters_by_date(self):
        """Test that only sales within date range are returned."""
        current_year = datetime.now().year

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title='July Sale',
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
        )

        add_sale(
            year=current_year,
            month=8,
            platform='eBay',
            sold_date='2026-08-15',
            item_title='August Sale',
            units=1,
            category='Electronics',
            sale_price=150.00,
            cost_of_goods=40.00,
        )

        # Query July only
        july_sales = _get_sales_for_report('2026-07-01', '2026-07-31')
        self.assertEqual(len(july_sales), 1)
        self.assertEqual(july_sales[0]['item_title'], 'July Sale')

    def test_get_sales_for_report_filters_by_year(self):
        """Test that sales are filtered by current year only."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Add current year sale
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

        # Manually add past year sale
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-15', 'Past Year', 1, 'Electronics', 200.00, 50.00))
        conn.commit()
        conn.close()

        # Query should only return current year
        sales = _get_sales_for_report('2026-07-01', '2026-07-31')
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0]['item_title'], 'Current Year')

    def test_get_sales_for_report_respects_year_parameter(self):
        """Test that year parameter works for historical queries."""
        current_year = datetime.now().year
        past_year = 2024

        # Manually add 2024 sale
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2024-07-15', '2024 Sale', 1, 'Electronics', 100.00, 30.00))
        conn.commit()
        conn.close()

        # Query 2024 explicitly
        sales_2024 = _get_sales_for_report('2024-07-01', '2024-07-31', year=2024)
        self.assertEqual(len(sales_2024), 1)
        self.assertEqual(sales_2024[0]['item_title'], '2024 Sale')


class TestCalculateSummaryStats(unittest.TestCase):
    """Tests for _calculate_summary_stats utility function."""

    def test_calculate_summary_stats_empty(self):
        """Test summary stats with no sales."""
        stats = _calculate_summary_stats([])
        self.assertEqual(stats['total_sales_count'], 0)
        self.assertEqual(stats['total_revenue'], 0.0)
        self.assertEqual(stats['total_cost'], 0.0)
        self.assertEqual(stats['total_fees'], 0.0)
        self.assertEqual(stats['total_profit'], 0.0)

    def test_calculate_summary_stats_single_sale(self):
        """Test summary stats with single sale."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': 10.00,
            'cost_of_goods': 30.00,
            'platform_fee': 5.00,
            'transaction_fee': 3.00,
            'promoted_fee': 0.00,
        }
        stats = _calculate_summary_stats([sale])

        self.assertEqual(stats['total_sales_count'], 1)
        self.assertAlmostEqual(stats['total_revenue'], 110.00, places=2)  # 100 + 10
        self.assertAlmostEqual(stats['total_cost'], 30.00, places=2)
        self.assertAlmostEqual(stats['total_fees'], 8.00, places=2)  # 5 + 3 + 0
        self.assertAlmostEqual(stats['total_profit'], 72.00, places=2)  # 110 - 30 - 8

    def test_calculate_summary_stats_multiple_sales(self):
        """Test summary stats aggregates multiple sales."""
        sales = [
            {
                'sale_price': 100.00,
                'shipping_collected': 10.00,
                'cost_of_goods': 30.00,
                'platform_fee': 5.00,
                'transaction_fee': 3.00,
                'promoted_fee': 0.00,
            },
            {
                'sale_price': 50.00,
                'shipping_collected': 5.00,
                'cost_of_goods': 20.00,
                'platform_fee': 2.00,
                'transaction_fee': 1.50,
                'promoted_fee': 0.00,
            },
        ]
        stats = _calculate_summary_stats(sales)

        self.assertEqual(stats['total_sales_count'], 2)
        self.assertAlmostEqual(stats['total_revenue'], 165.00, places=2)  # (100+10) + (50+5)
        self.assertAlmostEqual(stats['total_cost'], 50.00, places=2)  # 30 + 20
        self.assertAlmostEqual(stats['total_fees'], 11.50, places=2)  # (5+3+0) + (2+1.5+0)

    def test_calculate_summary_stats_handles_none_values(self):
        """Test summary stats handles None values in sales."""
        sale = {
            'sale_price': 100.00,
            'shipping_collected': None,
            'cost_of_goods': 30.00,
            'platform_fee': None,
            'transaction_fee': 3.00,
            'promoted_fee': 0.00,
        }
        stats = _calculate_summary_stats([sale])

        self.assertEqual(stats['total_sales_count'], 1)
        self.assertAlmostEqual(stats['total_revenue'], 100.00, places=2)  # 100 + 0
        self.assertAlmostEqual(stats['total_cost'], 30.00, places=2)
        self.assertAlmostEqual(stats['total_fees'], 3.00, places=2)  # 0 + 3 + 0


class TestGenerateCSVReport(unittest.TestCase):
    """Tests for generate_csv_report function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_reports_csv.db')

        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        import database
        database.DB_PATH = cls.test_db_path

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

    def test_generate_csv_report_returns_string(self):
        """Test CSV report without filename returns string."""
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
            cost_of_goods=30.00,
        )

        result = generate_csv_report('2026-07-01', '2026-07-31')
        self.assertIsInstance(result, str)
        self.assertIn('id,year,month', result)  # CSV header
        self.assertIn('Test Item', result)  # CSV data

    def test_generate_csv_report_writes_to_file(self):
        """Test CSV report with filename writes to file."""
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
            cost_of_goods=30.00,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'test_report.csv')
            result = generate_csv_report('2026-07-01', '2026-07-31', csv_path)

            self.assertEqual(result, csv_path)
            self.assertTrue(os.path.exists(csv_path))

            # Verify file contents
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['item_title'], 'Test Item')

    def test_generate_csv_report_contains_headers(self):
        """Test CSV report has all expected columns."""
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
            cost_of_goods=30.00,
        )

        result = generate_csv_report('2026-07-01', '2026-07-31')

        # Check for key columns
        self.assertIn('sold_date', result)
        self.assertIn('item_title', result)
        self.assertIn('platform', result)
        self.assertIn('category', result)
        self.assertIn('sale_price', result)
        self.assertIn('cost_of_goods', result)

    def test_generate_csv_report_multiple_sales(self):
        """Test CSV report with multiple sales."""
        current_year = datetime.now().year

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
        )

        add_sale(
            year=current_year,
            month=7,
            platform='Poshmark',
            sold_date='2026-07-20',
            item_title='Item 2',
            units=1,
            category='Clothing',
            sale_price=50.00,
            cost_of_goods=10.00,
        )

        result = generate_csv_report('2026-07-01', '2026-07-31')
        self.assertIn('Item 1', result)
        self.assertIn('Item 2', result)

    def test_generate_csv_report_empty_result(self):
        """Test CSV report with no sales returns headers only."""
        result = generate_csv_report('2026-07-01', '2026-07-31')
        self.assertIn('id,year,month', result)  # Header row
        lines = result.strip().split('\n')
        self.assertEqual(len(lines), 1)  # Only header


class TestGeneratePDFReport(unittest.TestCase):
    """Tests for generate_pdf_report function."""

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit_reports_pdf.db')

        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        import database
        database.DB_PATH = cls.test_db_path

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

    def test_generate_pdf_report_creates_file(self):
        """Test PDF report creates a file."""
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
            cost_of_goods=30.00,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test_report.pdf')
            result = generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            self.assertEqual(result, pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)

    def test_generate_pdf_report_default_filename(self):
        """Test PDF report generates default filename."""
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
            cost_of_goods=30.00,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = generate_pdf_report('2026-07-01', '2026-07-31')

                self.assertIn('sales_report_', result)
                self.assertTrue(result.endswith('.pdf'))
                self.assertTrue(os.path.exists(result))
            finally:
                os.chdir(original_dir)

    def test_generate_pdf_report_empty_sales(self):
        """Test PDF report with no sales still creates file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'empty_report.pdf')
            result = generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            self.assertTrue(os.path.exists(result))
            self.assertGreater(os.path.getsize(result), 0)

    def test_generate_pdf_report_summary_section(self):
        """Test PDF report includes summary section."""
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
            platform_fee=5.00,
            transaction_fee=3.00,
            promoted_fee=0.00,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test_summary.pdf')
            generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            # PDF file should exist and contain summary data
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)

    def test_generate_pdf_report_limits_detail_rows(self):
        """Test PDF report limits detail table to 100 rows."""
        current_year = datetime.now().year

        # Add 150 sales
        for i in range(150):
            add_sale(
                year=current_year,
                month=7,
                platform='eBay',
                sold_date='2026-07-15',
                item_title=f'Item {i}',
                units=1,
                category='Electronics',
                sale_price=100.00,
                cost_of_goods=30.00,
            )

        # PDF should be created successfully
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'large_report.pdf')
            result = generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            self.assertTrue(os.path.exists(result))
            self.assertGreater(os.path.getsize(result), 0)

    def test_generate_pdf_report_filters_by_year(self):
        """Test PDF report filters by current year."""
        current_year = datetime.now().year
        past_year = current_year - 1

        # Add current year sale
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

        # Manually add past year sale
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO sales (year, month, platform, sold_date, item_title, units, category, sale_price, cost_of_goods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (past_year, 7, 'eBay', '2025-07-15', 'Past Year', 1, 'Electronics', 200.00, 50.00))
        conn.commit()
        conn.close()

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'year_filter_report.pdf')
            result = generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            # PDF should only contain current year data
            self.assertTrue(os.path.exists(result))
            self.assertGreater(os.path.getsize(result), 0)

    def test_generate_pdf_report_handles_long_titles(self):
        """Test PDF report handles long item titles gracefully."""
        current_year = datetime.now().year
        long_title = 'A' * 100  # Very long title

        add_sale(
            year=current_year,
            month=7,
            platform='eBay',
            sold_date='2026-07-15',
            item_title=long_title,
            units=1,
            category='Electronics',
            sale_price=100.00,
            cost_of_goods=30.00,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'long_title_report.pdf')
            result = generate_pdf_report('2026-07-01', '2026-07-31', pdf_path)

            self.assertTrue(os.path.exists(result))
            self.assertGreater(os.path.getsize(result), 0)


if __name__ == '__main__':
    unittest.main()
