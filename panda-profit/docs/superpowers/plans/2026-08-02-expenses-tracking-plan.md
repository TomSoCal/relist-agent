# Expenses Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete expenses tracking system with current-year editing, year-based archive, receipt upload/view, and historical search across all expense fields.

**Architecture:** Two-tab UI (Expenses + Expense History) using soft-delete archive pattern. Database stores all expenses with archived flag; current year fully editable; prior years auto-archived at startup. Receipt files stored in APPDATA/receipts/ with relative paths. Search is cross-field and case-insensitive.

**Tech Stack:** PyQt5 (QTableWidget, QDialog, QFileDialog), SQLite (soft-delete, indexed archive), file I/O (receipts), parameterized SQL.

## Global Constraints

- Predefined categories (5): Storage, Business Subscriptions, Home Office, Shipping Supplies, Misc Expense
- Users can add unlimited custom categories
- expenses table uses `archived INTEGER DEFAULT 0` soft-delete flag (no data loss)
- Prior-year expenses auto-archived on app startup via `archive_expenses_for_year(year)`
- Current-year write protection: only add/edit/delete current year expenses
- Receipt uploads optional; stored in `<APPDATA>/receipts/YYYY/MM/expense-{id}-{filename}`
- invoice_number field optional (max 50 chars)
- Test isolation via conftest.py module-scoped fixture
- All 172 existing tests must continue passing

---

## File Structure

**Database layer:**
- Modify: `database.py` — Add schema migration, category seed, archive functions, CRUD functions

**UI layer:**
- Create: `ui/expenses_tab.py` — Main expenses tab (current year, editable)
- Create: `ui/expense_history_tab.py` — Historical expenses tab (archived, searchable)
- Create: `ui/expense_dialogs.py` — Add/Edit/View dialogs, category manager
- Modify: `ui/main_window.py` — Register new tabs

**Integration:**
- Modify: `main.py` — Call archive and seed functions at startup

**Testing:**
- Create: `tests/test_expenses.py` — Unit tests for database functions (archive, CRUD, categories)
- Create: `tests/test_expenses_ui.py` — UI tests for tabs and dialogs

---

### Task 1: Database Schema Migration & Seed Functions

**Files:**
- Modify: `database.py`
- Test: `tests/test_expenses.py` (new file, tests in this task)

**Interfaces:**
- Produces:
  - `get_or_create_expense_categories()` → None (side effect: seed if empty)
  - `add_expense_category(name: str) → int` (category_id)
  - `get_expense_categories() → list[dict]` ({id, name, is_custom})
  - `archive_expenses_for_year(year: int) → int` (count archived)
  - `check_and_archive_year_transition() → None` (side effect)

- [ ] **Step 1: Add `archived` and `invoice_number` columns to expenses table**

Open `database.py`, locate `CREATE TABLE IF NOT EXISTS expenses`. Update schema:

```python
c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        expense_date TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        invoice_number TEXT DEFAULT '',
        description TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        receipt_path TEXT DEFAULT '',
        archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES expense_categories (id)
    )
''')

c.execute('CREATE INDEX IF NOT EXISTS idx_expenses_archived ON expenses(archived, year)')
```

- [ ] **Step 2: Add seed function for predefined categories**

```python
def get_or_create_expense_categories():
    """Seed predefined expense categories if table is empty."""
    c = get_connection().cursor()
    c.execute('SELECT COUNT(*) FROM expense_categories')
    if c.fetchone()[0] == 0:
        categories = [
            ('Storage', 0),
            ('Business Subscriptions', 0),
            ('Home Office', 0),
            ('Shipping Supplies', 0),
            ('Misc Expense', 0),
        ]
        for name, is_custom in categories:
            c.execute('INSERT INTO expense_categories (name, is_custom) VALUES (?, ?)',
                      (name, is_custom))
        get_connection().commit()
```

- [ ] **Step 3: Add category management functions**

```python
def add_expense_category(name):
    """Add custom expense category. Return category_id or raise on duplicate."""
    c = get_connection().cursor()
    try:
        c.execute('INSERT INTO expense_categories (name, is_custom) VALUES (?, ?)',
                  (name.strip(), 1))
        get_connection().commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Category '{name}' already exists")

def get_expense_categories():
    """Return all categories (predefined + custom), sorted by name."""
    c = get_connection().cursor()
    c.execute('SELECT id, name, is_custom FROM expense_categories ORDER BY name')
    return [{'id': row[0], 'name': row[1], 'is_custom': row[2]} for row in c.fetchall()]
```

- [ ] **Step 4: Add archive functions**

```python
def archive_expenses_for_year(year):
    """Mark expenses with archived=0 and year < given_year as archived=1. Return count."""
    c = get_connection().cursor()
    c.execute('UPDATE expenses SET archived=1 WHERE archived=0 AND year < ? AND amount IS NOT NULL',
              (year,))
    get_connection().commit()
    return c.rowcount

def check_and_archive_year_transition():
    """Detect year boundary, auto-archive prior year expenses."""
    current_year = datetime.now().year
    archive_expenses_for_year(current_year)
```

- [ ] **Step 5: Write tests for schema, seed, and archive**

Create `tests/test_expenses.py`:

```python
import pytest
import sqlite3
from datetime import datetime
from database import (
    get_connection, init_db, get_or_create_expense_categories,
    add_expense_category, get_expense_categories, archive_expenses_for_year
)

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to temporary database."""
    test_db_path = str(tmp_path / 'test_expenses.db')
    monkeypatch.setattr('database.DB_PATH', test_db_path)
    init_db()
    yield
    # Cleanup: close and remove
    import os
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_seed_predefined_categories(test_db):
    """Test predefined categories are seeded."""
    get_or_create_expense_categories()
    categories = get_expense_categories()
    names = [c['name'] for c in categories]
    assert 'Storage' in names
    assert 'Business Subscriptions' in names
    assert len(categories) == 5

def test_add_custom_category(test_db):
    """Test adding custom category."""
    get_or_create_expense_categories()
    cat_id = add_expense_category('Custom Tools')
    categories = get_expense_categories()
    assert any(c['name'] == 'Custom Tools' and c['is_custom'] == 1 for c in categories)

def test_add_duplicate_category_raises(test_db):
    """Test duplicate category name raises error."""
    get_or_create_expense_categories()
    add_expense_category('MyCategory')
    with pytest.raises(ValueError):
        add_expense_category('MyCategory')

def test_archive_expenses_for_year(test_db):
    """Test prior-year expenses are archived."""
    get_or_create_expense_categories()
    c = get_connection().cursor()
    
    # Add current year and prior year expenses
    current_year = datetime.now().year
    prior_year = current_year - 1
    
    c.execute('INSERT INTO expenses (year, expense_date, category_id, amount, archived) VALUES (?, ?, ?, ?, ?)',
              (prior_year, f'{prior_year}-01-01', 1, 100.00, 0))
    c.execute('INSERT INTO expenses (year, expense_date, category_id, amount, archived) VALUES (?, ?, ?, ?, ?)',
              (current_year, f'{current_year}-01-01', 1, 200.00, 0))
    get_connection().commit()
    
    # Archive prior year
    count = archive_expenses_for_year(current_year)
    assert count == 1
    
    # Verify prior year archived, current year not
    c.execute('SELECT archived FROM expenses WHERE year=?', (prior_year,))
    assert c.fetchone()[0] == 1
    c.execute('SELECT archived FROM expenses WHERE year=?', (current_year,))
    assert c.fetchone()[0] == 0
```

- [ ] **Step 6: Run tests to verify pass**

```bash
pytest tests/test_expenses.py -v
```

Expected: PASS (all 5 tests)

- [ ] **Step 7: Commit**

```bash
git add database.py tests/test_expenses.py
git commit -m "feat: expenses schema, categories, archive functions

- Add archived flag and invoice_number to expenses table
- Create index on (archived, year) for performance
- Seed predefined categories: Storage, Subscriptions, Home Office, Shipping, Misc
- add_expense_category() for custom categories with duplicate check
- archive_expenses_for_year() and check_and_archive_year_transition()
- 5 unit tests for categories and archival
- All 172 existing tests still pass"
```

---

### Task 2: Database CRUD Functions

**Files:**
- Modify: `database.py`
- Modify: `tests/test_expenses.py` (add tests)

**Interfaces:**
- Consumes: `add_expense_category()`, `get_expense_categories()` (from Task 1)
- Produces:
  - `add_expense(year: int, expense_date: str, category_id: int, amount: float, invoice_number: str, description: str, notes: str, receipt_path: str) → int` (expense_id)
  - `get_expenses(year: int = None, archived: int = 0) → list[dict]` (expense records)
  - `update_expense(expense_id: int, expense_date: str, category_id: int, amount: float, invoice_number: str, description: str, notes: str, receipt_path: str) → int` (rows affected)
  - `delete_expense(expense_id: int) → int` (rows affected)
  - `get_expense_by_id(expense_id: int) → dict` (single expense record)
  - `get_archived_expenses(year: int, search_query: str = None) → list[dict]` (search results)
  - `get_expense_totals(year: int = None) → tuple[float, float, int, int]` (month_total, year_total, month_count, year_count)

- [ ] **Step 1: Write failing tests for add_expense**

Add to `tests/test_expenses.py`:

```python
def test_add_expense(test_db):
    """Test adding expense returns id."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    exp_id = add_expense(
        year=current_year,
        expense_date=f'{current_year}-08-01',
        category_id=1,
        amount=50.00,
        invoice_number='INV-001',
        description='Office supplies',
        notes='Pens and paper',
        receipt_path=''
    )
    assert exp_id > 0

def test_get_expenses(test_db):
    """Test fetching expenses."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Supplies', '', '')
    
    expenses = get_expenses(year=current_year)
    assert len(expenses) == 1
    assert expenses[0]['amount'] == 50.00
    assert expenses[0]['archived'] == 0

def test_get_expenses_archived_only(test_db):
    """Test fetching archived expenses."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1
    
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Current', '', '')
    exp_id = add_expense(prior_year, f'{prior_year}-08-01', 1, 100.00, '', 'Prior', '', '')
    
    # Archive prior year
    c = get_connection().cursor()
    c.execute('UPDATE expenses SET archived=1 WHERE id=?', (exp_id,))
    get_connection().commit()
    
    archived = get_expenses(year=prior_year, archived=1)
    assert len(archived) == 1
    assert archived[0]['amount'] == 100.00

def test_update_expense(test_db):
    """Test updating expense."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    exp_id = add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Old', '', '')
    
    rows = update_expense(exp_id, f'{current_year}-08-02', 2, 75.00, 'INV-002', 'New', 'Notes', '')
    assert rows == 1
    
    exp = get_expense_by_id(exp_id)
    assert exp['amount'] == 75.00
    assert exp['description'] == 'New'

def test_delete_expense(test_db):
    """Test deleting expense."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    exp_id = add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Test', '', '')
    
    rows = delete_expense(exp_id)
    assert rows == 1
    
    exp = get_expense_by_id(exp_id)
    assert exp is None

def test_year_write_protection_edit(test_db):
    """Test can't edit prior-year expense."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1
    
    exp_id = add_expense(prior_year, f'{prior_year}-08-01', 1, 50.00, '', 'Prior', '', '')
    
    # Try to update prior year (should fail or be ignored per implementation)
    with pytest.raises(ValueError):
        update_expense(exp_id, f'{prior_year}-08-02', 1, 75.00, '', 'New', '', '')

def test_get_expense_totals(test_db):
    """Test expense total calculations."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    add_expense(current_year, f'{current_year}-{current_month:02d}-01', 1, 50.00, '', '', '', '')
    add_expense(current_year, f'{current_year}-{current_month:02d}-02', 1, 30.00, '', '', '', '')
    add_expense(current_year, f'{current_year}-01-01', 1, 100.00, '', '', '', '')  # Different month
    
    month_total, year_total, month_count, year_count = get_expense_totals(year=current_year)
    assert month_total == 80.00
    assert year_total == 180.00
    assert month_count == 2
    assert year_count == 3
```

- [ ] **Step 2: Implement CRUD functions**

Add to `database.py`:

```python
def add_expense(year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path):
    """Insert expense. Validate category exists and year is current."""
    c = get_connection().cursor()
    
    # Validate category exists
    c.execute('SELECT id FROM expense_categories WHERE id=?', (category_id,))
    if not c.fetchone():
        raise ValueError(f"Category {category_id} not found")
    
    # Validate year is current
    if year != datetime.now().year:
        raise ValueError(f"Can only add expenses for current year")
    
    c.execute('''
        INSERT INTO expenses (year, expense_date, category_id, amount, invoice_number, description, notes, receipt_path, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (year, expense_date, category_id, amount, invoice_number or '', description, notes, receipt_path or ''))
    get_connection().commit()
    return c.lastrowid

def get_expenses(year=None, archived=0):
    """Fetch expenses by year and archive status, ordered by date DESC."""
    if year is None:
        year = datetime.now().year
    
    c = get_connection().cursor()
    c.execute('''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.year=? AND e.archived=?
        ORDER BY e.expense_date DESC
    ''', (year, archived))
    
    return [
        {
            'id': row[0],
            'year': row[1],
            'expense_date': row[2],
            'category_id': row[3],
            'category_name': row[4],
            'amount': row[5],
            'invoice_number': row[6],
            'description': row[7],
            'notes': row[8],
            'receipt_path': row[9],
            'archived': row[10]
        }
        for row in c.fetchall()
    ]

def get_expense_by_id(expense_id):
    """Fetch single expense by ID."""
    c = get_connection().cursor()
    c.execute('''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.id=?
    ''', (expense_id,))
    
    row = c.fetchone()
    if not row:
        return None
    
    return {
        'id': row[0],
        'year': row[1],
        'expense_date': row[2],
        'category_id': row[3],
        'category_name': row[4],
        'amount': row[5],
        'invoice_number': row[6],
        'description': row[7],
        'notes': row[8],
        'receipt_path': row[9],
        'archived': row[10]
    }

def update_expense(expense_id, expense_date, category_id, amount, invoice_number, description, notes, receipt_path):
    """Update expense. Only allow if current year."""
    c = get_connection().cursor()
    
    # Get expense year
    c.execute('SELECT year FROM expenses WHERE id=?', (expense_id,))
    row = c.fetchone()
    if not row:
        raise ValueError(f"Expense {expense_id} not found")
    
    exp_year = row[0]
    if exp_year != datetime.now().year:
        raise ValueError(f"Can only edit expenses from current year")
    
    c.execute('''
        UPDATE expenses
        SET expense_date=?, category_id=?, amount=?, invoice_number=?, description=?, notes=?, receipt_path=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (expense_date, category_id, amount, invoice_number or '', description, notes, receipt_path or '', expense_id))
    get_connection().commit()
    return c.rowcount

def delete_expense(expense_id):
    """Delete expense. Only allow if current year."""
    c = get_connection().cursor()
    
    # Get expense year
    c.execute('SELECT year FROM expenses WHERE id=?', (expense_id,))
    row = c.fetchone()
    if not row:
        return 0
    
    exp_year = row[0]
    if exp_year != datetime.now().year:
        raise ValueError(f"Can only delete expenses from current year")
    
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    get_connection().commit()
    return c.rowcount

def get_archived_expenses(year, search_query=None):
    """Search archived expenses by any field (case-insensitive, partial match)."""
    c = get_connection().cursor()
    
    query = '''
        SELECT e.id, e.year, e.expense_date, e.category_id, ec.name, e.amount, e.invoice_number, e.description, e.notes, e.receipt_path, e.archived
        FROM expenses e
        JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.year=? AND e.archived=1
    '''
    params = [year]
    
    if search_query:
        search_term = f'%{search_query.lower()}%'
        query += '''
            AND (
                CAST(e.id AS TEXT) LIKE ?
                OR DATE(e.expense_date) LIKE ?
                OR LOWER(ec.name) LIKE ?
                OR CAST(e.amount AS TEXT) LIKE ?
                OR LOWER(e.invoice_number) LIKE ?
                OR LOWER(e.description) LIKE ?
                OR LOWER(e.notes) LIKE ?
            )
        '''
        params.extend([search_term] * 7)
    
    query += ' ORDER BY e.expense_date DESC'
    c.execute(query, params)
    
    return [
        {
            'id': row[0],
            'year': row[1],
            'expense_date': row[2],
            'category_id': row[3],
            'category_name': row[4],
            'amount': row[5],
            'invoice_number': row[6],
            'description': row[7],
            'notes': row[8],
            'receipt_path': row[9],
            'archived': row[10]
        }
        for row in c.fetchall()
    ]

def get_expense_totals(year=None):
    """Return (month_total, year_total, month_count, year_count) for current month and year."""
    if year is None:
        year = datetime.now().year
    
    current_month = datetime.now().month
    c = get_connection().cursor()
    
    # Month total
    c.execute('''
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
        WHERE year=? AND CAST(strftime('%m', expense_date) AS INTEGER)=? AND archived=0
    ''', (year, current_month))
    month_total, month_count = c.fetchone()
    
    # Year total
    c.execute('''
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
        WHERE year=? AND archived=0
    ''', (year,))
    year_total, year_count = c.fetchone()
    
    return float(month_total), float(year_total), int(month_count), int(year_count)
```

- [ ] **Step 3: Run tests to verify pass**

```bash
pytest tests/test_expenses.py -v
```

Expected: PASS (all tests including new ones, 10+ total)

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -q
```

Expected: 172+ existing tests still PASS

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_expenses.py
git commit -m "feat: expenses CRUD and search functions

- add_expense() with year validation (current year only)
- get_expenses() by year and archive status, ordered by date DESC
- update_expense() with year write protection
- delete_expense() with year write protection
- get_expense_by_id() for single record fetch
- get_archived_expenses() with cross-field search (ID, date, category, amount, invoice, desc, notes)
- get_expense_totals() for month/year summary stats
- 10+ unit tests covering all CRUD operations
- All 172 existing tests still pass"
```

---

### Task 3: ExpensesTab UI (Current Year)

**Files:**
- Create: `ui/expenses_tab.py`
- Modify: `tests/test_expenses_ui.py` (new file, UI tests)

**Interfaces:**
- Consumes: `get_expenses()`, `add_expense()`, `update_expense()`, `delete_expense()`, `get_expense_categories()`, `get_expense_totals()` (from Tasks 1-2)
- Produces: `ExpensesTab` class (QWidget) with public methods:
  - `load_expenses()` → None
  - Used by main_window.py to register as tab

- [ ] **Step 1: Write minimal failing test**

Create `tests/test_expenses_ui.py`:

```python
import pytest
from PyQt5.QtWidgets import QApplication, QTableWidget
from ui.expenses_tab import ExpensesTab
from database import init_db, get_or_create_expense_categories, add_expense
from datetime import datetime

@pytest.fixture(scope='module')
def qapp():
    """Provide QApplication for all tests."""
    return QApplication.instance() or QApplication([])

@pytest.fixture(scope='function')
def test_db(monkeypatch, tmp_path):
    """Route tests to temporary database."""
    test_db_path = str(tmp_path / 'test_expenses_ui.db')
    monkeypatch.setattr('database.DB_PATH', test_db_path)
    init_db()
    yield
    import os
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_expenses_tab_loads(qapp, test_db):
    """Test ExpensesTab initializes and loads."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', 'Test', '', '')
    
    tab = ExpensesTab()
    tab.load_expenses()
    
    assert tab.table.rowCount() > 0
    assert tab.table.columnCount() == 9  # Select, Date, Category, Amount, Invoice, Desc, Notes, Receipt, (hidden id)

def test_expenses_tab_summary_stats(qapp, test_db):
    """Test summary stats display correct totals."""
    get_or_create_expense_categories()
    current_year = datetime.now().year
    add_expense(current_year, f'{current_year}-08-01', 1, 50.00, '', '', '', '')
    add_expense(current_year, f'{current_year}-08-02', 1, 30.00, '', '', '', '')
    
    tab = ExpensesTab()
    tab.load_expenses()
    
    # Stats should show totals (verify via labels or public properties)
    assert '80' in tab.total_label.text()  # Month total
```

- [ ] **Step 2: Implement ExpensesTab**

Create `ui/expenses_tab.py`:

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import database as db

class ExpensesTab(QWidget):
    """Tab for viewing and managing current-year expenses."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_expenses()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)
        year_layout.addStretch()
        layout.addLayout(year_layout)
        
        # Summary stats
        stats_layout = QHBoxLayout()
        
        self.month_label = QLabel("Total (This Month): $0.00")
        self.month_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.month_label)
        
        self.total_label = QLabel("Total (This Year): $0.00")
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_label)
        
        self.count_label = QLabel("Count (This Month): 0")
        self.count_label.setFont(QFont("Arial", 10))
        stats_layout.addWidget(self.count_label)
        
        layout.addLayout(stats_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Select', 'Date', 'Category', 'Amount', 'Invoice #', 'Description', 'Notes', 'Receipt', ''
        ])
        self.table.setColumnHidden(8, True)  # Hide expense_id column
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Expense")
        add_btn.clicked.connect(self.add_expense)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_expense)
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_expense)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("background-color: #c41e3a; color: white;")
        delete_btn.clicked.connect(self.delete_selected)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(view_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_expenses(self):
        """Load expenses for selected year."""
        year = int(self.year_selector.currentText()) if self.year_selector.count() > 0 else self.current_year
        expenses = db.get_expenses(year=year, archived=0)
        
        self.table.setRowCount(0)
        for expense in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Checkbox
            checkbox = QCheckBox()
            self.table.setCellWidget(row, 0, checkbox)
            
            # Columns
            self.table.setItem(row, 1, QTableWidgetItem(expense['expense_date']))
            self.table.setItem(row, 2, QTableWidgetItem(expense['category_name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"${expense['amount']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(expense['invoice_number'] or ''))
            self.table.setItem(row, 5, QTableWidgetItem(expense['description']))
            self.table.setItem(row, 6, QTableWidgetItem(expense['notes']))
            receipt_text = 'Yes' if expense['receipt_path'] else '—'
            self.table.setItem(row, 7, QTableWidgetItem(receipt_text))
            
            # Store expense_id
            id_item = QTableWidgetItem(str(expense['id']))
            self.table.setItem(row, 8, id_item)
        
        # Update year selector
        all_years = list(range(datetime.now().year - 5, datetime.now().year + 1))
        current_text = self.year_selector.currentText()
        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        for y in sorted(all_years, reverse=True):
            self.year_selector.addItem(str(y))
        self.year_selector.setCurrentText(current_text or str(self.current_year))
        self.year_selector.blockSignals(False)
        
        # Update summary stats
        month_total, year_total, month_count, year_count = db.get_expense_totals(year=year)
        self.month_label.setText(f"Total (This Month): ${month_total:.2f}")
        self.total_label.setText(f"Total (This Year): ${year_total:.2f}")
        self.count_label.setText(f"Count (This Month): {month_count}")
    
    def on_year_changed(self):
        """Handle year selector change."""
        self.load_expenses()
    
    def add_expense(self):
        """Open add expense dialog."""
        from ui.expense_dialogs import AddExpenseDialog
        dialog = AddExpenseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense added!")
    
    def edit_expense(self):
        """Edit selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        row = None
        
        if selected_rows:
            row = selected_rows[0].row()
        else:
            # Check checkboxes
            checked_rows = []
            for r in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(r, 0)
                if checkbox and checkbox.isChecked():
                    checked_rows.append(r)
            
            if len(checked_rows) == 1:
                row = checked_rows[0]
        
        if row is None:
            QMessageBox.warning(self, "Error", "Please select one expense to edit.")
            return
        
        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)
        
        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return
        
        from ui.expense_dialogs import EditExpenseDialog
        dialog = EditExpenseDialog(expense, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense updated!")
    
    def view_expense(self):
        """View selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select an expense to view.")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)
        
        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return
        
        from ui.expense_dialogs import ViewExpenseDialog
        ViewExpenseDialog(expense, self).exec_()
    
    def delete_selected(self):
        """Delete selected expenses."""
        checked_rows = []
        for r in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(r, 0)
            if checkbox and checkbox.isChecked():
                checked_rows.append(r)
        
        if not checked_rows:
            QMessageBox.warning(self, "Error", "Please select expenses to delete.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Delete {len(checked_rows)} expense(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            failed = []
            for r in sorted(checked_rows, reverse=True):
                expense_id = int(self.table.item(r, 8).text())
                try:
                    db.delete_expense(expense_id)
                except Exception as e:
                    failed.append(str(expense_id))
            
            if failed:
                QMessageBox.warning(
                    self, "Partial Deletion",
                    f"Could not delete {len(failed)} expense(s)."
                )
            
            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense(s) deleted!")
```

- [ ] **Step 3: Run UI tests**

```bash
pytest tests/test_expenses_ui.py -v
```

Expected: PASS (both tests)

- [ ] **Step 4: Run full suite**

```bash
pytest tests/ -q
```

Expected: 172+ tests PASS

- [ ] **Step 5: Commit**

```bash
git add ui/expenses_tab.py tests/test_expenses_ui.py
git commit -m "feat: ExpensesTab UI for current-year expenses

- Table with 9 columns: Select, Date, Category, Amount, Invoice, Desc, Notes, Receipt
- Summary stats: Total/Count for month and year
- Year selector (last 5 years)
- Add/Edit/View/Delete buttons
- Checkbox-based multi-select delete
- Load expenses on year change
- 2 UI tests verifying load and stats
- All 172 existing tests pass"
```

---

### Task 4: Expense Dialogs (Add, Edit, View)

**Files:**
- Create: `ui/expense_dialogs.py`
- Modify: `tests/test_expenses_ui.py` (add dialog tests)

**Interfaces:**
- Consumes: `add_expense()`, `update_expense()`, `get_expense_categories()`, `add_expense_category()` (from Tasks 1-2)
- Produces: `AddExpenseDialog`, `EditExpenseDialog`, `ViewExpenseDialog`, `AddCategoryDialog` (QDialog subclasses)

- [ ] **Step 1: Write test for Add dialog**

Add to `tests/test_expenses_ui.py`:

```python
def test_add_expense_dialog(qapp, test_db):
    """Test add expense dialog opens and saves."""
    from ui.expense_dialogs import AddExpenseDialog
    
    get_or_create_expense_categories()
    current_year = datetime.now().year
    
    dialog = AddExpenseDialog()
    # Simulate user input
    dialog.date_input.setDate(datetime(current_year, 8, 1).date())
    dialog.category_combo.setCurrentIndex(0)
    dialog.amount_spin.setValue(50.00)
    dialog.invoice_input.setText('INV-001')
    dialog.description_input.setText('Test expense')
    dialog.notes_input.setText('Test notes')
    
    # Accept dialog
    dialog.accept()
    
    # Verify expense was added
    expenses = db.get_expenses(year=current_year)
    assert len(expenses) == 1
    assert expenses[0]['amount'] == 50.00
```

- [ ] **Step 2: Implement dialogs**

Create `ui/expense_dialogs.py`:

```python
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QDateEdit, QDoubleSpinBox, QComboBox, QPushButton, QFileDialog,
    QMessageBox, QSpinBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import os
import database as db

class AddExpenseDialog(QDialog):
    """Dialog for adding a new expense."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Expense")
        self.setGeometry(150, 150, 500, 600)
        self.receipt_file = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        
        # Date
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.now().date())
        layout.addWidget(self.date_input)
        
        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        categories = db.get_expense_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])
        self.category_combo.addItem("Add New Category...", -1)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_combo)
        
        # Amount
        layout.addWidget(QLabel("Amount ($):"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 99999.99)
        self.amount_spin.setDecimals(2)
        layout.addWidget(self.amount_spin)
        
        # Invoice number
        layout.addWidget(QLabel("Invoice Number (optional):"))
        self.invoice_input = QLineEdit()
        self.invoice_input.setMaxLength(50)
        self.invoice_input.setPlaceholderText("e.g., INV-001")
        layout.addWidget(self.invoice_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit()
        self.description_input.setMaxLength(255)
        layout.addWidget(self.description_input)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)
        
        # Receipt
        layout.addWidget(QLabel("Receipt (optional):"))
        receipt_layout = QHBoxLayout()
        self.receipt_label = QLabel("No file selected")
        receipt_layout.addWidget(self.receipt_label)
        receipt_btn = QPushButton("Browse...")
        receipt_btn.clicked.connect(self.browse_receipt)
        receipt_layout.addWidget(receipt_btn)
        layout.addLayout(receipt_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_expense)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_category_changed(self):
        """Handle category selection change."""
        if self.category_combo.currentData() == -1:
            self.add_category()
    
    def add_category(self):
        """Open add category dialog."""
        dialog = AddCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            cat_id = dialog.category_id
            # Refresh category combo
            current_index = self.category_combo.count() - 1
            self.category_combo.blockSignals(True)
            self.category_combo.removeItem(current_index)
            categories = db.get_expense_categories()
            for cat in categories:
                self.category_combo.addItem(cat['name'], cat['id'])
            self.category_combo.addItem("Add New Category...", -1)
            self.category_combo.setCurrentData(cat_id)
            self.category_combo.blockSignals(False)
    
    def browse_receipt(self):
        """Browse for receipt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt", "",
            "Images (*.png *.jpg *.gif);;PDFs (*.pdf);;All Files (*.*)"
        )
        if file_path:
            self.receipt_file = file_path
            self.receipt_label.setText(os.path.basename(file_path))
    
    def save_expense(self):
        """Validate and save expense."""
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0.")
            return
        
        if not self.description_input.text().strip():
            QMessageBox.warning(self, "Error", "Description is required.")
            return
        
        try:
            category_id = self.category_combo.currentData()
            current_year = datetime.now().year
            
            db.add_expense(
                year=current_year,
                expense_date=self.date_input.date().toString("yyyy-MM-dd"),
                category_id=category_id,
                amount=self.amount_spin.value(),
                invoice_number=self.invoice_input.text().strip(),
                description=self.description_input.text().strip(),
                notes=self.notes_input.toPlainText().strip(),
                receipt_path=self.receipt_file or ''
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save expense: {str(e)}")

class EditExpenseDialog(QDialog):
    """Dialog for editing an existing expense."""
    
    def __init__(self, expense, parent=None):
        super().__init__(parent)
        self.expense = expense
        self.receipt_file = expense.get('receipt_path', '')
        self.setWindowTitle("Edit Expense")
        self.setGeometry(150, 150, 500, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        
        # Date
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.strptime(self.expense['expense_date'], '%Y-%m-%d').date())
        layout.addWidget(self.date_input)
        
        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        categories = db.get_expense_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])
        self.category_combo.setCurrentData(self.expense['category_id'])
        layout.addWidget(self.category_combo)
        
        # Amount
        layout.addWidget(QLabel("Amount ($):"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 99999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(self.expense['amount'])
        layout.addWidget(self.amount_spin)
        
        # Invoice number
        layout.addWidget(QLabel("Invoice Number (optional):"))
        self.invoice_input = QLineEdit()
        self.invoice_input.setMaxLength(50)
        self.invoice_input.setText(self.expense.get('invoice_number', ''))
        layout.addWidget(self.invoice_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit()
        self.description_input.setMaxLength(255)
        self.description_input.setText(self.expense['description'])
        layout.addWidget(self.description_input)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlainText(self.expense.get('notes', ''))
        layout.addWidget(self.notes_input)
        
        # Receipt
        layout.addWidget(QLabel("Receipt (optional):"))
        receipt_layout = QHBoxLayout()
        self.receipt_label = QLabel(
            os.path.basename(self.receipt_file) if self.receipt_file else "No file selected"
        )
        receipt_layout.addWidget(self.receipt_label)
        receipt_btn = QPushButton("Replace...")
        receipt_btn.clicked.connect(self.browse_receipt)
        receipt_layout.addWidget(receipt_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_receipt)
        receipt_layout.addWidget(clear_btn)
        layout.addLayout(receipt_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_expense)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_receipt(self):
        """Browse for receipt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt", "",
            "Images (*.png *.jpg *.gif);;PDFs (*.pdf);;All Files (*.*)"
        )
        if file_path:
            self.receipt_file = file_path
            self.receipt_label.setText(os.path.basename(file_path))
    
    def clear_receipt(self):
        """Clear receipt."""
        self.receipt_file = ''
        self.receipt_label.setText("No file selected")
    
    def save_expense(self):
        """Validate and update expense."""
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0.")
            return
        
        try:
            db.update_expense(
                expense_id=self.expense['id'],
                expense_date=self.date_input.date().toString("yyyy-MM-dd"),
                category_id=self.category_combo.currentData(),
                amount=self.amount_spin.value(),
                invoice_number=self.invoice_input.text().strip(),
                description=self.description_input.text().strip(),
                notes=self.notes_input.toPlainText().strip(),
                receipt_path=self.receipt_file
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update expense: {str(e)}")

class ViewExpenseDialog(QDialog):
    """Read-only dialog for viewing expense details."""
    
    def __init__(self, expense, parent=None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("View Expense")
        self.setGeometry(150, 150, 500, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        
        # Date
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(QLabel(self.expense['expense_date']))
        
        # Category
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(QLabel(self.expense['category_name']))
        
        # Amount
        layout.addWidget(QLabel("Amount:"))
        layout.addWidget(QLabel(f"${self.expense['amount']:.2f}"))
        
        # Invoice
        layout.addWidget(QLabel("Invoice Number:"))
        layout.addWidget(QLabel(self.expense.get('invoice_number', '—')))
        
        # Description
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(QLabel(self.expense['description']))
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(QLabel(self.expense.get('notes', '—')))
        
        # Receipt
        layout.addWidget(QLabel("Receipt:"))
        if self.expense.get('receipt_path'):
            receipt_layout = QHBoxLayout()
            receipt_layout.addWidget(QLabel(f"File: {self.expense['receipt_path']}"))
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(self.open_receipt)
            receipt_layout.addWidget(open_btn)
            receipt_layout.addStretch()
            layout.addLayout(receipt_layout)
        else:
            layout.addWidget(QLabel("No receipt attached"))
        
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def open_receipt(self):
        """Open receipt file."""
        receipt_path = self.expense.get('receipt_path', '')
        if receipt_path and os.path.exists(receipt_path):
            os.startfile(receipt_path)
        else:
            QMessageBox.warning(self, "Error", "Receipt file not found.")

class AddCategoryDialog(QDialog):
    """Dialog for adding a new expense category."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.category_id = None
        self.setWindowTitle("Add Category")
        self.setGeometry(200, 200, 300, 150)
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Category Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Tools, Inventory")
        layout.addWidget(self.name_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Add")
        save_btn.clicked.connect(self.add_category)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_category(self):
        """Add new category."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category name is required.")
            return
        
        try:
            self.category_id = db.add_expense_category(name)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_expenses_ui.py -v
```

Expected: PASS (including new dialog test)

- [ ] **Step 4: Commit**

```bash
git add ui/expense_dialogs.py tests/test_expenses_ui.py
git commit -m "feat: Add/Edit/View expense dialogs

- AddExpenseDialog with category dropdown, amount, invoice, desc, notes
- 'Add New Category' option in dropdown opens AddCategoryDialog
- Receipt file browser with file selection
- EditExpenseDialog with pre-populated fields and replace/clear receipt
- ViewExpenseDialog read-only display with receipt open button
- AddCategoryDialog for custom categories
- UI tests for dialog initialization and save
- All tests pass"
```

---

### Task 5: ExpenseHistoryTab UI (Archived Expenses)

**Files:**
- Create: `ui/expense_history_tab.py`
- Modify: `tests/test_expenses_ui.py` (add history tests)

**Interfaces:**
- Consumes: `get_archived_expenses()`, `get_expense_by_id()` (from Task 2)
- Produces: `ExpenseHistoryTab` class (QWidget) with public methods:
  - `load_history()` → None
  - Used by main_window.py to register as tab

- [ ] **Step 1: Write test for History tab**

Add to `tests/test_expenses_ui.py`:

```python
def test_expense_history_tab_loads(qapp, test_db):
    """Test ExpenseHistoryTab loads archived expenses."""
    from ui.expense_history_tab import ExpenseHistoryTab
    
    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1
    
    # Add and archive expense
    exp_id = db.add_expense(prior_year, f'{prior_year}-08-01', 1, 100.00, '', 'Prior', '', '')
    c = db.get_connection().cursor()
    c.execute('UPDATE expenses SET archived=1 WHERE id=?', (exp_id,))
    db.get_connection().commit()
    
    tab = ExpenseHistoryTab()
    tab.load_history()
    
    assert tab.table.rowCount() > 0

def test_expense_history_search(qapp, test_db):
    """Test expense history search by description."""
    from ui.expense_history_tab import ExpenseHistoryTab
    
    get_or_create_expense_categories()
    current_year = datetime.now().year
    prior_year = current_year - 1
    
    exp_id = db.add_expense(prior_year, f'{prior_year}-08-01', 1, 100.00, '', 'Special Widgets', '', '')
    c = db.get_connection().cursor()
    c.execute('UPDATE expenses SET archived=1 WHERE id=?', (exp_id,))
    db.get_connection().commit()
    
    tab = ExpenseHistoryTab()
    tab.load_history()
    tab.search_input.setText('Widgets')
    tab.search_input.textChanged.emit('Widgets')
    
    assert tab.table.rowCount() == 1
```

- [ ] **Step 2: Implement ExpenseHistoryTab**

Create `ui/expense_history_tab.py`:

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import database as db

class ExpenseHistoryTab(QWidget):
    """Tab for viewing archived expenses from prior years."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)
        
        # Search
        year_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, date, category, amount, invoice, description, notes...")
        self.search_input.textChanged.connect(self.on_search)
        year_layout.addWidget(self.search_input)
        year_layout.addStretch()
        layout.addLayout(year_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Select', 'Date', 'Category', 'Amount', 'Invoice #', 'Description', 'Notes', 'Receipt', ''
        ])
        self.table.setColumnHidden(8, True)  # Hide expense_id
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_expense)
        button_layout.addWidget(view_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_history(self):
        """Load archived expenses."""
        # Get years with archived expenses
        c = db.get_connection().cursor()
        c.execute('SELECT DISTINCT year FROM expenses WHERE archived=1 ORDER BY year DESC')
        years = [row[0] for row in c.fetchall()]
        
        current_text = self.year_selector.currentText()
        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        for y in years:
            self.year_selector.addItem(str(y))
        if current_text:
            self.year_selector.setCurrentText(current_text)
        elif years:
            self.year_selector.setCurrentIndex(0)
        self.year_selector.blockSignals(False)
        
        # Load expenses
        self.display_expenses()
    
    def display_expenses(self):
        """Display archived expenses based on year and search."""
        if self.year_selector.count() == 0:
            self.table.setRowCount(0)
            return
        
        year = int(self.year_selector.currentText())
        search_query = self.search_input.text().strip() or None
        
        expenses = db.get_archived_expenses(year=year, search_query=search_query)
        
        self.table.setRowCount(0)
        for expense in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Checkbox (disabled)
            checkbox = QCheckBox()
            checkbox.setEnabled(False)
            self.table.setCellWidget(row, 0, checkbox)
            
            # Columns
            self.table.setItem(row, 1, QTableWidgetItem(expense['expense_date']))
            self.table.setItem(row, 2, QTableWidgetItem(expense['category_name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"${expense['amount']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(expense['invoice_number'] or ''))
            self.table.setItem(row, 5, QTableWidgetItem(expense['description']))
            self.table.setItem(row, 6, QTableWidgetItem(expense['notes']))
            receipt_text = 'Yes' if expense['receipt_path'] else '—'
            self.table.setItem(row, 7, QTableWidgetItem(receipt_text))
            
            # Store expense_id
            id_item = QTableWidgetItem(str(expense['id']))
            self.table.setItem(row, 8, id_item)
    
    def on_year_changed(self):
        """Handle year change."""
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.display_expenses()
    
    def on_search(self):
        """Handle search input change."""
        self.display_expenses()
    
    def view_expense(self):
        """View selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select an expense to view.")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)
        
        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return
        
        from ui.expense_dialogs import ViewExpenseDialog
        ViewExpenseDialog(expense, self).exec_()
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_expenses_ui.py -v
```

Expected: PASS (all tests including history)

- [ ] **Step 4: Commit**

```bash
git add ui/expense_history_tab.py tests/test_expenses_ui.py
git commit -m "feat: ExpenseHistoryTab for archived expenses

- Year selector (only years with archived expenses)
- Search bar: cross-field search (ID, date, category, amount, invoice, desc, notes)
- 9-column table matching ExpensesTab layout
- View button for read-only expense details
- Real-time search filtering
- 2 tests for load and search
- All tests pass"
```

---

### Task 6: Integration (Main Window & App Startup)

**Files:**
- Modify: `ui/main_window.py`
- Modify: `main.py`

**Interfaces:**
- Consumes: `ExpensesTab`, `ExpenseHistoryTab` (from Tasks 3-5)
- Consumes: `check_and_archive_year_transition()`, `get_or_create_expense_categories()` (from Task 1)
- Produces: (none — integration only)

- [ ] **Step 1: Register tabs in main_window.py**

Open `ui/main_window.py`, find where other tabs are registered (around `InventoryHistoryTab`), add:

```python
from ui.expenses_tab import ExpensesTab
from ui.expense_history_tab import ExpenseHistoryTab

# In __init__ or tab registration section:
self.tab_expenses = ExpensesTab()
self.tab_expense_history = ExpenseHistoryTab()

tabWidget.addTab(self.tab_expenses, "Expenses")
tabWidget.addTab(self.tab_expense_history, "Expense History")
```

- [ ] **Step 2: Call startup functions in main.py**

Open `main.py`, find the startup code after `init_db()`, add:

```python
from database import get_or_create_expense_categories, check_and_archive_year_transition

# After init_db() call:
get_or_create_expense_categories()
check_and_archive_year_transition()
```

- [ ] **Step 3: Test integration**

Run app:
```bash
python main.py
```

Verify:
- Expenses tab appears in tab bar
- Expense History tab appears
- Predefined categories are seeded on first run
- Add/Edit/View/Delete work

- [ ] **Step 4: Run full suite**

```bash
pytest tests/ -q
```

Expected: 180+ tests PASS (172 existing + 8+ new)

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py main.py
git commit -m "integrate: register expenses tabs and startup functions

- Add ExpensesTab and ExpenseHistoryTab to main_window.py
- Call get_or_create_expense_categories() at startup
- Call check_and_archive_year_transition() at startup
- All 180+ tests pass
- App ready for manual testing"
```

---

### Task 7: Final Testing & Verification

**Files:**
- (No new files — verify existing tests)

**Interfaces:**
- (Testing only — no new production code)

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Verify:
- All 180+ tests PASS
- No regressions in existing 172 tests
- All new expense tests pass (archive, CRUD, UI, history)

- [ ] **Step 2: Manual smoke test**

1. Launch app
2. Navigate to Expenses tab
3. Add expense (test category dropdown, add new category)
4. Edit expense (change amount, invoice, notes, upload receipt)
5. View expense (check receipt opens)
6. Delete selected expense
7. Navigate to Expense History tab
8. Filter/search by different fields
9. Year change → verify data reloads
10. Verify summary stats update

- [ ] **Step 3: Year boundary test (optional)**

Manually set system date to year boundary, restart app, verify prior-year expenses auto-archive.

- [ ] **Step 4: Commit final**

```bash
git add -A && git commit -m "test: verify full expenses feature integration

- All 180+ tests passing (172 existing + 8 new)
- Manual smoke tests passed
- ExpensesTab and ExpenseHistoryTab working
- Archive, CRUD, search, dialogs all functional
- Ready for v0.6.0 release"
```

---

## Summary

**Total Tasks:** 7  
**Total Commits:** 7 (one per task)  
**Test Coverage:** 8+ new tests, all 172 existing tests pass  
**New Features:**
- Current-year expenses (add/edit/delete)
- Historical archived expenses (searchable, read-only)
- Receipt upload/view
- Custom category management
- Year-based auto-archive
- Cross-field search

