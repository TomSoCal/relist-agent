from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt

class HistoryTab(QWidget):
    """Container for Sales History, Inventory History, and Expense History views."""

    def __init__(self):
        super().__init__()
        self.current_view = None
        self.sales_view = None
        self.inventory_view = None
        self.expense_view = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI with button bar and stacked widget."""
        layout = QVBoxLayout()

        # Button bar
        button_layout = QHBoxLayout()

        sales_btn = QPushButton("Sales History")
        sales_btn.clicked.connect(self.on_sales_clicked)
        button_layout.addWidget(sales_btn)

        inventory_btn = QPushButton("Inventory History")
        inventory_btn.clicked.connect(self.on_inventory_clicked)
        button_layout.addWidget(inventory_btn)

        expense_btn = QPushButton("Expense History")
        expense_btn.clicked.connect(self.on_expense_clicked)
        button_layout.addWidget(expense_btn)

        layout.addLayout(button_layout)

        # Stacked widget for views
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        self.setLayout(layout)

    def on_sales_clicked(self):
        """Show Sales History view."""
        if self.sales_view is None:
            from ui.history.sales_history_view import SalesHistoryView
            self.sales_view = SalesHistoryView()
            self.stacked.addWidget(self.sales_view)
        self.stacked.setCurrentWidget(self.sales_view)

    def on_inventory_clicked(self):
        """Show Inventory History view."""
        if self.inventory_view is None:
            from ui.history.inventory_history_view import InventoryHistoryView
            self.inventory_view = InventoryHistoryView()
            self.stacked.addWidget(self.inventory_view)
        self.stacked.setCurrentWidget(self.inventory_view)

    def on_expense_clicked(self):
        """Show Expense History view."""
        if self.expense_view is None:
            from ui.history.expense_history_view import ExpenseHistoryView
            self.expense_view = ExpenseHistoryView()
            self.stacked.addWidget(self.expense_view)
        self.stacked.setCurrentWidget(self.expense_view)
