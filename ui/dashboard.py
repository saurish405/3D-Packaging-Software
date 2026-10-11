from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import Product, Carton, Job

class DashboardWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = SessionLocal()
        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # Title Banner
        banner = QLabel("Warehouse Packaging Optimization Dashboard")
        banner.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A365D; padding-bottom: 10px;")
        main_layout.addWidget(banner)

        # Top Section - Stats Cards Layout
        stats_layout = QGridLayout()
        
        self.prod_card = QGroupBox("Products Cataloged")
        self.prod_card.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        self.prod_lbl = QLabel("0")
        self.prod_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #319795; qproperty-alignment: AlignCenter; padding: 15px;")
        p_lay = QVBoxLayout(self.prod_card)
        p_lay.addWidget(self.prod_lbl)

        self.carton_card = QGroupBox("Carton Sizes")
        self.carton_card.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        self.carton_lbl = QLabel("0")
        self.carton_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #3182CE; qproperty-alignment: AlignCenter; padding: 15px;")
        c_lay = QVBoxLayout(self.carton_card)
        c_lay.addWidget(self.carton_lbl)

        self.jobs_card = QGroupBox("Optimized Packing Jobs")
        self.jobs_card.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        self.jobs_lbl = QLabel("0")
        self.jobs_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #805AD5; qproperty-alignment: AlignCenter; padding: 15px;")
        j_lay = QVBoxLayout(self.jobs_card)
        j_lay.addWidget(self.jobs_lbl)

        stats_layout.addWidget(self.prod_card, 0, 0)
        stats_layout.addWidget(self.carton_card, 0, 1)
        stats_layout.addWidget(self.jobs_card, 0, 2)
        main_layout.addLayout(stats_layout)

        main_layout.addSpacing(15)

        # Bottom Section - Recent History list
        history_group = QGroupBox("Recent Packing Operations")
        history_layout = QVBoxLayout(history_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Job ID", "Date & Time", "Carton Profile Used", "Space Utilization", "Shipping Weight"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        history_layout.addWidget(self.table)

        main_layout.addWidget(history_group, stretch=1)

    def refresh_dashboard(self):
        """Fetches latest metrics and populates widgets."""
        try:
            # Stats queries
            total_prods = self.db.query(Product).count()
            total_cartons = self.db.query(Carton).count()
            total_jobs = self.db.query(Job).count()

            self.prod_lbl.setText(str(total_prods))
            self.carton_lbl.setText(str(total_cartons))
            self.jobs_lbl.setText(str(total_jobs))

            # Recent Jobs query
            recent_jobs = self.db.query(Job).order_by(Job.date.desc()).limit(8).all()
            self.table.setRowCount(0)
            
            for row_idx, job in enumerate(recent_jobs):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(f"Job #{job.id}"))
                self.table.setItem(row_idx, 1, QTableWidgetItem(job.date.strftime("%Y-%m-%d %H:%M:%S")))
                
                box_name = job.carton.name if job.carton else "Custom Box"
                self.table.setItem(row_idx, 2, QTableWidgetItem(box_name))
                self.table.setItem(row_idx, 3, QTableWidgetItem(f"{job.utilization:.1f}%"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(f"{job.actual_weight:.2f} kg"))
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
