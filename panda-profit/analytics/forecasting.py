"""Forecasting and predictive analytics for sales and inventory.

This module provides functions to forecast:
- Future sales units based on moving averages
- Future revenue based on historical pricing
- Inventory turnover rates by category
- Seasonal sales patterns by month

All queries filter to CURRENT YEAR ONLY using the `year` column in the database.
"""

from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, dict_factory


def forecast_sales_units(period_days=30):
    """Forecast sales units for a future period using moving average.

    Queries last 90 days of current year sales to calculate average daily units sold,
    then multiplies by the forecast period.

    Formula:
        forecast = (sum of units in last 90 days) / 90 * period_days

    Args:
        period_days (int): Number of days to forecast (default: 30)

    Returns:
        int: Predicted number of units to sell (rounded to nearest integer)

    Note:
        Returns 0 if no sales data available in the last 90 days.
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    current_year = datetime.now().year

    # Calculate date range for last 90 days
    today = datetime.now().date()
    start_date = (today - timedelta(days=90)).isoformat()
    end_date = today.isoformat()

    c.execute('''
        SELECT SUM(units) as total_units
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND year = ?
    ''', (start_date, end_date, current_year))

    result = c.fetchone()
    conn.close()

    total_units = result['total_units'] if result and result['total_units'] is not None else 0

    # Calculate average daily units and forecast
    if total_units == 0:
        return 0

    avg_daily_units = total_units / 90.0
    forecast = int(round(avg_daily_units * period_days))

    return forecast


def forecast_revenue(period_days=30):
    """Forecast revenue for a future period.

    Queries last 90 days of current year sales to calculate average revenue per sale,
    then multiplies by forecasted units for the period.

    Formula:
        forecast_revenue = (avg revenue per sale) * forecast_sales_units(period_days)
        where avg revenue per sale = sum(sale_price + shipping_collected) / sale count

    Args:
        period_days (int): Number of days to forecast (default: 30)

    Returns:
        float: Predicted revenue amount (2 decimal places)

    Note:
        Returns 0.0 if no sales data available or average revenue is 0.
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    current_year = datetime.now().year

    # Calculate date range for last 90 days
    today = datetime.now().date()
    start_date = (today - timedelta(days=90)).isoformat()
    end_date = today.isoformat()

    c.execute('''
        SELECT
            COUNT(id) as sale_count,
            SUM(COALESCE(sale_price, 0) + COALESCE(shipping_collected, 0)) as total_revenue
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND year = ?
    ''', (start_date, end_date, current_year))

    result = c.fetchone()
    conn.close()

    sale_count = result['sale_count'] if result and result['sale_count'] is not None else 0
    total_revenue = result['total_revenue'] if result and result['total_revenue'] is not None else 0

    if sale_count == 0 or total_revenue == 0:
        return 0.0

    avg_revenue_per_sale = total_revenue / sale_count

    # Get forecast units to multiply by average revenue per sale
    forecast_units = forecast_sales_units(period_days)

    forecast_revenue_value = avg_revenue_per_sale * forecast_units

    return round(forecast_revenue_value, 2)


def forecast_inventory_turnover(category):
    """Forecast inventory turnover rate (days to sell) for a category.

    Queries last 180 days of current year sales for a specific category,
    calculates average days from listing to sold.

    Formula:
        turnover_days = AVG(sold_date - listed_date) for category in current year

    Args:
        category (str): Product category name

    Returns:
        float: Average days to sell for the category (e.g., 14.5)

    Note:
        Returns 0.0 if no matching sales found or category is None.
        Only includes sales where days_to_sell is calculated.
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year

    # Calculate date range for last 180 days
    today = datetime.now().date()
    start_date = (today - timedelta(days=180)).isoformat()
    end_date = today.isoformat()

    c.execute('''
        SELECT AVG(days_to_sell) as avg_days
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND category = ? AND year = ? AND days_to_sell IS NOT NULL
    ''', (start_date, end_date, category, current_year))

    result = c.fetchone()
    conn.close()

    avg_days = result[0] if result and result[0] is not None else 0.0

    return float(avg_days)


def forecast_seasonal_impact(month):
    """Analyze historical sales patterns for a specific month.

    Queries all sales from the same calendar month across all years in current year data,
    groups by month, and returns aggregate statistics.

    Args:
        month (int): Month number from 1 (January) to 12 (December)

    Returns:
        dict: Seasonal impact metrics for the month:
            - month (int): Month number (1-12)
            - month_name (str): Name of the month (e.g., "January")
            - avg_sales (float): Average number of sales in this month
            - avg_revenue (float): Average revenue in this month
            - best_category (str): Top performing category for this month
            - best_category_revenue (float): Revenue of top category

    Returns:
        dict: Empty dict if no sales data available for the month or month is invalid

    Raises:
        ValueError: If month is not between 1 and 12
    """
    import calendar

    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")

    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    current_year = datetime.now().year

    # Query all sales for this month in current year
    c.execute('''
        SELECT
            COUNT(id) as sale_count,
            SUM(COALESCE(sale_price, 0) + COALESCE(shipping_collected, 0)) as total_revenue
        FROM sales
        WHERE month = ? AND year = ?
    ''', (month, current_year))

    result = c.fetchone()

    sale_count = result['sale_count'] if result and result['sale_count'] is not None else 0
    total_revenue = result['total_revenue'] if result and result['total_revenue'] is not None else 0

    # If no sales for this month, return empty dict
    if sale_count == 0:
        conn.close()
        return {}

    avg_sales = sale_count
    avg_revenue = round(total_revenue, 2)

    # Find best performing category for this month
    c.execute('''
        SELECT
            category,
            SUM(COALESCE(sale_price, 0) + COALESCE(shipping_collected, 0)) as category_revenue
        FROM sales
        WHERE month = ? AND year = ? AND category IS NOT NULL
        GROUP BY category
        ORDER BY category_revenue DESC
        LIMIT 1
    ''', (month, current_year))

    best_category_result = c.fetchone()
    conn.close()

    best_category = best_category_result['category'] if best_category_result else None
    best_category_revenue = round(best_category_result['category_revenue'], 2) if best_category_result else 0.0

    month_name = calendar.month_name[month]

    return {
        'month': month,
        'month_name': month_name,
        'avg_sales': avg_sales,
        'avg_revenue': avg_revenue,
        'best_category': best_category,
        'best_category_revenue': best_category_revenue,
    }
