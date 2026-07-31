from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
import calendar
import database as db
from analytics.calculations import calculate_roi_by_category, calculate_profit


class MonthTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Load current month/year data on startup
        self.load_month_data()

    def init_ui(self):
        """Build the Month Tab layout with date selectors, stats, and tables."""
        layout = QVBoxLayout()

        # Top section: Month/Year selectors
        selector_layout = QHBoxLayout()

        # Month selector
        selector_layout.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        months = [calendar.month_name[i] for i in range(1, 13)]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.currentIndexChanged.connect(self.load_month_data)
        selector_layout.addWidget(self.month_combo)

        # Year selector
        selector_layout.addWidget(QLabel("Year:"))
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setMinimum(2020)
        self.year_spinbox.setMaximum(2050)
        self.year_spinbox.setValue(datetime.now().year)
        self.year_spinbox.valueChanged.connect(self.load_month_data)
        selector_layout.addWidget(self.year_spinbox)

        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Summary stats section
        stats_layout = QHBoxLayout()

        self.sales_count_label = QLabel("Sales: 0")
        self.sales_count_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.sales_count_label)

        self.revenue_label = QLabel("Revenue: $0.00")
        self.revenue_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.revenue_label)

        self.expenses_label = QLabel("Expenses: $0.00")
        self.expenses_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.expenses_label)

        self.profit_label = QLabel("Profit: $0.00")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        stats_layout.addWidget(self.profit_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # ROI by Category table
        roi_label = QLabel("ROI by Category")
        roi_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(roi_label)

        self.roi_table = QTableWidget()
        self.roi_table.setColumnCount(4)
        self.roi_table.setHorizontalHeaderLabels([
            "Category", "Cost", "Profit", "ROI %"
        ])
        self.roi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.roi_table.setMaximumHeight(200)

        layout.addWidget(self.roi_table)

        # Sales by Platform table
        platform_label = QLabel("Sales by Platform")
        platform_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(platform_label)

        self.platform_table = QTableWidget()
        self.platform_table.setColumnCount(4)
        self.platform_table.setHorizontalHeaderLabels([
            "Platform", "Units Sold", "Revenue", "Fees"
        ])
        self.platform_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.platform_table)

        self.setLayout(layout)

    def load_month_data(self):
        """Query and display sales data for the selected month/year."""
        # Get selected month and year
        selected_month = self.month_combo.currentIndex() + 1  # 1-12
        selected_year = self.year_spinbox.value()

        # Build date range for the selected month/year
        last_day = calendar.monthrange(selected_year, selected_month)[1]
        start_date = f"{selected_year:04d}-{selected_month:02d}-01"
        end_date = f"{selected_year:04d}-{selected_month:02d}-{last_day:02d}"

        # Query database for sales in selected month/year
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()

        c.execute('''
            SELECT * FROM sales
            WHERE sold_date BETWEEN ? AND ? AND year = ?
            ORDER BY sold_date DESC
        ''', (start_date, end_date, selected_year))

        sales = c.fetchall()
        conn.close()

        # Calculate summary statistics
        total_sales_count = len(sales)
        total_revenue = 0
        total_expenses = 0
        total_profit = 0

        for sale in sales:
            # Calculate revenue (sale price + shipping collected)
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            total_revenue += revenue

            # Calculate expenses (cost + shipping cost + all fees)
            cost = sale.get('cost_of_goods', 0) or 0
            shipping_cost = sale.get('shipping_cost', 0) or 0
            platform_fee = sale.get('platform_fee', 0) or 0
            transaction_fee = sale.get('transaction_fee', 0) or 0
            promoted_fee = sale.get('promoted_fee', 0) or 0

            expenses = cost + shipping_cost + platform_fee + transaction_fee + promoted_fee
            total_expenses += expenses

            # Calculate profit
            profit = calculate_profit(sale)
            total_profit += profit

        # Update summary labels
        self.sales_count_label.setText(f"Sales: {total_sales_count}")
        self.revenue_label.setText(f"Revenue: ${total_revenue:,.2f}")
        self.expenses_label.setText(f"Expenses: ${total_expenses:,.2f}")

        # Update profit label with color coding
        if total_profit >= 0:
            self.profit_label.setText(f"Profit: ${total_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        else:
            self.profit_label.setText(f"Profit: ${total_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")

        # Load ROI by Category data
        self._populate_roi_table(start_date, end_date, selected_year)

        # Load Sales by Platform data
        self._populate_platform_table(start_date, end_date, selected_year)

    def _populate_roi_table(self, start_date, end_date, current_year):
        """Populate the ROI by Category table."""
        # Get ROI data from analytics module
        roi_data = calculate_roi_by_category(start_date, end_date)

        # Populate table
        self.roi_table.setRowCount(len(roi_data))

        for row, item in enumerate(roi_data):
            # Category
            category_item = QTableWidgetItem(item['category'] or 'Uncategorized')
            self.roi_table.setItem(row, 0, category_item)

            # Cost
            cost_item = QTableWidgetItem(f"${item['cost']:,.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.roi_table.setItem(row, 1, cost_item)

            # Profit
            profit_item = QTableWidgetItem(f"${item['profit']:,.2f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if item['profit'] >= 0:
                profit_item.setForeground(QColor("green"))
            else:
                profit_item.setForeground(QColor("red"))
            self.roi_table.setItem(row, 2, profit_item)

            # ROI %
            roi_item = QTableWidgetItem(f"{item['roi_pct']:.1f}%")
            roi_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.roi_table.setItem(row, 3, roi_item)

    def _populate_platform_table(self, start_date, end_date, selected_year):
        """Populate the Sales by Platform table."""
        # Query database to get all platforms and their sales data
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()

        # Get distinct platforms for the selected month/year
        c.execute('''
            SELECT DISTINCT platform FROM sales
            WHERE sold_date BETWEEN ? AND ? AND year = ? AND platform IS NOT NULL
            ORDER BY platform
        ''', (start_date, end_date, selected_year))

        platforms = c.fetchall()

        platform_data = []
        for platform_row in platforms:
            platform = platform_row['platform']

            # Get aggregated data for this platform
            c.execute('''
                SELECT
                    COUNT(id) as units_sold,
                    SUM(COALESCE(sale_price, 0) + COALESCE(shipping_collected, 0)) as total_revenue,
                    SUM(COALESCE(platform_fee, 0) + COALESCE(transaction_fee, 0) + COALESCE(promoted_fee, 0)) as total_fees
                FROM sales
                WHERE sold_date BETWEEN ? AND ? AND platform = ? AND year = ?
            ''', (start_date, end_date, platform, selected_year))

            result = c.fetchone()
            if result:
                platform_data.append({
                    'platform': platform,
                    'units_sold': result['units_sold'] or 0,
                    'revenue': result['total_revenue'] or 0,
                    'fees': result['total_fees'] or 0,
                })

        conn.close()

        # Populate table
        self.platform_table.setRowCount(len(platform_data))

        for row, item in enumerate(platform_data):
            # Platform
            platform_item = QTableWidgetItem(item['platform'])
            self.platform_table.setItem(row, 0, platform_item)

            # Units Sold
            units_item = QTableWidgetItem(str(item['units_sold']))
            units_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.platform_table.setItem(row, 1, units_item)

            # Revenue
            revenue_item = QTableWidgetItem(f"${item['revenue']:,.2f}")
            revenue_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.platform_table.setItem(row, 2, revenue_item)

            # Fees
            fees_item = QTableWidgetItem(f"${item['fees']:,.2f}")
            fees_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.platform_table.setItem(row, 3, fees_item)
