import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from ui.history_tab import HistoryTab
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CURRENT_YEAR = datetime.now().year
PRIOR_YEAR = CURRENT_YEAR - 1

@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _seed_prior_year_data(database):
    """Create one archived prior-year row of each kind the History tab reads.

    Without this the History views have empty year selectors and every
    assertion below is vacuously true.
    """
    # --- Prior-year sale -------------------------------------------------
    # `year` is deliberately NOT passed: this is exactly what the UI
    # AddSaleDialog does, and it is what left sales.year NULL and crashed
    # SalesHistoryView.load_years(). get_sales() must derive the year from
    # sold_date instead.
    sale_id = database.add_sale(
        sold_date=f'{PRIOR_YEAR}-06-15',
        item_title='Prior Year Widget',
        units=2,
        sku='HIST-SALE-1',
        sale_price=25.00,
        cost_of_goods=10.00,
        profit_loss=15.00,
    )
    # A current-year sale too, so "excludes current year" is a real filter.
    database.add_sale(
        sold_date=f'{CURRENT_YEAR}-01-10',
        item_title='Current Year Widget',
        units=1,
        sku='HIST-SALE-2',
        sale_price=30.00,
    )

    # --- Prior-year archived inventory -----------------------------------
    # units=0 (fully sold) is the precondition archive_sold_inventory_for_year
    # requires; created_at drives the year selector via strftime('%Y', ...).
    inventory_id = database.add_inventory(
        listed_date=f'{PRIOR_YEAR}-03-10',
        item_title='Prior Year Inventory Item',
        units=0,
        sku='HIST-SALE-1',
        category='Collectibles',
        brand='TestBrand',
        cost=10.00,
        created_at=f'{PRIOR_YEAR}-03-10 09:00:00',
    )
    database.archive_sold_inventory_for_year(PRIOR_YEAR)

    # --- Prior-year archived expense -------------------------------------
    # Inserted directly: add_expense() refuses non-current years by design
    # (year-based write protection), which is precisely the row we need.
    categories = database.get_expense_categories()
    assert categories, 'init_db should seed default expense categories'
    category_id = categories[0]['id']

    conn = database.get_connection()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO expenses
           (year, expense_date, category_id, amount, invoice_number,
            description, notes, receipt_path, archived)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
        (PRIOR_YEAR, f'{PRIOR_YEAR}-11-02', category_id, 42.50,
         'INV-2001', 'Prior year shipping supplies', 'seeded by test', '')
    )
    conn.commit()
    expense_id = c.lastrowid
    conn.close()

    return {
        'sale_id': sale_id,
        'inventory_id': inventory_id,
        'expense_id': expense_id,
        'category_id': category_id,
    }


@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to a temporary database seeded with prior-year history."""
    import database
    test_db_path = str(tmp_path / 'test_history.db')

    # Remove existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Patch DB_PATH
    monkeypatch.setattr(database, 'DB_PATH', test_db_path)
    monkeypatch.setattr('database.DB_PATH', test_db_path)

    database.init_db()
    _seed_prior_year_data(database)

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

def test_history_tab_initializes(qapp, test_db):
    """HistoryTab should initialize without errors."""
    tab = HistoryTab()
    assert isinstance(tab, QWidget)
    assert tab is not None

def test_history_tab_has_buttons(qapp, test_db):
    """HistoryTab should have three history buttons in the button bar."""
    from PyQt5.QtWidgets import QPushButton
    tab = HistoryTab()
    # Only check the first three buttons (the history tab buttons)
    # The SalesHistoryView has additional buttons like "View"
    all_buttons = [b.text() for b in tab.findChildren(QPushButton)]
    assert 'Sales History' in all_buttons
    assert 'Inventory History' in all_buttons
    assert 'Expense History' in all_buttons


def test_seed_creates_prior_year_sale_with_null_year_column(test_db):
    """Guard the regression: the seeded sale has a NULL year column on disk.

    If this ever stops being true the UI tests below stop exercising the
    NULL-year crash and quietly become weaker.
    """
    import database
    conn = database.get_connection()
    rows = conn.execute(
        'SELECT year FROM sales WHERE sku = ?', ('HIST-SALE-1',)
    ).fetchall()
    conn.close()
    assert rows, 'seeded sale missing'
    assert rows[0][0] is None, 'sales.year should be NULL for UI-style inserts'


def test_get_sales_derives_year_from_sold_date(test_db):
    """database.get_sales() must never return a None year."""
    import database

    all_sales = database.get_sales()
    assert len(all_sales) == 2
    assert all(s['year'] is not None for s in all_sales)
    assert {s['year'] for s in all_sales} == {PRIOR_YEAR, CURRENT_YEAR}

    prior = database.get_sales(year=PRIOR_YEAR)
    assert len(prior) == 1
    assert prior[0]['sku'] == 'HIST-SALE-1'
    assert prior[0]['year'] == PRIOR_YEAR


def test_get_sales_derives_year_from_us_format_date(test_db):
    """MM/DD/YYYY dates (what the UI dialogs write) must resolve too."""
    import database
    database.add_sale(
        sold_date=f'03/15/{PRIOR_YEAR}',
        item_title='US Format Sale',
        units=1,
        sku='HIST-SALE-US',
        sale_price=12.00,
    )
    prior = database.get_sales(year=PRIOR_YEAR)
    skus = {s['sku'] for s in prior}
    assert skus == {'HIST-SALE-1', 'HIST-SALE-US'}
    assert all(s['year'] == PRIOR_YEAR for s in prior)


def test_sales_history_view_initializes(qapp, test_db):
    """SalesHistoryView should initialize without errors."""
    from ui.history.sales_history_view import SalesHistoryView
    view = SalesHistoryView()
    assert isinstance(view, QWidget)

def test_sales_history_view_excludes_current_year(qapp, test_db):
    """Year selector should list the prior year and omit the current year."""
    from ui.history.sales_history_view import SalesHistoryView
    view = SalesHistoryView()

    # Get year selector items
    years = [view.year_selector.itemText(i) for i in range(view.year_selector.count())]
    assert years, 'year selector must not be empty -- seeding failed'
    assert str(PRIOR_YEAR) in years
    assert str(CURRENT_YEAR) not in years


def test_sales_history_view_populates_table_and_totals(qapp, test_db):
    """The seeded prior-year sale must render with correct totals."""
    from ui.history.sales_history_view import SalesHistoryView
    view = SalesHistoryView()

    assert view.table.rowCount() == 1
    assert view.table.item(0, 1).text() == 'Prior Year Widget'
    assert view.table.item(0, 2).text() == '2'          # units
    assert view.table.item(0, 3).text() == '$25.00'     # price
    assert view.table.item(0, 4).text() == '$50.00'     # 2 x 25.00
    assert view.year_total_label.text() == '$50.00'
    assert view.count_label.text() == '1'


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
    """Sales view loads by default, others lazy-load on click."""
    tab = HistoryTab()

    # Sales view should load by default
    assert tab.sales_view is not None
    # Others should be None until clicked
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


def test_inventory_history_view_shows_archived_item(qapp, test_db):
    """The seeded archived inventory item must be findable and searchable."""
    tab = HistoryTab()
    tab.on_inventory_clicked()
    view = tab.inventory_view

    # "All Years" placeholder plus exactly one real prior year
    years = [view.year_combo.itemText(i) for i in range(view.year_combo.count())]
    assert years == ['All Years', str(PRIOR_YEAR)]

    view.perform_search()
    assert view.results_table.rowCount() == 1
    assert view.results_table.item(0, 0).text() == 'HIST-SALE-1'
    assert view.results_table.item(0, 1).text() == 'Prior Year Inventory Item'

    # Search narrows to a real hit...
    view.search_input.setText('TestBrand')
    assert view.results_table.rowCount() == 1

    # ...and a miss really returns nothing.
    view.search_input.setText('no-such-item-xyz')
    assert view.results_table.rowCount() == 0


def test_expense_history_view_shows_archived_expense(qapp, test_db):
    """The seeded archived prior-year expense must render."""
    tab = HistoryTab()
    tab.on_expense_clicked()
    view = tab.expense_view

    years = [view.year_selector.itemText(i) for i in range(view.year_selector.count())]
    assert years == [str(PRIOR_YEAR)]

    assert view.table.rowCount() == 1
    assert view.table.item(0, 1).text() == f'{PRIOR_YEAR}-11-02'
    assert view.table.item(0, 3).text() == '$42.50'
    assert view.table.item(0, 4).text() == 'INV-2001'
    assert view.table.item(0, 5).text() == 'Prior year shipping supplies'


def test_history_views_independent_year_selection(qapp, test_db):
    """Each view keeps its own year widget; changing one must not move another."""
    tab = HistoryTab()

    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()

    # Every selector is populated, so the assertions below are real
    # (InventoryHistoryView uses year_combo, the others use year_selector).
    assert tab.sales_view.year_selector.count() == 1
    assert tab.inventory_view.year_combo.count() == 2  # 'All Years' + prior year
    assert tab.expense_view.year_selector.count() == 1

    # They must be three distinct widgets
    widgets = [tab.sales_view.year_selector,
               tab.inventory_view.year_combo,
               tab.expense_view.year_selector]
    assert len({id(w) for w in widgets}) == 3

    # Moving the inventory combo off "All Years" must not disturb the others
    assert tab.inventory_view.year_combo.currentIndex() == 0
    tab.inventory_view.year_combo.setCurrentIndex(1)

    assert tab.inventory_view.year_combo.currentText() == str(PRIOR_YEAR)
    assert tab.sales_view.year_selector.currentText() == str(PRIOR_YEAR)
    assert tab.sales_view.year_selector.currentIndex() == 0
    assert tab.expense_view.year_selector.currentIndex() == 0


def test_all_history_views_exclude_current_year(qapp, test_db):
    """No history view year selector should include current year."""
    tab = HistoryTab()

    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()

    # Check Sales History year selector
    sales_years = [tab.sales_view.year_selector.itemText(i)
                   for i in range(tab.sales_view.year_selector.count())]
    assert sales_years, 'Sales History year selector is empty -- seeding failed'
    assert str(PRIOR_YEAR) in sales_years
    assert str(CURRENT_YEAR) not in sales_years, f"Current year {CURRENT_YEAR} found in Sales History"

    # Check Inventory History year combo (uses different attribute name)
    inventory_years = [tab.inventory_view.year_combo.itemText(i)
                       for i in range(tab.inventory_view.year_combo.count())]
    assert str(PRIOR_YEAR) in inventory_years
    assert str(CURRENT_YEAR) not in inventory_years, f"Current year {CURRENT_YEAR} found in Inventory History"

    # Check Expense History year selector
    expense_years = [tab.expense_view.year_selector.itemText(i)
                     for i in range(tab.expense_view.year_selector.count())]
    assert expense_years, 'Expense History year selector is empty -- seeding failed'
    assert str(PRIOR_YEAR) in expense_years
    assert str(CURRENT_YEAR) not in expense_years, f"Current year {CURRENT_YEAR} found in Expense History"
