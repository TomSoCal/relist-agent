#!/usr/bin/env python3
"""
Sample data generator for Panda Profit database.
Adds realistic inventory, sales, expenses, and mileage data for July 2026.
"""

import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

import database as db

def get_category_id_by_name(category_name):
    """Get expense category ID by name."""
    categories = db.get_all_expense_categories()
    for cat in categories:
        if cat['name'] == category_name:
            return cat['id']
    return None

def main():
    # Initialize database
    db.init_db()

    print("=" * 70)
    print("PANDA PROFIT - SAMPLE DATA GENERATOR")
    print("=" * 70)

    # === INVENTORY ITEMS ===
    print("\n[1/5] Adding Inventory Items...")
    inventory_items = [
        {
            'listed_date': '2026-07-01',
            'item_title': 'Vintage Sony Walkman CD Player',
            'units': 1,
            'sku': 'SONY-WM-2001',
            'bin': '1A-2',
            'store': 'Goodwill',
            'category': 'Electronics',
            'cost': 12.50,
            'notes': 'Working condition, includes headphones'
        },
        {
            'listed_date': '2026-07-02',
            'item_title': 'Lot of 5 Harry Potter Books - Hardcover',
            'units': 5,
            'sku': 'POTTER-LOT-001',
            'bin': '3B-5',
            'store': 'Estate Sale',
            'category': 'Books',
            'cost': 8.00,
            'notes': 'Complete series, first editions'
        },
        {
            'listed_date': '2026-07-03',
            'item_title': 'Coach Leather Handbag - Brown',
            'units': 1,
            'sku': 'COACH-LTH-BR',
            'bin': '2C-1',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'cost': 25.00,
            'notes': 'Authentic leather, minor wear'
        },
        {
            'listed_date': '2026-07-05',
            'item_title': 'Nintendo 64 Console - Gray',
            'units': 1,
            'sku': 'N64-GRAY-001',
            'bin': '1A-7',
            'store': 'Goodwill',
            'category': 'Electronics',
            'cost': 35.00,
            'notes': 'Working, no cables'
        },
        {
            'listed_date': '2026-07-06',
            'item_title': 'Funko Pop Figures - Marvel Set',
            'units': 8,
            'sku': 'FUNKO-MAR-001',
            'bin': '4A-3',
            'store': 'Estate Sale',
            'category': 'Collectibles',
            'cost': 5.00,
            'notes': 'Mix of Iron Man, Captain America, etc.'
        },
        {
            'listed_date': '2026-07-07',
            'item_title': 'Vintage Levi\'s 501 Jeans - Size 32',
            'units': 1,
            'sku': 'LEVIS-501-32',
            'bin': '2D-2',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'cost': 15.00,
            'notes': '1990s, excellent condition'
        },
        {
            'listed_date': '2026-07-08',
            'item_title': 'Nikon D3200 DSLR Camera - Black',
            'units': 1,
            'sku': 'NIKON-D3200',
            'bin': '1B-4',
            'store': 'Goodwill',
            'category': 'Electronics',
            'cost': 45.00,
            'notes': 'No lens, some shutter wear'
        },
        {
            'listed_date': '2026-07-10',
            'item_title': 'Apple iPod Touch - 4th Gen, 32GB',
            'units': 1,
            'sku': 'IPOD-4G-32',
            'bin': '1C-6',
            'store': 'Estate Sale',
            'category': 'Electronics',
            'cost': 18.00,
            'notes': 'Good battery, screen protector included'
        },
        {
            'listed_date': '2026-07-12',
            'item_title': 'Spiderman #1 Comic - CGC Graded',
            'units': 1,
            'sku': 'SPIDEY-001-CGC',
            'bin': '4B-1',
            'store': 'Pawn Shop',
            'category': 'Collectibles',
            'cost': 50.00,
            'notes': 'CGC 7.0 grade, 1963 reprint'
        },
        {
            'listed_date': '2026-07-14',
            'item_title': 'Samsung Smart TV - 43 inch, 4K',
            'units': 1,
            'sku': 'SAM-TV-43-4K',
            'bin': '1D-1',
            'store': 'Goodwill',
            'category': 'Electronics',
            'cost': 120.00,
            'notes': 'Working, no remote'
        }
    ]

    inventory_ids = []
    for item in inventory_items:
        item_id = db.add_inventory(
            listed_date=item['listed_date'],
            item_title=item['item_title'],
            units=item['units'],
            sku=item['sku'],
            bin=item['bin'],
            store=item['store'],
            category=item['category'],
            cost=item['cost'],
            notes=item['notes']
        )
        inventory_ids.append(item_id)

    print(f"  ✓ Added {len(inventory_ids)} inventory items")

    # === SALES TRANSACTIONS ===
    print("\n[2/5] Adding Sales Transactions...")
    sales_data = [
        # eBay sales
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 3,
            'platform': 'eBay',
            'sold_date': '2026-07-04',
            'listed_date': '2026-07-01',
            'item_title': 'Vintage Sony Walkman CD Player',
            'units': 1,
            'bin': '1A-2',
            'sku': 'SONY-WM-2001',
            'store': 'Goodwill',
            'category': 'Electronics',
            'sale_price': 45.99,
            'shipping_collected': 8.00,
            'cost_of_goods': 12.50,
            'shipping_cost': 5.50,
            'platform_fee': 6.58,  # 12.9% of sale price
            'transaction_fee': 1.01,  # 2.2% of sale price
        },
        # Poshmark sales
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 5,
            'platform': 'Poshmark',
            'sold_date': '2026-07-08',
            'listed_date': '2026-07-03',
            'item_title': 'Coach Leather Handbag - Brown',
            'units': 1,
            'bin': '2C-1',
            'sku': 'COACH-LTH-BR',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'sale_price': 85.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 25.00,
            'shipping_cost': 0.00,
            'platform_fee': 17.00,  # 20% commission
            'transaction_fee': 0.00,
        },
        # Mercari sales
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 2,
            'platform': 'Mercari',
            'sold_date': '2026-07-10',
            'listed_date': '2026-07-08',
            'item_title': 'Apple iPod Touch - 4th Gen, 32GB',
            'units': 1,
            'bin': '1C-6',
            'sku': 'IPOD-4G-32',
            'store': 'Estate Sale',
            'category': 'Electronics',
            'sale_price': 52.00,
            'shipping_collected': 5.00,
            'cost_of_goods': 18.00,
            'shipping_cost': 4.50,
            'platform_fee': 5.20,  # 10% commission
            'transaction_fee': 0.00,
        },
        # eBay sales - book lot
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 4,
            'platform': 'eBay',
            'sold_date': '2026-07-06',
            'listed_date': '2026-07-02',
            'item_title': 'Lot of 5 Harry Potter Books - Hardcover',
            'units': 5,
            'bin': '3B-5',
            'sku': 'POTTER-LOT-001',
            'store': 'Estate Sale',
            'category': 'Books',
            'sale_price': 78.50,
            'shipping_collected': 12.00,
            'cost_of_goods': 8.00,
            'shipping_cost': 10.00,
            'platform_fee': 11.26,  # 12.9%
            'transaction_fee': 1.73,  # 2.2%
        },
        # Facebook Marketplace (no fees)
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 1,
            'platform': 'Facebook',
            'sold_date': '2026-07-11',
            'listed_date': '2026-07-10',
            'item_title': 'Vintage Levi\'s 501 Jeans - Size 32',
            'units': 1,
            'bin': '2D-2',
            'sku': 'LEVIS-501-32',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'sale_price': 42.00,
            'shipping_collected': 6.00,
            'cost_of_goods': 15.00,
            'shipping_cost': 5.00,
            'platform_fee': 0.00,
            'transaction_fee': 0.00,
        },
        # Mercari - camera
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 6,
            'platform': 'Mercari',
            'sold_date': '2026-07-14',
            'listed_date': '2026-07-08',
            'item_title': 'Nikon D3200 DSLR Camera - Black',
            'units': 1,
            'bin': '1B-4',
            'sku': 'NIKON-D3200',
            'store': 'Goodwill',
            'category': 'Electronics',
            'sale_price': 125.00,
            'shipping_collected': 15.00,
            'cost_of_goods': 45.00,
            'shipping_cost': 12.00,
            'platform_fee': 12.50,  # 10% commission
            'transaction_fee': 0.00,
        },
        # Whatnot - collectibles
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 3,
            'platform': 'Whatnot',
            'sold_date': '2026-07-09',
            'listed_date': '2026-07-06',
            'item_title': 'Funko Pop Figures - Marvel Set',
            'units': 8,
            'bin': '4A-3',
            'sku': 'FUNKO-MAR-001',
            'store': 'Estate Sale',
            'category': 'Collectibles',
            'sale_price': 65.00,
            'shipping_collected': 8.00,
            'cost_of_goods': 5.00,
            'shipping_cost': 6.50,
            'platform_fee': 5.20,  # 8% commission
            'transaction_fee': 0.00,
        },
        # eBay - Nintendo 64
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 8,
            'platform': 'eBay',
            'sold_date': '2026-07-13',
            'listed_date': '2026-07-05',
            'item_title': 'Nintendo 64 Console - Gray',
            'units': 1,
            'bin': '1A-7',
            'sku': 'N64-GRAY-001',
            'store': 'Goodwill',
            'category': 'Electronics',
            'sale_price': 155.00,
            'shipping_collected': 12.00,
            'cost_of_goods': 35.00,
            'shipping_cost': 8.50,
            'platform_fee': 22.29,  # 12.9%
            'transaction_fee': 3.41,  # 2.2%
        },
        # Poshmark - jeans
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 9,
            'platform': 'Poshmark',
            'sold_date': '2026-07-15',
            'listed_date': '2026-07-06',
            'item_title': 'Vintage Levi\'s 501 Jeans - Size 32',
            'units': 1,
            'bin': '2D-2',
            'sku': 'LEVIS-501-32',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'sale_price': 58.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 15.00,
            'shipping_cost': 0.00,
            'platform_fee': 11.60,  # 20% commission
            'transaction_fee': 0.00,
        },
        # eBay - comic book
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 4,
            'platform': 'eBay',
            'sold_date': '2026-07-18',
            'listed_date': '2026-07-14',
            'item_title': 'Spiderman #1 Comic - CGC Graded',
            'units': 1,
            'bin': '4B-1',
            'sku': 'SPIDEY-001-CGC',
            'store': 'Pawn Shop',
            'category': 'Collectibles',
            'sale_price': 185.00,
            'shipping_collected': 20.00,
            'cost_of_goods': 50.00,
            'shipping_cost': 15.00,
            'platform_fee': 26.67,  # 12.9%
            'transaction_fee': 4.07,  # 2.2%
        },
        # Mercari - more items
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 7,
            'platform': 'Mercari',
            'sold_date': '2026-07-19',
            'listed_date': '2026-07-12',
            'item_title': 'Samsung Smart TV - 43 inch, 4K',
            'units': 1,
            'bin': '1D-1',
            'sku': 'SAM-TV-43-4K',
            'store': 'Goodwill',
            'category': 'Electronics',
            'sale_price': 285.00,
            'shipping_collected': 35.00,
            'cost_of_goods': 120.00,
            'shipping_cost': 28.00,
            'platform_fee': 28.50,  # 10% commission
            'transaction_fee': 0.00,
        },
        # Facebook - electronics
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 2,
            'platform': 'Facebook',
            'sold_date': '2026-07-20',
            'listed_date': '2026-07-18',
            'item_title': 'Sony CD Player Deck - Vintage',
            'units': 1,
            'bin': None,
            'sku': 'SONY-CD-DECK',
            'store': 'Estate Sale',
            'category': 'Electronics',
            'sale_price': 35.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 8.00,
            'shipping_cost': 0.00,
            'platform_fee': 0.00,
            'transaction_fee': 0.00,
        },
        # Whatnot - collectible figures
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 5,
            'platform': 'Whatnot',
            'sold_date': '2026-07-21',
            'listed_date': '2026-07-16',
            'item_title': 'Vintage Action Figures Lot',
            'units': 12,
            'bin': None,
            'sku': 'ACTION-FIG-LOT',
            'store': 'Goodwill',
            'category': 'Collectibles',
            'sale_price': 95.00,
            'shipping_collected': 10.00,
            'cost_of_goods': 18.00,
            'shipping_cost': 8.00,
            'platform_fee': 7.60,  # 8% commission
            'transaction_fee': 0.00,
        },
        # Poshmark - designer bag
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 11,
            'platform': 'Poshmark',
            'sold_date': '2026-07-24',
            'listed_date': '2026-07-13',
            'item_title': 'Designer Handbag - Michael Kors',
            'units': 1,
            'bin': None,
            'sku': 'MK-BAG-001',
            'store': 'Pawn Shop',
            'category': 'Fashion',
            'sale_price': 120.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 32.00,
            'shipping_cost': 0.00,
            'platform_fee': 24.00,  # 20% commission
            'transaction_fee': 0.00,
        },
        # eBay - vintage tech
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 10,
            'platform': 'eBay',
            'sold_date': '2026-07-25',
            'listed_date': '2026-07-15',
            'item_title': 'Vintage Atari 2600 Console Bundle',
            'units': 1,
            'bin': None,
            'sku': 'ATARI-2600',
            'store': 'Estate Sale',
            'category': 'Electronics',
            'sale_price': 98.50,
            'shipping_collected': 12.00,
            'cost_of_goods': 22.00,
            'shipping_cost': 10.00,
            'platform_fee': 14.14,  # 12.9%
            'transaction_fee': 2.17,  # 2.2%
        },
        # Mercari - clothing bundle
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 4,
            'platform': 'Mercari',
            'sold_date': '2026-07-27',
            'listed_date': '2026-07-23',
            'item_title': 'Vintage Clothing Bundle - Jeans & Shirts',
            'units': 6,
            'bin': None,
            'sku': 'CLOTHING-BUNDLE',
            'store': 'Goodwill',
            'category': 'Fashion',
            'sale_price': 72.00,
            'shipping_collected': 8.00,
            'cost_of_goods': 12.00,
            'shipping_cost': 7.00,
            'platform_fee': 7.20,  # 10% commission
            'transaction_fee': 0.00,
        },
        # Facebook - free local pickup
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 1,
            'platform': 'Facebook',
            'sold_date': '2026-07-28',
            'listed_date': '2026-07-27',
            'item_title': 'VHS Player - Panasonic',
            'units': 1,
            'bin': None,
            'sku': 'VHS-PANASONIC',
            'store': 'Estate Sale',
            'category': 'Electronics',
            'sale_price': 18.00,
            'shipping_collected': 0.00,
            'cost_of_goods': 3.00,
            'shipping_cost': 0.00,
            'platform_fee': 0.00,
            'transaction_fee': 0.00,
        },
        # Whatnot - collectible cards
        {
            'year': 2026,
            'month': 7,
            'days_to_sell': 6,
            'platform': 'Whatnot',
            'sold_date': '2026-07-29',
            'listed_date': '2026-07-23',
            'item_title': 'Pokemon Trading Card Lot - 50 cards',
            'units': 50,
            'bin': None,
            'sku': 'POKEMON-CARDS-50',
            'store': 'Pawn Shop',
            'category': 'Collectibles',
            'sale_price': 145.00,
            'shipping_collected': 8.00,
            'cost_of_goods': 28.00,
            'shipping_cost': 6.00,
            'platform_fee': 11.60,  # 8% commission
            'transaction_fee': 0.00,
        },
    ]

    sales_ids = []
    for sale in sales_data:
        sale_id = db.add_sale(**sale)
        sales_ids.append(sale_id)

    print(f"  ✓ Added {len(sales_ids)} sales transactions")

    # === EXPENSES ===
    print("\n[3/5] Adding Expenses...")
    expenses_data = [
        ('2026-07-02', 'Packaging Materials', 35.50, 'Bubble wrap and box supplies'),
        ('2026-07-04', 'Shipping Costs', 12.75, 'Extra postage for oversized item'),
        ('2026-07-06', 'Office Supplies', 24.99, 'Printer ink and labels'),
        ('2026-07-08', 'Software Subscriptions', 14.99, 'Monthly Sellfy subscription'),
        ('2026-07-10', 'Packaging Materials', 45.00, 'Thermal printer labels'),
        ('2026-07-12', 'Vehicle Expenses', 52.00, 'Gas for sourcing trips'),
        ('2026-07-15', 'Office Supplies', 18.50, 'Shipping scale batteries'),
        ('2026-07-18', 'Equipment', 89.99, 'Tissue paper dispenser'),
        ('2026-07-20', 'Advertising', 50.00, 'eBay promoted listings'),
        ('2026-07-25', 'Shipping Costs', 28.45, 'Return shipping label'),
    ]

    expense_ids = []
    for expense_date, category_name, amount, description in expenses_data:
        category_id = get_category_id_by_name(category_name)
        if category_id:
            expense_id = db.add_expense_legacy(
                expense_date=expense_date,
                category_id=category_id,
                amount=amount,
                description=description,
                year=2026
            )
            expense_ids.append(expense_id)

    print(f"  ✓ Added {len(expense_ids)} expense entries")

    # === MILEAGE TRIPS ===
    print("\n[4/5] Adding Mileage Trips...")
    mileage_data = [
        ('2026-07-01', 28.5, 'sourcing', 'Goodwill', 'Found 3 items'),
        ('2026-07-05', 35.2, 'sourcing', 'Estate Sale, Pawn Shop', 'Attended estate sale, picked up camera'),
        ('2026-07-08', 22.0, 'sourcing', 'Salvation Army', 'Regular sourcing run'),
        ('2026-07-12', 41.5, 'sourcing', 'Goodwill, Thrift Store', 'Multi-store sourcing trip'),
        ('2026-07-15', 18.3, 'sourcing', 'Estate Sale', 'Estate sale in neighboring town'),
        ('2026-07-19', 33.0, 'sourcing', 'Pawn Shop, Flea Market', 'Found collectible items'),
        ('2026-07-23', 26.8, 'sourcing', 'Goodwill', 'Weekly sourcing visit'),
    ]

    mileage_ids = []
    for trip_date, miles, purpose, stores_visited, notes in mileage_data:
        mileage_id = db.add_mileage_trip(
            trip_date=trip_date,
            miles=miles,
            purpose=purpose,
            stores_visited=stores_visited,
            notes=notes,
            year=2026
        )
        mileage_ids.append(mileage_id)

    print(f"  ✓ Added {len(mileage_ids)} mileage trips")

    # === VERIFY DATA ===
    print("\n[5/5] Verifying Data...")

    conn = db.get_connection()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM inventory')
    inventory_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM sales')
    sales_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM expenses')
    expenses_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM mileage')
    mileage_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM platform_fees')
    platform_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM expense_categories')
    category_count = c.fetchone()[0]

    conn.close()

    # === SUMMARY ===
    print("\n" + "=" * 70)
    print("SAMPLE DATA SUMMARY")
    print("=" * 70)
    print(f"\nInventory Items:        {inventory_count:>3} items")
    print(f"Sales Transactions:     {sales_count:>3} sales")
    print(f"Expenses:               {expenses_count:>3} entries")
    print(f"Mileage Trips:          {mileage_count:>3} trips")
    print(f"Platforms (pre-loaded): {platform_count:>3} platforms")
    print(f"Expense Categories:     {category_count:>3} categories")
    print("\n" + "=" * 70)

    # Calculate sample totals
    total_sale_price = sum([s['sale_price'] for s in sales_data])
    total_cost = sum([s['cost_of_goods'] for s in sales_data])
    total_fees = sum([s['platform_fee'] + s['transaction_fee'] for s in sales_data])
    total_expenses = sum([e[2] for e in expenses_data])
    total_mileage = sum([m[1] for m in mileage_data])

    print(f"\nSales Analysis (July 2026):")
    print(f"  Total Sale Price:       ${total_sale_price:>8.2f}")
    print(f"  Total Cost of Goods:    ${total_cost:>8.2f}")
    print(f"  Total Platform Fees:    ${total_fees:>8.2f}")
    print(f"  Gross Profit:           ${(total_sale_price - total_cost - total_fees):>8.2f}")

    print(f"\nExpenses Analysis (July 2026):")
    print(f"  Total Expenses:         ${total_expenses:>8.2f}")

    print(f"\nMileage Analysis (July 2026):")
    print(f"  Total Miles:            {total_mileage:>8.1f} miles")
    print(f"  Total Trips:            {len(mileage_ids):>8} trips")

    print("\n✓ Database populated successfully!")
    print("=" * 70)

if __name__ == '__main__':
    main()
