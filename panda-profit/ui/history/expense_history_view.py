from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import database as db

class ExpenseHistoryView(QWidget):
    """View for displaying archived expenses from prior years."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_history()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)

        # Search
        year_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, date, category, amount, invoice, description, notes...")
        self.search_input.textChanged.connect(self.on_search)
        year_layout.addWidget(self.search_input)
        year_layout.addStretch()
        layout.addLayout(year_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Select', 'Date', 'Category', 'Amount', 'Invoice #', 'Description', 'Notes', 'Receipt', ''
        ])
        self.table.setColumnHidden(8, True)  # Hide expense_id
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_expense)
        button_layout.addWidget(view_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_history(self):
        """Load archived expenses."""
        # Get years with archived expenses (prior years only)
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('SELECT DISTINCT year FROM expenses WHERE archived=1 ORDER BY year DESC')
        years = [row[0] for row in c.fetchall() if row[0] < self.current_year]
        conn.close()

        current_text = self.year_selector.currentText()
        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        for y in years:
            self.year_selector.addItem(str(y))
        if current_text:
            self.year_selector.setCurrentText(current_text)
        elif years:
            self.year_selector.setCurrentIndex(0)
        self.year_selector.blockSignals(False)

        # Load expenses
        self.display_expenses()

    def display_expenses(self):
        """Display archived expenses based on year and search."""
        if self.year_selector.count() == 0:
            self.table.setRowCount(0)
            return

        year = int(self.year_selector.currentText())
        search_query = self.search_input.text().strip() or None

        expenses = db.get_archived_expenses(year=year, search_query=search_query)

        self.table.setRowCount(0)
        for expense in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox (disabled)
            checkbox = QCheckBox()
            checkbox.setEnabled(False)
            self.table.setCellWidget(row, 0, checkbox)

            # Columns: Date, Category, Amount, Invoice, Description, Notes, Receipt
            self.table.setItem(row, 1, QTableWidgetItem(expense['expense_date']))
            self.table.setItem(row, 2, QTableWidgetItem(expense['category_name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"${expense['amount']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(expense['invoice_number'] or ''))
            self.table.setItem(row, 5, QTableWidgetItem(expense['description']))
            self.table.setItem(row, 6, QTableWidgetItem(expense['notes']))
            receipt_text = 'Yes' if expense['receipt_path'] else '—'
            self.table.setItem(row, 7, QTableWidgetItem(receipt_text))

            # Store expense_id
            id_item = QTableWidgetItem(str(expense['id']))
            self.table.setItem(row, 8, id_item)

    def on_year_changed(self):
        """Handle year change."""
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.display_expenses()

    def on_search(self):
        """Handle search input change."""
        self.display_expenses()

    def view_expense(self):
        """View selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select an expense to view.")
            return

        row = selected_rows[0].row()
        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)

        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return

        from ui.expense_dialogs import ViewExpenseDialog
        ViewExpenseDialog(expense, self).exec_()
