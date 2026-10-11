import os
import json
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QFormLayout, QDoubleSpinBox,
    QMessageBox, QHeaderView, QGroupBox, QSpinBox, QTabWidget, QSlider
)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import Product, Carton, Courier, Job
from database.repository import ProductRepository, CartonRepository, CourierRepository, JobRepository
from ui.settings_window import load_settings
from optimizer.python.optimizer import PackageOptimizer
from optimizer.python.carton_selector import CartonSelector
from visualization.layer_renderer import Layer2DWidget
from visualization.renderer3d import Viewer3DWidget, PYVISTA_AVAILABLE
from reports.pdf import generate_pdf_report

logger = logging.getLogger("OptimizerWindow")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class OptimizerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self.optimizer = PackageOptimizer()
        self.selector = CartonSelector()
        
        self.selected_products_to_pack = {}  # {sku: qty}
        self.last_layout_result = None
        self.last_packed_carton = None

        self._build_ui()
        self.load_catalogs()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column - Inputs and Configurations (1/3 width)
        left_layout = QVBoxLayout()

        # 1. Mode Selector
        mode_group = QGroupBox("Optimization Mode")
        mode_lay = QFormLayout(mode_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Mode A: Optimize Existing Carton",
            "Mode B: Recommend Best Carton",
            "Mode C: What Fits? (Max Capacity)"
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_lay.addRow("Select Mode:", self.mode_combo)
        left_layout.addWidget(mode_group)

        # 2. Add Products Form
        prod_group = QGroupBox("Add Products to Pack")
        prod_lay = QFormLayout(prod_group)
        self.product_combo = QComboBox()
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        self.qty_input.setValue(1)
        
        add_prod_btn = QPushButton("Add to list")
        add_prod_btn.clicked.connect(self.add_product_to_packing_list)
        add_prod_btn.setStyleSheet("background-color: #319795; color: white;")
        
        prod_lay.addRow("Select SKU:", self.product_combo)
        prod_lay.addRow("Quantity:", self.qty_input)
        prod_lay.addRow("", add_prod_btn)
        left_layout.addWidget(prod_group)

        # 3. Selected Products Table
        self.list_table = QTableWidget()
        self.list_table.setColumnCount(3)
        self.list_table.setHorizontalHeaderLabels(["SKU", "Qty", "Action"])
        self.list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.list_table.setFixedHeight(150)
        left_layout.addWidget(self.list_table)

        # 4. Carton Selection (Hidden or modified depending on mode)
        self.carton_group = QGroupBox("Carton Container Specifications")
        self.carton_lay = QFormLayout(self.carton_group)
        self.carton_combo = QComboBox()
        self.carton_combo.currentIndexChanged.connect(self.on_carton_changed)
        
        self.carton_l = QDoubleSpinBox()
        self.carton_l.setRange(10.0, 5000.0)
        self.carton_l.setSuffix(" mm")
        self.carton_w = QDoubleSpinBox()
        self.carton_w.setRange(10.0, 5000.0)
        self.carton_w.setSuffix(" mm")
        self.carton_h = QDoubleSpinBox()
        self.carton_h.setRange(10.0, 5000.0)
        self.carton_h.setSuffix(" mm")
        
        self.carton_max_w = QDoubleSpinBox()
        self.carton_max_w.setRange(0.1, 5000.0)
        self.carton_max_w.setSuffix(" kg")

        self.carton_lay.addRow("Select Box Preset:", self.carton_combo)
        self.carton_lay.addRow("Length (X) *:", self.carton_l)
        self.carton_lay.addRow("Width (Y) *:", self.carton_w)
        self.carton_lay.addRow("Height (Z) *:", self.carton_h)
        self.carton_lay.addRow("Weight Capacity:", self.carton_max_w)
        left_layout.addWidget(self.carton_group)

        # 5. Shipping Courier Selector
        courier_group = QGroupBox("Courier Shipping Profile")
        courier_lay = QFormLayout(courier_group)
        self.courier_combo = QComboBox()
        courier_lay.addRow("Select Courier:", self.courier_combo)
        left_layout.addWidget(courier_group)

        # 6. Action Button
        self.run_btn = QPushButton("Calculate Optimization")
        self.run_btn.clicked.connect(self.run_optimization)
        self.run_btn.setStyleSheet("background-color: #3182CE; color: white; font-weight: bold; padding: 12px; font-size: 13px;")
        left_layout.addWidget(self.run_btn)
        
        left_layout.addStretch()
        main_layout.addLayout(left_layout, stretch=1)

        # Right Column - Output Visualization & Results Tabs (2/3 width)
        right_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab 1: Layout Instruction View (2D canvas + step selector)
        self.tab_2d = QWidget()
        lay_2d_layout = QVBoxLayout(self.tab_2d)
        
        step_control_layout = QHBoxLayout()
        step_control_layout.addWidget(QLabel("Select Packing Step (Layer):"))
        self.layer_selector = QComboBox()
        self.layer_selector.currentIndexChanged.connect(self.on_layer_selection_changed)
        step_control_layout.addWidget(self.layer_selector)
        
        self.layer_details_lbl = QLabel("No steps compiled.")
        self.layer_details_lbl.setStyleSheet("color: #4A5568; font-weight: bold;")
        step_control_layout.addWidget(self.layer_details_lbl)
        step_control_layout.addStretch()
        
        lay_2d_layout.addLayout(step_control_layout)
        
        self.canvas_2d = Layer2DWidget()
        lay_2d_layout.addWidget(self.canvas_2d, stretch=1)
        
        self.tabs.addTab(self.tab_2d, "2D Packing Instructions")

        # Tab 2: 3D interactive viewer
        self.tab_3d = QWidget()
        lay_3d_layout = QVBoxLayout(self.tab_3d)
        
        # 3D Visual controls
        visual_controls = QHBoxLayout()
        visual_controls.addWidget(QLabel("Exploded view factor:"))
        self.exploded_slider = QSlider(Qt.Horizontal)
        self.exploded_slider.setRange(0, 100) # maps to 0.0 to 1.0
        self.exploded_slider.setValue(0)
        self.exploded_slider.valueChanged.connect(self.on_3d_render_params_changed)
        self.exploded_slider.setFixedWidth(150)
        visual_controls.addWidget(self.exploded_slider)
        
        visual_controls.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100) # maps to 0.1 to 1.0
        self.opacity_slider.setValue(80)
        self.opacity_slider.valueChanged.connect(self.on_3d_render_params_changed)
        self.opacity_slider.setFixedWidth(150)
        visual_controls.addWidget(self.opacity_slider)
        visual_controls.addStretch()
        lay_3d_layout.addLayout(visual_controls)

        self.canvas_3d = Viewer3DWidget()
        lay_3d_layout.addWidget(self.canvas_3d, stretch=1)
        self.tabs.addTab(self.tab_3d, "3D Container layout")

        # Tab 3: Mode B recommendations grid
        self.tab_rec = QTableWidget()
        self.tab_rec.setColumnCount(6)
        self.tab_rec.setHorizontalHeaderLabels([
            "Carton Name", "Fit Ratio", "Space Util.", "Packed/Wasted Qtys", "Shipping Cost", "Total Cost"
        ])
        self.tab_rec.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_rec.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab_rec.setSelectionMode(QTableWidget.SingleSelection)
        self.tab_rec.doubleClicked.connect(self.view_recommended_layout)
        self.tabs.addTab(self.tab_rec, "Box Recommendations (Mode B)")

        # Tab 4: Summary Statistics
        self.tab_summary = QWidget()
        summary_lay = QVBoxLayout(self.tab_summary)
        
        # Stats Details Panel
        self.stats_group = QGroupBox("Optimization Metrics Summary")
        self.stats_form = QFormLayout(self.stats_group)
        self.stats_form.setSpacing(10)
        
        self.lbl_util = QLabel("-")
        self.lbl_efficiency = QLabel("-")
        self.lbl_stability = QLabel("-")
        self.lbl_cog = QLabel("-")
        self.lbl_weight_breakdown = QLabel("-")
        self.lbl_chargeable = QLabel("-")
        self.lbl_courier_charge = QLabel("-")
        self.lbl_packing_time = QLabel("-")
        
        self.stats_form.addRow("Space Volume Utilization:", self.lbl_util)
        self.stats_form.addRow("Overall Packing Efficiency:", self.lbl_efficiency)
        self.stats_form.addRow("Structural Stability Score:", self.lbl_stability)
        self.stats_form.addRow("Center of Gravity horizontal score:", self.lbl_cog)
        self.stats_form.addRow("Tare/Net weights breakdown:", self.lbl_weight_breakdown)
        self.stats_form.addRow("Chargeable shipping weight:", self.lbl_chargeable)
        self.stats_form.addRow("Est. Courier fee quote:", self.lbl_courier_charge)
        self.stats_form.addRow("Estimated Packing duration:", self.lbl_packing_time)
        summary_lay.addWidget(self.stats_group)
        
        # Report generator triggers
        self.print_slip_btn = QPushButton("Save Job & Export PDF Packing Slip")
        self.print_slip_btn.clicked.connect(self.save_and_print_pdf_slip)
        self.print_slip_btn.setEnabled(False)
        self.print_slip_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 12px; font-weight: bold; font-size: 13px;")
        summary_lay.addWidget(self.print_slip_btn)
        summary_lay.addStretch()
        self.tabs.addTab(self.tab_summary, "Metrics Summary")

        right_layout.addWidget(self.tabs)
        main_layout.addLayout(right_layout, stretch=2)

    def load_catalogs(self):
        """Loads items in combos."""
        try:
            # 1. Products
            products = ProductRepository.get_all(self.db)
            self.product_combo.clear()
            for p in products:
                self.product_combo.addItem(f"{p.name} ({p.sku})", p.sku)

            # 2. Cartons
            cartons = CartonRepository.get_all(self.db)
            self.carton_combo.clear()
            for c in cartons:
                self.carton_combo.addItem(c.name, c.id)

            # 3. Couriers
            couriers = CourierRepository.get_all(self.db)
            self.courier_combo.clear()
            self.courier_combo.addItem("None (No cost calculations)", None)
            for c in couriers:
                self.courier_combo.addItem(f"{c.name} (Rate: ${c.rate_per_kg:.2f}/kg)", c.id)
        except Exception as e:
            logger.error(f"Error loading catalogs: {e}")

    def on_mode_changed(self, idx):
        """Modifies enabled views depending on mode selections."""
        # Index 0: Mode A
        # Index 1: Mode B (Recommend Carton, disable manual Carton inputs)
        # Index 2: Mode C (What Fits, single product only)
        if idx == 0:
            self.carton_group.setEnabled(True)
            self.tabs.setTabEnabled(0, True)
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabEnabled(2, False)
            self.tabs.setCurrentIndex(0)
        elif idx == 1:
            self.carton_group.setEnabled(False)
            self.tabs.setTabEnabled(0, False)
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabEnabled(2, True)
            self.tabs.setCurrentIndex(2)
        elif idx == 2:
            self.carton_group.setEnabled(True)
            self.tabs.setTabEnabled(0, True)
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabEnabled(2, False)
            self.tabs.setCurrentIndex(0)

    def on_carton_changed(self, idx):
        if idx < 0: return
        carton_id = self.carton_combo.currentData()
        c = CartonRepository.get_by_id(self.db, carton_id)
        if c:
            self.carton_l.setValue(c.length)
            self.carton_w.setValue(c.width)
            self.carton_h.setValue(c.height)
            self.carton_max_w.setValue(c.max_weight)

    def add_product_to_packing_list(self):
        sku = self.product_combo.currentData()
        if not sku:
            return
        qty = self.qty_input.value()

        # If Mode C, limit to exactly 1 product type in list
        if self.mode_combo.currentIndex() == 2:
            self.selected_products_to_pack.clear()

        self.selected_products_to_pack[sku] = self.selected_products_to_pack.get(sku, 0) + qty
        self.refresh_selected_table()

    def remove_product_from_packing_list(self, sku):
        if sku in self.selected_products_to_pack:
            del self.selected_products_to_pack[sku]
            self.refresh_selected_table()

    def refresh_selected_table(self):
        self.list_table.setRowCount(0)
        for row_idx, (sku, qty) in enumerate(self.selected_products_to_pack.items()):
            self.list_table.insertRow(row_idx)
            self.list_table.setItem(row_idx, 0, QTableWidgetItem(sku))
            self.list_table.setItem(row_idx, 1, QTableWidgetItem(str(qty)))
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked=False, s=sku: self.remove_product_from_packing_list(s))
            remove_btn.setStyleSheet("background-color: #E53E3E; color: white; padding: 2px;")
            self.list_table.setCellWidget(row_idx, 2, remove_btn)

    def run_optimization(self):
        if not self.selected_products_to_pack:
            QMessageBox.warning(self, "Configuration Error", "Please add at least one product to the packing list.")
            return

        mode_idx = self.mode_combo.currentIndex()
        settings = load_settings()
        
        # Load products details
        p_skus = list(self.selected_products_to_pack.keys())
        p_qtys = list(self.selected_products_to_pack.values())
        
        products_models = self.db.query(Product).filter(Product.sku.in_(p_skus)).all()
        products_list = [p.to_dict() for p in products_models]
        
        # Map quantities in the same order as products_list
        quantities = []
        for p in products_list:
            quantities.append(self.selected_products_to_pack[p["sku"]])

        # Load Courier profile
        courier_id = self.courier_combo.currentData()
        courier_dict = None
        if courier_id:
            c_model = CourierRepository.get_by_id(self.db, courier_id)
            if c_model:
                courier_dict = c_model.to_dict()

        if mode_idx == 0:
            # Mode A: Optimize Existing Carton
            carton_info = {
                "length": self.carton_l.value(),
                "width": self.carton_w.value(),
                "height": self.carton_h.value(),
                "max_weight": self.carton_max_w.value(),
                "empty_weight": 0.2, # default fallback
                "cost": 1.50
            }
            carton_preset_id = self.carton_combo.currentData()
            if carton_preset_id:
                c_model = CartonRepository.get_by_id(self.db, carton_preset_id)
                if c_model:
                    carton_info = c_model.to_dict()

            self._execute_mode_a(carton_info, products_list, quantities, courier_dict, settings)

        elif mode_idx == 1:
            # Mode B: Recommend Carton
            self._execute_mode_b(products_list, quantities, courier_dict, settings)

        elif mode_idx == 2:
            # Mode C: What Fits
            carton_preset_id = self.carton_combo.currentData()
            if not carton_preset_id:
                QMessageBox.warning(self, "Configuration Error", "Please select or create a carton preset for Mode C.")
                return
            
            sku = self.product_combo.currentData()
            if not sku:
                QMessageBox.warning(self, "Configuration Error", "Please select a product SKU in the dropdown.")
                return
            p_model = ProductRepository.get_by_sku(self.db, sku)
            if not p_model:
                QMessageBox.warning(self, "Configuration Error", "Product not found in database.")
                return

            c_model = CartonRepository.get_by_id(self.db, carton_preset_id)
            self._execute_mode_c(c_model.to_dict(), p_model.to_dict(), settings)

    def _execute_mode_a(self, carton: dict, products: list, quantities: list, courier: dict, settings: dict):
        try:
            # Run engine
            result = self.optimizer.optimize(
                carton=carton,
                products=products,
                quantities=quantities,
                top_clearance=settings["top_clearance"],
                cell_size=settings["cell_size"],
                height_tolerance=settings["height_tolerance"],
                required_support=settings["required_support"],
                max_steps=settings["max_steps"]
            )
            
            # Courier volumetric calculations
            vol_factor = courier["volumetric_factor"] if courier else 5000.0
            from shipping.volumetric import calculate_volumetric_weight
            from shipping.courier import estimate_shipping_fee
            
            actual_w = result["statistics"]["total_packed_weight"] + carton["empty_weight"]
            vol_w = calculate_volumetric_weight(carton["length"], carton["width"], carton["height"], vol_factor)
            chargeable_w = max(actual_w, vol_w)
            
            shipping_cost = 0.0
            if courier:
                shipping_cost = estimate_shipping_fee(
                    chargeable_w, courier["rate_per_kg"], courier["minimum_charge"]
                )

            # Package result extensions
            result["volumetric_weight"] = vol_w
            result["actual_weight"] = actual_w
            result["chargeable_weight"] = chargeable_w
            result["shipping_cost"] = shipping_cost
            
            self.last_layout_result = result
            self.last_packed_carton = carton

            self.refresh_layout_instructions()
            self.refresh_summary_tab(result, carton, courier)
            self.tabs.setCurrentIndex(0)
            
            self.print_slip_btn.setEnabled(True)

            # Display warning if items could not fit in selected carton
            if result.get("unpacked"):
                unpacked_msg = "\n".join([f"• {u['product']['name']} ({u['product']['sku']}): {u['quantity']} unpacked" for u in result["unpacked"]])
                QMessageBox.warning(
                    self, "Items Could Not Fit",
                    "Warning: Some requested items could not fit into the selected carton dimensions!\n\n"
                    f"Unpacked Items:\n{unpacked_msg}\n\n"
                    "Tip: Select a larger carton size (e.g. XL or XXL) or use 'Mode B: Recommend Best Carton'."
                )

            # Display warn message if limits exceeded
            if result["statistics"]["stack_limits_violated"]:
                QMessageBox.warning(
                    self, "Safety Constraint Violations", 
                    "Warning: Current packing layout violates safety load restrictions!\n\n" + 
                    "\n".join(result["statistics"]["limit_violations"])
                )
        except Exception as e:
            QMessageBox.critical(self, "Optimization Error", f"Failed to execute packaging optimizer: {e}")

    def _execute_mode_b(self, products: list, quantities: list, courier: dict, settings: dict):
        try:
            recs = self.selector.recommend_cartons(
                self.db, products, quantities, courier,
                top_clearance=settings["top_clearance"],
                cell_size=settings["cell_size"]
            )
            
            self.tab_rec.setRowCount(0)
            if not recs:
                QMessageBox.information(self, "Recommendations Empty", "No cartons in database are large enough to fit these products.")
                return

            for row_idx, r in enumerate(recs):
                self.tab_rec.insertRow(row_idx)
                # Store layout metadata inside row index
                self.tab_rec.setItem(row_idx, 0, QTableWidgetItem(r["carton"]["name"]))
                self.tab_rec.setItem(row_idx, 1, QTableWidgetItem(f"{r['fit_ratio']*100:.1f}%"))
                self.tab_rec.setItem(row_idx, 2, QTableWidgetItem(f"{r['utilization']:.1f}%"))
                
                totals_str = f"Packed {r['total_packed_items']} / Wasted {r['unpacked_count']}"
                self.tab_rec.setItem(row_idx, 3, QTableWidgetItem(totals_str))
                self.tab_rec.setItem(row_idx, 4, QTableWidgetItem(f"${r['estimated_shipping']:.2f}"))
                self.tab_rec.setItem(row_idx, 5, QTableWidgetItem(f"${r['total_cost']:.2f}"))
                
                # Tag carton preset dictionary inside item data slot for reference
                self.table_row_metadata = recs
            
            self.tabs.setCurrentIndex(2)
        except Exception as e:
            QMessageBox.critical(self, "Recommendation Error", f"Failed to run carton recommendations: {e}")

    def view_recommended_layout(self, index):
        """Loads Mode B row item visualization results back into Mode A tabs."""
        row = index.row()
        # Retrieve row preset dictionary
        selected_rec = self.table_row_metadata[row]
        
        self.last_layout_result = selected_rec["layout_result"]
        self.last_packed_carton = selected_rec["carton"]

        # Forward cost parameters back
        self.last_layout_result["volumetric_weight"] = selected_rec["volumetric_weight"]
        self.last_layout_result["actual_weight"] = selected_rec["actual_weight"]
        self.last_layout_result["chargeable_weight"] = selected_rec["chargeable_weight"]
        self.last_layout_result["shipping_cost"] = selected_rec["estimated_shipping"]

        self.refresh_layout_instructions()
        self.refresh_summary_tab(self.last_layout_result, self.last_packed_carton, None)
        self.tabs.setCurrentIndex(0)
        self.print_slip_btn.setEnabled(True)

    def _execute_mode_c(self, carton: dict, product: dict, settings: dict):
        try:
            qty, reason = self.selector.calculate_what_fits(
                carton, product,
                top_clearance=settings["top_clearance"],
                cell_size=settings["cell_size"]
            )
            QMessageBox.information(
                self, "What Fits Capacity Result",
                f"<b>Carton Size:</b> {carton['name']}<br/>"
                f"<b>Product SKU:</b> {product['sku']} ({product['name']})<br/><br/>"
                f"<b>Maximum Quantities Fitted:</b> {qty} units<br/>"
                f"<b>Limiting Factor constraint:</b> {reason}",
                QMessageBox.Ok
            )
        except Exception as e:
            QMessageBox.critical(self, "Solver Error", f"Failed to run Mode C solver: {e}")

    def refresh_layout_instructions(self):
        """Populates layer canvas selection tabs."""
        if not self.last_layout_result or "layers" not in self.last_layout_result:
            return

        self.layer_selector.blockSignals(True)
        self.layer_selector.clear()
        
        for idx, layer in enumerate(self.last_layout_result["layers"]):
            self.layer_selector.addItem(f"Layer {idx + 1}", idx)
            
        self.layer_selector.blockSignals(False)
        self.layer_selector.setCurrentIndex(0)
        
        self.on_layer_selection_changed(0)
        self.trigger_3d_rendering()

    def on_layer_selection_changed(self, idx):
        if idx < 0 or not self.last_layout_result:
            return
        layer_data = self.last_layout_result["layers"][idx]
        self.canvas_2d.set_layer(
            layer_data=layer_data,
            carton_width=self.last_packed_carton["length"],
            carton_length=self.last_packed_carton["width"]
        )
        z_start = layer_data["z_start"]
        z_end = z_start + layer_data["height"]
        self.layer_details_lbl.setText(
            f"Z Range: {z_start:.1f} - {z_end:.1f} mm  |  Placements: {len(layer_data['placements'])} items"
        )

    def trigger_3d_rendering(self):
        """Renders 3D mesh elements inside PyVista Qt widget."""
        if not PYVISTA_AVAILABLE or not self.last_layout_result:
            return
        
        exp = self.exploded_slider.value() / 100.0
        op = self.opacity_slider.value() / 100.0

        self.canvas_3d.render_packing(
            carton=self.last_packed_carton,
            layers=self.last_layout_result["layers"],
            exploded_factor=exp,
            opacity=op
        )

    def on_3d_render_params_changed(self):
        self.trigger_3d_rendering()

    def refresh_summary_tab(self, result: dict, carton: dict, courier: dict):
        stats = result["statistics"]
        self.lbl_util.setText(f"{stats['space_utilization']:.1f}% volume coverage")
        self.lbl_efficiency.setText(f"{stats['packing_efficiency_score']:.1f}% optimal score")
        self.lbl_stability.setText(f"{stats['stability_score']:.1f}% boxes verified stable")
        
        cog = stats["center_of_gravity"]
        self.lbl_cog.setText(f"X: {cog['x']:.1f}, Y: {cog['y']:.1f}, Z: {cog['z']:.1f} mm (Balance Score: {cog['score']:.1f}/100)")
        
        net_w = stats["total_packed_weight"]
        tare_w = carton["empty_weight"]
        self.lbl_weight_breakdown.setText(f"Net: {net_w:.2f} kg  +  Box Tare: {tare_w:.2f} kg  =  Total: {net_w + tare_w:.2f} kg")
        
        self.lbl_chargeable.setText(f"Physical weight: {result['actual_weight']:.2f} kg  |  Volumetric weight: {result['volumetric_weight']:.2f} kg")
        
        shipping_val = f"${result['shipping_cost']:.2f}" if courier else "$0.00 (No Courier Selected)"
        self.lbl_courier_charge.setText(shipping_val)
        
        time_sec = stats["packing_time_estimate_sec"]
        self.lbl_packing_time.setText(f"{int(time_sec // 60)} min {int(time_sec % 60)} sec estimated packing time")

    def save_and_print_pdf_slip(self):
        if not self.last_layout_result:
            return

        # Prepare outputs directory
        exports_dir = os.path.join(ROOT_DIR, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        try:
            # Query the database to get Carton ID if available
            c_model = self.db.query(Carton).filter(Carton.name == self.last_packed_carton["name"]).first()
            carton_id = c_model.id if c_model else None

            # Gather all products models to pack
            p_skus = list(self.selected_products_to_pack.keys())
            products_models = self.db.query(Product).filter(Product.sku.in_(p_skus)).all()
            products_list = [p.to_dict() for p in products_models]

            # 1. Create DB Job entry first to allocate an ID
            job = JobRepository.create(
                db=self.db,
                selected_products=self.selected_products_to_pack,
                carton_id=carton_id,
                layout=self.last_layout_result["layers"],
                utilization=self.last_layout_result["statistics"]["space_utilization"],
                actual_weight=self.last_layout_result["actual_weight"],
                volumetric_weight=self.last_layout_result["volumetric_weight"],
                chargeable_weight=self.last_layout_result["chargeable_weight"],
                shipping_cost=self.last_layout_result["shipping_cost"],
                report_path=None, # will fill after generation
                statistics=self.last_layout_result["statistics"]
            )

            # Generate PDF
            report_name = f"packing_slip_{job.id}.pdf"
            report_path = os.path.join(exports_dir, report_name)
            
            generate_pdf_report(
                output_path=report_path,
                job_id=job.id,
                carton=self.last_packed_carton,
                products_list=products_list,
                selected_quantities=self.selected_products_to_pack,
                layout_result=self.last_layout_result
            )

            # 2. Update job record report path
            job.report_path = report_path
            self.db.commit()

            QMessageBox.information(
                self, "Export Success", 
                f"Packing slip PDF has been generated and saved!\n\nPath: {report_path}"
            )
            
            # Auto open PDF
            os.startfile(report_path)

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save job and export PDF packing slip: {e}")

    def showEvent(self, event):
        self.load_catalogs()
        super().showEvent(event)

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
