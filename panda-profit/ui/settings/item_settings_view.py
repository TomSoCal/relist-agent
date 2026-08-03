from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QListWidget, QListWidgetItem, QTableWidget,
                            QTableWidgetItem, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
import database as db
from constants import CATEGORIES, STORES

class ItemSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI with three sections: Stores, Categories, Brands"""
        main_layout = QVBoxLayout()

        # STORES SECTION
        main_layout.addWidget(QLabel("Stores:"))
        stores_btn_layout = QHBoxLayout()
        add_store_btn = QPushButton("Add Store")
        add_store_btn.clicked.connect(self.add_store_dialog)
        delete_store_btn = QPushButton("Delete Store")
        delete_store_btn.clicked.connect(self.delete_store)
        stores_btn_layout.addWidget(add_store_btn)
        stores_btn_layout.addWidget(delete_store_btn)
        stores_btn_layout.addStretch()
        main_layout.addLayout(stores_btn_layout)

        self.stores_list = QListWidget()
        self.stores_list.addItems(STORES)
        main_layout.addWidget(self.stores_list)

        main_layout.addSpacing(20)

        # CATEGORIES SECTION
        main_layout.addWidget(QLabel("Categories:"))
        cat_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.clicked.connect(self.add_category_dialog)
        delete_cat_btn = QPushButton("Delete Category")
        delete_cat_btn.clicked.connect(self.delete_category)
        cat_btn_layout.addWidget(add_cat_btn)
        cat_btn_layout.addWidget(delete_cat_btn)
        cat_btn_layout.addStretch()
        main_layout.addLayout(cat_btn_layout)

        self.categories_list = QListWidget()
        self.categories_list.addItems(CATEGORIES)
        main_layout.addWidget(self.categories_list)

        main_layout.addSpacing(20)

        # BRANDS SECTION
        main_layout.addWidget(QLabel("Brands:"))
        add_brand_btn_layout = QHBoxLayout()
        add_brand_btn = QPushButton("Add Brand")
        add_brand_btn.clicked.connect(self.add_brand_dialog)
        add_brand_btn_layout.addWidget(add_brand_btn)
        add_brand_btn_layout.addStretch()
        main_layout.addLayout(add_brand_btn_layout)

        self.brands_table = QTableWidget()
        self.brands_table.setColumnCount(1)
        self.brands_table.setHorizontalHeaderLabels(["Brand Name"])
        self.brands_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.brands_table.customContextMenuRequested.connect(self.show_brands_context_menu)
        main_layout.addWidget(self.brands_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_settings(self):
        """Load brands from database"""
        self.load_brands()

    def load_brands(self):
        """Load brands table from database"""
        try:
            brands = db.get_all_brands()
            self.brands_table.setRowCount(len(brands))
            for row, brand in enumerate(brands):
                self.brands_table.setItem(row, 0, QTableWidgetItem(brand['name']))
                item = self.brands_table.item(row, 0)
                item.setData(Qt.UserRole, brand['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load brands: {str(e)}")

    def add_store_dialog(self):
        """Add new store to STORES list"""
        text, ok = QInputDialog.getText(self, "Add New Store", "Store name:")
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
        """Delete selected store"""
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
        """Add new category to CATEGORIES list"""
        text, ok = QInputDialog.getText(self, "Add New Category", "Category name:")
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
        """Delete selected category"""
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

    def add_brand_dialog(self):
        """Add new brand to database"""
        name, ok = QInputDialog.getText(self, "Add Brand", "Brand name:")
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
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.brands_table.mapToGlobal(position))

        if action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete",
                                        f"Delete brand '{brand_name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_brand(brand_id)

    def save_custom_items(self):
        """Persist STORES and CATEGORIES to database"""
        import json
        db.set_setting('custom_stores', json.dumps(STORES))
        db.set_setting('custom_categories', json.dumps(CATEGORIES))
