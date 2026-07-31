# Panda Profit

**Premium Reseller Sales & Profit Tracking for eBay and Multi-Platform Sellers**

Panda Profit is a comprehensive business management application for resellers. Track inventory, log sales across multiple platforms, manage expenses, record mileage deductions, and analyze profitability with advanced forecasting and analytics.

---

## Quick Start

### Installation

**Option 1: Installer (Recommended)**
1. Download `PandaProfit-0.1.0.msi`
2. Run installer and follow prompts
3. Launch from Start Menu or Desktop shortcut

**Option 2: From Source**
```bash
# Install Python 3.8+
git clone https://github.com/yourrepo/panda-profit.git
cd panda-profit
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### First Run

1. Database initializes automatically on first launch
2. Configure eBay OAuth in Settings tab (optional, for future auto-import)
3. Adjust platform fees if needed (eBay, Poshmark, Facebook, Mercari, Whatnot pre-configured)
4. Start tracking: add inventory, log sales, or record expenses

---

## Features

### Dashboard
- Real-time summary of sales, revenue, profit, and margins
- Performance trends by platform and category
- Customizable time periods (All Time, This Year, Last 30/90 days)

### Inventory Management
- Add/edit/delete items awaiting sale
- Track: listed date, title, units, SKU, bin, store, category, brand, cost
- Search and filter by any field

### Sales Tracking
- Log completed sales with full profit calculations
- Supports: eBay, Poshmark, Facebook Marketplace, Mercari, Whatnot (custom platforms)
- Auto-calculate: profit/loss, days-to-sell, fee impact by platform
- Export to CSV for further analysis

### Daily / Monthly / Yearly Views
- **Day Tab** — Daily performance summary
- **Month Tab** — Monthly analysis with trends and top performers
- **Year Tab** — Annual totals, month-by-month breakdown, seasonal patterns

### Expense Tracking
- Log business expenses (supplies, shipping, equipment, advertising, rent, utilities, etc.)
- 15 pre-configured expense categories (customizable)
- Year-based (read any year, modify current year only)
- Expense totals by category

### Mileage Tracking
- Record sourcing trips and business travel
- Track: trip date, miles, odometer readings, stores visited, purpose, notes
- Tax deduction calculation (per IRS standards)
- Sourcing efficiency analysis

### Advanced Analytics
- **ROI by Category** — Profit and return on investment for each product category
- **Platform Analysis** — Fee impact and profitability by platform
- **Turnover Rates** — Average days to sell by category
- **Seasonal Patterns** — Sales trends by month

### Forecasting
- Predict 30-day sales units (90-day moving average)
- Forecast revenue (average sale price × forecast units)
- Inventory turnover prediction by category
- Seasonal impact analysis

### Reports
- **CSV Export** — Full transaction export for accounting/analysis
- **PDF Report** — Professional summary with transaction details and category/platform breakdown
- Custom date ranges and year selection (read any year, modify current year only)

### Settings & Configuration
- **eBay OAuth** — Connect for future automation
- **Store Management** — Add/delete inventory sources
- **Category Management** — Organize products for analysis
- **Platform Fees** — Configure or update fees for each platform
- **Expense Categories** — Add custom expense types

---

## Database Architecture

**Database:** SQLite (local, no cloud sync)  
**Core Tables:**
- `inventory` — Items awaiting sale
- `sales` — Completed transactions with full profit calculations
- `expenses` — Business expenses by category
- `mileage` — Sourcing trips and business travel
- `brands` — Manufacturer/brand lookup
- `settings` — Application configuration
- `expense_categories` — Expense type definitions
- `platform_fees` — Fee structure by platform

**Year-Based Design:** Read-only access to historical data; current year only modifiable (protects tax records)

---

## Analytics & Calculations

### Profit Formula
```
Profit = (Sale Price + Shipping Collected)
       - (Cost of Goods + Shipping Cost + Platform Fee + Transaction Fee + Promoted Fee)
```

### Key Metrics
- **ROI by Category** — Profit ÷ Cost × 100
- **Turnover Rate** — Average days from listing to sold
- **Platform Impact** — Fees as % of revenue
- **Sales Forecast** — 90-day moving average × period days
- **Revenue Forecast** — Avg revenue per sale × forecast units

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **UI Framework** | PyQt5 5.15.9 |
| **Database** | SQLite 3 with WAL mode |
| **Reports** | ReportLab (PDF generation) |
| **API Client** | Requests 2.31.0 |
| **Security** | Cryptography library |
| **Testing** | Pytest (161 tests, 100% pass rate) |
| **Bundling** | PyInstaller |
| **Installer** | WiX Toolset |

---

## System Requirements

- **OS:** Windows 10/11 (Linux/Mac untested)
- **Python:** 3.8 or higher (3.11.9 tested)
- **RAM:** 512 MB minimum
- **Disk:** 100 MB application + database
- **Network:** Optional (only for eBay OAuth)

---

## Project Structure

```
panda-profit/
├── main.py                          # App entry point
├── database.py                      # SQLite CRUD operations
├── config.py                        # Configuration & constants
├── license_check.py                 # License validation
├── panda_suite_api.py               # PandaSuite licensing integration
├── api.py                           # eBay API client
├── oauth_setup.py                   # OAuth configuration
├── requirements.txt                 # Python dependencies
├── ui/                              # User interface
│   ├── main_window.py               # Main application window (10 tabs)
│   ├── dashboard_tab.py             # Summary dashboard
│   ├── day_tab.py                   # Daily view
│   ├── month_tab.py                 # Monthly view
│   ├── year_tab.py                  # Annual view
│   ├── inventory_tab.py             # Inventory management
│   ├── sales_tab.py                 # Sales logging
│   ├── settings_tab.py              # Settings & configuration
│   ├── mileage_tab.py               # Mileage tracking
│   ├── reports_tab.py               # CSV/PDF export
│   └── analytics_tab.py             # Analytics & forecasting
├── analytics/                       # Analytics & forecasting engine
│   ├── calculations.py              # ROI, turnover, platform analysis
│   ├── forecasting.py               # Sales/revenue predictions
│   ├── reports.py                   # CSV/PDF report generation
│   └── date_utils.py                # Date range calculations
├── tests/                           # Test suite (161 tests)
│   ├── test_database.py
│   ├── test_calculations.py
│   ├── test_forecasting.py
│   ├── test_reports.py
│   └── test_date_utils.py
├── docs/                            # Documentation
└── panda_profit.db                  # SQLite database (created on first run)
```

---

## Testing

**Test Coverage:** 161 tests across 5 modules  
**Pass Rate:** 100%  
**Focus Areas:**
- Database CRUD operations
- Profit calculations and ROI analysis
- Sales forecasting and predictions
- PDF/CSV report generation
- Date range calculations
- Year-based filtering

Run tests:
```bash
python -m pytest tests/ -v
```

---

## Licensing & Support

**License:** Proprietary — Trashed Panda  
**Commercial Licensing:** Server-based via thetrashedpanda.com (RA- prefix)

**Support:** tomnissley@gmail.com

**Documentation:** See `FEATURES_COMPLETE.md` for comprehensive feature reference

---

## Build & Deployment

### Build Executable
```bash
pip install pyinstaller
python build_installer.py
# Output: dist/PandaProfit.exe (121 MB)
```

### Build MSI Installer
```bash
# Requires WiX Toolset: https://wixtoolset.org/
python build_installer.py --msi
# Output: dist/PandaProfit-0.1.0.msi
```

---

## Future Roadmap

### v0.2
- Inventory audit/sync features
- Advanced multi-year comparison
- Enhanced forecasting models

### v0.3+
- Automated eBay listing import/sync
- Multi-user support with cloud sync
- Etsy, Amazon, Poshmark API integration
- Mobile companion app
- ML-based pricing suggestions
- Custom workflow automation

---

## Version History

**v0.1.0 (Current)** — July 30, 2026
- Complete sales and inventory tracking
- Full analytics and forecasting engine
- Expense and mileage tracking
- Multi-tab dashboard with calendar views
- CSV and PDF report generation
- eBay OAuth support
- 161 tests, 100% pass rate
- Commercial licensing integration
