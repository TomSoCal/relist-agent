from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTableWidget, QTableWidgetItem, QInputDialog,
                            QMessageBox, QMenu)
from PyQt5.QtCore import Qt
import database as db

class PlatformFeesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI with platform fees table"""
        main_layout = QVBoxLayout()

        main_layout.addWidget(QLabel("Platform Fees:"))
        add_platform_btn_layout = QHBoxLayout()
        add_platform_btn = QPushButton("Add Platform")
        add_platform_btn.clicked.connect(self.add_platform_fee_dialog)
        add_platform_btn_layout.addWidget(add_platform_btn)
        add_platform_btn_layout.addStretch()
        main_layout.addLayout(add_platform_btn_layout)

        self.platform_table = QTableWidget()
        self.platform_table.setColumnCount(5)
        self.platform_table.setHorizontalHeaderLabels(["Platform", "Transaction %", "Shipping %", "Payment %", "Notes"])
        self.platform_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.platform_table.customContextMenuRequested.connect(self.show_platform_context_menu)
        main_layout.addWidget(self.platform_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_settings(self):
        """Load platform fees from database"""
        self.load_platform_fees()

    def load_platform_fees(self):
        """Load and display platform fees"""
        try:
            fees = db.get_all_platform_fees()
            self.platform_table.setRowCount(len(fees))
            for row, fee in enumerate(fees):
                self.platform_table.setItem(row, 0, QTableWidgetItem(fee['platform']))
                self.platform_table.setItem(row, 1, QTableWidgetItem(str(fee.get('transaction_fee', 0))))
                self.platform_table.setItem(row, 2, QTableWidgetItem(str(fee.get('shipping_fee', 0))))
                self.platform_table.setItem(row, 3, QTableWidgetItem(str(fee.get('payment_fee', 0))))
                self.platform_table.setItem(row, 4, QTableWidgetItem(fee.get('notes', '')))
                item = self.platform_table.item(row, 0)
                item.setData(Qt.UserRole, fee['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load platform fees: {str(e)}")

    def add_platform_fee_dialog(self):
        """Add new platform fee"""
        platform, ok = QInputDialog.getText(self, "Add Platform", "Platform name:")
        if not ok or not platform:
            return

        trans_fee, ok = QInputDialog.getDouble(self, "Transaction Fee", "Transaction fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return

        ship_fee, ok = QInputDialog.getDouble(self, "Shipping Fee", "Shipping fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return

        pay_fee, ok = QInputDialog.getDouble(self, "Payment Fee", "Payment fee %:", 0.0, 0.0, 100.0, 2)
        if not ok:
            return

        notes, ok = QInputDialog.getText(self, "Notes", "Notes (optional):")
        if not ok:
            return

        try:
            db.add_platform_fee(platform, trans_fee, ship_fee, pay_fee, notes)
            self.load_platform_fees()
            QMessageBox.information(self, "Success", f"Platform '{platform}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add platform: {str(e)}")

    def delete_platform_fee(self, fee_id):
        """Delete platform fee by ID"""
        try:
            db.delete_platform_fee(fee_id)
            self.load_platform_fees()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete platform fee: {str(e)}")

    def show_platform_context_menu(self, position):
        """Show context menu for platform fees table"""
        item = self.platform_table.itemAt(position)
        if not item:
            return

        fee_id = item.data(Qt.UserRole)
        platform_name = self.platform_table.item(self.platform_table.row(item), 0).text()

        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.platform_table.mapToGlobal(position))

        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                        f"Delete platform '{platform_name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_platform_fee(fee_id)
