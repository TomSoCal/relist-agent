from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QDoubleSpinBox, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt
import database as db

class TaxSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI with mileage rate, tax percentage, and calculated total"""
        main_layout = QVBoxLayout()

        # MILEAGE DEDUCTION SECTION
        main_layout.addWidget(QLabel("Mileage Deduction (Tax & Deductions)"))
        main_layout.addWidget(QLabel("Enter the IRS standard mileage rate for your region."))

        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Rate: $"))
        self.mileage_rate_input = QDoubleSpinBox()
        self.mileage_rate_input.setRange(0.0, 10.0)
        self.mileage_rate_input.setSingleStep(0.01)
        self.mileage_rate_input.setDecimals(3)
        self.mileage_rate_input.setValue(0.67)
        rate_layout.addWidget(self.mileage_rate_input)
        rate_layout.addWidget(QLabel("/ mile"))

        save_rate_btn = QPushButton("Save Rate")
        save_rate_btn.clicked.connect(self.save_mileage_rate)
        rate_layout.addWidget(save_rate_btn)
        rate_layout.addStretch()

        main_layout.addLayout(rate_layout)
        main_layout.addSpacing(20)

        # TAX SAVINGS PERCENTAGE SECTION
        main_layout.addWidget(QLabel("Tax Savings Percentage"))
        main_layout.addWidget(QLabel("Enter the percentage of your P&L you want to reserve for taxes."))

        tax_pct_layout = QHBoxLayout()
        tax_pct_layout.addWidget(QLabel("Percentage:"))
        self.tax_percentage_input = QDoubleSpinBox()
        self.tax_percentage_input.setRange(0.0, 100.0)
        self.tax_percentage_input.setSingleStep(1.0)
        self.tax_percentage_input.setDecimals(1)
        self.tax_percentage_input.setValue(50.0)
        self.tax_percentage_input.valueChanged.connect(self.update_total_to_save)
        tax_pct_layout.addWidget(self.tax_percentage_input)
        tax_pct_layout.addWidget(QLabel("%"))

        save_tax_btn = QPushButton("Save Percentage")
        save_tax_btn.clicked.connect(self.save_tax_percentage)
        tax_pct_layout.addWidget(save_tax_btn)
        tax_pct_layout.addStretch()

        main_layout.addLayout(tax_pct_layout)
        main_layout.addSpacing(20)

        # CALCULATED TOTAL SECTION
        main_layout.addWidget(QLabel("Total to Save for Taxes"))
        main_layout.addWidget(QLabel("Formula: P&L Total × (1 - Tax Savings %/100)"))

        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total to Save:"))
        self.total_to_save = QLineEdit()
        self.total_to_save.setReadOnly(True)
        self.total_to_save.setText("$0.00")
        total_layout.addWidget(self.total_to_save)
        total_layout.addStretch()

        main_layout.addLayout(total_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_settings(self):
        """Load mileage rate and tax percentage from database"""
        try:
            # Load mileage rate
            mileage_rate = db.get_setting('mileage_rate')
            if mileage_rate:
                self.mileage_rate_input.setValue(float(mileage_rate))
            else:
                self.mileage_rate_input.setValue(0.67)  # Default IRS rate

            # Load tax percentage
            tax_pct = db.get_setting('tax_percentage')
            if tax_pct:
                self.tax_percentage_input.setValue(float(tax_pct))
            else:
                self.tax_percentage_input.setValue(50.0)  # Default 50%

            # Calculate and display total
            self.update_total_to_save()

        except Exception as e:
            print(f"Error loading tax settings: {e}")

    def save_mileage_rate(self):
        """Save mileage rate to database"""
        try:
            rate = self.mileage_rate_input.value()
            db.set_setting('mileage_rate', str(rate))
            QMessageBox.information(self, "Success", f"Mileage rate saved: ${rate:.3f}/mile")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mileage rate: {str(e)}")

    def save_tax_percentage(self):
        """Save tax percentage to database"""
        try:
            pct = self.tax_percentage_input.value()
            db.set_setting('tax_percentage', str(pct))
            QMessageBox.information(self, "Success", f"Tax percentage saved: {pct}%")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tax percentage: {str(e)}")

    def update_total_to_save(self):
        """Recalculate total to save based on P&L and tax percentage"""
        try:
            pl_total = db.get_pl_total()
            tax_pct = self.tax_percentage_input.value()

            # Formula: P&L × (1 - tax% / 100)
            total_to_save = pl_total * (1.0 - tax_pct / 100.0)

            self.total_to_save.setText(f"${total_to_save:,.2f}")
        except Exception as e:
            self.total_to_save.setText("$0.00")
            self.total_to_save.setToolTip(f"Unable to calculate: {str(e)}")

    def showEvent(self, event):
        """Recalculate total when tab is shown (refreshes P&L)"""
        super().showEvent(event)
        self.update_total_to_save()
