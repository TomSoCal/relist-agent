from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import database as db

class ExpensesTab(QWidget):
    """Tab for viewing and managing current-year expenses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = datetime.now().year
        self.init_ui()
        self.load_expenses()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        self.year_selector.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_selector)
        year_layout.addStretch()
        layout.addLayout(year_layout)

        # Summary stats
        stats_layout = QHBoxLayout()

        self.month_label = QLabel("Total (This Month): $0.00")
        self.month_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.month_label)

        self.total_label = QLabel("Total (This Year): $0.00")
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_label)

        self.count_label = QLabel("Count (This Month): 0")
        self.count_label.setFont(QFont("Arial", 10))
        stats_layout.addWidget(self.count_label)

        layout.addLayout(stats_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Select', 'Date', 'Category', 'Amount', 'Invoice #', 'Description', 'Notes', 'Receipt', ''
        ])
        self.table.setColumnHidden(8, True)  # Hide expense_id column
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Expense")
        add_btn.clicked.connect(self.add_expense)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_expense)
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self.view_expense)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("background-color: #c41e3a; color: white;")
        delete_btn.clicked.connect(self.delete_selected)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(view_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_expenses(self):
        """Load expenses for selected year."""
        year = int(self.year_selector.currentText()) if self.year_selector.count() > 0 else self.current_year
        expenses = db.get_expenses(year=year, archived=0)

        self.table.setRowCount(0)
        for expense in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            checkbox = QCheckBox()
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

        # Update year selector
        all_years = list(range(datetime.now().year - 5, datetime.now().year + 1))
        current_text = self.year_selector.currentText()
        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        for y in sorted(all_years, reverse=True):
            self.year_selector.addItem(str(y))
        self.year_selector.setCurrentText(current_text or str(self.current_year))
        self.year_selector.blockSignals(False)

        # Update summary stats
        month_total, year_total, month_count, year_count = db.get_expense_totals(year=year)
        self.month_label.setText(f"Total (This Month): ${month_total:.2f}")
        self.total_label.setText(f"Total (This Year): ${year_total:.2f}")
        self.count_label.setText(f"Count (This Month): {month_count}")

    def on_year_changed(self):
        """Handle year selector change."""
        self.load_expenses()

    def add_expense(self):
        """Open add expense dialog."""
        from ui.expense_dialogs import AddExpenseDialog
        dialog = AddExpenseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense added!")

    def edit_expense(self):
        """Edit selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        row = None

        if selected_rows:
            row = selected_rows[0].row()
        else:
            # Check checkboxes
            checked_rows = []
            for r in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(r, 0)
                if checkbox and checkbox.isChecked():
                    checked_rows.append(r)

            if len(checked_rows) == 1:
                row = checked_rows[0]

        if row is None:
            QMessageBox.warning(self, "Error", "Please select one expense to edit.")
            return

        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)

        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return

        from ui.expense_dialogs import EditExpenseDialog
        dialog = EditExpenseDialog(expense, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense updated!")

    def view_expense(self):
        """View selected expense."""
        selected_rows = self.table.selectionModel().selectedRows()
        row = None

        if selected_rows:
            row = selected_rows[0].row()
        else:
            # Check checkboxes
            checked_rows = []
            for r in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(r, 0)
                if checkbox and checkbox.isChecked():
                    checked_rows.append(r)

            if len(checked_rows) == 1:
                row = checked_rows[0]

        if row is None:
            QMessageBox.warning(self, "Error", "Please select an expense to view.")
            return
        expense_id = int(self.table.item(row, 8).text())
        expense = db.get_expense_by_id(expense_id)

        if not expense:
            QMessageBox.warning(self, "Error", "Expense not found.")
            return

        from ui.expense_dialogs import ViewExpenseDialog
        ViewExpenseDialog(expense, self).exec_()

    def delete_selected(self):
        """Delete selected expenses."""
        checked_rows = []
        for r in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(r, 0)
            if checkbox and checkbox.isChecked():
                checked_rows.append(r)

        if not checked_rows:
            QMessageBox.warning(self, "Error", "Please select expenses to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm",
            f"Delete {len(checked_rows)} expense(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            failed = []
            for r in sorted(checked_rows, reverse=True):
                expense_id = int(self.table.item(r, 8).text())
                try:
                    db.delete_expense(expense_id)
                except Exception as e:
                    failed.append(str(expense_id))

            if failed:
                QMessageBox.warning(
                    self, "Partial Deletion",
                    f"Could not delete {len(failed)} expense(s)."
                )

            self.load_expenses()
            QMessageBox.information(self, "Success", "Expense(s) deleted!")
