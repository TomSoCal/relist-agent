import pytest
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui.settings_tab import SettingsTab
from ui.settings.api_info_view import ApiInfoView
from ui.settings.item_settings_view import ItemSettingsView
from ui.settings.platform_fees_view import PlatformFeesView
from ui.settings.tax_settings_view import TaxSettingsView
import database as db

@pytest.fixture(scope='module')
def qapp():
    """Fixture for QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Fixture for isolated test database"""
    test_db_path = str(tmp_path / 'test_settings_tab.db')
    monkeypatch.setattr('database.DB_PATH', test_db_path)
    db.init_db()
    yield
    import os
    import gc
    # Force cleanup of database connections
    gc.collect()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            pass  # Database may still be locked; tmp_path cleanup will handle it

# ========== SettingsTab Tests ==========

def test_settings_tab_initializes(qapp, test_db):
    """SettingsTab should initialize with 4 empty tabs"""
    tab = SettingsTab()
    assert tab.tabs is not None
    assert tab.tabs.count() == 4
    assert tab.tabs.tabText(0) == "API Info"
    assert tab.tabs.tabText(1) == "Item Settings"
    assert tab.tabs.tabText(2) == "Platform Fees"
    assert tab.tabs.tabText(3) == "Tax Settings"

def test_settings_tab_lazy_loads_views(qapp, test_db):
    """API view should load by default, others None until clicked"""
    tab = SettingsTab()
    assert tab.api_view is not None  # API Info loads by default
    assert tab.items_view is None    # Others lazy-load on click
    assert tab.fees_view is None
    assert tab.tax_view is None

def test_settings_tab_loads_api_view_on_click(qapp, test_db):
    """Clicking API Info button should instantiate ApiInfoView"""
    tab = SettingsTab()
    tab.on_api_clicked()
    assert tab.api_view is not None
    assert isinstance(tab.api_view, ApiInfoView)

def test_settings_tab_loads_items_view_on_click(qapp, test_db):
    """Clicking Item Settings button should instantiate ItemSettingsView"""
    tab = SettingsTab()
    tab.on_items_clicked()
    assert tab.items_view is not None
    assert isinstance(tab.items_view, ItemSettingsView)

def test_settings_tab_loads_fees_view_on_click(qapp, test_db):
    """Clicking Platform Fees button should instantiate PlatformFeesView"""
    tab = SettingsTab()
    tab.on_fees_clicked()
    assert tab.fees_view is not None
    assert isinstance(tab.fees_view, PlatformFeesView)

def test_settings_tab_loads_tax_view_on_click(qapp, test_db):
    """Clicking Tax Settings button should instantiate TaxSettingsView"""
    tab = SettingsTab()
    tab.on_tax_clicked()
    assert tab.tax_view is not None
    assert isinstance(tab.tax_view, TaxSettingsView)

# ========== ApiInfoView Tests ==========

def test_api_info_view_initializes(qapp, test_db):
    """ApiInfoView should initialize without errors"""
    view = ApiInfoView()
    assert view is not None
    assert hasattr(view, 'app_id')
    assert hasattr(view, 'cert_id')

def test_api_info_view_loads_settings(qapp, test_db):
    """ApiInfoView should load eBay status from config"""
    view = ApiInfoView()
    # Should have app_id field (even if empty)
    assert view.app_id is not None

# ========== ItemSettingsView Tests ==========

def test_item_settings_view_initializes(qapp, test_db):
    """ItemSettingsView should initialize with three sections"""
    view = ItemSettingsView()
    assert view is not None
    assert hasattr(view, 'stores_list')
    assert hasattr(view, 'categories_list')
    assert hasattr(view, 'brands_table')

def test_item_settings_view_displays_stores(qapp, test_db):
    """ItemSettingsView should display existing stores"""
    from constants import STORES
    view = ItemSettingsView()
    assert view.stores_list.count() == len(STORES)

def test_item_settings_view_displays_categories(qapp, test_db):
    """ItemSettingsView should display existing categories"""
    from constants import CATEGORIES
    view = ItemSettingsView()
    assert view.categories_list.count() == len(CATEGORIES)

def test_item_settings_view_loads_brands(qapp, test_db):
    """ItemSettingsView should load brands from database"""
    # Add test brand
    db.add_brand("Test Brand")
    view = ItemSettingsView()
    # Should have at least one brand
    assert view.brands_table.rowCount() >= 1

# ========== PlatformFeesView Tests ==========

def test_platform_fees_view_initializes(qapp, test_db):
    """PlatformFeesView should initialize with fees table"""
    view = PlatformFeesView()
    assert view is not None
    assert hasattr(view, 'platform_table')

def test_platform_fees_view_loads_fees(qapp, test_db):
    """PlatformFeesView should load platform fees from database"""
    # Add test platform
    db.add_platform_fee("TestPlatform", 2.5, 0.5, 1.0, "Test")
    view = PlatformFeesView()
    # Should have at least one platform
    assert view.platform_table.rowCount() >= 1

def test_platform_fees_view_table_columns(qapp, test_db):
    """PlatformFeesView table should have 5 columns"""
    view = PlatformFeesView()
    assert view.platform_table.columnCount() == 5

# ========== TaxSettingsView Tests ==========

def test_tax_settings_view_initializes(qapp, test_db):
    """TaxSettingsView should initialize with rate and percentage inputs"""
    view = TaxSettingsView()
    assert view is not None
    assert hasattr(view, 'mileage_rate_input')
    assert hasattr(view, 'tax_percentage_input')
    assert hasattr(view, 'total_to_save')

def test_tax_settings_view_loads_mileage_rate(qapp, test_db):
    """TaxSettingsView should load mileage rate from database"""
    db.set_setting('mileage_rate', '0.60')
    view = TaxSettingsView()
    # Should load the saved rate (allow small float difference)
    assert abs(view.mileage_rate_input.value() - 0.60) < 0.01

def test_tax_settings_view_loads_tax_percentage(qapp, test_db):
    """TaxSettingsView should load tax percentage from database"""
    db.set_setting('tax_percentage', '45.0')
    view = TaxSettingsView()
    assert abs(view.tax_percentage_input.value() - 45.0) < 0.1

def test_tax_settings_view_calculates_total(qapp, test_db):
    """TaxSettingsView should calculate total to save from P&L"""
    # Seed test data
    current_year = datetime.now().year
    db.add_sale(item_title="Test Item", units=1, sale_price=1000.0, sold_date=f"{current_year}-01-01")
    db.add_expense(current_year, f"{current_year}-01-01", 1, 100.0, '', 'Test', '', '')

    view = TaxSettingsView()
    view.tax_percentage_input.setValue(50.0)
    view.update_total_to_save()

    # P&L = 1000 - 100 = 900
    # Total to save = 900 * (1 - 50/100) = 450
    total_text = view.total_to_save.text()
    assert "$" in total_text
    assert "45" in total_text or "450" in total_text

def test_tax_settings_view_saves_mileage_rate(qapp, test_db, monkeypatch):
    """TaxSettingsView should save mileage rate to database"""
    view = TaxSettingsView()
    view.mileage_rate_input.setValue(0.75)

    # Mock QMessageBox to avoid dialog
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)

    view.save_mileage_rate()

    # Verify saved
    saved = db.get_setting('mileage_rate')
    assert saved is not None
    assert float(saved) == 0.75

def test_tax_settings_view_saves_tax_percentage(qapp, test_db, monkeypatch):
    """TaxSettingsView should save tax percentage to database"""
    view = TaxSettingsView()
    view.tax_percentage_input.setValue(40.0)

    # Mock QMessageBox to avoid dialog
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)

    view.save_tax_percentage()

    # Verify saved
    saved = db.get_setting('tax_percentage')
    assert saved is not None
    assert float(saved) == 40.0
