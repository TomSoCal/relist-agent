import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# We'll test the tab components

class TestInventoryHistoryTab:

    @pytest.fixture
    def app(self):
        """Fixture to provide QApplication instance"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_tab_initializes(self, app):
        """InventoryHistoryTab should initialize without errors"""
        from ui.inventory_history_tab import InventoryHistoryTab
        from database import init_db

        init_db()
        tab = InventoryHistoryTab()

        assert tab is not None
        # Check for key widgets
        assert hasattr(tab, 'year_combo')
        assert hasattr(tab, 'search_input')
        assert hasattr(tab, 'results_table')
        assert hasattr(tab, 'search_button')

    def test_search_updates_table(self, app):
        """Search should populate results table"""
        from ui.inventory_history_tab import InventoryHistoryTab
        from database import init_db, add_inventory

        init_db()

        # Add archived item
        item_id = add_inventory(
            listed_date='2026-01-01',
            item_title='Test Item',
            units=0,
            sku='TEST-01',
            category='Test',
            cost=10.0
        )

        from database import db
        db.execute("UPDATE inventory SET archived = 1 WHERE id = ?", (item_id,))
        db.commit()

        # Create tab and search
        tab = InventoryHistoryTab()
        tab.search_input.setText('TEST')
        tab.perform_search()

        # Verify table populated
        assert tab.results_table.rowCount() > 0
