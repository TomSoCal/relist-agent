"""Reports module for generating PDF and CSV exports of sales data.

This module provides functions to generate various reports for sales data analysis:
- CSV exports of sales transactions
- PDF reports with summary and detailed breakdowns

All reports filter to the current calendar year using the `year` column in the database.
"""

import csv
import os
import sys
from datetime import datetime
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_sales_by_date_range, get_connection, dict_factory, SALE_YEAR_SQL


def _format_currency(value):
    """Format a value as currency.

    Args:
        value (float): Numeric value to format

    Returns:
        str: Formatted currency string (e.g., "$1,234.56")
    """
    if value is None:
        value = 0.0
    return f"${value:,.2f}"


def _get_sales_for_report(start_date, end_date, year=None):
    """Get sales for the specified date range, filtered by year.

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        year (int, optional): Year to filter by. Defaults to current year.

    Returns:
        list: List of sale dicts from database, sorted by sold_date DESC
    """
    if year is None:
        year = datetime.now().year

    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # sales.year is nullable and NULL for every UI-entered sale, so the year is
    # derived from sold_date (NOT NULL) instead. See database.SALE_YEAR_SQL.
    c.execute(f'''
        SELECT *, {SALE_YEAR_SQL} AS year FROM sales
        WHERE sold_date BETWEEN ? AND ? AND {SALE_YEAR_SQL} = ?
        ORDER BY sold_date DESC
    ''', (start_date, end_date, year))

    sales = c.fetchall()
    conn.close()
    return sales


def _calculate_summary_stats(sales):
    """Calculate summary statistics from sales list.

    Args:
        sales (list): List of sale dicts

    Returns:
        dict: Summary stats with keys:
            - total_sales_count (int): Number of sales
            - total_revenue (float): Sum of sale_price + shipping_collected
            - total_cost (float): Sum of cost_of_goods
            - total_fees (float): Sum of all fees (platform_fee + transaction_fee + promoted_fee)
            - total_profit (float): Revenue - Cost - Fees
    """
    if not sales:
        return {
            'total_sales_count': 0,
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'total_fees': 0.0,
            'total_profit': 0.0,
        }

    total_sales_count = len(sales)
    total_revenue = sum((s.get('sale_price', 0) or 0) + (s.get('shipping_collected', 0) or 0) for s in sales)
    total_cost = sum((s.get('cost_of_goods', 0) or 0) for s in sales)
    total_fees = sum(
        (s.get('platform_fee', 0) or 0) +
        (s.get('transaction_fee', 0) or 0) +
        (s.get('promoted_fee', 0) or 0)
        for s in sales
    )
    total_profit = total_revenue - total_cost - total_fees

    return {
        'total_sales_count': total_sales_count,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_fees': total_fees,
        'total_profit': total_profit,
    }


def generate_csv_report(start_date, end_date, filename=None, year=None):
    """Generate a CSV report of sales data for the specified date range.

    Exports all sales columns to CSV format. Filters to current year by default.

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        filename (str, optional): Path to write CSV file. If None, returns CSV string.
        year (int, optional): Year to filter by. Defaults to current year.

    Returns:
        str or filename: If filename provided, returns the filename.
                        If filename not provided, returns CSV string.
    """
    sales = _get_sales_for_report(start_date, end_date, year)

    # Define CSV columns
    fieldnames = [
        'id', 'year', 'month', 'days_to_sell', 'platform', 'sold_date', 'listed_date',
        'item_title', 'units', 'bin', 'sku', 'store', 'category', 'sale_price',
        'shipping_collected', 'cost_of_goods', 'shipping_cost', 'platform_fee',
        'promoted_fee', 'transaction_fee', 'sales_tax_collected', 'total_fees',
        'profit_loss', 'refund', 'total_income', 'total_platform_expenses'
    ]

    # Create CSV content
    if filename:
        # Write to file
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for sale in sales:
                # Only include columns that exist in fieldnames
                row = {k: sale.get(k, '') for k in fieldnames}
                writer.writerow(row)
        return filename
    else:
        # Return as string
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for sale in sales:
            row = {k: sale.get(k, '') for k in fieldnames}
            writer.writerow(row)
        return output.getvalue()


def generate_pdf_report(start_date, end_date, filename=None, year=None):
    """Generate a PDF report of sales data for the specified date range.

    Creates a formatted PDF with:
    - Title and date range
    - Summary table (Total Sales, Revenue, Cost, Fees, Net Profit)
    - Detail table (Date, Item, Platform, Price, Fees, Profit, Category) - limited to 100 rows

    Filters to current year by default.

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        filename (str, optional): Path to write PDF file. If None, uses default name.
        year (int, optional): Year to filter by. Defaults to current year.

    Returns:
        str: The filename of the generated PDF
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

    sales = _get_sales_for_report(start_date, end_date, year)
    stats = _calculate_summary_stats(sales)

    # Determine filename
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"sales_report_{timestamp}.pdf"

    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    title = Paragraph(f"Sales Report: {start_date} to {end_date}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    # Summary Table
    summary_heading = Paragraph("Summary", styles['Heading2'])
    elements.append(summary_heading)
    elements.append(Spacer(1, 0.1 * inch))

    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', str(stats['total_sales_count'])],
        ['Total Revenue', _format_currency(stats['total_revenue'])],
        ['Total Cost', _format_currency(stats['total_cost'])],
        ['Total Fees', _format_currency(stats['total_fees'])],
        ['Net Profit', _format_currency(stats['total_profit'])],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Detail Table
    detail_heading = Paragraph("Sales Details (Limited to 100 rows)", styles['Heading2'])
    elements.append(detail_heading)
    elements.append(Spacer(1, 0.1 * inch))

    # Prepare detail data - limit to 100 rows
    detail_data = [
        ['Date', 'Item', 'Platform', 'Price', 'Fees', 'Profit', 'Category']
    ]

    for sale in sales[:100]:
        revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
        fees = (
            (sale.get('platform_fee', 0) or 0) +
            (sale.get('transaction_fee', 0) or 0) +
            (sale.get('promoted_fee', 0) or 0)
        )
        profit = revenue - (sale.get('cost_of_goods', 0) or 0) - fees

        # Truncate item title if too long
        item_title = sale.get('item_title', '')[:40]
        if len(sale.get('item_title', '')) > 40:
            item_title += '...'

        detail_data.append([
            sale.get('sold_date', '')[:10],
            item_title,
            sale.get('platform', '')[:15],
            _format_currency(revenue),
            _format_currency(fees),
            _format_currency(profit),
            (sale.get('category', '') or '')[:15],
        ])

    # Create detail table with smaller column widths
    col_widths = [0.8 * inch, 2.0 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch]
    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(detail_table)

    # Build PDF
    doc.build(elements)
    return filename


if __name__ == '__main__':
    # Example usage
    from datetime import datetime, timedelta

    today = datetime.now().date()
    start = (today.replace(day=1)).isoformat()
    end = today.isoformat()

    print("Generating CSV report...")
    csv_file = generate_csv_report(start, end, 'sales_report.csv')
    print(f"CSV report generated: {csv_file}")

    print("Generating PDF report...")
    pdf_file = generate_pdf_report(start, end, 'sales_report.pdf')
    print(f"PDF report generated: {pdf_file}")
