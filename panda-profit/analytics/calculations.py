"""Calculation functions for profit analysis and reporting.

This module provides functions to calculate:
- Profit after all fees for individual sales
- ROI by product category
- Turnover rates (days to sell)
- Platform fee impact

All queries filter to CURRENT YEAR ONLY using the `year` column in the database.
"""

from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, dict_factory


def calculate_profit(sale):
    """Calculate profit for a single sale after all fees.

    Formula:
        profit = (sale_price + shipping_collected) - (cost_of_goods + shipping_cost + platform_fee + transaction_fee + promoted_fee)

    Args:
        sale (dict): Sale record with all required fields

    Returns:
        float: Profit amount (can be negative for losses)

    Raises:
        KeyError: If required fields are missing from sale dict
    """
    revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
    costs = (
        (sale.get('cost_of_goods', 0) or 0) +
        (sale.get('shipping_cost', 0) or 0) +
        (sale.get('platform_fee', 0) or 0) +
        (sale.get('transaction_fee', 0) or 0) +
        (sale.get('promoted_fee', 0) or 0)
    )
    return revenue - costs


def calculate_roi_by_category(start_date, end_date):
    """Calculate ROI (Return on Investment) grouped by category for current year.

    Query filters to current year only using: WHERE year = ?

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        list: List of dicts with keys:
            - category (str): Product category
            - cost (float): Total cost of goods sold
            - profit (float): Total profit after fees
            - roi_pct (float): ROI percentage (profit/cost*100), or 0 if cost=0
        Sorted by roi_pct descending
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    current_year = datetime.now().year

    c.execute('''
        SELECT
            category,
            SUM(cost_of_goods) as total_cost,
            SUM(
                COALESCE(sale_price, 0) +
                COALESCE(shipping_collected, 0) -
                COALESCE(cost_of_goods, 0) -
                COALESCE(shipping_cost, 0) -
                COALESCE(platform_fee, 0) -
                COALESCE(transaction_fee, 0) -
                COALESCE(promoted_fee, 0)
            ) as total_profit
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND year = ? AND category IS NOT NULL
        GROUP BY category
        ORDER BY total_profit DESC
    ''', (start_date, end_date, current_year))

    results = c.fetchall()
    conn.close()

    # Calculate ROI percentage for each category
    roi_results = []
    for row in results:
        category = row['category']
        cost = row['total_cost'] or 0
        profit = row['total_profit'] or 0

        roi_pct = (profit / cost * 100) if cost > 0 else 0

        roi_results.append({
            'category': category,
            'cost': cost,
            'profit': profit,
            'roi_pct': roi_pct,
        })

    # Sort by ROI descending
    roi_results.sort(key=lambda x: x['roi_pct'], reverse=True)

    return roi_results


def calculate_turnover_rate(category, start_date, end_date):
    """Calculate average days from listing to sold (turnover rate) for a category in current year.

    Query filters to current year only using: WHERE year = ?

    Args:
        category (str): Product category name
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        float: Average days to sell (e.g., 14.5), or 0 if no matching sales

    Note:
        Only includes sales where both listed_date and sold_date are present
        and days_to_sell is calculated.
    """
    conn = get_connection()
    c = conn.cursor()

    current_year = datetime.now().year

    c.execute('''
        SELECT AVG(days_to_sell) as avg_days
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND category = ? AND year = ? AND days_to_sell IS NOT NULL
    ''', (start_date, end_date, category, current_year))

    result = c.fetchone()
    conn.close()

    avg_days = result[0] if result and result[0] is not None else 0
    return float(avg_days)


def calculate_platform_impact(platform, start_date, end_date):
    """Calculate fee impact and profitability by platform for current year.

    Query filters to current year only using: WHERE year = ?

    Args:
        platform (str): Platform name (e.g., 'eBay', 'Poshmark')
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        dict: Platform impact metrics:
            - platform (str): Platform name
            - sales_count (int): Number of sales on this platform
            - total_revenue (float): Total sale price + shipping collected
            - total_fees (float): Sum of all fees (platform_fee + transaction_fee + promoted_fee)
            - total_cost (float): Total cost of goods
            - net_profit (float): Revenue - fees - cost
            - fee_percentage (float): Fees as % of revenue (0 if revenue=0)

    Returns:
        dict: Empty dict if no sales found for the platform in the date range
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    current_year = datetime.now().year

    c.execute('''
        SELECT
            platform,
            COUNT(id) as sales_count,
            SUM(COALESCE(sale_price, 0) + COALESCE(shipping_collected, 0)) as total_revenue,
            SUM(COALESCE(platform_fee, 0) + COALESCE(transaction_fee, 0) + COALESCE(promoted_fee, 0)) as total_fees,
            SUM(COALESCE(cost_of_goods, 0)) as total_cost
        FROM sales
        WHERE sold_date BETWEEN ? AND ? AND platform = ? AND year = ?
        GROUP BY platform
    ''', (start_date, end_date, platform, current_year))

    result = c.fetchone()
    conn.close()

    if not result:
        return {}

    sales_count = result['sales_count'] or 0
    total_revenue = result['total_revenue'] or 0
    total_fees = result['total_fees'] or 0
    total_cost = result['total_cost'] or 0
    net_profit = total_revenue - total_fees - total_cost

    # Calculate fee percentage
    fee_pct = (total_fees / total_revenue * 100) if total_revenue > 0 else 0

    return {
        'platform': platform,
        'sales_count': sales_count,
        'total_revenue': total_revenue,
        'total_fees': total_fees,
        'total_cost': total_cost,
        'net_profit': net_profit,
        'fee_percentage': fee_pct,
    }
