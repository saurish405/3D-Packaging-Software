import hashlib
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF

class Layer2DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layer_data = None  # {"z_start": float, "height": float, "grid": list, "placements": list}
        self.carton_width = 1.0  # physical mm
        self.carton_length = 1.0  # physical mm
        self.setMinimumSize(300, 300)

    def set_layer(self, layer_data: dict, carton_width: float, carton_length: float):
        """Sets the active layer packing data to render."""
        self.layer_data = layer_data
        self.carton_width = max(1.0, carton_width)
        self.carton_length = max(1.0, carton_length)
        self.update()

    def _get_color_for_sku(self, sku: str) -> QColor:
        """Generates a consistent, modern pastel HSL color based on SKU hashing."""
        h_hash = hashlib.md5(sku.encode('utf-8')).hexdigest()
        hue = int(h_hash[:4], 16) % 360
        # High saturation (65-80%) and balanced lightness (75-85%) for beautiful modern look
        sat = 75
        light = 80
        color = QColor()
        color.setHsl(hue, int(sat * 2.55), int(light * 2.55))
        return color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Clear background (premium dark mode or clean off-white background)
        # Let's check parent styling, or use a soft grey canvas background
        painter.fillRect(self.rect(), QColor("#EDF2F7"))

        if not self.layer_data or "placements" not in self.layer_data:
            painter.setPen(QColor("#718096"))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Layer Selected / No Packings Placed")
            return

        # Calculate bounding offsets and scale to preserve aspect ratio
        margin = 30.0
        avail_w = self.width() - (margin * 2.0)
        avail_h = self.height() - (margin * 2.0)

        # Map:
        # X physical corresponds to carton width (horizontal)
        # Y physical corresponds to carton length (vertical)
        scale_x = avail_w / self.carton_width
        scale_y = avail_h / self.carton_length
        scale = min(scale_x, scale_y)

        # Center the carton drawing in the widget area
        drawn_w = self.carton_width * scale
        drawn_h = self.carton_length * scale
        offset_x = margin + (avail_w - drawn_w) / 2.0
        offset_y = margin + (avail_h - drawn_h) / 2.0

        # Draw carton boundaries (outer frame)
        carton_rect = QRectF(offset_x, offset_y, drawn_w, drawn_h)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#2B6CB0"), 3, Qt.SolidLine))
        painter.drawRect(carton_rect)

        # Render each placement rectangle
        placements = self.layer_data.get("placements", [])
        for pl in placements:
            px = offset_x + pl["x"] * scale
            py = offset_y + pl["y"] * scale
            pw = pl["length"] * scale
            ph = pl["width"] * scale

            box_rect = QRectF(px, py, pw, ph)

            # Draw filled product body
            fill_color = self._get_color_for_sku(pl["sku"])
            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(QColor("#1A202C"), 1.5, Qt.SolidLine))
            painter.drawRect(box_rect)

            # Draw text labels if box size is large enough to display details
            painter.setPen(QColor("#1A202C"))
            font_size = max(7, int(min(pw, ph) / 8.0))
            font_size = min(11, font_size)
            
            painter.setFont(QFont("Arial", font_size, QFont.Bold))
            sku_rect = QRectF(px + 4, py + 4, pw - 8, font_size + 4)
            painter.drawText(sku_rect, Qt.AlignLeft | Qt.AlignVCenter, pl["sku"])

            painter.setFont(QFont("Arial", max(6, font_size - 1)))
            name_rect = QRectF(px + 4, py + 4 + font_size + 2, pw - 8, font_size + 4)
            painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, pl["name"])

            # Draw orientation arrow pointing forward (Y-axis) or side (X-axis)
            # Typically show direction based on dimensions orientation
            painter.setPen(QPen(QColor("#2D3748"), 2, Qt.SolidLine))
            arrow_size = min(pw, ph) * 0.25
            arrow_size = min(12.0, max(6.0, arrow_size))

            cx = px + pw / 2.0
            cy = py + ph - arrow_size - 4.0

            # Arrow indicating pointing up (standard direction)
            # Or draw arrow pointing in the direction of the longest side
            is_horizontal = pl["length"] > pl["width"]
            
            if is_horizontal:
                # Arrow points right: -->
                painter.drawLine(QPointF(cx - arrow_size/2.0, cy), QPointF(cx + arrow_size/2.0, cy))
                painter.drawLine(QPointF(cx + arrow_size/2.0, cy), QPointF(cx + arrow_size/2.0 - 3, cy - 3))
                painter.drawLine(QPointF(cx + arrow_size/2.0, cy), QPointF(cx + arrow_size/2.0 - 3, cy + 3))
            else:
                # Arrow points up: ^
                painter.drawLine(QPointF(cx, cy + arrow_size/2.0), QPointF(cx, cy - arrow_size/2.0))
                painter.drawLine(QPointF(cx, cy - arrow_size/2.0), QPointF(cx - 3, cy - arrow_size/2.0 + 3))
                painter.drawLine(QPointF(cx, cy - arrow_size/2.0), QPointF(cx + 3, cy - arrow_size/2.0 + 3))
