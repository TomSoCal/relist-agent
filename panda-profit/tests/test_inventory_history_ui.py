import os
import sys

import pytest
from PyQt5.QtWidgets import QApplication

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Isolated database for each test.

    Patches database.DB_PATH so nothing in this module can touch the
    production panda_profit.db.
    """
    import database
    from database import init_db

    test_db_path = os.path.join(os.path.dirname(__file__), 'test_history_ui.db')

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    monkeypatch.setattr(database, 'DB_PATH', test_db_path)

    init_db()

    yield test_db_path

    for suffix in ('', '-wal', '-shm'):
        path = test_db_path + suffix
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


class TestInventoryHistoryTab:

    @pytest.fixture
    def app(self):
        """Fixture to provide QApplication instance"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_tab_initializes(self, app, test_db):
        """InventoryHistoryView should initialize without errors"""
        from ui.history.inventory_history_view import InventoryHistoryView

        tab = InventoryHistoryView()

        assert tab is not None
        # Check for key widgets
        assert hasattr(tab, 'year_combo')
        assert hasattr(tab, 'search_input')
        assert hasattr(tab, 'results_table')
        assert hasattr(tab, 'search_button')

    def test_search_updates_table(self, app, test_db):
        """Search should populate results table"""
        from ui.history.inventory_history_view import InventoryHistoryView
        from database import add_inventory, get_connection

        # Add archived item
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Test Item',
            units=0,
            sku='TEST-01',
            category='Test',
            cost=10.0
        )

        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        # Create view and search
        tab = InventoryHistoryView()
        tab.search_input.setText('TEST')
        tab.perform_search()

        # Verify table populated
        assert tab.results_table.rowCount() > 0

    def test_tab_reads_from_current_db_path(self, app, test_db, monkeypatch):
        """View must resolve DB_PATH at query time, not at import time.

        Guards against reintroducing a module-level connection singleton.
        """
        import database
        from database import add_inventory, get_connection, init_db
        from ui.history.inventory_history_view import InventoryHistoryView

        # Item lives only in the *second* database
        second_db = os.path.join(os.path.dirname(__file__), 'test_history_ui_2.db')
        if os.path.exists(second_db):
            os.remove(second_db)

        monkeypatch.setattr(database, 'DB_PATH', second_db)
        init_db()

        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Second DB Item',
            units=0,
            sku='SECOND-01',
            category='Test',
            cost=10.0
        )
        conn = get_connection()
        conn.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        try:
            tab = InventoryHistoryView()
            tab.search_input.setText('SECOND')
            tab.perform_search()

            assert tab.results_table.rowCount() == 1
            assert tab.results_table.item(0, 0).text() == 'SECOND-01'
        finally:
            for suffix in ('', '-wal', '-shm'):
                path = second_db + suffix
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
