# Final Fix Report — Unified History Tab

Both blockers from the whole-branch review are resolved. Full suite: **205 passed**.

---

## BLOCKER 1 — Sales History crashed with TypeError

### Root cause (confirmed by reproduction, not inspection)

`sales.year` is a nullable column. Neither UI add-sale path populates it:

- `ui/sales_tab.py` — `AddSaleDialog.get_sale_data()` returns a dict with no `year` key
- `ui/inventory_tab.py:326` — passes `year=` but only on the sell-from-inventory path

So every sale entered through `AddSaleDialog` lands with `year = NULL`.
`database.get_sales()` did `SELECT *`, and `SalesHistoryView.load_years()` line 68
compared `sale['year'] < self.current_year` → `None < int` → `TypeError`.

Reproduced before fixing:

```
rows: [(2, None, '2025-06-01'), (1, None, '03/15/2025')]
REPRO OK -> TypeError: '<' not supported between instances of 'NoneType' and 'int'
```

### Additional finding — two date formats in the wild

The prescribed fix `CAST(substr(sold_date,1,4) AS INTEGER)` would have been **wrong**
for the majority of rows. `sold_date` is not consistently ISO:

| Source | Format | Example |
|---|---|---|
| `ui/sales_tab.py:376`, `ui/inventory_tab.py:671` (both use `strftime("%m/%d/%Y")`) | `MM/DD/YYYY` | `03/15/2025` |
| Imported / legacy rows in `panda_profit.db` | `YYYY-MM-DD` | `2026-02-01` |

`substr('03/15/2025', 1, 4)` = `'03/1'` → `CAST` → **3**. Every UI-entered sale would
have been bucketed into year 3 and silently vanished from the History tab — a data-
correctness bug replacing a crash. The derivation was made format-aware instead.

### Fix

Added a single shared SQL expression in `database.py` (top of module, after `DB_PATH`):

```sql
CAST(CASE WHEN sold_date LIKE '____-__-__%'
     THEN substr(sold_date, 1, 4) ELSE substr(sold_date, -4) END AS INTEGER)
```

ISO dates take the first 4 chars; anything else falls back to the trailing 4 chars,
which covers `MM/DD/YYYY` and any other format ending in a 4-digit year.
`sold_date` is `NOT NULL`, so the result is always a real integer.

**`database.get_sales()`** — both branches now select and filter on the derived value:

```python
c.execute(f'SELECT *, {SALE_YEAR_SQL} AS year FROM sales ORDER BY sold_date DESC')
# and
c.execute(f'SELECT *, {SALE_YEAR_SQL} AS year FROM sales '
          f'WHERE {SALE_YEAR_SQL} = ? ORDER BY sold_date DESC', (year,))
```

The `AS year` alias intentionally shadows the raw nullable column from `SELECT *`;
`dict_factory` assigns columns in cursor order, so the derived value wins. This is
documented in the function docstring so it is not "fixed" back later.

### Second site — checked and also fixed

The review asked to check whether `analytics_reports.py` shares the bug. The file is
`analytics/reports.py`; `_get_sales_for_report()` line 56 had the identical
`AND year = ?` predicate and the identical NULL exposure. Fixed the same way,
importing `SALE_YEAR_SQL` rather than duplicating the expression.

### Verification

| `sold_date` | derived `year` |
|---|---|
| `2026-01-05` | 2026 |
| `2025-06-01` | 2025 |
| `03/15/2025` | 2025 |

`get_sales(year=2025)` returns both 2025 rows across both formats; `get_sales(year=2026)`
returns only the 2026 row.

---

## BLOCKER 2 — Test coverage was vacuous

### Root cause

`tests/test_history_tab.py` never wrote a row. `init_db()` on an empty temp DB leaves
`sales`, `inventory` and `expenses` empty, so every year selector was empty, every
`years` list was `[]`, and every assertion was of the form
`assert str(current_year) not in []` — trivially true. The two `if count > 0:` guards
in `test_history_views_independent_year_selection` never entered their bodies.
The suite could not observe the crash in Blocker 1 at all.

### Fix

Added `_seed_prior_year_data()`, called from the `test_db` fixture. It seeds:

- **1 prior-year sale** — `sold_date = f'{PRIOR_YEAR}-06-15'`, deliberately **without**
  passing `year=`, so the fixture reproduces the exact NULL-year condition the UI creates
- **1 current-year sale** — so "excludes current year" is a filter under test, not a no-op
- **1 prior-year archived inventory item** — `units=0` + `created_at` in the prior year,
  then `archive_sold_inventory_for_year(PRIOR_YEAR)`
- **1 prior-year archived expense** — inserted via direct SQL, because `add_expense()`
  rejects non-current years by design (year-based write protection)

Years are computed as `datetime.now().year - 1` rather than hardcoded `2025`, so the
suite does not rot at the next year boundary.

### Tests strengthened

Vacuous conditionals removed; assertions now check concrete values.

| Test | Now asserts |
|---|---|
| `test_history_tab_has_buttons` | actual button labels, not `tab is not None` |
| `test_seed_creates_prior_year_sale_with_null_year_column` | **new** — guards that the seeded row really has `year IS NULL`, so the suite can't silently weaken |
| `test_get_sales_derives_year_from_sold_date` | **new** — no `None` years; `{PRIOR, CURRENT}` |
| `test_get_sales_derives_year_from_us_format_date` | **new** — `MM/DD/YYYY` resolves correctly |
| `test_sales_history_view_excludes_current_year` | selector is **non-empty**, contains prior year, excludes current |
| `test_sales_history_view_populates_table_and_totals` | **new** — row count, title, units, `$25.00`, `$50.00` line total, `$50.00` year total |
| `test_inventory_history_view_shows_archived_item` | **new** — combo is exactly `['All Years', PRIOR]`; search hit **and** miss |
| `test_expense_history_view_shows_archived_expense` | **new** — date, `$42.50`, invoice, description |
| `test_history_views_independent_year_selection` | `if` guards deleted; asserts populated counts, three distinct widgets, and that moving one combo leaves the others untouched |
| `test_all_history_views_exclude_current_year` | each selector asserted non-empty before the exclusion check |

`test_history_tab_initializes` and `test_history_tab_has_buttons` were also given the
`test_db` fixture — they previously ran against the developer's real `panda_profit.db`.

### Proof the tests are no longer vacuous

The fix was temporarily reverted in `database.get_sales()` and the suite re-run:

```
9 failed, 5 passed
FAILED test_get_sales_derives_year_from_sold_date
FAILED test_get_sales_derives_year_from_us_format_date
FAILED test_sales_history_view_initializes - TypeError
FAILED test_sales_history_view_excludes_current_year
FAILED test_sales_history_view_populates_table_and_totals
FAILED test_history_tab_buttons_switch_views - TypeError
FAILED test_history_tab_lazy_loads_views - TypeError
FAILED test_history_views_independent_year_selection
FAILED test_all_history_views_exclude_current_year
```

The fix was then restored and all tests pass again. Before this change the same revert
produced **zero** failures.

---

## Test results

```
tests/test_history_tab.py ...  14 passed
tests/ (full suite)            205 passed in 26.06s
```

205 = 199 prior + 6 net new tests in `test_history_tab.py` (8 → 14).

## Files changed

- `database.py` — added `SALE_YEAR_SQL`; `get_sales()` derives and filters on it
- `analytics/reports.py` — `_get_sales_for_report()` uses the same derivation
- `tests/test_history_tab.py` — seeded fixture + real assertions

## Status

Both blockers addressed. No remaining blockers to merge.

## Note for follow-up (not fixed — out of scope)

The underlying inconsistency remains: `AddSaleDialog` still writes `year = NULL` and
still writes `MM/DD/YYYY` into a column that elsewhere holds ISO dates. The read path is
now robust to both, so nothing is broken, but normalising the write path (populate `year`,
store ISO) would be the cleaner long-term fix. Flagging rather than changing it, since it
touches the sales entry UI which was outside this fix's scope.
