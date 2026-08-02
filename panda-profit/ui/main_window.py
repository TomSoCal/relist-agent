from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                            QMenuBar, QMenu, QStatusBar, QMessageBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.dashboard_tab import DashboardTab
from ui.inventory_tab import InventoryTab
from ui.inventory_history_tab import InventoryHistoryTab
from ui.sales_tab import SalesTab
from ui.settings_tab import SettingsTab
from ui.day_tab import DayTab
from ui.month_tab import MonthTab
from ui.year_tab import YearTab
from ui.analytics_tab import AnalyticsTab
from ui.mileage_tab import MileageTab
from ui.reports_tab import ReportsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab()
        self.sales_tab = SalesTab()
        self.inventory_tab = InventoryTab(sales_tab=self.sales_tab)
        # Pass inventory_tab reference to sales_tab for auto-refresh on return
        self.sales_tab.inventory_tab = self.inventory_tab
        self.inventory_history_tab = InventoryHistoryTab()
        self.day_tab = DayTab()
        self.month_tab = MonthTab()
        self.year_tab = YearTab()
        self.analytics_tab = AnalyticsTab()
        self.mileage_tab = MileageTab()
        self.reports_tab = ReportsTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.inventory_tab, "Inventory")
        self.tabs.addTab(self.inventory_history_tab, "Inventory History")
        self.tabs.addTab(self.sales_tab, "Sales")
        self.tabs.addTab(self.day_tab, "Day")
        self.tabs.addTab(self.month_tab, "Month")
        self.tabs.addTab(self.year_tab, "Year")
        self.tabs.addTab(self.analytics_tab, "Forecasting")
        self.tabs.addTab(self.mileage_tab, "Mileage")
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar().showMessage("Ready")

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        export_action = file_menu.addAction("Export Sales to CSV")
        export_action.triggered.connect(self.export_sales)

        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def export_sales(self):
        self.sales_tab.export_to_csv()

    def show_about(self):
        QMessageBox.about(self, "About Panda Profit",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Inventory and sales tracking for resellers.\n"
            "© Trashed Panda 2026")

    def refresh_settings_tab(self):
        """Rebuild settings tab after OAuth setup"""
        # Remove old settings tab
        old_index = self.tabs.indexOf(self.settings_tab)
        self.tabs.removeTab(old_index)

        # Create new settings tab
        self.settings_tab = SettingsTab()
        self.tabs.insertTab(old_index, self.settings_tab, "Settings")
