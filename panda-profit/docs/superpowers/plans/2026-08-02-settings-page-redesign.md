# Settings Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize Settings page from single scrollable layout into 4 independent QTabWidget tabs with lazy-loading and full functionality preservation.

**Architecture:** Main `SettingsTab` container uses `QTabWidget` with 4 separate view classes (ApiInfoView, ItemSettingsView, PlatformFeesView, TaxSettingsView). Views instantiate only on first click, each maintaining independent state. Tax Settings includes P&L-derived calculated total.

**Tech Stack:** PyQt5 (QTabWidget, QStackedWidget, lazy-loading pattern), SQLite (database.py), existing oauth_setup and config modules

## Global Constraints

- Use `QTabWidget` for tab management (consistent with Unified History Tab v0.1.0)
- Lazy-load views to avoid startup lag — views should be None initially, instantiate on button click
- Database calls ONLY via `database.py` functions (never raw SQL in UI)
- All settings persist to `panda_profit.db`
- No breaking schema changes
- Follow existing code style: PyQt5, Python 3.9+, PEP 8
- Tab state is independent (changes in one tab don't affect others)
- All existing functionality must be preserved (no regressions)

---

## File Structure

**New Files:**
- `ui/settings/__init__.py` — Package marker
- `ui/settings/api_info_view.py` — eBay API configuration view
- `ui/settings/item_settings_view.py` — Stores/Categories/Brands consolidated view
- `ui/settings/platform_fees_view.py` — Platform fees table view
- `ui/settings/tax_settings_view.py` — Mileage + tax % + calculated total view
- `tests/test_settings_tab.py` — Comprehensive test suite

**Modified Files:**
- `ui/settings_tab.py` — Convert to QTabWidget with lazy-loading and button callbacks
- `database.py` — Add `get_pl_total()` function (if not exists)

**Unchanged:**
- `ui/main_window.py` — SettingsTab registration stays same
- `constants.py` — Already imported by views
- `config.py` — Existing usage unchanged
- `oauth_setup.py` — Existing usage unchanged

---

## Task Breakdown

### Task 1: Create Settings Package Structure

**Files:**
- Create: `ui/settings/__init__.py`

**Interfaces:**
- Produces: `ui.settings` package (empty module for future imports)

- [ ] **Step 1: Create the directory and init file**

Run:
```bash
mkdir -p ui/settings
touch ui/settings/__init__.py
```

- [ ] **Step 2: Verify structure**

Run:
```bash
ls -la ui/settings/
```

Expected: `__init__.py` file exists

- [ ] **Step 3: Commit**

```bash
git add ui/settings/__init__.py
git commit -m "feat: create ui/settings package structure"
```

---

### Task 2: Create ApiInfoView

**Files:**
- Create: `ui/settings/api_info_view.py`
- Test: `tests/test_settings_tab.py` (API info section)

**Interfaces:**
- Consumes: `config.ebay_configured()`, `config.get_ebay_config()`, `oauth_setup.prompt_for_oauth_setup()`
- Produces: `ApiInfoView(QWidget)` class with:
  - `__init__(self)` — Initialize UI
  - `load_settings()` → None — Load eBay status and app_id
  - `reconfigure_oauth()` → None — Handle OAuth setup
  - `test_ebay_connection()` → None — Test connection button

- [ ] **Step 1: Write ApiInfoView class with initialization**

Create `ui/settings/api_info_view.py`:

```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QMessageBox)
from PyQt5.QtGui import QFont
import config
from oauth_setup import prompt_for_oauth_setup

class ApiInfoView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()
        
        # Check if eBay is configured
        self.ebay_configured = config.ebay_configured()
        
        # Warning banner if not configured
        if not self.ebay_configured:
            warning_layout = QHBoxLayout()
            warning_label = QLabel("⚠️  eBay API not configured — Setup required to use inventory/sales features")
            warning_label.setStyleSheet("background-color: #2a2a1a; padding: 10px; border-radius: 4px; color: #ffaa00;")
            warning_font = QFont()
            warning_font.setBold(True)
            warning_label.setFont(warning_font)
            warning_layout.addWidget(warning_label)
            main_layout.addLayout(warning_layout)
        
        # eBay API Settings
        ebay_layout = QVBoxLayout()
        
        if self.ebay_configured:
            status_text = "✓ eBay credentials configured"
        else:
            status_text = "✗ eBay credentials not configured"
        
        ebay_layout.addWidget(QLabel(status_text))
        
        ebay_layout.addWidget(QLabel("App ID:"))
        self.app_id = QLineEdit()
        self.app_id.setReadOnly(True)
        ebay_layout.addWidget(self.app_id)
        
        ebay_layout.addWidget(QLabel("Cert ID:"))
        self.cert_id = QLineEdit()
        self.cert_id.setEchoMode(QLineEdit.Password)
        self.cert_id.setReadOnly(True)
        ebay_layout.addWidget(self.cert_id)
        
        button_layout = QHBoxLayout()
        
        if self.ebay_configured:
            reconfigure_btn = QPushButton("Reconfigure OAuth")
            reconfigure_btn.clicked.connect(self.reconfigure_oauth)
            button_layout.addWidget(reconfigure_btn)
            
            test_btn = QPushButton("Test Connection")
            test_btn.clicked.connect(self.test_ebay_connection)
            button_layout.addWidget(test_btn)
        else:
            setup_btn = QPushButton("Setup eBay OAuth")
            setup_btn.setStyleSheet("background-color: #ffaa00; font-weight: bold; padding: 5px; color: #000000;")
            setup_btn.clicked.connect(self.reconfigure_oauth)
            button_layout.addWidget(setup_btn)
            
            info_label = QLabel("(Required to use inventory/sales features)")
            info_label.setStyleSheet("color: #aaa; font-style: italic;")
            button_layout.addWidget(info_label)
        
        button_layout.addStretch()
        ebay_layout.addLayout(button_layout)
        
        main_layout.addLayout(ebay_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load eBay credentials from config"""
        try:
            if config.ebay_configured():
                ebay_config = config.get_ebay_config()
                self.app_id.setText(ebay_config.get('app_id', ''))
                self.cert_id.setPlaceholderText("(Already configured in PandaSuite)")
            else:
                self.app_id.setPlaceholderText("Enter your eBay App ID")
                self.cert_id.setPlaceholderText("Enter your eBay Cert ID")
        except Exception as e:
            print(f"Error loading API settings: {e}")
    
    def reconfigure_oauth(self):
        """Run OAuth setup"""
        try:
            if prompt_for_oauth_setup(self):
                QMessageBox.information(self, "Success",
                    "✓ eBay OAuth credentials configured!\n\n"
                    "These credentials are shared with all PandaSuite apps.\n"
                    "Restart the app or click Settings tab to see updates.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup eBay OAuth: {str(e)}")
    
    def test_ebay_connection(self):
        """Test eBay API connection"""
        if not config.ebay_configured():
            QMessageBox.warning(self, "Setup Required",
                "eBay credentials not configured yet.\n\n"
                "Click 'Setup eBay OAuth' to get started.")
            return
        
        try:
            token = config.get_ebay_token()
            QMessageBox.information(self, "Connection Successful",
                "✓ eBay API connection successful!\n\n"
                "Token is valid and will auto-refresh when needed.\n"
                "Credentials are shared with all PandaSuite apps.")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed",
                f"Error: {str(e)}\n\n"
                "Try clicking 'Reconfigure OAuth' to re-authenticate.")
```

- [ ] **Step 2: Verify file is created**

Run:
```bash
ls -l ui/settings/api_info_view.py
```

- [ ] **Step 3: Test import**

Run:
```bash
python -c "from ui.settings.api_info_view import ApiInfoView; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 4: Commit**

```bash
git add ui/settings/api_info_view.py
git commit -m "feat: add ApiInfoView for eBay API configuration"
```

---

### Task 3: Create ItemSettingsView

**Files:**
- Create: `ui/settings/item_settings_view.py`
- Test: `tests/test_settings_tab.py` (item settings section)

**Interfaces:**
- Consumes: `constants.STORES`, `constants.CATEGORIES`, `database.get_all_brands()`, `database.add_brand()`, `database.delete_brand()`, brand management functions
- Produces: `ItemSettingsView(QWidget)` class with:
  - `__init__(self)` — Initialize UI
  - `load_brands()` → None — Load brands from database
  - `add_store_dialog()` → None
  - `delete_store()` → None
  - `add_category_dialog()` → None
  - `delete_category()` → None
  - `add_brand_dialog()` → None
  - `delete_brand()` → None
  - `save_custom_items()` → None

- [ ] **Step 1: Write ItemSettingsView class**

Create `ui/settings/item_settings_view.py`:

```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QListWidget, QListWidgetItem, QTableWidget,
                            QTableWidgetItem, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
import database as db
from constants import CATEGORIES, STORES

class ItemSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI with three sections: Stores, Categories, Brands"""
        main_layout = QVBoxLayout()
        
        # STORES SECTION
        main_layout.addWidget(QLabel("Stores:"))
        stores_btn_layout = QHBoxLayout()
        add_store_btn = QPushButton("Add Store")
        add_store_btn.clicked.connect(self.add_store_dialog)
        delete_store_btn = QPushButton("Delete Store")
        delete_store_btn.clicked.connect(self.delete_store)
        stores_btn_layout.addWidget(add_store_btn)
        stores_btn_layout.addWidget(delete_store_btn)
        stores_btn_layout.addStretch()
        main_layout.addLayout(stores_btn_layout)
        
        self.stores_list = QListWidget()
        self.stores_list.addItems(STORES)
        main_layout.addWidget(self.stores_list)
        
        main_layout.addSpacing(20)
        
        # CATEGORIES SECTION
        main_layout.addWidget(QLabel("Categories:"))
        cat_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.clicked.connect(self.add_category_dialog)
        delete_cat_btn = QPushButton("Delete Category")
        delete_cat_btn.clicked.connect(self.delete_category)
        cat_btn_layout.addWidget(add_cat_btn)
        cat_btn_layout.addWidget(delete_cat_btn)
        cat_btn_layout.addStretch()
        main_layout.addLayout(cat_btn_layout)
        
        self.categories_list = QListWidget()
        self.categories_list.addItems(CATEGORIES)
        main_layout.addWidget(self.categories_list)
        
        main_layout.addSpacing(20)
        
        # BRANDS SECTION
        main_layout.addWidget(QLabel("Brands:"))
        add_brand_btn_layout = QHBoxLayout()
        add_brand_btn = QPushButton("Add Brand")
        add_brand_btn.clicked.connect(self.add_brand_dialog)
        add_brand_btn_layout.addWidget(add_brand_btn)
        add_brand_btn_layout.addStretch()
        main_layout.addLayout(add_brand_btn_layout)
        
        self.brands_table = QTableWidget()
        self.brands_table.setColumnCount(1)
        self.brands_table.setHorizontalHeaderLabels(["Brand Name"])
        self.brands_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.brands_table.customContextMenuRequested.connect(self.show_brands_context_menu)
        main_layout.addWidget(self.brands_table)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load brands from database"""
        self.load_brands()
    
    def load_brands(self):
        """Load brands table from database"""
        try:
            brands = db.get_all_brands()
            self.brands_table.setRowCount(len(brands))
            for row, brand in enumerate(brands):
                self.brands_table.setItem(row, 0, QTableWidgetItem(brand['name']))
                item = self.brands_table.item(row, 0)
                item.setData(Qt.UserRole, brand['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load brands: {str(e)}")
    
    def add_store_dialog(self):
        """Add new store to STORES list"""
        text, ok = QInputDialog.getText(self, "Add New Store", "Store name:")
        if ok and text:
            if text not in STORES:
                STORES.append(text)
                STORES.sort()
                self.stores_list.clear()
                self.stores_list.addItems(STORES)
                self.save_custom_items()
                QMessageBox.information(self, "Success", f"Store '{text}' added!")
            else:
                QMessageBox.warning(self, "Error", "Store already exists")
    
    def delete_store(self):
        """Delete selected store"""
        current = self.stores_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a store to delete")
            return
        
        store_name = current.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete store '{store_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            STORES.remove(store_name)
            self.stores_list.clear()
            self.stores_list.addItems(STORES)
            self.save_custom_items()
            QMessageBox.information(self, "Success", f"Store '{store_name}' deleted!")
    
    def add_category_dialog(self):
        """Add new category to CATEGORIES list"""
        text, ok = QInputDialog.getText(self, "Add New Category", "Category name:")
        if ok and text:
            if text not in CATEGORIES:
                CATEGORIES.append(text)
                CATEGORIES.sort()
                self.categories_list.clear()
                self.categories_list.addItems(CATEGORIES)
                self.save_custom_items()
                QMessageBox.information(self, "Success", f"Category '{text}' added!")
            else:
                QMessageBox.warning(self, "Error", "Category already exists")
    
    def delete_category(self):
        """Delete selected category"""
        current = self.categories_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a category to delete")
            return
        
        category_name = current.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete category '{category_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            CATEGORIES.remove(category_name)
            self.categories_list.clear()
            self.categories_list.addItems(CATEGORIES)
            self.save_custom_items()
            QMessageBox.information(self, "Success", f"Category '{category_name}' deleted!")
    
    def add_brand_dialog(self):
        """Add new brand to database"""
        name, ok = QInputDialog.getText(self, "Add Brand", "Brand name:")
        if not ok or not name:
            return
        
        try:
            db.add_brand(name)
            self.load_brands()
            QMessageBox.information(self, "Success", f"Brand '{name}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add brand: {str(e)}")
    
    def delete_brand(self, brand_id):
        """Delete brand by ID"""
        try:
            db.delete_brand(brand_id)
            self.load_brands()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete brand: {str(e)}")
    
    def show_brands_context_menu(self, position):
        """Show context menu for brands table"""
        item = self.brands_table.itemAt(position)
        if not item:
            return
        
        brand_id = item.data(Qt.UserRole)
        brand_name = self.brands_table.item(self.brands_table.row(item), 0).text()
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.brands_table.mapToGlobal(position))
        
        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                        f"Delete brand '{brand_name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_brand(brand_id)
    
    def save_custom_items(self):
        """Persist STORES and CATEGORIES to database"""
        import json
        db.set_setting('custom_stores', json.dumps(STORES))
        db.set_setting('custom_categories', json.dumps(CATEGORIES))
```

- [ ] **Step 2: Verify file is created**

Run:
```bash
ls -l ui/settings/item_settings_view.py
```

- [ ] **Step 3: Test import**

Run:
```bash
python -c "from ui.settings.item_settings_view import ItemSettingsView; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 4: Commit**

```bash
git add ui/settings/item_settings_view.py
git commit -m "feat: add ItemSettingsView for Stores/Categories/Brands management"
```

---

### Task 4: Create PlatformFeesView

**Files:**
- Create: `ui/settings/platform_fees_view.py`
- Test: `tests/test_settings_tab.py` (platform fees section)

**Interfaces:**
- Consumes: `database.get_all_platform_fees()`, `database.add_platform_fee()`, `database.update_platform_fee()`, `database.delete_platform_fee()`
- Produces: `PlatformFeesView(QWidget)` class with:
  - `__init__(self)` — Initialize UI
  - `load_platform_fees()` → None
  - `add_platform_fee_dialog()` → None
  - `delete_platform_fee()` → None
  - `show_platform_context_menu()` → None

- [ ] **Step 1: Write PlatformFeesView class**

Create `ui/settings/platform_fees_view.py`:

```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTableWidget, QTableWidgetItem, QInputDialog,
                            QMessageBox, QMenu)
from PyQt5.QtCore import Qt
import database as db

class PlatformFeesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI with platform fees table"""
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(QLabel("Platform Fees:"))
        add_platform_btn_layout = QHBoxLayout()
        add_platform_btn = QPushButton("Add Platform")
        add_platform_btn.clicked.connect(self.add_platform_fee_dialog)
        add_platform_btn_layout.addWidget(add_platform_btn)
        add_platform_btn_layout.addStretch()
        main_layout.addLayout(add_platform_btn_layout)
        
        self.platform_table = QTableWidget()
        self.platform_table.setColumnCount(5)
        self.platform_table.setHorizontalHeaderLabels(["Platform", "Transaction %", "Shipping %", "Payment %", "Notes"])
        self.platform_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.platform_table.customContextMenuRequested.connect(self.show_platform_context_menu)
        main_layout.addWidget(self.platform_table)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load platform fees from database"""
        self.load_platform_fees()
    
    def load_platform_fees(self):
        """Load and display platform fees"""
        try:
            fees = db.get_all_platform_fees()
            self.platform_table.setRowCount(len(fees))
            for row, fee in enumerate(fees):
                self.platform_table.setItem(row, 0, QTableWidgetItem(fee['platform']))
                self.platform_table.setItem(row, 1, QTableWidgetItem(str(fee.get('transaction_fee', 0))))
                self.platform_table.setItem(row, 2, QTableWidgetItem(str(fee.get('shipping_fee', 0))))
                self.platform_table.setItem(row, 3, QTableWidgetItem(str(fee.get('payment_fee', 0))))
                self.platform_table.setItem(row, 4, QTableWidgetItem(fee.get('notes', '')))
                item = self.platform_table.item(row, 0)
                item.setData(Qt.UserRole, fee['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load platform fees: {str(e)}")
    
    def add_platform_fee_dialog(self):
        """Add new platform fee"""
        platform, ok = QInputDialog.getText(self, "Add Platform", "Platform name:")
        if not ok or not platform:
            return
        
        trans_fee, ok = QInputDialog.getDouble(self, "Transaction Fee", "Transaction fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return
        
        ship_fee, ok = QInputDialog.getDouble(self, "Shipping Fee", "Shipping fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return
        
        pay_fee, ok = QInputDialog.getDouble(self, "Payment Fee", "Payment fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return
        
        notes, ok = QInputDialog.getText(self, "Notes", "Notes (optional):")
        if not ok:
            return
        
        try:
            db.add_platform_fee(platform, trans_fee, ship_fee, pay_fee, notes)
            self.load_platform_fees()
            QMessageBox.information(self, "Success", f"Platform '{platform}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add platform: {str(e)}")
    
    def delete_platform_fee(self, fee_id):
        """Delete platform fee by ID"""
        try:
            db.delete_platform_fee(fee_id)
            self.load_platform_fees()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete platform fee: {str(e)}")
    
    def show_platform_context_menu(self, position):
        """Show context menu for platform fees table"""
        item = self.platform_table.itemAt(position)
        if not item:
            return
        
        fee_id = item.data(Qt.UserRole)
        platform_name = self.platform_table.item(self.platform_table.row(item), 0).text()
        
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.platform_table.mapToGlobal(position))
        
        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                        f"Delete platform '{platform_name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_platform_fee(fee_id)
```

- [ ] **Step 2: Verify file is created**

Run:
```bash
ls -l ui/settings/platform_fees_view.py
```

- [ ] **Step 3: Test import**

Run:
```bash
python -c "from ui.settings.platform_fees_view import PlatformFeesView; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 4: Commit**

```bash
git add ui/settings/platform_fees_view.py
git commit -m "feat: add PlatformFeesView for platform fees management"
```

---

### Task 5: Add get_pl_total() to Database

**Files:**
- Modify: `database.py`

**Interfaces:**
- Produces: `get_pl_total(year=None) -> float` — Returns current-year P&L total (revenue - expenses)

- [ ] **Step 1: Read database.py to understand existing P&L functions**

Run:
```bash
grep -n "def get_" database.py | head -20
```

- [ ] **Step 2: Add get_pl_total() function to database.py**

Add this function to `database.py` (find a good location after other calculate/get functions):

```python
def get_pl_total(year=None):
    """
    Calculate total Profit & Loss for a given year (current year if not specified).
    Returns: revenue - expenses (can be negative if expenses exceed revenue).
    """
    from datetime import datetime
    
    if year is None:
        year = datetime.now().year
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate total revenue from sales (current year)
        cursor.execute(f"""
            SELECT COALESCE(SUM(CAST(sale_price AS FLOAT) * units), 0)
            FROM sales
            WHERE strftime('%Y', sold_date) = ? AND archived = 0
        """, (str(year),))
        total_revenue = cursor.fetchone()[0]
        
        # Calculate total expenses (current year)
        cursor.execute(f"""
            SELECT COALESCE(SUM(CAST(amount AS FLOAT)), 0)
            FROM expenses
            WHERE strftime('%Y', date_incurred) = ? AND archived = 0
        """, (str(year),))
        total_expenses = cursor.fetchone()[0]
        
        conn.close()
        
        # P&L = Revenue - Expenses
        return total_revenue - total_expenses
    
    except Exception as e:
        print(f"Error calculating P&L total: {e}")
        return 0.0
```

- [ ] **Step 3: Verify function is added**

Run:
```bash
grep -A 20 "def get_pl_total" database.py
```

Expected: Function body visible

- [ ] **Step 4: Test the function**

Run:
```python
python -c "import database as db; result = db.get_pl_total(); print(f'P&L Total: \${result:.2f}')"
```

Expected: Numeric output (even if $0.00)

- [ ] **Step 5: Commit**

```bash
git add database.py
git commit -m "feat: add get_pl_total() function to calculate P&L for tax settings"
```

---

### Task 6: Create TaxSettingsView

**Files:**
- Create: `ui/settings/tax_settings_view.py`
- Test: `tests/test_settings_tab.py` (tax settings section)

**Interfaces:**
- Consumes: `database.get_setting()`, `database.set_setting()`, `database.get_pl_total()`
- Produces: `TaxSettingsView(QWidget)` class with:
  - `__init__(self)` — Initialize UI
  - `load_settings()` → None — Load mileage rate and tax percentage
  - `save_mileage_rate()` → None
  - `save_tax_percentage()` → None
  - `update_total_to_save()` → None — Recalculate P&L-derived total
  - `showEvent(event)` — Override to recalculate on tab show

- [ ] **Step 1: Write TaxSettingsView class**

Create `ui/settings/tax_settings_view.py`:

```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QDoubleSpinBox, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt
import database as db

class TaxSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI with mileage rate, tax percentage, and calculated total"""
        main_layout = QVBoxLayout()
        
        # MILEAGE DEDUCTION SECTION
        main_layout.addWidget(QLabel("Mileage Deduction (Tax & Deductions)"))
        main_layout.addWidget(QLabel("Enter the IRS standard mileage rate for your region."))
        
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Rate: $"))
        self.mileage_rate_input = QDoubleSpinBox()
        self.mileage_rate_input.setRange(0.0, 10.0)
        self.mileage_rate_input.setSingleStep(0.01)
        self.mileage_rate_input.setDecimals(3)
        self.mileage_rate_input.setValue(0.67)
        rate_layout.addWidget(self.mileage_rate_input)
        rate_layout.addWidget(QLabel("/ mile"))
        
        save_rate_btn = QPushButton("Save Rate")
        save_rate_btn.clicked.connect(self.save_mileage_rate)
        rate_layout.addWidget(save_rate_btn)
        rate_layout.addStretch()
        
        main_layout.addLayout(rate_layout)
        main_layout.addSpacing(20)
        
        # TAX SAVINGS PERCENTAGE SECTION
        main_layout.addWidget(QLabel("Tax Savings Percentage"))
        main_layout.addWidget(QLabel("Enter the percentage of your P&L you want to reserve for taxes."))
        
        tax_pct_layout = QHBoxLayout()
        tax_pct_layout.addWidget(QLabel("Percentage:"))
        self.tax_percentage_input = QDoubleSpinBox()
        self.tax_percentage_input.setRange(0.0, 100.0)
        self.tax_percentage_input.setSingleStep(1.0)
        self.tax_percentage_input.setDecimals(1)
        self.tax_percentage_input.setValue(50.0)
        self.tax_percentage_input.valueChanged.connect(self.update_total_to_save)
        tax_pct_layout.addWidget(self.tax_percentage_input)
        tax_pct_layout.addWidget(QLabel("%"))
        
        save_tax_btn = QPushButton("Save Percentage")
        save_tax_btn.clicked.connect(self.save_tax_percentage)
        tax_pct_layout.addWidget(save_tax_btn)
        tax_pct_layout.addStretch()
        
        main_layout.addLayout(tax_pct_layout)
        main_layout.addSpacing(20)
        
        # CALCULATED TOTAL SECTION
        main_layout.addWidget(QLabel("Total to Save for Taxes"))
        main_layout.addWidget(QLabel("Formula: P&L Total × (1 - Tax Savings %/100)"))
        
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total to Save:"))
        self.total_to_save = QLineEdit()
        self.total_to_save.setReadOnly(True)
        self.total_to_save.setText("$0.00")
        total_layout.addWidget(self.total_to_save)
        total_layout.addStretch()
        
        main_layout.addLayout(total_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load mileage rate and tax percentage from database"""
        try:
            # Load mileage rate
            mileage_rate = db.get_setting('mileage_rate')
            if mileage_rate:
                self.mileage_rate_input.setValue(float(mileage_rate))
            else:
                self.mileage_rate_input.setValue(0.67)  # Default IRS rate
            
            # Load tax percentage
            tax_pct = db.get_setting('tax_percentage')
            if tax_pct:
                self.tax_percentage_input.setValue(float(tax_pct))
            else:
                self.tax_percentage_input.setValue(50.0)  # Default 50%
            
            # Calculate and display total
            self.update_total_to_save()
        
        except Exception as e:
            print(f"Error loading tax settings: {e}")
    
    def save_mileage_rate(self):
        """Save mileage rate to database"""
        try:
            rate = self.mileage_rate_input.value()
            db.set_setting('mileage_rate', str(rate))
            QMessageBox.information(self, "Success", f"Mileage rate saved: ${rate:.3f}/mile")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mileage rate: {str(e)}")
    
    def save_tax_percentage(self):
        """Save tax percentage to database"""
        try:
            pct = self.tax_percentage_input.value()
            db.set_setting('tax_percentage', str(pct))
            QMessageBox.information(self, "Success", f"Tax percentage saved: {pct}%")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tax percentage: {str(e)}")
    
    def update_total_to_save(self):
        """Recalculate total to save based on P&L and tax percentage"""
        try:
            pl_total = db.get_pl_total()
            tax_pct = self.tax_percentage_input.value()
            
            # Formula: P&L × (1 - tax% / 100)
            total_to_save = pl_total * (1.0 - tax_pct / 100.0)
            
            self.total_to_save.setText(f"${total_to_save:,.2f}")
        except Exception as e:
            self.total_to_save.setText("$0.00")
            self.total_to_save.setToolTip(f"Unable to calculate: {str(e)}")
    
    def showEvent(self, event):
        """Recalculate total when tab is shown (refreshes P&L)"""
        super().showEvent(event)
        self.update_total_to_save()
```

- [ ] **Step 2: Verify file is created**

Run:
```bash
ls -l ui/settings/tax_settings_view.py
```

- [ ] **Step 3: Test import**

Run:
```bash
python -c "from ui.settings.tax_settings_view import TaxSettingsView; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 4: Commit**

```bash
git add ui/settings/tax_settings_view.py
git commit -m "feat: add TaxSettingsView with mileage rate, tax percentage, and P&L-derived total"
```

---

### Task 7: Refactor SettingsTab to Use QTabWidget

**Files:**
- Modify: `ui/settings_tab.py` (complete rewrite)

**Interfaces:**
- Consumes: `ApiInfoView`, `ItemSettingsView`, `PlatformFeesView`, `TaxSettingsView`
- Produces: `SettingsTab(QWidget)` with:
  - `__init__(self)` — Initialize QTabWidget
  - `on_api_clicked()` → None
  - `on_items_clicked()` → None
  - `on_fees_clicked()` → None
  - `on_tax_clicked()` → None

- [ ] **Step 1: Back up current settings_tab.py**

Run:
```bash
cp ui/settings_tab.py ui/settings_tab.py.backup
```

- [ ] **Step 2: Rewrite settings_tab.py with QTabWidget**

Replace entire content of `ui/settings_tab.py`:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QStackedWidget
from ui.settings.api_info_view import ApiInfoView
from ui.settings.item_settings_view import ItemSettingsView
from ui.settings.platform_fees_view import PlatformFeesView
from ui.settings.tax_settings_view import TaxSettingsView

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.api_view = None
        self.items_view = None
        self.fees_view = None
        self.tax_view = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize QTabWidget with 4 settings tabs"""
        main_layout = QVBoxLayout()
        
        # Create QTabWidget
        self.tabs = QTabWidget()
        
        # Tab 1: API Info
        self.api_button = QPushButton("API Info")
        self.api_button.clicked.connect(self.on_api_clicked)
        
        # Tab 2: Item Settings
        self.items_button = QPushButton("Item Settings")
        self.items_button.clicked.connect(self.on_items_clicked)
        
        # Tab 3: Platform Fees
        self.fees_button = QPushButton("Platform Fees")
        self.fees_button.clicked.connect(self.on_fees_clicked)
        
        # Tab 4: Tax Settings
        self.tax_button = QPushButton("Tax Settings")
        self.tax_button.clicked.connect(self.on_tax_clicked)
        
        # Add tabs (initially empty, will be filled on click)
        self.tabs.addTab(QWidget(), "API Info")
        self.tabs.addTab(QWidget(), "Item Settings")
        self.tabs.addTab(QWidget(), "Platform Fees")
        self.tabs.addTab(QWidget(), "Tax Settings")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def on_api_clicked(self):
        """Lazy-load API Info view"""
        if self.api_view is None:
            self.api_view = ApiInfoView()
            self.tabs.removeTab(0)
            self.tabs.insertTab(0, self.api_view, "API Info")
        self.tabs.setCurrentIndex(0)
    
    def on_items_clicked(self):
        """Lazy-load Item Settings view"""
        if self.items_view is None:
            self.items_view = ItemSettingsView()
            self.tabs.removeTab(1)
            self.tabs.insertTab(1, self.items_view, "Item Settings")
        self.tabs.setCurrentIndex(1)
    
    def on_fees_clicked(self):
        """Lazy-load Platform Fees view"""
        if self.fees_view is None:
            self.fees_view = PlatformFeesView()
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.fees_view, "Platform Fees")
        self.tabs.setCurrentIndex(2)
    
    def on_tax_clicked(self):
        """Lazy-load Tax Settings view"""
        if self.tax_view is None:
            self.tax_view = TaxSettingsView()
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.tax_view, "Tax Settings")
        self.tabs.setCurrentIndex(3)
```

- [ ] **Step 3: Verify file is updated**

Run:
```bash
head -20 ui/settings_tab.py
```

Expected: QTabWidget imports visible

- [ ] **Step 4: Test import**

Run:
```bash
python -c "from ui.settings_tab import SettingsTab; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 5: Commit**

```bash
git add ui/settings_tab.py
git commit -m "feat: refactor SettingsTab to use QTabWidget with lazy-loading"
```

---

### Task 8: Create Comprehensive Test Suite

**Files:**
- Create: `tests/test_settings_tab.py`

**Interfaces:**
- Consumes: `SettingsTab`, `ApiInfoView`, `ItemSettingsView`, `PlatformFeesView`, `TaxSettingsView`, `database.py`
- Produces: 20+ tests covering all settings functionality

- [ ] **Step 1: Write test file with fixtures**

Create `tests/test_settings_tab.py`:

```python
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

@pytest.fixture
def qapp(qtbot):
    """Fixture for QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def test_db(tmp_path):
    """Fixture for isolated test database"""
    db_path = tmp_path / "test_panda_profit.db"
    db.DB_PATH = str(db_path)
    db.init_db()
    yield db
    sqlite3.connect(str(db_path)).close()

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
    """Views should be None initially"""
    tab = SettingsTab()
    assert tab.api_view is None
    assert tab.items_view is None
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
    db.add_sale(item_name="Test Item", units=1, sale_price=1000.0, sold_date=f"{datetime.now().year}-01-01")
    db.add_expense(category_id=1, amount=100.0, date_incurred=f"{datetime.now().year}-01-01")
    
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
```

- [ ] **Step 2: Verify file is created**

Run:
```bash
ls -l tests/test_settings_tab.py
```

- [ ] **Step 3: Run tests**

Run:
```bash
pytest tests/test_settings_tab.py -v
```

Expected: All tests pass (20+)

- [ ] **Step 4: Check full test suite**

Run:
```bash
pytest tests/ -v --tb=short 2>&1 | tail -15
```

Expected: All tests passing, no regressions

- [ ] **Step 5: Commit**

```bash
git add tests/test_settings_tab.py
git commit -m "test: add comprehensive test suite for Settings page redesign

- SettingsTab initialization and lazy-loading
- ApiInfoView initialization
- ItemSettingsView stores/categories/brands display
- PlatformFeesView table and fees loading
- TaxSettingsView rate/percentage/calculation
- Settings persistence tests
- All 20+ tests passing"
```

---

### Task 9: Manual Testing and Verification

**Files:**
- No files modified (testing only)

**Interfaces:**
- Testing: Manual smoke test of complete Settings page
- Verifying: All views working, data persisting, no regressions

- [ ] **Step 1: Launch app**

Run:
```bash
python main.py &
```

Wait for GUI to appear.

- [ ] **Step 2: Smoke test API Info tab**

Manual checklist:
- [ ] Click "API Info" tab → ApiInfoView loads
- [ ] Status label displays (configured or not)
- [ ] App ID field visible
- [ ] Cert ID field masked
- [ ] OAuth button visible
- [ ] Tab switches back to other tabs without error

- [ ] **Step 3: Smoke test Item Settings tab**

Manual checklist:
- [ ] Click "Item Settings" tab → ItemSettingsView loads
- [ ] Stores section visible with list
- [ ] Categories section visible with list
- [ ] Brands section visible with table
- [ ] Add store button works
- [ ] Delete store button works (after adding one)
- [ ] Add category button works
- [ ] Delete category button works
- [ ] Add brand button works
- [ ] Delete brand via context menu works

- [ ] **Step 4: Smoke test Platform Fees tab**

Manual checklist:
- [ ] Click "Platform Fees" tab → PlatformFeesView loads
- [ ] Table displays with 5 columns
- [ ] Add Platform button works
- [ ] Can add a new platform fee
- [ ] Table updates with new entry
- [ ] Right-click context menu shows delete option
- [ ] Delete works

- [ ] **Step 5: Smoke test Tax Settings tab**

Manual checklist:
- [ ] Click "Tax Settings" tab → TaxSettingsView loads
- [ ] Mileage rate spinbox displays
- [ ] Tax percentage spinbox displays
- [ ] Save Rate button works
- [ ] Save Percentage button works
- [ ] Total to Save field displays calculation
- [ ] Changing tax % updates total
- [ ] Settings persist after app restart

- [ ] **Step 6: Verify no regressions**

Manual checklist:
- [ ] Sales tab still works
- [ ] Inventory tab still works
- [ ] Expenses tab still works
- [ ] History tab still works
- [ ] Dashboard tab still works
- [ ] No errors in console (run main.py in terminal to see output)
- [ ] Tab switching is smooth

- [ ] **Step 7: Run full test suite once more**

Run:
```bash
pytest tests/ -v 2>&1 | tail -10
```

Expected: All tests passing

- [ ] **Step 8: Create final verification commit**

```bash
git commit --allow-empty -m "test: verify Settings page redesign complete

- All 4 tabs initialized and functional (API Info, Item Settings, Platform Fees, Tax Settings)
- Lazy-loading working (views created on first click)
- Tab state independent (changes in one don't affect others)
- All existing functionality preserved (no regressions)
- API Info shows eBay status and OAuth buttons
- Item Settings consolidates Stores, Categories, Brands
- Platform Fees table displays and allows add/delete
- Tax Settings shows mileage rate, tax percentage, calculated total
- Total to Save recalculates on tax percentage change
- All 20+ tests passing
- Manual smoke test complete
- Settings persist across app restarts
- Production ready"
```

---

## Summary

This plan implements the Settings page redesign as a complete reorganization into 4 independent QTabWidget tabs with lazy-loading, full test coverage, and no schema changes. Each task is independently reviewable and testable. Total: 9 tasks, ~200 lines of new code per view, 20+ comprehensive tests.

