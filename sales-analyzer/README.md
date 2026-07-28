# Sales Analyzer

Simple tool to compare your sold eBay items from the last year against currently active listings with exact title match.

## What It Does

1. Fetches all **sold items** from the past 12 months
2. Fetches all **active listings** you currently have for sale
3. Matches them by exact title (same title = same item)
4. Shows side-by-side:
   - **Left:** Sold items (ID + sold date)
   - **Right:** Active listings (ID + quantity available)

## How to Use

**Double-click `RUN.bat`** to start the app.

The app will:
- Auto-fetch data from your eBay account (using Relist Agent credentials)
- Display matches side-by-side
- Sort by title alphabetically

**Export to CSV:** Click "Export to CSV" to save matches to `sales_analyzer_matches.csv` (useful for manual review/deletion on eBay).

## What It Shows

For each matching item:
- **Title** (both sides)
- **Item ID** (Sold ID on left, Active ID on right)
- **Sold Time** (when it sold)
- **Quantity Available** (how many you have listed now)

Use this to:
- Identify items that sold but still have active listings
- Manually delete them on eBay
- Refine your inventory strategy

## Notes

- Requires active eBay API credentials from Relist Agent (reuses auth)
- Exact title match only (titles must be identical)
- Fetches last 12 months of sold items
- No deletion — just shows you what to delete

---

**Next steps:**
1. Click "Refresh Data" to re-fetch if needed
2. Review the list
3. Manually delete matched items on eBay website
4. Or use "Export to CSV" for bulk review
