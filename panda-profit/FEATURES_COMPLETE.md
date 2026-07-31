# Panda Profit - Complete Feature Documentation

## Overview

Panda Profit is a premium reseller sales and profit tracking application designed for eBay, Poshmark, Facebook Marketplace, and multi-platform sellers. It provides comprehensive inventory management, sales tracking, expense logging, mileage tracking, and advanced analytics to help resellers maximize profitability.

**Current Version:** 0.1.0  
**Release Date:** July 30, 2026  
**Architecture:** Year-based (read any year, write current year only)

---

## Database Schema

### Core Tables

#### 1. **inventory** — Active Inventory Management
Tracks items available for sale (not yet sold).

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| listed_date | TEXT | When item was listed for sale |
| item_title | TEXT | Product name/description |
| units | INTEGER | Number of units in stock |
| sku | TEXT | Stock Keeping Unit identifier |
| bin | TEXT | Bin/storage location |
| store | TEXT | Store source where acquired |
| category | TEXT | Product category |
| brand | TEXT | Brand/manufacturer |
| cost | REAL | Cost per unit or total cost |
| notes | TEXT | Additional notes |
| xp | INTEGER | Experience points (custom field) |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**CRUD Operations:**
- `add_inventory()` — Create new inventory item
- `get_all_inventory()` — Retrieve all inventory items
- `get_inventory_by_id(item_id)` — Get single inventory item
- `update_inventory(item_id, **kwargs)` — Modify inventory item
- `delete_inventory(item_id)` — Remove inventory item

#### 2. **sales** — Completed Sales Transactions
Tracks all completed sales with full profit/loss calculations.

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| year | INTEGER | Year of sale (write-protected) |
| month | INTEGER | Month of sale (1-12) |
| days_to_sell | INTEGER | Days from listing to sold |
| platform | TEXT | Platform (eBay, Poshmark, Facebook, etc.) |
| sold_date | TEXT | Sale completion date (YYYY-MM-DD) |
| listed_date | TEXT | Original listing date |
| item_title | TEXT | Product name |
| units | INTEGER | Units sold |
| bin | TEXT | Storage location |
| sku | TEXT | Stock Keeping Unit |
| store | TEXT | Store source |
| category | TEXT | Product category |
| sale_price | REAL | Sale price per unit (or total) |
| shipping_collected | REAL | Shipping revenue collected |
| cost_of_goods | REAL | Cost to acquire item |
| shipping_cost | REAL | Actual shipping cost |
| platform_fee | REAL | Platform/listing fee |
| promoted_fee | REAL | Advertising/promotion fee |
| transaction_fee | REAL | Payment processing fee |
| sales_tax_collected | REAL | Sales tax collected |
| refund | REAL | Refund amount (if applicable) |
| total_fees | REAL | Sum of all fees |
| profit_loss | REAL | Net profit/loss calculation |
| total_income | REAL | Total revenue from sale |
| total_platform_expenses | REAL | Total platform costs |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**CRUD Operations:**
- `add_sale(**kwargs)` — Log new sale
- `get_all_sales()` — Retrieve all sales |
- `get_sales_by_date_range(start, end)` — Query sales by date
- `update_sale(sale_id, **kwargs)` — Modify sale record
- `delete_sale(sale_id)` — Remove sale

**Profit Calculation Formula:**
```
profit = (sale_price + shipping_collected) 
        - (cost_of_goods + shipping_cost + platform_fee + transaction_fee + promoted_fee)
```

#### 3. **expenses** — Business Expense Tracking
Tracks operating expenses categorized by type (supplies, shipping, equipment, etc.).

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| year | INTEGER | Year of expense (write-protected) |
| expense_date | TEXT | Date of expense (YYYY-MM-DD) |
| category_id | INTEGER FK | Reference to expense_categories |
| amount | REAL | Expense amount |
| description | TEXT | Expense description |
| receipt_path | TEXT | Path to receipt file |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**Default Expense Categories:**
- Packaging Materials (supplies)
- Shipping Costs (shipping)
- Office Supplies (supplies)
- Equipment (equipment)
- Software Subscriptions (subscriptions)
- Advertising (marketing)
- Professional Services (services)
- Rent (facility)
- Utilities (facility)
- Insurance (insurance)
- Vehicle Expenses (vehicle)
- Travel (travel)
- Meals & Entertainment (meals)
- Training & Development (education)
- Miscellaneous (other)

**CRUD Operations:**
- `add_expense()` — Log new expense (current year only)
- `get_expenses_by_date_range(start, end, year)` — Query expenses
- `delete_expense(expense_id)` — Remove expense (current year only)
- `get_total_expenses_by_category(start, end, year)` — Aggregate by category

#### 4. **mileage** — Business Mileage Tracking
Tracks sourcing trips and business-related travel for tax deductions.

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| year | INTEGER | Year of trip (write-protected) |
| trip_date | TEXT | Date of trip (YYYY-MM-DD) |
| odometer_start | INTEGER | Starting odometer reading |
| odometer_end | INTEGER | Ending odometer reading |
| miles | REAL | Total miles traveled |
| purpose | TEXT | Trip purpose (sourcing/business/delivery) |
| stores_visited | TEXT | Comma-separated list of locations |
| notes | TEXT | Trip notes |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**CRUD Operations:**
- `add_mileage_trip()` — Log new trip (current year only)
- `get_mileage_by_date_range(start, end, year)` — Query trips
- `delete_mileage_trip(trip_id)` — Remove trip (current year only)
- `get_total_mileage_for_period(start, end, year)` — Aggregate miles

#### 5. **expense_categories** — Expense Category Management
Lookup table for expense types with categorization.

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| name | TEXT | Category name (unique) |
| category_type | TEXT | Type (supplies, shipping, equipment, etc.) |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**CRUD Operations:**
- `add_expense_category()` — Create new category
- `get_all_expense_categories()` — List all categories
- `delete_expense_category(category_id)` — Remove category

#### 6. **platform_fees** — Platform Fee Configuration
Stores fee structures for different sales platforms.

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| platform | TEXT | Platform name (eBay, Poshmark, etc.) |
| listing_fee | REAL | Per-listing fee |
| transaction_fee_pct | REAL | Transaction fee percentage |
| shipping_fee_pct | REAL | Shipping fee percentage |
| payment_fee_pct | REAL | Payment processing fee percentage |
| notes | TEXT | Platform-specific notes |
| created_at | TEXT | Timestamp of creation |
| updated_at | TEXT | Timestamp of last update |

**Default Platforms:**
- **eBay** — 0.30 listing, 12.9% transaction, 2.2% payment
- **Poshmark** — 20% commission
- **Facebook Marketplace** — No fees
- **Mercari** — 10% commission
- **Whatnot** — 8% commission

**CRUD Operations:**
- `add_platform_fee()` — Add new platform
- `get_platform_fee(platform)` — Get platform fees
- `get_all_platform_fees()` — List all platform fees
- `update_platform_fee(platform, **kwargs)` — Modify fees
- `delete_platform_fee(fee_id)` — Remove platform

#### 7. **settings** — Application Configuration
Stores user preferences and API credentials (encrypted).

| Column | Type | Purpose |
|--------|------|---------|
| key | TEXT PK | Setting name |
| value | TEXT | Setting value |
| updated_at | TEXT | Timestamp of last update |

**CRUD Operations:**
- `set_setting(key, value)` — Save setting
- `get_setting(key)` — Retrieve setting

#### 8. **brands** — Brand/Manufacturer Lookup
Stores brand names used in inventory categorization.

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Unique identifier |
| name | TEXT | Brand name (unique) |
| created_at | TEXT | Timestamp of creation |

**CRUD Operations:**
- `add_brand(name)` — Create new brand
- `get_all_brands()` — List all brands
- `delete_brand(brand_id)` — Remove brand

---

## Analytics & Calculations Module

### Profit Calculations (`analytics/calculations.py`)

#### `calculate_profit(sale)`
Calculates net profit after all fees for a single sale.

**Formula:**
```
profit = (sale_price + shipping_collected) 
       - (cost_of_goods + shipping_cost + platform_fee + transaction_fee + promoted_fee)
```

**Returns:** Float (profit amount, can be negative)

---

#### `calculate_roi_by_category(start_date, end_date, year=None)`
Calculates Return on Investment by product category.

**Returns:** List of dicts with:
- `category` (str)
- `cost` (float) — Total cost of goods
- `profit` (float) — Total profit after fees
- `roi_pct` (float) — ROI percentage (profit/cost * 100)

**Sorted by:** ROI percentage (descending)

**Year Filtering:** Defaults to current year; can query any year

---

#### `calculate_turnover_rate(category, start_date, end_date, year=None)`
Calculates average days from listing to sold for a category.

**Formula:**
```
turnover_days = AVG(days_to_sell) for category in year
```

**Returns:** Float (average days, e.g., 14.5)

**Year Filtering:** Defaults to current year; can query any year

---

#### `calculate_platform_impact(platform, start_date, end_date, year=None)`
Analyzes profitability and fee impact by platform.

**Returns:** Dict with:
- `platform` (str)
- `sales_count` (int)
- `total_revenue` (float)
- `total_fees` (float)
- `total_cost` (float)
- `net_profit` (float)
- `fee_percentage` (float) — Fees as % of revenue

**Year Filtering:** Defaults to current year; can query any year

---

### Forecasting Module (`analytics/forecasting.py`)

#### `forecast_sales_units(period_days=30)`
Forecasts units to sell in future period using 90-day moving average.

**Formula:**
```
forecast = (sum of units in last 90 days) / 90 * period_days
```

**Returns:** Integer (rounded to nearest whole unit)

**Note:** Uses current year only

---

#### `forecast_revenue(period_days=30)`
Forecasts revenue for future period based on historical pricing and sales velocity.

**Formula:**
```
avg_revenue_per_sale = total_revenue / sale_count (last 90 days)
forecast_revenue = avg_revenue_per_sale * forecast_sales_units(period_days)
```

**Returns:** Float (rounded to 2 decimals)

**Note:** Uses current year only

---

#### `forecast_inventory_turnover(category)`
Forecasts days to sell for a product category.

**Returns:** Float (average days, e.g., 14.5)

**Note:** Based on last 180 days of current year data

---

#### `forecast_seasonal_impact(month)`
Analyzes seasonal sales patterns by month.

**Returns:** Dict with:
- `month` (int)
- `sales_count` (int)
- `total_revenue` (float)
- `avg_sale_price` (float)

**Note:** Uses current year only

---

### Reports Module (`analytics/reports.py`)

#### `generate_csv_report(start_date, end_date, filename=None, year=None)`
Exports sales transactions to CSV format.

**Columns:** All sales fields in structured format

**Returns:** String (CSV content) and optionally writes to file

**Year Filtering:** Defaults to current year

---

#### `generate_pdf_report(start_date, end_date, filename=None, year=None)`
Generates professional PDF report with summary and transaction details.

**Includes:**
- Summary statistics (sales count, revenue, profit, fees)
- Date range and year
- Detailed transaction table (first 50 rows)
- Summary by category and platform

**Returns:** Filename of generated PDF

**Year Filtering:** Defaults to current year

---

### Date Utilities (`analytics/date_utils.py`)

Helper functions for date range calculations:
- `get_current_year_range()` — Jan 1 to Dec 31 of current year
- `get_month_range(year, month)` — First to last day of month
- `get_last_n_days(n)` — Today minus n days to today
- `get_ytd_range()` — Year-to-date range

---

## User Interface Tabs

### 1. **Dashboard Tab** (`dashboard_tab.py`)

**Summary View:**
Primary overview of business performance for selected time period.

**Key Metrics:**
- Total Sales (count)
- Total Revenue
- Total Profit
- Profit Margin (%)
- Average Profit per Item

**Segmentation:**
- Sales by Platform (pie chart)
- Sales by Category (bar chart)
- Top 5 Categories by Profit

**Period Selector:**
- All Time
- This Year
- Last 30 days
- Last 90 days
- Custom date range

---

### 2. **Day Tab** (`day_tab.py`)

**Daily Performance View:**
Track sales and expenses for individual days.

**Features:**
- Daily sales list
- Daily totals (sales count, revenue, profit)
- Daily expenses summary
- Day-over-day comparison

**Filtering:** Selectable date picker

---

### 3. **Month Tab** (`month_tab.py`)

**Monthly Performance View:**
Analyze performance by calendar month.

**Features:**
- Month selector (calendar widget)
- Monthly totals (sales, revenue, profit, fees)
- Sales breakdown by category
- Top performers for month
- Month-over-month trends

**Year Selector:** Read any year; modify current year only

---

### 4. **Year Tab** (`year_tab.py`)

**Annual Performance View:**
Full-year business summary and trends.

**Features:**
- Annual totals (sales, revenue, profit, expenses)
- Monthly breakdown (table)
- Best/worst performing months
- Platform comparison
- Category performance ranking
- Seasonal trends visualization

**Year Selector:** Read any year; modify current year only

---

### 5. **Forecasting Tab** (`ui/forecasting_tab.py`)

**Predictive Analytics:**
Forecast future sales, revenue, and inventory turnover.

**Features:**
- 30-day sales forecast
- 30-day revenue forecast
- Inventory turnover by category
- Seasonal pattern analysis
- Trend visualization

**Input:** Customizable forecast period (days)

---

### 6. **Mileage Tab** (`mileage_tab.py`)

**Business Travel Tracking:**
Log sourcing trips and business-related mileage for tax deductions.

**Features:**
- Add/edit/delete mileage trips
- Odometer reading tracking (for verification)
- Trip purpose categorization (sourcing, delivery, business)
- Stores visited logging
- Year-to-date mileage summary
- Mileage deduction calculation (per IRS standards)

**Compliance:**
- Year-based isolation (read any year, write current only)
- Detailed trip logging for audit trails

---

### 7. **Reports Tab** (`reports_tab.py`)

**Export & Analysis Reports:**
Generate CSV and PDF reports for analysis and accounting.

**Report Types:**
- **CSV Export** — Full sales transaction export
- **PDF Report** — Professional summary with transaction details
- **Date Range Selector** — Any custom period
- **Year Selector** — Read any year; modify current year only

**PDF Report Includes:**
- Summary statistics
- Date range and year
- Top 50 transaction details
- Platform breakdown
- Category breakdown

---

### 8. **Settings Tab** (`settings_tab.py`)

**Configuration & Administration:**

**Subsections:**

#### eBay OAuth Configuration
- OAuth connection status
- Token refresh/disconnect
- Test API connectivity

#### Store Management
- Add/delete store sources
- List active stores
- Dropdown auto-population

#### Category Management
- Add/delete product categories
- List active categories
- Dropdown auto-population

#### Platform Fee Configuration
- View/edit fees for each platform (eBay, Poshmark, etc.)
- Listing fees, transaction percentages, etc.
- Custom platform addition

#### Expense Categories
- View/manage expense categories
- Assign category types (supplies, shipping, etc.)
- Add custom categories

#### Application Settings
- Theme/appearance (if applicable)
- Export location
- Default currency

---

### 9. **Inventory Tab** (`inventory_tab.py`)

**Inventory Management:**
Track items awaiting sale (not yet sold).

**Features:**
- Add new inventory items
- Edit existing items
- Delete items (with confirmation)
- Search/filter by any field
- Categorized dropdowns (auto-managed)
- Store source selection
- Brand selection
- Units and cost tracking

**Fields:**
- Listed Date, Item Title, Units, SKU
- Bin (storage location), Store, Category, Brand
- Cost, Notes, XP (custom field)

---

### 10. **Sales Tab** (`sales_tab.py`)

**Sales Logging & Tracking:**
Record and analyze completed transactions.

**Features:**
- Add new sales transaction
- View/edit sale details
- Delete sales (with confirmation)
- Export to CSV
- Profit calculations (automatic)
- Platform and category tracking
- Days-to-sell calculation
- Fee application by platform

**Fields:**
- Sold Date, Platform, Item Details
- Sale Price, Shipping Collected
- Cost of Goods, Shipping Cost
- Platform Fees, Transaction Fees, Promoted Fees
- Sales Tax Collected, Refunds
- Profit/Loss (calculated)

---

## Architecture & Data Protection

### Year-Based Read/Write Architecture

**Design Pattern:**
- **Read:** Unrestricted access to any year of historical data (for analysis and comparison)
- **Write:** Only current calendar year can be modified (for data integrity)

**Implementation:**
- All expense, mileage, and sales records include a `year` column
- Database functions enforce write protection via `WHERE year = current_year`
- Query functions accept optional `year` parameter for historical analysis
- UI tabs check current year before enabling edit/delete operations

**Rationale:** Prevents accidental modification of past tax records and historical data

**Functions with Write Protection:**
- `add_expense()` — Enforces current year only
- `delete_expense()` — Enforces current year only
- `add_mileage_trip()` — Enforces current year only
- `delete_mileage_trip()` — Enforces current year only

**Read-Only Historical Access:**
- `get_expenses_by_date_range(year=2024)` ✅ Allowed
- `get_total_expenses_by_category(year=2024)` ✅ Allowed
- `get_mileage_by_date_range(year=2024)` ✅ Allowed
- `calculate_roi_by_category(year=2024)` ✅ Allowed
- `forecast_*()` functions — Current year only (forecasting is forward-looking)

---

## Testing

### Test Suite Overview

**Total Test Cases:** 161 tests  
**Pass Rate:** 100%  
**Coverage:** 5 modules across database, calculations, forecasting, reporting

### Test Modules

#### 1. **test_database.py**
Database CRUD operations and schema validation.

**Test Classes:**
- TestExpenseCategories (5 tests) — Expense category creation, retrieval, deletion
  - Default categories creation
  - Field validation
  - CRUD operations

**Key Tests:**
- Verify 15 default expense categories created
- Confirm category_type field populated
- Test CRUD operations

---

#### 2. **test_calculations.py**
Profit calculations and analytics.

**Test Classes:**
- TestCalculateProfit — Profit calculation formula validation
- TestCalculateROIByCategory — ROI by category, year filtering
- TestCalculateTurnoverRate — Inventory turnover days to sell
- TestCalculatePlatformImpact — Platform fee analysis

**Key Coverage:**
- Profit formula: (revenue - costs)
- ROI percentage calculation
- Year filtering (current year only)
- Platform fee impact analysis

---

#### 3. **test_date_utils.py**
Date range calculations and utilities.

**Test Classes:**
- TestDateRanges — Month, year, and custom range calculations
- TestDateFormatting — ISO format handling

---

#### 4. **test_forecasting.py**
Sales forecasting and predictive analytics (161+ tests total).

**Test Classes:**
- TestForecastSalesUnits (6 tests) — 90-day moving average
- TestForecastRevenue (5 tests) — Revenue forecasting
- TestForecastInventoryTurnover (6 tests) — Turnover rate prediction
- TestForecastSeasonalImpact (7 tests) — Monthly seasonal analysis

**Key Coverage:**
- Forecasting uses last 90 days of current year only
- Handles edge cases (no sales, zero data)
- Custom period forecasting
- Seasonal pattern detection

---

#### 5. **test_reports.py**
Report generation and export functionality (50+ tests).

**Test Classes:**
- TestFormatCurrency (6 tests) — Currency formatting
- TestGetSalesForReport (5 tests) — Date/year filtering
- TestCalculateSummaryStats (4 tests) — Summary aggregation
- TestGenerateCSVReport (5 tests) — CSV export
- TestGeneratePDFReport (7 tests) — PDF report generation

**Key Coverage:**
- CSV export formatting
- PDF report creation with summaries
- Year filtering
- Large title handling
- Transaction limit enforcement (50 rows in detail)

---

## Installation Requirements

### System Requirements
- **Python:** 3.8 or higher (tested on 3.11.9)
- **OS:** Windows 10/11 (optimized for Windows; Linux/Mac untested)
- **RAM:** 512 MB minimum
- **Disk:** 100 MB for application and database

### Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt5 | 5.15.9 | Desktop GUI framework |
| PyQt5-sip | 12.13.0 | PyQt5 bindings |
| requests | 2.31.0 | HTTP client (eBay API) |
| Flask | 2.3.3 | Web framework (if API server needed) |
| Flask-CORS | 4.0.0 | CORS support (if API server needed) |
| gunicorn | 21.2.0 | WSGI server (if API server needed) |
| reportlab | (included) | PDF generation |
| cryptography | (included) | Credential encryption |

### Installation Steps

**From Source:**
```bash
# Clone repository
git clone https://github.com/yourrepo/panda-profit.git
cd panda-profit

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

**From Installer:**
```bash
# Download PandaProfit-0.1.0.msi
# Double-click to run installer
# Follow on-screen prompts
# Launch from Start Menu
```

---

## Performance Characteristics

- **Database:** SQLite with WAL (Write-Ahead Logging) for concurrent access
- **Data Loading:** Lazy-loaded by tab; no unnecessary database queries
- **Chart Rendering:** PyQt5 native (responsive)
- **CSV Export:** Handles 10,000+ transactions
- **PDF Report:** Generated in-memory (first 50 transactions in detail)

---

## Known Limitations & Future Enhancements

### Current Limitations
- Single-user local application (no network sync)
- SQLite database (suitable for single user; can upgrade to PostgreSQL)
- eBay OAuth flow requires manual setup (future: auto-import active listings)

### Planned Features (v0.2+)
- Automated eBay listing import/sync
- Multi-user support with cloud sync
- Advanced ML-based pricing suggestions
- Mobile companion app
- Integration with Etsy, Amazon, Poshmark APIs
- Custom workflow automation

---

## Licensing & Support

**License:** Proprietary — Trashed Panda  
**Support Email:** tomnissley@gmail.com  

**Commercial Licensing:**
Panda Profit uses server-based licensing via thetrashedpanda.com. License keys use the RA- prefix and are managed through the shared licensing system with other Trashed Panda applications.

---

## Summary Statistics

- **Database Tables:** 8 core tables
- **CRUD Functions:** 60+ database operations
- **Analytics Functions:** 12+ calculation and forecasting functions
- **UI Tabs:** 10 tabs covering all business aspects
- **Test Coverage:** 161 tests, 100% pass rate
- **Lines of Code:** ~8,000+ (Python + UI)
- **Default Data:** 15 expense categories, 5 platforms pre-configured

