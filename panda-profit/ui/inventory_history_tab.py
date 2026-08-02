from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QDialog, QMessageBox,
    QCheckBox, QFormLayout
)
from PyQt5.QtCore import Qt
from datetime import datetime
from database import (
    get_archived_inventory, copy_archived_to_active, get_inventory_by_id,
    db, get_all_inventory
)


class RestockModal(QDialog):
    """Modal dialog for restocking archived inventory item"""

    def __init__(self, archived_item, parent=None):
        super().__init__(parent)
        self.archived_item = archived_item
        self.new_item_id = None

        self.setWindowTitle("Restock Item")
        self.setGeometry(100, 100, 500, 400)

        layout = QFormLayout()

        # Read-only fields showing archived item details
        layout.addRow("Original SKU:", QLineEdit(archived_item['sku']))
        layout.addRow("Item Title:", QLineEdit(archived_item['item_title']))
        layout.addRow("Category:", QLineEdit(archived_item['category']))
        layout.addRow("Brand:", QLineEdit(archived_item.get('brand', '')))
        layout.addRow("Original Cost:", QLineEdit(f"${archived_item['cost']:.2f}"))

        if archived_item['last_sold_date']:
            layout.addRow("Last Sold:", QLineEdit(archived_item['last_sold_date']))
        if archived_item['units_sold_total']:
            layout.addRow("Units Sold:", QLineEdit(str(archived_item['units_sold_total'])))
        if archived_item['revenue_total']:
            layout.addRow("Total Revenue:", QLineEdit(f"${archived_item['revenue_total']:.2f}"))

        # Make read-only fields actually read-only
        for i in range(layout.rowCount()):
            widget = layout.itemAt(i, QFormLayout.FieldRole).widget()
            if isinstance(widget, QLineEdit):
                widget.setReadOnly(True)

        # New SKU input
        self.new_sku_input = QLineEdit()
        self.new_sku_input.setPlaceholderText("Enter new SKU for restocked item")
        layout.addRow("New SKU:", self.new_sku_input)

        # Copy details checkbox
        self.copy_details_checkbox = QCheckBox("Copy all details (title, category, brand, cost)")
        self.copy_details_checkbox.setChecked(True)
        layout.addRow(self.copy_details_checkbox)

        # Buttons
        button_layout = QHBoxLayout()

        add_button = QPushButton("Add to Inventory")
        add_button.clicked.connect(self.add_to_inventory)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)

        layout.addRow(button_layout)

        self.setLayout(layout)

    def add_to_inventory(self):
        """Validate and create new inventory item"""
        new_sku = self.new_sku_input.text().strip()

        if not new_sku:
            QMessageBox.warning(self, "Validation Error", "New SKU is required")
            return

        copy_details = self.copy_details_checkbox.isChecked()

        try:
            # Check for duplicate SKU in active inventory
            existing = db.execute(
                "SELECT id FROM inventory WHERE sku = ? AND archived = 0",
                (new_sku,)
            ).fetchone()

            if existing:
                QMessageBox.warning(self, "SKU Conflict", f"SKU '{new_sku}' already exists in active inventory")
                return

            # Copy to active
            self.new_item_id = copy_archived_to_active(
                self.archived_item['id'],
                new_sku,
                copy_details=copy_details
            )

            QMessageBox.information(
                self,
                "Success",
                f"Item restocked as SKU '{new_sku}' and added to active inventory"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restock item: {str(e)}")


class InventoryHistoryTab(QWidget):
    """Tab for searching and restocking historical archived inventory"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_years()

    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()

        # Search bar layout
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(self.perform_search)
        search_layout.addWidget(self.year_combo)

        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by SKU, title, category, or brand...")
        self.search_input.textChanged.connect(self.perform_search)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        main_layout.addLayout(search_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            'SKU', 'Item Title', 'Category', 'Brand', 'Cost',
            'Last Sold', 'Units Sold', 'Revenue'
        ])
        self.results_table.setColumnWidth(1, 200)
        self.results_table.setColumnWidth(2, 100)
        self.results_table.doubleClicked.connect(self.on_item_double_clicked)

        main_layout.addWidget(self.results_table)

        # Restock button
        button_layout = QHBoxLayout()
        self.restock_button = QPushButton("Restock Selected Item")
        self.restock_button.clicked.connect(self.restock_selected)
        button_layout.addWidget(self.restock_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_years(self):
        """Populate year dropdown with available years from database"""
        query = """
        SELECT DISTINCT strftime('%Y', created_at) as year
        FROM inventory
        WHERE archived = 1
        ORDER BY year DESC
        """
        years = db.execute(query).fetchall()

        for year_row in years:
            year = year_row['year'] if isinstance(year_row, dict) else year_row[0]
            if year:  # Skip NULL
                self.year_combo.addItem(year, year)

        # Add "All Years" option
        self.year_combo.insertItem(0, "All Years", None)
        self.year_combo.setCurrentIndex(0)

    def perform_search(self):
        """Search archived inventory and populate results table"""
        year = self.year_combo.currentData()
        search_query = self.search_input.text().strip() if self.search_input.text() else None

        # Query archived inventory
        results = get_archived_inventory(year=int(year) if year else None, search_query=search_query)

        # Populate table
        self.results_table.setRowCount(len(results))

        for row_idx, item in enumerate(results):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(item['sku']))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(item['item_title']))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(item['category'] or ''))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(item['brand'] or ''))
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(f"${item['cost']:.2f}"))
            self.results_table.setItem(row_idx, 5, QTableWidgetItem(item['last_sold_date'] or 'N/A'))
            self.results_table.setItem(row_idx, 6, QTableWidgetItem(str(item['units_sold_total'] or 0)))
            self.results_table.setItem(row_idx, 7, QTableWidgetItem(f"${item['revenue_total']:.2f}" if item['revenue_total'] else '$0.00'))

        # Store results for later reference
        self.last_results = results

    def on_item_double_clicked(self):
        """Handle double-click on table row"""
        self.restock_selected()

    def restock_selected(self):
        """Open restock modal for selected item"""
        current_row = self.results_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select an item to restock")
            return

        if not hasattr(self, 'last_results') or current_row >= len(self.last_results):
            QMessageBox.warning(self, "Error", "Could not find selected item")
            return

        selected_item = self.last_results[current_row]

        # Open restock modal
        modal = RestockModal(selected_item, self)
        result = modal.exec_()

        if result == QDialog.Accepted and modal.new_item_id:
            # Refresh search to show updated results
            self.perform_search()
            QMessageBox.information(self, "Success", "Item successfully restocked!")
