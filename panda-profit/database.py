import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'panda_profit.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

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

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
