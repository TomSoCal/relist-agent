from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTableWidget, QTableWidgetItem, QDialog, QLabel,
                            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                            QTextEdit, QMessageBox, QDateEdit, QHeaderView,
                            QScrollArea, QListWidget, QListWidgetItem, QFileDialog,
                            QCheckBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
from datetime import datetime
import database as db
from constants import CATEGORIES, STORES
import os
import webbrowser

class InventoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout()

        # Button bar
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item_dialog)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_item_dialog)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_item)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_table)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "✓", "ID", "Listed Date", "Item Title", "Units", "SKU",
            "Store", "Category", "Cost", "Notes", "XP"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Disable inline editing - users must select and click Edit
        from PyQt5.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Set checkbox column narrower
        self.table.setColumnWidth(0, 40)

        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def refresh_table(self):
        items = db.get_all_inventory()
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Checkbox column
            checkbox = QCheckBox()
            self.table.setCellWidget(row, 0, checkbox)

            self.table.setItem(row, 1, QTableWidgetItem(str(item['id'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(item['listed_date'])))
            self.table.setItem(row, 3, QTableWidgetItem(item['item_title']))
            self.table.setItem(row, 4, QTableWidgetItem(str(item['units'])))
            self.table.setItem(row, 5, QTableWidgetItem(item['sku'] or ''))
            self.table.setItem(row, 6, QTableWidgetItem(item['store'] or ''))
            self.table.setItem(row, 7, QTableWidgetItem(item['category'] or ''))
            self.table.setItem(row, 8, QTableWidgetItem(f"${item['cost']:.2f}" if item['cost'] else ''))
            self.table.setItem(row, 9, QTableWidgetItem(item['notes'] or ''))
            self.table.setItem(row, 10, QTableWidgetItem(str(item['xp'] or 0)))

    def add_item_dialog(self):
        dialog = AddItemDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            db.add_inventory(
                dialog.listed_date.text(),
                dialog.item_title.text(),
                dialog.units.value(),
                dialog.sku.text(),
                dialog.bin.text(),
                dialog.store.currentText(),
                dialog.category.currentText(),
                dialog.cost.value(),
                dialog.notes.toPlainText(),
                dialog.xp.value()
            )
            self.refresh_table()
            QMessageBox.information(self, "Success", "Item added successfully!")

    def edit_item_dialog(self):
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break

        if checked_row is None:
            QMessageBox.warning(self, "Error", "Please check the box next to the item you want to edit.")
            return

        item_id = int(self.table.item(checked_row, 1).text())
        item = db.get_inventory_by_id(item_id)

        dialog = EditItemDialog(self, item)
        if dialog.exec_() == QDialog.Accepted:
            db.update_inventory(
                item_id,
                listed_date=dialog.listed_date.text(),
                item_title=dialog.item_title.text(),
                units=dialog.units.value(),
                sku=dialog.sku.text(),
                bin=dialog.bin.text(),
                store=dialog.store.currentText(),
                category=dialog.category.currentText(),
                cost=dialog.cost.value(),
                notes=dialog.notes.toPlainText(),
                xp=dialog.xp.value()
            )
            self.refresh_table()
            QMessageBox.information(self, "Success", "Item updated successfully!")

    def delete_item(self):
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break

        if checked_row is None:
            QMessageBox.warning(self, "Error", "Please check the box next to the item you want to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this item?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            item_id = int(self.table.item(checked_row, 1).text())
            db.delete_inventory(item_id)
            self.refresh_table()
            QMessageBox.information(self, "Success", "Item deleted successfully!")

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Inventory Item")
        self.setGeometry(150, 150, 500, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Listed Date:"))
        self.listed_date = QLineEdit()
        self.listed_date.setText(datetime.now().strftime("%m/%d/%Y"))
        layout.addWidget(self.listed_date)

        layout.addWidget(QLabel("Item Title:"))
        self.item_title = QLineEdit()
        layout.addWidget(self.item_title)

        layout.addWidget(QLabel("Units:"))
        self.units = QSpinBox()
        self.units.setValue(1)
        layout.addWidget(self.units)

        layout.addWidget(QLabel("SKU:"))
        self.sku = QLineEdit()
        layout.addWidget(self.sku)

        layout.addWidget(QLabel("Bin:"))
        self.bin = QLineEdit()
        layout.addWidget(self.bin)

        layout.addWidget(QLabel("Store:"))
        self.store = QComboBox()
        self.store.addItems([""] + STORES)
        self.store.setEditable(True)
        layout.addWidget(self.store)

        layout.addWidget(QLabel("Category:"))
        self.category = QComboBox()
        self.category.addItems([""] + CATEGORIES)
        self.category.setEditable(True)
        layout.addWidget(self.category)

        layout.addWidget(QLabel("Cost:"))
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10000)
        layout.addWidget(self.cost)

        layout.addWidget(QLabel("Notes:"))
        self.notes = QTextEdit()
        layout.addWidget(self.notes)

        layout.addWidget(QLabel("XP:"))
        self.xp = QSpinBox()
        layout.addWidget(self.xp)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

class EditItemDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.item_id = item['id']
        self.images = db.get_inventory_images(self.item_id)
        self.setWindowTitle("Edit Inventory Item")
        self.setGeometry(150, 150, 700, 800)
        self.init_ui()
        self.populate_fields()

    def init_ui(self):
        layout = QVBoxLayout()

        # Item fields (top section)
        layout.addWidget(QLabel("Listed Date:"))
        self.listed_date = QLineEdit()
        layout.addWidget(self.listed_date)

        layout.addWidget(QLabel("Item Title:"))
        self.item_title = QLineEdit()
        layout.addWidget(self.item_title)

        layout.addWidget(QLabel("Units:"))
        self.units = QSpinBox()
        self.units.setValue(1)
        layout.addWidget(self.units)

        layout.addWidget(QLabel("SKU:"))
        self.sku = QLineEdit()
        layout.addWidget(self.sku)

        layout.addWidget(QLabel("Bin:"))
        self.bin = QLineEdit()
        layout.addWidget(self.bin)

        layout.addWidget(QLabel("Store:"))
        self.store = QComboBox()
        self.store.addItems([""] + STORES)
        self.store.setEditable(True)
        layout.addWidget(self.store)

        layout.addWidget(QLabel("Category:"))
        self.category = QComboBox()
        self.category.addItems([""] + CATEGORIES)
        self.category.setEditable(True)
        layout.addWidget(self.category)

        layout.addWidget(QLabel("Cost:"))
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10000)
        layout.addWidget(self.cost)

        layout.addWidget(QLabel("Notes:"))
        self.notes = QTextEdit()
        layout.addWidget(self.notes)

        layout.addWidget(QLabel("XP:"))
        self.xp = QSpinBox()
        layout.addWidget(self.xp)

        # Images section
        layout.addWidget(QLabel("Pictures:"))

        # Image buttons
        image_btn_layout = QHBoxLayout()
        add_img_btn = QPushButton("Add Picture")
        add_img_btn.clicked.connect(self.add_image)
        delete_img_btn = QPushButton("Delete Selected")
        delete_img_btn.clicked.connect(self.delete_selected_image)
        image_btn_layout.addWidget(add_img_btn)
        image_btn_layout.addWidget(delete_img_btn)
        layout.addLayout(image_btn_layout)

        # Image list
        self.image_list = QListWidget()
        self.image_list.itemDoubleClicked.connect(self.view_image)
        layout.addWidget(self.image_list)

        # Load images into list
        self.refresh_image_list()

        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def populate_fields(self):
        self.listed_date.setText(self.item['listed_date'])
        self.item_title.setText(self.item['item_title'])
        self.units.setValue(self.item['units'])
        self.sku.setText(self.item['sku'] or '')
        self.bin.setText(self.item['bin'] or '')

        # Set combobox values
        store_val = self.item['store'] or ''
        store_idx = self.store.findText(store_val)
        if store_idx >= 0:
            self.store.setCurrentIndex(store_idx)
        else:
            self.store.setCurrentText(store_val)

        cat_val = self.item['category'] or ''
        cat_idx = self.category.findText(cat_val)
        if cat_idx >= 0:
            self.category.setCurrentIndex(cat_idx)
        else:
            self.category.setCurrentText(cat_val)

        self.cost.setValue(self.item['cost'] or 0)
        self.notes.setText(self.item['notes'] or '')
        self.xp.setValue(self.item['xp'] or 0)

    def refresh_image_list(self):
        self.image_list.clear()
        self.images = db.get_inventory_images(self.item_id)
        for img in self.images:
            item_widget = QListWidgetItem(f"📷 {img['image_url'][:80]}")
            item_widget.setData(Qt.UserRole, img['id'])
            self.image_list.addItem(item_widget)

    def add_image(self):
        # Create a simple dialog with two options
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Picture")
        dialog.setGeometry(200, 200, 400, 150)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Choose how to add a picture:"))

        # URL button
        url_btn = QPushButton("📋 Enter Web URL")
        url_btn.clicked.connect(lambda: self.add_image_from_url(dialog))
        layout.addWidget(url_btn)

        # Browse button
        browse_btn = QPushButton("📁 Browse Computer")
        browse_btn.clicked.connect(lambda: self.add_image_from_file(dialog))
        layout.addWidget(browse_btn)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def add_image_from_url(self, parent_dialog):
        from PyQt5.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(parent_dialog, "Add Picture", "Enter image web URL:")
        if ok and url:
            db.add_inventory_image(self.item_id, url)
            self.refresh_image_list()
            parent_dialog.accept()

    def add_image_from_file(self, parent_dialog):
        file_path, _ = QFileDialog.getOpenFileName(
            parent_dialog,
            "Select Picture",
            os.path.expanduser("~\\Pictures"),
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
        )
        if file_path:
            # Convert to file:// URL
            url = f"file:///{os.path.abspath(file_path).replace(chr(92), '/')}"
            db.add_inventory_image(self.item_id, url)
            self.refresh_image_list()
            parent_dialog.accept()

    def delete_selected_image(self):
        current = self.image_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select an image to delete.")
            return

        image_id = current.data(Qt.UserRole)
        db.delete_inventory_image(image_id)
        self.refresh_image_list()

    def view_image(self, item):
        image_id = item.data(Qt.UserRole)
        image = next((i for i in self.images if i['id'] == image_id), None)
        if image:
            url = image['image_url']
            if url.startswith('file://'):
                file_path = url.replace('file:///', '').replace('/', chr(92))
                if os.path.exists(file_path):
                    os.startfile(file_path)
            else:
                import webbrowser
                webbrowser.open(url)
