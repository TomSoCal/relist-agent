import pytest
from PyQt5.QtWidgets import QApplication, QTableWidget
from ui.expenses_tab import ExpensesTab
import database as db
from database import init_db, get_or_create_expense_categories, add_expense
from datetime import datetime

@pytest.fixture(scope='module')
def qapp():
    """Provide QApplication for all tests."""
    return QApplication.instance() or QApplication([])

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to temporary database."""
    test_db_path = str(tmp_path / 'test_expenses_ui.db')
    monkeypatch.setattr('database.DB_PATH', test_db_path)
    init_db()
    yield
    import os
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_expenses_tab_loads(qapp, test_db):
    """Test ExpensesTab initializes and loads."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Test', '', '')

    tab = ExpensesTab()
    tab.load_expenses()

    assert tab.table.rowCount() > 0
    assert tab.table.columnCount() == 9

def test_expenses_tab_summary_stats(qapp, test_db):
    """Test summary stats display correct totals."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', '', '', '')
    add_expense(current_year, f'{current_year}-08-02', 1, 30.00, '', '', '', '')

    tab = ExpensesTab()
    tab.load_expenses()

    # Stats should show totals (verify via labels)
    assert '80' in tab.total_label.text()

def test_expense_history_tab_loads(qapp, test_db):
    """Test ExpenseHistoryTab loads archived expenses."""
    from ui.expense_history_tab import ExpenseHistoryTab

    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1

    # Seed a prior-year expense directly; add_expense() enforces current-year-only
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO expenses (year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path, archived)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)''',
              (prior_year, f'{prior_year}-08-01', 1, 100.00, '', 'Prior', '', ''))
    exp_id = c.lastrowid
    conn.commit()

    # Archive the prior-year expense
    c.execute('UPDATE expenses SET archived=1 WHERE id=?', (exp_id,))
    conn.commit()
    conn.close()

    tab = ExpenseHistoryTab()
    tab.load_history()

    assert tab.table.rowCount() > 0

def test_expense_history_search(qapp, test_db):
    """Test expense history search by description."""
    from ui.expense_history_tab import ExpenseHistoryTab

    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1

    # Seed a prior-year expense directly; add_expense() enforces current-year-only
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO expenses (year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path, archived)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)''',
              (prior_year, f'{prior_year}-08-01', 1, 100.00, '', 'Special Widgets', '', ''))
    exp_id = c.lastrowid
    conn.commit()

    # Archive the prior-year expense
    c.execute('UPDATE expenses SET archived=1 WHERE id=?', (exp_id,))
    conn.commit()
    conn.close()

    tab = ExpenseHistoryTab()
    tab.load_history()
    tab.search_input.setText('Widgets')
    tab.search_input.textChanged.emit('Widgets')

    assert tab.table.rowCount() == 1
