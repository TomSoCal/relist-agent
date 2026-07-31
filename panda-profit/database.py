import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'panda_profit.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Brands table
    c.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inventory table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listed_date TEXT NOT NULL,
            item_title TEXT NOT NULL,
            units INTEGER NOT NULL,
            sku TEXT,
            bin TEXT,
            store TEXT,
            category TEXT,
            brand TEXT,
            cost REAL,
            notes TEXT,
            xp INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sales table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            days_to_sell INTEGER,
            platform TEXT,
            sold_date TEXT NOT NULL,
            listed_date TEXT,
            item_title TEXT NOT NULL,
            units INTEGER NOT NULL,
            bin TEXT,
            sku TEXT,
            store TEXT,
            category TEXT,
            sale_price REAL,
            shipping_collected REAL DEFAULT 0,
            cost_of_goods REAL,
            shipping_cost REAL DEFAULT 0,
            platform_fee REAL DEFAULT 0,
            promoted_fee REAL DEFAULT 0,
            transaction_fee REAL DEFAULT 0,
            sales_tax_collected REAL DEFAULT 0,
            total_fees REAL DEFAULT 0,
            profit_loss REAL DEFAULT 0,
            refund REAL DEFAULT 0,
            total_income REAL DEFAULT 0,
            total_platform_expenses REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Settings table for eBay API credentials
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Expense Categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category_type TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default expense categories
    default_categories = [
        ('Packaging Materials', 'supplies'),
        ('Shipping Costs', 'shipping'),
        ('Office Supplies', 'supplies'),
        ('Equipment', 'equipment'),
        ('Software Subscriptions', 'subscriptions'),
        ('Advertising', 'marketing'),
        ('Professional Services', 'services'),
        ('Rent', 'facility'),
        ('Utilities', 'facility'),
        ('Insurance', 'insurance'),
        ('Vehicle Expenses', 'vehicle'),
        ('Travel', 'travel'),
        ('Meals & Entertainment', 'meals'),
        ('Training & Development', 'education'),
        ('Miscellaneous', 'other'),
    ]

    for name, category_type in default_categories:
        c.execute('''
            INSERT OR IGNORE INTO expense_categories (name, category_type)
            VALUES (?, ?)
        ''', (name, category_type))

    # Platform Fees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS platform_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL UNIQUE,
            listing_fee REAL DEFAULT 0,
            transaction_fee_pct REAL DEFAULT 0,
            shipping_fee_pct REAL DEFAULT 0,
            payment_fee_pct REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default platform fees
    default_platforms = [
        ('eBay', 0.30, 12.9, 0, 2.2, None),
        ('Poshmark', 0, 20, 0, 0, 'Commission-based'),
        ('Facebook Marketplace', 0, 0, 0, 0, 'No fees'),
        ('Mercari', 0, 10, 0, 0, 'Commission-based'),
        ('Whatnot', 0, 8, 0, 0, 'Commission-based'),
    ]

    for platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes in default_platforms:
        c.execute('''
            INSERT OR IGNORE INTO platform_fees (platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes))

    # Expenses table (for logging actual expenses)
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            expense_date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT DEFAULT '',
            receipt_path TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        )
    ''')

    # Mileage table (for tracking business trips and sourcing miles)
    c.execute('''
        CREATE TABLE IF NOT EXISTS mileage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            trip_date TEXT NOT NULL,
            odometer_start INTEGER DEFAULT 0,
            odometer_end INTEGER DEFAULT 0,
            miles REAL NOT NULL,
            purpose TEXT DEFAULT 'sourcing',
            stores_visited TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add brand column to inventory if it doesn't exist
    c.execute("PRAGMA table_info(inventory)")
    columns = [column[1] for column in c.fetchall()]
    if 'brand' not in columns:
        c.execute('ALTER TABLE inventory ADD COLUMN brand TEXT')

    # Inventory Images table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inventory_id) REFERENCES inventory (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Inventory operations
def add_inventory(listed_date, item_title, units, sku, bin, store, category, cost, notes, xp=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO inventory (listed_date, item_title, units, sku, bin, store, category, cost, notes, xp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (listed_date, item_title, units, sku, bin, store, category, cost, notes, xp))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def get_all_inventory():
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM inventory ORDER BY listed_date DESC')
    items = c.fetchall()
    conn.close()
    return items

def get_inventory_by_id(item_id):
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
    item = c.fetchone()
    conn.close()
    return item

def update_inventory(item_id, **kwargs):
    conn = get_connection()
    c = conn.cursor()
    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
    values = list(kwargs.values()) + [item_id]
    c.execute(f'UPDATE inventory SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

def delete_inventory(item_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

# Inventory Images operations
def add_inventory_image(inventory_id, image_url, display_order=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO inventory_images (inventory_id, image_url, display_order)
        VALUES (?, ?, ?)
    ''', (inventory_id, image_url, display_order))
    conn.commit()
    image_id = c.lastrowid
    conn.close()
    return image_id

def get_inventory_images(inventory_id):
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM inventory_images WHERE inventory_id = ? ORDER BY display_order', (inventory_id,))
    images = c.fetchall()
    conn.close()
    return images

def delete_inventory_image(image_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM inventory_images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

def delete_all_inventory_images(inventory_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM inventory_images WHERE inventory_id = ?', (inventory_id,))
    conn.commit()
    conn.close()

# Sales operations
def add_sale(**kwargs):
    conn = get_connection()
    c = conn.cursor()
    cols = ', '.join(kwargs.keys())
    placeholders = ', '.join(['?' for _ in kwargs])
    c.execute(f'INSERT INTO sales ({cols}) VALUES ({placeholders})', list(kwargs.values()))
    conn.commit()
    sale_id = c.lastrowid
    conn.close()
    return sale_id

def get_all_sales():
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM sales ORDER BY sold_date DESC')
    sales = c.fetchall()
    conn.close()
    return sales

def get_sales_by_date_range(start_date, end_date):
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM sales WHERE sold_date BETWEEN ? AND ? ORDER BY sold_date DESC', (start_date, end_date))
    sales = c.fetchall()
    conn.close()
    return sales

def update_sale(sale_id, **kwargs):
    conn = get_connection()
    c = conn.cursor()
    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
    values = list(kwargs.values()) + [sale_id]
    c.execute(f'UPDATE sales SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

def delete_sale(sale_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
    conn.commit()
    conn.close()

# Settings operations
def set_setting(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Expense Categories operations
def add_expense_category(name, category_type):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO expense_categories (name, category_type)
        VALUES (?, ?)
    ''', (name, category_type))
    conn.commit()
    category_id = c.lastrowid
    conn.close()
    return category_id

def get_all_expense_categories():
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM expense_categories ORDER BY name ASC')
    categories = c.fetchall()
    conn.close()
    return categories

def delete_expense_category(category_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM expense_categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()

# Platform Fees operations
def add_platform_fee(platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO platform_fees (platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (platform, listing_fee, transaction_fee_pct, shipping_fee_pct, payment_fee_pct, notes))
    conn.commit()
    fee_id = c.lastrowid
    conn.close()
    return fee_id

def get_platform_fee(platform):
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM platform_fees WHERE platform = ?', (platform,))
    fee = c.fetchone()
    conn.close()
    return fee

def get_all_platform_fees():
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM platform_fees ORDER BY platform COLLATE NOCASE ASC')
    fees = c.fetchall()
    conn.close()
    return fees

def update_platform_fee(platform, **kwargs):
    conn = get_connection()
    c = conn.cursor()
    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
    values = list(kwargs.values()) + [platform]
    c.execute(f'UPDATE platform_fees SET {set_clause} WHERE platform = ?', values)
    conn.commit()
    conn.close()

def delete_platform_fee(fee_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM platform_fees WHERE id = ?', (fee_id,))
    conn.commit()
    conn.close()

# Expenses operations
def add_expense(expense_date, category_id, amount, description='', receipt_path='', year=None):
    """Add a new expense entry. Year defaults to current system year if not provided.

    Args:
        expense_date: Date of the expense (YYYY-MM-DD format)
        category_id: ID of the expense category
        amount: Expense amount
        description: Optional description
        receipt_path: Optional path to receipt file
        year: Optional year for the expense. If provided and != current year, raises ValueError (write protection)

    Returns:
        expense_id: ID of the newly created expense

    Raises:
        ValueError: If year is provided and != current year (only current year can be edited)
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year

    # If year is provided, validate it matches current year (write protection)
    if year is not None and year != current_year:
        conn.close()
        raise ValueError(f"Can only add expenses for the current year ({current_year}). Cannot add expenses for year {year}.")

    # Use current year if not provided
    if year is None:
        year = current_year

    c.execute('''
        INSERT INTO expenses (year, expense_date, category_id, amount, description, receipt_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (year, expense_date, category_id, amount, description, receipt_path))
    conn.commit()
    expense_id = c.lastrowid
    conn.close()
    return expense_id

def get_expenses_by_date_range(start_date, end_date, year=None):
    """Get expenses within a date range. Defaults to current calendar year if year not specified.

    Args:
        start_date: Start date for the range (YYYY-MM-DD format)
        end_date: End date for the range (YYYY-MM-DD format)
        year: Optional year filter. If None, defaults to current year. Can be any year (read-only access to past years).

    Returns:
        List of expense records ordered by expense_date DESC
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # If year not specified, use current year
    if year is None:
        year = datetime.now().year

    c.execute('''
        SELECT * FROM expenses
        WHERE expense_date BETWEEN ? AND ? AND year = ?
        ORDER BY expense_date DESC
    ''', (start_date, end_date, year))
    expenses = c.fetchall()
    conn.close()
    return expenses

def delete_expense(expense_id):
    """Delete an expense entry. Only allows deletion of current year expenses (write protection).

    Args:
        expense_id: ID of the expense to delete

    Returns:
        Number of rows deleted (0 if expense doesn't exist or is from past year, 1 if success)
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year
    # Only delete if expense is from current year (prevents deleting past years)
    c.execute('DELETE FROM expenses WHERE id = ? AND year = ?', (expense_id, current_year))
    conn.commit()
    rows_deleted = c.rowcount
    conn.close()
    return rows_deleted

def get_total_expenses_by_category(start_date, end_date, year=None):
    """Get total expenses grouped by category for a date range. Defaults to current calendar year if year not specified.

    Args:
        start_date: Start date for the range (YYYY-MM-DD format)
        end_date: End date for the range (YYYY-MM-DD format)
        year: Optional year filter. If None, defaults to current year. Can be any year (read-only access to past years).

    Returns:
        List of category totals ordered by total_amount DESC
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # If year not specified, use current year
    if year is None:
        year = datetime.now().year

    c.execute('''
        SELECT
            ec.id,
            ec.name,
            ec.category_type,
            SUM(e.amount) as total_amount,
            COUNT(e.id) as count
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.expense_date BETWEEN ? AND ? AND e.year = ?
        GROUP BY ec.id
        ORDER BY total_amount DESC
    ''', (start_date, end_date, year))
    results = c.fetchall()
    conn.close()
    return results

# Mileage operations
def add_mileage_trip(trip_date, miles, purpose='sourcing', stores_visited='', notes='', odometer_start=0, odometer_end=0, year=None):
    """Add a new mileage trip. Year defaults to current system year if not provided.

    Args:
        trip_date: Date of the trip (YYYY-MM-DD format)
        miles: Miles traveled
        purpose: Purpose of the trip (default: 'sourcing')
        stores_visited: Comma-separated list of stores visited (default: '')
        notes: Optional notes about the trip (default: '')
        odometer_start: Starting odometer reading (default: 0)
        odometer_end: Ending odometer reading (default: 0)
        year: Optional year for the trip. If provided and != current year, raises ValueError (write protection)

    Returns:
        mileage_id: ID of the newly created mileage trip

    Raises:
        ValueError: If year is provided and != current year (only current year can be edited)
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year

    # If year is provided, validate it matches current year (write protection)
    if year is not None and year != current_year:
        conn.close()
        raise ValueError(f"Can only add mileage for the current year ({current_year}). Cannot add mileage for year {year}.")

    # Use current year if not provided
    if year is None:
        year = current_year

    c.execute('''
        INSERT INTO mileage (year, trip_date, odometer_start, odometer_end, miles, purpose, stores_visited, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (year, trip_date, odometer_start, odometer_end, miles, purpose, stores_visited, notes))
    conn.commit()
    mileage_id = c.lastrowid
    conn.close()
    return mileage_id

def get_mileage_by_date_range(start_date, end_date, year=None):
    """Get mileage trips within a date range. Defaults to current calendar year if year not specified.

    Args:
        start_date: Start date for the range (YYYY-MM-DD format)
        end_date: End date for the range (YYYY-MM-DD format)
        year: Optional year filter. If None, defaults to current year. Can be any year (read-only access to past years).

    Returns:
        List of mileage trip records ordered by trip_date DESC
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # If year not specified, use current year
    if year is None:
        year = datetime.now().year

    c.execute('''
        SELECT * FROM mileage
        WHERE trip_date BETWEEN ? AND ? AND year = ?
        ORDER BY trip_date DESC
    ''', (start_date, end_date, year))
    trips = c.fetchall()
    conn.close()
    return trips

def delete_mileage_trip(trip_id):
    """Delete a mileage trip. Only allows deletion of current year trips (write protection).

    Args:
        trip_id: ID of the mileage trip to delete

    Returns:
        Number of rows deleted (0 if trip doesn't exist or is from past year, 1 if success)
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year
    # Only delete if trip is from current year (prevents deleting past years)
    c.execute('DELETE FROM mileage WHERE id = ? AND year = ?', (trip_id, current_year))
    conn.commit()
    rows_deleted = c.rowcount
    conn.close()
    return rows_deleted

def get_total_mileage_for_period(start_date, end_date, year=None):
    """Get total miles and trip count for a date range. Defaults to current calendar year if year not specified.

    Args:
        start_date: Start date for the range (YYYY-MM-DD format)
        end_date: End date for the range (YYYY-MM-DD format)
        year: Optional year filter. If None, defaults to current year. Can be any year (read-only access to past years).

    Returns:
        Dict with 'total_miles' and 'trip_count' keys
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # If year not specified, use current year
    if year is None:
        year = datetime.now().year

    c.execute('''
        SELECT
            SUM(miles) as total_miles,
            COUNT(id) as trip_count
        FROM mileage
        WHERE trip_date BETWEEN ? AND ? AND year = ?
    ''', (start_date, end_date, year))
    result = c.fetchone()
    conn.close()

    # Handle null results (no trips in range)
    if result and result['total_miles'] is not None:
        return {
            'total_miles': result['total_miles'],
            'trip_count': result['trip_count']
        }
    else:
        return {
            'total_miles': 0,
            'trip_count': 0
        }

# Brands operations
def add_brand(name):
    """Add a new brand. Raises IntegrityError if name already exists."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO brands (name)
        VALUES (?)
    ''', (name,))
    conn.commit()
    brand_id = c.lastrowid
    conn.close()
    return brand_id

def get_all_brands():
    """Get all brands ordered by name."""
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute('SELECT * FROM brands ORDER BY name COLLATE NOCASE ASC')
    brands = c.fetchall()
    conn.close()
    return brands

def delete_brand(brand_id):
    """Delete a brand by id."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM brands WHERE id = ?', (brand_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
