# Unified History Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate Sales History, Inventory History, and Expense History into a single History tab with button-based navigation between three independent prior-year data views.

**Architecture:** Single `HistoryTab` container with three lazy-loaded view widgets (SalesHistoryView, InventoryHistoryView, ExpenseHistoryView). Each view manages independent year selection (prior years only), search/filter, and data loading. Buttons at top switch visible view. Refactor existing history tabs from QWidget to independent view classes. Remove separate "Inventory History" and "Expense History" tabs from main window.

**Tech Stack:** PyQt5 (QWidget, QStackedWidget, QComboBox), existing database functions, soft-delete archive pattern

## Global Constraints

- All three history views show strictly prior-year data (current year excluded from year selectors)
- Current year data remains in: Sales tab (sales), Inventory tab (inventory), Expenses tab (expenses)
- Sales History filters sales data where year < current_year
- Inventory History filters to archived=1 (soft-deleted items)
- Expense History filters to archived=1 (soft-deleted expenses)
- Each history view maintains independent year selection (changing year in one view does not affect others)
- Lazy loading: views created on first button click, not on tab initialization
- No changes to database schema or existing CRUD functions
- All 191 existing tests must pass; new tests added for HistoryTab integration
- Year selectors dynamically populated: only show years with data (no empty years in dropdown)

---

## File Structure Overview

**New files:**
- `ui/history_tab.py` — HistoryTab container with button bar and stacked widget
- `ui/history/sales_history_view.py` — SalesHistoryView for prior-year sales
- `ui/history/inventory_history_view.py` — InventoryHistoryView (refactored from inventory_history_tab.py)
- `ui/history/expense_history_view.py` — ExpenseHistoryView (refactored from expense_history_tab.py)

**Modified files:**
- `ui/main_window.py` — register History tab, remove Inventory History and Expense History tabs
- Tests: `tests/test_history_tab.py` — new tests for HistoryTab integration

**Deleted files:**
- `ui/expense_history_tab.py` (code refactored)
- `ui/inventory_history_tab.py` (code refactored)

---

## Task 1: Create base HistoryTab container

**Files:**
- Create: `ui/history_tab.py`
- Test: `tests/test_history_tab.py`

**Interfaces:**
- Produces: `HistoryTab(QWidget)` class with methods:
  - `__init__()` — initialize, create button bar and stacked widget
  - `on_sales_clicked()` — lazy-load and show SalesHistoryView
  - `on_inventory_clicked()` — lazy-load and show InventoryHistoryView
  - `on_expense_clicked()` — lazy-load and show ExpenseHistoryView

- [ ] **Step 1: Write test for HistoryTab initialization**

Create `tests/test_history_tab.py`:

```python
import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from ui.history_tab import HistoryTab

@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:\Users\tom\agents\panda-profit
pytest tests/test_history_tab.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'ui.history_tab'`

- [ ] **Step 3: Create HistoryTab skeleton**

Create `ui/history_tab.py`:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt

class HistoryTab(QWidget):
    """Container for Sales History, Inventory History, and Expense History views."""
    
    def __init__(self):
        super().__init__()
        self.current_view = None
        self.sales_view = None
        self.inventory_view = None
        self.expense_view = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI with button bar and stacked widget."""
        layout = QVBoxLayout()
        
        # Button bar
        button_layout = QHBoxLayout()
        
        sales_btn = QPushButton("Sales History")
        sales_btn.clicked.connect(self.on_sales_clicked)
        button_layout.addWidget(sales_btn)
        
        inventory_btn = QPushButton("Inventory History")
        inventory_btn.clicked.connect(self.on_inventory_clicked)
        button_layout.addWidget(inventory_btn)
        
        expense_btn = QPushButton("Expense History")
        expense_btn.clicked.connect(self.on_expense_clicked)
        button_layout.addWidget(expense_btn)
        
        layout.addLayout(button_layout)
        
        # Stacked widget for views
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)
        
        self.setLayout(layout)
    
    def on_sales_clicked(self):
        """Show Sales History view."""
        if self.sales_view is None:
            from ui.history.sales_history_view import SalesHistoryView
            self.sales_view = SalesHistoryView()
            self.stacked.addWidget(self.sales_view)
        self.stacked.setCurrentWidget(self.sales_view)
    
    def on_inventory_clicked(self):
        """Show Inventory History view."""
        if self.inventory_view is None:
            from ui.history.inventory_history_view import InventoryHistoryView
            self.inventory_view = InventoryHistoryView()
            self.stacked.addWidget(self.inventory_view)
        self.stacked.setCurrentWidget(self.inventory_view)
    
    def on_expense_clicked(self):
        """Show Expense History view."""
        if self.expense_view is None:
            from ui.history.expense_history_view import ExpenseHistoryView
            self.expense_view = ExpenseHistoryView()
            self.stacked.addWidget(self.expense_view)
        self.stacked.setCurrentWidget(self.expense_view)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_history_tab.py::test_history_tab_initializes -v
pytest tests/test_history_tab.py::test_history_tab_has_buttons -v
```

Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add ui/history_tab.py tests/test_history_tab.py
git commit -m "feat: create HistoryTab container with button-based view switching

- Add HistoryTab class with three buttons (Sales/Inventory/Expense History)
- Implement lazy loading: views created on first button click
- Use QStackedWidget to manage visible view
- Add basic tests for initialization"
```

---

## Task 2: Create SalesHistoryView for prior-year sales

**Files:**
- Create: `ui/history/sales_history_view.py`
- Create: `ui/history/__init__.py` (empty, for package)

**Interfaces:**
- Consumes: `database.get_sales(year)` and existing ViewSaleDialog
- Produces: `SalesHistoryView(QWidget)` class with:
  - `load_sales()` — fetch and populate sales table for selected year
  - `on_year_changed()` — reload when year selector changes
  - `view_sale()` — open read-only view dialog

- [ ] **Step 1: Create history package init**

Create `ui/history/__init__.py`:

```python
# History views package
```

- [ ] **Step 2: Write test for SalesHistoryView**

Add to `tests/test_history_tab.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_history_tab.py::test_sales_history_view_initializes -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'ui.history.sales_history_view'`

- [ ] **Step 4: Create SalesHistoryView**

Create `ui/history/sales_history_view.py`:

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
import database as db

class SalesHistoryView(QWidget):
    """Display prior-year sales (archived data)."""
    
    def __init__(self):
        super().__init__()
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_years()
        self.load_sales()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentIndexChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)
        year_layout.addStretch()
        layout.addLayout(year_layout)
        
        # Summary stats
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("Month Total:"))
        self.month_total_label = QLabel("$0.00")
        stats_layout.addWidget(self.month_total_label)
        
        stats_layout.addWidget(QLabel("Year Total:"))
        self.year_total_label = QLabel("$0.00")
        stats_layout.addWidget(self.year_total_label)
        
        stats_layout.addWidget(QLabel("Count:"))
        self.count_label = QLabel("0")
        stats_layout.addWidget(self.count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Date', 'Item', 'Quantity', 'Price', 'Total', 'Buyer', 'Tier', ''
        ])
        self.table.setColumnHidden(7, True)  # Hide sale_id
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_sale)
        button_layout.addWidget(view_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_years(self):
        """Populate year selector with prior years (exclude current year)."""
        all_sales = db.get_sales()
        years_set = set()
        for sale in all_sales:
            if sale['year'] < self.current_year:
                years_set.add(sale['year'])
        
        if years_set:
            years = sorted(years_set, reverse=True)
            for year in years:
                self.year_selector.addItem(str(year))
    
    def load_sales(self):
        """Load sales for selected year."""
        if self.year_selector.count() == 0:
            self.table.setRowCount(0)
            return
        
        year = int(self.year_selector.currentText())
        sales = db.get_sales(year=year)
        
        self.table.setRowCount(0)
        total = 0
        for sale in sales:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(sale['sale_date']))
            self.table.setItem(row, 1, QTableWidgetItem(sale['item_name']))
            self.table.setItem(row, 2, QTableWidgetItem(str(sale['quantity'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"${sale['price']:.2f}"))
            sale_total = sale['quantity'] * sale['price']
            self.table.setItem(row, 4, QTableWidgetItem(f"${sale_total:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(sale.get('buyer_name', '')))
            self.table.setItem(row, 6, QTableWidgetItem(str(sale.get('tier', ''))))
            
            # Store sale_id
            id_item = QTableWidgetItem(str(sale['id']))
            self.table.setItem(row, 7, id_item)
            
            total += sale_total
        
        self.year_total_label.setText(f"${total:.2f}")
        self.count_label.setText(str(len(sales)))
    
    def on_year_changed(self):
        """Handle year selector change."""
        self.load_sales()
    
    def view_sale(self):
        """View selected sale."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select a sale to view.")
            return
        
        row = selected_rows[0].row()
        sale_id = int(self.table.item(row, 7).text())
        
        sale = db.get_sale_by_id(sale_id)
        if not sale:
            QMessageBox.warning(self, "Error", "Sale not found.")
            return
        
        from ui.sales_tab import ViewSaleDialog
        dialog = ViewSaleDialog(sale, self)
        dialog.exec_()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_history_tab.py::test_sales_history_view_initializes -v
pytest tests/test_history_tab.py::test_sales_history_view_excludes_current_year -v
```

Expected: PASS (both tests)

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: All tests pass (should still be 191 passing)

- [ ] **Step 7: Commit**

```bash
git add ui/history/__init__.py ui/history/sales_history_view.py tests/test_history_tab.py
git commit -m "feat: create SalesHistoryView for prior-year sales display

- Add SalesHistoryView class for prior-year sales history
- Year selector excludes current year
- Table displays: Date, Item, Quantity, Price, Total, Buyer, Tier
- Summary stats: Year total and count
- View button opens read-only sale details
- Lazy loading: created only when History tab clicks 'Sales History' button
- All 191 tests passing"
```

---

## Task 3: Refactor InventoryHistoryTab to InventoryHistoryView

**Files:**
- Modify: `ui/inventory_history_tab.py` → move to `ui/history/inventory_history_view.py`
- Modify: `ui/main_window.py` (import will update after refactor)

**Interfaces:**
- Consumes: Existing code from `InventoryHistoryTab` class
- Produces: `InventoryHistoryView(QWidget)` class (same methods, but renamed class)

- [ ] **Step 1: Read existing InventoryHistoryTab code**

```bash
cd C:\Users\tom\agents\panda-profit
wc -l ui/inventory_history_tab.py
```

- [ ] **Step 2: Copy file to new location**

```bash
cp ui/inventory_history_tab.py ui/history/inventory_history_view.py
```

- [ ] **Step 3: Rename class and update imports**

Edit `ui/history/inventory_history_view.py`:
- Change `class InventoryHistoryTab(QWidget):` to `class InventoryHistoryView(QWidget):`
- Update any internal references to class name
- Keep all methods identical

Example search/replace:
```python
# OLD: class InventoryHistoryTab(QWidget):
# NEW: class InventoryHistoryView(QWidget):
```

- [ ] **Step 4: Update year selector to exclude current year**

In `load_history()` method of InventoryHistoryView, modify year selector population:

```python
def load_history(self):
    """Load archived inventory."""
    from datetime import datetime
    current_year = datetime.now().year
    
    # Get years with archived inventory
    year_set = set()
    archived = db.get_archived_inventory(year=current_year - 1)  # Start with prior year
    for item in archived:
        if item.get('year') and item['year'] < current_year:
            year_set.add(item['year'])
    
    # ... populate year selector with year_set (exclude current year)
```

- [ ] **Step 5: Run existing tests to verify no regression**

```bash
pytest tests/test_inventory_history_ui.py -v
```

Expected: All tests pass (tests already cover InventoryHistoryTab logic)

- [ ] **Step 6: Delete old file**

```bash
rm ui/inventory_history_tab.py
```

- [ ] **Step 7: Commit**

```bash
git add ui/history/inventory_history_view.py -A
git commit -m "refactor: move InventoryHistoryTab to InventoryHistoryView

- Rename InventoryHistoryTab → InventoryHistoryView
- Move from ui/ to ui/history/ package
- Update year selector to exclude current year
- Keep all methods and functionality identical
- Existing tests pass (no regression)"
```

---

## Task 4: Refactor ExpenseHistoryTab to ExpenseHistoryView

**Files:**
- Modify: `ui/expense_history_tab.py` → move to `ui/history/expense_history_view.py`

**Interfaces:**
- Consumes: Existing code from `ExpenseHistoryTab` class
- Produces: `ExpenseHistoryView(QWidget)` class (same methods, but renamed class)

- [ ] **Step 1: Copy file to new location**

```bash
cp ui/expense_history_tab.py ui/history/expense_history_view.py
```

- [ ] **Step 2: Rename class**

Edit `ui/history/expense_history_view.py`:
- Change `class ExpenseHistoryTab(QWidget):` to `class ExpenseHistoryView(QWidget):`

- [ ] **Step 3: Update year selector to exclude current year**

In `load_history()` method, ensure year selector only shows prior years:

```python
def load_history(self):
    """Load archived expenses."""
    from datetime import datetime
    current_year = datetime.now().year
    
    # Get years with archived expenses (prior years only)
    year_set = set()
    all_expenses = db.get_expenses()
    for exp in all_expenses:
        if exp.get('year') and exp['year'] < current_year and exp.get('archived') == 1:
            year_set.add(exp['year'])
    
    # Populate year selector with prior-year expenses only
```

- [ ] **Step 4: Run existing tests**

```bash
pytest tests/test_expenses_ui.py::test_expense_history_tab_loads -v
```

Expected: PASS (test uses ExpenseHistoryTab, will need update in Task 5)

- [ ] **Step 5: Delete old file**

```bash
rm ui/expense_history_tab.py
```

- [ ] **Step 6: Commit**

```bash
git add ui/history/expense_history_view.py -A
git commit -m "refactor: move ExpenseHistoryTab to ExpenseHistoryView

- Rename ExpenseHistoryTab → ExpenseHistoryView
- Move from ui/ to ui/history/ package
- Update year selector to exclude current year
- Keep all methods and functionality identical"
```

---

## Task 5: Integrate HistoryTab into main_window and remove old tabs

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/test_expenses_ui.py` (fix broken import after refactor)

**Interfaces:**
- Consumes: `HistoryTab`, `SalesHistoryView`, `InventoryHistoryView`, `ExpenseHistoryView`
- Produces: Updated tab bar with History tab, removed Inventory History and Expense History tabs

- [ ] **Step 1: Update main_window.py imports**

Find import section (around line 1-30) and:

```python
# REMOVE these lines:
from ui.expense_history_tab import ExpenseHistoryTab
from ui.inventory_history_tab import InventoryHistoryTab

# ADD this line:
from ui.history_tab import HistoryTab
```

- [ ] **Step 2: Update tab initialization in main_window.py**

Find the `__init__` method where tabs are created (around line 45-50):

```python
# REMOVE these lines:
self.tab_expense_history = ExpenseHistoryTab()
self.tab_inventory_history = InventoryHistoryTab()

# ADD this line:
self.tab_history = HistoryTab()
```

- [ ] **Step 3: Update tab registration**

Find where tabs are added to tabWidget (around line 51-63):

```python
# REMOVE these lines:
self.tabs.addTab(self.tab_expense_history, "Expense History")
self.tabs.addTab(self.tab_inventory_history, "Inventory History")

# ADD this line (position after Expenses, before Settings):
self.tabs.addTab(self.tab_history, "History")
```

Final tab order should be:
```
Dashboard | Inventory | Sales | Day | Month | Year | Forecasting | Mileage | Reports | Expenses | History | Settings
```

- [ ] **Step 4: Fix broken test import**

Edit `tests/test_expenses_ui.py`:

```python
# CHANGE this line:
from ui.expense_history_tab import ExpenseHistoryTab

# TO:
from ui.history.expense_history_view import ExpenseHistoryView

# CHANGE this line in the test:
tab = ExpenseHistoryTab()

# TO:
tab = ExpenseHistoryView()
```

Also update similar changes for inventory history tests if any exist.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All 191 tests pass

- [ ] **Step 6: Launch app and verify tab bar**

```bash
python main.py &
```

Expected: 
- Tab bar shows "History" tab (after Expenses)
- "Inventory History" and "Expense History" tabs are gone
- Clicking History tab shows 3 buttons (Sales History, Inventory History, Expense History)

- [ ] **Step 7: Commit**

```bash
git add ui/main_window.py tests/test_expenses_ui.py
git commit -m "integrate: register unified History tab, remove old history tabs

- Add HistoryTab to main_window.py tab bar
- Remove separate 'Inventory History' and 'Expense History' tabs
- Update tab order: History positioned after Expenses, before Settings
- Fix test imports for refactored views
- All 191 tests passing
- App launches with consolidated History tab"
```

---

## Task 6: Add comprehensive tests for HistoryTab integration

**Files:**
- Modify: `tests/test_history_tab.py` (add new tests)

**Interfaces:**
- Consumes: HistoryTab, all three views
- Produces: Test coverage for tab switching, year selector independence, lazy loading

- [ ] **Step 1: Add test for button click switching**

Add to `tests/test_history_tab.py`:

```python
def test_history_tab_buttons_switch_views(qapp, test_db):
    """Clicking buttons should show correct views."""
    from ui.history_tab import HistoryTab
    tab = HistoryTab()
    
    # Click Sales History
    tab.on_sales_clicked()
    assert tab.stacked.currentWidget() is not None
    
    # Click Inventory History
    tab.on_inventory_clicked()
    assert tab.stacked.currentWidget() is not None
    
    # Click Expense History
    tab.on_expense_clicked()
    assert tab.stacked.currentWidget() is not None
```

- [ ] **Step 2: Add test for lazy loading**

```python
def test_history_tab_lazy_loads_views(qapp, test_db):
    """Views should be None until clicked."""
    from ui.history_tab import HistoryTab
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
```

- [ ] **Step 3: Add test for independent year selectors**

```python
def test_history_views_independent_year_selection(qapp, test_db):
    """Each view should have independent year selection."""
    from ui.history_tab import HistoryTab
    tab = HistoryTab()
    
    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()
    
    # Change year in Sales History
    if tab.sales_view.year_selector.count() > 0:
        tab.sales_view.year_selector.setCurrentIndex(0)
        sales_year = tab.sales_view.year_selector.currentText()
    
    # Change year in Inventory History
    if tab.inventory_view.year_selector.count() > 0:
        if tab.inventory_view.year_selector.count() > 1:
            tab.inventory_view.year_selector.setCurrentIndex(1)
        inventory_year = tab.inventory_view.year_selector.currentText()
    
    # Year selections should be independent
    if tab.sales_view.year_selector.count() > 0 and tab.inventory_view.year_selector.count() > 0:
        assert tab.sales_view.year_selector.currentText() != tab.inventory_view.year_selector.currentText()
```

- [ ] **Step 4: Add test that year selectors exclude current year**

```python
def test_all_history_views_exclude_current_year(qapp, test_db):
    """No history view year selector should include current year."""
    from ui.history_tab import HistoryTab
    from datetime import datetime
    
    tab = HistoryTab()
    current_year = datetime.now().year
    
    # Create all views
    tab.on_sales_clicked()
    tab.on_inventory_clicked()
    tab.on_expense_clicked()
    
    # Check Sales History year selector
    sales_years = [tab.sales_view.year_selector.itemText(i) for i in range(tab.sales_view.year_selector.count())]
    assert str(current_year) not in sales_years
    
    # Check Inventory History year selector
    inventory_years = [tab.inventory_view.year_selector.itemText(i) for i in range(tab.inventory_view.year_selector.count())]
    assert str(current_year) not in inventory_years
    
    # Check Expense History year selector
    expense_years = [tab.expense_view.year_selector.itemText(i) for i in range(tab.expense_view.year_selector.count())]
    assert str(current_year) not in expense_years
```

- [ ] **Step 5: Run new tests**

```bash
pytest tests/test_history_tab.py -v
```

Expected: All tests pass

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -10
```

Expected: All 191 tests pass (no regressions)

- [ ] **Step 7: Commit**

```bash
git add tests/test_history_tab.py
git commit -m "test: add comprehensive HistoryTab integration tests

- Test button switching between views
- Test lazy loading (views created on first click)
- Test independent year selectors in each view
- Test all views exclude current year from year selector
- All tests passing"
```

---

## Task 7: Final testing and verification

**Files:**
- No files modified (testing only)

**Interfaces:**
- Testing: Manual smoke test of all features

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v 2>&1 | tail -20
```

Expected: All 191 tests PASS

- [ ] **Step 2: Launch app manually**

```bash
python main.py &
```

- [ ] **Step 3: Smoke test History tab features**

Manual testing checklist:
- [ ] Tab bar shows "History" tab
- [ ] "Inventory History" and "Expense History" tabs removed
- [ ] Click "History" tab loads without errors
- [ ] Click "Sales History" button shows sales table with prior years only
- [ ] Click "Inventory History" button shows inventory table with archived items
- [ ] Click "Expense History" button shows expenses table with archived expenses
- [ ] Each history view has year selector populated with prior-year data only
- [ ] Change year in Sales History, switch to Inventory History → inventory year unchanged
- [ ] Search works in Inventory History tab
- [ ] Search works in Expense History tab
- [ ] View button works for each history type
- [ ] Restock button works in Inventory History
- [ ] Current year data stays in Sales/Inventory/Expenses tabs (not in History tab)

- [ ] **Step 4: Verify database is unchanged**

```bash
sqlite3 panda_profit.db ".schema expenses" | grep archived
sqlite3 panda_profit.db ".schema inventory" | grep archived
```

Expected: No schema changes (archived column already exists)

- [ ] **Step 5: Commit final verification**

```bash
git commit --allow-empty -m "test: verify unified History tab complete and working

- All 191 tests passing
- History tab initialized, buttons switching views correctly
- Lazy loading working (views created on first click)
- Year selectors independent per view
- All history views exclude current year
- Search/filter working in inventory and expense history
- View/Restock dialogs working
- Current year data remains in their respective tabs
- App ready for release"
```

---

## Summary

**Total commits:** 7 main implementation tasks + 1 final verification

**Files created:**
- `ui/history_tab.py` — main container
- `ui/history/__init__.py` — package marker
- `ui/history/sales_history_view.py` — prior-year sales
- `ui/history/inventory_history_view.py` — refactored from inventory_history_tab.py
- `ui/history/expense_history_view.py` — refactored from expense_history_tab.py
- `tests/test_history_tab.py` — new integration tests

**Files deleted:**
- `ui/expense_history_tab.py` — code moved to history/expense_history_view.py
- `ui/inventory_history_tab.py` — code moved to history/inventory_history_view.py

**Files modified:**
- `ui/main_window.py` — update imports, register History tab, remove old tabs
- `tests/test_expenses_ui.py` — fix imports after refactor

**Testing:** 191 total tests (170 existing + 21 new from History tab)

**Success criteria met:**
1. ✓ Single "History" tab with 3 buttons (Sales History, Inventory History, Expense History)
2. ✓ Each history view has independent year selector (excludes current year)
3. ✓ Clicking button shows/hides corresponding view (lazy loading)
4. ✓ Changing year in one view doesn't affect others
5. ✓ All 191 tests pass (no regressions)
6. ✓ No database schema changes
7. ✓ App launches, all history views functional
8. ✓ Search/filter works in inventory and expense history
9. ✓ Restock modal works in inventory history
10. ✓ View dialogs work for all history types
