from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QFormLayout, QDoubleSpinBox,
    QMessageBox, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.repository import CartonRepository

class CartonWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self.selected_carton_id = None
        self._build_ui()
        self.load_cartons()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column - Carton List Table
        left_layout = QVBoxLayout()
        title_lbl = QLabel("Carton Profiles Catalog")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1A365D;")
        left_layout.addWidget(title_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Dimensions (LxWxH)", "Empty Wt.", "Max Wt. Capacity", "Unit Cost"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)

        main_layout.addLayout(left_layout, stretch=2)

        # Right Column - CRUD Editor Form
        right_layout = QVBoxLayout()
        form_group = QGroupBox("Carton Specification details")
        form_layout = QFormLayout(form_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Carton Box Name (e.g. Medium Box)")

        self.len_input = QDoubleSpinBox()
        self.len_input.setRange(1.0, 10000.0)
        self.len_input.setValue(300.0)
        self.len_input.setSuffix(" mm")

        self.wid_input = QDoubleSpinBox()
        self.wid_input.setRange(1.0, 10000.0)
        self.wid_input.setValue(200.0)
        self.wid_input.setSuffix(" mm")

        self.hei_input = QDoubleSpinBox()
        self.hei_input.setRange(1.0, 10000.0)
        self.hei_input.setValue(200.0)
        self.hei_input.setSuffix(" mm")

        self.empty_weight_input = QDoubleSpinBox()
        self.empty_weight_input.setRange(0.0, 100.0)
        self.empty_weight_input.setValue(0.2)
        self.empty_weight_input.setSuffix(" kg")

        self.max_weight_input = QDoubleSpinBox()
        self.max_weight_input.setRange(0.1, 10000.0)
        self.max_weight_input.setValue(20.0)
        self.max_weight_input.setSuffix(" kg capacity")

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0.0, 1000.0)
        self.cost_input.setValue(1.50)
        self.cost_input.setPrefix("$ ")

        form_layout.addRow("Box Profile Name *:", self.name_input)
        form_layout.addRow("Length (X) *:", self.len_input)
        form_layout.addRow("Width (Y) *:", self.wid_input)
        form_layout.addRow("Height (Z) *:", self.hei_input)
        form_layout.addRow("Empty Weight (Tare):", self.empty_weight_input)
        form_layout.addRow("Max Load Weight *:", self.max_weight_input)
        form_layout.addRow("Unit Purchase Cost:", self.cost_input)

        right_layout.addWidget(form_group)

        # Editor Operations Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.add_carton)
        self.add_btn.setStyleSheet("background-color: #319795; color: white; padding: 8px;")
        
        self.update_btn = QPushButton("Save Changes")
        self.update_btn.clicked.connect(self.update_carton)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 8px;")
        
        self.delete_btn = QPushButton("Delete Box")
        self.delete_btn.clicked.connect(self.delete_carton)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #E53E3E; color: white; padding: 8px;")

        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setStyleSheet("background-color: #718096; color: white; padding: 8px;")

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        main_layout.addLayout(right_layout, stretch=1)

    def load_cartons(self):
        self.table.setRowCount(0)
        cartons = CartonRepository.get_all(self.db)

        for row_idx, c in enumerate(cartons):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(c.name))
            
            dims_str = f"{c.length}x{c.width}x{c.height} mm"
            self.table.setItem(row_idx, 2, QTableWidgetItem(dims_str))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{c.empty_weight} kg"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{c.max_weight} kg"))
            self.table.setItem(row_idx, 5, QTableWidgetItem(f"${c.cost:.2f}"))

    def on_selection_changed(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_form()
            return

        row = selected_ranges[0].topRow()
        carton_id = int(self.table.item(row, 0).text())
        c = CartonRepository.get_by_id(self.db, carton_id)
        if not c:
            return

        self.selected_carton_id = c.id
        self.name_input.setText(c.name)
        self.len_input.setValue(c.length)
        self.wid_input.setValue(c.width)
        self.hei_input.setValue(c.height)
        self.empty_weight_input.setValue(c.empty_weight)
        self.max_weight_input.setValue(c.max_weight)
        self.cost_input.setValue(c.cost)

        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def clear_form(self):
        self.selected_carton_id = None
        self.name_input.setText("")
        self.len_input.setValue(300.0)
        self.wid_input.setValue(200.0)
        self.hei_input.setValue(200.0)
        self.empty_weight_input.setValue(0.2)
        self.max_weight_input.setValue(20.0)
        self.cost_input.setValue(1.50)

        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def _get_form_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "length": self.len_input.value(),
            "width": self.wid_input.value(),
            "height": self.hei_input.value(),
            "empty_weight": self.empty_weight_input.value(),
            "max_weight": self.max_weight_input.value(),
            "cost": self.cost_input.value()
        }

    def add_carton(self):
        data = self._get_form_data()
        if not data["name"]:
            QMessageBox.warning(self, "Input Error", "Box profile name is required!")
            return

        # Check unique Name
        # Check from all list
        cartons = CartonRepository.get_all(self.db)
        if any(c.name.lower() == data["name"].lower() for c in cartons):
            QMessageBox.warning(self, "Input Error", f"Box name '{data['name']}' already exists.")
            return

        CartonRepository.create(self.db, **data)
        self.load_cartons()
        self.clear_form()

    def update_carton(self):
        if not self.selected_carton_id:
            return
        data = self._get_form_data()
        if not data["name"]:
            QMessageBox.warning(self, "Input Error", "Box profile name is required!")
            return

        CartonRepository.update(self.db, self.selected_carton_id, data)
        self.load_cartons()
        self.clear_form()

    def delete_carton(self):
        if not self.selected_carton_id:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this carton profile?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            CartonRepository.delete(self.db, self.selected_carton_id)
            self.load_cartons()
            self.clear_form()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
