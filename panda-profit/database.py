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
            other_fee REAL DEFAULT 0,
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

    # Add is_custom column if it doesn't exist
    c.execute("PRAGMA table_info(expense_categories)")
    columns = [column[1] for column in c.fetchall()]
    if 'is_custom' not in columns:
        c.execute('ALTER TABLE expense_categories ADD COLUMN is_custom INTEGER DEFAULT 0')
        print("[+] Added 'is_custom' column to expense_categories table")

    # Insert predefined expense categories (only if table is empty, for fresh installs)
    c.execute('SELECT COUNT(*) FROM expense_categories')
    if c.fetchone()[0] == 0:
        default_categories = [
            ('Storage', 'supplies', 0),
            ('Business Subscriptions', 'subscriptions', 0),
            ('Home Office', 'supplies', 0),
            ('Shipping Supplies', 'supplies', 0),
            ('Misc Expense', 'other', 0),
        ]
        for name, category_type, is_custom in default_categories:
            c.execute('''
                INSERT INTO expense_categories (name, category_type, is_custom)
                VALUES (?, ?, ?)
            ''', (name, category_type, is_custom))

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
            invoice_number TEXT DEFAULT '',
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            receipt_path TEXT DEFAULT '',
            archived INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        )
    ''')

    # Add missing columns to expenses table if they don't exist
    c.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in c.fetchall()]
    if 'invoice_number' not in columns:
        c.execute('ALTER TABLE expenses ADD COLUMN invoice_number TEXT DEFAULT \'\'')
        print("[+] Added 'invoice_number' column to expenses table")
    if 'archived' not in columns:
        c.execute('ALTER TABLE expenses ADD COLUMN archived INTEGER DEFAULT 0')
        print("[+] Added 'archived' column to expenses table")
    if 'notes' not in columns:
        c.execute('ALTER TABLE expenses ADD COLUMN notes TEXT DEFAULT \'\'')
        print("[+] Added 'notes' column to expenses table")

    c.execute('CREATE INDEX IF NOT EXISTS idx_expenses_archived ON expenses(archived, year)')

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

    # Add other_fee column to sales if it doesn't exist
    c.execute("PRAGMA table_info(sales)")
    columns = [column[1] for column in c.fetchall()]
    if 'other_fee' not in columns:
        c.execute('ALTER TABLE sales ADD COLUMN other_fee REAL DEFAULT 0')

    # Add inventory_id column to sales if it doesn't exist (tracks original inventory item)
    c.execute("PRAGMA table_info(sales)")
    columns = [column[1] for column in c.fetchall()]
    if 'inventory_id' not in columns:
        c.execute('ALTER TABLE sales ADD COLUMN inventory_id INTEGER')

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

    # Add archived column if it doesn't exist
    c.execute("PRAGMA table_info(inventory)")
    columns = [row[1] for row in c.fetchall()]
    if 'archived' not in columns:
        c.execute("""
            ALTER TABLE inventory ADD COLUMN archived INTEGER DEFAULT 0
        """)
        # Create index for fast filtering
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_archived ON inventory(archived)
        """)
        print("[+] Added 'archived' column to inventory table")

    conn.commit()
    conn.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def get_dict_connection():
    """Connection whose rows come back as dicts. Caller must close it.

    Always resolves DB_PATH at call time -- never cache the returned
    connection at module level or it will bind to a stale database.
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    return conn

# Inventory operations
def add_inventory(listed_date, item_title='', units=0, sku='', bin='', store='', category='', cost=0.0, notes='', brand='', xp=0, created_at=None):
    conn = get_connection()
    c = conn.cursor()
    if created_at is None:
        created_at = datetime.now().isoformat()
    c.execute('''
        INSERT INTO inventory (listed_date, item_title, units, sku, bin, store, category, cost, notes, brand, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (listed_date, item_title, units, sku, bin, store, category, cost, notes, brand, created_at))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def restore_inventory_from_sale(sale):
    """
    Restore a sale back to inventory. If the sale has an inventory_id,
    restore it to the original item (increase units). Otherwise, create a new item.
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    if sale['inventory_id']:
        # Restore to original inventory item
        c.execute('''SELECT * FROM inventory WHERE id = ?''', (sale['inventory_id'],))
        original_item = c.fetchone()

        if original_item:
            # Item still exists - add units back to it
            new_units = original_item['units'] + sale['units']
            new_cost_total = (original_item['cost'] * original_item['units']) + (sale['cost_of_goods'])
            new_cost = new_cost_total / new_units if new_units > 0 else 0

            c.execute('''UPDATE inventory
                         SET units = ?, cost = ?, notes = ?
                         WHERE id = ?''',
                      (new_units, new_cost,
                       f"Returned from sale on {sale['sold_date']} (Reason: Mistake or Customer Return)",
                       sale['inventory_id']))
            conn.commit()
            result_id = sale['inventory_id']
        else:
            # Original item was deleted - create new one with the same ID
            # Note: We can't reuse the same ID (auto-increment), so we'll create a new one
            # but the notes will indicate it's a restored item from sale
            c.execute('''INSERT INTO inventory
                         (listed_date, item_title, units, sku, bin, store, category, cost, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (sale['listed_date'] or datetime.now().strftime("%m/%d/%Y"),
                       sale['item_title'], sale['units'], sale['sku'], sale['bin'],
                       sale['store'], sale['category'],
                       sale['cost_of_goods'] / sale['units'] if sale['units'] > 0 else 0,
                       f"Restored from sale (Original ID: {sale['inventory_id']}) - Sold on {sale['sold_date']}"))
            conn.commit()
            result_id = c.lastrowid
    else:
        # No inventory_id - create a new item (legacy behavior)
        c.execute('''INSERT INTO inventory
                     (listed_date, item_title, units, sku, bin, store, category, cost, notes)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (sale['listed_date'] or datetime.now().strftime("%m/%d/%Y"),
                   sale['item_title'], sale['units'], sale['sku'], sale['bin'],
                   sale['store'], sale['category'],
                   sale['cost_of_goods'] / sale['units'] if sale['units'] > 0 else 0,
                   f"Returned from sale on {sale['sold_date']} (Reason: Mistake or Customer Return)"))
        conn.commit()
        result_id = c.lastrowid

    conn.close()
    return result_id

def merge_inventory(listed_date, item_title, units, sku, bin, store, category, cost, notes):
    """Add item to inventory or update existing item if title+SKU match"""
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    # Check if item with same title and SKU exists
    c.execute('''SELECT id, units, cost FROM inventory
                 WHERE item_title = ? AND sku = ?''',
              (item_title, sku or ''))
    existing = c.fetchone()

    if existing:
        # Update existing item: add units and average the cost
        existing_units = existing['units']
        existing_cost = existing['cost'] or 0
        new_total_units = existing_units + units

        # Calculate weighted average cost
        if new_total_units > 0:
            avg_cost = ((existing_cost * existing_units) + (cost * units)) / new_total_units
        else:
            avg_cost = cost

        # Update the existing item
        c.execute('''UPDATE inventory
                     SET units = ?, cost = ?, notes = ?
                     WHERE id = ?''',
                  (new_total_units, avg_cost, notes, existing['id']))
        conn.commit()
        item_id = existing['id']
    else:
        # Create new item
        c.execute('''INSERT INTO inventory (listed_date, item_title, units, sku, bin, store, category, cost, notes)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (listed_date, item_title, units, sku, bin, store, category, cost, notes))
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
def add_expense_legacy(expense_date, category_id, amount, description='', receipt_path='', year=None):
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

def get_expenses_by_date_range_legacy(start_date, end_date, year=None):
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

def delete_expense_legacy(expense_id):
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

def get_total_expenses_by_category_legacy(start_date, end_date, year=None):
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

def get_or_create_expense_categories():
    """Seed predefined expense categories if table is empty."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM expense_categories')
    if c.fetchone()[0] == 0:
        categories = [
            ('Storage', 'supplies', 0),
            ('Business Subscriptions', 'subscriptions', 0),
            ('Home Office', 'supplies', 0),
            ('Shipping Supplies', 'supplies', 0),
            ('Misc Expense', 'other', 0),
        ]
        for name, category_type, is_custom in categories:
            c.execute('INSERT INTO expense_categories (name, category_type, is_custom) VALUES (?, ?, ?)',
                      (name, category_type, is_custom))
        conn.commit()
    conn.close()

def add_expense_category(name, category_type=None):
    """Add expense category. Return category_id or raise on duplicate.

    Args:
        name: Category name
        category_type: Optional category type. If None, marks as custom (is_custom=1).
                      If provided, marks as predefined (is_custom=0).
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # If category_type is provided, this is the old API (predefined category)
        # If not provided, this is the new API (custom category)
        if category_type is None:
            is_custom = 1
            category_type = 'custom'
        else:
            is_custom = 0

        c.execute('INSERT INTO expense_categories (name, category_type, is_custom) VALUES (?, ?, ?)',
                  (name.strip(), category_type, is_custom))
        conn.commit()
        category_id = c.lastrowid
        conn.close()
        return category_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Category '{name}' already exists")

def get_expense_categories():
    """Return all categories (predefined + custom), sorted by name."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, is_custom FROM expense_categories ORDER BY name')
    categories = [{'id': row[0], 'name': row[1], 'is_custom': row[2]} for row in c.fetchall()]
    conn.close()
    return categories

def archive_expenses_for_year(year):
    """Mark expenses with archived=0 and year < given_year as archived=1. Return count."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE expenses SET archived=1 WHERE archived=0 AND year < ? AND amount IS NOT NULL',
              (year,))
    conn.commit()
    count = c.rowcount
    conn.close()
    return count

def check_and_archive_year_transition():
    """Detect year boundary, auto-archive prior year expenses."""
    current_year = datetime.now().year
    archive_expenses_for_year(current_year)

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

def update_mileage_trip(trip_id, trip_date=None, miles=None, odometer_start=None, odometer_end=None, purpose=None, stores_visited=None, notes=None):
    """Update a mileage trip. Only allows updates to current year trips (write protection).

    Args:
        trip_id: ID of the mileage trip to update
        trip_date: Date of trip (YYYY-MM-DD format)
        miles: Miles driven
        odometer_start: Starting odometer reading
        odometer_end: Ending odometer reading
        purpose: Trip purpose
        stores_visited: Stores visited
        notes: Trip notes

    Returns:
        Number of rows updated (0 if trip doesn't exist or is from past year, 1 if success)
    """
    conn = get_connection()
    c = conn.cursor()
    current_year = datetime.now().year

    # Build update query only for provided fields
    updates = []
    values = []

    if trip_date is not None:
        updates.append("trip_date = ?")
        values.append(trip_date)
    if miles is not None:
        updates.append("miles = ?")
        values.append(miles)
    if odometer_start is not None:
        updates.append("odometer_start = ?")
        values.append(odometer_start)
    if odometer_end is not None:
        updates.append("odometer_end = ?")
        values.append(odometer_end)
    if purpose is not None:
        updates.append("purpose = ?")
        values.append(purpose)
    if stores_visited is not None:
        updates.append("stores_visited = ?")
        values.append(stores_visited)
    if notes is not None:
        updates.append("notes = ?")
        values.append(notes)

    if not updates:
        conn.close()
        return 0

    updates.append("updated_at = CURRENT_TIMESTAMP")
    query = f"UPDATE mileage SET {', '.join(updates)} WHERE id = ? AND year = ?"
    values.extend([trip_id, current_year])

    c.execute(query, values)
    conn.commit()
    rows_updated = c.rowcount
    conn.close()
    return rows_updated

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


# Archive operations
def archive_sold_inventory_for_year(year):
    """
    Archive all inventory from the given year where units = 0 (completely sold).
    Called at year boundary. Never deletes data.

    Args:
        year (int): The year to archive (e.g., 2026)
    """
    conn = get_connection()
    c = conn.cursor()
    query = """
    UPDATE inventory
    SET archived = 1
    WHERE
        strftime('%Y', created_at) = ?
        AND units = 0
    """
    c.execute(query, (str(year),))
    conn.commit()
    conn.close()


def get_archived_inventory(year=None, search_query=None):
    """
    Fetch archived inventory items with sales history metadata.

    Args:
        year (int, optional): Filter by year created. Default: all years.
        search_query (str, optional): Filter by SKU, title, category, or brand.

    Returns:
        List of dicts with fields:
        - id, sku, item_title, category, brand, cost, created_at
        - last_sold_date, units_sold_total, revenue_total
    """
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()

    query = """
    SELECT
        i.id, i.sku, i.item_title, i.category, i.brand, i.cost, i.created_at,
        MAX(s.sold_date) as last_sold_date,
        SUM(s.units) as units_sold_total,
        SUM(s.sale_price * s.units + COALESCE(s.shipping_collected, 0)) as revenue_total
    FROM inventory i
    LEFT JOIN sales s ON i.sku = s.sku
    WHERE i.archived = 1
    """

    params = []

    if year:
        query += " AND strftime('%Y', i.created_at) = ?"
        params.append(str(year))

    if search_query:
        query += " AND (i.sku LIKE ? OR i.item_title LIKE ? OR i.category LIKE ? OR i.brand LIKE ?)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " GROUP BY i.id ORDER BY last_sold_date DESC NULLS LAST"

    rows = c.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def copy_archived_to_active(archived_id, new_sku, copy_details=True):
    """
    Copy archived inventory to active inventory with new SKU.

    Args:
        archived_id (int): ID of archived inventory item.
        new_sku (str): New SKU for restocked item.
        copy_details (bool): If True, copy title, category, brand, cost.

    Returns:
        int: ID of new inventory item.

    Raises:
        ValueError: If new_sku already exists in active inventory.
    """
    conn = get_connection()
    c = conn.cursor()

    # Check for duplicate SKU
    existing = c.execute(
        "SELECT id FROM inventory WHERE sku = ? AND archived = 0",
        (new_sku,)
    ).fetchone()

    if existing:
        conn.close()
        raise ValueError(f"SKU '{new_sku}' already exists in active inventory")

    archived = get_inventory_by_id(archived_id)

    if copy_details:
        new_item = {
            'sku': new_sku,
            'item_title': archived['item_title'],
            'category': archived['category'],
            'brand': archived.get('brand', ''),
            'cost': archived['cost'],
            'units': 1,
            'listed_date': datetime.today().isoformat(),
            'store': archived.get('store', ''),
            'bin': archived.get('bin', ''),
            'notes': f"Restocked from SKU {archived['sku']}",
            'xp': 0
        }
    else:
        new_item = {
            'sku': new_sku,
            'units': 1,
            'listed_date': datetime.today().isoformat()
        }

    conn.close()
    return add_inventory(**new_item)


def check_and_archive_year_transition():
    """
    On app startup, check if year has changed.
    If new year detected, archive sold inventory from prior year.
    Returns True if archival happened, False otherwise.
    """
    current_year = datetime.now().year
    last_year_recorded = int(get_setting('last_app_year') or current_year - 1)

    if current_year > last_year_recorded:
        # Year boundary crossed; archive prior year's sold inventory
        print(f"[*] Year transition detected: {last_year_recorded} -> {current_year}")
        archive_sold_inventory_for_year(last_year_recorded)
        set_setting('last_app_year', str(current_year))
        print(f"[+] Archived sold inventory from {last_year_recorded}")
        return True

    return False

def add_expense(year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path):
    """Insert expense. Validate category exists and year is current."""
    conn = get_connection()
    c = conn.cursor()

    # Validate category exists
    c.execute('SELECT id FROM expense_categories WHERE id=?', (category_id,))
    if not c.fetchone():
        conn.close()
        raise ValueError(f"Category {category_id} not found")

    # Validate year is current
    if year != datetime.now().year:
        conn.close()
        raise ValueError(f"Can only add expenses for current year")

    c.execute('''
        INSERT INTO expenses (year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (year, expense_date, category_id, amount, invoice_number or '', description, notes, receipt_path or ''))
    conn.commit()
    expense_id = c.lastrowid
    conn.close()
    return expense_id

def get_expenses(year=None, archived=0):
    """Fetch expenses by year and archive status, ordered by date DESC."""
    if year is None:
        year = datetime.now().year

    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.year=? AND e.archived=?
        ORDER BY e.expense_date DESC
    ''', (year, archived))

    rows = c.fetchall()
    conn.close()

    return [
        {
            'id': row[0],
            'year': row[1],
            'expense_date': row[2],
            'category_id': row[3],
            'category_name': row[4],
            'amount': row[5],
            'invoice_number': row[6],
            'description': row[7],
            'notes': row[8],
            'receipt_path': row[9],
            'archived': row[10]
        }
        for row in rows
    ]

def get_expense_by_id(expense_id):
    """Fetch single expense by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.id=?
    ''', (expense_id,))

    row = c.fetchone()
    conn.close()
    if not row:
        return None

    return {
        'id': row[0],
        'year': row[1],
        'expense_date': row[2],
        'category_id': row[3],
        'category_name': row[4],
        'amount': row[5],
        'invoice_number': row[6],
        'description': row[7],
        'notes': row[8],
        'receipt_path': row[9],
        'archived': row[10]
    }

def update_expense(expense_id, expense_date, category_id, amount, invoice_number, description, notes, receipt_path):
    """Update expense. Only allow if current year."""
    conn = get_connection()
    c = conn.cursor()

    # Get expense year
    c.execute('SELECT year FROM expenses WHERE id=?', (expense_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Expense {expense_id} not found")

    exp_year = row[0]
    if exp_year != datetime.now().year:
        conn.close()
        raise ValueError(f"Can only edit expenses from current year")

    c.execute('''
        UPDATE expenses
        SET expense_date=?, category_id=?, amount=?, invoice_number=?, description=?, notes=?, receipt_path=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (expense_date, category_id, amount, invoice_number or '', description, notes, receipt_path or '', expense_id))
    conn.commit()
    rowcount = c.rowcount
    conn.close()
    return rowcount

def delete_expense(expense_id):
    """Delete expense. Only allow if current year."""
    conn = get_connection()
    c = conn.cursor()

    # Get expense year
    c.execute('SELECT year FROM expenses WHERE id=?', (expense_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return 0

    exp_year = row[0]
    if exp_year != datetime.now().year:
        conn.close()
        raise ValueError(f"Can only delete expenses from current year")

    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()
    rowcount = c.rowcount
    conn.close()
    return rowcount

def get_archived_expenses(year, search_query=None):
    """Search archived expenses by any field (case-insensitive, partial match)."""
    conn = get_connection()
    c = conn.cursor()

    query = '''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.year=? AND e.archived=1
    '''
    params = [year]

    if search_query:
        search_term = f'%{search_query.lower()}%'
        query += '''
            AND (
                CAST(e.id AS TEXT) LIKE ?
                OR DATE(e.expense_date) LIKE ?
                OR LOWER(ec.name) LIKE ?
                OR CAST(e.amount AS TEXT) LIKE ?
                OR LOWER(e.invoice_number) LIKE ?
                OR LOWER(e.description) LIKE ?
                OR LOWER(e.notes) LIKE ?
            )
        '''
        params.extend([search_term] * 7)

    query += ' ORDER BY e.expense_date DESC'
    c.execute(query, params)

    rows = c.fetchall()
    conn.close()

    return [
        {
            'id': row[0],
            'year': row[1],
            'expense_date': row[2],
            'category_id': row[3],
            'category_name': row[4],
            'amount': row[5],
            'invoice_number': row[6],
            'description': row[7],
            'notes': row[8],
            'receipt_path': row[9],
            'archived': row[10]
        }
        for row in rows
    ]

def get_expense_totals(year=None):
    """Return (month_total, year_total, month_count, year_count) for current month and year."""
    if year is None:
        year = datetime.now().year

    current_month = datetime.now().month
    conn = get_connection()
    c = conn.cursor()

    # Month total
    c.execute('''
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
        WHERE year=? AND CAST(strftime('%m', expense_date) AS INTEGER)=? AND archived=0
    ''', (year, current_month))
    month_total, month_count = c.fetchone()

    # Year total
    c.execute('''
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
        WHERE year=? AND archived=0
    ''', (year,))
    year_total, year_count = c.fetchone()

    conn.close()
    return float(month_total), float(year_total), int(month_count), int(year_count)

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
