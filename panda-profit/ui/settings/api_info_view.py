from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QMessageBox)
from PyQt5.QtGui import QFont
import config
from oauth_setup import prompt_for_oauth_setup

class ApiInfoView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()

        # Check if eBay is configured
        self.ebay_configured = config.ebay_configured()

        # Warning banner if not configured
        if not self.ebay_configured:
            warning_layout = QHBoxLayout()
            warning_label = QLabel("⚠️  eBay API not configured — Setup required to use inventory/sales features")
            warning_label.setStyleSheet("background-color: #2a2a1a; padding: 10px; border-radius: 4px; color: #ffaa00;")
            warning_font = QFont()
            warning_font.setBold(True)
            warning_label.setFont(warning_font)
            warning_layout.addWidget(warning_label)
            main_layout.addLayout(warning_layout)

        # eBay API Settings
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
            setup_btn.setStyleSheet("background-color: #ffaa00; font-weight: bold; padding: 5px; color: #000000;")
            setup_btn.clicked.connect(self.reconfigure_oauth)
            button_layout.addWidget(setup_btn)

            info_label = QLabel("(Required to use inventory/sales features)")
            info_label.setStyleSheet("color: #aaa; font-style: italic;")
            button_layout.addWidget(info_label)

        button_layout.addStretch()
        ebay_layout.addLayout(button_layout)

        main_layout.addLayout(ebay_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_settings(self):
        """Load eBay credentials from config"""
        try:
            if config.ebay_configured():
                ebay_config = config.get_ebay_config()
                self.app_id.setText(ebay_config.get('app_id', ''))
                self.cert_id.setPlaceholderText("(Already configured in PandaSuite)")
            else:
                self.app_id.setPlaceholderText("Enter your eBay App ID")
                self.cert_id.setPlaceholderText("Enter your eBay Cert ID")
        except Exception as e:
            print(f"Error loading API settings: {e}")

    def reconfigure_oauth(self):
        """Run OAuth setup"""
        try:
            if prompt_for_oauth_setup(self):
                QMessageBox.information(self, "Success",
                    "✓ eBay OAuth credentials configured!\n\n"
                    "These credentials are shared with all PandaSuite apps.\n"
                    "Restart the app or click Settings tab to see updates.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup eBay OAuth: {str(e)}")

    def test_ebay_connection(self):
        """Test eBay API connection"""
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
