"""Analytics tab for forecasting and seasonal insights.

Displays:
- Sales and revenue forecasts based on period selector
- Inventory turnover analysis by category
- Seasonal sales patterns by month
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from analytics.forecasting import (forecast_sales_units, forecast_revenue,
                                   forecast_inventory_turnover, forecast_seasonal_impact)


class AnalyticsTab(QWidget):
    """Analytics tab showing forecasts and seasonal insights."""

    def __init__(self):
        """Initialize the Analytics tab."""
        super().__init__()
        self.init_ui()
        self.update_forecasts()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Forecast Period selector
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Forecast Period (days):"))
        self.period_spinbox = QSpinBox()
        self.period_spinbox.setMinimum(1)
        self.period_spinbox.setMaximum(365)
        self.period_spinbox.setValue(30)
        self.period_spinbox.valueChanged.connect(self.update_forecasts)
        period_layout.addWidget(self.period_spinbox)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        # Forecast Section Title
        forecast_title = QLabel("Sales Forecast")
        forecast_title_font = QFont()
        forecast_title_font.setBold(True)
        forecast_title_font.setPointSize(11)
        forecast_title.setFont(forecast_title_font)
        layout.addWidget(forecast_title)

        # Forecast metrics (Units and Revenue)
        metrics_layout = QHBoxLayout()

        # Units forecast
        units_label = QLabel("Units (next")
        units_label_font = QFont()
        units_label_font.setBold(True)
        units_label.setFont(units_label_font)
        metrics_layout.addWidget(units_label)

        self.units_period_label = QLabel("30 days")
        metrics_layout.addWidget(self.units_period_label)

        units_colon = QLabel(")")
        metrics_layout.addWidget(units_colon)

        self.units_value_label = QLabel("0 units")
        self.units_value_label_font = QFont()
        self.units_value_label_font.setBold(True)
        self.units_value_label.setFont(self.units_value_label_font)
        metrics_layout.addWidget(self.units_value_label)

        metrics_layout.addStretch()

        # Revenue forecast
        revenue_label = QLabel("Revenue (next")
        revenue_label_font = QFont()
        revenue_label_font.setBold(True)
        revenue_label.setFont(revenue_label_font)
        metrics_layout.addWidget(revenue_label)

        self.revenue_period_label = QLabel("30 days")
        metrics_layout.addWidget(self.revenue_period_label)

        revenue_colon = QLabel(")")
        metrics_layout.addWidget(revenue_colon)

        self.revenue_value_label = QLabel("$0.00")
        self.revenue_value_label_font = QFont()
        self.revenue_value_label_font.setBold(True)
        self.revenue_value_label.setFont(self.revenue_value_label_font)
        metrics_layout.addWidget(self.revenue_value_label)

        layout.addLayout(metrics_layout)
        layout.addSpacing(20)

        # Inventory Turnover by Category
        turnover_title = QLabel("Inventory Turnover by Category")
        turnover_title_font = QFont()
        turnover_title_font.setBold(True)
        turnover_title_font.setPointSize(11)
        turnover_title.setFont(turnover_title_font)
        layout.addWidget(turnover_title)

        self.turnover_table = QTableWidget()
        self.turnover_table.setColumnCount(3)
        self.turnover_table.setHorizontalHeaderLabels([
            "Category", "Avg Days to Sell", "Items Sold (90d)"
        ])
        self.turnover_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.turnover_table.setMaximumHeight(200)
        layout.addWidget(self.turnover_table)

        layout.addSpacing(20)

        # Seasonal Analysis by Month
        seasonal_title = QLabel("Seasonal Analysis")
        seasonal_title_font = QFont()
        seasonal_title_font.setBold(True)
        seasonal_title_font.setPointSize(11)
        seasonal_title.setFont(seasonal_title_font)
        layout.addWidget(seasonal_title)

        self.seasonal_table = QTableWidget()
        self.seasonal_table.setColumnCount(4)
        self.seasonal_table.setHorizontalHeaderLabels([
            "Month", "Avg Sales", "Avg Revenue", "Top Category"
        ])
        self.seasonal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.seasonal_table)

        self.setLayout(layout)

    def update_forecasts(self):
        """Update forecast displays based on selected period."""
        period_days = self.period_spinbox.value()

        # Update period labels
        self.units_period_label.setText(f"{period_days} days")
        self.revenue_period_label.setText(f"{period_days} days")

        # Get forecast data
        units_forecast = forecast_sales_units(period_days)
        revenue_forecast = forecast_revenue(period_days)

        # Update forecast labels
        self.units_value_label.setText(f"{units_forecast} units")
        self.revenue_value_label.setText(f"${revenue_forecast:,.2f}")

        # Update inventory turnover table
        self.update_turnover_table()

        # Update seasonal analysis table
        self.update_seasonal_table()

    def update_turnover_table(self):
        """Update the inventory turnover by category table."""
        # Get distinct categories from sales table
        categories = self.get_sales_categories()

        # Sort by average days to sell
        turnover_data = []
        for category in categories:
            if category:  # Skip empty categories
                avg_days = forecast_inventory_turnover(category)
                items_sold = self.get_items_sold_90d(category)
                if items_sold > 0 or avg_days > 0:  # Only show if there's data
                    turnover_data.append({
                        'category': category,
                        'avg_days': avg_days,
                        'items_sold': items_sold
                    })

        # Sort by avg_days ascending (fastest turnover first)
        turnover_data.sort(key=lambda x: (x['avg_days'], x['category']))

        # Populate table
        self.turnover_table.setRowCount(len(turnover_data))
        for row, data in enumerate(turnover_data):
            category_item = QTableWidgetItem(data['category'])
            days_item = QTableWidgetItem(f"{data['avg_days']:.1f}")
            items_item = QTableWidgetItem(str(data['items_sold']))

            self.turnover_table.setItem(row, 0, category_item)
            self.turnover_table.setItem(row, 1, days_item)
            self.turnover_table.setItem(row, 2, items_item)

    def update_seasonal_table(self):
        """Update the seasonal analysis table."""
        import calendar

        seasonal_data = []

        # Query all 12 months
        for month in range(1, 13):
            impact = forecast_seasonal_impact(month)

            if impact:  # Only add if there's data for this month
                seasonal_data.append({
                    'month': month,
                    'month_name': calendar.month_name[month],
                    'avg_sales': impact.get('avg_sales', 0),
                    'avg_revenue': impact.get('avg_revenue', 0.0),
                    'best_category': impact.get('best_category', 'N/A') or 'N/A'
                })

        # Populate table
        self.seasonal_table.setRowCount(len(seasonal_data))
        for row, data in enumerate(seasonal_data):
            month_item = QTableWidgetItem(data['month_name'])
            sales_item = QTableWidgetItem(str(data['avg_sales']))
            revenue_item = QTableWidgetItem(f"${data['avg_revenue']:.2f}")
            category_item = QTableWidgetItem(data['best_category'])

            self.seasonal_table.setItem(row, 0, month_item)
            self.seasonal_table.setItem(row, 1, sales_item)
            self.seasonal_table.setItem(row, 2, revenue_item)
            self.seasonal_table.setItem(row, 3, category_item)

    def get_sales_categories(self):
        """Get distinct categories from sales table.

        Returns:
            list: Sorted list of category names (strings)
        """
        conn = db.get_connection()
        c = conn.cursor()
        current_year = datetime.now().year

        c.execute('''
            SELECT DISTINCT category
            FROM sales
            WHERE category IS NOT NULL AND category != '' AND year = ?
            ORDER BY category
        ''', (current_year,))

        rows = c.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def get_items_sold_90d(self, category):
        """Get count of items sold in the last 90 days for a category.

        Args:
            category (str): Product category name

        Returns:
            int: Number of items sold in last 90 days
        """
        from datetime import timedelta

        conn = db.get_connection()
        c = conn.cursor()
        current_year = datetime.now().year

        # Calculate date range for last 90 days
        today = datetime.now().date()
        start_date = (today - timedelta(days=90)).isoformat()
        end_date = today.isoformat()

        c.execute('''
            SELECT COUNT(id) as item_count
            FROM sales
            WHERE sold_date BETWEEN ? AND ? AND category = ? AND year = ?
        ''', (start_date, end_date, category, current_year))

        result = c.fetchone()
        conn.close()

        return result[0] if result else 0
