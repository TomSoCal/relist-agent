"""Tests for analytics date_utils module."""

import unittest
import os
import sys
from datetime import datetime, timedelta
import calendar

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.date_utils import (
    get_days_elapsed_this_month,
    get_days_left_this_month,
    get_months_elapsed_this_year,
    get_months_left_this_year,
    get_percent_year_elapsed,
    get_month_start_end,
    get_year_start_end,
    get_last_30_days,
    get_month_name,
)


class TestDaysElapsedThisMonth(unittest.TestCase):
    """Tests for get_days_elapsed_this_month function."""

    def test_days_elapsed_returns_int(self):
        """Test that function returns an integer."""
        result = get_days_elapsed_this_month()
        self.assertIsInstance(result, int)

    def test_days_elapsed_in_range(self):
        """Test that day of month is between 1 and 31."""
        result = get_days_elapsed_this_month()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 31)

    def test_days_elapsed_matches_today(self):
        """Test that returned day matches current day of month."""
        today = datetime.now()
        result = get_days_elapsed_this_month()
        self.assertEqual(result, today.day)


class TestDaysLeftThisMonth(unittest.TestCase):
    """Tests for get_days_left_this_month function."""

    def test_days_left_returns_int(self):
        """Test that function returns an integer."""
        result = get_days_left_this_month()
        self.assertIsInstance(result, int)

    def test_days_left_in_range(self):
        """Test that days left are between 0 and 30."""
        result = get_days_left_this_month()
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 30)

    def test_days_elapsed_plus_left_equals_month_days(self):
        """Test that days_elapsed + days_left approximately equals days in month."""
        today = datetime.now()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_elapsed = get_days_elapsed_this_month()
        days_left = get_days_left_this_month()
        # days_elapsed + days_left should equal days_in_month (due to current day)
        self.assertEqual(days_elapsed + days_left, days_in_month)


class TestMonthsElapsedThisYear(unittest.TestCase):
    """Tests for get_months_elapsed_this_year function."""

    def test_months_elapsed_returns_int(self):
        """Test that function returns an integer."""
        result = get_months_elapsed_this_year()
        self.assertIsInstance(result, int)

    def test_months_elapsed_in_range(self):
        """Test that months elapsed are between 0 and 11."""
        result = get_months_elapsed_this_year()
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 11)

    def test_months_elapsed_matches_current_month(self):
        """Test that months elapsed matches current month (0-indexed)."""
        today = datetime.now()
        result = get_months_elapsed_this_year()
        self.assertEqual(result, today.month - 1)


class TestMonthsLeftThisYear(unittest.TestCase):
    """Tests for get_months_left_this_year function."""

    def test_months_left_returns_int(self):
        """Test that function returns an integer."""
        result = get_months_left_this_year()
        self.assertIsInstance(result, int)

    def test_months_left_in_range(self):
        """Test that months left are between 0 and 11."""
        result = get_months_left_this_year()
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 11)

    def test_months_elapsed_plus_left_equals_11(self):
        """Test that months_elapsed + months_left = 11 (current month is part of elapsed)."""
        months_elapsed = get_months_elapsed_this_year()
        months_left = get_months_left_this_year()
        # Current month is in elapsed, so we have 11 total (not counting Dec if in Dec)
        self.assertEqual(months_elapsed + months_left, 11)


class TestPercentYearElapsed(unittest.TestCase):
    """Tests for get_percent_year_elapsed function."""

    def test_percent_returns_float(self):
        """Test that function returns a float."""
        result = get_percent_year_elapsed()
        self.assertIsInstance(result, float)

    def test_percent_in_range(self):
        """Test that percentage is between 0 and 100."""
        result = get_percent_year_elapsed()
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 100.0)

    def test_percent_correlates_with_month(self):
        """Test that percent increases with month number."""
        today = datetime.now()
        result = get_percent_year_elapsed()

        # Very rough test: each month should be roughly 1/12th of year
        # At month 1, should be ~0-8%, at month 6 should be ~41-58%, at month 12 should be ~92-100%
        if today.month <= 3:
            self.assertLess(result, 30.0)
        elif today.month <= 6:
            self.assertGreater(result, 25.0)
            self.assertLess(result, 60.0)
        elif today.month <= 9:
            self.assertGreater(result, 55.0)
            self.assertLess(result, 80.0)
        else:
            self.assertGreater(result, 75.0)


class TestMonthStartEnd(unittest.TestCase):
    """Tests for get_month_start_end function."""

    def test_month_start_end_returns_tuple(self):
        """Test that function returns a tuple."""
        result = get_month_start_end()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_month_start_end_datetime_objects(self):
        """Test that both elements are datetime objects."""
        start, end = get_month_start_end()
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)

    def test_month_start_end_start_before_end(self):
        """Test that start date is before end date."""
        start, end = get_month_start_end()
        self.assertLess(start, end)

    def test_month_start_end_start_is_first_day(self):
        """Test that start is the first day of the month."""
        start, end = get_month_start_end()
        self.assertEqual(start.day, 1)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)

    def test_month_start_end_end_is_last_day(self):
        """Test that end is the last day of the month."""
        today = datetime.now()
        start, end = get_month_start_end()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        self.assertEqual(end.day, days_in_month)
        self.assertEqual(end.month, start.month)
        self.assertEqual(end.year, start.year)

    def test_month_start_end_same_year_and_month(self):
        """Test that start and end are in the same month and year."""
        start, end = get_month_start_end()
        self.assertEqual(start.year, end.year)
        self.assertEqual(start.month, end.month)


class TestYearStartEnd(unittest.TestCase):
    """Tests for get_year_start_end function."""

    def test_year_start_end_returns_tuple(self):
        """Test that function returns a tuple."""
        result = get_year_start_end()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_year_start_end_datetime_objects(self):
        """Test that both elements are datetime objects."""
        start, end = get_year_start_end()
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)

    def test_year_start_end_start_before_end(self):
        """Test that start date is before end date."""
        start, end = get_year_start_end()
        self.assertLess(start, end)

    def test_year_start_end_start_is_jan_1(self):
        """Test that start is January 1st."""
        start, end = get_year_start_end()
        self.assertEqual(start.month, 1)
        self.assertEqual(start.day, 1)

    def test_year_start_end_end_is_dec_31(self):
        """Test that end is December 31st."""
        start, end = get_year_start_end()
        self.assertEqual(end.month, 12)
        self.assertEqual(end.day, 31)

    def test_year_start_end_same_year(self):
        """Test that start and end are in the same year."""
        start, end = get_year_start_end()
        self.assertEqual(start.year, end.year)

    def test_year_start_end_current_year(self):
        """Test that dates are in the current year."""
        today = datetime.now()
        start, end = get_year_start_end()
        self.assertEqual(start.year, today.year)
        self.assertEqual(end.year, today.year)


class TestLast30Days(unittest.TestCase):
    """Tests for get_last_30_days function."""

    def test_last_30_days_returns_tuple(self):
        """Test that function returns a tuple."""
        result = get_last_30_days()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_last_30_days_datetime_objects(self):
        """Test that both elements are datetime objects."""
        start, end = get_last_30_days()
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)

    def test_last_30_days_start_before_end(self):
        """Test that start date is before end date."""
        start, end = get_last_30_days()
        self.assertLess(start, end)

    def test_last_30_days_range_is_30_days(self):
        """Test that the range is exactly 30 days."""
        start, end = get_last_30_days()
        diff = (end - start).days
        self.assertEqual(diff, 30)

    def test_last_30_days_end_is_approximately_today(self):
        """Test that end date is approximately today."""
        start, end = get_last_30_days()
        today = datetime.now()
        # Should be within 1 second
        time_diff = (today - end).total_seconds()
        self.assertLess(abs(time_diff), 2)

    def test_last_30_days_start_30_days_back(self):
        """Test that start is approximately 30 days before end."""
        start, end = get_last_30_days()
        expected_start = end - timedelta(days=30)
        # Allow small time difference
        diff = abs((start - expected_start).total_seconds())
        self.assertLess(diff, 2)


class TestMonthName(unittest.TestCase):
    """Tests for get_month_name function."""

    def test_month_name_returns_string(self):
        """Test that function returns a string."""
        result = get_month_name(1)
        self.assertIsInstance(result, str)

    def test_all_12_months(self):
        """Test all 12 month names."""
        expected = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for month_num, expected_name in enumerate(expected, start=1):
            with self.subTest(month=month_num):
                result = get_month_name(month_num)
                self.assertEqual(result, expected_name)

    def test_month_name_january(self):
        """Test January."""
        self.assertEqual(get_month_name(1), "January")

    def test_month_name_june(self):
        """Test June."""
        self.assertEqual(get_month_name(6), "June")

    def test_month_name_december(self):
        """Test December."""
        self.assertEqual(get_month_name(12), "December")

    def test_month_name_invalid_zero(self):
        """Test that month 0 raises ValueError."""
        with self.assertRaises(ValueError):
            get_month_name(0)

    def test_month_name_invalid_thirteen(self):
        """Test that month 13 raises ValueError."""
        with self.assertRaises(ValueError):
            get_month_name(13)

    def test_month_name_negative(self):
        """Test that negative month raises ValueError."""
        with self.assertRaises(ValueError):
            get_month_name(-1)

    def test_month_name_high_number(self):
        """Test that very high month number raises ValueError."""
        with self.assertRaises(ValueError):
            get_month_name(100)


if __name__ == '__main__':
    unittest.main()
