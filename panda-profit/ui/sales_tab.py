from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTableWidget, QTableWidgetItem, QDialog, QLabel,
                            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                            QTextEdit, QMessageBox, QHeaderView, QFileDialog, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
import database as db
import csv
from constants import CATEGORIES, PLATFORMS

class SalesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.bulk_mode = False
        self.inventory_tab = None
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout()

        # Button bar
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Sale")
        add_btn.clicked.connect(self.add_sale_dialog)

        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_sale_details)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_sale)

        return_btn = QPushButton("Return to Inventory")
        return_btn.clicked.connect(self.return_to_inventory)

        self.bulk_btn = QPushButton("Bulk Actions")
        self.bulk_btn.clicked.connect(self.toggle_bulk_mode)
        self.bulk_btn.setStyleSheet("background-color: lightblue")

        self.bulk_return_btn = QPushButton("Return Selected")
        self.bulk_return_btn.clicked.connect(self.bulk_return_items)
        self.bulk_return_btn.setVisible(False)

        self.bulk_cancel_btn = QPushButton("Cancel Bulk")
        self.bulk_cancel_btn.clicked.connect(self.toggle_bulk_mode)
        self.bulk_cancel_btn.setVisible(False)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_table)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(view_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(return_btn)
        button_layout.addWidget(self.bulk_btn)
        button_layout.addWidget(self.bulk_return_btn)
        button_layout.addWidget(self.bulk_cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(export_btn)
        button_layout.addWidget(refresh_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels([
            "Checkbox", "ID", "Sold Date", "Platform", "Item Title", "Sale Price",
            "Cost", "Shipping", "Transaction Fee", "Promoted Fee", "Other Fee",
            "Total Fees", "Profit/Loss Per Unit", "Total Profit/Loss", "Category", "Days to Sell", "Units"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Summary bar
        summary_layout = QHBoxLayout()
        self.summary_label = QLabel("Total Sales: $0 | Total Profit: $0 | Total Items: 0")
        summary_layout.addWidget(self.summary_label)

        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        layout.addLayout(summary_layout)
        self.setLayout(layout)

    def refresh_table(self):
        sales = db.get_all_sales()
        self.table.setRowCount(len(sales))

        total_sales = 0
        total_profit = 0
        total_units = 0

        for row, sale in enumerate(sales):
            # Checkbox column
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, state))
            self.table.setCellWidget(row, 0, checkbox)

            # Data columns (shifted right by 1 for checkbox)
            self.table.setItem(row, 1, QTableWidgetItem(str(sale['id'])))
            self.table.setItem(row, 2, QTableWidgetItem(sale['sold_date']))
            self.table.setItem(row, 3, QTableWidgetItem(sale['platform'] or ''))
            self.table.setItem(row, 4, QTableWidgetItem(sale['item_title']))
            self.table.setItem(row, 5, QTableWidgetItem(f"${sale['sale_price']:.2f}" if sale['sale_price'] else '$0'))
            self.table.setItem(row, 6, QTableWidgetItem(f"${sale['cost_of_goods']:.2f}" if sale['cost_of_goods'] else '$0'))
            shipping = (sale['shipping_collected'] or 0) - (sale['shipping_cost'] or 0)
            self.table.setItem(row, 7, QTableWidgetItem(f"${shipping:.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"${sale['transaction_fee']:.2f}" if sale['transaction_fee'] else '$0'))
            self.table.setItem(row, 9, QTableWidgetItem(f"${sale['promoted_fee']:.2f}" if sale['promoted_fee'] else '$0'))
            self.table.setItem(row, 10, QTableWidgetItem(f"${sale.get('other_fee', 0):.2f}"))
            self.table.setItem(row, 11, QTableWidgetItem(f"${sale['total_fees']:.2f}" if sale['total_fees'] else '$0'))

            # Profit/Loss per unit
            units = sale['units'] or 1
            profit_per_unit = (sale['profit_loss'] or 0) / units
            self.table.setItem(row, 12, QTableWidgetItem(f"${profit_per_unit:.2f}"))

            # Total Profit/Loss
            self.table.setItem(row, 13, QTableWidgetItem(f"${sale['profit_loss']:.2f}" if sale['profit_loss'] else '$0'))
            self.table.setItem(row, 14, QTableWidgetItem(sale['category'] or ''))
            self.table.setItem(row, 15, QTableWidgetItem(str(sale['days_to_sell'] or 0)))
            self.table.setItem(row, 16, QTableWidgetItem(str(sale['units'])))

            total_sales += sale['sale_price'] or 0
            total_profit += sale['profit_loss'] or 0
            total_units += sale['units']

        self.summary_label.setText(
            f"Total Sales: ${total_sales:,.2f} | "
            f"Total Profit: ${total_profit:,.2f} | "
            f"Total Items: {total_units}"
        )

    def add_sale_dialog(self):
        dialog = AddSaleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            sale_data = dialog.get_sale_data()
            db.add_sale(**sale_data)
            self.refresh_table()
            QMessageBox.information(self, "Success", "Sale added successfully!")

    def view_sale_details(self):
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break

        if checked_row is None:
            QMessageBox.warning(self, "Error", "Please check the box next to the sale you want to view.")
            return

        sale_id = int(self.table.item(checked_row, 1).text())
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        c.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        sale = c.fetchone()
        conn.close()

        if sale:
            details = "\n".join([f"{k}: {v}" for k, v in sale.items()])
            QMessageBox.information(self, "Sale Details", details)

    def delete_sale(self):
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break

        if checked_row is None:
            QMessageBox.warning(self, "Error", "Please check the box next to the sale you want to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this sale?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            sale_id = int(self.table.item(checked_row, 1).text())
            db.delete_sale(sale_id)
            self.refresh_table()
            QMessageBox.information(self, "Success", "Sale deleted successfully!")

    def return_to_inventory(self):
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break

        if checked_row is None:
            QMessageBox.warning(self, "Error", "Please check the box next to the sale you want to return.")
            return

        sale_id = int(self.table.item(checked_row, 1).text())
        conn = db.get_connection()
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        c.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        sale = c.fetchone()
        conn.close()

        if not sale:
            QMessageBox.warning(self, "Error", "Sale not found.")
            return

        reply = QMessageBox.question(self, "Return to Inventory",
                                     f"Return {sale['units']} unit(s) of '{sale['item_title']}' to inventory?\n\n"
                                     "This will reverse the sale and add the item back to active inventory.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Merge item back to inventory (will add to existing if same item exists)
            db.merge_inventory(
                sale['listed_date'] or datetime.now().strftime("%m/%d/%Y"),
                sale['item_title'],
                sale['units'],
                sale['sku'],
                sale['bin'],
                sale['store'],
                sale['category'],
                sale['cost_of_goods'] / sale['units'] if sale['units'] > 0 else 0,
                f"Returned from sale on {sale['sold_date']} (Reason: Mistake or Customer Return)"
            )

            # Delete the sale
            db.delete_sale(sale_id)
            self.refresh_table()

            # Auto-refresh Inventory tab if available
            print(f"DEBUG: inventory_tab is {self.inventory_tab}")
            if self.inventory_tab:
                print("DEBUG: Calling refresh_table on inventory_tab")
                # Clear search filters to show the returned item
                self.inventory_tab.search_title.clear()
                self.inventory_tab.search_sku.clear()
                self.inventory_tab.refresh_table()
                print("DEBUG: Refresh complete")
                QMessageBox.information(self, "Success",
                                       f"Sale reversed! {sale['units']} unit(s) returned to inventory.\n\n"
                                       "Inventory tab has been refreshed. Search filters cleared.")
            else:
                QMessageBox.information(self, "Success",
                                       f"Sale reversed! {sale['units']} unit(s) returned to inventory.\n\n"
                                       "Note: Inventory tab reference not found. Please click on Inventory tab to refresh.")

    def on_checkbox_changed(self, row, state):
        # Highlight row when checked
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col) if col > 0 else None
            if item:
                if state == Qt.Checked:
                    item.setBackground(QColor("yellow"))
                else:
                    item.setBackground(QColor("white"))

        # In single-select mode, uncheck other rows
        if not self.bulk_mode:
            for r in range(self.table.rowCount()):
                if r != row:
                    checkbox = self.table.cellWidget(r, 0)
                    if checkbox and checkbox.isChecked():
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
                        # Reset highlight
                        for col in range(self.table.columnCount()):
                            item = self.table.item(r, col) if col > 0 else None
                            if item:
                                item.setBackground(QColor("white"))

    def toggle_bulk_mode(self):
        self.bulk_mode = not self.bulk_mode
        self.bulk_btn.setVisible(not self.bulk_mode)
        self.bulk_return_btn.setVisible(self.bulk_mode)
        self.bulk_cancel_btn.setVisible(self.bulk_mode)

        # Clear selections when exiting bulk mode
        if not self.bulk_mode:
            for r in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(r, 0)
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                    for col in range(self.table.columnCount()):
                        item = self.table.item(r, col) if col > 0 else None
                        if item:
                            item.setBackground(QColor("white"))

    def bulk_return_items(self):
        # Get all checked items
        checked_rows = []
        for r in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(r, 0)
            if checkbox and checkbox.isChecked():
                checked_rows.append(r)

        if not checked_rows:
            QMessageBox.warning(self, "Error", "Please select sales to return.")
            return

        reply = QMessageBox.question(self, "Return to Inventory",
                                     f"Return {len(checked_rows)} sale(s) back to inventory?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for r in sorted(checked_rows, reverse=True):
                sale_id = int(self.table.item(r, 1).text())
                conn = db.get_connection()
                conn.row_factory = db.dict_factory
                c = conn.cursor()
                c.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
                sale = c.fetchone()
                conn.close()

                if sale:
                    # Merge item back to inventory (will add to existing if same item exists)
                    db.merge_inventory(
                        sale['listed_date'] or datetime.now().strftime("%m/%d/%Y"),
                        sale['item_title'],
                        sale['units'],
                        sale['sku'],
                        sale['bin'],
                        sale['store'],
                        sale['category'],
                        sale['cost_of_goods'] / sale['units'] if sale['units'] > 0 else 0,
                        f"Returned from sale on {sale['sold_date']} (Reason: Mistake or Customer Return)"
                    )
                    db.delete_sale(sale_id)

            self.refresh_table()

            # Auto-refresh Inventory tab if available
            if self.inventory_tab:
                # Clear search filters to show the returned items
                self.inventory_tab.search_title.clear()
                self.inventory_tab.search_sku.clear()
                self.inventory_tab.refresh_table()

            self.toggle_bulk_mode()

            if self.inventory_tab:
                QMessageBox.information(self, "Success", f"Returned {len(checked_rows)} sale(s) to inventory!\n\nInventory tab has been refreshed. Search filters cleared.")
            else:
                QMessageBox.information(self, "Success", f"Returned {len(checked_rows)} sale(s) to inventory!\n\nNote: Inventory tab reference not found. Please click on Inventory tab to refresh.")

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Sales", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            sales = db.get_all_sales()
            if not sales:
                QMessageBox.warning(self, "Error", "No sales to export.")
                return

            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sales[0].keys())
                writer.writeheader()
                writer.writerows(sales)

            QMessageBox.information(self, "Success", f"Sales exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

class AddSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sale")
        self.setGeometry(150, 150, 600, 800)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Sold Date:"))
        self.sold_date = QLineEdit()
        self.sold_date.setText(datetime.now().strftime("%m/%d/%Y"))
        layout.addWidget(self.sold_date)

        layout.addWidget(QLabel("Platform:"))
        self.platform = QComboBox()
        self.platform.addItems([""] + PLATFORMS)
        layout.addWidget(self.platform)

        layout.addWidget(QLabel("Item Title:"))
        self.item_title = QLineEdit()
        layout.addWidget(self.item_title)

        layout.addWidget(QLabel("Units:"))
        self.units = QSpinBox()
        self.units.setValue(1)
        layout.addWidget(self.units)

        layout.addWidget(QLabel("Sale Price:"))
        self.sale_price = QDoubleSpinBox()
        self.sale_price.setRange(0, 100000)
        layout.addWidget(self.sale_price)

        layout.addWidget(QLabel("Shipping Collected:"))
        self.shipping_collected = QDoubleSpinBox()
        self.shipping_collected.setRange(0, 100000)
        layout.addWidget(self.shipping_collected)

        layout.addWidget(QLabel("Cost of Goods:"))
        self.cost_of_goods = QDoubleSpinBox()
        self.cost_of_goods.setRange(0, 100000)
        layout.addWidget(self.cost_of_goods)

        layout.addWidget(QLabel("Shipping Cost:"))
        self.shipping_cost = QDoubleSpinBox()
        self.shipping_cost.setRange(0, 100000)
        layout.addWidget(self.shipping_cost)

        layout.addWidget(QLabel("Platform Fee:"))
        self.platform_fee = QDoubleSpinBox()
        self.platform_fee.setRange(0, 100000)
        layout.addWidget(self.platform_fee)

        layout.addWidget(QLabel("Transaction Fee:"))
        self.transaction_fee = QDoubleSpinBox()
        self.transaction_fee.setRange(0, 100000)
        layout.addWidget(self.transaction_fee)

        layout.addWidget(QLabel("SKU:"))
        self.sku = QLineEdit()
        layout.addWidget(self.sku)

        layout.addWidget(QLabel("Category:"))
        self.category = QComboBox()
        self.category.addItems([""] + CATEGORIES)
        self.category.setEditable(True)
        layout.addWidget(self.category)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_sale_data(self):
        total_fees = (self.platform_fee.value() or 0) + (self.transaction_fee.value() or 0)
        profit_loss = (self.sale_price.value() + self.shipping_collected.value()) - \
                      (self.cost_of_goods.value() + self.shipping_cost.value() + total_fees)

        return {
            'sold_date': self.sold_date.text(),
            'platform': self.platform.currentText(),
            'item_title': self.item_title.text(),
            'units': self.units.value(),
            'sale_price': self.sale_price.value(),
            'shipping_collected': self.shipping_collected.value(),
            'cost_of_goods': self.cost_of_goods.value(),
            'shipping_cost': self.shipping_cost.value(),
            'platform_fee': self.platform_fee.value(),
            'transaction_fee': self.transaction_fee.value(),
            'total_fees': total_fees,
            'profit_loss': profit_loss,
            'sku': self.sku.text(),
            'category': self.category.currentText()
        }
