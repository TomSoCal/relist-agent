"""Date and calendar utilities for analytics.

Provides functions to calculate time-based metrics useful for tracking
progress through months and years.
"""

from datetime import datetime, timedelta
import calendar


def get_days_elapsed_this_month() -> int:
    """Returns the current day of month (1-31).

    Returns:
        int: Day of month from 1 to 31.
    """
    return datetime.now().day


def get_days_left_this_month() -> int:
    """Returns the number of days remaining in the current month.

    Returns:
        int: Days remaining in month (0-30).
    """
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return days_in_month - today.day


def get_months_elapsed_this_year() -> int:
    """Returns the number of months elapsed this year (0-indexed).

    Returns:
        int: Months elapsed (0 for January, 1 for February, ..., 11 for December).
    """
    return datetime.now().month - 1


def get_months_left_this_year() -> int:
    """Returns the number of months left in the current year.

    Returns:
        int: Months remaining (0-11).
    """
    return 12 - datetime.now().month


def get_percent_year_elapsed() -> float:
    """Returns the percentage of the year that has elapsed.

    Returns:
        float: Percentage from 0.0 to 100.0.
    """
    today = datetime.now()
    year_start = datetime(today.year, 1, 1)
    year_end = datetime(today.year, 12, 31)

    total_days = (year_end - year_start).days + 1
    days_elapsed = (today - year_start).days + 1

    return (days_elapsed / total_days) * 100.0


def get_month_start_end() -> tuple:
    """Returns the start and end dates for the current month.

    Returns:
        tuple: (start_date, end_date) as datetime objects.
    """
    today = datetime.now()
    first_day = datetime(today.year, today.month, 1)

    last_day_num = calendar.monthrange(today.year, today.month)[1]
    last_day = datetime(today.year, today.month, last_day_num)

    return (first_day, last_day)


def get_year_start_end() -> tuple:
    """Returns the start and end dates for the current year.

    Returns:
        tuple: (start_date, end_date) as datetime objects.
    """
    today = datetime.now()
    start = datetime(today.year, 1, 1)
    end = datetime(today.year, 12, 31)
    return (start, end)


def get_last_30_days() -> tuple:
    """Returns the date range for the last 30 days.

    Returns:
        tuple: (start_date, end_date) as datetime objects, where end_date is today.
    """
    today = datetime.now()
    start = today - timedelta(days=30)
    return (start, today)


def get_month_name(month_num: int) -> str:
    """Returns the name of the month for a given month number.

    Args:
        month_num (int): Month number from 1 (January) to 12 (December).

    Returns:
        str: Name of the month, e.g., "January", "February", etc.

    Raises:
        ValueError: If month_num is not between 1 and 12.
    """
    if month_num < 1 or month_num > 12:
        raise ValueError(f"Month number must be between 1 and 12, got {month_num}")

    return calendar.month_name[month_num]
