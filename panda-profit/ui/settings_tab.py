from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QGroupBox, QMessageBox, QListWidget,
                            QListWidgetItem, QDialog, QTableWidget, QTableWidgetItem, QInputDialog,
                            QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import database as db
import config
from constants import CATEGORIES, STORES
from oauth_setup import prompt_for_oauth_setup
from theme_manager import get_theme_manager

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # Check if eBay is configured
        self.ebay_configured = config.ebay_configured()

        # Warning banner if not configured
        if not self.ebay_configured:
            warning_layout = QHBoxLayout()
            warning_label = QLabel("⚠️  eBay API not configured — Setup required to use inventory/sales features")
            warning_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 4px; color: #856404;")
            warning_font = QFont()
            warning_font.setBold(True)
            warning_label.setFont(warning_font)
            warning_layout.addWidget(warning_label)
            layout.addLayout(warning_layout)

        # eBay API Settings Group
        ebay_group = QGroupBox("eBay API Configuration")
        ebay_layout = QVBoxLayout()

        if self.ebay_configured:
            status_text = "✓ eBay credentials configured"
        else:
            status_text = "✗ eBay credentials not configured"

        ebay_layout.addWidget(QLabel(status_text))

        ebay_layout.addWidget(QLabel("App ID:"))
        self.app_id = QLineEdit()
        self.app_id.setReadOnly(True)
        ebay_layout.addWidget(self.app_id)

        ebay_layout.addWidget(QLabel("Cert ID:"))
        self.cert_id = QLineEdit()
        self.cert_id.setEchoMode(QLineEdit.Password)
        self.cert_id.setReadOnly(True)
        ebay_layout.addWidget(self.cert_id)

        button_layout = QHBoxLayout()

        if self.ebay_configured:
            reconfigure_btn = QPushButton("Reconfigure OAuth")
            reconfigure_btn.clicked.connect(self.reconfigure_oauth)
            button_layout.addWidget(reconfigure_btn)

            test_btn = QPushButton("Test Connection")
            test_btn.clicked.connect(self.test_ebay_connection)
            button_layout.addWidget(test_btn)
        else:
            setup_btn = QPushButton("Setup eBay OAuth")
            setup_btn.setStyleSheet("background-color: #ffc107; font-weight: bold; padding: 5px;")
            setup_btn.clicked.connect(self.reconfigure_oauth)
            button_layout.addWidget(setup_btn)

            info_label = QLabel("(Required to use inventory/sales features)")
            info_label.setStyleSheet("color: #666; font-style: italic;")
            button_layout.addWidget(info_label)

        button_layout.addStretch()

        ebay_layout.addLayout(button_layout)
        ebay_group.setLayout(ebay_layout)

        # Store & Category Management
        mgmt_group = QGroupBox("Manage Stores & Categories")
        mgmt_layout = QVBoxLayout()

        # Stores
        mgmt_layout.addWidget(QLabel("Stores:"))
        stores_btn_layout = QHBoxLayout()
        add_store_btn = QPushButton("Add Store")
        add_store_btn.clicked.connect(self.add_store_dialog)
        delete_store_btn = QPushButton("Delete Store")
        delete_store_btn.clicked.connect(self.delete_store)
        stores_btn_layout.addWidget(add_store_btn)
        stores_btn_layout.addWidget(delete_store_btn)
        stores_btn_layout.addStretch()
        mgmt_layout.addLayout(stores_btn_layout)

        self.stores_list = QListWidget()
        self.stores_list.addItems(STORES)
        mgmt_layout.addWidget(self.stores_list)

        # Categories
        mgmt_layout.addWidget(QLabel("Categories:"))
        cat_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.clicked.connect(self.add_category_dialog)
        delete_cat_btn = QPushButton("Delete Category")
        delete_cat_btn.clicked.connect(self.delete_category)
        cat_btn_layout.addWidget(add_cat_btn)
        cat_btn_layout.addWidget(delete_cat_btn)
        cat_btn_layout.addStretch()
        mgmt_layout.addLayout(cat_btn_layout)

        self.categories_list = QListWidget()
        self.categories_list.addItems(CATEGORIES)
        mgmt_layout.addWidget(self.categories_list)

        mgmt_group.setLayout(mgmt_layout)

        # Expense Categories Management
        expense_group = QGroupBox("Expense Categories")
        expense_layout = QVBoxLayout()

        expense_layout.addWidget(QLabel("Expense Categories:"))
        add_expense_btn_layout = QHBoxLayout()
        add_expense_btn = QPushButton("Add Expense Category")
        add_expense_btn.clicked.connect(self.add_expense_category_dialog)
        add_expense_btn_layout.addWidget(add_expense_btn)
        add_expense_btn_layout.addStretch()
        expense_layout.addLayout(add_expense_btn_layout)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(2)
        self.expense_table.setHorizontalHeaderLabels(["Name", "Type"])
        self.expense_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.expense_table.customContextMenuRequested.connect(self.show_expense_context_menu)
        expense_layout.addWidget(self.expense_table)

        expense_group.setLayout(expense_layout)

        # Platform Fees Management
        platform_group = QGroupBox("Platform Fees")
        platform_layout = QVBoxLayout()

        platform_layout.addWidget(QLabel("Platform Fees:"))
        add_platform_btn_layout = QHBoxLayout()
        add_platform_btn = QPushButton("Add Platform")
        add_platform_btn.clicked.connect(self.add_platform_fee_dialog)
        add_platform_btn_layout.addWidget(add_platform_btn)
        add_platform_btn_layout.addStretch()
        platform_layout.addLayout(add_platform_btn_layout)

        self.platform_table = QTableWidget()
        self.platform_table.setColumnCount(5)
        self.platform_table.setHorizontalHeaderLabels(["Platform", "Transaction %", "Shipping %", "Payment %", "Notes"])
        self.platform_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.platform_table.customContextMenuRequested.connect(self.show_platform_context_menu)
        platform_layout.addWidget(self.platform_table)

        platform_group.setLayout(platform_layout)

        # Brands Management
        brands_group = QGroupBox("Brands")
        brands_layout = QVBoxLayout()

        brands_layout.addWidget(QLabel("Brands:"))
        add_brand_btn_layout = QHBoxLayout()
        add_brand_btn = QPushButton("Add Brand")
        add_brand_btn.clicked.connect(self.add_brand_dialog)
        add_brand_btn_layout.addWidget(add_brand_btn)
        add_brand_btn_layout.addStretch()
        brands_layout.addLayout(add_brand_btn_layout)

        self.brands_table = QTableWidget()
        self.brands_table.setColumnCount(1)
        self.brands_table.setHorizontalHeaderLabels(["Brand Name"])
        self.brands_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.brands_table.customContextMenuRequested.connect(self.show_brands_context_menu)
        brands_layout.addWidget(self.brands_table)

        brands_group.setLayout(brands_layout)

        # Appearance Settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()

        appearance_layout.addWidget(QLabel("Theme:"))
        theme_layout = QHBoxLayout()

        self.theme_group = QButtonGroup()
        self.light_radio = QRadioButton("Light Mode")
        self.dark_radio = QRadioButton("Dark Mode (Panda Print)")

        theme_manager = get_theme_manager()
        if theme_manager.is_dark_mode():
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        self.theme_group.addButton(self.light_radio, 0)
        self.theme_group.addButton(self.dark_radio, 1)
        self.theme_group.buttonClicked.connect(self.on_theme_changed)

        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)

        appearance_group.setLayout(appearance_layout)

        layout.addWidget(ebay_group)
        layout.addWidget(mgmt_group)
        layout.addWidget(expense_group)
        layout.addWidget(platform_group)
        layout.addWidget(brands_group)
        layout.addWidget(appearance_group)
        layout.addStretch()
        self.setLayout(layout)

    def load_settings(self):
        """Load eBay credentials from PandaSuite (shared)"""
        try:
            if config.ebay_configured():
                ebay_config = config.get_ebay_config()
                self.app_id.setText(ebay_config.get('app_id', ''))
                # Note: cert_id is sensitive, don't display it
                self.cert_id.setPlaceholderText("(Already configured in PandaSuite)")
            else:
                self.app_id.setPlaceholderText("Enter your eBay App ID (will be shared with all PandaSuite apps)")
                self.cert_id.setPlaceholderText("Enter your eBay Cert ID")
        except Exception as e:
            print(f"Error loading settings: {e}")

        # Load management data
        self.load_expense_categories()
        self.load_platform_fees()
        self.load_brands()

    def reconfigure_oauth(self):
        """Run OAuth setup to configure or update credentials"""
        try:
            if prompt_for_oauth_setup(self):
                QMessageBox.information(self, "Success",
                    "✓ eBay OAuth credentials configured!\n\n"
                    "These credentials are shared with all PandaSuite apps.\n"
                    "Restart the app or click Settings tab to see updates.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup eBay OAuth: {str(e)}")

    def test_ebay_connection(self):
        """Test eBay API connection using PandaSuite credentials"""
        if not config.ebay_configured():
            QMessageBox.warning(self, "Setup Required",
                "eBay credentials not configured yet.\n\n"
                "Click 'Setup eBay OAuth' to get started.")
            return

        try:
            token = config.get_ebay_token()
            QMessageBox.information(self, "Connection Successful",
                "✓ eBay API connection successful!\n\n"
                "Token is valid and will auto-refresh when needed.\n"
                "Credentials are shared with all PandaSuite apps.")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed",
                f"Error: {str(e)}\n\n"
                "Try clicking 'Reconfigure OAuth' to re-authenticate.")

    def add_store_dialog(self):
        text, ok = self._get_text_input("Add New Store", "Store name:")
        if ok and text:
            if text not in STORES:
                STORES.append(text)
                STORES.sort()
                self.stores_list.clear()
                self.stores_list.addItems(STORES)
                self.save_custom_items()
                QMessageBox.information(self, "Success", f"Store '{text}' added!")
            else:
                QMessageBox.warning(self, "Error", "Store already exists")

    def delete_store(self):
        current = self.stores_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a store to delete")
            return

        store_name = current.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete store '{store_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            STORES.remove(store_name)
            self.stores_list.clear()
            self.stores_list.addItems(STORES)
            self.save_custom_items()
            QMessageBox.information(self, "Success", f"Store '{store_name}' deleted!")

    def add_category_dialog(self):
        text, ok = self._get_text_input("Add New Category", "Category name:")
        if ok and text:
            if text not in CATEGORIES:
                CATEGORIES.append(text)
                CATEGORIES.sort()
                self.categories_list.clear()
                self.categories_list.addItems(CATEGORIES)
                self.save_custom_items()
                QMessageBox.information(self, "Success", f"Category '{text}' added!")
            else:
                QMessageBox.warning(self, "Error", "Category already exists")

    def delete_category(self):
        current = self.categories_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a category to delete")
            return

        category_name = current.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete category '{category_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            CATEGORIES.remove(category_name)
            self.categories_list.clear()
            self.categories_list.addItems(CATEGORIES)
            self.save_custom_items()
            QMessageBox.information(self, "Success", f"Category '{category_name}' deleted!")

    def save_custom_items(self):
        import json
        db.set_setting('custom_stores', json.dumps(STORES))
        db.set_setting('custom_categories', json.dumps(CATEGORIES))

    # Expense Categories Management
    def load_expense_categories(self):
        """Load expense categories from database and populate table"""
        try:
            categories = db.get_all_expense_categories()
            self.expense_table.setRowCount(len(categories))
            for row, category in enumerate(categories):
                self.expense_table.setItem(row, 0, QTableWidgetItem(category['name']))
                self.expense_table.setItem(row, 1, QTableWidgetItem(category['category_type']))
                # Store ID in item data for deletion
                item = self.expense_table.item(row, 0)
                item.setData(Qt.UserRole, category['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load expense categories: {str(e)}")

    def add_expense_category_dialog(self):
        """Open dialog to add new expense category"""
        name, ok = self._get_text_input("Add Expense Category", "Category name:")
        if not ok or not name:
            return

        # Get category type
        types = ["supplies", "shipping", "equipment", "subscriptions", "marketing", "services", "facility", "insurance", "vehicle", "travel", "meals", "education", "other"]
        category_type, type_ok = QInputDialog.getItem(self, "Select Type", "Category type:", types, 0, False)
        if not type_ok:
            return

        try:
            db.add_expense_category(name, category_type)
            self.load_expense_categories()
            QMessageBox.information(self, "Success", f"Expense category '{name}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add expense category: {str(e)}")

    def delete_expense_category(self, category_id):
        """Delete expense category by ID"""
        try:
            db.delete_expense_category(category_id)
            self.load_expense_categories()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete expense category: {str(e)}")

    def show_expense_context_menu(self, position):
        """Show context menu for expense categories table"""
        item = self.expense_table.itemAt(position)
        if not item:
            return

        category_id = item.data(Qt.UserRole)
        category_name = self.expense_table.item(self.expense_table.row(item), 0).text()

        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.expense_table.mapToGlobal(position))

        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                       f"Delete expense category '{category_name}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_expense_category(category_id)

    # Platform Fees Management
    def load_platform_fees(self):
        """Load platform fees from database and populate table"""
        try:
            fees = db.get_all_platform_fees()
            self.platform_table.setRowCount(len(fees))
            for row, fee in enumerate(fees):
                self.platform_table.setItem(row, 0, QTableWidgetItem(fee['platform']))
                self.platform_table.setItem(row, 1, QTableWidgetItem(str(fee['transaction_fee_pct'])))
                self.platform_table.setItem(row, 2, QTableWidgetItem(str(fee['shipping_fee_pct'])))
                self.platform_table.setItem(row, 3, QTableWidgetItem(str(fee['payment_fee_pct'])))
                self.platform_table.setItem(row, 4, QTableWidgetItem(fee['notes'] or ''))
                # Store ID in item data for deletion
                item = self.platform_table.item(row, 0)
                item.setData(Qt.UserRole, fee['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load platform fees: {str(e)}")

    def add_platform_fee_dialog(self):
        """Open dialog to add new platform fee"""
        platform, ok = self._get_text_input("Add Platform", "Platform name:")
        if not ok or not platform:
            return

        try:
            transaction_pct, t_ok = QInputDialog.getDouble(self, "Transaction Fee", "Transaction fee %:", 0, 0, 100, 2)
            if not t_ok:
                return

            shipping_pct, s_ok = QInputDialog.getDouble(self, "Shipping Fee", "Shipping fee %:", 0, 0, 100, 2)
            if not s_ok:
                return

            payment_pct, p_ok = QInputDialog.getDouble(self, "Payment Fee", "Payment fee %:", 0, 0, 100, 2)
            if not p_ok:
                return

            notes, n_ok = self._get_text_input("Platform Notes", "Notes (optional):")
            if not n_ok:
                return

            db.add_platform_fee(platform, 0, transaction_pct, shipping_pct, payment_pct, notes if notes else None)
            self.load_platform_fees()
            QMessageBox.information(self, "Success", f"Platform '{platform}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add platform fee: {str(e)}")

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

        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.platform_table.mapToGlobal(position))

        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                       f"Delete platform '{platform_name}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_platform_fee(fee_id)

    # Brands Management
    def load_brands(self):
        """Load brands from database and populate table"""
        try:
            brands = db.get_all_brands()
            self.brands_table.setRowCount(len(brands))
            for row, brand in enumerate(brands):
                item = QTableWidgetItem(brand['name'])
                item.setData(Qt.UserRole, brand['id'])
                self.brands_table.setItem(row, 0, item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load brands: {str(e)}")

    def add_brand_dialog(self):
        """Open dialog to add new brand"""
        name, ok = self._get_text_input("Add Brand", "Brand name:")
        if not ok or not name:
            return

        try:
            db.add_brand(name)
            self.load_brands()
            QMessageBox.information(self, "Success", f"Brand '{name}' added!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add brand: {str(e)}")

    def delete_brand(self, brand_id):
        """Delete brand by ID"""
        try:
            db.delete_brand(brand_id)
            self.load_brands()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete brand: {str(e)}")

    def show_brands_context_menu(self, position):
        """Show context menu for brands table"""
        item = self.brands_table.itemAt(position)
        if not item:
            return

        brand_id = item.data(Qt.UserRole)
        brand_name = self.brands_table.item(self.brands_table.row(item), 0).text()

        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.brands_table.mapToGlobal(position))

        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                       f"Delete brand '{brand_name}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_brand(brand_id)

    def _get_text_input(self, title, label):
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok

    def on_theme_changed(self, button):
        """Handle theme selection change"""
        theme_manager = get_theme_manager()
        if button == self.light_radio:
            theme_manager.apply_theme(theme_manager.LIGHT)
        elif button == self.dark_radio:
            theme_manager.apply_theme(theme_manager.DARK)
