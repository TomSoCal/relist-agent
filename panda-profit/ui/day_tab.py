from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime
import database as db
from analytics.calculations import calculate_profit


class DayTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Load today's data on startup
        self.load_day_data()

    def init_ui(self):
        """Build the Day Tab layout with date picker, stats, and sales table."""
        layout = QVBoxLayout()

        # Top section: Date picker
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Select Date:"))

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_day_data)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()

        layout.addLayout(date_layout)

        # Summary stats section
        stats_layout = QHBoxLayout()

        self.sales_count_label = QLabel("Sales Today: 0")
        self.sales_count_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.sales_count_label)

        self.revenue_label = QLabel("Revenue: $0.00")
        self.revenue_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        stats_layout.addWidget(self.revenue_label)

        self.profit_label = QLabel("Profit: $0.00")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        stats_layout.addWidget(self.profit_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Sales table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Item", "Platform", "Price", "Shipping", "Fees", "Cost", "Profit", "Category"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_day_data(self):
        """Query and display sales for the selected date."""
        # Get selected date
        selected_date = self.date_edit.date().toPyDate()
        date_str = selected_date.strftime("%m/%d/%Y")

        # Get current year
        current_year = datetime.now().year

        # Query database for sales on this date in current year
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        c.execute('''
            SELECT * FROM sales
            WHERE sold_date = ? AND year = ?
            ORDER BY sold_date DESC
        ''', (date_str, current_year))

        sales = c.fetchall()
        conn.close()

        # Populate table
        self.table.setRowCount(len(sales))

        total_revenue = 0
        total_profit = 0

        for row, sale in enumerate(sales):
            # Calculate values
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            total_fees = (sale.get('platform_fee', 0) or 0) + \
                        (sale.get('transaction_fee', 0) or 0) + \
                        (sale.get('promoted_fee', 0) or 0)
            cost = sale.get('cost_of_goods', 0) or 0
            profit = calculate_profit(sale)

            total_revenue += revenue
            total_profit += profit

            # Item
            self.table.setItem(row, 0, QTableWidgetItem(sale.get('item_title', '')))

            # Platform
            self.table.setItem(row, 1, QTableWidgetItem(sale.get('platform', '') or ''))

            # Price
            price_item = QTableWidgetItem(f"${sale.get('sale_price', 0) or 0:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, price_item)

            # Shipping
            shipping = (sale.get('shipping_collected', 0) or 0) - (sale.get('shipping_cost', 0) or 0)
            shipping_item = QTableWidgetItem(f"${shipping:.2f}")
            shipping_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, shipping_item)

            # Fees
            fees_item = QTableWidgetItem(f"${total_fees:.2f}")
            fees_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, fees_item)

            # Cost
            cost_item = QTableWidgetItem(f"${cost:.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, cost_item)

            # Profit - color-coded
            profit_item = QTableWidgetItem(f"${profit:.2f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if profit >= 0:
                profit_item.setForeground(QColor("green"))
            else:
                profit_item.setForeground(QColor("red"))
            self.table.setItem(row, 6, profit_item)

            # Category
            self.table.setItem(row, 7, QTableWidgetItem(sale.get('category', '') or ''))

        # Update summary labels
        self.sales_count_label.setText(f"Sales Today: {len(sales)}")
        self.revenue_label.setText(f"Revenue: ${total_revenue:,.2f}")

        # Update profit label with color coding
        if total_profit >= 0:
            self.profit_label.setText(f"Profit: ${total_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        else:
            self.profit_label.setText(f"Profit: ${total_profit:,.2f}")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")
