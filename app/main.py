import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QSize

# Adjust python paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from ui.dashboard import DashboardWindow
from ui.product_window import ProductWindow
from ui.carton_window import CartonWindow
from ui.optimizer_window import OptimizerWindow
from ui.reports_window import ReportsWindow
from ui.settings_window import SettingsWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warehouse Packaging Optimizer")
        self.resize(1100, 750)
        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        """Applies a premium, modern dark stylesheet to the Qt interface."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A202C; /* Dark Charcoal */
            }
            QWidget {
                color: #E2E8F0; /* Off-White text */
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#Sidebar {
                background-color: #2D3748; /* Slate Grey sidebar */
                border-right: 1px solid #4A5568;
            }
            QPushButton.SidebarBtn {
                background-color: transparent;
                border: none;
                color: #A0AEC0;
                text-align: left;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                border-left: 4px solid transparent;
            }
            QPushButton.SidebarBtn:hover {
                background-color: #4A5568;
                color: #FFFFFF;
            }
            QPushButton.SidebarBtn:checked {
                background-color: #3182CE; /* Solid Blue highlight */
                color: #FFFFFF;
                border-left: 4px solid #319795; /* Teal edge marker */
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #4A5568;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #2D3748;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #319795; /* Teal titles */
            }
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                background-color: #1A202C;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 5px;
                color: #E2E8F0;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #3182CE;
            }
            QTableWidget {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                gridline-color: #4A5568;
                color: #E2E8F0;
                selection-background-color: #3182CE;
                selection-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1A202C;
                color: #A0AEC0;
                padding: 5px;
                border: 1px solid #4A5568;
            }
            QTabWidget::pane {
                border: 1px solid #4A5568;
                background-color: #2D3748;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #1A202C;
                border: 1px solid #4A5568;
                border-bottom: none;
                padding: 8px 16px;
                color: #A0AEC0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:hover {
                background-color: #2D3748;
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background-color: #2D3748;
                color: #319795;
                border-bottom: 2px solid #319795;
            }
            QMessageBox {
                background-color: #2D3748;
            }
        """)

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Frame
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)

        # Logo/Brand header
        brand_lbl = QLabel("Antigravity Pack")
        brand_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #319795; padding-left: 20px; padding-bottom: 5px;")
        sub_lbl = QLabel("Warehouse Solutions")
        sub_lbl.setStyleSheet("font-size: 10px; color: #718096; padding-left: 20px; padding-bottom: 30px;")
        sidebar_layout.addWidget(brand_lbl)
        sidebar_layout.addWidget(sub_lbl)

        # Navigation Buttons
        self.nav_buttons = []
        self.btn_dashboard = self._create_nav_button("Dashboard", 0)
        self.btn_optimizer = self._create_nav_button("Packing Optimizer", 1)
        self.btn_products = self._create_nav_button("Products Catalog", 2)
        self.btn_cartons = self._create_nav_button("Carton Profiles", 3)
        self.btn_history = self._create_nav_button("Job Log History", 4)
        self.btn_settings = self._create_nav_button("Courier & Settings", 5)

        for btn in [self.btn_dashboard, self.btn_optimizer, self.btn_products, self.btn_cartons, self.btn_history, self.btn_settings]:
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()
        
        version_lbl = QLabel("v1.0.0 (Offline Mode)")
        version_lbl.setStyleSheet("font-size: 9px; color: #718096; text-align: center; padding-left: 20px;")
        sidebar_layout.addWidget(version_lbl)

        main_layout.addWidget(self.sidebar)

        # 2. Main Content Canvas StackedWidget
        self.content_stack = QStackedWidget()
        
        # Instantiate views
        self.view_dashboard = DashboardWindow()
        self.view_optimizer = OptimizerWindow()
        self.view_products = ProductWindow()
        self.view_cartons = CartonWindow()
        self.view_history = ReportsWindow()
        self.view_settings = SettingsWindow()

        # Add to stack
        self.content_stack.addWidget(self.view_dashboard) # Index 0
        self.content_stack.addWidget(self.view_optimizer) # Index 1
        self.content_stack.addWidget(self.view_products)  # Index 2
        self.content_stack.addWidget(self.view_cartons)   # Index 3
        self.content_stack.addWidget(self.view_history)   # Index 4
        self.content_stack.addWidget(self.view_settings)  # Index 5

        # Content container widget for margins styling
        content_container = QWidget()
        cc_layout = QVBoxLayout(content_container)
        cc_layout.setContentsMargins(20, 20, 20, 20)
        cc_layout.addWidget(self.content_stack)

        main_layout.addWidget(content_container, stretch=1)

        # Select initial button
        self.btn_dashboard.setChecked(True)

    def _create_nav_button(self, label: str, index: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setProperty("class", "SidebarBtn")
        btn.clicked.connect(lambda: self.switch_view(index))
        return btn

    def switch_view(self, index: int):
        """Changes the stacked widget view index and refreshes datasets on entry."""
        self.content_stack.setCurrentIndex(index)
        
        # Refresh widgets dynamic values when tabs open
        if index == 0:
            self.view_dashboard.refresh_dashboard()
        elif index == 1:
            self.view_optimizer.load_catalogs()
        elif index == 2:
            self.view_products.load_products()
        elif index == 3:
            self.view_cartons.load_cartons()
        elif index == 4:
            self.view_history.load_jobs()
        elif index == 5:
            self.view_settings.load_couriers()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
