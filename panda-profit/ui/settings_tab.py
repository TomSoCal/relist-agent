from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget
from ui.settings.api_info_view import ApiInfoView
from ui.settings.item_settings_view import ItemSettingsView
from ui.settings.platform_fees_view import PlatformFeesView
from ui.settings.tax_settings_view import TaxSettingsView

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.api_view = None
        self.items_view = None
        self.fees_view = None
        self.tax_view = None
        self.init_ui()

    def init_ui(self):
        """Initialize QTabWidget with 4 settings tabs"""
        main_layout = QVBoxLayout()

        # Create QTabWidget
        self.tabs = QTabWidget()

        # Tab 1: API Info
        self.api_button = QPushButton("API Info")
        self.api_button.clicked.connect(self.on_api_clicked)

        # Tab 2: Item Settings
        self.items_button = QPushButton("Item Settings")
        self.items_button.clicked.connect(self.on_items_clicked)

        # Tab 3: Platform Fees
        self.fees_button = QPushButton("Platform Fees")
        self.fees_button.clicked.connect(self.on_fees_clicked)

        # Tab 4: Tax Settings
        self.tax_button = QPushButton("Tax Settings")
        self.tax_button.clicked.connect(self.on_tax_clicked)

        # Add tabs (initially empty, will be filled on click)
        self.tabs.addTab(QWidget(), "API Info")
        self.tabs.addTab(QWidget(), "Item Settings")
        self.tabs.addTab(QWidget(), "Platform Fees")
        self.tabs.addTab(QWidget(), "Tax Settings")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def on_api_clicked(self):
        """Lazy-load API Info view"""
        if self.api_view is None:
            self.api_view = ApiInfoView()
            self.tabs.removeTab(0)
            self.tabs.insertTab(0, self.api_view, "API Info")
        self.tabs.setCurrentIndex(0)

    def on_items_clicked(self):
        """Lazy-load Item Settings view"""
        if self.items_view is None:
            self.items_view = ItemSettingsView()
            self.tabs.removeTab(1)
            self.tabs.insertTab(1, self.items_view, "Item Settings")
        self.tabs.setCurrentIndex(1)

    def on_fees_clicked(self):
        """Lazy-load Platform Fees view"""
        if self.fees_view is None:
            self.fees_view = PlatformFeesView()
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.fees_view, "Platform Fees")
        self.tabs.setCurrentIndex(2)

    def on_tax_clicked(self):
        """Lazy-load Tax Settings view"""
        if self.tax_view is None:
            self.tax_view = TaxSettingsView()
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.tax_view, "Tax Settings")
        self.tabs.setCurrentIndex(3)
