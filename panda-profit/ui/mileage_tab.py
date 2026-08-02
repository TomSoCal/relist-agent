from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTableWidget, QTableWidgetItem, QDialog, QLabel,
                            QLineEdit, QSpinBox, QTextEdit, QMessageBox,
                            QDateEdit, QHeaderView, QTabWidget, QCheckBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta
import database as db
from constants import STORES


class MileageTab(QWidget):
    """Tab for tracking business mileage and computing tax deductions."""

    def __init__(self):
        super().__init__()
        self.mileage_rate = self._get_mileage_rate()
        self.init_ui()
        self.load_mileage()

    def _get_mileage_rate(self):
        """Get mileage rate from settings, default to IRS 2026 rate."""
        try:
            rate = db.get_setting('mileage_rate')
            if rate:
                return float(rate)
        except:
            pass
        return 0.67  # Default IRS rate for 2026

    def init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout()

        # Button bar
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Mileage Trip")
        add_btn.clicked.connect(self.add_trip_dialog)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_trip)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_trips)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_mileage)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Summary stats section
        stats_layout = QHBoxLayout()

        self.total_miles_label = self._create_stat_label("Total Miles (This Month)", "0")
        self.trips_count_label = self._create_stat_label("Trips (This Month)", "0")
        self.mileage_value_label = self._create_stat_label(f"Mileage Value (@ ${self.mileage_rate}/mi)", "$0.00")

        stats_layout.addWidget(self.total_miles_label)
        stats_layout.addWidget(self.trips_count_label)
        stats_layout.addWidget(self.mileage_value_label)

        layout.addLayout(stats_layout)

        # Mileage log table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Select", "Date", "Start Odometer", "End Odometer", "Miles", "Purpose", "Stores", "Notes"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)  # Checkbox column narrower

        layout.addWidget(self.table)
        self.setLayout(layout)

    def _create_stat_label(self, title, value):
        """Create a styled stat label widget."""
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))

        container_layout.addWidget(title_label)
        container_layout.addWidget(value_label)
        container.setLayout(container_layout)
        container.setStyleSheet("border-radius: 5px; padding: 10px; background-color: transparent; border: 1px solid #333333;")

        # Store labels for updating
        container.title_label = title_label
        container.value_label = value_label

        return container

    def get_month_date_range(self):
        """Get the start and end dates for the current month."""
        today = datetime.now()
        month_start = today.replace(day=1).strftime("%Y-%m-%d")
        month_end = today.strftime("%Y-%m-%d")
        return month_start, month_end

    def load_mileage(self):
        """Load and display mileage trips for the current month."""
        month_start, month_end = self.get_month_date_range()

        # Refresh mileage rate from settings
        self.mileage_rate = self._get_mileage_rate()

        # Get total mileage and trip count
        totals = db.get_total_mileage_for_period(month_start, month_end)
        total_miles = totals.get('total_miles', 0) or 0
        trip_count = totals.get('trip_count', 0) or 0
        mileage_value = total_miles * self.mileage_rate

        # Update summary labels
        self.total_miles_label.value_label.setText(f"{total_miles:.1f}")
        self.trips_count_label.value_label.setText(str(trip_count))
        self.mileage_value_label.value_label.setText(f"${mileage_value:.2f}")

        # Get and display trips in table
        trips = db.get_mileage_by_date_range(month_start, month_end)
        self.table.setRowCount(len(trips))

        for row, trip in enumerate(trips):
            # Checkbox for selection
            checkbox = QCheckBox()
            self.table.setCellWidget(row, 0, checkbox)

            self.table.setItem(row, 1, QTableWidgetItem(str(trip['trip_date'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(trip.get('odometer_start', 0) or 0)))
            self.table.setItem(row, 3, QTableWidgetItem(str(trip.get('odometer_end', 0) or 0)))
            self.table.setItem(row, 4, QTableWidgetItem(str(trip['miles'])))
            self.table.setItem(row, 5, QTableWidgetItem(trip['purpose'] or ''))
            self.table.setItem(row, 6, QTableWidgetItem(trip['stores_visited'] or ''))
            self.table.setItem(row, 7, QTableWidgetItem(trip['notes'] or ''))

            # Store trip ID for edit/delete operations
            self.table.item(row, 1).trip_id = trip['id']

    def add_trip_dialog(self):
        """Open dialog to add a new mileage trip."""
        dialog = AddMileageDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Determine which tab was used and get odometer values
                odometer_start = 0
                odometer_end = 0

                # Check which tab was active (0=direct miles, 1=odometer)
                for child in dialog.findChildren(QTabWidget):
                    if child.currentIndex() == 1:  # Odometer tab
                        odometer_start = dialog.odometer_start.value()
                        odometer_end = dialog.odometer_end.value()
                    break

                db.add_mileage_trip(
                    trip_date=dialog.trip_date.date().toString("yyyy-MM-dd"),
                    miles=dialog.miles_value,
                    odometer_start=odometer_start,
                    odometer_end=odometer_end,
                    purpose=dialog.purpose_input.text() or "sourcing",
                    stores_visited=dialog.stores_input.text(),
                    notes=dialog.notes_input.toPlainText()
                )
                self.load_mileage()
                QMessageBox.information(self, "Success", "Mileage trip added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add trip: {str(e)}")

    def delete_selected_trips(self):
        """Delete all checked mileage trips."""
        # Find all checked rows
        trip_ids = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                trip_id = self.table.item(row, 1).trip_id
                trip_ids.append(trip_id)

        if not trip_ids:
            QMessageBox.warning(self, "Error", "Please select at least one trip to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(trip_ids)} trip(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                failed = []
                for trip_id in trip_ids:
                    rows_deleted = db.delete_mileage_trip(trip_id)
                    if rows_deleted == 0:
                        failed.append(trip_id)

                if failed:
                    QMessageBox.warning(
                        self, "Partial Deletion",
                        f"Could not delete {len(failed)} trip(s). Trips from previous years cannot be deleted."
                    )
                else:
                    QMessageBox.information(self, "Success", f"{len(trip_ids)} trip(s) deleted successfully!")

                self.load_mileage()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete trips: {str(e)}")

    def edit_trip(self):
        """Edit the selected mileage trip."""
        # Try row selection first
        selected_rows = self.table.selectionModel().selectedRows()
        row = None

        if selected_rows:
            row = selected_rows[0].row()
        else:
            # If no row selected, check if only one checkbox is checked
            checked_rows = []
            for r in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(r, 0)
                if checkbox and checkbox.isChecked():
                    checked_rows.append(r)

            if len(checked_rows) == 1:
                row = checked_rows[0]
            elif len(checked_rows) > 1:
                QMessageBox.warning(self, "Error", "Please select only one trip to edit (uncheck the others).")
                return
            else:
                QMessageBox.warning(self, "Error", "Please select a trip to edit (click on a row or check a checkbox).")
                return
        if not hasattr(self.table.item(row, 1), 'trip_id'):
            QMessageBox.warning(self, "Error", "Trip ID not found. Please refresh and try again.")
            return

        trip_id = self.table.item(row, 1).trip_id

        # Get the trip data - all year data to handle any year
        try:
            # Read values directly from table cells (already loaded)
            trip_date = self.table.item(row, 1).text()
            odometer_start = int(self.table.item(row, 2).text() or 0)
            odometer_end = int(self.table.item(row, 3).text() or 0)
            miles = int(self.table.item(row, 4).text() or 0)
            purpose = self.table.item(row, 5).text()
            stores = self.table.item(row, 6).text()
            notes = self.table.item(row, 7).text()

            # Create trip dict from table data
            trip = {
                'id': trip_id,
                'trip_date': trip_date,
                'odometer_start': odometer_start,
                'odometer_end': odometer_end,
                'miles': miles,
                'purpose': purpose,
                'stores_visited': stores,
                'notes': notes
            }

            # Open edit dialog
            dialog = EditMileageDialog(trip, self)
            if dialog.exec_() == QDialog.Accepted:
                try:
                    db.update_mileage_trip(
                        trip_id,
                        trip_date=dialog.trip_date.date().toString("yyyy-MM-dd"),
                        miles=dialog.miles_value,
                        odometer_start=dialog.odometer_start.value(),
                        odometer_end=dialog.odometer_end.value(),
                        purpose=dialog.purpose_input.text() or "sourcing",
                        stores_visited=dialog.stores_input.text(),
                        notes=dialog.notes_input.toPlainText()
                    )
                    self.load_mileage()
                    QMessageBox.information(self, "Success", "Trip updated successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update trip: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open edit dialog: {str(e)}")


class AddMileageDialog(QDialog):
    """Dialog for adding a new mileage trip with two input methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Mileage Trip")
        self.setGeometry(150, 150, 550, 500)
        self.miles_value = 0  # Final miles value to store
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI with tabbed input methods."""
        layout = QVBoxLayout()

        # Trip date picker (shared)
        layout.addWidget(QLabel("Trip Date:"))
        self.trip_date = QDateEdit()
        self.trip_date.setDate(QDate.currentDate())
        self.trip_date.setCalendarPopup(True)
        layout.addWidget(self.trip_date)

        # Miles input tab widget
        tab_widget = QTabWidget()
        self.direct_miles_tab = self._create_direct_miles_tab()
        self.odometer_tab = self._create_odometer_tab()
        tab_widget.addTab(self.direct_miles_tab, "Enter Miles")
        tab_widget.addTab(self.odometer_tab, "Enter Odometer")
        layout.addWidget(tab_widget)

        # Miles driven display (updates based on current tab)
        layout.addWidget(QLabel("Miles Driven:"))
        self.miles_display = QLabel("0 miles")
        self.miles_display.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.miles_display)

        # Purpose
        layout.addWidget(QLabel("Purpose:"))
        self.purpose_input = QLineEdit()
        self.purpose_input.setText("sourcing")
        layout.addWidget(self.purpose_input)

        # Stores visited
        layout.addWidget(QLabel("Stores Visited:"))
        self.stores_input = QLineEdit()
        self.stores_input.setPlaceholderText("Goodwill, Salvation Army, etc.")
        layout.addWidget(self.stores_input)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any additional notes about the trip...")
        layout.addWidget(self.notes_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Connect value changes to update display
        tab_widget.currentChanged.connect(self._update_miles_display)

    def _create_direct_miles_tab(self):
        """Create the direct miles entry tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Enter miles driven directly:"))
        self.miles_spinner = QSpinBox()
        self.miles_spinner.setRange(0, 999)
        self.miles_spinner.setValue(0)
        self.miles_spinner.valueChanged.connect(self._update_miles_display)
        layout.addWidget(self.miles_spinner)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_odometer_tab(self):
        """Create the odometer reading entry tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Enter odometer readings to calculate miles:"))

        # Odometer start
        layout.addWidget(QLabel("Odometer Start (miles):"))
        self.odometer_start = QSpinBox()
        self.odometer_start.setRange(0, 999999)
        self.odometer_start.setValue(0)
        self.odometer_start.valueChanged.connect(self._update_miles_display)
        layout.addWidget(self.odometer_start)

        # Odometer end
        layout.addWidget(QLabel("Odometer End (miles):"))
        self.odometer_end = QSpinBox()
        self.odometer_end.setRange(0, 999999)
        self.odometer_end.setValue(0)
        self.odometer_end.valueChanged.connect(self._update_miles_display)
        layout.addWidget(self.odometer_end)

        # Error label for validation
        self.odometer_error_label = QLabel("")
        self.odometer_error_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.odometer_error_label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _update_miles_display(self):
        """Update the miles driven display based on current tab and input values."""
        # Determine which tab is active
        tab_widget = self.sender() if isinstance(self.sender(), QTabWidget) else None

        # If called from tab change, use the widget's currentIndex
        if tab_widget is None:
            # Find the tab widget
            for child in self.findChildren(QTabWidget):
                tab_widget = child
                break

        current_tab = tab_widget.currentIndex() if tab_widget else 0

        # Clear error message
        self.odometer_error_label.setText("")

        if current_tab == 0:  # Direct miles tab
            miles = self.miles_spinner.value()
            self.miles_value = miles
            self.miles_display.setText(f"{miles} miles")
        else:  # Odometer tab
            odometer_start = self.odometer_start.value()
            odometer_end = self.odometer_end.value()

            if odometer_end < odometer_start:
                self.odometer_error_label.setText("Error: End odometer must be >= Start odometer")
                self.miles_value = 0
                self.miles_display.setText("0 miles")
            else:
                miles = odometer_end - odometer_start
                self.miles_value = miles
                self.miles_display.setText(f"{miles} miles")

    def _on_save(self):
        """Validate and save the dialog."""
        # Validate that miles > 0
        if self.miles_value <= 0:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Miles driven must be greater than 0."
            )
            return

        # Validate odometer readings if in odometer tab
        tab_widget = None
        for child in self.findChildren(QTabWidget):
            tab_widget = child
            break

        if tab_widget and tab_widget.currentIndex() == 1:
            if self.odometer_end.value() < self.odometer_start.value():
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "End odometer reading must be greater than or equal to start reading."
                )
                return

        # All validation passed, accept the dialog
        self.accept()


class EditMileageDialog(QDialog):
    """Dialog for editing an existing mileage trip."""

    def __init__(self, trip, parent=None):
        super().__init__(parent)
        self.trip = trip
        self.setWindowTitle("Edit Mileage Trip")
        self.setGeometry(150, 150, 550, 500)
        self.miles_value = trip['miles']
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout()

        # Trip date picker
        layout.addWidget(QLabel("Trip Date:"))
        self.trip_date = QDateEdit()
        self.trip_date.setDate(QDate.fromString(self.trip['trip_date'], "yyyy-MM-dd"))
        self.trip_date.setCalendarPopup(True)
        layout.addWidget(self.trip_date)

        # Odometer readings
        layout.addWidget(QLabel("Odometer Start (miles):"))
        self.odometer_start = QSpinBox()
        self.odometer_start.setRange(0, 999999)
        self.odometer_start.setValue(self.trip.get('odometer_start') or 0)
        self.odometer_start.valueChanged.connect(self._update_miles_display)
        layout.addWidget(self.odometer_start)

        layout.addWidget(QLabel("Odometer End (miles):"))
        self.odometer_end = QSpinBox()
        self.odometer_end.setRange(0, 999999)
        self.odometer_end.setValue(self.trip.get('odometer_end') or 0)
        self.odometer_end.valueChanged.connect(self._update_miles_display)
        layout.addWidget(self.odometer_end)

        # Miles driven display
        layout.addWidget(QLabel("Miles Driven:"))
        self.miles_display = QLabel(f"{self.trip['miles']} miles")
        self.miles_display.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.miles_display)

        # Purpose
        layout.addWidget(QLabel("Purpose:"))
        self.purpose_input = QLineEdit()
        self.purpose_input.setText(self.trip['purpose'] or 'sourcing')
        layout.addWidget(self.purpose_input)

        # Stores visited
        layout.addWidget(QLabel("Stores Visited:"))
        self.stores_input = QLineEdit()
        self.stores_input.setText(self.trip['stores_visited'] or '')
        layout.addWidget(self.stores_input)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlainText(self.trip['notes'] or '')
        layout.addWidget(self.notes_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _update_miles_display(self):
        """Update the miles display based on odometer readings."""
        odometer_start = self.odometer_start.value()
        odometer_end = self.odometer_end.value()

        if odometer_end >= odometer_start:
            miles = odometer_end - odometer_start
            self.miles_value = miles
            self.miles_display.setText(f"{miles} miles")
        else:
            self.miles_display.setText("Invalid: End must be >= Start")

    def _on_save(self):
        """Validate and save the dialog."""
        if self.odometer_end.value() < self.odometer_start.value():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "End odometer reading must be greater than or equal to start reading."
            )
            return

        self.accept()
