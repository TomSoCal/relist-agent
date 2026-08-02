# Unified History Tab Implementation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate Sales History, Inventory History, and Expense History into a single "History" tab with button-based navigation between prior-year data views.

**Architecture:** Single `HistoryTab` container with three independent history view widgets (SalesHistoryView, InventoryHistoryView, ExpenseHistoryView). Each view manages its own year selector (prior years only), search/filter, and data loading. Button bar switches which view is visible.

**Tech Stack:** PyQt5 QWidget, existing database functions, soft-delete archive pattern

## Global Constraints

- All three history views show strictly prior-year data (current year excluded from year selectors)
- Current year data remains in: Sales tab (sales), Inventory tab (inventory), Expenses tab (expenses)
- Sales History filters sales data where year < current_year
- Inventory History filters to archived=1 (soft-deleted items)
- Expense History filters to archived=1 (soft-deleted expenses)
- Each history view maintains independent year selection (changing year in one view does not affect others)
- Lazy loading: views created on first button click, not on tab initialization (performance)
- No changes to database schema or existing CRUD functions
- All 191 existing tests must pass; new tests added for HistoryTab integration

---

## Files Changed

### New Files

**`ui/history_tab.py`**
- Main container widget for unified history interface
- Class: `HistoryTab(QWidget)`

**`ui/history/sales_history_view.py`**
- Prior-year sales view (extracted from sales_tab.py logic)
- Class: `SalesHistoryView(QWidget)`

**`ui/history/inventory_history_view.py`**
- Prior-year inventory view (refactored from inventory_history_tab.py)
- Class: `InventoryHistoryView(QWidget)`
- Rename existing `InventoryHistoryTab` class to `InventoryHistoryView`

**`ui/history/expense_history_view.py`**
- Prior-year expenses view (refactored from expense_history_tab.py)
- Class: `ExpenseHistoryView(QWidget)`
- Rename existing `ExpenseHistoryTab` class to `ExpenseHistoryView`

### Modified Files

**`ui/main_window.py`**
- Remove imports: `from ui.expense_history_tab import ExpenseHistoryTab` and `from ui.inventory_history_tab import InventoryHistoryTab`
- Add import: `from ui.history_tab import HistoryTab`
- Remove: `self.tab_expense_history = ExpenseHistoryTab()` and `self.tab_inventory_history = InventoryHistoryTab()`
- Remove: `self.tabs.addTab(self.tab_expense_history, "Expense History")` and `self.tabs.addTab(self.tab_inventory_history, "Inventory History")`
- Add: `self.tab_history = HistoryTab()`
- Add: `self.tabs.addTab(self.tab_history, "History")`
- Position History tab after Year tab, before Settings tab (for logical grouping)

**`ui/sales_tab.py`** (no structural change, only reference if needed for SalesHistoryView)
- No modifications to existing Sales tab
- SalesHistoryView extracts similar logic but filters to prior years only

### Deleted Files

- `ui/expense_history_tab.py` (code refactored into `ui/history/expense_history_view.py`)
- `ui/inventory_history_tab.py` (code refactored into `ui/history/inventory_history_view.py`)

---

## HistoryTab Implementation

### Class: `HistoryTab(QWidget)`

**Initialization:**
```python
class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_view = None
        self.sales_view = None
        self.inventory_view = None
        self.expense_view = None
        self.init_ui()
```

**UI Layout:**
- Top: Horizontal button layout with 3 buttons
  - Button 1: "Sales History" — show sales_view
  - Button 2: "Inventory History" — show inventory_view
  - Button 3: "Expense History" — show expense_view
- Center: QStackedWidget containing the three views (only one visible at a time)

**Methods:**
- `init_ui()` — create button bar and stacked widget
- `on_sales_clicked()` — create (if needed) and show SalesHistoryView
- `on_inventory_clicked()` — create (if needed) and show InventoryHistoryView
- `on_expense_clicked()` — create (if needed) and show ExpenseHistoryView
- `_show_view(view)` — internal: set current widget in stacked layout
- `_create_sales_view()` — lazy load SalesHistoryView
- `_create_inventory_view()` — lazy load InventoryHistoryView
- `_create_expense_view()` — lazy load ExpenseHistoryView

**Lazy Loading Pattern:**
```python
def on_sales_clicked(self):
    if self.sales_view is None:
        self.sales_view = self._create_sales_view()
        self.stacked.addWidget(self.sales_view)
    self._show_view(self.sales_view)
```

---

## SalesHistoryView Implementation

### Class: `SalesHistoryView(QWidget)`

**Data Source:** `database.get_sales(year=year)` where year < current_year

**UI Components:**
- Year selector: QComboBox populated with years 1-6 years prior (2020–2025 for current year 2026)
  - Does NOT include current year
  - Triggers `on_year_changed()` when selection changes
- Summary stats: Month total, Year total, Month count, Year count (same as Sales tab)
- Table: 8 columns
  - Date, Item, Quantity, Price, Total, Buyer, Tier, (hidden) sale_id
  - Data populated from `get_sales(year)` result
  - Sorted by date DESC
- View button: Opens read-only ViewSaleDialog (existing dialog from sales_tab)

**Methods:**
- `load_sales()` — fetch sales for selected year, populate table
- `on_year_changed()` — handle year selector change, call load_sales()
- `view_sale()` — open ViewSaleDialog for selected row
- `_update_stats()` — calculate and display month/year totals

---

## InventoryHistoryView Implementation

### Class: `InventoryHistoryView(QWidget)`

**Refactored from:** `InventoryHistoryTab`

**Data Source:** `database.get_archived_inventory(year=year)` where archived=1

**UI Components:**
- Year selector: QComboBox populated only with years containing archived inventory
  - Excludes current year (only shows prior-year archives)
  - Triggers `on_year_changed()` when selection changes
- Search bar: QLineEdit for searching across all fields
  - Real-time filtering (connected to `on_search()`)
- Table: 7 columns
  - SKU, Item, Quantity, Cost, Total, Added Date, (hidden) inventory_id
  - Data populated from `get_archived_inventory(year, search_query)`
- Buttons: View, Restock
  - View: Opens ViewItemDialog (read-only)
  - Restock: Opens RestockModal to create new inventory entry with updated SKU

**Methods:**
- `load_history()` — fetch archived inventory for selected year, populate table
- `on_year_changed()` — handle year selector change, call load_history()
- `on_search()` — filter table by search query in real-time
- `view_item()` — open ViewItemDialog
- `restock_item()` — open RestockModal

**Key Constraint:** Year selector only populated with years that have archived inventory entries (performance + clarity).

---

## ExpenseHistoryView Implementation

### Class: `ExpenseHistoryView(QWidget)`

**Refactored from:** `ExpenseHistoryTab`

**Data Source:** `database.get_archived_expenses(year=year, search_query=None)` where archived=1

**UI Components:**
- Year selector: QComboBox populated only with years containing archived expenses
  - Excludes current year (only shows prior-year archives)
  - Triggers `on_year_changed()` when selection changes
- Search bar: QLineEdit for searching across 7 fields
  - Real-time filtering (connected to `on_search()`)
  - Searches: ID, date, category, amount, invoice, description, notes
- Table: 8 columns
  - Date, Category, Amount, Invoice #, Description, Notes, Receipt, (hidden) expense_id
  - Data populated from `get_archived_expenses(year, search_query)`
- View button: Opens ViewExpenseDialog (read-only)

**Methods:**
- `load_history()` — fetch archived expenses for selected year, populate table
- `on_year_changed()` — handle year selector change, call load_history()
- `on_search()` — filter table by search query across all fields
- `view_expense()` — open ViewExpenseDialog

**Key Constraint:** Year selector only populated with years that have archived expenses.

---

## Data Flow

1. **User clicks History tab** → HistoryTab initializes, displays button bar, no views created yet
2. **User clicks "Sales History" button** → SalesHistoryView created (lazy), year selector populated with prior years, sales table loaded for most recent prior year
3. **User changes year in Sales History** → SalesHistoryView reloads sales for new year, InventoryHistoryView/ExpenseHistoryView unaffected
4. **User clicks "Expense History" button** → ExpenseHistoryView created (lazy), year selector populated independently
5. **Each view manages its own state:** year selection, search query, visible table data

---

## Database Layer (No Changes)

Existing functions already support prior-year filtering:

- `database.get_sales(year=None)` — pass year parameter to filter
- `database.get_archived_inventory(year, search_query=None)` — already exists
- `database.get_archived_expenses(year, search_query=None)` — already exists
- Archive pattern: `archived=1` column flags prior-year data for all three tables

No new database functions or schema changes required.

---

## Testing

### Unit Tests (`tests/test_history_tab.py`)

- Test HistoryTab initializes without errors
- Test button clicks create and show correct views
- Test lazy loading: views not created on init, created on first click
- Test year selectors are independent (changing year in one view doesn't affect others)
- Test SalesHistoryView loads prior-year sales correctly
- Test InventoryHistoryView loads archived inventory correctly
- Test ExpenseHistoryView loads archived expenses correctly
- Test search filtering in InventoryHistoryView and ExpenseHistoryView
- Test view/restock/edit buttons work for each view

### Integration Tests

- Test main_window.py: History tab registered, "Inventory History" and "Expense History" tabs removed
- Test all 191 existing tests pass (no regressions)
- Test end-to-end: switch between history views, change years independently, use search

---

## Integration with Main Window

**Tab Bar Before:**
```
Dashboard | Inventory | Inventory History | Sales | Day | Month | Year | Forecasting | Mileage | Reports | Expenses | Expense History | Settings
```

**Tab Bar After:**
```
Dashboard | Inventory | Sales | Day | Month | Year | Forecasting | Mileage | Reports | Expenses | History | Settings
```

**Changes:**
- Remove "Inventory History" tab
- Remove "Expense History" tab
- Add "History" tab (positioned after Expenses, before Settings)

---

## Success Criteria

1. ✓ Single "History" tab with 3 buttons (Sales History, Inventory History, Expense History)
2. ✓ Each history view has independent year selector (excludes current year)
3. ✓ Clicking button shows/hides corresponding view
4. ✓ Changing year in one view doesn't affect others
5. ✓ Lazy loading: views created on first click
6. ✓ All 191 existing tests pass
7. ✓ New tests verify HistoryTab integration
8. ✓ No database schema changes
9. ✓ App launches, all history views functional
10. ✓ Search/filter works in inventory and expense history views
11. ✓ Restock modal works in inventory history
12. ✓ View dialogs work for sales, inventory, expense history

---

## Notes

- Prior-year data defined as: year < current_year (excludes current year from History tab)
- Current year Sales/Inventory/Expenses remain in their respective tabs
- Lazy loading improves startup time: no history views loaded until user explicitly clicks History tab
- Year selectors dynamically populated: only show years with data (no empty years in dropdown)
