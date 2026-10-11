import os
import json
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.repository import JobRepository
from reports.pdf import generate_pdf_report

logger = logging.getLogger("ReportsWindow")

class ReportsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self.selected_job_id = None
        self._build_ui()
        self.load_jobs()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column - Job List
        left_layout = QVBoxLayout()
        title = QLabel("Saved Optimization Jobs History")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1A365D;")
        left_layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Job ID", "Date & Time", "Carton Box", "Utilization", "Shipping Cost"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)

        main_layout.addLayout(left_layout, stretch=2)

        # Right Column - Details and Actions Panel
        right_layout = QVBoxLayout()
        self.details_group = QGroupBox("Selected Job Details")
        form_layout = QFormLayout(self.details_group)

        self.id_lbl = QLabel("-")
        self.date_lbl = QLabel("-")
        self.carton_lbl = QLabel("-")
        self.util_lbl = QLabel("-")
        self.weight_lbl = QLabel("-")
        self.cost_lbl = QLabel("-")

        form_layout.addRow("Job Reference ID:", self.id_lbl)
        form_layout.addRow("Optimization Date:", self.date_lbl)
        form_layout.addRow("Carton Container:", self.carton_lbl)
        form_layout.addRow("Space Utilization:", self.util_lbl)
        form_layout.addRow("Total Weight (Actual):", self.weight_lbl)
        form_layout.addRow("Est. Courier Fee:", self.cost_lbl)

        right_layout.addWidget(self.details_group)

        # Actions buttons
        actions_layout = QVBoxLayout()
        self.open_pdf_btn = QPushButton("Open PDF Packing Slip")
        self.open_pdf_btn.clicked.connect(self.open_pdf_report)
        self.open_pdf_btn.setEnabled(False)
        self.open_pdf_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 10px; font-weight: bold;")
        
        self.delete_btn = QPushButton("Delete Job Record")
        self.delete_btn.clicked.connect(self.delete_job)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #E53E3E; color: white; padding: 10px;")

        actions_layout.addWidget(self.open_pdf_btn)
        actions_layout.addWidget(self.delete_btn)
        right_layout.addLayout(actions_layout)
        right_layout.addStretch()

        main_layout.addLayout(right_layout, stretch=1)

    def load_jobs(self):
        self.table.setRowCount(0)
        jobs = JobRepository.get_all(self.db)
        
        for row_idx, job in enumerate(jobs):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(f"#{job.id}"))
            self.table.setItem(row_idx, 1, QTableWidgetItem(job.date.strftime("%Y-%m-%d %H:%M:%S")))
            
            box_name = job.carton.name if job.carton else "Custom Box"
            self.table.setItem(row_idx, 2, QTableWidgetItem(box_name))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{job.utilization:.1f}%"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"${job.shipping_cost:.2f}"))

    def on_selection_changed(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_details()
            return

        row = selected_ranges[0].topRow()
        # Parse job ID from #ID string
        job_id_str = self.table.item(row, 0).text().replace("#", "")
        job_id = int(job_id_str)
        job = JobRepository.get_by_id(self.db, job_id)
        if not job:
            return

        self.selected_job_id = job.id
        self.id_lbl.setText(f"Job #{job.id}")
        self.date_lbl.setText(job.date.strftime("%Y-%m-%d %H:%M:%S"))
        
        box_name = job.carton.name if job.carton else "Custom Box"
        self.carton_lbl.setText(box_name)
        self.util_lbl.setText(f"{job.utilization:.1f}%")
        self.weight_lbl.setText(f"{job.actual_weight:.2f} kg (Chargeable: {job.chargeable_weight:.2f} kg)")
        self.cost_lbl.setText(f"${job.shipping_cost:.2f}")

        self.open_pdf_btn.setEnabled(bool(job.report_path and os.path.exists(job.report_path)))
        
        # If file missing but record exists, enable re-generation fallback
        if job.report_path and not os.path.exists(job.report_path):
            self.open_pdf_btn.setEnabled(True)
            self.open_pdf_btn.setText("Regenerate & Open PDF")
        else:
            self.open_pdf_btn.setText("Open PDF Packing Slip")

        self.delete_btn.setEnabled(True)

    def clear_details(self):
        self.selected_job_id = None
        self.id_lbl.setText("-")
        self.date_lbl.setText("-")
        self.carton_lbl.setText("-")
        self.util_lbl.setText("-")
        self.weight_lbl.setText("-")
        self.cost_lbl.setText("-")
        self.open_pdf_btn.setEnabled(False)
        self.open_pdf_btn.setText("Open PDF Packing Slip")
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def open_pdf_report(self):
        if not self.selected_job_id:
            return
        job = JobRepository.get_by_id(self.db, self.selected_job_id)
        if not job:
            return

        report_path = job.report_path
        
        # Re-generate PDF if it is missing
        if not report_path or not os.path.exists(report_path):
            try:
                # Compile parameters for PDF generation
                carton_dict = job.carton.to_dict() if job.carton else {
                    "name": "Custom Carton", "length": 0.0, "width": 0.0, "height": 0.0,
                    "max_weight": 0.0, "empty_weight": 0.0, "cost": 0.0
                }
                
                # Fetch products details
                selected_prods = json.loads(job.selected_products)
                layout_result = {
                    "layers": json.loads(job.layout),
                    "volumetric_weight": job.volumetric_weight,
                    "actual_weight": job.actual_weight,
                    "chargeable_weight": job.chargeable_weight,
                    "shipping_cost": job.shipping_cost,
                    "statistics": json.loads(job.statistics) if job.statistics else {"space_utilization": job.utilization, "packing_efficiency_score": job.utilization}
                }
                
                # Load actual products models from database
                from database.models import Product
                prods_catalog = self.db.query(Product).filter(Product.id.in_(selected_prods.keys())).all()
                products_list = [p.to_dict() for p in prods_catalog]

                # Default export path
                exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
                report_path = os.path.join(exports_dir, f"packing_slip_{job.id}.pdf")
                
                generate_pdf_report(
                    output_path=report_path,
                    job_id=job.id,
                    carton=carton_dict,
                    products_list=products_list,
                    selected_quantities=selected_prods,
                    layout_result=layout_result
                )
                
                # Update job report path
                job.report_path = report_path
                self.db.commit()
                
                self.open_pdf_btn.setText("Open PDF Packing Slip")
            except Exception as e:
                QMessageBox.critical(self, "PDF Regeneration Error", f"Failed to regenerate PDF: {e}")
                return

        # Open PDF in OS viewer
        try:
            os.startfile(report_path)
        except Exception as e:
            QMessageBox.critical(self, "Viewer Error", f"Failed to open PDF file: {e}")

    def delete_job(self):
        if not self.selected_job_id:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this job record from database history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            JobRepository.delete(self.db, self.selected_job_id)
            self.load_jobs()
            self.clear_details()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
