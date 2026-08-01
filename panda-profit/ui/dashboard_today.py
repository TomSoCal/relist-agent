"""Today's $$$ Tracker Widget for real-time sales monitoring."""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import database as db
from analytics.calculations import calculate_profit


class TodayTrackerWidget(QFrame):
    """Real-time today's sales tracker widget showing sales count, revenue, and profit."""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("border-radius: 5px; padding: 10px; border: 1px solid #333333;")
        self.setContentsMargins(10, 10, 10, 10)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Title and clock
        title_layout = QHBoxLayout()

        self.title_label = QLabel("TODAY'S $$$ TRACKER")
        title_font = QFont("Arial", 16, QFont.Bold)
        self.title_label.setFont(title_font)
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        self.clock_label = QLabel("00:00:00 AM")
        clock_font = QFont("Arial", 12, QFont.Bold)
        self.clock_label.setFont(clock_font)
        title_layout.addWidget(self.clock_label)

        self.layout.addLayout(title_layout)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        # Sales count
        self.sales_label = self._create_stat_label("Sales", "0")
        stats_layout.addWidget(self.sales_label)

        # Revenue
        self.revenue_label = self._create_stat_label("Revenue", "$0.00")
        stats_layout.addWidget(self.revenue_label)

        # Profit (will be color-coded)
        self.profit_label = self._create_stat_label("Profit", "$0.00")
        stats_layout.addWidget(self.profit_label)

        stats_layout.addStretch()

        self.layout.addLayout(stats_layout)
        self.setLayout(self.layout)

        # Timers
        # 30-second data refresh timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(30000)  # 30 seconds

        # 1-second clock update timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)  # 1 second

        # Initial data load
        self.refresh_data()
        self.update_clock()

    def _create_stat_label(self, title, value):
        """Create a stat label widget with title and value."""
        container = QFrame()
        container.setStyleSheet("border-radius: 3px; padding: 8px; border: 1px solid #333333;")

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(5)

        title_label = QLabel(title)
        title_font = QFont("Arial", 10)
        title_label.setFont(title_font)

        value_label = QLabel(value)
        value_font = QFont("Arial", 14, QFont.Bold)
        value_label.setFont(value_font)

        container_layout.addWidget(title_label)
        container_layout.addWidget(value_label)
        container.setLayout(container_layout)

        # Store references for updates
        container.title_label = title_label
        container.value_label = value_label

        return container

    def update_clock(self):
        """Update the clock display."""
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")  # HH:MM:SS AP format
        self.clock_label.setText(time_str)

    def refresh_data(self):
        """Query and update today's sales data."""
        today = datetime.now()
        today_str = today.strftime("%m/%d/%Y")
        current_year = today.year

        # Query database
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        c.execute('''
            SELECT * FROM sales
            WHERE sold_date = ? AND year = ?
            ORDER BY sold_date DESC
        ''', (today_str, current_year))

        sales = c.fetchall()
        conn.close()

        # Calculate metrics
        sales_count = len(sales)
        total_revenue = 0
        total_profit = 0

        for sale in sales:
            revenue = (sale.get('sale_price', 0) or 0) + (sale.get('shipping_collected', 0) or 0)
            total_revenue += revenue
            profit = calculate_profit(sale)
            total_profit += profit

        # Update labels
        self.sales_label.value_label.setText(str(sales_count))
        self.revenue_label.value_label.setText(f"${total_revenue:,.2f}")

        # Update profit with color coding
        if total_profit >= 0:
            self.profit_label.value_label.setText(f"${total_profit:,.2f}")
            self.profit_label.value_label.setStyleSheet("color: #90EE90;")  # Light green
        else:
            self.profit_label.value_label.setText(f"${total_profit:,.2f}")
            self.profit_label.value_label.setStyleSheet("color: #FF6B6B;")  # Light red

    def closeEvent(self, event):
        """Clean up timers on widget close."""
        self.data_timer.stop()
        self.clock_timer.stop()
        super().closeEvent(event)
