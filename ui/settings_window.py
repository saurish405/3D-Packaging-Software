import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QFormLayout, QDoubleSpinBox,
    QSpinBox, QMessageBox, QHeaderView, QGroupBox
)
from database.database import SessionLocal
from database.repository import CourierRepository

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")

def load_settings() -> dict:
    """Loads settings from a local JSON file with robust default fallbacks."""
    defaults = {
        "top_clearance": 20.0,
        "cell_size": 10.0,
        "height_tolerance": 5.0,
        "required_support": 0.70,
        "max_steps": 15000
    }
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return defaults

def save_settings(settings: dict):
    """Saves settings to a local JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self.selected_courier_id = None
        self._build_ui()
        self.load_couriers()
        self.load_general_settings()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column - General Solver Configuration
        left_layout = QVBoxLayout()
        config_group = QGroupBox("Optimization Solver Defaults")
        config_layout = QFormLayout(config_group)

        self.clearance_input = QDoubleSpinBox()
        self.clearance_input.setRange(0.0, 500.0)
        self.clearance_input.setSuffix(" mm")
        
        self.cell_input = QDoubleSpinBox()
        self.cell_input.setRange(1.0, 100.0)
        self.cell_input.setSuffix(" mm (Resolution)")

        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setRange(0.0, 100.0)
        self.tolerance_input.setSuffix(" mm")

        self.support_input = QDoubleSpinBox()
        self.support_input.setRange(0.0, 1.0)
        self.support_input.setSingleStep(0.05)
        self.support_input.setSuffix(" ratio (e.g. 0.70 = 70%)")

        self.steps_input = QSpinBox()
        self.steps_input.setRange(500, 100000)
        self.steps_input.setSingleStep(1000)

        config_layout.addRow("Cushioning Top Clearance:", self.clearance_input)
        config_layout.addRow("Solver Grid Cell Size:", self.cell_input)
        config_layout.addRow("Layer Height Tolerance:", self.tolerance_input)
        config_layout.addRow("Minimum Stability Support:", self.support_input)
        config_layout.addRow("Max Backtracking Steps:", self.steps_input)

        save_config_btn = QPushButton("Save Defaults")
        save_config_btn.clicked.connect(self.save_general_settings)
        save_config_btn.setStyleSheet("background-color: #319795; color: white; font-weight: bold; padding: 10px;")
        config_layout.addRow("", save_config_btn)

        left_layout.addWidget(config_group)
        left_layout.addStretch()
        main_layout.addLayout(left_layout, stretch=1)

        # Right Column - Courier Pricing CRUD Table
        right_layout = QVBoxLayout()
        
        courier_group = QGroupBox("Courier Pricing & Factors")
        courier_main = QHBoxLayout(courier_group)

        # Courier List Table
        c_list_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Vol. Factor", "Rate/kg", "Min Charge"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        c_list_layout.addWidget(self.table)
        courier_main.addLayout(c_list_layout, stretch=2)

        # Courier Form Editor
        c_edit_layout = QVBoxLayout()
        c_form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. DHL Express")
        
        self.factor_input = QDoubleSpinBox()
        self.factor_input.setRange(1000.0, 10000.0)
        self.factor_input.setValue(5000.0)
        self.factor_input.setDecimals(1)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.0, 1000.0)
        self.rate_input.setValue(2.50)
        self.rate_input.setPrefix("$ ")

        self.min_charge_input = QDoubleSpinBox()
        self.min_charge_input.setRange(0.0, 1000.0)
        self.min_charge_input.setValue(10.00)
        self.min_charge_input.setPrefix("$ ")

        c_form.addRow("Courier Name *:", self.name_input)
        c_form.addRow("Volumetric Factor *:", self.factor_input)
        c_form.addRow("Rate per kg *:", self.rate_input)
        c_form.addRow("Minimum Charge:", self.min_charge_input)
        c_edit_layout.addLayout(c_form)

        # Courier Actions
        c_btns = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_courier)
        self.add_btn.setStyleSheet("background-color: #319795; color: white;")
        
        self.update_btn = QPushButton("Save")
        self.update_btn.clicked.connect(self.update_courier)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("background-color: #3182CE; color: white;")

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_courier)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #E53E3E; color: white;")

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_courier_form)
        self.clear_btn.setStyleSheet("background-color: #718096; color: white;")

        c_btns.addWidget(self.add_btn)
        c_btns.addWidget(self.update_btn)
        c_btns.addWidget(self.delete_btn)
        c_btns.addWidget(self.clear_btn)
        c_edit_layout.addLayout(c_btns)
        c_edit_layout.addStretch()

        courier_main.addLayout(c_edit_layout, stretch=1)
        right_layout.addWidget(courier_group)
        
        main_layout.addLayout(right_layout, stretch=2)

    # General config helpers
    def load_general_settings(self):
        settings = load_settings()
        self.clearance_input.setValue(settings["top_clearance"])
        self.cell_input.setValue(settings["cell_size"])
        self.tolerance_input.setValue(settings["height_tolerance"])
        self.support_input.setValue(settings["required_support"])
        self.steps_input.setValue(settings["max_steps"])

    def save_general_settings(self):
        settings = {
            "top_clearance": self.clearance_input.value(),
            "cell_size": self.cell_input.value(),
            "height_tolerance": self.tolerance_input.value(),
            "required_support": self.support_input.value(),
            "max_steps": self.steps_input.value()
        }
        save_settings(settings)
        QMessageBox.information(self, "Settings Saved", "Solver default configurations have been saved successfully!")

    # Courier DB helpers
    def load_couriers(self):
        self.table.setRowCount(0)
        couriers = CourierRepository.get_all(self.db)
        for row_idx, c in enumerate(couriers):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(c.name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(c.volumetric_factor)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"${c.rate_per_kg:.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"${c.minimum_charge:.2f}"))

    def on_selection_changed(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_courier_form()
            return

        row = selected_ranges[0].topRow()
        courier_id = int(self.table.item(row, 0).text())
        c = CourierRepository.get_by_id(self.db, courier_id)
        if not c:
            return

        self.selected_courier_id = c.id
        self.name_input.setText(c.name)
        self.factor_input.setValue(c.volumetric_factor)
        self.rate_input.setValue(c.rate_per_kg)
        self.min_charge_input.setValue(c.minimum_charge)

        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def clear_courier_form(self):
        self.selected_courier_id = None
        self.name_input.setText("")
        self.factor_input.setValue(5000.0)
        self.rate_input.setValue(2.50)
        self.min_charge_input.setValue(10.00)

        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def add_courier(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Courier name is required!")
            return

        # Check unique
        couriers = CourierRepository.get_all(self.db)
        if any(c.name.lower() == name.lower() for c in couriers):
            QMessageBox.warning(self, "Input Error", f"Courier name '{name}' already exists.")
            return

        CourierRepository.create(
            self.db,
            name=name,
            volumetric_factor=self.factor_input.value(),
            rate_per_kg=self.rate_input.value(),
            minimum_charge=self.min_charge_input.value()
        )
        self.load_couriers()
        self.clear_courier_form()

    def update_courier(self):
        if not self.selected_courier_id:
            return
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Courier name is required!")
            return

        CourierRepository.update(
            self.db,
            self.selected_courier_id,
            {
                "name": name,
                "volumetric_factor": self.factor_input.value(),
                "rate_per_kg": self.rate_input.value(),
                "minimum_charge": self.min_charge_input.value()
            }
        )
        self.load_couriers()
        self.clear_courier_form()

    def delete_courier(self):
        if not self.selected_courier_id:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this courier profile?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            CourierRepository.delete(self.db, self.selected_courier_id)
            self.load_couriers()
            self.clear_courier_form()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
