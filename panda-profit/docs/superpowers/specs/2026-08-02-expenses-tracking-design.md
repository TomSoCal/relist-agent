# Expenses Tracking Feature — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add comprehensive expense tracking with year-based filtering, historical archive, and receipt management for tax deduction calculations and year-over-year metrics.

**Architecture:** Two-tab system (current Expenses + historical Expense History) using soft-delete archive pattern. Current-year expenses fully editable; prior-year expenses auto-archived and searchable for metrics. Receipt files stored with relative paths and viewable on-demand.

**Tech Stack:** PyQt5 QTableWidget, QDialog, QFileDialog, SQLite soft-delete with archived flag, year-boundary auto-archive at app startup.

## Global Constraints

- Predefined categories (non-deletable): Storage, Business Subscriptions, Home Office, Shipping Supplies, Misc Expense
- Users can add unlimited custom categories
- Expenses table uses `archived INTEGER DEFAULT 0` soft-delete flag (no data loss)
- Prior-year expenses auto-archived on app startup via `archive_expenses_for_year(year)`
- Current-year only write protection (can only add/edit/delete expenses from current year)
- Receipt uploads optional; stored with relative paths in receipt_path field
- Year filtering matches Mileage tab pattern (QComboBox, dynamically populated)
- Test isolation via conftest.py module-scoped fixture (like inventory archive feature)

---

## Feature Components

### 1. Database Schema

**Expenses Table (Enhanced)**
```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    expense_date TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    receipt_path TEXT DEFAULT '',
    archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES expense_categories (id)
);
CREATE INDEX idx_expenses_archived ON expenses(archived, year);
```

**Expense Categories Table (Existing)**
```sql
CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    is_custom INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Predefined Categories** (seed on first app launch):
1. Storage (is_custom=0)
2. Business Subscriptions (is_custom=0)
3. Home Office (is_custom=0)
4. Shipping Supplies (is_custom=0)
5. Misc Expense (is_custom=0)

### 2. Database Functions (database.py)

**Core Functions:**

- `get_or_create_expense_categories()` — Seed 5 predefined categories if table empty
- `add_expense_category(name)` — Create custom category, return category_id; reject duplicates
- `get_expense_categories()` — Return all categories (predefined + custom), sorted by name
- `add_mileage_trip(year, expense_date, category_id, amount, description, notes, receipt_path)` — Insert expense, return expense_id; validate category_id, year is current
- `get_expenses(year=None, archived=0)` — Fetch expenses by year and archive status, ordered by date DESC; year=None = current year
- `update_expense(expense_id, expense_date, category_id, amount, description, notes, receipt_path)` — Update expense; validate year is current
- `delete_expense(expense_id)` — Delete expense; reject if not current year
- `get_archived_expenses(year, search_query=None)` — Search archived expenses by: expense_id, category name, description, amount range, date range
- `archive_expenses_for_year(year)` — Mark expenses with archived=0 and year < current_year as archived=1
- `check_and_archive_year_transition()` — Detect year boundary, auto-archive prior year; call at app startup
- `get_expense_totals(year=None)` — Return (total_this_month, total_this_year) for dashboard

**Receipt Handling:**
- Receipt files stored in `<app-data-folder>/receipts/` with structure: `receipts/YYYY/MM/expense-{id}-{filename}`
- `receipt_path` field stores relative path: `YYYY/MM/expense-{id}-{filename}`
- Validation: only accept common formats (.pdf, .jpg, .png, .gif)

### 3. UI Layer

#### Tab 1: Expenses (Current Year)

**File:** `ui/expenses_tab.py` (NEW)

**Components:**
- Year selector (QComboBox, dynamically populated from database)
- Summary stats (3 boxes):
  - Total Expenses (This Month)
  - Total Expenses (This Year)
  - Expense Count (This Month)
- Table (8 visible columns, 1 hidden):
  1. Select (QCheckBox)
  2. Date (YYYY-MM-DD)
  3. Category (category name)
  4. Amount (currency format: $#,##0.00)
  5. Description (text)
  6. Notes (text, truncated in table)
  7. Receipt (indicator: "Yes" or "—")
  8. (Hidden) expense_id
- Buttons: Add Expense, Edit, View, Delete Selected

**Functionality:**
- Load expenses for selected year (archive=0 only)
- Recalculate totals on load
- Year selector change → reload expenses + recalc totals
- Add Expense → AddExpenseDialog → insert to DB → reload table
- Edit → requires 1 row selected → EditExpenseDialog → update DB → reload table
- View → requires 1 row selected → ViewExpenseDialog (read-only, shows receipt if attached)
- Delete Selected → multi-select via checkboxes → confirmation dialog → bulk delete → reload table
- Year-based write protection: reject edit/delete if expense.year != current_year

**Table Formatting:**
- Header row: dark theme primary color background, white bold text
- Alternating white/gray rows
- Currency column right-aligned
- Checkbox column width: 40px
- Date/Category/Amount fixed widths
- Description/Notes dynamic
- Receipt column: 60px, center-aligned

#### Tab 2: Expense History (Archived Years)

**File:** `ui/expense_history_tab.py` (NEW)

**Components:**
- Year selector (QComboBox, loads only years with archived expenses)
- Search bar (QLineEdit, real-time filtering):
  - Search by: Expense ID, category name, description, amount
- Filter controls (optional, MVP can skip):
  - Date range picker
  - Amount range slider
- Results table (same 8 columns as main Expenses tab):
  1. Select (disabled in history)
  2. Date
  3. Category
  4. Amount
  5. Description
  6. Notes
  7. Receipt
  8. (Hidden) expense_id
- Buttons: View, Copy to Current Year (optional future feature)

**Functionality:**
- Load archived expenses (archive=1) for selected year
- Real-time search filters results on-the-fly
- View button → ViewExpenseDialog (read-only, shows receipt)
- No edit/delete (prior-year data immutable)
- Copy to Current Year (future): copy archived expense to active with new SKU-like mechanism

#### Dialogs

**AddExpenseDialog** (QDialog)
- Date picker (QDateEdit, default today)
- Category dropdown (QComboBox, all categories + "Add New Category..." option)
- Amount (QDoubleSpinBox, range 0.00–99,999.99, 2 decimals)
- Description (QLineEdit, max 255 chars)
- Notes (QTextEdit, max 1000 chars)
- Receipt upload (QPushButton "Browse", QLabel showing filename)
- Save/Cancel buttons
- Validation: amount > 0, category selected, date valid
- On Save: insert to DB, close dialog

**EditExpenseDialog** (QDialog)
- Same fields as AddExpenseDialog, pre-populated with existing data
- Receipt section shows current receipt (if any) with "Replace" / "Clear" options
- Current-year-only: reject if expense.year != current_year
- On Save: update DB, close dialog

**ViewExpenseDialog** (QDialog, read-only)
- All fields displayed as labels (non-editable)
- Receipt section:
  - If no receipt: "No receipt attached"
  - If receipt: show file path + "Open Receipt" button (opens file with default app)
- Close button

**AddCategoryDialog** (QDialog)
- Text input (QLineEdit) for new category name
- Validation: non-empty, no duplicates
- Save/Cancel buttons
- On Save: insert to DB, update dropdown in parent dialog

### 4. Integration Points

**main.py:**
- Call `check_and_archive_year_transition()` at startup (after `init_db()`)
- Call `get_or_create_expense_categories()` at startup to seed predefined categories

**main_window.py:**
- Register ExpensesTab and ExpenseHistoryTab in tab widget
- Add tabs to main window after InventoryHistoryTab

**dashboard_tab.py (future):**
- Add expense widgets: "Total Expenses (YTD)", "Largest Expense Category", trending chart

---

## Testing Strategy

**Unit Tests** (`tests/test_expenses.py`):
- Archive marks prior-year expenses, doesn't mark current-year
- Get archived expenses returns only archived
- Search filters by expense_id, category, description
- Add/Update/Delete expenses works with validation
- Current-year-only write protection
- Predefined categories auto-seed
- Custom category creation

**UI Tests** (`tests/test_expenses_ui.py`):
- ExpensesTab loads current-year expenses
- Summary stats calculate correctly
- Add/Edit/Delete workflows
- Receipt file handling
- Year selector filters correctly

**Test Isolation:**
- Use conftest.py module-scoped fixture (restore DB_PATH between test modules)
- UI tests use function-scoped test_db fixture (route to tests/test_expenses_ui.db)

---

## Migration Plan

1. Add `archived INTEGER DEFAULT 0` column to existing expenses table
2. Create index on (archived, year)
3. Seed predefined categories
4. No data loss (soft-delete only)

---

## Success Criteria

- [x] Current-year expenses fully editable (add/edit/delete)
- [x] Prior-year expenses auto-archived and searchable
- [x] Receipt upload/view works
- [x] Year-based filtering works
- [x] Summary stats accurate
- [x] 15+ tests passing (unit + UI)
- [x] No regressions in existing 172 tests
- [ ] Production ready (v0.6.0-expenses tag)

