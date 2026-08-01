"""Reports tab for generating PDF and CSV export of sales data.

Displays:
- Report type selector (Monthly Summary, Custom Date Range, Year-to-Date, All Time)
- Date range pickers (start and end dates)
- Export buttons for PDF and CSV formats
- File dialogs for saving reports to disk
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QComboBox, QDateEdit, QPushButton, QMessageBox,
                            QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import reports


class ReportsTab(QWidget):
    """Tab for generating and exporting sales reports."""

    def __init__(self):
        """Initialize the Reports tab."""
        super().__init__()
        self.init_ui()
        self._update_date_range_from_report_type()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Report Type Section
        report_type_layout = QHBoxLayout()
        report_type_layout.addWidget(QLabel("Report Type:"))

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Monthly Summary",
            "Custom Date Range",
            "Year-to-Date",
            "All Time"
        ])
        self.report_type_combo.setCurrentIndex(0)  # Default: Monthly Summary
        self.report_type_combo.currentIndexChanged.connect(
            self._update_date_range_from_report_type
        )
        report_type_layout.addWidget(self.report_type_combo)
        report_type_layout.addStretch()

        layout.addLayout(report_type_layout)

        # Date Range Section
        date_range_group = QGroupBox("Date Range")
        date_range_layout = QHBoxLayout()

        # Start Date
        date_range_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        date_range_layout.addWidget(self.start_date_edit)

        # End Date
        date_range_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.end_date_edit)

        date_range_layout.addStretch()
        date_range_group.setLayout(date_range_layout)
        layout.addWidget(date_range_group)

        # Export Section
        export_layout = QHBoxLayout()

        self.pdf_btn = QPushButton("Generate PDF")
        self.pdf_btn.clicked.connect(self.generate_pdf)
        export_layout.addWidget(self.pdf_btn)

        self.csv_btn = QPushButton("Generate CSV")
        self.csv_btn.clicked.connect(self.generate_csv)
        export_layout.addWidget(self.csv_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        # Info section
        info_label = QLabel(
            "Select a report type and date range, then click Generate PDF or Generate CSV to export. "
            "You will be prompted to choose where to save the file."
        )
        info_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Add stretch to push everything to top
        layout.addStretch()

        self.setLayout(layout)

    def _update_date_range_from_report_type(self):
        """Update date range based on selected report type."""
        report_type = self.report_type_combo.currentText()
        today = QDate.currentDate()

        if report_type == "Monthly Summary":
            # First day of current month to today
            start_date = QDate(today.year(), today.month(), 1)
            end_date = today
        elif report_type == "Year-to-Date":
            # First day of current year to today
            start_date = QDate(today.year(), 1, 1)
            end_date = today
        elif report_type == "All Time":
            # Use a very old date to get all records (1990-01-01)
            start_date = QDate(1990, 1, 1)
            end_date = today
        else:  # Custom Date Range
            # Keep current selections
            return

        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)

    def _get_date_range(self):
        """Get selected date range as ISO format strings.

        Returns:
            tuple: (start_date_str, end_date_str) in YYYY-MM-DD format
        """
        start_date = self.start_date_edit.date().toPyDate().isoformat()
        end_date = self.end_date_edit.date().toPyDate().isoformat()
        return start_date, end_date

    def generate_pdf(self):
        """Generate PDF report and prompt user for save location."""
        try:
            start_date, end_date = self._get_date_range()

            # Generate default filename
            timestamp = datetime.now().strftime('%Y%m%d')
            default_filename = f"sales_report_{timestamp}.pdf"

            # Show file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF Report",
                default_filename,
                "PDF Files (*.pdf);;All Files (*)"
            )

            if not file_path:
                # User cancelled
                return

            # Generate PDF with selected file path
            reports.generate_pdf_report(start_date, end_date, filename=file_path)

            QMessageBox.information(
                self,
                "Success",
                f"PDF report generated successfully!\n\nSaved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate PDF report:\n{str(e)}"
            )

    def generate_csv(self):
        """Generate CSV report and prompt user for save location."""
        try:
            start_date, end_date = self._get_date_range()

            # Generate default filename
            timestamp = datetime.now().strftime('%Y%m%d')
            default_filename = f"sales_report_{timestamp}.csv"

            # Show file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV Report",
                default_filename,
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                # User cancelled
                return

            # Generate CSV with selected file path
            reports.generate_csv_report(start_date, end_date, filename=file_path)

            QMessageBox.information(
                self,
                "Success",
                f"CSV report generated successfully!\n\nSaved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate CSV report:\n{str(e)}"
            )
