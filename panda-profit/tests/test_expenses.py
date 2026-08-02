import pytest
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_connection, init_db, get_or_create_expense_categories,
    add_expense_category, get_expense_categories, archive_expenses_for_year
)

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to temporary database."""
    import database
    test_db_path = str(tmp_path / 'test_expenses.db')

    # Remove existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Patch DB_PATH
    monkeypatch.setattr(database, 'DB_PATH', test_db_path)
    monkeypatch.setattr('database.DB_PATH', test_db_path)

    init_db()

    yield test_db_path

    # Cleanup: close all connections and remove file
    try:
        conn = get_connection()
        conn.close()
    except:
        pass

    # Give SQLite a moment to release file locks
    import time
    time.sleep(0.2)

    # Remove test database and WAL files
    for ext in ['', '-wal', '-shm']:
        db_file = test_db_path + ext
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except:
                pass

def test_seed_predefined_categories(test_db):
    """Test predefined categories are seeded."""
    get_or_create_expense_categories()
    categories = get_expense_categories()
    names = [c['name'] for c in categories]
    assert 'Storage' in names
    assert 'Business Subscriptions' in names
    assert len(categories) == 5

def test_add_custom_category(test_db):
    """Test adding custom category."""
    get_or_create_expense_categories()
    cat_id = add_expense_category('Custom Tools')
    categories = get_expense_categories()
    assert any(c['name'] == 'Custom Tools' and c['is_custom'] == 1 for c in categories)

def test_add_duplicate_category_raises(test_db):
    """Test duplicate category name raises error."""
    get_or_create_expense_categories()
    add_expense_category('MyCategory')
    with pytest.raises(ValueError):
        add_expense_category('MyCategory')

def test_archive_expenses_for_year(test_db):
    """Test prior-year expenses are archived."""
    get_or_create_expense_categories()
    conn = get_connection()
    c = conn.cursor()

    # Add current year and prior year expenses
    current_year = datetime.now().year
    prior_year = current_year - 1

    c.execute('INSERT INTO expenses (year, expense_date, category_id, amount, archived) VALUES (?, ?, ?, ?, ?)',
              (prior_year, f'{prior_year}-01-01', 1, 100.00, 0))
    c.execute('INSERT INTO expenses (year, expense_date, category_id, amount, archived) VALUES (?, ?, ?, ?, ?)',
              (current_year, f'{current_year}-01-01', 1, 200.00, 0))
    conn.commit()
    conn.close()

    # Archive prior year
    count = archive_expenses_for_year(current_year)
    assert count == 1

    # Verify prior year archived, current year not
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT archived FROM expenses WHERE year=?', (prior_year,))
    assert c.fetchone()[0] == 1
    c.execute('SELECT archived FROM expenses WHERE year=?', (current_year,))
    assert c.fetchone()[0] == 0
    conn.close()

def test_archive_expenses_does_not_archive_current_year(test_db):
    """Test archive does not mark current year as archived."""
    get_or_create_expense_categories()
    conn = get_connection()
    c = conn.cursor()

    current_year = datetime.now().year
    c.execute('INSERT INTO expenses (year, expense_date, category_id, amount, archived) VALUES (?, ?, ?, ?, ?)',
              (current_year, f'{current_year}-08-01', 1, 50.00, 0))
    conn.commit()
    conn.close()

    archive_expenses_for_year(current_year)

    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT archived FROM expenses WHERE year=?', (current_year,))
    assert c.fetchone()[0] == 0
    conn.close()
