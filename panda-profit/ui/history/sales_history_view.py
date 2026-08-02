from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
import database as db

class SalesHistoryView(QWidget):
    """Display prior-year sales (archived data)."""

    def __init__(self):
        super().__init__()
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_years()
        self.load_sales()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentIndexChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)
        year_layout.addStretch()
        layout.addLayout(year_layout)

        # Summary stats
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("Month Total:"))
        self.month_total_label = QLabel("$0.00")
        stats_layout.addWidget(self.month_total_label)

        stats_layout.addWidget(QLabel("Year Total:"))
        self.year_total_label = QLabel("$0.00")
        stats_layout.addWidget(self.year_total_label)

        stats_layout.addWidget(QLabel("Count:"))
        self.count_label = QLabel("0")
        stats_layout.addWidget(self.count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Date', 'Item', 'Quantity', 'Price', 'Total', 'Buyer', 'Tier', ''
        ])
        self.table.setColumnHidden(7, True)  # Hide sale_id
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_sale)
        button_layout.addWidget(view_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_years(self):
        """Populate year selector with prior years (exclude current year)."""
        all_sales = db.get_sales()
        years_set = set()
        for sale in all_sales:
            if sale['year'] < self.current_year:
                years_set.add(sale['year'])

        if years_set:
            years = sorted(years_set, reverse=True)
            for year in years:
                self.year_selector.addItem(str(year))

    def load_sales(self):
        """Load sales for selected year."""
        if self.year_selector.count() == 0:
            self.table.setRowCount(0)
            return

        year = int(self.year_selector.currentText())
        sales = db.get_sales(year=year)

        self.table.setRowCount(0)
        total = 0
        for sale in sales:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(sale['sold_date']))
            self.table.setItem(row, 1, QTableWidgetItem(sale['item_title']))
            self.table.setItem(row, 2, QTableWidgetItem(str(sale['units'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"${sale['sale_price']:.2f}"))
            sale_total = sale['units'] * sale['sale_price']
            self.table.setItem(row, 4, QTableWidgetItem(f"${sale_total:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(sale.get('buyer_name', '')))
            self.table.setItem(row, 6, QTableWidgetItem(str(sale.get('tier', ''))))

            # Store sale_id
            id_item = QTableWidgetItem(str(sale['id']))
            self.table.setItem(row, 7, id_item)

            total += sale_total

        self.year_total_label.setText(f"${total:.2f}")
        self.count_label.setText(str(len(sales)))

    def on_year_changed(self):
        """Handle year selector change."""
        self.load_sales()

    def view_sale(self):
        """View selected sale."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select a sale to view.")
            return

        row = selected_rows[0].row()
        sale_id = int(self.table.item(row, 7).text())

        sale = db.get_sale_by_id(sale_id)
        if not sale:
            QMessageBox.warning(self, "Error", "Sale not found.")
            return

        from ui.sales_tab import ViewSaleDialog
        dialog = ViewSaleDialog(sale, self)
        dialog.exec_()
