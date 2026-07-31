# Checkbox Selection Implementation - Complete

## Summary
Both Inventory and Sales tabs now support:
- ✓ Checkbox selection in column 0
- ✓ Row highlighting (yellow when checked, white when unchecked)
- ✓ Single-select mode by default (only one item selectable)
- ✓ Bulk Actions mode for multi-select operations
- ✓ Limited bulk operations: delete (Inventory), return-to-inventory (Sales)

## Changes Made

### Sales Tab (ui/sales_tab.py)
- Added checkbox column (column 0) to table
- Increased column count from 16 to 17
- Added headers for all columns
- Fixed column numbering in refresh_table() to account for checkbox column
- Updated ID extraction in view_sale_details(), delete_sale(), return_to_inventory()
- Implemented on_checkbox_changed() - handles row highlighting and single-select enforcement
- Implemented toggle_bulk_mode() - switches between single-select and multi-select modes
- Implemented bulk_return_items() - returns multiple sales to inventory at once

### Inventory Tab (ui/inventory_tab.py)
- Already had full implementation
- on_checkbox_changed() - row highlighting and single-select enforcement
- toggle_bulk_mode() - mode switching with button visibility
- bulk_delete_items() - deletes multiple items at once

## Usage

### Single-Select Mode (Default)
1. Click checkbox next to item to select it
2. Row highlights yellow
3. Clicking another checkbox automatically unchecks the first one
4. Use single-item buttons: Delete, Edit, Return to Inventory, etc.

### Bulk Actions Mode
1. Click "Bulk Actions" button (blue background)
2. Button visibility changes:
   - "Bulk Actions" button hidden
   - "Return Selected" button appears (Sales tab) or "Delete Selected" (Inventory tab)
   - "Cancel Bulk" button appears
3. Check multiple items (they all stay highlighted)
4. Click "Return Selected" or "Delete Selected" to perform bulk operation
5. Click "Cancel Bulk" to exit bulk mode and clear selections

## Testing
- Table structure verified: 17 columns (1 checkbox + 16 data columns)
- All required methods present and functional
- Button visibility logic verified
- Bulk mode toggle tested

## Files Modified
- ui/sales_tab.py: Complete checkbox implementation
- ui/inventory_tab.py: No changes needed (already had full implementation)
- database.py: No changes
- ui/main_window.py: No changes

## Edge Cases Handled
- Column references updated for checkbox column shift
- blockSignals() used to prevent recursive checkbox events
- Sorted reverse deletion to avoid row index shifting during bulk operations
- Uncheck all items when exiting bulk mode
