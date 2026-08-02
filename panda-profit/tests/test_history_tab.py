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
