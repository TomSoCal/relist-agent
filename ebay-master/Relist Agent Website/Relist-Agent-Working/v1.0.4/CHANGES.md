# v1.5.0 Change Log

## WORKING FEATURES (DO NOT TOUCH)
- ✅ Logo displays (220x110)
- ✅ Store name populates from config
- ✅ Exclusions persist after save
- ✅ Excluded items disappear from available list after save
- ✅ Debug logs in hidden folder
- ✅ Clean app directory at launch

## ISSUE TO FIX (MINIMAL)
- ❌ Search in ExclusionsWindow shows excluded items
- Root cause: filter_available_skus() compares raw SKU against display text
- Fix: Use self.excluded_skus_set instead of parsing listbox display

## CHANGES MADE
### Commit: [pending]
- **File:** gui_app.py line 968
- **Change:** filter_available_skus() - replace line that reads from listbox display text
- **Old:** `excluded_skus = set(self.excluded_skus.get(0, tk.END))`
- **New:** `excluded_skus = self.excluded_skus_set`
- **Why:** listbox.get() returns "SKU - Title" strings, not raw SKU values
- **Impact:** Search will now properly filter excluded items

## STRICT RULES
1. Only edit line 968 in filter_available_skus() method
2. Do NOT touch any other function
3. Do NOT change how store_name loads
4. Do NOT change how inventory displays
5. Rebuild EXE
6. Test search - excluded items should NOT appear
