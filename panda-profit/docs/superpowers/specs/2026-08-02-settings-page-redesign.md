# Settings Page Redesign — QTabWidget Architecture

**Date:** 2026-08-02  
**Feature:** Settings page reorganization into sub-menu tabs  
**Status:** Design spec (pending implementation)  
**Related:** Unified History Tab (v0.1.0) — uses same QTabWidget pattern

---

## Overview

Reorganize Panda Profit's Settings page from a single scrollable layout into a tabbed interface with 4 independent tabs: API Info, Item Settings, Platform Fees, and Tax Settings. Each tab lazy-loads on first click and maintains its own state independently.

**Goal:** Improve organization, scalability, and future expansion capability for settings management.

---

## Architecture

### Pattern
Mirror the **Unified History Tab** implementation (v0.1.0):
- Main container (`SettingsTab`) uses `QTabWidget`
- Each tab is a separate view class (lazy-loaded)
- Views instantiate only on first click
- Tab state is independent (no cross-tab interference)

### Tab Structure

```
Settings (QTabWidget)
├── Tab 1: API Info
│   └── eBay API Configuration (expandable for future APIs)
├── Tab 2: Item Settings
│   ├── Stores (add/delete)
│   ├── Categories (add/delete)
│   └── Brands (add/delete)
├── Tab 3: Platform Fees
│   └── Fees table (Platform | Transaction % | Shipping % | Payment % | Notes)
└── Tab 4: Tax Settings
    ├── Mileage Deduction Rate ($/mile)
    ├── Tax Savings Percentage (%)
    └── TOTAL TO SAVE FOR TAXES (calculated from P&L)
```

### Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| `SettingsTab` | Main container, QTabWidget, button callbacks, lazy-loading |
| `ApiInfoView` | eBay API section (status, app_id display, oauth buttons, test connection) |
| `ItemSettingsView` | Stores + Categories + Brands (three independent sections) |
| `PlatformFeesView` | Platform fees table (add/edit/delete via context menu) |
| `TaxSettingsView` | Mileage rate input, tax % input, P&L-derived TOTAL TO SAVE display |

---

## Data Flow

### Read Path
1. **On Tab Click:** `SettingsTab.on_[view]_clicked()` → check if view is None
2. **If None:** Instantiate view (lazy-load) and add to stacked widget
3. **If exists:** Show existing view (state preserved)
4. **View Initialization:** Each view loads its data from database/config on creation

### Write Path
1. **User Action:** Edit/add/delete in any view
2. **View Handler:** Save to database via `database.py` functions
3. **State Persistence:** Changes reflect immediately in tab (no re-query needed)
4. **Cross-Session:** Next app launch loads saved settings

### P&L Integration (Tax Settings Only)
1. **On Tab Click:** `TaxSettingsView` loads mileage rate + tax % from database
2. **P&L Query:** Fetch current-year P&L total from `database.py.get_pl_total()`
3. **Calculate Total:** `pl_total * (1 - tax_percentage/100)` → display in "TOTAL TO SAVE FOR TAXES"
4. **Update Trigger:** Recalculate on:
   - User changes tax percentage
   - Tab is shown (refresh latest P&L)

---

## API Info Tab Specification

### Current Implementation (eBay)
```
Status: ✓ eBay credentials configured  (or ✗ not configured)

App ID: [read-only field, masked value or placeholder]
Cert ID: [password field, read-only]

Buttons:
- [Setup eBay OAuth] (if not configured)
- [Reconfigure OAuth] + [Test Connection] (if configured)
```

### Future Expansion Pattern
When new APIs are added:
1. Add new section below eBay (same layout)
2. Each API gets: status label, credential fields, setup/reconfigure/test buttons
3. No schema changes needed — keep existing credential storage pattern

**Design Principle:** Each API section is self-contained and independent. No API affects another.

---

## Item Settings Tab Specification

### Three Independent Sections

**Section 1: Stores**
```
Stores:
[Add Store] [Delete Store]
[List widget with current stores]
```

**Section 2: Categories**
```
Categories:
[Add Category] [Delete Category]
[List widget with current categories]
```

**Section 3: Brands**
```
Brands:
[Add Brand]
[Table widget with brand names]
[Context menu: delete on right-click]
```

### Behavior
- All three sections visible at once (not nested tabs)
- Add/delete operations modify `constants.py` and persist to database
- Changes take effect immediately (no dialog confirmation)
- Search/filter: Not required for this tab

---

## Platform Fees Tab Specification

### Existing Table (No Changes)

```
Platform Fees:
[Add Platform]
[Table: Platform | Transaction % | Shipping % | Payment % | Notes]
[Context menu: edit/delete on right-click]
```

### Behavior
- Keep exact current implementation
- Persist to database via `db.add_platform_fee()` / `db.delete_platform_fee()`
- Context menu for edit/delete (existing pattern)

---

## Tax Settings Tab Specification

### Three Input/Display Areas

**Area 1: Mileage Deduction**
```
Mileage Rate ($/mile):
Enter the IRS standard mileage rate for your region.

Rate: $ [0.67 default, spinbox 0.0-10.0, 3 decimals] / mile [Save Rate button]
```

**Area 2: Tax Savings Percentage**
```
Tax Savings Percentage (%):
Enter the percentage of your P&L you want to reserve for taxes.

Percentage: [50 default, spinbox 0-100, 1 decimal] % [Save Percentage button]
```

**Area 3: TOTAL TO SAVE FOR TAXES (Calculated)**
```
Total to Save for Taxes:
[Display-only field showing calculated amount]
Formula: P&L Total × (1 - Tax Savings %/100)
Example: $10,000 P&L × (1 - 50%/100) = $5,000 to save
```

### Behavior
- Mileage rate: Saved to database via `db.set_setting('mileage_rate', value)`
- Tax percentage: Saved to database via `db.set_setting('tax_percentage', value)`
- Total to save: Calculated on tab show and on percentage change
- P&L source: `db.get_pl_total()` (current year only)
- No edit button needed for calculated field (read-only display)

---

## Database & Configuration

### No Schema Changes Required
- `settings` table already exists
- `mileage_rate` setting already stored/retrieved
- Tax percentage to be added to settings
- P&L calculation uses existing sales/inventory data

### Database Functions Needed
```python
# Existing (no changes)
db.set_setting(key, value)
db.get_setting(key)

# Existing (no changes)
db.add_store(name)
db.delete_store(name)
db.add_category(name)
db.delete_category(name)
# etc.

# NEW: Support P&L calculation in Tax Settings
db.get_pl_total(year=None)  # Returns current-year P&L total
```

---

## Testing Strategy

### Unit Tests
- **ApiInfoView:** OAuth buttons exist, status label updates correctly
- **ItemSettingsView:** Add/delete operations update constants and database
- **PlatformFeesView:** Table populated, context menu works
- **TaxSettingsView:** Mileage rate saves, tax % saves, calculated total updates on input

### Integration Tests
- **Tab Switching:** Click each tab, verify correct view loads
- **Lazy Loading:** Verify views are None initially, instantiated on first click
- **State Isolation:** Change year in one tab, verify others unaffected (if applicable)
- **Data Persistence:** Set values, close/reopen app, verify values persist

### Manual Testing Checklist
- [ ] All 4 tabs visible in tab bar
- [ ] Click each tab, verify content displays correctly
- [ ] Add/edit/delete in Item Settings, verify changes persist
- [ ] Edit mileage rate, verify saves and displays on reload
- [ ] Edit tax percentage, verify calculated total updates
- [ ] API Info shows correct status (configured/not configured)
- [ ] eBay OAuth buttons work (if applicable)
- [ ] Platform Fees table displays all data correctly
- [ ] No errors in console during tab switching

---

## Files to Create/Modify

### New Files
- `ui/settings/api_info_view.py` — eBay API section
- `ui/settings/item_settings_view.py` — Stores/Categories/Brands
- `ui/settings/platform_fees_view.py` — Platform fees table
- `ui/settings/tax_settings_view.py` — Mileage + tax % + calculated total

### Modified Files
- `ui/settings_tab.py` — Convert to QTabWidget with lazy-loading + buttons
- `ui/main_window.py` — Register SettingsTab (no changes likely needed)
- `database.py` — Add `get_pl_total()` if not exists

### No Changes Needed
- `constants.py` — Stores/Categories/Brands already imported
- Test fixtures — Existing patterns sufficient

---

## Error Handling

### Database Errors
- If `get_pl_total()` fails: Display "$0.00" in calculated field with tooltip "Unable to calculate"
- If settings save fails: Show error dialog, don't close tab

### OAuth Errors (API Info Tab)
- Existing pattern: user clicked "Setup eBay OAuth" → error dialog → user can retry

### Invalid Input (Tax Settings)
- Tax percentage: Validate 0-100, spinbox enforces this
- Mileage rate: Validate 0.0-10.0, spinbox enforces this
- No need for additional validation

---

## Global Constraints

From Panda Profit codebase:
- Use `QTabWidget` for tab management (consistent with History Tab)
- Lazy-load views to avoid startup lag
- Database calls via `database.py` functions (never raw SQL in UI)
- All settings persist to `panda_profit.db`
- No breaking changes to database schema
- Follow existing code style (PyQt5, Python 3.9+)

---

## Success Criteria

- ✅ Settings page displays 4 tabs: API Info, Item Settings, Platform Fees, Tax Settings
- ✅ Each tab lazy-loads on first click
- ✅ Tab state is independent (changes in one don't affect others)
- ✅ All existing functionality preserved (no regressions)
- ✅ Mileage rate persists and displays on reload
- ✅ Tax percentage persists and updates calculated total
- ✅ Calculated "TOTAL TO SAVE FOR TAXES" displays correctly
- ✅ All 4 views have comprehensive test coverage
- ✅ Manual smoke test passes all checklist items
- ✅ No errors in console during normal use

---

## Notes

### Pre-Existing (Related but Out of Scope)
- AddSaleDialog writes `year = NULL` (inconsistent with imports) — flagged for future normalization
- Analytics layer uses raw `WHERE year = ?` (silently undercounts) — flagged for follow-up

### Future Enhancement Opportunities
- Add search/filter to Item Settings (if list grows large)
- Add import/export for settings (batch operations)
- Add settings versioning (rollback capability)

