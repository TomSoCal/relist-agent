from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import database as db
from datetime import datetime, timedelta
from ui.dashboard_today import TodayTrackerWidget

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_dashboard()

    def init_ui(self):
        layout = QVBoxLayout()

        # Time period selector
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["All Time", "This Month", "This Year", "Last 30 Days", "Last 90 Days"])
        self.period_combo.currentIndexChanged.connect(self.refresh_dashboard)
        filter_layout.addWidget(self.period_combo)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Today's $$$ Tracker Widget
        self.today_tracker = TodayTrackerWidget()
        layout.addWidget(self.today_tracker)

        # Revenue Summary
        revenue_group = QGroupBox("Revenue & Profit Summary")
        revenue_layout = QVBoxLayout()

        self.total_sales_label = self._create_stat_label("Total Sales", "$0.00")
        self.total_profit_label = self._create_stat_label("Total Profit", "$0.00")
        self.profit_margin_label = self._create_stat_label("Profit Margin", "0%")
        self.avg_profit_label = self._create_stat_label("Avg Profit/Item", "$0.00")

        stat_layout = QHBoxLayout()
        stat_layout.addWidget(self.total_sales_label)
        stat_layout.addWidget(self.total_profit_label)
        stat_layout.addWidget(self.profit_margin_label)
        stat_layout.addWidget(self.avg_profit_label)

        revenue_layout.addLayout(stat_layout)
        revenue_group.setLayout(revenue_layout)

        # Activity Summary
        activity_group = QGroupBox("Activity Summary")
        activity_layout = QVBoxLayout()

        self.items_sold_label = self._create_stat_label("Items Sold", "0")
        self.avg_days_to_sell_label = self._create_stat_label("Avg Days to Sell", "0")
        self.total_inventory_label = self._create_stat_label("Current Inventory", "0")
        self.total_inventory_cost_label = self._create_stat_label("Inventory Value", "$0.00")

        activity_stat_layout = QHBoxLayout()
        activity_stat_layout.addWidget(self.items_sold_label)
        activity_stat_layout.addWidget(self.avg_days_to_sell_label)
        activity_stat_layout.addWidget(self.total_inventory_label)
        activity_stat_layout.addWidget(self.total_inventory_cost_label)

        activity_layout.addLayout(activity_stat_layout)
        activity_group.setLayout(activity_layout)

        # Platform Summary
        platform_group = QGroupBox("Sales by Platform")
        platform_layout = QVBoxLayout()

        self.platform_labels = {}
        self.platform_container = QWidget()
        self.platform_container_layout = QVBoxLayout()
        self.platform_container.setLayout(self.platform_container_layout)

        platform_layout.addWidget(self.platform_container)
        platform_group.setLayout(platform_layout)

        # Category Summary
        category_group = QGroupBox("Top Categories")
        category_layout = QVBoxLayout()

        self.category_labels = {}
        self.category_container = QWidget()
        self.category_container_layout = QVBoxLayout()
        self.category_container.setLayout(self.category_container_layout)

        category_layout.addWidget(self.category_container)
        category_group.setLayout(category_layout)

        # Add all groups
        layout.addWidget(revenue_group)
        layout.addWidget(activity_group)
        layout.addWidget(platform_group)
        layout.addWidget(category_group)
        layout.addStretch()

        self.setLayout(layout)

    def _create_stat_label(self, title, value):
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #666;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet("color: #1F3864;")  # Trashed Panda blue

        container_layout.addWidget(title_label)
        container_layout.addWidget(value_label)
        container.setLayout(container_layout)
        container.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")

        # Store labels for updating
        container.title_label = title_label
        container.value_label = value_label

        return container

    def get_date_range(self):
        period = self.period_combo.currentText()
        today = datetime.now()

        if period == "All Time":
            return "1900-01-01", today.strftime("%Y-%m-%d")
        elif period == "This Month":
            month_start = today.replace(day=1).strftime("%Y-%m-%d")
            return month_start, today.strftime("%Y-%m-%d")
        elif period == "This Year":
            year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            return year_start, today.strftime("%Y-%m-%d")
        elif period == "Last 30 Days":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            return start, today.strftime("%Y-%m-%d")
        elif period == "Last 90 Days":
            start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
            return start, today.strftime("%Y-%m-%d")

    def refresh_dashboard(self):
        start_date, end_date = self.get_date_range()
        sales = db.get_sales_by_date_range(start_date, end_date)

        # Calculate metrics
        total_sales = sum(s.get('sale_price', 0) or 0 for s in sales)
        total_profit = sum(s.get('profit_loss', 0) or 0 for s in sales)
        total_items = sum(s.get('units', 0) for s in sales)
        total_shipping_collected = sum(s.get('shipping_collected', 0) or 0 for s in sales)

        profit_margin = (total_profit / (total_sales + total_shipping_collected) * 100) if (total_sales + total_shipping_collected) > 0 else 0
        avg_profit = total_profit / total_items if total_items > 0 else 0
        avg_days_to_sell = sum(s.get('days_to_sell', 0) or 0 for s in sales) / total_items if total_items > 0 else 0

        # Update summary labels
        self.total_sales_label.value_label.setText(f"${total_sales:,.2f}")
        self.total_profit_label.value_label.setText(f"${total_profit:,.2f}")
        self.profit_margin_label.value_label.setText(f"{profit_margin:.1f}%")
        self.avg_profit_label.value_label.setText(f"${avg_profit:.2f}")

        # Activity metrics
        inventory = db.get_all_inventory()
        inventory_cost = sum(i.get('cost', 0) or 0 for i in inventory)

        self.items_sold_label.value_label.setText(str(total_items))
        self.avg_days_to_sell_label.value_label.setText(f"{avg_days_to_sell:.0f} days")
        self.total_inventory_label.value_label.setText(str(len(inventory)))
        self.total_inventory_cost_label.value_label.setText(f"${inventory_cost:,.2f}")

        # Platform breakdown
        self._update_platform_summary(sales)

        # Category breakdown
        self._update_category_summary(sales)

    def _update_platform_summary(self, sales):
        # Clear existing
        for i in reversed(range(self.platform_container_layout.count())):
            self.platform_container_layout.itemAt(i).widget().setParent(None)
        self.platform_labels = {}

        # Group by platform
        platforms = {}
        for sale in sales:
            platform = sale.get('platform') or 'Unknown'
            if platform not in platforms:
                platforms[platform] = {'count': 0, 'profit': 0}
            platforms[platform]['count'] += sale.get('units', 0)
            platforms[platform]['profit'] += sale.get('profit_loss', 0) or 0

        for platform, data in sorted(platforms.items()):
            label_text = f"{platform}: {data['count']} items | Profit: ${data['profit']:,.2f}"
            label = QLabel(label_text)
            self.platform_container_layout.addWidget(label)

        if not platforms:
            self.platform_container_layout.addWidget(QLabel("No sales data"))

    def _update_category_summary(self, sales):
        # Clear existing
        for i in reversed(range(self.category_container_layout.count())):
            self.category_container_layout.itemAt(i).widget().setParent(None)
        self.category_labels = {}

        # Group by category
        categories = {}
        for sale in sales:
            category = sale.get('category') or 'Uncategorized'
            if category not in categories:
                categories[category] = {'count': 0, 'profit': 0}
            categories[category]['count'] += sale.get('units', 0)
            categories[category]['profit'] += sale.get('profit_loss', 0) or 0

        # Sort by profit (top first)
        for category, data in sorted(categories.items(), key=lambda x: x[1]['profit'], reverse=True)[:5]:
            label_text = f"{category}: {data['count']} items | Profit: ${data['profit']:,.2f}"
            label = QLabel(label_text)
            self.category_container_layout.addWidget(label)

        if not categories:
            self.category_container_layout.addWidget(QLabel("No sales data"))
