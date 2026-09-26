"""
preview_tab.py — Standalone Floating Stage Visualizer Window (2D & 3D)
Provides high-fidelity stage lighting simulation with dynamic RGBW PAR LED beam glows,
draggable fixtures, and multi-monitor detachable window support.
"""

from __future__ import annotations
import math

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QGroupBox, QSplitter, QTabWidget,
    Qt, QPoint, QRectF, Signal, QPainter, QColor, QPen,
    QRadialGradient, QLinearGradient, QBrush, QFont
)
from ui.styles import Theme, CONSOLE_QSS


class Stage2DCanvas(QFrame if HAS_QT else object):
    """Front-view 2D Stage Canvas with realistic RGBW PAR LED beam projection and glow halos."""
    fixture_selected = Signal(int, int, int)

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #07080a; border: 1px solid #333844; border-radius: 6px;")
        self.fixtures = [
            {"id": 1, "name": "PAR LED 1", "x": 120, "y": 80, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
            {"id": 2, "name": "PAR LED 2", "x": 260, "y": 80, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"id": 3, "name": "PAR LED 3", "x": 400, "y": 80, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"id": 4, "name": "PAR LED 4", "x": 540, "y": 80, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
        ]
        self.selected_idx = 0
        self._drag_active = False

    def set_fixture_color(self, idx: int, r: int, g: int, b: int, w: int, dim: int) -> None:
        if 0 <= idx < len(self.fixtures):
            self.fixtures[idx]["r"] = r
            self.fixtures[idx]["g"] = g
            self.fixtures[idx]["b"] = b
            self.fixtures[idx]["w"] = w
            self.fixtures[idx]["dim"] = dim
            self.update()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX channels (1-16) for 4 generic PAR LED RGBW fixtures."""
        if len(dmx_channels) >= 16:
            for par_idx in range(4):
                base = par_idx * 4
                r = dmx_channels[base]
                g = dmx_channels[base + 1]
                b = dmx_channels[base + 2]
                w = dmx_channels[base + 3]
                dim = max(r, g, b, w)
                self.set_fixture_color(par_idx, r, g, b, w, dim)

    def mousePressEvent(self, event) -> None:
        pos = event.position().toPoint()
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            if (pos.x() - fx)**2 + (pos.y() - fy)**2 <= 28**2:
                self.selected_idx = idx
                self._drag_active = True
                self.fixture_selected.emit(fix["id"], fx, fy)
                self.update()
                break

    def mouseMoveEvent(self, event) -> None:
        if not self._drag_active: return
        pos = event.position().toPoint()
        self.fixtures[self.selected_idx]["x"] = max(35, min(self.width() - 35, pos.x()))
        self.fixtures[self.selected_idx]["y"] = max(35, min(self.height() - 35, pos.y()))
        fix = self.fixtures[self.selected_idx]
        self.fixture_selected.emit(fix["id"], fix["x"], fix["y"])
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_active = False

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Truss rig bar at top
        pen_truss = QPen(QColor("#242832"), 6)
        painter.setPen(pen_truss)
        painter.drawLine(20, 80, w - 20, 80)

        # Stage floor line
        pen_floor = QPen(QColor("#1e222a"), 3)
        painter.setPen(pen_floor)
        painter.drawLine(0, h - 30, w, h - 30)

        # Render fixtures & light beams
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # 1. Light Conical Beam Projection downwards
            if dim > 0.05:
                beam_grad = QLinearGradient(fx, fy, fx, h - 30)
                beam_color_top = QColor(r, g, b, int(160 * dim))
                beam_color_bottom = QColor(r, g, b, int(20 * dim))
                beam_grad.setColorAt(0.0, beam_color_top)
                beam_grad.setColorAt(1.0, beam_color_bottom)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(beam_grad))

                beam_path = [
                    QPoint(fx - 14, fy + 8),
                    QPoint(fx + 14, fy + 8),
                    QPoint(fx + 65, h - 30),
                    QPoint(fx - 65, h - 30),
                ]
                painter.drawPolygon(beam_path)

            # 2. Glowing Halo
            rad_grad = QRadialGradient(fx, fy, 45)
            rad_grad.setColorAt(0.0, QColor(r, g, b, int(230 * dim)))
            rad_grad.setColorAt(0.4, QColor(r, g, b, int(110 * dim)))
            rad_grad.setColorAt(1.0, QColor(r, g, b, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(rad_grad))
            painter.drawEllipse(fx - 45, fy - 45, 90, 90)

            # 3. Fixture Head Hardware Housing
            is_sel = (idx == self.selected_idx)
            painter.setPen(QPen(QColor(Theme.ACCENT_CYAN if is_sel else Theme.BORDER_STRONG), 2))
            painter.setBrush(QColor("#181c24"))
            painter.drawEllipse(fx - 18, fy - 18, 36, 36)

            # 4. Lens Center
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(r, g, b, int(255 * max(0.2, dim))))
            painter.drawEllipse(fx - 11, fy - 11, 22, 22)

            # Label
            painter.setFont(QFont("Inter", 8, QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            painter.drawText(QRectF(fx - 40, fy + 22, 80, 16), Qt.AlignCenter, fix["name"])

        painter.end()


class StageVisualizerWindow(QWidget if HAS_QT else object):
    """
    Standalone Floating Window for Stage Visualization.
    Can be placed on second monitor (projector / external FOH screen).
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Stage Visualizer (2D & 3D) — ZZLUXORA")
        self.resize(800, 540)
        self.setStyleSheet(CONSOLE_QSS)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("STAGE LIGHTING VISUALIZER (MULTI-SCREEN SUPPORT)")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Simulasi Tampak Depan Panggung • Pendaran Berkas Cahaya Dinamis PAR LED RGBW")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_reset_pos = QPushButton("↺ Reset Posisi Panggung")
        self.btn_reset_pos.clicked.connect(self._reset_positions)
        top_bar.addWidget(self.btn_reset_pos)

        self.btn_close = QPushButton("Tutup")
        self.btn_close.clicked.connect(self.close)
        top_bar.addWidget(self.btn_close)

        main_layout.addLayout(top_bar)

        # Splitter: Canvas vs Inspector
        splitter = QSplitter(Qt.Horizontal)

        # 2D Canvas
        self.canvas_2d = Stage2DCanvas(self)
        self.canvas_2d.fixture_selected.connect(self._on_fixture_selected)
        splitter.addWidget(self.canvas_2d)

        # Inspector Card
        insp_box = QGroupBox("Inspektor Posisi Fixture")
        insp_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        insp_layout = QVBoxLayout(insp_box)
        insp_layout.setSpacing(10)

        self.lbl_fix_name = QLabel("Fixture Terpilih: PAR LED 1")
        self.lbl_fix_name.setStyleSheet(f"font-weight: 700; color: {Theme.ACCENT_CYAN};")
        insp_layout.addWidget(self.lbl_fix_name)

        insp_layout.addWidget(QLabel("Koordinat X (Horizontal):"))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 1920)
        self.spin_x.setValue(120)
        self.spin_x.valueChanged.connect(self._on_spin_changed)
        insp_layout.addWidget(self.spin_x)

        insp_layout.addWidget(QLabel("Koordinat Y (Vertikal Truss):"))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 1080)
        self.spin_y.setValue(80)
        self.spin_y.valueChanged.connect(self._on_spin_changed)
        insp_layout.addWidget(self.spin_y)

        insp_layout.addStretch()
        splitter.addWidget(insp_box)

        splitter.setSizes([620, 180])
        main_layout.addWidget(splitter, 1)

    def _on_fixture_selected(self, fix_id: int, x: int, y: int) -> None:
        self.lbl_fix_name.setText(f"Fixture Terpilih: PAR LED {fix_id}")
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

    def _on_spin_changed(self) -> None:
        idx = self.canvas_2d.selected_idx
        self.canvas_2d.fixtures[idx]["x"] = self.spin_x.value()
        self.canvas_2d.fixtures[idx]["y"] = self.spin_y.value()
        self.canvas_2d.update()

    def _reset_positions(self) -> None:
        defaults = [120, 260, 400, 540]
        for i, x in enumerate(defaults):
            if i < len(self.canvas_2d.fixtures):
                self.canvas_2d.fixtures[i]["x"] = x
                self.canvas_2d.fixtures[i]["y"] = 80
        self.canvas_2d.update()

    def update_dmx(self, channels: list[int] | bytearray) -> None:
        self.canvas_2d.update_dmx_frame(channels)
