import hashlib
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QColor

logger = logging.getLogger("Renderer3D")

# Global flags for PyVista / VTK availability
PYVISTA_AVAILABLE = False
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PyVista 3D packages (pyvista, pyvistaqt) could not be loaded: {e}. Running in 2D-only fallback mode.")

class Viewer3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = None
        self.fallback_label = None

        if PYVISTA_AVAILABLE:
            try:
                # Initialize QtInteractor widget
                self.plotter = QtInteractor(self)
                self.layout.addWidget(self.plotter)
                self.plotter.set_background("white")
            except Exception as ex:
                logger.error(f"Failed to initialize VTK 3D renderer: {ex}. Falling back to text display.")
                self.plotter = None
                self._create_fallback_label(str(ex))
        else:
            self._create_fallback_label("PyVista/VTK modules not installed.")

    def _create_fallback_label(self, reason: str):
        self.fallback_label = QLabel(
            f"3D Rendering Unavailable\n({reason})\n\nPlease use the 2D Layer-by-Layer viewer.", 
            self
        )
        self.fallback_label.setStyleSheet("color: #718096; font-size: 13px; font-weight: bold;")
        self.fallback_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.fallback_label)

    def _get_rgb_for_sku(self, sku: str) -> tuple:
        """Generates consistent RGB color values based on SKU hashing."""
        h_hash = hashlib.md5(sku.encode('utf-8')).hexdigest()
        hue = int(h_hash[:4], 16) % 360
        # Convert HSL (hue, 75% saturation, 65% lightness) to RGB
        q_color = QColor()
        q_color.setHsl(hue, int(0.75 * 255), int(0.65 * 255))
        return (q_color.red() / 255.0, q_color.green() / 255.0, q_color.blue() / 255.0)

    def render_packing(
        self,
        carton: dict,
        layers: list,
        exploded_factor: float = 0.0,
        opacity: float = 0.8,
        hidden_layers: set = None
    ):
        """
        Renders the carton and packed items in 3D.
        exploded_factor: Vertical expansion multiplier (e.g. 0.0 to 1.5).
        opacity: Opacity value for product cubes (0.0 to 1.0).
        hidden_layers: Set of layer indices to hide.
        """
        if not self.plotter:
            return

        if hidden_layers is None:
            hidden_layers = set()

        self.plotter.clear()

        c_w = float(carton["length"])
        c_l = float(carton["width"])
        c_h = float(carton["height"])

        z_offset_accum = 0.0

        # Draw carton wireframe outer bounding box
        # bounds: (x_min, x_max, y_min, y_max, z_min, z_max)
        carton_mesh = pv.Box(bounds=(0, c_w, 0, c_l, 0, c_h))
        self.plotter.add_mesh(carton_mesh, style="wireframe", color="#1A365D", line_width=2.5, name="carton_wireframe")

        for k, layer in enumerate(layers):
            if k in hidden_layers:
                continue

            # In exploded view, shift each layer's starting Z position upwards using accumulated height
            z_shift = z_offset_accum

            for pl in layer["placements"]:
                x1, x2 = pl["x"], pl["x"] + pl["length"]
                y1, y2 = pl["y"], pl["y"] + pl["width"]
                z1, z2 = pl["z"] + z_shift, pl["z"] + pl["height"] + z_shift

                # Create 3D box mesh for this item
                item_mesh = pv.Box(bounds=(x1, x2, y1, y2, z1, z2))
                color_rgb = self._get_rgb_for_sku(pl["sku"])
                
                # Add item mesh to plotter
                self.plotter.add_mesh(
                    item_mesh,
                    color=color_rgb,
                    opacity=opacity,
                    edge_color="black",
                    show_edges=True,
                    line_width=1.0
                )

                # Add small text label at the center of the box for identification
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                cz = (z1 + z2) / 2.0
                # Add labels selectively if they aren't too crowded
                # self.plotter.add_point_labels([[cx, cy, cz]], [f"#{pl['id']}"], font_size=8, text_color="black")

            z_offset_accum += layer["height"] * exploded_factor

        self.plotter.reset_camera()
        self.plotter.render()
# Map Qt alignment flags locally if needed
from PySide6.QtCore import Qt
