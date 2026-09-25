"""
preview_tab.py — 2D Stage Visualizer with Dynamic RGBW PAR LED Glow
Front-view stage representation with draggable fixtures and coordinate inspector.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QSpinBox, QGroupBox, QSplitter
    )
    from PySide6.QtCore import Qt, QPoint, QRectF, Signal
    from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class StageCanvas(QFrame if HAS_QT else object):
    """2D Stage Canvas: front view rendering of PAR LED fixtures with RGBW light beams."""
    fixture_selected = Signal(int, int, int) if HAS_QT else None  # fixture_id, x, y

    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #08090b; border: 1px solid #282c34; border-radius: 6px;")
        self.fixtures = [
            {"id": 1, "name": "PAR LED 1", "x": 120, "y": 90, "r": 255, "g": 180, "b": 0, "w": 50, "dim": 220},
            {"id": 2, "name": "PAR LED 2", "x": 260, "y": 90, "r": 255, "g": 140, "b": 0, "w": 40, "dim": 240},
            {"id": 3, "name": "PAR LED 3", "x": 400, "y": 90, "r": 255, "g": 140, "b": 0, "w": 40, "dim": 240},
            {"id": 4, "name": "PAR LED 4", "x": 540, "y": 90, "r": 255, "g": 180, "b": 0, "w": 50, "dim": 220},
        ]
        self.selected_idx = 0
        self._drag_active = False

    def select_fixture(self, idx: int):
        if 0 <= idx < len(self.fixtures):
            self.selected_idx = idx
            fix = self.fixtures[idx]
            if HAS_QT and self.fixture_selected:
                self.fixture_selected.emit(fix["id"], fix["x"], fix["y"])
            self.update()

    def update_fixture_pos(self, x: int, y: int):
        if 0 <= self.selected_idx < len(self.fixtures):
            self.fixtures[self.selected_idx]["x"] = x
            self.fixtures[self.selected_idx]["y"] = y
            self.update()

    def update_color(self, idx: int, r: int, g: int, b: int, w: int, dim: int):
        if 0 <= idx < len(self.fixtures):
            self.fixtures[idx]["r"] = r
            self.fixtures[idx]["g"] = g
            self.fixtures[idx]["b"] = b
            self.fixtures[idx]["w"] = w
            self.fixtures[idx]["dim"] = dim
            if HAS_QT: self.update()

    def mousePressEvent(self, event):
        if not HAS_QT: return
        pos = event.position().toPoint()
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            if (pos.x() - fx)**2 + (pos.y() - fy)**2 <= 25**2:
                self.selected_idx = idx
                self._drag_active = True
                if self.fixture_selected:
                    self.fixture_selected.emit(fix["id"], fx, fy)
                self.update()
                break

    def mouseMoveEvent(self, event):
        if not HAS_QT or not self._drag_active: return
        pos = event.position().toPoint()
        self.fixtures[self.selected_idx]["x"] = max(30, min(self.width() - 30, pos.x()))
        self.fixtures[self.selected_idx]["y"] = max(30, min(self.height() - 30, pos.y()))
        fix = self.fixtures[self.selected_idx]
        if self.fixture_selected:
            self.fixture_selected.emit(fix["id"], fix["x"], fix["y"])
        self.update()

    def mouseReleaseEvent(self, event):
        self._drag_active = False

    def paintEvent(self, event):
        if not HAS_QT: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Draw Stage Truss bar
        painter.setPen(QPen(QColor("#3e4451"), 3))
        painter.drawLine(40, 90, w - 40, 90)

        # Draw Stage Floor line
        painter.setPen(QPen(QColor("#282c34"), 2, Qt.DashLine))
        painter.drawLine(20, h - 40, w - 20, h - 40)
        painter.setPen(QColor(Theme.TEXT_MUTED))
        painter.drawText(30, h - 48, "STAGE FLOOR (PANGGUNG GIA DELIKSARI)")

        # Render Fixtures
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            r, g, b, w_val, dim = fix["r"], fix["g"], fix["b"], fix["w"], fix["dim"]

            # Compute effective illuminated color with white addition
            factor = dim / 255.0
            er = min(255, int((r + w_val * 0.8) * factor))
            eg = min(255, int((g + w_val * 0.8) * factor))
            eb = min(255, int((b + w_val * 0.8) * factor))

            # Light beam downward cone (Gradient)
            cone_grad = QRadialGradient(fx, fy, 160)
            cone_grad.setColorAt(0.0, QColor(er, eg, eb, int(140 * factor)))
            cone_grad.setColorAt(0.5, QColor(er, eg, eb, int(60 * factor)))
            cone_grad.setColorAt(1.0, QColor(er, eg, eb, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(cone_grad))
            painter.drawEllipse(fx - 70, fy - 20, 140, 220)

            # Fixture Lens Body
            is_sel = (idx == self.selected_idx)
            border_color = Theme.ACCENT_CYAN if is_sel else "#ffffff"

            painter.setPen(QPen(QColor(border_color), 2 if is_sel else 1))
            painter.setBrush(QColor(er, eg, eb))
            painter.drawEllipse(fx - 16, fy - 16, 32, 32)

            # Fixture ID text
            painter.setPen(QColor("#ffffff" if is_sel else Theme.TEXT_MUTED))
            painter.drawText(fx - 20, fy - 22, fix["name"])


class PreviewTab(QWidget):
    """Stage Preview Tab: 2D Front-View Stage with Coordinate Inspector."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("2D STAGE LIGHTING VISUALIZER (FRONT VIEW)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Simulasi radiasi warna lampu PAR LED RGBW tampak depan panggung gereja.")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Splitter: Canvas Left, Coordinates Inspector Right
        splitter = QSplitter(Qt.Horizontal)

        self.canvas = StageCanvas()
        self.canvas.fixture_selected.connect(self._on_fixture_selected)
        splitter.addWidget(self.canvas)

        # Right Inspector Panel
        inspector = QGroupBox("Fixture Position Inspector")
        inspector.setFixedWidth(240)
        ins_layout = QVBoxLayout(inspector)

        self.lbl_selected_fix = QLabel("Fixture Terpilih: PAR LED 1")
        self.lbl_selected_fix.setStyleSheet("font-weight: bold; color: #00e5ff;")
        ins_layout.addWidget(self.lbl_selected_fix)

        pos_grid = QHBoxLayout()
        pos_grid.addWidget(QLabel("X:"))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 1920)
        self.spin_x.setValue(120)
        self.spin_x.valueChanged.connect(self._on_spin_changed)
        pos_grid.addWidget(self.spin_x)

        pos_grid.addWidget(QLabel("Y:"))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 1080)
        self.spin_y.setValue(90)
        self.spin_y.valueChanged.connect(self._on_spin_changed)
        pos_grid.addWidget(self.spin_y)
        ins_layout.addLayout(pos_grid)

        ins_layout.addStretch()
        splitter.addWidget(inspector)

        main_layout.addWidget(splitter)

    def _on_fixture_selected(self, fix_id: int, x: int, y: int):
        self.lbl_selected_fix.setText(f"Fixture Terpilih: PAR LED {fix_id}")
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

    def _on_spin_changed(self):
        self.canvas.update_fixture_pos(self.spin_x.value(), self.spin_y.value())
