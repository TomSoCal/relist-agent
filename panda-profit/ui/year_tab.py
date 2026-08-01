from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
                            QTableWidget, QTableWidgetItem, QHeaderView, QAbstractButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from datetime import datetime
import calendar
import database as db
from analytics.calculations import calculate_profit


class YearTab(QWidget):
    """Year Tab for YTD summary and year-over-year analysis."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        # Load current year data on startup
        self.load_year_data()

    def init_ui(self):
        """Build the Year Tab layout with year selector, YTD summary, and comparison tables."""
        layout = QVBoxLayout()

        # Top section: Year selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Year:"))

        self.year_spinbox = QSpinBox()
        self.year_spinbox.setMinimum(2020)
        self.year_spinbox.setMaximum(2050)
        self.year_spinbox.setValue(datetime.now().year)
        self.year_spinbox.valueChanged.connect(self.load_year_data)
        selector_layout.addWidget(self.year_spinbox)
        selector_layout.addStretch()

        layout.addLayout(selector_layout)

        # YTD Summary stats section
        stats_layout = QHBoxLayout()

        self.sales_count_label = QLabel("Sales: 0")
        self.sales_count_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.sales_count_label)

        self.revenue_label = QLabel("Revenue: $0.00")
        self.revenue_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.revenue_label)

        self.profit_label = QLabel("Profit: $0.00")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        stats_layout.addWidget(self.profit_label)

        self.margin_label = QLabel("Margin %: 0.0%")
        self.margin_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.margin_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Monthly Breakdown table
        monthly_label = QLabel("Monthly Breakdown")
        monthly_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(monthly_label)

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels([
            "Month", "Sales", "Revenue", "Expenses", "Profit"
        ])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.verticalHeader().setStyleSheet("background-color: #1a3a5e; color: #00ff88;")
        self.monthly_table.horizontalHeader().setStyleSheet("background-color: #1a3a5e; color: #00ff88;")
        self.monthly_table.setStyleSheet("QTableWidget { background-color: #0d0d1a; } QTableWidget::item { background-color: #0d0d1a; }")
        # Style the corner button directly
        self._style_corner_button(self.monthly_table)
        self.monthly_table.setMaximumHeight(300)

        layout.addWidget(self.monthly_table)

        # Year-over-Year Comparison table
        yoy_label = QLabel("Year-over-Year Comparison")
        yoy_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(yoy_label)

        self.yoy_table = QTableWidget()
        self.yoy_table.setColumnCount(4)
        self.yoy_table.setHorizontalHeaderLabels([
            "Metric", "Last Year", "This Year", "Growth %"
        ])
        self.yoy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.yoy_table.verticalHeader().setStyleSheet("background-color: #1a3a5e; color: #00ff88;")
        self.yoy_table.horizontalHeader().setStyleSheet("background-color: #1a3a5e; color: #00ff88;")
        self.yoy_table.setStyleSheet("QTableWidget { background-color: #0d0d1a; } QTableWidget::item { background-color: #0d0d1a; }")
        # Style the corner button directly
        self._style_corner_button(self.yoy_table)

        layout.addWidget(self.yoy_table)

        self.setLayout(layout)

    def load_year_data(self):
        """Query and display sales data for the selected year."""
        selected_year = self.year_spinbox.value()

        # Query database for sales in selected year
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()

        c.execute('''
            SELECT * FROM sales
            WHERE year = ?
            ORDER BY sold_date DESC
        ''', (selected_year,))

        sales = c.fetchall()
        conn.close()

        # Calculate YTD totals
        ytd_sales_count = len(sales)
        ytd_revenue = 0
        ytd_expenses = 0
        ytd_profit = 0

        for sale in sales:
            # Calculate revenue (sale price + shipping collected)
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            ytd_revenue += revenue

            # Calculate expenses (cost + shipping cost + all fees)
            cost = sale.get('cost_of_goods', 0) or 0
            shipping_cost = sale.get('shipping_cost', 0) or 0
            platform_fee = sale.get('platform_fee', 0) or 0
            transaction_fee = sale.get('transaction_fee', 0) or 0
            promoted_fee = sale.get('promoted_fee', 0) or 0

            expenses = cost + shipping_cost + platform_fee + transaction_fee + promoted_fee
            ytd_expenses += expenses

            # Calculate profit
            profit = calculate_profit(sale)
            ytd_profit += profit

        # Calculate margin percentage
        ytd_margin = (ytd_profit / ytd_revenue * 100) if ytd_revenue > 0 else 0

        # Update YTD summary labels
        self.sales_count_label.setText(f"Sales: {ytd_sales_count}")
        self.revenue_label.setText(f"Revenue: ${ytd_revenue:,.2f}")

        # Update profit label with color coding
        if ytd_profit >= 0:
            self.profit_label.setText(f"Profit: ${ytd_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        else:
            self.profit_label.setText(f"Profit: ${ytd_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")

        self.margin_label.setText(f"Margin %: {ytd_margin:.1f}%")

        # Load monthly breakdown data
        self._populate_monthly_table(selected_year)

        # Load year-over-year comparison
        self._populate_yoy_table(selected_year)

    def _populate_monthly_table(self, selected_year):
        """Populate the Monthly Breakdown table for the selected year."""
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()

        monthly_data = []

        # Loop through all 12 months
        for month in range(1, 13):
            month_name = calendar.month_name[month]

            # Query sales for this month/year
            c.execute('''
                SELECT * FROM sales
                WHERE year = ? AND month = ?
                ORDER BY sold_date DESC
            ''', (selected_year, month))

            sales = c.fetchall()

            # Calculate monthly totals
            month_sales_count = len(sales)
            month_revenue = 0
            month_expenses = 0
            month_profit = 0

            for sale in sales:
                # Calculate revenue
                revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
                month_revenue += revenue

                # Calculate expenses
                cost = sale.get('cost_of_goods', 0) or 0
                shipping_cost = sale.get('shipping_cost', 0) or 0
                platform_fee = sale.get('platform_fee', 0) or 0
                transaction_fee = sale.get('transaction_fee', 0) or 0
                promoted_fee = sale.get('promoted_fee', 0) or 0

                expenses = cost + shipping_cost + platform_fee + transaction_fee + promoted_fee
                month_expenses += expenses

                # Calculate profit
                profit = (revenue - expenses)
                month_profit += profit

            monthly_data.append({
                'month': month_name,
                'sales': month_sales_count,
                'revenue': month_revenue,
                'expenses': month_expenses,
                'profit': month_profit,
            })

        conn.close()

        # Populate table
        self.monthly_table.setRowCount(len(monthly_data))

        for row, item in enumerate(monthly_data):
            # Month
            month_item = QTableWidgetItem(item['month'])
            self.monthly_table.setItem(row, 0, month_item)

            # Sales
            sales_item = QTableWidgetItem(str(item['sales']))
            sales_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.monthly_table.setItem(row, 1, sales_item)

            # Revenue
            revenue_item = QTableWidgetItem(f"${item['revenue']:,.2f}")
            revenue_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.monthly_table.setItem(row, 2, revenue_item)

            # Expenses
            expenses_item = QTableWidgetItem(f"${item['expenses']:,.2f}")
            expenses_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.monthly_table.setItem(row, 3, expenses_item)

            # Profit
            profit_item = QTableWidgetItem(f"${item['profit']:,.2f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if item['profit'] >= 0:
                profit_item.setForeground(QColor("green"))
            else:
                profit_item.setForeground(QColor("red"))
            self.monthly_table.setItem(row, 4, profit_item)

    def _populate_yoy_table(self, selected_year):
        """Populate the Year-over-Year Comparison table."""
        # Query data for selected year and previous year
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()

        # Get data for selected year
        c.execute('SELECT * FROM sales WHERE year = ?', (selected_year,))
        this_year_sales = c.fetchall()

        # Get data for previous year
        previous_year = selected_year - 1
        c.execute('SELECT * FROM sales WHERE year = ?', (previous_year,))
        last_year_sales = c.fetchall()

        conn.close()

        # Calculate totals for this year
        this_year_units = len(this_year_sales)
        this_year_revenue = 0
        this_year_profit = 0

        for sale in this_year_sales:
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            this_year_revenue += revenue

            profit = (revenue -
                     ((sale.get('cost_of_goods', 0) or 0) +
                      (sale.get('shipping_cost', 0) or 0) +
                      (sale.get('platform_fee', 0) or 0) +
                      (sale.get('transaction_fee', 0) or 0) +
                      (sale.get('promoted_fee', 0) or 0)))
            this_year_profit += profit

        # Calculate totals for last year
        last_year_units = len(last_year_sales)
        last_year_revenue = 0
        last_year_profit = 0

        for sale in last_year_sales:
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            last_year_revenue += revenue

            profit = (revenue -
                     ((sale.get('cost_of_goods', 0) or 0) +
                      (sale.get('shipping_cost', 0) or 0) +
                      (sale.get('platform_fee', 0) or 0) +
                      (sale.get('transaction_fee', 0) or 0) +
                      (sale.get('promoted_fee', 0) or 0)))
            last_year_profit += profit

        # Calculate growth percentages
        units_growth = ((this_year_units - last_year_units) / last_year_units * 100) if last_year_units > 0 else 0
        revenue_growth = ((this_year_revenue - last_year_revenue) / last_year_revenue * 100) if last_year_revenue > 0 else 0
        profit_growth = ((this_year_profit - last_year_profit) / last_year_profit * 100) if last_year_profit > 0 else 0

        # Prepare YoY data
        yoy_data = [
            {
                'metric': 'Units Sold',
                'last_year': last_year_units,
                'this_year': this_year_units,
                'growth': units_growth,
            },
            {
                'metric': 'Revenue',
                'last_year': last_year_revenue,
                'this_year': this_year_revenue,
                'growth': revenue_growth,
            },
            {
                'metric': 'Profit',
                'last_year': last_year_profit,
                'this_year': this_year_profit,
                'growth': profit_growth,
            },
        ]

        # Populate table
        self.yoy_table.setRowCount(len(yoy_data))

        for row, item in enumerate(yoy_data):
            # Metric
            metric_item = QTableWidgetItem(item['metric'])
            self.yoy_table.setItem(row, 0, metric_item)

            # Last Year
            if item['metric'] == 'Units Sold':
                last_year_item = QTableWidgetItem(str(item['last_year']))
            else:
                last_year_item = QTableWidgetItem(f"${item['last_year']:,.2f}")
            last_year_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.yoy_table.setItem(row, 1, last_year_item)

            # This Year
            if item['metric'] == 'Units Sold':
                this_year_item = QTableWidgetItem(str(item['this_year']))
            else:
                this_year_item = QTableWidgetItem(f"${item['this_year']:,.2f}")
            this_year_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.yoy_table.setItem(row, 2, this_year_item)

            # Growth %
            growth_item = QTableWidgetItem(f"{item['growth']:.1f}%")
            growth_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if item['growth'] >= 0:
                growth_item.setForeground(QColor("green"))
            else:
                growth_item.setForeground(QColor("red"))
            self.yoy_table.setItem(row, 3, growth_item)

    def _style_corner_button(self, table):
        """Paint over the corner button area with dark background."""
        # The corner button seems to be rendering white regardless of our styling attempts
        # Try a different approach: set the viewport background directly
        dark_color = QColor("#1a3a5e")

        # Style the header viewport (the area containing the corner button)
        header = table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView {
                background-color: #1a3a5e;
            }
            QHeaderView::section {
                background-color: #1a3a5e;
                color: #00ff88;
                padding: 5px;
                border: none;
                border-right: 1px solid #222222;
                border-bottom: 1px solid #222222;
            }
        """)

        # Also set vertical header
        v_header = table.verticalHeader()
        v_header.setStyleSheet("""
            QHeaderView {
                background-color: #1a3a5e;
            }
            QHeaderView::section {
                background-color: #1a3a5e;
                color: #00ff88;
                padding: 5px;
                border: none;
                border-right: 1px solid #222222;
                border-bottom: 1px solid #222222;
            }
        """)

        # Try to style any buttons we can find (as backup)
        buttons = table.findChildren(QAbstractButton)
        for button in buttons:
            button.setStyleSheet("background-color: #1a3a5e; border: none;")
