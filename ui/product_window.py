import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QFormLayout, QCheckBox, QDoubleSpinBox,
    QMessageBox, QFileDialog, QHeaderView, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.repository import ProductRepository

class ProductWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self.selected_product_id = None
        self._build_ui()
        self.load_products()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column - Product Table and Search
        left_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_lbl = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by SKU, Name, or Category...")
        self.search_input.textChanged.connect(self.load_products)
        search_layout.addWidget(search_lbl)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "SKU", "Name", "Dimensions (LxWxH)", "Weight (kg)", "Fragile", "Stackable"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)

        # Excel / CSV Import & Template Buttons
        csv_layout = QHBoxLayout()
        
        import_btn = QPushButton("📥 Import Products (Excel / CSV)")
        import_btn.clicked.connect(self.import_excel_or_csv)
        import_btn.setStyleSheet("background-color: #2B6CB0; color: white; font-weight: bold; padding: 8px;")
        
        template_btn = QPushButton("📄 Download Sample Template")
        template_btn.clicked.connect(self.download_sample_template)
        template_btn.setStyleSheet("background-color: #2D3748; color: white; padding: 8px;")
        
        csv_layout.addWidget(import_btn)
        csv_layout.addWidget(template_btn)
        left_layout.addLayout(csv_layout)

        main_layout.addLayout(left_layout, stretch=2)

        # Right Column - CRUD Editor Form
        right_layout = QVBoxLayout()
        form_group = QGroupBox("Product Editor details")
        form_layout = QFormLayout(form_group)

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Unique SKU ID (e.g., A101)")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Display Name")

        self.len_input = QDoubleSpinBox()
        self.len_input.setRange(1.0, 5000.0)
        self.len_input.setValue(100.0)
        self.len_input.setSuffix(" mm")

        self.wid_input = QDoubleSpinBox()
        self.wid_input.setRange(1.0, 5000.0)
        self.wid_input.setValue(100.0)
        self.wid_input.setSuffix(" mm")

        self.hei_input = QDoubleSpinBox()
        self.hei_input.setRange(1.0, 5000.0)
        self.hei_input.setValue(100.0)
        self.hei_input.setSuffix(" mm")

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.01, 1000.0)
        self.weight_input.setValue(1.0)
        self.weight_input.setSuffix(" kg")

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Optional barcode scanner digits")

        self.fragile_check = QCheckBox("Fragile (No vertical pressure)")
        self.stackable_check = QCheckBox("Stackable (Allow items on top)")
        self.stackable_check.setChecked(True)

        self.max_stack_input = QDoubleSpinBox()
        self.max_stack_input.setRange(0.0, 9999.0)
        self.max_stack_input.setValue(50.0)
        self.max_stack_input.setSuffix(" kg limit")

        self.rotations_combo = QComboBox()
        self.rotations_combo.addItems(["XYZ (All Axes Allowed)", "XY (No Tipping)", "Z (This Side Up Only)"])

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category (e.g. Electronics)")

        form_layout.addRow("SKU ID *:", self.sku_input)
        form_layout.addRow("Name *:", self.name_input)
        form_layout.addRow("Length (X) *:", self.len_input)
        form_layout.addRow("Width (Y) *:", self.wid_input)
        form_layout.addRow("Height (Z) *:", self.hei_input)
        form_layout.addRow("Weight *:", self.weight_input)
        form_layout.addRow("Barcode:", self.barcode_input)
        form_layout.addRow("Category:", self.category_input)
        form_layout.addRow("Rotation Rules:", self.rotations_combo)
        form_layout.addRow(self.fragile_check)
        form_layout.addRow(self.stackable_check)
        form_layout.addRow("Max Stack Weight:", self.max_stack_input)

        right_layout.addWidget(form_group)

        # Editor Operations Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.add_product)
        self.add_btn.setStyleSheet("background-color: #319795; color: white; padding: 8px;")
        
        self.update_btn = QPushButton("Save Changes")
        self.update_btn.clicked.connect(self.update_product)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 8px;")
        
        self.delete_btn = QPushButton("Delete Product")
        self.delete_btn.clicked.connect(self.delete_product)
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

    def load_products(self):
        """Loads and filters products inside table."""
        self.table.setRowCount(0)
        search_text = self.search_input.text().strip()
        products = ProductRepository.get_all(self.db, search_text if search_text else None)

        for row_idx, p in enumerate(products):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(p.sku))
            self.table.setItem(row_idx, 2, QTableWidgetItem(p.name))
            
            dims_str = f"{p.length}x{p.width}x{p.height} mm"
            self.table.setItem(row_idx, 3, QTableWidgetItem(dims_str))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{p.weight} kg"))
            self.table.setItem(row_idx, 5, QTableWidgetItem("Yes" if p.fragile else "No"))
            self.table.setItem(row_idx, 6, QTableWidgetItem("Yes" if p.stackable else "No"))

    def on_selection_changed(self):
        """Fills edit form with selected item's values."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_form()
            return

        row = selected_ranges[0].topRow()
        product_id = int(self.table.item(row, 0).text())
        p = ProductRepository.get_by_id(self.db, product_id)
        if not p:
            return

        self.selected_product_id = p.id
        self.sku_input.setText(p.sku)
        self.sku_input.setEnabled(False) # Prevent modifying SKU key
        self.name_input.setText(p.name)
        self.len_input.setValue(p.length)
        self.wid_input.setValue(p.width)
        self.hei_input.setValue(p.height)
        self.weight_input.setValue(p.weight)
        self.barcode_input.setText(p.barcode or "")
        self.category_input.setText(p.category or "")
        self.fragile_check.setChecked(p.fragile)
        self.stackable_check.setChecked(p.stackable)
        self.max_stack_input.setValue(p.max_stack_weight)

        # Set allowed rotations mapping
        if p.allowed_rotations == "XYZ":
            self.rotations_combo.setCurrentIndex(0)
        elif p.allowed_rotations == "XY":
            self.rotations_combo.setCurrentIndex(1)
        else:
            self.rotations_combo.setCurrentIndex(2)

        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def clear_form(self):
        self.selected_product_id = None
        self.sku_input.setText("")
        self.sku_input.setEnabled(True)
        self.name_input.setText("")
        self.len_input.setValue(100.0)
        self.wid_input.setValue(100.0)
        self.hei_input.setValue(100.0)
        self.weight_input.setValue(1.0)
        self.barcode_input.setText("")
        self.category_input.setText("")
        self.fragile_check.setChecked(False)
        self.stackable_check.setChecked(True)
        self.max_stack_input.setValue(50.0)
        self.rotations_combo.setCurrentIndex(0)

        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def _get_form_data(self) -> dict:
        """Parses current form inputs."""
        rot_sel = self.rotations_combo.currentIndex()
        rot_val = "XYZ"
        if rot_sel == 1:
            rot_val = "XY"
        elif rot_sel == 2:
            rot_val = "Z"

        return {
            "sku": self.sku_input.text().strip(),
            "name": self.name_input.text().strip(),
            "length": self.len_input.value(),
            "width": self.wid_input.value(),
            "height": self.hei_input.value(),
            "weight": self.weight_input.value(),
            "barcode": self.barcode_input.text().strip() or None,
            "category": self.category_input.text().strip() or None,
            "fragile": self.fragile_check.isChecked(),
            "stackable": self.stackable_check.isChecked(),
            "max_stack_weight": self.max_stack_input.value(),
            "allowed_rotations": rot_val
        }

    def add_product(self):
        data = self._get_form_data()
        if not data["sku"] or not data["name"]:
            QMessageBox.warning(self, "Input Error", "SKU ID and Name are required fields!")
            return

        # Check unique SKU
        if ProductRepository.get_by_sku(self.db, data["sku"]):
            QMessageBox.warning(self, "Input Error", f"SKU '{data['sku']}' already exists in database.")
            return

        ProductRepository.create(self.db, **data)
        self.load_products()
        self.clear_form()

    def update_product(self):
        if not self.selected_product_id:
            return
        data = self._get_form_data()
        if not data["name"]:
            QMessageBox.warning(self, "Input Error", "Name is a required field!")
            return

        # SKU is unmodifiable on edit
        del data["sku"]

        ProductRepository.update(self.db, self.selected_product_id, data)
        self.load_products()
        self.clear_form()

    def delete_product(self):
        if not self.selected_product_id:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this product? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            ProductRepository.delete(self.db, self.selected_product_id)
            self.load_products()
            self.clear_form()

    def import_excel_or_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Product Catalog (Excel / CSV)", "", 
            "Excel & CSV Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            res = ProductRepository.import_excel_or_csv(self.db, file_path)
            err_msg = ""
            if res["errors"]:
                err_msg = "\n\nWarnings/Errors:\n" + "\n".join(res["errors"][:5])

            QMessageBox.information(
                self, "Import Completed", 
                f"<b>Product Catalog Import Summary:</b><br/><br/>"
                f"• <b>New Products Added:</b> {res['imported']}<br/>"
                f"• <b>Existing Products Updated:</b> {res['updated']}<br/>"
                f"• <b>Total Processed:</b> {res['total']}"
                f"{err_msg}"
            )
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")

    def download_sample_template(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Sample Product Catalog Template", "sample_product_catalog.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            from database.excel_template import generate_sample_excel_template, generate_sample_csv_template
            if file_path.lower().endswith(".csv"):
                generate_sample_csv_template(file_path)
            else:
                if not file_path.lower().endswith(".xlsx"):
                    file_path += ".xlsx"
                generate_sample_excel_template(file_path)

            QMessageBox.information(
                self, "Template Saved", 
                f"Sample Excel template successfully saved!\n\nLocation: {file_path}\n\n"
                "You can now open this file in Excel, add your products, and click 'Import Products'."
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save sample template: {e}")

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
