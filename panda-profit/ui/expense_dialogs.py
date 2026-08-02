from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QDateEdit, QDoubleSpinBox, QComboBox, QPushButton, QFileDialog,
    QMessageBox, QSpinBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import os
import database as db

class AddExpenseDialog(QDialog):
    """Dialog for adding a new expense."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Expense")
        self.setGeometry(150, 150, 500, 600)
        self.receipt_file = None
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()

        # Date
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.now().date())
        layout.addWidget(self.date_input)

        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        categories = db.get_expense_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])
        self.category_combo.addItem("Add New Category...", -1)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_combo)

        # Amount
        layout.addWidget(QLabel("Amount ($):"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 99999.99)
        self.amount_spin.setDecimals(2)
        layout.addWidget(self.amount_spin)

        # Invoice number
        layout.addWidget(QLabel("Invoice Number (optional):"))
        self.invoice_input = QLineEdit()
        self.invoice_input.setMaxLength(50)
        self.invoice_input.setPlaceholderText("e.g., INV-001")
        layout.addWidget(self.invoice_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit()
        self.description_input.setMaxLength(255)
        layout.addWidget(self.description_input)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)

        # Receipt
        layout.addWidget(QLabel("Receipt (optional):"))
        receipt_layout = QHBoxLayout()
        self.receipt_label = QLabel("No file selected")
        receipt_layout.addWidget(self.receipt_label)
        receipt_btn = QPushButton("Browse...")
        receipt_btn.clicked.connect(self.browse_receipt)
        receipt_layout.addWidget(receipt_btn)
        layout.addLayout(receipt_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_expense)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_category_changed(self):
        """Handle category selection change."""
        if self.category_combo.currentData() == -1:
            self.add_category()

    def add_category(self):
        """Open add category dialog."""
        dialog = AddCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            cat_id = dialog.category_id
            self.category_combo.blockSignals(True)
            current_index = self.category_combo.count() - 1
            self.category_combo.removeItem(current_index)
            categories = db.get_expense_categories()
            for cat in categories:
                self.category_combo.addItem(cat['name'], cat['id'])
            self.category_combo.addItem("Add New Category...", -1)
            self.category_combo.setCurrentData(cat_id)
            self.category_combo.blockSignals(False)

    def browse_receipt(self):
        """Browse for receipt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt", "",
            "Images (*.png *.jpg *.gif);;PDFs (*.pdf);;All Files (*.*)"
        )
        if file_path:
            self.receipt_file = file_path
            self.receipt_label.setText(os.path.basename(file_path))

    def save_expense(self):
        """Validate and save expense."""
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0.")
            return

        if not self.description_input.text().strip():
            QMessageBox.warning(self, "Error", "Description is required.")
            return

        try:
            category_id = self.category_combo.currentData()
            current_year = datetime.now().year

            db.add_expense(
                year=current_year,
                expense_date=self.date_input.date().toString("yyyy-MM-dd"),
                category_id=category_id,
                amount=self.amount_spin.value(),
                invoice_number=self.invoice_input.text().strip(),
                description=self.description_input.text().strip(),
                notes=self.notes_input.toPlainText().strip(),
                receipt_path=self.receipt_file or ''
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save expense: {str(e)}")

class EditExpenseDialog(QDialog):
    """Dialog for editing an existing expense."""

    def __init__(self, expense, parent=None):
        super().__init__(parent)
        self.expense = expense
        self.receipt_file = expense.get('receipt_path', '')
        self.setWindowTitle("Edit Expense")
        self.setGeometry(150, 150, 500, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()

        # Date
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.strptime(self.expense['expense_date'], '%Y-%m-%d').date())
        layout.addWidget(self.date_input)

        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        categories = db.get_expense_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])
        self.category_combo.setCurrentData(self.expense['category_id'])
        layout.addWidget(self.category_combo)

        # Amount
        layout.addWidget(QLabel("Amount ($):"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 99999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(self.expense['amount'])
        layout.addWidget(self.amount_spin)

        # Invoice number
        layout.addWidget(QLabel("Invoice Number (optional):"))
        self.invoice_input = QLineEdit()
        self.invoice_input.setMaxLength(50)
        self.invoice_input.setText(self.expense.get('invoice_number', ''))
        layout.addWidget(self.invoice_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit()
        self.description_input.setMaxLength(255)
        self.description_input.setText(self.expense['description'])
        layout.addWidget(self.description_input)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlainText(self.expense.get('notes', ''))
        layout.addWidget(self.notes_input)

        # Receipt
        layout.addWidget(QLabel("Receipt (optional):"))
        receipt_layout = QHBoxLayout()
        self.receipt_label = QLabel(
            os.path.basename(self.receipt_file) if self.receipt_file else "No file selected"
        )
        receipt_layout.addWidget(self.receipt_label)
        receipt_btn = QPushButton("Replace...")
        receipt_btn.clicked.connect(self.browse_receipt)
        receipt_layout.addWidget(receipt_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_receipt)
        receipt_layout.addWidget(clear_btn)
        layout.addLayout(receipt_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_expense)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_receipt(self):
        """Browse for receipt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt", "",
            "Images (*.png *.jpg *.gif);;PDFs (*.pdf);;All Files (*.*)"
        )
        if file_path:
            self.receipt_file = file_path
            self.receipt_label.setText(os.path.basename(file_path))

    def clear_receipt(self):
        """Clear receipt."""
        self.receipt_file = ''
        self.receipt_label.setText("No file selected")

    def save_expense(self):
        """Validate and update expense."""
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0.")
            return

        try:
            db.update_expense(
                expense_id=self.expense['id'],
                expense_date=self.date_input.date().toString("yyyy-MM-dd"),
                category_id=self.category_combo.currentData(),
                amount=self.amount_spin.value(),
                invoice_number=self.invoice_input.text().strip(),
                description=self.description_input.text().strip(),
                notes=self.notes_input.toPlainText().strip(),
                receipt_path=self.receipt_file
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update expense: {str(e)}")

class ViewExpenseDialog(QDialog):
    """Read-only dialog for viewing expense details."""

    def __init__(self, expense, parent=None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("View Expense")
        self.setGeometry(150, 150, 500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()

        # Date
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(QLabel(self.expense['expense_date']))

        # Category
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(QLabel(self.expense['category_name']))

        # Amount
        layout.addWidget(QLabel("Amount:"))
        layout.addWidget(QLabel(f"${self.expense['amount']:.2f}"))

        # Invoice
        layout.addWidget(QLabel("Invoice Number:"))
        layout.addWidget(QLabel(self.expense.get('invoice_number', '—')))

        # Description
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(QLabel(self.expense['description']))

        # Notes
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(QLabel(self.expense.get('notes', '—')))

        # Receipt
        layout.addWidget(QLabel("Receipt:"))
        if self.expense.get('receipt_path'):
            receipt_layout = QHBoxLayout()
            receipt_layout.addWidget(QLabel(f"File: {self.expense['receipt_path']}"))
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(self.open_receipt)
            receipt_layout.addWidget(open_btn)
            receipt_layout.addStretch()
            layout.addLayout(receipt_layout)
        else:
            layout.addWidget(QLabel("No receipt attached"))

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def open_receipt(self):
        """Open receipt file."""
        receipt_path = self.expense.get('receipt_path', '')
        if receipt_path and os.path.exists(receipt_path):
            os.startfile(receipt_path)
        else:
            QMessageBox.warning(self, "Error", "Receipt file not found.")

class AddCategoryDialog(QDialog):
    """Dialog for adding a new expense category."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.category_id = None
        self.setWindowTitle("Add Category")
        self.setGeometry(200, 200, 300, 150)
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Category Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Tools, Inventory")
        layout.addWidget(self.name_input)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("Add")
        save_btn.clicked.connect(self.add_category)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_category(self):
        """Add new category."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category name is required.")
            return

        try:
            self.category_id = db.add_expense_category(name)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
