# v1.5.0 Change Log

## VERIFIED WORKING FEATURES
- ✅ Logo displays (220x110)
- ✅ Store name populates from config
- ✅ Exclusions load from config (552 items)
- ✅ Excluded items listbox shows all items
- ✅ Search filter respects exclusions
- ✅ Debug logs in hidden folder

## FIXES APPLIED

### Fix #1: Search Filter Bug
**Commit:** `fix: search filter uses excluded_skus_set, not display text`
- **File:** gui_app.py line 968
- **Root cause:** filter_available_skus() was comparing raw SKU against listbox display text ("SKU - Title")
- **What changed:** `excluded_skus = set(self.excluded_skus.get(0, tk.END))` → `excluded_skus = self.excluded_skus_set`
- **Why:** listbox.get(0, END) returns display text strings, not raw SKU values. In-memory set has correct SKU values.
- **Verified by:** Search no longer shows excluded items

### Fix #2: Store Name Not Updating
**Commit:** `fix: create store_label always, not conditionally`
- **File:** gui_app.py lines 1153-1162
- **Root cause:** store_label was set to None if store_name was empty at startup. Later when user saved settings, refresh_after_settings_save() checked `if self.store_label:` which was None, so update never happened.
- **What changed:** Always create store_label widget (don't conditionally), initialize with empty text, populate if store_name exists
- **Why:** Label widget must exist to be updated later. Can't update a None object.
- **Verified by:** store_label can now be updated when config changes

### Fix #3: Exclusions Not Loading
**Commit:** `fix: load_excluded_from_config uses config_dict parameter, not fresh import`
- **File:** gui_app.py lines 901-903
- **Root cause:** load_excluded_from_config() was doing `from auth import load_config` and getting a fresh config instead of using self.config_dict passed to constructor
- **What changed:** Removed fresh import, now uses `self.config_dict.get("excluded_skus", [])`
- **Why:** ExclusionsWindow receives config_dict in constructor with all excluded_skus already loaded, should use that instead of reimporting
- **Verified by:** exclusions_debug.log now shows "Loaded 552 SKUs" instead of "Loaded 0 SKUs"

## STRICT RULES FOR FUTURE CHANGES
1. Follow CHANGE_PROCESS.md ALWAYS
2. Read actual code - never assume
3. Check debug logs - verify actual behavior
4. One change per fix
5. Test that specific fix only
6. Verify nothing else broke
7. Document with debug log evidence
