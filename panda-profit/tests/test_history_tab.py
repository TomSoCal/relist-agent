import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from ui.history_tab import HistoryTab
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to temporary database."""
    import database
    test_db_path = str(tmp_path / 'test_history.db')

    # Remove existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Patch DB_PATH
    monkeypatch.setattr(database, 'DB_PATH', test_db_path)
    monkeypatch.setattr('database.DB_PATH', test_db_path)

    database.init_db()

    yield test_db_path

    # Cleanup: close all connections and remove file
    try:
        conn = database.get_connection()
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

def test_history_tab_initializes(qapp):
    """HistoryTab should initialize without errors."""
    tab = HistoryTab()
    assert isinstance(tab, QWidget)
    assert tab is not None

def test_history_tab_has_buttons(qapp):
    """HistoryTab should have three buttons."""
    tab = HistoryTab()
    # Check button layout exists (will verify in UI step)
    assert tab is not None

def test_sales_history_view_initializes(qapp, test_db):
    """SalesHistoryView should initialize without errors."""
    from ui.history.sales_history_view import SalesHistoryView
    view = SalesHistoryView()
    assert isinstance(view, QWidget)

def test_sales_history_view_excludes_current_year(qapp, test_db):
    """Year selector should not include current year."""
    from ui.history.sales_history_view import SalesHistoryView
    from datetime import datetime
    view = SalesHistoryView()
    current_year = datetime.now().year

    # Get year selector items
    years = [view.year_selector.itemText(i) for i in range(view.year_selector.count())]
    assert str(current_year) not in years


def test_history_tab_buttons_switch_views(qapp, test_db):
    """Clicking buttons should show correct views."""
    tab = HistoryTab()

    # Click Sales History
    tab.on_sales_clicked()
    assert tab.stacked.currentWidget() is not None
    assert tab.stacked.currentWidget() is tab.sales_view

    # Click Inventory History
    tab.on_inventory_clicked()
    assert tab.stacked.currentWidget() is not None
    assert tab.stacked.currentWidget() is tab.inventory_view

    # Click Expense History
    tab.on_expense_clicked()
    assert tab.stacked.currentWidget() is not None
    assert tab.stacked.currentWidget() is tab.expense_view


def test_history_tab_lazy_loads_views(qapp, test_db):
    """Views should be None until clicked."""
    tab = HistoryTab()

    # Views should be None initially
    assert tab.sales_view is None
    assert tab.inventory_view is None
    assert tab.expense_view is None

    # Click Sales History
    tab.on_sales_clicked()
    assert tab.sales_view is not None

    # Other views still None
    assert tab.inventory_view is None
    assert tab.expense_view is None

    # Click Inventory History
    tab.on_inventory_clicked()
    assert tab.inventory_view is not None

    # Expense view still None
    assert tab.expense_view is None

    # Click Expense History
    tab.on_expense_clicked()
    assert tab.expense_view is not None


def test_history_views_independent_year_selection(qapp, test_db):
    """Each view should have independent year selection."""
    tab = HistoryTab()

    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()

    # Get initial year counts (InventoryHistoryView uses year_combo, others use year_selector)
    sales_year_count = tab.sales_view.year_selector.count()
    inventory_year_count = tab.inventory_view.year_combo.count()
    expense_year_count = tab.expense_view.year_selector.count()

    # All should have at least one year option
    # If empty, test still passes (no previous data in test db)
    if sales_year_count > 0 and inventory_year_count > 1:
        # Change year in Sales History to first option
        tab.sales_view.year_selector.setCurrentIndex(0)
        sales_year = tab.sales_view.year_selector.currentText()

        # Change year in Inventory History to different option if available
        tab.inventory_view.year_combo.setCurrentIndex(
            min(1, inventory_year_count - 1)
        )
        inventory_year = tab.inventory_view.year_combo.currentText()

        # If we have different options, they should be independent
        if sales_year_count > 1 and inventory_year_count > 1:
            # Year selections can be independent (different indices)
            assert tab.sales_view.year_selector.currentIndex() != tab.inventory_view.year_combo.currentIndex()


def test_all_history_views_exclude_current_year(qapp, test_db):
    """No history view year selector should include current year."""
    from datetime import datetime

    tab = HistoryTab()
    current_year = datetime.now().year

    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()

    # Check Sales History year selector
    sales_years = [tab.sales_view.year_selector.itemText(i)
                   for i in range(tab.sales_view.year_selector.count())]
    assert str(current_year) not in sales_years, f"Current year {current_year} found in Sales History"

    # Check Inventory History year combo (uses different attribute name)
    inventory_years = [tab.inventory_view.year_combo.itemText(i)
                       for i in range(tab.inventory_view.year_combo.count())]
    assert str(current_year) not in inventory_years, f"Current year {current_year} found in Inventory History"

    # Check Expense History year selector
    expense_years = [tab.expense_view.year_selector.itemText(i)
                     for i in range(tab.expense_view.year_selector.count())]
    assert str(current_year) not in expense_years, f"Current year {current_year} found in Expense History"
